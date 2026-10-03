"""Variacion paso 3 · añadir una tercera etapa: generar -> resumir -> traducir."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

modelo = ChatOllama(model="llama3.1", temperature=0)
parser = StrOutputParser()

generar = ChatPromptTemplate.from_template("Escribe un párrafo divulgativo de unas 80 palabras sobre: {tema}") | modelo | parser
resumir = ChatPromptTemplate.from_template("Resume en UNA sola frase el siguiente texto:\n\n{parrafo}") | modelo | parser
traducir = ChatPromptTemplate.from_template("Traduce al inglés. Devuelve SOLO la traducción:\n\n{resumen}") | modelo | parser

pipeline = (
    RunnablePassthrough.assign(parrafo=generar)
    | RunnablePassthrough.assign(resumen=resumir)
    | RunnablePassthrough.assign(traduccion=traducir)   # la nueva etapa: una línea más
)

resultado = pipeline.invoke({"tema": "qué es un agente de IA"})
print("Claves al final:", list(resultado.keys()))
print("\n── RESUMEN ──\n" + resultado["resumen"])
print("\n── TRADUCCIÓN (etapa 3) ──\n" + resultado["traduccion"])
