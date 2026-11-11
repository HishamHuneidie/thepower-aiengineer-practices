FROM python:3.14.4-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY .docker/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir runs
COPY 01_connect_to_mcp.py ./runs/01_connect_to_mcp.py
COPY colorize.py ./runs/colorize.py

COPY app ./app

EXPOSE 8000

CMD ["python", "-m", "app.main"]
