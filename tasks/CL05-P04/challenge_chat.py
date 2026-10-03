"""
    Creates a chat with following capabilities:
    - Memorizes old messages
    - Uses tools
"""

from datetime import datetime
import time
from typing import List, Tuple
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool

# tools

def colorize(txt: str, color: str) -> str:
    green = '\033[32m'
    red = '\033[31m'
    blue = '\033[34m'
    yellow = '\033[33m'
    reset_color = '\033[0m'
    
    selected_color = None
    
    if color == 'green': selected_color = green
    elif color == 'red': selected_color = red
    elif color == 'blue': selected_color = blue
    elif color == 'yellow': selected_color = yellow
    
    if selected_color is None:
        return txt
    
    return f"{selected_color}{txt}{reset_color}"

@tool
def add_numbers(a: float, b: float) -> float:
    """Add two float numbers"""
    return a + b

@tool
def give_current_time() -> str:
    """Returns current time in format d/m H:M"""
    return datetime.now().strftime("%d/%m %H:%M")

tools = [add_numbers, give_current_time]
tools_by_name = {t.name: t for t in tools}

# model
model = ChatOllama(model='llama3.2:3b', temperature=0).bind_tools(tools)

# prompt
system_message = 'You are an agent that uses tools to answer questions. You use always your tools even when you can solve it without them.'
welcome_message = 'Hi, ask whatever you want'
first_question = str(input(f'{welcome_message}...\n'))

messages: List[BaseMessage] = [
    SystemMessage(system_message),
    AIMessage(welcome_message),
    HumanMessage(first_question),
]

# parser

# chain

# execute

start = time.time()
print()

while True:
    ai: BaseMessage = model.invoke(messages)
    messages.append(ai)
    
    if not ai.tool_calls:
        break

    for call in ai.tool_calls:
        c_id, c_name, c_args = call['id'], call['name'], call['args']
        
        print(f'[TOOL CALL] >> {c_name}({c_args})')
        
        result: AIMessage = tools_by_name[c_name].invoke(c_args)
        print(f'[RESULT]    >> {result}')
        messages.append(ToolMessage(content=str(result), tool_call_id=c_id))

duration = time.time() - start
print()
print(f'It took {duration} seconds in answering')
print(f'[RESULT]    >> \n{colorize(str(ai.content), "yellow")}')

print()
for message in messages:
    print(f'<{message.__class__.__name__}> :: ' + colorize(str(message.content), 'yellow'))