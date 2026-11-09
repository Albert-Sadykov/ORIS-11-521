import itertools
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

notes = []
note_ids = itertools.count(1)


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


@app.get("/")
def index():
    return "<h1>Гостевая книга</h1>"


@app.get("/notes")
def list_notes():
    pagination = get_pagination()
    if pagination is None:
        return jsonify(error="invalid pagination"), 400

    author = request.args.get("author")
    result = notes if author is None else [note for note in notes if note["author"] == author]
    start = pagination["offset"]
    return jsonify(result[start:start + pagination["limit"]])


@app.post("/notes")
def create_note():
    data = get_note_data(request.get_json(silent=True), ("author", "text"))
    if data is None:
        return jsonify(error="fields 'author' and 'text' (non-empty strings) are required"), 400
    note = {"id": next(note_ids), **data}
    notes.append(note)
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
    return jsonify(note)


@app.delete("/notes/<int:note_id>")
def delete_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)
    notes.remove(note)
    return "", 204

@app.errorhandler(404)
def not_found(error):
    return jsonify(error="not found"), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify(error="method not allowed"), 405

if __name__ == "__main__":
    app.run(debug=True)
