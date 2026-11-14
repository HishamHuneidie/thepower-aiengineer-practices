FROM ollama/ollama

ENV OLLAMA_MODELS=/opt/ollama/models

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
    ollama pull gemma3:4b; \
    ollama pull llama3.2:3b

CMD ["serve"]