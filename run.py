import streamlit as st
from functions import (
    configure_retriever,
    load_model,
    generate_session_name,classify_intent,update_file
)
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains.conversation.base import ConversationChain
from langchain import PromptTemplate, HuggingFaceHub
from prompt_template import *
from filter_retriever import VectorStoreRetrieverWithFiltering, ConversationalRetrievalChainPassArgs, ConversationalRetrievalChain
from datetime import datetime
import os

if 'session_id' not in st.session_state:
    st.session_state.session_id=generate_session_name()


st.title("COSC 40053 Virtual Teaching Assistant")
# Add WVU-specific UI elements here
lecture_retriever=configure_retriever("lectures")
syllabus_retriever=configure_retriever("syllabus")
hw_clarification_retriever=configure_retriever("homework")

llm=load_model(model_name="gemma2")
def save_context(question, answer,k):
    st.session_state.memory.append({"question": question, "answer": answer})

    # Keep only the last 2 interactions
    if len(st.session_state.memory) > k:
        st.session_state.memory = st.session_state.memory[-k:]

def save_context2(prompt, answer,k):
    st.session_state.memory2.append({"input": prompt, "response": answer})

    # Keep only the last 2 interactions
    if len(st.session_state.memory2) > k:
        st.session_state.memory2 = st.session_state.memory[-k:]

if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            input_key="input",
            output_key="response",
            return_messages=True,
            k=2,
        )

FollowupChain= ConversationChain(
            llm=llm,
            memory=st.session_state.memory,
            verbose=True,
            prompt=PromptTemplate(
            input_variables=["input","chat_history"], template=FollowupTemplate
        ),
        )
if "memory2" not in st.session_state:
    st.session_state.memory2 = ConversationBufferWindowMemory(
            memory_key="chat_history",
            input_key="question",
            output_key="answer",
            return_messages=True,
            k=2,
        )
promptHist = PromptTemplate(
        input_variables=["context", "question", "chat_history"], template=LectureTemplate
    )

LectureConceptChain=ConversationalRetrievalChainPassArgs.from_llm(
        llm,
        retriever=lecture_retriever,
        chain_type="stuff",
        memory=st.session_state.memory2,
        verbose=True,
        max_tokens_limit=4000,
        combine_docs_chain_kwargs={"prompt": promptHist}
    )

promptHist = PromptTemplate(
        input_variables=["context", "question", "chat_history"], template=HWClarificaitonTemplate
    )
HomeworkClarificationChain=ConversationalRetrievalChainPassArgs.from_llm(
        llm,
        retriever=hw_clarification_retriever,
        chain_type="stuff",
        memory=st.session_state.memory2,
        verbose=True,
        max_tokens_limit=4000,
        combine_docs_chain_kwargs={"prompt": promptHist}
    )

promptHist = PromptTemplate(
        input_variables=["context", "question", "chat_history"], template=LectureTemplate
    )
SyllabusChain=ConversationalRetrievalChainPassArgs.from_llm(
        llm,
        retriever=syllabus_retriever,
        chain_type="stuff",
        memory=st.session_state.memory2,
        verbose=True,
        max_tokens_limit=4000,
        combine_docs_chain_kwargs={"prompt": promptHist}
    )

GuidanceChain=ConversationalRetrievalChainPassArgs.from_llm(
        llm,
        retriever=lecture_retriever,
        chain_type="stuff",
        memory=st.session_state.memory2,
        verbose=True,
        max_tokens_limit=4000,
        combine_docs_chain_kwargs={"prompt": PromptTemplate(
        input_variables=["context", "question", "chat_history"], template=GuidanceTemplate
    )},condense_question_prompt=PromptTemplate.from_template(condensed_template)
    )

promptHist=PromptTemplate(
        input_variables=["context", "question"], template=SolveHWTemplate
)
SolveHWChain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=hw_clarification_retriever,
        chain_type="stuff",
        memory=st.session_state.memory2,
        verbose=True,
        max_tokens_limit=4000,
        combine_docs_chain_kwargs={"prompt": promptHist}
)

if "current_intent" not in st.session_state:
    st.session_state.current_intent = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "message" not in st.session_state:
    st.session_state.message=[]

for message1 in st.session_state.message:
    with st.chat_message(message1["role"]):
        st.markdown(message1["content"])

assistant = st.chat_message("assistant")
# Start chat input when a button is pressed (or any other trigger)
import pandas as pd
data=pd.read_csv("QAv2.csv",header=1)
question_list=list(data.Question.values)
for enum,prompt in enumerate(question_list):
    print("=============== The user input is=============",prompt,enum)

    intent,llm_intent=classify_intent(prompt,"llama3.1")
    print("The classified intent is=========",intent)
    print("llm response for intent is",llm_intent)
    print('***********************************")')
    print(st.session_state.memory2.load_memory_variables({}))
    if intent=="Homework Question Clarification" or intent=="Providing Homework Guidance":
        homework_no_presence=llm_intent.split(",")[-1] if len(llm_intent.split(','))>1 else 0
        if homework_no_presence:
            homework_filter = {"source": "homework/"+homework_no_presence.strip()+".pdf"}
        else:
            homework_filter=False
    elif intent=="Answering Questions on Lecture Slides" or intent =="Asking for Clarifying Concepts or Topics":
        chapter_no_presence=llm_intent.split(",")[-1] if len(llm_intent.split(','))>1 else 0
        if chapter_no_presence:
            lecture_filter = {"source": "lectures/"+chapter_no_presence.strip()+".pdf"}
        else:
            lecture_filter=False                       
    st.session_state.current_intent = intent
    with st.chat_message("user"):
        st.markdown(prompt)
        st.session_state.message.append({"role":"user","content":prompt})
    with st.chat_message("assistant"):
                if intent=="Answering Questions on Lecture Slides" or intent == "Asking for Clarifying Concepts or Topics":
                    if lecture_filter:
                        response=LectureConceptChain.run({"question":prompt,"filter":lecture_filter})
                    else:
                        response=LectureConceptChain.run(prompt)
                elif intent=="Answering Questions about Syllabus": #"Answering Questions about Syllabus"
                    response=SyllabusChain.run(prompt)
                elif intent == "Homework Question Clarification":
                    if homework_filter:
                        response=HomeworkClarificationChain.run({"question":prompt,"filter":homework_filter})
                    else:
                        response=HomeworkClarificationChain.run(prompt)

                elif intent == "Providing Homework Guidance":
                    if homework_filter:
                        response=GuidanceChain.run({"question":prompt,"filter":homework_filter})
                    else:
                        response=GuidanceChain.run(prompt)
                elif intent=="Reply to previous conversation":
                    response=FollowupChain.predict(input=prompt)   
                    st.session_state.memory2.save_context({"question":prompt},{"answer":response})    
                elif intent=="Asking to Solve/Answer Homework Question":
                    print("Here")
                    response=SolveHWChain.run({"question":prompt})
                    
                if intent!="Reply to previous conversation":
                    st.session_state.memory.save_context({"input":prompt},{"response":response})
                st.markdown(response)
                st.session_state.chat_history.append({"input":prompt,"role":intent,"response":response})
                update_file()

