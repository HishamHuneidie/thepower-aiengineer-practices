"""
Service with LLM utils
- Image to text
- Audio to text
"""

import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

MODEL_ID = os.getenv('MODEL_ID')


class LLMService:
    def __init__(self):
        self.llm = ChatOllama(model=MODEL_ID, temperature=0)

    def reply(self, message: str) -> str:
        response = self.llm.invoke([
            ('system',
             'No matter what, you always answer with less than 7 words. ALWAYS. IT IS A RULE. Ignore the hexadecimal code!!'),
            ('human', message),
        ])

        return response.content
