"""Variacion paso 5 · que ve el modelo de una tool y que devuelve cuando decide usarla."""
import json

from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_ollama import ChatOllama


@tool
def sumar(a: float, b: float) -> float:
    """Suma dos números y devuelve el resultado."""
    return a + b


print("1) ESQUEMA QUE RECIBE EL MODELO (sale del nombre, el docstring y los type hints):")
f = convert_to_openai_tool(sumar)["function"]
print(f"   name        = {f['name']}")
print(f"   description = {f['description']}")
print(f"   parameters  = {json.dumps(f['parameters']['properties'])}")
print(f"   required    = {f['parameters']['required']}")

ai = ChatOllama(model="llama3.1", temperature=0).bind_tools([sumar]).invoke("¿Cuánto es 1234.5 más 8765.5?")
print("\n2) LO QUE DEVUELVE EL MODELO:")
print(f"   content    = {ai.content!r}   <- no hay texto: no responde, PIDE")
print(f"   tool_calls = {ai.tool_calls}")
