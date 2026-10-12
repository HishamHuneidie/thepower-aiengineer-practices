"""Practice observability with just decorator @observe"""

# imports
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langchain_ollama import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langfuse import observe, get_client

load_dotenv()

# state

class State(TypedDict):
    messages: Annotated[list, add_messages]

# tools

@tool
@observe(name='car-price-faqs :: get price')
def get_car_price(car_name: str) -> int|None:
    """Get the car price from the cars name"""
    cars = {
        'ford': 145,
        'lamborguinni': 200,
        'ferrari': 185,
    }
    
    return cars.get(car_name, None)

@tool
@observe(name='car-price-faqs :: add prices')
def add_up_two_car_prices(price_1: int, price_2: int) -> int:
    """Add up the price of two cars"""
    return price_1 + price_2

all_tools = [get_car_price, add_up_two_car_prices]

# model
model = ChatOllama(model='llama3.2:3b', temperature=0)
model_with_prices = model.bind_tools([get_car_price])
model_with_sum = model.bind_tools([add_up_two_car_prices], tool_choice='required')

# define nodes

@observe(name='car-price-faqs :: chatbot')
def chatbot(state: State) -> dict:
    messages = state['messages']
    
    # This was made because the LLM fails in the sum.
    # It called badly the tool that sums the prices
    # Now it does not work because it does not call the tool that sums prices

    prices_received = [
        message
        for message in messages
        if message.type == 'tool'
        and message.name == 'get_car_price'
        and message.status == 'success'
    ]

    sum_completed = any(
        message.type == "tool"
        and message.name == "add_up_two_car_prices"
        and message.status == "success"
        for message in messages
    )

    current_model = model_with_prices

    if sum_completed:
        current_model = model
    elif len(prices_received) >= 2:
        current_model = model_with_sum

    result = current_model.invoke(messages)
    return {'messages': [result]}

# connect nodes

builder = StateGraph(State)

builder.add_node('chatbot', chatbot)
builder.add_node('tools', ToolNode(all_tools))

builder.add_edge(START, 'chatbot')
builder.add_conditional_edges('chatbot', tools_condition)
builder.add_edge('tools', 'chatbot')

# execute

graph = builder.compile()

@observe(name='car-price-faqs :: init')
def execute(question: str) -> dict:
    messages = [
        SystemMessage(content="""
            You are a car price assistant.

            Rules:
            1. ALWAYS use get_car_price to retrieve car prices.
            2. NEVER invent car prices.
            3. When asked for the total of two cars:
                - First call get_car_price for each car.
                - Wait for the results.
                - Then call add_up_two_car_prices using the numeric prices.
                - ALWAYS call add_up_two_car_prices even if you know how to add up two numbers.
            4. NEVER pass tool names as arguments.
            5. If a tool fails, do not invent a result.
        """),
        HumanMessage(content=question),
    ]

    result = graph.invoke({'messages': messages})
    
    return result

questions = [
    #'What is the cost of the car ferrari?',
    'How much is it if I buy two cars, ford and lamborguinni. What is the total?',
]

for question in questions:
    """Ask several questions"""
    
    result = execute(question)
    
    print()
    print(result)

get_client().flush()