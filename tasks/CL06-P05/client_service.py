"""
This answers questions and complains
"""

# IMPORTS
from typing import TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from methods import my_state_to_string

# MODEL

model = ChatOllama(model='llama3.2:3b', temperature=0)

# STATE GRAPH
class State(TypedDict):
    message: str
    tipo: str
    response: str

# NODES

def qualify(state: State) -> dict:
    """Decides if message is  a question or a complain"""
    
    result = model.invoke(
        f'Answer "question" or "complain" depending on the user message: "{state["message"]}"'
        f'Answer just one word "question" or "complain".'
    )
    
    tipo = result.content.strip().lower()
    
    if tipo == 'question': return {'tipo': 'ask'}
    
    return {'tipo': 'complain'}

def ask(state: State) -> dict:
    """Ask this question"""
    
    result = model.invoke(
        f'Answer this question shortly: "{state["message"]}"'
    )
    
    return {'response': result.content}

def complain(state: State) -> dict:
    """Answer this complain"""
    
    result = model.invoke(
        f'Answer this complain shortly: "{state["message"]}"'
    )
    
    return {'response': result.content}

# EDGE CONDITIONS

def condition(state: State) -> str:
    return state['tipo']

# GRAPH AND COMPILER

builder = StateGraph(State)

builder.add_node('qualify', qualify)
builder.add_node('ask', ask)
builder.add_node('complain', complain)

builder.add_edge(START, 'qualify')
builder.add_conditional_edges('qualify', condition, {
    'ask': 'ask',
    'complain': 'complain',
})
builder.add_edge('ask', END)
builder.add_edge('ask', END)

graph = builder.compile()

# EXECUTE

user_messages: list[str] = [
    'How is my order going?',
    'I am very angry because my order came broken.'
]

i=0

for msn in user_messages:
    """Iterate user messages"""
    
    i += 1
    
    print(f'Message number: {i} -> "{msn}"')
    
    for node in graph.stream(
        {'message': msn, 'tipo': '', 'response': ''},
        stream_mode='updates',
    ):
        print()
        print(my_state_to_string(node))
    
    
    print('===================')
    










# response = my_state_to_string({
#     'message': 'Este es mi msn',
#     'tipo': 'queja',
#     'response': 'Respondido',
# })

# print(response)