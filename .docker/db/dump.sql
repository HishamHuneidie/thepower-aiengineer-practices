DROP TABLE IF EXISTS cars;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE cars (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    brand VARCHAR(80) NOT NULL,
    model VARCHAR(120) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 1886),
    owner_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE messages (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    question VARCHAR(120) NOT NULL,
    answer VARCHAR(120) NOT NULL,
    sender_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email) VALUES
    ('Ada Lovelace', 'ada@example.com'),
    ('Grace Hopper', 'grace@example.com'),
    ('Alan Turing', 'alan@example.com');

INSERT INTO cars (brand, model, year, owner_id) VALUES
    ('Seat', 'Ibiza', 2020, 1),
    ('Volkswagen', 'Golf', 2021, 1),
    ('Toyota', 'Corolla', 2022, 2),
    ('Ford', 'Focus', 2019, 2),
    ('Renault', 'Clio', 2018, 3),
    ('Peugeot', '208', 2023, 3),
    ('Honda', 'Civic', 2020, NULL),
    ('BMW', 'Serie 3', 2022, NULL),
    ('Audi', 'A3', 2021, 1),
    ('Tesla', 'Model 3', 2023, NULL);

INSERT INTO messages (question, answer, sender_id, sent_at) VALUES
    ('Hola', 'Que tal? En que te puedo ayudar?', 1, '2026-09-17 02:35:00');
