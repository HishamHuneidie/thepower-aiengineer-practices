FROM python:3.12-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Ollama se ejecuta dentro de este mismo contenedor.
# Los modelos se guardan en la imagen para no descargarlos en cada arranque.
ARG OLLAMA_MODEL=llama3.2:3b
ENV OLLAMA_MODEL=${OLLAMA_MODEL}
ENV OLLAMA_MODELS=/opt/ollama/models

# curl y ca-certificates para el instalador; zstd para descomprimir el paquete de Ollama.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates zstd \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

# Arranca Ollama temporalmente durante el build solo para descargar el modelo.
RUN set -eu; \
    ollama serve > /tmp/ollama.log 2>&1 & \
    server_pid=$!; \
    trap 'kill "$server_pid" 2>/dev/null || true' EXIT; \
    attempts=0; \
    until ollama list >/dev/null 2>&1; do \
        attempts=$((attempts + 1)); \
        if [ "$attempts" -ge 30 ]; then \
            cat /tmp/ollama.log; \
            exit 1; \
        fi; \
        sleep 1; \
    done; \
    ollama pull "$OLLAMA_MODEL"

COPY .docker/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .docker/app/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

COPY app ./app

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home appuser \
    && chown -R appuser:appuser /code /opt/ollama

USER appuser

EXPOSE 8000

CMD ["start.sh"]
