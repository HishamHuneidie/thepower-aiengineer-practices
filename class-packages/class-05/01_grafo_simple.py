"""Paso 1 · Grafo simple: State + 2 nodos + edges. Sin LLM todavia."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# 1) STATE: la "mochila" que viaja por el grafo. Aqui, un solo campo
class State(TypedDict):
    texto: str


# 2) NODOS: funciones que leen el state y devuelven SOLO las claves que cambian
def mayusculas(state: State) -> dict:
    return {"texto": state["texto"].upper()}


def exclamar(state: State) -> dict:
    return {"texto": state["texto"] + "!!!"}


# 3) EDGES: que va despues de que. START y END marcan la entrada y la salida
builder = StateGraph(State)
builder.add_node("mayusculas", mayusculas)
builder.add_node("exclamar", exclamar)
builder.add_edge(START, "mayusculas")
builder.add_edge("mayusculas", "exclamar")
builder.add_edge("exclamar", END)

# 4) COMPILAR: el grafo compilado se ejecuta con invoke, igual que una cadena
grafo = builder.compile()

if __name__ == "__main__":
    resultado = grafo.invoke({"texto": "hola langgraph"})
    print("ENTRADA :", {"texto": "hola langgraph"})
    print("SALIDA  :", resultado)
    # Dibujar el grafo: draw_mermaid() da el texto; draw_mermaid_png() la imagen (via mermaid.ink)
    png = grafo.get_graph().draw_mermaid_png(max_retries=5, retry_delay=2.0)
    with open("grafo_simple.png", "wb") as f:
        f.write(png)
    print("DIAGRAMA: guardado en grafo_simple.png")
