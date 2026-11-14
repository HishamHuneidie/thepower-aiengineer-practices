CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    text TEXT,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
    position BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    audio_path TEXT,
    image_path TEXT,
    audio_transcript TEXT,
    image_transcript TEXT
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
