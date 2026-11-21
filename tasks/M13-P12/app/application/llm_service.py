"""
Service with LLM utils (Gemini)
- Image to text (MULTIMODAL_MODEL_ID)
- Audio to text (MULTIMODAL_MODEL_ID)
- Route decision and final answer
- Text to speech (TTS_MODEL_ID)
"""

import re
from typing import Literal

from google.genai import types
from pydantic import BaseModel, Field

from app.domain.entities import Audio, Image, Message
from app.infrastructure.gemini import (
    AUDIO_MAX_SECONDS,
    MULTIMODAL_MODEL_ID,
    TTS_MODEL_ID,
    TTS_VOICE,
    get_client,
    normalize_audio,
    pcm_to_wav,
)

Route = Literal["direct", "tool", "research", "clarify"]


class RouteDecision(BaseModel):
    route: Route = Field(description="direct, tool, research o clarify")
    ticket_id: str | None = Field(default=None, description="Identificador de incidencia tal cual aparece (p. ej. SOP-10427)")
    research_question: str | None = Field(default=None, description="Pregunta autocontenida para Deep Research")
    reason: str = Field(description="Motivo breve de la ruta elegida")


class AnswerDraft(BaseModel):
    answer: str = Field(description="Respuesta completa para el chat")
    speech: str = Field(description="Resumen hablado de una a tres frases, sin URLs ni listas")


ROUTER_SYSTEM = """
Eres el planificador de un asistente de soporte de la academia Nube (plataforma CampusNube).
Decides la ruta del turno actual. Rutas:
- tool: el usuario pregunta por el estado, fecha, prioridad o detalle de una incidencia/ticket.
  Herramienta disponible: get_ticket(ticket_id) de solo lectura. Formato válido: SOP- y cinco cifras.
  Si el identificador no está en el turno, búscalo en el historial de ESTA conversación o en el campo "Ticket conocido".
- research: el usuario pide investigar, buscar normativa, derechos o información externa que exige fuentes,
  o pregunta cómo va una investigación ya iniciada. research_question debe ser autocontenida y en español.
- clarify: falta un dato imprescindible (por ejemplo, pregunta por "mi ticket" y no hay ningún identificador
  en el turno, en el historial ni en "Ticket conocido"), o la imagen y el audio se contradicen.
- direct: saludo, pregunta general sobre la academia o algo que se responde con el contexto disponible.
Nunca inventes identificadores. Devuelve solo el JSON pedido.
"""

ANSWER_SYSTEM = """
Eres el asistente de soporte de la academia Nube. Respondes en español, con tono claro y breve.
Reglas:
- Usa solo la evidencia proporcionada (historial, imagen, audio, herramienta, contexto o informe).
- Si hay imagen y audio en el turno, combina explícitamente la información de ambos.
- No inventes datos. Si algo falta o no se ha podido verificar, dilo.
- "answer": respuesta para el chat (máximo 120 palabras salvo que resumas un informe).
- "speech": de una a tres frases para leer en voz alta, sin URLs, sin listas, sin markdown.
"""


def limit_sentences(text: str, max_sentences: int = 3) -> str:
    """Asegura que el texto que va al TTS tenga como mucho tres frases."""
    clean = re.sub(r"https?://\S+", "", text or "").replace("*", "").strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
    return " ".join(sentences[:max_sentences])


class LLMService:

    def _generate_json(self, system: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
        response = get_client().models.generate_content(
            model=MULTIMODAL_MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0,
            ),
        )
        if response.parsed is not None:
            return response.parsed
        return schema.model_validate_json(response.text)

    def read_audio(self, audio: Audio) -> str:
        """Transcribe el audio con Gemini. Rechaza audios de más de AUDIO_MAX_SECONDS."""

        wav_bytes, seconds = normalize_audio(audio.getvalue())
        if seconds > AUDIO_MAX_SECONDS + 0.5:
            raise ValueError(f"El audio dura {seconds:.1f} s; el máximo es {AUDIO_MAX_SECONDS:.0f} s")

        response = get_client().models.generate_content(
            model=MULTIMODAL_MODEL_ID,
            contents=[
                types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
                "Transcribe literalmente esta nota de voz en su idioma original. "
                "Devuelve solo la transcripción, sin comentarios. Si no se entiende, devuelve una cadena vacía.",
            ],
            config=types.GenerateContentConfig(temperature=0),
        )

        return (response.text or "").strip()

    def read_image(self, image: Image) -> str:
        """Describe la imagen y transcribe su texto con Gemini."""

        response = get_client().models.generate_content(
            model=MULTIMODAL_MODEL_ID,
            contents=[
                types.Part.from_bytes(data=image.getvalue(), mime_type=getattr(image, "mime_type", "image/png")),
                "Analiza esta captura. Primero transcribe literalmente todo el texto visible "
                "(códigos de error, identificadores de incidencia, fechas). Después describe en una frase "
                "qué muestra. Formato:\nTexto: ...\nDescripción: ...",
            ],
            config=types.GenerateContentConfig(temperature=0),
        )

        return (response.text or "").strip()

    def decide_route(self, conversation: str, turn: str, known_ticket: str | None, research_info: str) -> RouteDecision:
        """El modelo propone la ruta; el grafo valida la propuesta después."""

        prompt = f"""
Historial de ESTA conversación (más antiguo primero):
{conversation or '(vacío)'}

Ticket conocido en esta conversación: {known_ticket or 'ninguno'}
Investigación de esta conversación: {research_info}

Turno actual:
{turn}
"""
        return self._generate_json(ROUTER_SYSTEM, prompt, RouteDecision)

    def compose_answer(self, route: str, conversation: str, turn: str, evidence: str) -> AnswerDraft:
        prompt = f"""
Ruta elegida: {route}

Historial de esta conversación:
{conversation or '(vacío)'}

Turno actual:
{turn}

Evidencia disponible:
{evidence or '(ninguna)'}
"""
        draft: AnswerDraft = self._generate_json(ANSWER_SYSTEM, prompt, AnswerDraft)
        draft.speech = limit_sentences(draft.speech or draft.answer)
        return draft

    def generate_audio(self, text: str) -> Audio:
        """Convierte un texto de hasta tres frases a WAV con Gemini TTS."""

        response = get_client().models.generate_content(
            model=TTS_MODEL_ID,
            contents=text,  # solo el texto: el modelo lee en voz alta cualquier instrucción que se añada
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=TTS_VOICE),
                    ),
                ),
            ),
        )

        part = response.candidates[0].content.parts[0]
        audio = Audio(pcm_to_wav(part.inline_data.data, part.inline_data.mime_type))
        audio.seek(0)
        return audio

    def formulate(self, message: Message) -> str:
        """Texto del turno con su origen: mensaje, nota de voz e imagen."""

        prompt = f"Mensaje escrito: {message.text or '(sin texto)'}"

        if message.audio_transcript:
            prompt += f"\nNota de voz (transcripción): {message.audio_transcript}"

        if message.image_transcript:
            prompt += f"\nCaptura (texto y descripción): {message.image_transcript}"

        return prompt
