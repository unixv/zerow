"""ZeroW: a persistent multiplayer lobby for Raspberry Pi Zero W."""
import hashlib
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, jsonify, make_response, request, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, static_folder="static")
# A small JSON cap protects the Pi Zero W from oversized request bodies.
app.config["MAX_CONTENT_LENGTH"] = 4096
DB = Path(os.environ.get("ZEROW_DB", "/opt/zerow/data/atrium.sqlite3"))
WIDTH, HEIGHT = 16, 11
SESSION_SECONDS = 30 * 24 * 3600
PRESENCE_HEARTBEAT_SECONDS = 10  # Avoid writing for every browser poll.
USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_-]{3,18}\Z")
PASSWORD_METHOD = "scrypt:32768:8:1"


@contextmanager
def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA journal_mode=WAL")
    # The previous guest-player table is intentionally left untouched for safe migration.
    con.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        x INTEGER NOT NULL DEFAULT 8,
        y INTEGER NOT NULL DEFAULT 5,
        created REAL NOT NULL,
        last_login REAL NOT NULL,
        last_seen REAL NOT NULL DEFAULT 0
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires REAL NOT NULL
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS session_user_idx ON sessions(user_id)")
    con.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
        username TEXT PRIMARY KEY,
        attempts INTEGER NOT NULL,
        reset_at REAL NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        body TEXT NOT NULL,
        created REAL NOT NULL
    )""")
    cols = {r["name"] for r in con.execute("PRAGMA table_info(messages)")}
    if "user_id" not in cols:
        con.execute("ALTER TABLE messages ADD COLUMN user_id INTEGER")
    con.commit()
    try:
        with con:
            yield con
    finally:
        con.close()


def token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def identity(con):
    token = request.cookies.get("zerow_session", "")
    if not 35 <= len(token) <= 128:
        return None
    return con.execute(
        """SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id
           WHERE s.token_hash=? AND s.expires>?""",
        (token_hash(token), time.time()),
    ).fetchone()


def create_session(con, user_id):
    token = secrets.token_urlsafe(32)
    now = time.time()
    con.execute("DELETE FROM sessions WHERE user_id=? OR expires<?", (user_id, now))
    con.execute("UPDATE users SET last_seen=0 WHERE id=?", (user_id,))
    con.execute("INSERT INTO sessions(token_hash,user_id,expires) VALUES(?,?,?)",
                (token_hash(token), user_id, now + SESSION_SECONDS))
    response = make_response(jsonify(ok=True))
    response.set_cookie("zerow_session", token, max_age=SESSION_SECONDS, httponly=True,
                        samesite="Lax", secure=request.is_secure or os.environ.get("ZEROW_SECURE_COOKIES", "0") == "1",
                        path="/")
    response.delete_cookie("zerow_player", path="/")
    return response


def require_user(con):
    player = identity(con)
    return player


def error(message, status=400):
    return jsonify(error=message), status


@app.errorhandler(RequestEntityTooLarge)
def oversized_request(exc):
    return error("Request body exceeds 4 KiB.", 413)


@app.before_request
def check_origin():
    # Prevent cross-site browser forms from mutating accounts / world state.
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    if request.path.startswith("/api/"):
        if request.mimetype != "application/json":
            return error("Expected JSON request body.", 415)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error("Expected a JSON object.", 400)
    origin = request.headers.get("Origin")
    if not origin:
        return error("Origin header required", 403)
    try:
        parts = urlsplit(origin)
        if parts.scheme not in ("http", "https") or parts.netloc.lower() != request.host.lower():
            return error("Origin not permitted", 403)
    except ValueError:
        return error("Origin not permitted", 403)


@app.after_request
def add_headers(response):
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/health")
def health():
    with connect() as con:
        con.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    if not isinstance(name, str):
        return error("Username must be a string.")
    name = name.strip()
    password = data.get("password", "")
    if not USERNAME_PATTERN.fullmatch(name):
        return error("Username must be 3–18 letters, numbers, _ or -.")
    if not isinstance(password, str) or not 10 <= len(password) <= 128:
        return error("Password must be 10–128 characters.")
    with connect() as con:
        existing = con.execute("SELECT id FROM users WHERE name=?", (name,)).fetchone()
        if existing:
            return error("Username is taken.", 409)
        # Password hashing is deliberately outside the INSERT transaction.
        hashed = generate_password_hash(password, method=PASSWORD_METHOD)
        now = time.time()
        try:
            cursor = con.execute(
                "INSERT INTO users(name,password_hash,created,last_login) VALUES(?,?,?,?)",
                (name, hashed, now, now),
            )
        except sqlite3.IntegrityError:
            return error("Username is taken.", 409)
        return create_session(con, cursor.lastrowid)


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    if not isinstance(name, str):
        return error("Incorrect username or password.", 401)
    name = name.strip()
    password = data.get("password", "")
    if not USERNAME_PATTERN.fullmatch(name) or not isinstance(password, str):
        return error("Incorrect username or password.", 401)
    now = time.time()
    key = name.lower()
    with connect() as con:
        limit = con.execute("SELECT attempts,reset_at FROM login_attempts WHERE username=?", (key,)).fetchone()
        if limit and limit["reset_at"] > now and limit["attempts"] >= 6:
            return error("Too many attempts. Try again in 15 minutes.", 429)
        user = con.execute("SELECT id,password_hash FROM users WHERE name=?", (name,)).fetchone()
        valid = bool(user and check_password_hash(user["password_hash"], password))
        if not valid:
            if not limit or limit["reset_at"] <= now:
                con.execute("REPLACE INTO login_attempts VALUES(?,?,?)", (key, 1, now + 900))
            else:
                con.execute("UPDATE login_attempts SET attempts=attempts+1 WHERE username=?", (key,))
            return error("Incorrect username or password.", 401)
        con.execute("DELETE FROM login_attempts WHERE username=?", (key,))
        con.execute("UPDATE users SET last_login=? WHERE id=?", (now, user["id"]))
        return create_session(con, user["id"])


@app.post("/api/change-password")
def change_password():
    """Rotate a password and revoke all existing sessions, including this one."""
    data = request.get_json(silent=True) or {}
    old_password = data.get("current_password")
    new_password = data.get("new_password")
    if not isinstance(old_password, str) or not isinstance(new_password, str):
        return error("Passwords are required.")
    if not 10 <= len(new_password) <= 128:
        return error("New password must be 10–128 characters.")
    if secrets.compare_digest(old_password, new_password):
        return error("New password must be different.")
    with connect() as con:
        user = identity(con)
        if user is None:
            return error("Log in first.", 401)
        # Bound expensive verification attempts per account, including authenticated sessions.
        now = time.time()
        key = "password:" + str(user["id"])
        limit = con.execute(
            "SELECT attempts,reset_at FROM login_attempts WHERE username=?", (key,)
        ).fetchone()
        if limit and limit["reset_at"] > now and limit["attempts"] >= 6:
            return error("Too many attempts. Try again in 15 minutes.", 429)
        if not check_password_hash(user["password_hash"], old_password):
            if not limit or limit["reset_at"] <= now:
                con.execute("REPLACE INTO login_attempts VALUES(?,?,?)", (key, 1, now + 900))
            else:
                con.execute("UPDATE login_attempts SET attempts=attempts+1 WHERE username=?", (key,))
            return error("Current password is incorrect.", 401)
        hashed = generate_password_hash(new_password, method=PASSWORD_METHOD)
        con.execute("UPDATE users SET password_hash=? WHERE id=?", (hashed, user["id"]))
        con.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
        con.execute("UPDATE users SET last_seen=0 WHERE id=?", (user["id"],))
        con.execute("DELETE FROM login_attempts WHERE username=?", (key,))
    resp = make_response(jsonify(ok=True, message="Password changed. Please log in again."))
    resp.delete_cookie("zerow_session", path="/")
    return resp


@app.post("/api/logout")
def logout():
    token = request.cookies.get("zerow_session", "")
    if token:
        with connect() as con:
            user = identity(con)
            con.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(token),))
            if user is not None:
                con.execute("UPDATE users SET last_seen=0 WHERE id=?", (user["id"],))
    resp = make_response(jsonify(ok=True))
    resp.delete_cookie("zerow_session", path="/")
    return resp


@app.get("/api/state")
def state():
    with connect() as con:
        user = require_user(con)
        if user is None:
            return jsonify(me=None, players=[], messages=[])
        now = time.time()
        # A heartbeat every ten seconds preserves the 40-second presence window
        # while avoiding a SQLite WAL write on every 1.5-second poll.
        if user["last_seen"] <= now - PRESENCE_HEARTBEAT_SECONDS:
            con.execute("UPDATE users SET last_seen=? WHERE id=? AND last_seen<=?",
                        (now, user["id"], now - PRESENCE_HEARTBEAT_SECONDS))
        people = [dict(row) for row in con.execute(
            "SELECT u.name,u.x,u.y FROM users u WHERE u.last_seen>? AND EXISTS (SELECT 1 FROM sessions s WHERE s.user_id=u.id AND s.expires>?) ORDER BY u.name LIMIT 100", (now - 40, now))]
        messages = [dict(row) for row in con.execute(
            """SELECT id, CASE WHEN user_id IS NULL THEN 'Guest · ' || name ELSE name END AS name,
                      body,created FROM (SELECT * FROM messages ORDER BY id DESC LIMIT 60)
               ORDER BY id""")]
        return jsonify(me=user["name"], players=people, messages=messages, room="Lobby",
                       width=WIDTH, height=HEIGHT, joined=user["created"])


@app.post("/api/move")
def move():
    data = request.get_json(silent=True) or {}
    x, y = data.get("x"), data.get("y")
    if type(x) is not int or type(y) is not int or not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        return error("Invalid tile")
    with connect() as con:
        user = require_user(con)
        if user is None:
            return error("Log in first.", 401)
        con.execute("UPDATE users SET x=?,y=?,last_seen=? WHERE id=?",
                    (x, y, time.time(), user["id"]))
    return jsonify(ok=True)


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    body = data.get("message", "")
    if not isinstance(body, str):
        return error("Invalid message.")
    body = body.strip()
    if not body or len(body) > 280 or any(ord(c) < 32 and c not in "\n\t" for c in body):
        return error("Message must be 1–280 characters.")
    with connect() as con:
        user = require_user(con)
        if user is None:
            return error("Log in first.", 401)
        now = time.time()
        last = con.execute(
            "SELECT created FROM messages WHERE user_id=? ORDER BY id DESC LIMIT 1", (user["id"],)
        ).fetchone()
        if last and now - last["created"] < 1.25:
            return error("Slow down a little.", 429)
        con.execute("INSERT INTO messages(name,body,created,user_id) VALUES(?,?,?,?)",
                    (user["name"], body, now, user["id"]))
        con.execute("DELETE FROM messages WHERE id < (SELECT COALESCE(MAX(id),0)-500 FROM messages)")
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
