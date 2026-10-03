"""Paso 3 · Cadena compuesta: generar -> resumir, conservando la salida intermedia."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

modelo = ChatOllama(model="llama3.1", temperature=0)
parser = StrOutputParser()

# Etapa 1: genera un párrafo sobre el tema
generar = (
    ChatPromptTemplate.from_template("Escribe un párrafo divulgativo de unas 80 palabras sobre: {tema}")
    | modelo
    | parser
)

# Etapa 2: resume ese párrafo en una frase
resumir = (
    ChatPromptTemplate.from_template("Resume en UNA sola frase el siguiente texto:\n\n{parrafo}")
    | modelo
    | parser
)

# RunnablePassthrough.assign deja pasar la entrada y le AÑADE claves nuevas.
# Así el diccionario va creciendo: {tema} -> {tema, parrafo} -> {tema, parrafo, resumen}
pipeline = (
    RunnablePassthrough.assign(parrafo=generar)
    | RunnablePassthrough.assign(resumen=resumir)
)

if __name__ == "__main__":
    resultado = pipeline.invoke({"tema": "qué es un agente de IA"})
    print("── ETAPA 1 · PÁRRAFO (salida intermedia) ──")
    print(resultado["parrafo"])
    print("\n── ETAPA 2 · RESUMEN (salida final) ──")
    print(resultado["resumen"])
