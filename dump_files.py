import json 
import pandas as pd
qa=pd.read_csv("QAv2.csv",header=1)
with open("llama3-1.json",'r') as file:
    llama_chat=json.load(file)

with open("gemma2.json",'r') as file:
    gemma_chat=json.load(file)

def dump_filess(roles,file_name):
    qa_obj=list(qa.Objective.values)
    qa_question=list(qa.Question.values)
    qa_role=list(qa['Expected Role'].values)
    qa_solution=list(qa['Expected Solution'].values)
    qa_lec_question=list(qa['Actual Question'].values)
    print(len(qa),len(llama_chat),len(gemma_chat))
    lecture_qn=[]
    llama_answer,gemma_answer=[],[]
    true_roles,true_answer=[],[]
    obj=[]
    for enum,prompt in enumerate(qa_question):
        if any(role in qa_role[enum] for role in roles):
            model_prompt=llama_chat[enum]['input']
            # if prompt==model_prompt:
            true_roles.append(qa_role[enum])
            true_answer.append(qa_solution[enum])
            obj.append(qa_obj[enum])
            lecture_qn.append(prompt)
            llama_answer.append(llama_chat[enum]['response'])
            gemma_answer.append(gemma_chat[enum]['response'])

            # else:
                # print("lecture issue",len(prompt),len(model_prompt))
                # print("prompt",prompt)
                # print("model",model_prompt)
                # print("====================")
    # Create a DataFrame from the lists
    df = pd.DataFrame({
        'true_roles': true_roles,
        'objectives': obj,
        'actual_question': lecture_qn,
        'true_answer': true_answer,
        'llama_answer': llama_answer,
        'gemma_answer': gemma_answer,
        'evaluation_llama':[0 for i in gemma_answer],
        'evaluation_gemma':[0 for i in gemma_answer]
    })
    df.to_csv(file_name)


lecture_roles=["Answering Questions on Lecture Slides","Asking for Clarifying Concepts or Topics","Answering Questions about Syllabus"]

dump_filess(lecture_roles,"human_evaluation/lecture.csv")

homework_roles=["Providing Homework Guidance"]


def dump_hw_filess(roles,file_name):
    qa_obj=list(qa.Objective.values)
    qa_question=list(qa.Question.values)
    qa_role=list(qa['Expected Role'].values)
    qa_solution=list(qa['Expected Solution'].values)
    qa_hw_question=list(qa['Actual Question'].values)

    llama_answer,gemma_answer=[],[]
    true_roles,hw_question=[],[]
    obj=[]
    for enum,prompt in enumerate(qa_question):
        if any(role in qa_role[enum] for role in roles):
            model_prompt=llama_chat[enum]['input']
            # if prompt==model_prompt:
            true_roles.append(qa_role[enum])
            hw_question.append(qa_hw_question[enum])
            obj.append(qa_obj[enum])
            llama_answer.append(llama_chat[enum]['response'])
            gemma_answer.append(gemma_chat[enum]['response'])
            # else:
            #     print("homework issue",len(prompt),len(model_prompt))
            #     print("prompt",prompt)
            #     print("model",model_prompt)
            #     print("====================")

    # Create a DataFrame from the lists
    df = pd.DataFrame({
        'true_roles': true_roles,
        'objectives': obj,
        'actual_question': hw_question,
        'llama_answer': llama_answer,
        'gemma_answer': gemma_answer,
        'evaluation_llama':[0 for i in gemma_answer],
        'evaluation_gemma':[0 for i in gemma_answer]
    })
    df.to_csv(file_name)
dump_hw_filess(homework_roles,"human_evaluation/homework_guidance.csv")
homework_roles=["Homework Question Clarification"]
dump_hw_filess(homework_roles,"human_evaluation/homework_clarification.csv")

