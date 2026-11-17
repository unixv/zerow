import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, jsonify, make_response, request, send_from_directory

app = Flask(__name__, static_folder="static")
DB = Path(os.environ.get("ZEROW_DB", "/opt/zerow/data/atrium.sqlite3"))
WIDTH, HEIGHT = 16, 11

@contextmanager
def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS players (
        token TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE COLLATE NOCASE,
        x INTEGER NOT NULL DEFAULT 8,
        y INTEGER NOT NULL DEFAULT 5,
        last_seen REAL NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        body TEXT NOT NULL,
        created REAL NOT NULL
    )""")
    con.commit()
    try:
        with con:
            yield con
    finally:
        con.close()

def identity(con):
    token = request.cookies.get("zerow_player", "")
    if not token or len(token) > 128:
        return None
    return con.execute("SELECT * FROM players WHERE token=?", (token,)).fetchone()

@app.after_request
def no_cache(resp):
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/health")
def health():
    with connect() as con:
        con.execute("SELECT 1")
    return {"status": "ok"}

@app.post("/api/join")
def join():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not re.fullmatch(r"[a-zA-Z0-9 _-]{2,18}", name):
        return jsonify(error="Use 2–18 letters, numbers, spaces, _ or -."), 400
    with connect() as con:
        existing = identity(con)
        if existing:
            if existing["name"].lower() == name.lower():
                con.execute("UPDATE players SET last_seen=? WHERE token=?", (time.time(), existing["token"]))
                return jsonify(name=existing["name"])
            return jsonify(error="You're already signed in as " + existing["name"] + "."), 409
        token = secrets.token_urlsafe(32)
        try:
            con.execute("INSERT INTO players(token,name,x,y,last_seen) VALUES(?,?,?,?,?)",
                        (token, name, 8, 5, time.time()))
        except sqlite3.IntegrityError:
            return jsonify(error="That name is already taken. Try another."), 409
    resp = make_response(jsonify(name=name))
    resp.set_cookie("zerow_player", token, max_age=60*60*24*90, httponly=True,
                    samesite="Lax", secure=request.is_secure)
    return resp

@app.get("/api/state")
def state():
    with connect() as con:
        player = identity(con)
        if not player:
            return jsonify(me=None, players=[], messages=[])
        now = time.time()
        con.execute("UPDATE players SET last_seen=? WHERE token=?", (now, player["token"]))
        people = [dict(row) for row in con.execute(
            "SELECT name,x,y FROM players WHERE last_seen>? ORDER BY name LIMIT 100", (now-40,))]
        lines = [dict(row) for row in con.execute(
            "SELECT id,name,body,created FROM (SELECT * FROM messages ORDER BY id DESC LIMIT 60) ORDER BY id")]
        return jsonify(me=player["name"], players=people, messages=lines, room="Lobby", width=WIDTH, height=HEIGHT)

@app.post("/api/move")
def move():
    data = request.get_json(silent=True) or {}
    x, y = data.get("x"), data.get("y")
    if type(x) is not int or type(y) is not int or not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        return jsonify(error="Invalid tile"), 400
    with connect() as con:
        player = identity(con)
        if not player:
            return jsonify(error="Choose a name first"), 401
        con.execute("UPDATE players SET x=?,y=?,last_seen=? WHERE token=?",
                    (x, y, time.time(), player["token"]))
    return jsonify(ok=True)

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    body = str(data.get("message", "")).strip()
    if not body or len(body) > 280 or any(ord(c) < 32 and c not in "\n\t" for c in body):
        return jsonify(error="Message must be 1–280 characters"), 400
    with connect() as con:
        player = identity(con)
        if not player:
            return jsonify(error="Choose a name first"), 401
        now = time.time()
        last = con.execute("SELECT created FROM messages WHERE name=? ORDER BY id DESC LIMIT 1", (player["name"],)).fetchone()
        if last and now-last["created"] < 1.25:
            return jsonify(error="Slow down a little"), 429
        con.execute("INSERT INTO messages(name,body,created) VALUES(?,?,?)",
                    (player["name"], body, now))
        con.execute("DELETE FROM messages WHERE id < (SELECT COALESCE(MAX(id),0)-500 FROM messages)")
    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
