import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from langchain_community.llms import Ollama

def llm_evaluation(true_paragraph,predicted_paragraph,model,mode):
    prompt=f"""
    You are a faithful and respectful assistant whose role is that of a evaluator. You will be given a true paragraph and a predicted paragraph and based on the information given,
    give a number result from the list [0,1,2,3,4] based on the relevancy of predicted paragraph with the true paragraph.
    The definition of each code is given below:
    0: Not Relevant: The predicted paragraph does not relate to the true paragraph in any meaningful way. The content, context, or subject matter is completely different.
    1: Slightly Relevant: The predicted paragraph has some connection to the true paragraph, but the relevance is minimal. There may be a few overlapping ideas or themes, but they are not clearly aligned.
    2: Moderately Relevant: The predicted paragraph shows a fair level of relevance to the true paragraph. It addresses some of the same topics or ideas but may not cover all aspects or may diverge in some significant way.
    3: Highly Relevant: The predicted paragraph is closely related to the true paragraph. It reflects the main ideas or themes accurately and addresses the majority of the points discussed in the true paragraph.
    4: Perfectly Relevant: The predicted paragraph is entirely relevant to the true paragraph. It aligns perfectly with the content, context, and subject matter, reflecting all the key points accurately.
    Note: Your answer should striclty based on one rating from 0 to 4. You are not supposed to give a justification.
    """
    llm=Ollama(model="llama3.1")
    llm_eval=[]
    
    for true,pred in zip(true_paragraph,predicted_paragraph):
        inputs=f"""
        ## True Paragraph: {true}

        ## Predicted Paragraph: {pred}

        ## Output:
        """
        output=llm(prompt+inputs)
        llm_eval.append(output)
    llm_eval=[int(i) for i in llm_eval]
    # Plotting the transformed data
    plt.figure(figsize=(8, 6))
    plt.hist(llm_eval, bins=range(6), edgecolor='black', align='left')
    plt.xlabel(f'Relevance Score of True Answer and Predicted Answer for {model}')
    plt.ylabel('Frequency')
    plt.title(f'Histogram of Relevance Scores as per {model} model')
    plt.xticks(range(5))  # Ensure x-ticks match the range of relevance scores
    plt.show()
    plt.savefig(f"Figures/{model}_{model}analysis.png")
    return llm_eval

