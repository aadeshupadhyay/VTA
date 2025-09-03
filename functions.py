import streamlit as st
# Function to switch layouts
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.vectorstores import FAISS
from filter_retriever import VectorStoreRetrieverWithFiltering, ConversationalRetrievalChainPassArgs
from langchain.embeddings import HuggingFaceEmbeddings
import json
import pandas as pd
import os
from langchain.llms import Ollama
from langchain.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
from typing import Any, Dict, List
from langchain.schema import Document
import json
import io
from datetime import datetime
import uuid
import pytz
import streamlit as st 
from prompt_template import *
import textdistance
from langchain import HuggingFaceHub


CHAT_HISTORY_FILE = "chat_history.json"

class DocumentLoader(object):
    """Loads in a document with a supported extension"""

    supported_extensions = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".docx": UnstructuredWordDocumentLoader,
    }

def load_document(temp_filepath: str) -> List[Document]:
    '''Load a file and return it as a list of documents.'''
    extension = os.path.splitext(temp_filepath)[1]
    loader_class = DocumentLoader.supported_extensions.get(extension)
    if loader_class:
        loader = loader_class(temp_filepath)
        return loader.load()
    else:
        raise ValueError(f"Unsupported file extension: {extension}")

def configure_retriever(folder: str) -> VectorStoreRetrieverWithFiltering:
    '''Read documents, configure retriever, and the chain.'''
    files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
    docs = []
    for file in files:
        docs.extend(load_document(os.path.join(folder, file)))
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)    
    # Create embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create the FAISS vector store
    vectorstore = FAISS.from_documents(splits, embeddings)
    # Create the retriever
    retriever = VectorStoreRetrieverWithFiltering(vectorstore=vectorstore, search_type="similarity")
    return retriever


# Function to read chat history from file
def read_chat_history():
    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
                        return json.load(f)
    except FileNotFoundError:
        return []


       
# Function to write chat history to file
def write_chat_history(history):
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(history, f,indent=4)
# Conversion function
def convert_structure(data):
    # Define the conversion mapping
    user = data["user"]
    content = data["content"]
    response = data["response"]

    # Prepare the converted format
    user_output = f"{user}:{content}"
    response_output = f"Teaching Assistant: {response}"
    return user_output, response_output

@st.cache_resource
def load_model(model_name):
    llm=Ollama(model=model_name,temperature=0)
    return llm

# User input handling
TOPIC_FILE = "topic.json"
# Function to read discussion topic from file
def read_topic():
    try:
        with open(TOPIC_FILE, "r") as f:
            data = json.load(f)  # Load the entire JSON data once
            topic=data.get("topic", "")
            details=data.get("details", "")
            return topic,details
    except FileNotFoundError:
        return ""


# Function to write discussion topic to file
def write_topic(topic,details):
    with open(TOPIC_FILE, "w") as f:
        json.dump({"topic": topic,"details":details}, f,indent=4)


def generate_session_name():
    '''
    returns the name of run for session for history tracking
    '''
    # You can customize the session name format here
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = uuid.uuid4().hex
    return f"session-{timestamp}-{unique_id}"


def classify_intent(query,model_name):
    """
    Use the LLM to classify the intent of the query.
    """
    prompt = intent_classification+ "\n"+"Question: "+query 
    intents = [
        "Answering Questions on Lecture Slides",
        "Providing Homework Guidance",
        "Asking for Clarifying Concepts or Topics",
        "Answering Questions about Syllabus",
        "Homework Question Clarification",
        "Reply to previous conversation",
        "Asking to Solve/Answer Homework Question"
    ]
    llm=load_model(model_name)

    response = llm(prompt, max_tokens=1024)
    distances = [
        textdistance.levenshtein(response.lower(), INTENT.lower()) for INTENT in intents
    ]
    # Find the index of the smallest distance (most similar)
    closest_intent_index = distances.index(min(distances))
    closest_intent = intents[closest_intent_index]
    return closest_intent,response.lower()

def update_file():
    history=st.session_state.chat_history
    # session_id=st.session_state.session_id+".json"
    session_id="lol.json"
    with open(session_id, "w") as json_file:
        json.dump(history, json_file, indent=4)


