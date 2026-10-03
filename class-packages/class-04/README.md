# langchain-basics · Master AI Engineer · Sesion 1

Proyecto de clase: las piezas basicas de LangChain, una por archivo, en el orden de la sesion.
Todo corre en local con Ollama (llama3.1): coste de API 0 EUR.

## Puesta en marcha
1. Instala Ollama (https://ollama.com) y descarga el modelo: `ollama pull llama3.1`
2. Crea el entorno: `python -m venv .venv` y activalo (`.venv\Scripts\activate` en Windows)
3. Instala dependencias: `pip install -r requirements.txt`

## Los pasos
| Archivo | Pieza de LangChain | Que demuestra |
|---|---|---|
| `00_hola.py` | Models | Python habla con el modelo local; devuelve un `AIMessage` |
| `01_chain.py` | Prompts + Parsers + LCEL | `prompt \| modelo \| parser` traduce al ingles y devuelve texto limpio |
| `02_compuesta.py` | Chains compuestas | Generar -> resumir con `RunnablePassthrough.assign`, viendo el paso intermedio |
| `03_memoria.py` | Memory | `RunnableWithMessageHistory`: recuerda por `session_id` |
| `04_tool.py` | Tools | `@tool` + `bind_tools`: el modelo pide la llamada, nuestro codigo la ejecuta |

Ejecuta cada uno con `python <archivo>`.

## Extras (variaciones vistas en clase)
- `extras/paso2_batch.py` · la misma cadena traduce una lista con `batch`
- `extras/paso3_tres_etapas.py` · tercera etapa: generar -> resumir -> traducir
- `extras/paso4_que_ve_el_modelo.py` · que mensajes se reenvian al modelo en cada llamada
- `extras/paso5_esquema_tool.py` · el esquema que ve el modelo de una tool y su tool call en crudo

## Notas
- La primera llamada tarda mas: Ollama carga el modelo en memoria.
- `RunnableWithMessageHistory` funciona pero esta marcado como deprecado en LangChain 1.x:
  su sustituto es la persistencia de LangGraph (Sesion 2).
- Poca RAM (<8 GB)? Usa `llama3.2:3b` y cambia el nombre del modelo en los scripts.

## Ejercicios para casa
- **Ejercicio 1 · Tu primer resumidor con LCEL** (basico, 1 h): cadena `prompt | modelo | parser` que resume un texto largo en 3 vinetas.
  Solucion de referencia: `soluciones/ejercicio1_resumidor.py` (intentalo antes de mirarla).
- **Ejercicio 2 · Reto: memoria + herramientas**: un chat con memoria que use al menos una tool en una conversacion de varios turnos.
  Parte de `03_memoria.py` y `04_tool.py`.
