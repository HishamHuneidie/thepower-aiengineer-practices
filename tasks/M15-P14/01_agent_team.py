"""
Agent team:
- researcher
- writer
"""

# imports

import time
from typing import TypedDict

from ddgs import DDGS
from ddgs.exceptions import DDGSException
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from colorize import colorize

# global configs

llm = ChatOllama(model='llama3.2:3b', temperature=0)

class DDGSSource(TypedDict):
    title: str
    href: str
    body: str

class GlobalState(TypedDict):
    question: str
    sources: list[DDGSSource]
    summary: str


# nodes

def researcher(state: GlobalState) -> GlobalState:
    """Researches with DuckDuckGo"""

    for _ in range(4):
        """Attempt several times the research"""
        try:
            sources: list[DDGSSource] = DDGS().text(state['question'], max_results=5)

            return GlobalState(sources=sources)
        except DDGSException as e:
            print(e)
            time.sleep(.5)

    return GlobalState(sources=[])

def writer(state: GlobalState) -> GlobalState:
    """Summarizes topic from sources"""

    delimiter = "\n"
    source_list = delimiter + delimiter.join(
        f"[{i}] {source['title']}: {source['body']}" for i, source in enumerate(state['sources'])
    )

    prompt = f"""
    Write a 5 lines summary in Spanish using ONLY these sources:
    
    {source_list}
    
    Note: Cite each data with a [n]
    """

    response: AIMessage = llm.invoke(prompt)

    return GlobalState(summary=response.content)


# graph connections and execution


builder = StateGraph(GlobalState)

builder.add_node('researcher', researcher)
builder.add_node('writer', writer)
builder.add_edge(START, 'researcher')
builder.add_edge('researcher', 'writer')
builder.add_edge('writer', END)

graph = builder.compile()


# run graph

if __name__ == '__main__':
    result = graph.invoke({'question': 'Semana laboral de 4 días en España'})

    print()
    print(colorize('Topic:', 'magenta'))
    print(colorize(f"{result['question']}", 'yellow'))

    print()
    print(colorize('Summary:', 'magenta'))
    print(colorize(f"{result['summary']}", 'yellow'))

    print()
    print(colorize('Sources:', 'magenta'))
    for i, source in enumerate(result['sources']):
        n = colorize(f"[{i}]", 'magenta')
        line = colorize(f"{source['title']}: {source['body']}", 'yellow')
        print(f"{n} {line}")