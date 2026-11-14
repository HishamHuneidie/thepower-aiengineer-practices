#!/bin/sh
# Arranca el servidor de Ollama en segundo plano y, cuando responde, lanza FastAPI.
set -eu

ollama serve &

attempts=0
until ollama list >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 30 ]; then
        echo "Ollama no ha arrancado tras 30 segundos" >&2
        exit 1
    fi
    sleep 1
done

echo "Ollama listo. Arrancando FastAPI." >&2

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
