"""Gemini Deep Research mediante la Interactions API.

- start(): crea la investigación con background=True y guarda interaction_id.
  Respeta el presupuesto: como mucho RESEARCH_MAX_REAL_RUNS investigaciones reales; después
  reutiliza la última guardada (en BD o en evidence/research/*.json) indicándolo.
- poll(): consulta SIEMPRE el mismo interaction_id con un número y tiempo máximos de intentos.
  Maneja completed, failed/cancelled/incomplete/budget_exceeded, requires_action y espera agotada.
  Dejar de consultar no cancela la tarea remota: el id queda guardado para volver a consultar.
- Se pueden simular fallos (simulate="failed" | "timeout") sin llamar a Google. La simulación
  nunca sustituye a la investigación real ni cuenta para el presupuesto.
"""

import base64
import json
import os
import re
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.domain.entities import ResearchJob
from app.infrastructure.gemini import DEEP_RESEARCH_AGENT_ID, get_client
from app.infrastructure.postgres_repository import PostgresResearchRepository

RESEARCH_MAX_REAL_RUNS = int(os.getenv("RESEARCH_MAX_REAL_RUNS", "1"))
RESEARCH_MAX_POLLS = int(os.getenv("RESEARCH_MAX_POLLS", "6"))
RESEARCH_POLL_SECONDS = float(os.getenv("RESEARCH_POLL_SECONDS", "10"))
EVIDENCE_DIR = Path(os.getenv("EVIDENCE_DIR", "evidence")) / "research"

COMPLETED = {"completed"}
FAILED = {"failed", "cancelled", "incomplete", "budget_exceeded"}
NEEDS_ACTION = {"requires_action"}
TERMINAL = COMPLETED | FAILED | NEEDS_ACTION


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_status_for(remote_status: str) -> str:
    if remote_status in COMPLETED:
        return "completed"
    if remote_status in FAILED:
        return "failed"
    if remote_status in NEEDS_ACTION:
        return "requires_action"
    return "pending"


def extract_report(interaction) -> str:
    # Deep Research puede repartir el informe en varios model_output (p. ej. secciones 1-5 y 6-fin);
    # output_text solo devuelve el último, así que se unen todos en orden.
    parts: list[str] = []
    for step in getattr(interaction, "steps", None) or []:
        if getattr(step, "type", None) != "model_output":
            continue
        for content in getattr(step, "content", None) or []:
            if getattr(content, "text", None):
                parts.append(content.text.strip())
    if parts:
        return "\n\n".join(parts)

    return getattr(interaction, "output_text", None) or ""


def extract_sources(payload: object, report: str) -> list[dict]:
    """Busca citas (url/title) en toda la respuesta y, si no hay, URLs en el texto del informe."""
    found: dict[str, dict] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            url = node.get("url") or node.get("uri")
            if isinstance(url, str) and url.startswith("http") and url not in found:
                found[url] = {"title": node.get("title") or "", "url": url}
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    # Deep Research cierra el informe con una lista Markdown "N. [dominio](url)": de ahí sale el título.
    for title, url in re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", report or ""):
        entry = found.setdefault(url, {"title": "", "url": url})
        entry["title"] = entry["title"] or title.strip()

    walk(payload)
    for url in re.findall(r"https?://[^\s)\]>\"']+", report or ""):
        url = url.rstrip(".,;")
        found.setdefault(url, {"title": "", "url": url})

    return list(found.values())


class DeepResearchService:

    def __init__(self):
        self.repository = PostgresResearchRepository()

    # ------------------------------------------------------------------ crear
    def start(self, question: str, thread_id: str, simulate: str | None = None) -> ResearchJob:
        simulate = simulate or os.getenv("RESEARCH_SIMULATE") or None
        if simulate:
            return self._start_simulated(question, thread_id, simulate)

        previous = self.repository.latest_real() or self._import_saved_evidence()
        if previous and self.repository.count_real() >= RESEARCH_MAX_REAL_RUNS:
            # Presupuesto agotado: se reutiliza la ejecución anterior, sin crear otra.
            previous.reused = True
            previous.local_status = local_status_for(previous.remote_status)
            return previous

        interaction = get_client().interactions.create(
            agent=DEEP_RESEARCH_AGENT_ID,
            input=question,
            background=True,
        )

        job = ResearchJob(
            interaction_id=interaction.id,
            thread_id=thread_id,
            question=question,
            agent=DEEP_RESEARCH_AGENT_ID,
            remote_status=str(interaction.status or "in_progress"),
            created_at=now_iso(),
        )
        job.local_status = local_status_for(job.remote_status)
        self.repository.save(job)
        self._write_evidence(job)
        print(f"[research] creada interaction_id={job.interaction_id} thread={thread_id}", flush=True)
        return job

    # --------------------------------------------------------------- consultar
    def poll(self, interaction_id: str, max_polls: int | None = None, poll_seconds: float | None = None) -> ResearchJob:
        max_polls = RESEARCH_MAX_POLLS if max_polls is None else max_polls
        poll_seconds = RESEARCH_POLL_SECONDS if poll_seconds is None else poll_seconds

        job = self.repository.get(interaction_id)
        if job is None:
            raise ValueError(f"No hay ninguna investigación guardada con id {interaction_id}")

        if job.remote_status in TERMINAL:
            job.local_status = local_status_for(job.remote_status)
            return job

        if job.simulated:
            return self._poll_simulated(job, max_polls)

        for attempt in range(1, max_polls + 1):
            job.poll_count += 1
            try:
                # Siempre el mismo id: nunca se crea otra investigación al volver a consultar.
                interaction = get_client().interactions.get(id=job.interaction_id)
                job.remote_status = str(interaction.status)
                job.error = None
                print(f"[research] poll {attempt}/{max_polls} id={job.interaction_id} status={job.remote_status}", flush=True)

                if job.remote_status in COMPLETED:
                    job.report = extract_report(interaction)
                    job.sources = extract_sources(interaction.model_dump(mode="json"), job.report)
                    job.usage = interaction.usage.model_dump(mode="json") if getattr(interaction, "usage", None) else None
                    job.completed_at = now_iso()  # momento en que se recogió el resultado
                    self._save_output_image(job, interaction)
                elif job.remote_status in FAILED | NEEDS_ACTION:
                    errors = getattr(interaction, "errors", None) or []
                    job.error = "; ".join(str(e) for e in errors) or f"Estado remoto: {job.remote_status}"
                    job.report = extract_report(interaction) or None  # conservar lo disponible
            except Exception as error:  # red, cuota... se cuenta como intento
                job.error = f"Consulta fallida: {error}"
                print(f"[research] poll {attempt}/{max_polls} error: {error}", flush=True)

            self.repository.save(job)

            if job.remote_status in TERMINAL:
                job.local_status = local_status_for(job.remote_status)
                self._write_evidence(job)
                return job

            if attempt < max_polls:
                time.sleep(poll_seconds)

        # Espera local agotada. La tarea remota sigue su curso y el id queda guardado.
        job.local_status = "timeout"
        self._write_evidence(job)
        return job

    # ------------------------------------------------------------- simulación
    def _start_simulated(self, question: str, thread_id: str, mode: str) -> ResearchJob:
        job = ResearchJob(
            interaction_id=f"simulated-{mode}-{uuid4().hex[:8]}",
            thread_id=thread_id,
            question=question,
            agent=DEEP_RESEARCH_AGENT_ID,
            remote_status="in_progress",
            simulated=True,
            created_at=now_iso(),
        )
        job.local_status = "pending"
        self.repository.save(job)
        return job

    def _poll_simulated(self, job: ResearchJob, max_polls: int) -> ResearchJob:
        job.poll_count += max_polls
        if job.interaction_id.startswith("simulated-failed"):
            job.remote_status = "failed"
            job.error = "Fallo simulado para probar el manejo de errores"
            job.local_status = "failed"
        else:
            job.local_status = "timeout"  # sigue in_progress: espera agotada
        self.repository.save(job)
        self._write_evidence(job)
        return job

    # -------------------------------------------------------------- evidencias
    def _save_output_image(self, job: ResearchJob, interaction) -> None:
        """Deep Research puede adjuntar un gráfico (base64); se guarda junto al JSON."""
        image = getattr(interaction, "output_image", None)
        if not getattr(image, "data", None):
            return
        try:
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            extension = (image.mime_type or "image/png").split("/")[-1]
            (EVIDENCE_DIR / f"{job.interaction_id}.{extension}").write_bytes(base64.b64decode(image.data))
        except (OSError, ValueError) as error:
            print(f"[research] no se pudo guardar la imagen: {error}", flush=True)

    def _write_evidence(self, job: ResearchJob) -> None:
        try:
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            data = asdict(job)
            data["saved_at"] = now_iso()
            (EVIDENCE_DIR / f"{job.interaction_id}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as error:
            print(f"[research] no se pudo escribir la evidencia: {error}", flush=True)

    def _import_saved_evidence(self) -> ResearchJob | None:
        """Si la BD se borró, recupera la investigación real guardada en evidence/research."""
        if not EVIDENCE_DIR.exists():
            return None

        candidates = []
        for path in EVIDENCE_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not data.get("simulated") and data.get("interaction_id"):
                candidates.append(data)

        if not candidates:
            return None

        data = sorted(candidates, key=lambda d: d.get("created_at") or "")[-1]
        allowed = set(ResearchJob.__dataclass_fields__) - {"reused", "local_status"}
        job = ResearchJob(**{k: v for k, v in data.items() if k in allowed})
        self.repository.save(job)
        return job
