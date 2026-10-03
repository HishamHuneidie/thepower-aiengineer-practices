"""Paso 2 · Primera cadena LCEL: prompt | modelo | parser."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# 1) PROMPT: la instrucción se escribe una vez; {texto} es el hueco que rellenamos al invocar
prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un traductor profesional. Devuelve SOLO la traducción al inglés, sin comentarios."),
    ("human", "{texto}"),
])

# 2) MODELO: el ChatModel local. Cambiar de proveedor = cambiar solo esta línea
modelo = ChatOllama(model="llama3.1", temperature=0)

# 3) PARSER: el modelo devuelve un AIMessage; el parser se queda con el texto limpio
parser = StrOutputParser()

# LCEL: el | une las tres piezas en una tubería. La cadena también es un Runnable
cadena = prompt | modelo | parser

if __name__ == "__main__":
    entrada = {"texto": "Mañana empezamos el máster de AI Engineer y estamos muy ilusionados."}
    salida = cadena.invoke(entrada)
    print("ENTRADA :", entrada["texto"])
    print("SALIDA  :", salida)
    print("ES TEXTO:", isinstance(salida, str))   # True: el parser ha convertido el AIMessage en texto
