FROM python:3.12-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .docker/app/chunking.py ./chunking.py
COPY .docker/app/documents ./documents
COPY .docker/db/dump.sql ./schema.sql

EXPOSE 8000

CMD ["sh", "-c", "python chunking.py && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
