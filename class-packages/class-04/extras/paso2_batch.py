"""Variacion paso 2 · batch: la misma cadena traduce varios textos de una vez."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un traductor profesional. Devuelve SOLO la traducción al inglés, sin comentarios."),
    ("human", "{texto}"),
])
cadena = prompt | ChatOllama(model="llama3.1", temperature=0) | StrOutputParser()

textos = [
    "El modelo no recuerda nada entre llamadas.",
    "Un parser convierte texto en datos.",
    "La cadena también es un Runnable.",
]
# batch: una lista de entradas -> una lista de salidas, sin escribir ningún bucle
salidas = cadena.batch([{"texto": t} for t in textos])
for t, s in zip(textos, salidas):
    print(f"ES: {t}\nEN: {s}\n")
