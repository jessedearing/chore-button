import sqlite3
from flask import Flask, request, jsonify, g, render_template
from waitress import serve

app = Flask(__name__)
DB_PATH = "chores.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        _ = db.execute(
            """
            CREATE TABLE IF NOT EXISTS chores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                date TEXT
            )
            """
        )
        _ = db.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_chores_date on chores (date)
            """
        )


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/chores")
def list_chores():
    date = request.args.get("date")
    db = get_db()
    if date:
        rows = db.execute(
            "SELECT * FROM chores WHERE date = ? ORDER BY id", (date,)
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM chores ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/chores")
def add_chore():
    data = request.json or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    date = data.get("date")
    db = get_db()
    cur = db.execute("INSERT INTO chores (name, date) VALUES (?, ?)", (name, date))
    db.commit()
    return jsonify({"id": cur.lastrowid, "name": name, "done": 0, "date": date}), 201


@app.patch("/chores/<int:chore_id>")
def update_chore(chore_id):
    data = request.json or {}
    db = get_db()
    if "done" in data:
        db.execute(
            "UPDATE chores SET done = ? WHERE id = ?",
            (int(bool(data["done"])), chore_id),
        )
    if "name" in data:
        db.execute(
            "UPDATE chores SET name = ? WHERE id = ?", (data["name"].strip(), chore_id)
        )
    if "date" in data:
        db.execute("UPDATE chores SET date = ? WHERE id = ?", (data["date"], chore_id))
    db.commit()
    row = db.execute("SELECT * FROM chores WHERE id = ?", (chore_id,)).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@app.delete("/chores/<int:chore_id>")
def delete_chore(chore_id):
    db = get_db()
    db.execute("DELETE FROM chores WHERE id = ?", (chore_id,))
    db.commit()
    return "", 204


def run_app():
    init_db()
    serve(app, host="0.0.0.0", port=8080)
