"""Agent in phases"""

#imports

from typing import TypedDict, Annotated
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from methods import my_state_to_string

#model and tools

@tool
def get_price(product_name: str) -> None|float:
    """Ask for a product's price by product name"""
    
    products = {
        'laptop': 243.12,
        'mouse': 43.05,
        'screen': 150.88
    }
    
    if product_name not in products: return None
    
    return products.get(product_name)

model = ChatOllama(model='llama3.2:3b', temperature=0).bind_tools([get_price])

#state

class State(TypedDict):
    messages: Annotated[list, add_messages]

#define nodes

def chatbot(state: State) -> dict:
    result = model.invoke(state['messages'])
    return {'messages': [result]}

#compile, nodes endges and conditions

builder = StateGraph(State)

builder.add_node('chatbot', chatbot)
builder.add_node('tools', ToolNode([get_price]))

builder.add_edge(START, 'chatbot')
builder.add_conditional_edges('chatbot', tools_condition)
builder.add_edge('tools', 'chatbot')

#memory

graph = builder.compile(checkpointer=MemorySaver())

config: RunnableConfig = {
    'configurable': {
        'thread_id': 'client_id_1'
    }
}

#execute

questions: list[str] = [
    'how much is the laptop?',
    '¿What is the cost of the mouse?',
]

for question in questions:
    """Ask several times different things"""
    
    print()
    print(f'Question: {question}')

    for node in graph.stream(
        {'messages': [HumanMessage(content=question)]},
        config=config,
        stream_mode='updates',
    ):
        print()
        print(my_state_to_string(node))
        #print()
        #print(f'User says : {question}')
        #print(f'  AI says : {response["messages"][-1].content}')