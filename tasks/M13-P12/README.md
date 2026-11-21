# M13-P12 · Sesión 12 · Deep Research + Multimodal

Asistente con **LangGraph** que interpreta una imagen y un audio con Gemini, recuerda la conversación por
`thread_id` (checkpointer en Postgres), consulta una herramienta propia de solo lectura, lanza una
investigación asíncrona con **Gemini Deep Research (Interactions API)** y responde con voz (**Gemini TTS**).

Caso ficticio: un alumno de la academia Nube manda una **captura de error** (Error 403, incidencia
`SOP-10427`) y una **nota de voz** pidiendo el estado de su incidencia.

## Grafo

```
START → prepare → decide ─┬─ direct ─────────────────────────┐
                          ├─ tool (get_ticket) ──────────────┤
                          ├─ start_research → poll_research ─┤
                          └─ clarify ────────────────────────→ respond → speak → END
```

| Nodo | Qué hace |
|---|---|
| `prepare` | Imagen y audio a texto con `MULTIMODAL_MODEL_ID`. El audio se normaliza a WAV y se rechaza si supera 30 s. En el estado solo se guardan **referencias** de MinIO y **texto**. |
| `decide` | El modelo propone la ruta con salida estructurada y la aplicación la valida (por ejemplo, `tool` sin ticket pasa a `clarify`). |
| `direct` | Recupera contexto del RAG de la academia (las prácticas anteriores). |
| `tool` | `get_ticket(ticket_id)`: solo lectura (`MappingProxyType`), valida el formato `SOP-#####` y devuelve solo los campos permitidos. |
| `start_research` | `client.interactions.create(agent=DEEP_RESEARCH_AGENT_ID, input=..., background=True)` y guarda `interaction_id`. Si el hilo ya tiene una investigación pendiente, **no crea otra**. |
| `poll_research` | `client.interactions.get(id=interaction_id)` como mucho `RESEARCH_MAX_POLLS` veces, cada `RESEARCH_POLL_SECONDS`. Maneja `completed`, `failed`/`cancelled`/`incomplete`/`budget_exceeded`, `requires_action` y la espera agotada. Dejar de consultar **no cancela** la tarea remota. |
| `respond` | Respuesta final y un texto de 3 frases como máximo para la voz. |
| `speak` | `TTS_MODEL_ID` devuelve PCM, que se envuelve en WAV y se guarda en MinIO y en `evidence/tts/` junto al texto exacto enviado. |

**Presupuesto:** `RESEARCH_MAX_REAL_RUNS=1`. Cuando ya existe una investigación real (en la BD o en
`evidence/research/*.json`), se reutiliza y la respuesta indica que es una *ejecución anterior*.
Los fallos se pueden **simular** sin llamar a Google; la simulación nunca cuenta como investigación real.

## Puesta en marcha

1. Copia `.env.example` a `.env` y pon tu `GEMINI_API_KEY` (de Gemini API, no las credenciales de Google Cloud):

   ```bash
   cp .env.example .env
   ```

2. Arranca los contenedores:

   ```bash
   make start
   ```

   Ollama ya no se usa. Si quedó el contenedor antiguo, bórralo con:

   ```bash
   docker compose -p thepower-course-m13-p12 up -d --remove-orphans
   ```

## Demo y evidencias

```bash
make inputs           # genera inputs/captura_error.png (Pillow) y inputs/nota_voz.wav (Gemini TTS, < 30 s)
make demo             # imagen + audio → herramienta, memoria en hilo A, aislamiento en hilo B, validación, RAG
make demo-simulate    # fallo simulado y espera agotada (mismo interaction_id al volver a consultar)
make demo-research    # UNA investigación real; sigue consultando hasta 30 min. Repetirlo la reutiliza
make research-status  # tabla research_jobs
```

También funciona desde la web (`http://localhost:8000`), con un campo `thread_id` y la opción
«Responder con voz». El estado del checkpointer de un hilo se puede ver en `GET /threads/{thread_id}/state`.

Todo queda en `evidence/`:

| Requisito | Evidencia |
|---|---|
| Comprensión de imagen y audio | `demo_base_*.md` (turno 1: transcripción, lectura de la imagen y respuesta que usa ambas) |
| Voz | `tts/*.wav` y `tts/*.txt` (el texto exacto enviado al TTS) |
| Memoria separada | `state_demo-a-*.json` y `state_demo-b-*.json`, más los turnos 2 y 3 de la demo |
| Herramienta | `traces/*.jsonl` (`tool_call` con `args`, `ok`, `result`/`error`) |
| Investigación | `research/<interaction_id>.json` (id, fecha, estado, informe, fuentes, uso) y `demo_research_*.md` |
| Límites de ejecución | `demo_simulate_*.md` (fallo, espera agotada y el mismo id) |

## Configuración

| Variable | Por defecto |
|---|---|
| `GEMINI_API_KEY` | (obligatoria, en `.env`) |
| `MULTIMODAL_MODEL_ID` | `gemini-3.8-flash` |
| `TTS_MODEL_ID` / `TTS_VOICE` | `gemini-3.8-flash-lite-tts` / `Kore` |
| `DEEP_RESEARCH_AGENT_ID` | `deep-research-preview-04-2026` |
| `RESEARCH_MAX_REAL_RUNS` | `1` |
| `RESEARCH_MAX_POLLS` / `RESEARCH_POLL_SECONDS` | `6` / `10` (como mucho 1 min de espera por turno) |
| `AUDIO_MAX_SECONDS` | `30` |
