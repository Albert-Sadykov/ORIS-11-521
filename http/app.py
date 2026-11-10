import itertools
import json
from pathlib import Path

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

notes_file = Path(__file__).with_name("notes.json")


def load_notes():
    if not notes_file.exists():
        return []

    with notes_file.open(encoding="utf-8") as file:
        loaded_notes = json.load(file)
    for note in loaded_notes:
        note.setdefault("likes", 0)
    return loaded_notes


def save_notes():
    with notes_file.open("w", encoding="utf-8") as file:
        json.dump(notes, file, ensure_ascii=False, indent=2)


notes = load_notes()
note_ids = itertools.count(max((note["id"] for note in notes), default=0) + 1)


def find_note(note_id):
    return next((n for n in notes if n["id"] == note_id), None)


def get_note_data(data, fields):
    if not isinstance(data, dict):
        return None

    values = {}
    for field in fields:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return None
        values[field] = value.strip()
    return values


def get_pagination():
    values = {}
    for name, default, minimum, maximum in (
        ("limit", 10, 1, 100),
        ("offset", 0, 0, None),
    ):
        value = request.args.get(name, default)
        try:
            value = int(value)
        except (TypeError, ValueError):
            return None
        if value < minimum or (maximum is not None and value > maximum):
            return None
        values[name] = value
    return values


def get_sorting():
    sort = request.args.get("sort", "id")
    order = request.args.get("order", "asc")
    if sort not in {"id", "likes"} or order not in {"asc", "desc"}:
        return None
    return sort, order


@app.get("/")
def index():
    return "<h1>Гостевая книга</h1>"


@app.get("/notes")
def list_notes():
    pagination = get_pagination()
    if pagination is None:
        return jsonify(error="invalid pagination"), 400

    sorting = get_sorting()
    if sorting is None:
        return jsonify(error="invalid sort or order"), 400

    author = request.args.get("author")
    result = notes if author is None else [note for note in notes if note["author"] == author]
    sort, order = sorting
    result = sorted(result, key=lambda note: note[sort], reverse=order == "desc")
    start = pagination["offset"]
    return jsonify(result[start:start + pagination["limit"]])


@app.post("/notes")
def create_note():
    data = get_note_data(request.get_json(silent=True), ("author", "text"))
    if data is None:
        return jsonify(error="fields 'author' and 'text' (non-empty strings) are required"), 400
    note = {"id": next(note_ids), "likes": 0, **data}
    notes.append(note)
    save_notes()
    return jsonify(note), 201


@app.get("/notes/<int:note_id>")
def get_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)
    return jsonify(note)


@app.put("/notes/<int:note_id>")
def replace_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)

    data = get_note_data(request.get_json(silent=True), ("author", "text"))
    if data is None:
        return jsonify(error="fields 'author' and 'text' (non-empty strings) are required"), 400
    note.update(data)
    save_notes()
    return jsonify(note)


@app.patch("/notes/<int:note_id>")
def update_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {"text"}:
        return jsonify(error="field 'text' (non-empty string) is required"), 400
    data = get_note_data(data, ("text",))
    if data is None:
        return jsonify(error="field 'text' (non-empty string) is required"), 400
    note.update(data)
    save_notes()
    return jsonify(note)


@app.post("/notes/<int:note_id>/like")
def like_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)
    note["likes"] += 1
    save_notes()
    return jsonify(note)


@app.delete("/notes/<int:note_id>")
def delete_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)
    notes.remove(note)
    save_notes()
    return "", 204


@app.delete("/notes")
def delete_notes_by_author():
    author = request.args.get("author")
    if author is None or not author.strip():
        return jsonify(error="non-empty query parameter 'author' is required"), 400

    author = author.strip()
    deleted = sum(note["author"] == author for note in notes)
    notes[:] = [note for note in notes if note["author"] != author]
    save_notes()
    return jsonify(deleted=deleted)


@app.get("/authors")
def list_authors():
    authors = {}
    for note in notes:
        stats = authors.setdefault(note["author"], {"notes": 0, "likes": 0})
        stats["notes"] += 1
        stats["likes"] += note["likes"]
    return jsonify([
        {"author": author, **authors[author]}
        for author in sorted(authors)
    ])


@app.errorhandler(404)
def not_found(error):
    return jsonify(error="not found"), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify(error="method not allowed"), 405

if __name__ == "__main__":
    app.run(debug=True)
