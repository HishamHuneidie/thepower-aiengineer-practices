# observability-basics · Master AI Engineer · Sesion 3

Observabilidad del agente de soporte de la Sesion 2 (LangGraph + tool `consulta_pedido`) con **LangSmith** y **LangFuse**.
El agente no se toca: vive en `agente.py` y no sabe nada de ninguna de las dos herramientas.
Coste: 0 EUR (modelo local con Ollama + planes gratuitos de LangSmith y LangFuse Cloud).

## Puesta en marcha
1. Ollama con el modelo descargado: `ollama pull llama3.1`
2. Crea el entorno: `python -m venv .venv`, activalo e instala: `pip install -r requirements.txt`
3. Crea cuenta gratuita en **smith.langchain.com** y en **cloud.langfuse.com** y genera sus API keys
4. Copia `.env.example` como `.env` y pega tus claves. **Nunca subas el `.env` a git.**

## Los conceptos
- **Traza (trace)**: una ejecucion completa, una peticion del usuario.
- **Span**: un paso dentro de la traza (un nodo del grafo, una tool).
- **Generation**: una llamada al LLM, con tokens, coste y latencia.
- **Prompt management**: el prompt vive fuera del codigo, versionado; el codigo lo pide por nombre y etiqueta (`production`).
- **Evaluacion**: un dataset de ejemplos + una tarea + evaluadores (reglas o LLM-as-a-judge) = metricas comparables.

## Los pasos
| Archivo | Que demuestra |
|---|---|
| `01_langsmith.py` | LangSmith solo con variables de entorno: el agente sin tocar |
| `02_langfuse.py` | LangFuse con `@observe` + `CallbackHandler`: trazas, spans y generations |
| `03a_crear_prompts.py` | Guarda el prompt `chatbot-soporte` en dos versiones (v1 production, v2 staging) |
| `03_prompt_management.py` | Carga el prompt por nombre: la version la decide LangFuse |
| `03b_promocionar_v2.py` | Mueve `production` a la v2 sin tocar codigo (en la web: *Promote*) |
| `04_evaluacion.py` | Dataset de 5 preguntas + evaluador por regla + juez LLM; deja el detalle en `detalle_evaluacion.txt` |
| `05_comparativa.py` | La misma ejecucion trazada a la vez en LangSmith y LangFuse |

## Extras (variaciones vistas en clase)
- `extras/paso2_precio_modelo.py` · precio de referencia para llama3.1: LangFuse calcula el coste
- `extras/paso3_rollback.py` · volver a la v1 del prompt en un segundo
- `extras/paso4_comparar_prompts.py` · un experimento por version del prompt, comparables en la web

## Ejercicios para casa
- **Ejercicio 1 · Pon lupa a tu cadena con LangFuse** (basico, 1 h). Solucion: `soluciones/ejercicio1_lupa_langfuse.py`
- **Ejercicio 2 · Reto**: grafo instrumentado en las dos herramientas + prompt versionado + dataset de evaluacion.

## Notas
- `LANGFUSE_HOST` debe llevar `https://` delante; si no, falla con "missing protocol".
- La integracion de LangFuse con LangChain necesita el paquete `langchain` (ya esta en requirements.txt).
- En las organizaciones de LangFuse creadas desde septiembre de 2026, los "dataset runs" se llaman **Experiments**.
- Un juez LLM pequeno (llama3.1 8B) no es fiable: compara siempre sus veredictos con una revision humana.
