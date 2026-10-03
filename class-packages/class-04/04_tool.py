"""Paso 5 · Tools: el modelo decide llamar a una función; nuestro código la ejecuta."""
from datetime import datetime

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama


@tool
def sumar(a: float, b: float) -> float:
    """Suma dos números y devuelve el resultado."""
    return a + b


@tool
def hora_actual() -> str:
    """Devuelve la fecha y hora actuales del sistema."""
    return datetime.now().strftime("%d/%m/%Y %H:%M")


tools = [sumar, hora_actual]
tools_por_nombre = {t.name: t for t in tools}

# bind_tools: le enseñamos al modelo el "menú" de herramientas (nombre + docstring + argumentos)
modelo = ChatOllama(model="llama3.1", temperature=0).bind_tools(tools)

if __name__ == "__main__":
    pregunta = "¿Cuánto es 1234.5 más 8765.5? Y dime también qué hora es."
    mensajes = [HumanMessage(pregunta)]
    print("PREGUNTA:", pregunta, "\n")

    # 1) El modelo NO responde: pide llamar a las tools
    ai = modelo.invoke(mensajes)
    mensajes.append(ai)
    for llamada in ai.tool_calls:
        print(f"🔧 TOOL CALL -> {llamada['name']}({llamada['args']})")
        # 2) Nuestro código ejecuta la tool y devuelve el resultado como ToolMessage
        resultado = tools_por_nombre[llamada["name"]].invoke(llamada["args"])
        print(f"   RESULTADO -> {resultado}")
        mensajes.append(ToolMessage(content=str(resultado), tool_call_id=llamada["id"]))

    # 3) Con los resultados en el contexto, el modelo redacta la respuesta final
    final = modelo.invoke(mensajes)
    print("\n✅ RESPUESTA FINAL:", final.content)
