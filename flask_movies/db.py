import sqlite3

from flask import current_app, g

DEMO_MOVIES = (
    (
        "Назад в будущее",
        "Школьник Марти отправляется в прошлое на машине времени.",
        "Роберт Земекис",
    ),
    (
        "Унесённые призраками",
        "Девочка Тихиро попадает в мир духов и пытается спасти родителей.",
        "Хаяо Миядзаки",
    ),
    (
        "Интерстеллар",
        "Команда исследователей отправляется в космос искать новый дом для человечества.",
        "Кристофер Нолан",
    ),
)

MOVIE_SELECT = """
    SELECT m.id, m.title, m.description, d.name AS director
    FROM movies AS m
    JOIN directors AS d ON d.id = m.director_id AND d.user_id = m.user_id
"""


def get_db():
    if "db" not in g:
        database = sqlite3.connect(current_app.config["DATABASE"])
        g.db = database
        database.row_factory = sqlite3.Row
        database.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.register_error_handler(sqlite3.Error, render_database_error)
    with app.app_context(), app.open_resource("schema.sql", mode="r") as schema:
        get_db().executescript(schema.read())


def render_database_error(error):
    current_app.logger.error("SQLite operation failed", exc_info=error)
    code = getattr(error, "sqlite_errorcode", None)
    if code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
        return "База данных занята. Повторите попытку.", 503
    return "Произошла ошибка базы данных.", 500


def create_user(username, password_hash):
    with get_db() as database:
        cursor = database.execute(
            """
            INSERT INTO users (username, password_hash) VALUES (?, ?)
            ON CONFLICT (username) DO NOTHING
            """,
            (username, password_hash),
        )
        if not cursor.rowcount:
            return None
        user_id = cursor.lastrowid
        for title, description, director in DEMO_MOVIES:
            _insert_movie(database, user_id, title, description, director)
    return user_id


def get_user(user_id):
    cursor = get_db().execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


def get_user_for_login(username):
    cursor = get_db().execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (username,)
    )
    return cursor.fetchone()


def list_movies(user_id):
    cursor = get_db().execute(
        MOVIE_SELECT + "WHERE m.user_id = ? ORDER BY m.id", (user_id,)
    )
    return cursor.fetchall()


def get_movie(user_id, movie_id):
    cursor = get_db().execute(
        MOVIE_SELECT + "WHERE m.user_id = ? AND m.id = ?", (user_id, movie_id)
    )
    return cursor.fetchone()


def _get_or_create_director(database, user_id, name):
    database.execute(
        """
        INSERT INTO directors (user_id, name) VALUES (?, ?)
        ON CONFLICT (user_id, name) DO NOTHING
        """,
        (user_id, name),
    )
    return database.execute(
        "SELECT id FROM directors WHERE user_id = ? AND name = ?",
        (user_id, name),
    ).fetchone()["id"]


def _insert_movie(database, user_id, title, description, director):
    director_id = _get_or_create_director(database, user_id, director)
    database.execute(
        "INSERT INTO movies (user_id, director_id, title, description) VALUES (?, ?, ?, ?)",
        (user_id, director_id, title, description),
    )


def create_movie(user_id, title, description, director):
    with get_db() as database:
        _insert_movie(database, user_id, title, description, director)


def update_movie(user_id, movie_id, title, description, director):
    with get_db() as database:
        director_id = _get_or_create_director(database, user_id, director)
        cursor = database.execute(
            """
            UPDATE movies SET title = ?, description = ?, director_id = ?
            WHERE user_id = ? AND id = ?
            """,
            (title, description, director_id, user_id, movie_id),
        )
        if not cursor.rowcount:
            database.rollback()
            return False
    return True


def delete_movie(user_id, movie_id):
    with get_db() as database:
        cursor = database.execute(
            "DELETE FROM movies WHERE user_id = ? AND id = ?", (user_id, movie_id)
        )
    return cursor.rowcount == 1
