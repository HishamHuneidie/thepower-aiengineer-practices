"""Cliente de Gemini API y utilidades de audio.

La clave se lee de GEMINI_API_KEY (Gemini API / AI Studio), nunca del código.
"""

import io
import os
import re
import subprocess
import wave
from functools import lru_cache
from tempfile import TemporaryDirectory

from google import genai
from google.genai import types

MULTIMODAL_MODEL_ID = os.getenv("MULTIMODAL_MODEL_ID", "gemini-3.8-flash")
TTS_MODEL_ID = os.getenv("TTS_MODEL_ID", "gemini-3.8-flash-lite-tts")
TTS_VOICE = os.getenv("TTS_VOICE", "Kore")
DEEP_RESEARCH_AGENT_ID = os.getenv("DEEP_RESEARCH_AGENT_ID", "deep-research-preview-04-2026")
AUDIO_MAX_SECONDS = float(os.getenv("AUDIO_MAX_SECONDS", "30"))


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY. Cópiala en tasks/M13-P12/.env (ver .env.example).")
    # v1beta: el TTS (speech_config y los modelos *-tts) no existe en v1, que da 404/400.
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta"))


def normalize_audio(content: bytes) -> tuple[bytes, float]:
    """Convierte cualquier audio admitido (webm, ogg, m4a, mp3, wav) a WAV mono 16 kHz.

    Devuelve el WAV y su duración en segundos. Gemini no admite webm, que es lo que graba
    el navegador, así que se normaliza siempre con ffmpeg.
    """
    with TemporaryDirectory() as tmp:
        source, target = f"{tmp}/input", f"{tmp}/output.wav"
        with open(source, "wb") as file:
            file.write(content)
        result = subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", source, "-ac", "1", "-ar", "16000", target],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise ValueError("El audio no se puede leer: " + result.stderr.decode(errors="ignore")[:200])
        with open(target, "rb") as file:
            wav_bytes = file.read()

    with wave.open(io.BytesIO(wav_bytes)) as wav:
        seconds = wav.getnframes() / float(wav.getframerate())

    return wav_bytes, seconds


def pcm_to_wav(pcm: bytes, mime_type: str | None) -> bytes:
    """Gemini TTS devuelve PCM crudo (audio/L16;rate=24000). Se envuelve en un WAV."""
    if mime_type and "wav" in mime_type:
        return pcm

    rate_match = re.search(r"rate=(\d+)", mime_type or "")
    rate = int(rate_match.group(1)) if rate_match else 24000

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm)
    return buffer.getvalue()
