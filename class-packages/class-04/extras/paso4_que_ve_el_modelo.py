"""Variacion paso 4 · que se le reenvia realmente al modelo en cada llamada."""
import warnings

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama

warnings.filterwarnings("ignore")  # ocultamos el aviso de deprecación (ya lo vimos en el paso 4)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un asistente amable. Responde en español y en una sola frase."),
    MessagesPlaceholder(variable_name="historial"),
    ("human", "{pregunta}"),
])
cadena = prompt | ChatOllama(model="llama3.1", temperature=0) | StrOutputParser()
historiales = {}
chat = RunnableWithMessageHistory(
    cadena,
    lambda sid: historiales.setdefault(sid, InMemoryChatMessageHistory()),
    input_messages_key="pregunta",
    history_messages_key="historial",
)
config = {"configurable": {"session_id": "alumno-1"}}
for pregunta in ["Me llamo Ignacio.", "Mi lenguaje favorito es Python.", "¿Qué sabes de mí?"]:
    chat.invoke({"pregunta": pregunta}, config=config)

print("Lo que hay guardado en la sesión 'alumno-1':\n")
for m in historiales["alumno-1"].messages:
    print(f"  {type(m).__name__:<13} | {m.content}")

# Lo que recibiría el modelo en la PRÓXIMA llamada: system + historial + pregunta nueva
siguiente = prompt.invoke({"historial": historiales["alumno-1"].messages, "pregunta": "¿Y cómo me llamo?"})
print(f"\nMensajes que viajan al modelo en la siguiente llamada: {len(siguiente.messages)}")
