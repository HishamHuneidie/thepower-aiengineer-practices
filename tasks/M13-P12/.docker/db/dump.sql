CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    text TEXT NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
    position BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE
);
