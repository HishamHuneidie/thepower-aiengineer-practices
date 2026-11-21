CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    text TEXT,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
    position BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    audio_path TEXT,
    image_path TEXT,
    audio_transcript TEXT,
    image_transcript TEXT,
    response_in_audio_path TEXT
);

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    path TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    UNIQUE (document_id, position)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- S12: cada mensaje pertenece a una conversación (thread_id). El estado del grafo
-- lo guarda aparte el checkpointer de LangGraph (tablas checkpoint*).
ALTER TABLE messages ADD COLUMN IF NOT EXISTS thread_id TEXT NOT NULL DEFAULT 'default';
CREATE INDEX IF NOT EXISTS messages_thread_idx ON messages (thread_id, position);

-- S12: trabajos de Gemini Deep Research. interaction_id es el id que devuelve Google.
CREATE TABLE IF NOT EXISTS research_jobs (
    interaction_id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    question TEXT NOT NULL,
    agent TEXT NOT NULL,
    simulated BOOLEAN NOT NULL DEFAULT FALSE,
    remote_status TEXT NOT NULL,
    report TEXT,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    usage JSONB,
    error TEXT,
    poll_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);
