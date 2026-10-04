"""
    Use pipelines to generate a several steps answer
"""

from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

model = ChatOllama(model='llama3.2:3b', temperature=0)
parser = StrOutputParser()

text_generator = (
    ChatPromptTemplate.from_template('Generate a paragraph of 50 words about this topic: {topic}')
    | model
    | parser
)

summarizer = (
    ChatPromptTemplate.from_template('Summarize this {paragraph} in maximum 15 words')
    | model
    | parser
)

pipeline = (
    RunnablePassthrough.assign(paragraph=text_generator)
    | RunnablePassthrough.assign(summary=summarizer)
)

result = pipeline.invoke({'topic': str(input('Tell me a topic: '))})

print('    TOPIC : '+ result['topic'])
print('PARAGRAPH : '+ result['paragraph'])
print('  SUMMARY : '+ result['summary'])