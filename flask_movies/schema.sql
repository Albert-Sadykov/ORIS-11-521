BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS directors (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 120),
    UNIQUE (user_id, name),
    UNIQUE (user_id, id)
);

CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    director_id INTEGER NOT NULL,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
    description TEXT NOT NULL CHECK (length(description) BETWEEN 1 AND 5000),
    FOREIGN KEY (user_id, director_id) REFERENCES directors(user_id, id)
);

CREATE INDEX IF NOT EXISTS movies_user_id_idx ON movies (user_id, id);

COMMIT;
