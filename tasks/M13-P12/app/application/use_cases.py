import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.application.graph import get_thread_state, run_turn
from app.domain.entities import Message
from app.domain.repositories import MessageRepository

EVIDENCE_DIR = Path(os.getenv("EVIDENCE_DIR", "evidence"))


def reply(message: Message, want_speech: bool = False, research_simulation: str | None = None) -> tuple[Message, dict]:
    """Ejecuta un turno del grafo LangGraph en el hilo del mensaje."""

    state = run_turn(
        thread_id=message.thread_id,
        text=message.text or "",
        image_ref=message.image_path,
        audio_ref=message.audio_path,
        want_speech=want_speech,
        research_simulation=research_simulation,
    )

    message.audio_transcript = state.get("transcript") or None
    message.image_transcript = state.get("vision_text") or None

    response = Message(
        role="assistant",
        thread_id=message.thread_id,
        text=state.get("answer") or "",
        response_in_audio_path=state.get("speech_audio_ref"),
    )

    return response, state


def send_message(
    message: Message,
    repository: MessageRepository,
    want_speech: bool = False,
    research_simulation: str | None = None,
) -> Message:
    # Si el usuario habla, el asistente también responde con voz.
    want_speech = want_speech or bool(message.audio_path)

    response, state = reply(message, want_speech, research_simulation)

    repository.save([message, response])
    write_trace(message, response, state)

    return response


def get_messages(repository: MessageRepository, thread_id: str) -> list[Message]:
    return repository.list_all(thread_id)


def get_state(thread_id: str) -> dict:
    return get_thread_state(thread_id)


def write_trace(message: Message, response: Message, state: dict) -> None:
    """Una línea JSON por turno en evidence/traces/<thread_id>.jsonl."""

    record = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "thread_id": message.thread_id,
        "input": {
            "text": message.text,
            "image_ref": message.image_path,
            "audio_ref": message.audio_path,
            "image_text": state.get("vision_text"),
            "audio_transcript": state.get("transcript"),
        },
        "route": state.get("route"),
        "route_reason": state.get("route_reason"),
        "tool_call": state.get("tool_call"),
        "research": {
            "interaction_id": state.get("interaction_id"),
            "remote_status": state.get("remote_status"),
            "local_status": state.get("local_status"),
            "meta": state.get("research_meta"),
        } if state.get("route") == "research" else None,
        "memory": {
            "ticket_id": state.get("ticket_id"),
            "history_len": len(state.get("history") or []),
            "file_refs": state.get("file_refs"),
        },
        "answer": response.text,
        "tts_text": state.get("speech_text") if response.response_in_audio_path else None,
        "tts_audio_ref": response.response_in_audio_path,
        "errors": state.get("errors"),
    }

    try:
        traces = EVIDENCE_DIR / "traces"
        traces.mkdir(parents=True, exist_ok=True)
        with open(traces / f"{message.thread_id}.jsonl", "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as error:
        print(f"[trace] no se pudo escribir: {error}", flush=True)
