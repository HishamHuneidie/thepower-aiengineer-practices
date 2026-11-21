"""Demo en terminal del caso ficticio (soporte de la academia Nube).

Uso (dentro del contenedor, ver Makefile):
    python -m app.demo --prepare-inputs     # genera inputs/captura_error.png y inputs/nota_voz.wav
    python -m app.demo                      # imagen + audio, herramienta, memoria en dos hilos
    python -m app.demo --simulate           # fallos simulados de la investigación (fallo y espera agotada)
    python -m app.demo --research           # UNA investigación real (o reutiliza la guardada)
    python -m app.demo --status             # estado de las investigaciones guardadas

Todo queda en evidence/: demo_<id>.md, traces/*.jsonl, tts/*.wav|txt, research/*.json, state_*.json.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from app.application.graph import EVIDENCE_DIR, get_thread_state
from app.application.use_cases import send_message
from app.domain.entities import Message
from app.infrastructure.files import initialize_storage, save_file
from app.infrastructure.postgres_repository import PostgresMessageRepository

INPUTS_DIR = Path("inputs")
IMAGE_PATH = INPUTS_DIR / "captura_error.png"
AUDIO_PATH = INPUTS_DIR / "nota_voz.wav"
AUDIO_SCRIPT = (
    "Hola, soy alumno del curso básico de Nube. Ayer por la tarde intenté entrar en la clase en directo "
    "y la plataforma me mostró el error de la captura. Ya abrí una incidencia con soporte. "
    "¿Me dices en qué estado está y qué puedo hacer mientras tanto para no perder la clase?"
)
RESEARCH_PROMPT = (
    "Investiga qué derechos tiene en España una persona consumidora que ha contratado un curso online "
    "y no puede acceder a las clases por un fallo técnico de la plataforma: normativa aplicable "
    "(por ejemplo, el Texto Refundido de la Ley General para la Defensa de los Consumidores y Usuarios), "
    "plazos razonables, opciones de reclamación y posibilidad de reembolso parcial. "
    "Prioriza fuentes oficiales (BOE, europa.eu, organismos de consumo) y cita las fuentes."
)

repository = PostgresMessageRepository()
log: list[str] = []


def out(line: str = "") -> None:
    print(line, flush=True)
    log.append(line)


# ------------------------------------------------------------------ entradas

def prepare_inputs(force: bool = False) -> None:
    INPUTS_DIR.mkdir(exist_ok=True)

    if force or not IMAGE_PATH.exists():
        from PIL import Image, ImageDraw, ImageFont

        image = Image.new("RGB", (1100, 620), "#f8fafc")
        draw = ImageDraw.Draw(image)
        big, mid, small = (ImageFont.load_default(size=s) for s in (40, 28, 22))
        draw.rectangle((0, 0, 1100, 80), fill="#1e3a8a")
        draw.text((32, 20), "CampusNube · Academia Nube", font=mid, fill="white")
        draw.rounded_rectangle((60, 130, 1040, 560), radius=18, fill="white", outline="#fca5a5", width=3)
        draw.text((100, 165), "Error 403 · Acceso denegado", font=big, fill="#b91c1c")
        lines = [
            "No tienes permiso para entrar en la clase en directo.",
            "Clase: Curso básico · jueves 19/11/2026 · 18:00",
            "Código técnico: ACC-403-LIVE",
            "",
            "Si el problema continúa, indica al equipo de soporte",
            "el número de incidencia: SOP-10427",
        ]
        for i, line in enumerate(lines):
            draw.text((100, 245 + i * 44), line, font=mid if line.startswith(("Código", "el número")) else small, fill="#1e293b")
        draw.text((32, 585), "Captura sintética para la práctica M13-P12 · datos ficticios", font=small, fill="#64748b")
        image.save(IMAGE_PATH)
        out(f"Imagen sintética creada: {IMAGE_PATH}")

    if force or not AUDIO_PATH.exists():
        from google.genai import types
        from app.infrastructure.gemini import TTS_MODEL_ID, get_client, normalize_audio, pcm_to_wav

        response = get_client().models.generate_content(
            model=TTS_MODEL_ID,
            contents=AUDIO_SCRIPT,  # solo el texto: el modelo lee en voz alta cualquier instrucción
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")),
                ),
            ),
        )
        part = response.candidates[0].content.parts[0]
        wav = pcm_to_wav(part.inline_data.data, part.inline_data.mime_type)
        _, seconds = normalize_audio(wav)
        if seconds > 30:
            raise RuntimeError(f"La nota de voz sintética dura {seconds:.1f} s (máximo 30)")
        AUDIO_PATH.write_bytes(wav)
        (INPUTS_DIR / "nota_voz.txt").write_text(AUDIO_SCRIPT, encoding="utf-8")
        out(f"Nota de voz sintética creada: {AUDIO_PATH} ({seconds:.1f} s)")


def upload(path: Path, mime: str, kind: str) -> str:
    return save_file(path.read_bytes(), mime, kind)


# ---------------------------------------------------------------------- turnos

def turn(thread_id: str, text: str, image: str | None = None, audio: str | None = None,
         speak: bool = False, simulate: str | None = None) -> Message:
    out(f"\n### [{thread_id}] Usuario")
    out(f"> {text or '(sin texto)'}" + (f"  \n> 📎 imagen {image}" if image else "") + (f"  \n> 🎤 audio {audio}" if audio else ""))

    started = time.monotonic()
    response = send_message(
        Message(role="user", thread_id=thread_id, text=text, image_path=image, audio_path=audio),
        repository,
        want_speech=speak,
        research_simulation=simulate,
    )
    state = get_thread_state(thread_id)["values"]

    out(f"\n**Ruta:** `{state.get('route')}` — {state.get('route_reason')}  ")
    if audio:
        out(f"**Transcripción del audio:** {state.get('transcript')}  ")
    if image:
        out(f"**Lectura de la imagen:** {(state.get('vision_text') or '').replace(chr(10), ' · ')}  ")
    if state.get("route") == "tool":
        out(f"**Herramienta:** `{json.dumps(state.get('tool_call'), ensure_ascii=False)}`  ")
    if state.get("route") == "research":
        meta = state.get("research_meta") or {}
        out(f"**Investigación:** interaction_id=`{state.get('interaction_id')}` remoto=`{state.get('remote_status')}` "
            f"local=`{state.get('local_status')}` consultas={meta.get('poll_count')} reutilizada={meta.get('reused')} "
            f"simulada={meta.get('simulated')}  ")
    if state.get("errors"):
        out(f"**Errores del turno:** {state.get('errors')}  ")
    out(f"\n### [{thread_id}] Asistente ({time.monotonic() - started:.1f} s)")
    out(response.text or "")
    if response.response_in_audio_path:
        out(f"\n🔊 Voz: `{response.response_in_audio_path}` · texto enviado al TTS: «{state.get('speech_text')}»")
    return response


def dump_state(thread_id: str) -> None:
    path = EVIDENCE_DIR / f"state_{thread_id}.json"
    path.write_text(json.dumps(get_thread_state(thread_id), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    out(f"Estado del checkpointer guardado en {path}")


# ----------------------------------------------------------------- escenarios

def scenario_base(run_id: str) -> None:
    thread_a, thread_b = f"demo-a-{run_id}", f"demo-b-{run_id}"
    image_ref = upload(IMAGE_PATH, "image/png", "image")
    audio_ref = upload(AUDIO_PATH, "audio/wav", "audio")

    out("\n## 1. Imagen + audio → herramienta (hilo A)")
    turn(thread_a, "Te mando la captura y una nota de voz.", image=image_ref, audio=audio_ref, speak=True)

    out("\n## 2. Memoria del hilo A: «esa incidencia» sin repetir el número")
    turn(thread_a, "¿Y cuándo se actualizó por última vez esa incidencia?")

    out("\n## 3. Hilo B: no ve nada del hilo A")
    turn(thread_b, "¿En qué estado está mi incidencia?")
    turn(thread_b, "¿Qué error aparecía en la captura que te envié?")

    out("\n## 4. Validación de argumentos de la herramienta (hilo B)")
    turn(thread_b, "Mi incidencia es la SOP-99999.")
    turn(thread_b, "Pues mira la incidencia ABC-1.")

    out("\n## 5. Pregunta directa con la base de conocimiento (hilo B)")
    turn(thread_b, "¿Cómo recupero la contraseña de CampusNube?", speak=True)

    dump_state(thread_a)
    dump_state(thread_b)


def scenario_simulate(run_id: str) -> None:
    out("\n## Fallos simulados de la investigación (no llaman a Google)")
    turn(f"demo-sim-failed-{run_id}", "Investiga la normativa de consumo sobre cursos online.", simulate="failed")
    turn(f"demo-sim-timeout-{run_id}", "Investiga la normativa de consumo sobre cursos online.", simulate="timeout")
    out("\n_Segunda consulta del hilo con espera agotada: usa el mismo interaction_id, no crea otro._")
    turn(f"demo-sim-timeout-{run_id}", "¿Cómo va la investigación?", simulate="timeout")


def scenario_research(run_id: str, wait_minutes: float, pause_seconds: float) -> None:
    thread = f"demo-research-{run_id}"
    out("\n## Investigación real con Gemini Deep Research")
    turn(thread, RESEARCH_PROMPT, speak=True)

    deadline = time.monotonic() + wait_minutes * 60
    while get_thread_state(thread)["values"].get("local_status") in ("pending", "timeout"):
        if time.monotonic() > deadline:
            out(f"\nEspera de la demo agotada ({wait_minutes} min). La tarea remota sigue; "
                f"vuelve a ejecutar `make demo-research` o pregunta en el hilo {thread}.")
            break
        time.sleep(pause_seconds)
        turn(thread, "¿Cómo va la investigación?", speak=True)

    dump_state(thread)


def show_status() -> None:
    from app.infrastructure.database import get_connection

    with get_connection() as connection:
        rows = connection.execute(
            """SELECT interaction_id, thread_id, simulated, remote_status, poll_count, created_at, completed_at,
                      jsonb_array_length(sources) AS sources, left(coalesce(error, ''), 120) AS error
               FROM research_jobs ORDER BY created_at"""
        ).fetchall()
    for row in rows:
        print(json.dumps(row, default=str, ensure_ascii=False))
    if not rows:
        print("No hay investigaciones guardadas.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prepare-inputs", action="store_true", help="solo genera las entradas sintéticas")
    parser.add_argument("--force-inputs", action="store_true", help="regenera las entradas aunque existan")
    parser.add_argument("--simulate", action="store_true", help="fallos simulados de la investigación")
    parser.add_argument("--research", action="store_true", help="investigación real (una sola vez; después se reutiliza)")
    parser.add_argument("--wait-minutes", type=float, default=30, help="espera máxima de la demo para la investigación")
    parser.add_argument("--pause-seconds", type=float, default=30, help="pausa entre turnos de seguimiento")
    parser.add_argument("--status", action="store_true", help="muestra las investigaciones guardadas")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    initialize_storage()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    prepare_inputs(force=args.force_inputs)
    if args.prepare_inputs:
        return

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out(f"# Demo M13-P12 · {run_id}")

    if args.simulate:
        scenario_simulate(run_id)
    elif args.research:
        scenario_research(run_id, args.wait_minutes, args.pause_seconds)
    else:
        scenario_base(run_id)

    kind = "simulate" if args.simulate else "research" if args.research else "base"
    report = EVIDENCE_DIR / f"demo_{kind}_{run_id}.md"
    report.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"\nInforme de la demo: {report}")


if __name__ == "__main__":
    main()
