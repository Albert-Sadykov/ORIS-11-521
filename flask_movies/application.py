from pathlib import Path

from cachelib.file import FileSystemCache
from flask import Flask
from flask_session import Session

import auth
import db
import movies


def create_app(config=None):
    app = Flask(__name__)
    instance_path = Path(app.instance_path)
    app.config.from_mapping(
        DATABASE=instance_path / "movies.sqlite3",
        SESSION_TYPE="cachelib",
        SESSION_DIRECTORY=instance_path / "sessions",
        SESSION_COOKIE_NAME="movie_session",
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_PERMANENT=False,
        PERMANENT_SESSION_LIFETIME=8 * 60 * 60,
        MAX_CONTENT_LENGTH=128 * 1024,
    )
    app.config.from_prefixed_env()
    if config is not None:
        app.config.update(config)

    Path(app.config["DATABASE"]).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    app.config["SESSION_CACHELIB"] = FileSystemCache(
        cache_dir=str(app.config["SESSION_DIRECTORY"])
    )
    Session(app)

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(movies.bp)
    return app
