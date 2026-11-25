from hmac import compare_digest
from secrets import token_urlsafe

from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import db

bp = Blueprint("auth", __name__)


@bp.before_app_request
def load_user():
    user_id = session.get("user_id")
    g.user = db.get_user(user_id) if user_id is not None else None
    if user_id is not None and g.user is None:
        session.clear()


@bp.before_app_request
def check_csrf():
    if request.method in ("POST", "DELETE") and request.endpoint is not None:
        expected = session.get("csrf_token")
        submitted = request.headers.get("X-CSRF-Token") or request.form.get(
            "csrf_token", ""
        )
        if not expected or not compare_digest(expected.encode(), submitted.encode()):
            abort(400, description="Срок действия формы истёк. Откройте её заново.")


@bp.app_template_global()
def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = token_urlsafe(32)
    return session["csrf_token"]


def start_session(user_id):
    session.clear()
    session["user_id"] = user_id
    current_app.session_interface.regenerate(session)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user is not None:
        return redirect(url_for("movies.index"))

    if request.method == "POST":
        submitted = request.form.get("username", "")
        username = submitted.strip().casefold()
        password = request.form.get("password", "")

        errors = []
        if not 3 <= len(username) <= 32:
            errors.append("Имя пользователя должно содержать от 3 до 32 символов.")
        if not 8 <= len(password) <= 128 or not password.strip():
            errors.append("Введите пароль длиной от 8 до 128 символов.")
        if errors:
            return render_template(
                "auth.html", register=True, username=submitted, errors=errors
            ), 400

        user_id = db.create_user(username, generate_password_hash(password))
        if user_id is None:
            return render_template(
                "auth.html",
                register=True,
                username=submitted,
                errors=["Это имя пользователя уже занято."],
            ), 409

        start_session(user_id)
        return redirect(url_for("movies.index"))

    return render_template("auth.html", register=True)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("movies.index"))

    if request.method == "POST":
        submitted = request.form.get("username", "")
        username = submitted.strip().casefold()
        password = request.form.get("password", "")
        user = db.get_user_for_login(username)
        if (
            user is None
            or not 1 <= len(password) <= 128
            or not check_password_hash(user["password_hash"], password)
        ):
            return render_template(
                "auth.html",
                register=False,
                username=submitted,
                errors=["Неверное имя пользователя или пароль."],
            ), 401

        start_session(user["id"])
        return redirect(url_for("movies.index"))

    return render_template("auth.html", register=False)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
