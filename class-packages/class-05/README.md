# langgraph-basics · Master AI Engineer · Sesion 2

Proyecto de clase: de un grafo minimo a un agente con memoria y herramientas, un paso por archivo.
Todo corre en local con Ollama (llama3.1): coste de API 0 EUR.

## Puesta en marcha
1. Ollama con el modelo descargado (de la Sesion 1): `ollama pull llama3.1`
2. Crea el entorno: `python -m venv .venv` y activalo (`.venv\Scripts\activate` en Windows)
3. Instala dependencias: `pip install -r requirements.txt`

## Los conceptos
- **State**: un TypedDict que viaja por todo el grafo. Es la memoria compartida: si no esta en el State, el grafo no lo sabe.
- **Nodos**: funciones que leen el State y devuelven SOLO las claves que cambian.
- **Aristas (edges)**: que nodo va despues de cual. Las **condicionales** eligen el camino segun el State y permiten ciclos.
- **Checkpointer**: guarda el State despues de cada paso, por `thread_id`. Da memoria entre turnos.

## Los pasos
| Archivo | Que demuestra |
|---|---|
| `01_grafo_simple.py` | State + 2 nodos + edges; compilar, invocar y dibujar el grafo |
| `02_chatbot.py` | State con `add_messages` y un nodo que llama a ChatOllama |
| `03_memoria.py` | `MemorySaver` + `thread_id`: recuerda entre turnos |
| `04_herramientas.py` | `ToolNode` + `tools_condition`: el ciclo chatbot -> tools -> chatbot |
| `05_grafo_final.py` | Dibuja el grafo final en `grafo.png` |

Ejecuta cada uno con `python <archivo>`.

## Extras (variaciones vistas en clase)
- `extras/paso1_stream.py` · ver el State despues de cada nodo con `stream`
- `extras/paso2_sin_reducer.py` · que pasa si quitas `add_messages`
- `extras/paso3_checkpoints.py` · el checkpointer guarda una foto en cada paso
- `extras/paso4_sin_tool.py` · la arista condicional decide: con y sin tool

## Ejercicios para casa
- **Ejercicio 1 · Un grafo que clasifica y responde** (basico, 1,5 h): clasifica un mensaje como pregunta o queja y una arista condicional lo manda a un nodo de respuesta u otro.
  Solucion de referencia: `soluciones/ejercicio1_clasificador.py` (intentalo antes de mirarla).
- **Ejercicio 2 · Reto: el grafo por fases**: grafo simple -> chatbot -> memoria -> herramientas, con tu propia tool, y una conversacion multi-turno que la use.

## Notas
- La primera llamada tarda mas: Ollama carga el modelo en memoria.
- `draw_mermaid_png` usa el servicio web mermaid.ink; si tarda, los scripts reintentan hasta 5 veces.
- Poca RAM (<8 GB)? Usa `llama3.2:3b` y cambia el nombre del modelo en los scripts.
