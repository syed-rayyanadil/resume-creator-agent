# import ollama

# def generate_text(prompt: str) -> str:
#     """Sends a prompt to the local Llama 3 model and returns the text response."""
#     response = ollama.chat(
#         model='llama3', 
#         messages=[
#             {'role': 'user', 'content': prompt}
#         ]
#     )
#     return response['message']['content']

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load the secret API key from your .env file
load_dotenv()

def generate_text(prompt: str, model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct") -> str:
    """
    Sends a prompt to Groq's cloud using the model selected in the UI.
    Defaults to the 17B model if nothing is passed.
    """
    try:
        # We initialize the LLM dynamically based on the model_name passed in!
        llm = ChatGroq(
            model=model_name, 
            temperature=0.7, 
            max_tokens=4000  
        )
        
        response = llm.invoke(prompt)
        return response.content
        
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return "{}"