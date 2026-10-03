"""Paso 4 · Memoria: la cadena recuerda la conversación por session_id."""
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama

prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un asistente amable. Responde en español y en una o dos frases."),
    MessagesPlaceholder(variable_name="historial"),   # aquí se inyecta la conversación previa
    ("human", "{pregunta}"),
])
cadena = prompt | ChatOllama(model="llama3.1", temperature=0) | StrOutputParser()

# El "almacén" de memoria: un historial por session_id (en producción: Redis o Postgres)
historiales: dict[str, InMemoryChatMessageHistory] = {}

def obtener_historial(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]

chat = RunnableWithMessageHistory(
    cadena,
    obtener_historial,
    input_messages_key="pregunta",
    history_messages_key="historial",
)

if __name__ == "__main__":
    config = {"configurable": {"session_id": "alumno-1"}}
    turnos = [
        "Hola, me llamo Ignacio y soy profesor en The Power.",
        "Estoy preparando una clase sobre LangChain. ¿Me das una idea para abrirla?",
        "¿Cómo me llamo y de qué es la clase que preparo?",
    ]
    for i, pregunta in enumerate(turnos, 1):
        respuesta = chat.invoke({"pregunta": pregunta}, config=config)
        print(f"[Turno {i}] Tú  : {pregunta}")
        print(f"[Turno {i}] Bot : {respuesta}\n")

    # Prueba de control: otra sesión NO comparte memoria
    otra = chat.invoke({"pregunta": "¿Cómo me llamo?"}, config={"configurable": {"session_id": "alumno-2"}})
    print(f"[Otra sesión] Bot : {otra}")
    print(f"\nMensajes guardados en 'alumno-1': {len(historiales['alumno-1'].messages)}")
