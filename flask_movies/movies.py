from flask import (
    Blueprint,
    abort,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

import db

bp = Blueprint("movies", __name__)
MOVIE_URL = "/movies/<string(maxlength=19):movie_id>"
FORM_FIELDS = (
    ("title", "название фильма", 200),
    ("description", "описание фильма", 5000),
    ("director", "имя режиссёра", 120),
)


@bp.before_request
def require_login():
    if g.user is None:
        return redirect(url_for("auth.login"))


def parse_movie_id(movie_id):
    if movie_id.isascii() and movie_id.isdecimal():
        number = int(movie_id)
        if 1 <= number <= 2**63 - 1:
            return number
    abort(404, description="Фильм не найден.")


def read_movie_form():
    values = {}
    errors = []
    for field, label, limit in FORM_FIELDS:
        value = request.form.get(field, "").strip()
        if not value:
            errors.append(f"Введите {label}.")
        elif len(value) > limit:
            errors.append(f"Сократите {label} до {limit} символов.")
        elif "\x00" in value:
            errors.append(f"Проверьте {label}. Поле содержит недопустимый символ.")
        values[field] = value
    return values, errors


@bp.get("/")
def index():
    query = request.args.get("q", "").strip()
    sort = request.args.get("sort", "")
    movies = db.list_movies(g.user["id"])
    if query:
        search = query.casefold()
        movies = [movie for movie in movies if search in movie["title"].casefold()]
    if sort == "title":
        movies.sort(key=lambda movie: movie["title"].casefold())
    return render_template("index.html", movies=movies, query=query, sort=sort)


@bp.get(MOVIE_URL)
def detail(movie_id):
    movie = db.get_movie(g.user["id"], parse_movie_id(movie_id))
    if movie is None:
        abort(404, description="Фильм не найден.")
    return render_template("detail.html", movie=movie)


@bp.route("/movies/add", methods=["GET", "POST"])
def add_movie():
    if request.method == "POST":
        values, errors = read_movie_form()
        if errors:
            return render_template("add.html", form=request.form, errors=errors), 400

        db.create_movie(g.user["id"], **values)
        return redirect(url_for("movies.index"))

    return render_template("add.html", form={})


@bp.route(MOVIE_URL + "/edit", methods=["GET", "POST"])
def edit_movie(movie_id):
    movie_id = parse_movie_id(movie_id)
    user_id = g.user["id"]
    movie = db.get_movie(user_id, movie_id)
    if movie is None:
        abort(404, description="Фильм не найден.")

    if request.method == "POST":
        values, errors = read_movie_form()
        if errors:
            return render_template(
                "edit.html", movie=movie, form=request.form, errors=errors
            ), 400

        if not db.update_movie(user_id, movie_id, **values):
            abort(404, description="Фильм не найден.")
        return redirect(url_for("movies.detail", movie_id=movie_id))

    return render_template("edit.html", movie=movie, form=movie)


@bp.post(MOVIE_URL + "/delete")
@bp.delete(MOVIE_URL)
def delete_movie(movie_id):
    if not db.delete_movie(g.user["id"], parse_movie_id(movie_id)):
        abort(404, description="Фильм не найден.")
    if request.method == "DELETE":
        return "", 204
    return redirect(url_for("movies.index"))
