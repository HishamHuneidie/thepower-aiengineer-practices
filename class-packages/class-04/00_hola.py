"""Paso 1 · Setup: comprobar que Python habla con el modelo local (Ollama + llama3.1)."""
from langchain_ollama import ChatOllama

modelo = ChatOllama(model="llama3.1", temperature=0)

respuesta = modelo.invoke("Hola, preséntate en una sola frase.")

print("Modelo :", modelo.model)
print("Tipo   :", type(respuesta).__name__)   # AIMessage: un mensaje, no un string
print("Texto  :", respuesta.content)
