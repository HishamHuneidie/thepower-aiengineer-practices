"""Grafo LangGraph del asistente multimodal.

START → prepare → decide ─┬─ direct ──────────────────────┐
                          ├─ tool ────────────────────────┤
                          ├─ start_research → poll_research┤
                          └─ clarify ─────────────────────→ respond → speak → END

- prepare: imagen y audio → texto (Gemini). En el estado solo hay referencias y texto, nunca binarios.
- decide: el modelo propone la ruta; el grafo valida la propuesta (p. ej. tool sin ticket → clarify).
- tool: get_ticket de solo lectura con argumentos validados.
- start_research / poll_research: Deep Research con background=True e interaction_id guardado.
- respond: respuesta final + texto de hasta tres frases para la voz.
- speak: TTS de Gemini si el usuario mandó audio o pidió voz.

El checkpointer (PostgresSaver) guarda el estado por thread_id: cada conversación tiene su memoria.
"""

import json
import os
import operator
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, TypedDict
from urllib.parse import urlparse

import psycopg
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

from app.application.audio_service import AudioService
from app.application.image_service import ImageService
from app.application.llm_service import LLMService, RouteDecision, limit_sentences
from app.application.rag_service import RAGService
from app.application.research_agents import DeepResearchService
from app.application.tools import ToolError, get_ticket
from app.infrastructure.files import locate_file_name, save_file

EVIDENCE_DIR = Path(os.getenv("EVIDENCE_DIR", "evidence"))
REPORT_CHARS_FOR_ANSWER = 100_000  # el informe completo (~80 000 caracteres sin URLs cabe de sobra)
MARKDOWN_LINK_URL = re.compile(r"\]\(https?://[^)\s]+\)")

audio_service = AudioService()
image_service = ImageService()
llm_service = LLMService()
rag_service = RAGService()
research_service = DeepResearchService()


def add_or_reset(left: list | None, right: list | None) -> list:
    """Reducer de errores: None en la entrada del turno los vacía; una lista los acumula."""
    if right is None:
        return []
    return (left or []) + right


class State(TypedDict, total=False):
    # --- Memoria del hilo: persiste entre turnos gracias al checkpointer ---
    history: Annotated[list[dict], operator.add]      # {"role", "content", "files"?}
    file_refs: Annotated[list[str], operator.add]     # referencias a MinIO, no binarios
    ticket_id: str | None                             # último ticket consultado con éxito
    interaction_id: str | None                        # id de Gemini Deep Research
    research_question: str | None
    remote_status: str | None                         # estado que devuelve Google
    local_status: str | None                          # pending | timeout | completed | failed | ...
    report: str | None
    sources: list[dict]
    research_meta: dict

    # --- Entradas del turno ---
    user_text: str
    image_ref: str | None
    audio_ref: str | None
    want_speech: bool
    research_simulation: str | None                   # None | "failed" | "timeout"

    # --- Resultado del turno ---
    vision_text: str
    transcript: str
    turn: str
    route: str
    route_reason: str
    tool_args: dict | None
    tool_call: dict | None
    research_request: str | None
    context: str
    answer: str
    speech_text: str
    speech_audio_ref: str | None
    errors: Annotated[list[str], add_or_reset]


TURN_RESET = {
    "vision_text": "",
    "transcript": "",
    "turn": "",
    "route": "",
    "route_reason": "",
    "tool_args": None,
    "tool_call": None,
    "research_request": None,
    "context": "",
    "answer": "",
    "speech_text": "",
    "speech_audio_ref": None,
    "errors": None,
}


def thread_of(config: RunnableConfig) -> str:
    return config["configurable"]["thread_id"]


def history_text(history: list[dict], limit: int = 12) -> str:
    lines = []
    for entry in history[-limit:]:
        who = "Usuario" if entry["role"] == "user" else "Asistente"
        lines.append(f"{who}: {entry['content'][:1500]}")
    return "\n".join(lines)


def research_summary(state: State) -> str:
    if not state.get("interaction_id"):
        return "ninguna"
    return (
        f"interaction_id={state['interaction_id']}, estado remoto={state.get('remote_status')}, "
        f"estado local={state.get('local_status')}, pregunta={state.get('research_question')!r}"
    )


# ============================================================== nodos

def prepare(state: State) -> dict:
    """Valida y lee los adjuntos. ValueError (formato, duración) corta el turno con un 400."""
    errors: list[str] = []
    vision_text = transcript = ""

    if state.get("image_ref"):
        try:
            vision_text = image_service.read(image_service.get(locate_file_name(state["image_ref"])))
        except ValueError:
            raise
        except Exception as error:
            errors.append(f"No se pudo analizar la imagen: {error}")

    if state.get("audio_ref"):
        try:
            transcript = audio_service.read(audio_service.get(locate_file_name(state["audio_ref"])))
        except ValueError:
            raise
        except Exception as error:
            errors.append(f"No se pudo transcribir el audio: {error}")

    turn = f"Mensaje escrito: {state.get('user_text') or '(sin texto)'}"
    if state.get("audio_ref"):
        turn += f"\nNota de voz (transcripción): {transcript or '(ilegible)'}"
    if state.get("image_ref"):
        turn += f"\nCaptura (texto y descripción): {vision_text or '(ilegible)'}"

    refs = [ref for ref in (state.get("image_ref"), state.get("audio_ref")) if ref]

    return {
        "vision_text": vision_text,
        "transcript": transcript,
        "turn": turn,
        "file_refs": refs,
        "history": [{"role": "user", "content": turn, "files": refs}],
        "errors": errors,
    }


def decide(state: State) -> dict:
    """El modelo propone; la aplicación valida la ruta y sus argumentos."""
    previous = state.get("history", [])[:-1]
    try:
        decision = llm_service.decide_route(
            history_text(previous), state["turn"], state.get("ticket_id"), research_summary(state)
        )
    except Exception as error:
        decision = RouteDecision(route="direct", reason=f"Planificador no disponible ({error}); respuesta directa")

    route, reason = decision.route, decision.reason
    update: dict = {}

    if route == "tool":
        ticket = decision.ticket_id or state.get("ticket_id")
        if not ticket:
            route, reason = "clarify", "Pregunta por una incidencia sin identificador en esta conversación"
        else:
            update["tool_args"] = {"ticket_id": ticket}

    if route == "research":
        request = decision.research_question
        if not request and not state.get("interaction_id"):
            route, reason = "clarify", "Pide investigar sin indicar qué"
        update["research_request"] = request

    print(f"[graph] route={route} reason={reason}", flush=True)
    return {**update, "route": route, "route_reason": reason}


def choose_route(state: State) -> str:
    return state["route"]


def direct(state: State) -> dict:
    """Contexto del RAG de la academia (si supera el threshold)."""
    question = " ".join(filter(None, [state.get("user_text"), state.get("transcript")])) or state["turn"]
    chunks = rag_service.retrieve([question])
    return {"context": "\n---\n".join(chunk.chunk.content for chunk in chunks[:3])}


def tool(state: State) -> dict:
    args = dict(state.get("tool_args") or {})
    call = {"name": "get_ticket", "args": args}
    update: dict = {}
    try:
        call["result"] = get_ticket(**args)
        call["ok"] = True
        update["ticket_id"] = call["result"]["ticket_id"]
    except (ToolError, TypeError) as error:
        call["ok"] = False
        call["error"] = str(error)
    print(f"[graph] tool_call={json.dumps(call, ensure_ascii=False)}", flush=True)
    return {**update, "tool_call": call}


def job_update(job) -> dict:
    return {
        "interaction_id": job.interaction_id,
        "research_question": job.question,
        "remote_status": job.remote_status,
        "local_status": job.local_status,
        "report": job.report,
        "sources": job.sources,
        "research_meta": {
            "agent": job.agent,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "poll_count": job.poll_count,
            "reused": job.reused,
            "simulated": job.simulated,
            "error": job.error,
            "origin_thread_id": job.thread_id,
        },
    }


def start_research(state: State, config: RunnableConfig) -> dict:
    """Crea la investigación una sola vez. Si hay una pendiente en el hilo, no crea otra."""
    if state.get("interaction_id") and state.get("local_status") in ("pending", "timeout"):
        return {}

    question = state.get("research_request") or state.get("research_question")
    try:
        job = research_service.start(question, thread_of(config), simulate=state.get("research_simulation"))
    except Exception as error:
        return {
            "local_status": "create_failed",
            "errors": [f"No se pudo crear la investigación: {error}. Si llegó a enviarse, el resultado es desconocido."],
        }
    return job_update(job)


def poll_research(state: State) -> dict:
    """Consulta el mismo interaction_id con intentos y tiempo máximos."""
    if state.get("local_status") == "create_failed" or not state.get("interaction_id"):
        return {}
    try:
        job = research_service.poll(state["interaction_id"])
    except Exception as error:
        return {"errors": [f"No se pudo consultar la investigación: {error}"]}
    return job_update(job)


def research_answer(state: State) -> tuple[str, str]:
    status = state.get("local_status")
    iid = state.get("interaction_id")
    meta = state.get("research_meta") or {}

    if status == "create_failed" or not iid:
        text = "No he podido iniciar la investigación. " + " ".join(state.get("errors") or [])
        return text, "No he podido iniciar la investigación."

    if status in ("pending", "timeout"):
        text = (
            f"La investigación sigue en curso (interaction_id {iid}, estado remoto {state.get('remote_status')}, "
            f"{meta.get('poll_count', 0)} consultas). He dejado de esperar en este turno, pero la tarea remota "
            "no se ha cancelado. Pregúntame «¿cómo va la investigación?» y consultaré el mismo identificador."
        )
        return text, "La investigación sigue en curso. Pregúntame más tarde y consultaré su estado."

    if status in ("failed", "requires_action"):
        text = (
            f"La investigación {iid} terminó con estado {state.get('remote_status')}"
            f"{' (simulado)' if meta.get('simulated') else ''}: {meta.get('error') or 'sin detalle'}. "
            "Conservo lo disponible y no la vuelvo a lanzar automáticamente."
        )
        return text, "La investigación no ha podido completarse. Conservo el identificador y lo disponible."

    # completed
    sources = state.get("sources") or []
    # Las URLs de Google son redirecciones larguísimas: en el chat se muestran los dominios citados
    # y la lista completa (con URLs) queda en evidence/research/<interaction_id>.json.
    domains = list(dict.fromkeys(s.get("title") or urlparse(s["url"]).netloc for s in sources))
    sources_text = ", ".join(domains[:20]) + (f" y {len(domains) - 20} más" if len(domains) > 20 else "")
    # Se quitan las URLs de los enlaces para que el informe completo quepa sin ruido.
    report = MARKDOWN_LINK_URL.sub("]", state.get("report") or "")
    evidence = (
        f"Informe COMPLETO de Gemini Deep Research:\n{report[:REPORT_CHARS_FOR_ANSWER]}\n\n"
        f"Dominios citados: {sources_text or '(sin fuentes)'}"
    )
    draft = llm_service.compose_answer(
        "research", history_text(state.get("history", [])[:-1]), state["turn"],
        evidence + "\n\nResume el informe en un máximo de 150 palabras, indicando límites y preguntas pendientes.",
    )
    origin = "ejecución anterior reutilizada, no se ha lanzado otra investigación" if meta.get("reused") else "ejecución de esta conversación"
    header = (
        f"\n\n— Gemini Deep Research ({origin}) · interaction_id {iid} · "
        f"creada {meta.get('created_at')} · resultado recogido {meta.get('completed_at')}"
    )
    answer = draft.answer + header + (
        f"\nFuentes ({len(sources)} citas): {sources_text}" if sources else "\nSin fuentes devueltas."
    )
    speech = draft.speech
    if meta.get("reused"):
        speech = limit_sentences("Uso una investigación anterior ya guardada. " + speech)
    return answer, speech


def respond(state: State) -> dict:
    route = state["route"]
    try:
        if route == "research":
            answer, speech = research_answer(state)
        else:
            if route == "tool":
                evidence = "Resultado de get_ticket: " + json.dumps(state.get("tool_call"), ensure_ascii=False)
            elif route == "clarify":
                evidence = f"Falta información: {state.get('route_reason')}. Pide al usuario el dato que falta."
            else:
                evidence = f"Base de conocimiento de la academia:\n{state.get('context') or '(sin coincidencias)'}"
            if state.get("errors"):
                evidence += "\nIncidencias del turno: " + "; ".join(state["errors"])

            draft = llm_service.compose_answer(route, history_text(state.get("history", [])[:-1]), state["turn"], evidence)
            answer, speech = draft.answer, draft.speech
    except Exception as error:
        answer = f"No he podido generar la respuesta ({error})."
        speech = "No he podido generar la respuesta."

    return {
        "answer": answer,
        "speech_text": limit_sentences(speech),
        "history": [{"role": "assistant", "content": answer}],
    }


def speak(state: State, config: RunnableConfig) -> dict:
    """TTS. Si falla, la respuesta en texto se conserva: el error es de esta etapa."""
    if not state.get("want_speech") or not state.get("speech_text"):
        return {}
    try:
        audio = audio_service.generate(state["speech_text"])
        wav = audio.getvalue()
        ref = save_file(wav, "audio/wav", "audio")

        tts_dir = EVIDENCE_DIR / "tts"
        tts_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        base = tts_dir / f"{stamp}_{thread_of(config)}"
        base.with_suffix(".wav").write_bytes(wav)
        base.with_suffix(".txt").write_text(state["speech_text"], encoding="utf-8")

        return {"speech_audio_ref": ref}
    except Exception as error:
        return {"errors": [f"No se pudo generar la voz: {error}"]}


# ============================================================== grafo

def build_graph() -> StateGraph:
    builder = StateGraph(State)
    builder.add_node("prepare", prepare)
    builder.add_node("decide", decide)
    builder.add_node("direct", direct)
    builder.add_node("tool", tool)
    builder.add_node("start_research", start_research)
    builder.add_node("poll_research", poll_research)
    builder.add_node("respond", respond)
    builder.add_node("speak", speak)

    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "decide")
    builder.add_conditional_edges("decide", choose_route, {
        "direct": "direct",
        "tool": "tool",
        "research": "start_research",
        "clarify": "respond",
    })
    builder.add_edge("direct", "respond")
    builder.add_edge("tool", "respond")
    builder.add_edge("start_research", "poll_research")
    builder.add_edge("poll_research", "respond")
    builder.add_edge("respond", "speak")
    builder.add_edge("speak", END)
    return builder


_graph = None
_graph_lock = threading.Lock()


def get_graph():
    """Grafo compilado con PostgresSaver (persiste entre reinicios, a diferencia de InMemorySaver)."""
    global _graph
    with _graph_lock:
        if _graph is None:
            connection = psycopg.connect(
                make_conninfo(
                    host=os.getenv("POSTGRES_HOST", "localhost"),
                    port=os.getenv("POSTGRES_PORT", "5432"),
                    dbname=os.getenv("POSTGRES_DB", "thepower"),
                    user=os.getenv("POSTGRES_USER", "thepower"),
                    password=os.getenv("POSTGRES_PASSWORD", "thepower"),
                ),
                autocommit=True,
                prepare_threshold=0,
                row_factory=dict_row,
            )
            checkpointer = PostgresSaver(connection)
            checkpointer.setup()
            _graph = build_graph().compile(checkpointer=checkpointer)
    return _graph


def run_turn(
    thread_id: str,
    text: str,
    image_ref: str | None = None,
    audio_ref: str | None = None,
    want_speech: bool = False,
    research_simulation: str | None = None,
) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    turn_input = {
        **TURN_RESET,
        "user_text": text,
        "image_ref": image_ref,
        "audio_ref": audio_ref,
        "want_speech": want_speech,
        "research_simulation": research_simulation,
    }
    return get_graph().invoke(turn_input, config)


def get_thread_state(thread_id: str) -> dict:
    """Estado guardado por el checkpointer para un hilo (evidencia de memoria separada)."""
    snapshot = get_graph().get_state({"configurable": {"thread_id": thread_id}})
    values = dict(snapshot.values or {})
    if values.get("report"):
        values["report"] = values["report"][:1500] + ("…" if len(values["report"]) > 1500 else "")
    return {"thread_id": thread_id, "next": list(snapshot.next), "values": values}
