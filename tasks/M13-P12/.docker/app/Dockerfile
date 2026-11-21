FROM python:3.12-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ffmpeg normaliza el audio (webm/ogg/m4a) a WAV y mide su duración antes de enviarlo a Gemini.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# PyTorch solo CPU (más ligero, sin dependencias de CUDA).
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.7.1

COPY .docker/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .docker/app/chunking.py   ./chunking.py
COPY .docker/app/threshold.py  ./threshold.py
COPY .docker/app/documents     ./documents
COPY .docker/app/assess        ./assess
COPY .docker/db/dump.sql       ./schema.sql

EXPOSE 8000

CMD ["sh", "-c", "python chunking.py && python threshold.py && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app"]