"""Atrium player-owned rooms and earnable-coin furniture shop.

No payment processor or real-money transactions are involved. All purchases,
inventory assignments, and tile placements are authoritative SQLite operations.
"""
import re
import sqlite3
import time
from flask import jsonify, request

ROOM_WIDTH = 10
ROOM_HEIGHT = 7
MAX_ROOMS = 3
EXTRA_ROOM_COST = 150
DAILY_COINS = 100
DAILY_INTERVAL = 86400
MAX_ITEMS = 100

FURNITURE = {
    "chair": {"name": "Reading chair", "price": 35, "symbol": "♜", "color": "#c98a5e"},
    "plant": {"name": "Potted fern", "price": 45, "symbol": "♣", "color": "#79be83"},
    "lamp": {"name": "Floor lamp", "price": 70, "symbol": "✦", "color": "#efd18b"},
    "table": {"name": "Coffee table", "price": 80, "symbol": "▣", "color": "#bd9d7b"},
    "rug": {"name": "Soft rug", "price": 50, "symbol": "▤", "color": "#b999d8"},
    "sofa": {"name": "Cozy sofa", "price": 120, "symbol": "▰", "color": "#8bb1ce"},
    "books": {"name": "Bookshelf", "price": 90, "symbol": "▥", "color": "#d9a77d"},
    "flower": {"name": "Flower pot", "price": 40, "symbol": "✿", "color": "#e9a3a9"},
}


def ensure_schema(con):
    # Legacy account rows receive the one-time starter grant through the column
    # default; this does not rewrite user identity or existing game progress.
    fields = {r["name"] for r in con.execute("PRAGMA table_info(users)")}
    if "coins" not in fields:
        con.execute("ALTER TABLE users ADD COLUMN coins INTEGER NOT NULL DEFAULT 300")
    if "last_coin_claim" not in fields:
        con.execute("ALTER TABLE users ADD COLUMN last_coin_claim REAL NOT NULL DEFAULT 0")
    con.execute("""CREATE TABLE IF NOT EXISTS player_rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        created REAL NOT NULL
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS player_rooms_owner_idx ON player_rooms(owner_id)")
    con.execute("""CREATE TABLE IF NOT EXISTS furniture_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        sku TEXT NOT NULL,
        room_id INTEGER,
        x INTEGER,
        y INTEGER,
        purchased REAL NOT NULL,
        CHECK ((room_id IS NULL AND x IS NULL AND y IS NULL)
            OR (room_id IS NOT NULL AND x BETWEEN 0 AND 9 AND y BETWEEN 0 AND 6)),
        UNIQUE(room_id, x, y)
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS furniture_owner_idx ON furniture_items(owner_id)")
    con.execute("CREATE INDEX IF NOT EXISTS furniture_room_idx ON furniture_items(room_id)")
    con.execute("""CREATE TABLE IF NOT EXISTS room_visitors (
        user_id INTEGER PRIMARY KEY,
        room_id INTEGER NOT NULL,
        seen REAL NOT NULL
    )""")
    visitor_fields = {r["name"] for r in con.execute("PRAGMA table_info(room_visitors)")}
    for column in ("x", "y"):
        if column not in visitor_fields:
            con.execute(f"ALTER TABLE room_visitors ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0")
    con.execute("CREATE INDEX IF NOT EXISTS room_visitors_room_idx ON room_visitors(room_id,seen)")
    con.execute("""CREATE TABLE IF NOT EXISTS room_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        body TEXT NOT NULL,
        created REAL NOT NULL
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS room_messages_room_idx ON room_messages(room_id,id DESC)")
    con.execute("CREATE INDEX IF NOT EXISTS room_messages_user_idx ON room_messages(user_id,id DESC)")


def catalog():
    return [{"sku": sku, **entry} for sku, entry in FURNITURE.items()]


def register(app, connect, identity, error):
    def current(con):
        u = identity(con)
        return u

    @app.get("/api/homes")
    def homes():
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in to see rooms.", 401)
            public = [dict(r) for r in con.execute(
                """SELECT r.id,r.name,u.name AS owner,
                    (SELECT COUNT(*) FROM furniture_items f WHERE f.room_id=r.id) AS furniture_count
                   FROM player_rooms r JOIN users u ON u.id=r.owner_id
                   ORDER BY r.created DESC,r.id DESC LIMIT 50"""
            )]
            mine = [dict(r) for r in con.execute(
                "SELECT id,name FROM player_rooms WHERE owner_id=? ORDER BY id", (u["id"],)
            )]
            inventory = [dict(r) for r in con.execute(
                """SELECT id,sku,room_id FROM furniture_items
                   WHERE owner_id=? ORDER BY id DESC LIMIT 100""", (u["id"],)
            )]
            return jsonify(rooms=public, mine=mine, inventory=inventory,
                           coins=u["coins"], next_claim=max(0, int(u["last_coin_claim"] + DAILY_INTERVAL - time.time())),
                           catalog=catalog(), room_cost=EXTRA_ROOM_COST,
                           max_rooms=MAX_ROOMS)

    @app.get("/api/homes/<int:room_id>")
    def view_home(room_id):
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            room = con.execute(
                "SELECT r.id,r.name,r.owner_id,u.name AS owner FROM player_rooms r "
                "JOIN users u ON u.id=r.owner_id WHERE r.id=?", (room_id,)
            ).fetchone()
            if room is None:
                return error("Room not found.", 404)
            items = [dict(r) for r in con.execute(
                "SELECT id,sku,x,y FROM furniture_items WHERE room_id=? ORDER BY id", (room_id,)
            )]
            return jsonify(room={"id": room["id"], "name": room["name"], "owner": room["owner"],
                                 "editable": room["owner_id"] == u["id"],
                                 "width": ROOM_WIDTH, "height": ROOM_HEIGHT},
                           items=items)


    @app.post("/api/homes/<int:room_id>/visit")
    def visit_home(room_id):
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            if not con.execute("SELECT 1 FROM player_rooms WHERE id=?", (room_id,)).fetchone():
                return error("Room not found.", 404)
            now = time.time()
            con.execute("INSERT INTO room_visitors(user_id,room_id,seen,x,y) VALUES(?,?,?,0,0) "
                        "ON CONFLICT(user_id) DO UPDATE SET "
                        "x=CASE WHEN room_id=excluded.room_id THEN x ELSE 0 END,"
                        "y=CASE WHEN room_id=excluded.room_id THEN y ELSE 0 END,"
                        "room_id=excluded.room_id,seen=excluded.seen",
                        (u["id"], room_id, now))
            return jsonify(ok=True)

    @app.post("/api/homes/<int:room_id>/move")
    def move_in_home(room_id):
        data = request.get_json(silent=True) or {}
        x, y = data.get("x"), data.get("y")
        if type(x) is not int or type(y) is not int or not (0 <= x < ROOM_WIDTH and 0 <= y < ROOM_HEIGHT):
            return error("Choose a tile inside the room.")
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            now = time.time()
            visitor = con.execute(
                "SELECT room_id,seen,x,y FROM room_visitors WHERE user_id=?", (u["id"],)
            ).fetchone()
            if visitor is None or visitor["room_id"] != room_id or visitor["seen"] < now-30:
                return error("Enter this room before walking.", 403)
            if con.execute("SELECT 1 FROM furniture_items WHERE room_id=? AND x=? AND y=?",
                           (room_id,x,y)).fetchone():
                return error("Furniture blocks that tile.", 409)
            if abs(x-visitor["x"])+abs(y-visitor["y"]) != 1:
                return error("Walk to an adjacent tile.", 400)
            con.execute("UPDATE room_visitors SET x=?,y=?,seen=? WHERE user_id=?",
                        (x,y,now,u["id"]))
            return jsonify(ok=True,x=x,y=y)

    @app.post("/api/homes/leave")
    def leave_home():
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            con.execute("DELETE FROM room_visitors WHERE user_id=?", (u["id"],))
            return jsonify(ok=True)

    @app.get("/api/homes/<int:room_id>/social")
    def home_social(room_id):
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            if not con.execute("SELECT 1 FROM player_rooms WHERE id=?", (room_id,)).fetchone():
                return error("Room not found.", 404)
            now = time.time()
            visitors = [dict(row) for row in con.execute(
                """SELECT u.name,u.avatar_color,u.avatar_style,v.x,v.y,
                          CASE WHEN u.id=? THEN 1 ELSE 0 END AS self
                   FROM room_visitors v JOIN users u ON u.id=v.user_id
                   WHERE v.room_id=? AND v.seen>? AND EXISTS (
                     SELECT 1 FROM sessions s WHERE s.user_id=u.id AND s.expires>?)
                   ORDER BY u.name LIMIT 30""", (u["id"],room_id, now-30, now))]
            messages = [dict(row) for row in con.execute(
                """SELECT id,name,body,created FROM (
                   SELECT id,name,body,created FROM room_messages
                   WHERE room_id=? ORDER BY id DESC LIMIT 35) ORDER BY id""",
                (room_id,))]
            return jsonify(visitors=visitors,messages=messages)

    @app.post("/api/homes/<int:room_id>/chat")
    def home_chat(room_id):
        data = request.get_json(silent=True) or {}
        body = data.get("message")
        if not isinstance(body, str):
            return error("Invalid message.")
        body = body.strip()
        if not body or len(body)>280 or any(ord(c)<32 and c not in "\n\t" for c in body):
            return error("Message must be 1–280 characters.")
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            now = time.time()
            visitor = con.execute("SELECT room_id,seen FROM room_visitors WHERE user_id=?",
                                  (u["id"],)).fetchone()
            if visitor is None or visitor["room_id"] != room_id or visitor["seen"] < now-30:
                return error("Enter this room to chat.", 403)
            last = con.execute("SELECT created FROM room_messages WHERE user_id=? ORDER BY id DESC LIMIT 1",
                               (u["id"],)).fetchone()
            if last and now-last["created"] < 1.25:
                return error("Slow down a little.", 429)
            con.execute("INSERT INTO room_messages(room_id,user_id,name,body,created) VALUES(?,?,?,?,?)",
                        (room_id,u["id"],u["name"],body,now))
            con.execute("UPDATE room_visitors SET seen=? WHERE user_id=?", (now,u["id"]))
            con.execute("DELETE FROM room_messages WHERE id IN (SELECT id FROM room_messages "
                        "WHERE room_id=? ORDER BY id DESC LIMIT -1 OFFSET 100)", (room_id,))
            return jsonify(ok=True)

    @app.post("/api/homes/create")
    def create_home():
        name = request.get_json()["name"] if "name" in request.get_json() else ""
        if not isinstance(name, str):
            return error("Choose a room name.")
        name = name.strip()
        if not re.fullmatch(r"[A-Za-z0-9 _'-]{3,28}", name):
            return error("Room name must be 3–28 letters, numbers or spaces.")
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            con.execute("BEGIN IMMEDIATE")
            count = con.execute("SELECT COUNT(*) FROM player_rooms WHERE owner_id=?", (u["id"],)).fetchone()[0]
            if count >= MAX_ROOMS:
                return error("Three rooms per player is the current limit.", 409)
            price = 0 if count == 0 else EXTRA_ROOM_COST
            if price:
                paid = con.execute("UPDATE users SET coins=coins-? WHERE id=? AND coins>=?",
                                   (price, u["id"], price))
                if paid.rowcount != 1:
                    return error("Not enough coins to create another room.", 409)
            cur = con.execute("INSERT INTO player_rooms(owner_id,name,created) VALUES(?,?,?)",
                              (u["id"], name, time.time()))
            coins = con.execute("SELECT coins FROM users WHERE id=?", (u["id"],)).fetchone()[0]
            return jsonify(ok=True, room_id=cur.lastrowid, coins=coins)

    @app.post("/api/homes/claim")
    def claim_coins():
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            now = time.time()
            # One atomic conditional update prevents multi-tab double-claims.
            updated = con.execute(
                "UPDATE users SET coins=coins+?,last_coin_claim=? WHERE id=? AND last_coin_claim<=?",
                (DAILY_COINS, now, u["id"], now-DAILY_INTERVAL),
            )
            if updated.rowcount != 1:
                return error("Daily coins have already been collected.", 409)
            coins = con.execute("SELECT coins FROM users WHERE id=?", (u["id"],)).fetchone()[0]
            return jsonify(ok=True, awarded=DAILY_COINS, coins=coins)

    @app.post("/api/homes/buy")
    def buy_furniture():
        sku = request.get_json().get("sku")
        if not isinstance(sku, str) or sku not in FURNITURE:
            return error("Unknown furniture item.")
        price = FURNITURE[sku]["price"]
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            con.execute("BEGIN IMMEDIATE")
            count = con.execute("SELECT COUNT(*) FROM furniture_items WHERE owner_id=?", (u["id"],)).fetchone()[0]
            if count >= MAX_ITEMS:
                return error("Inventory limit reached.", 409)
            paid = con.execute("UPDATE users SET coins=coins-? WHERE id=? AND coins>=?",
                               (price, u["id"], price))
            if paid.rowcount != 1:
                return error("Not enough coins.", 409)
            item = con.execute(
                "INSERT INTO furniture_items(owner_id,sku,purchased) VALUES(?,?,?)",
                (u["id"], sku, time.time())
            )
            coins = con.execute("SELECT coins FROM users WHERE id=?", (u["id"],)).fetchone()[0]
            return jsonify(ok=True, item_id=item.lastrowid, coins=coins)

    @app.post("/api/homes/place")
    def place_furniture():
        data = request.get_json()
        room_id, item_id, x, y = (data.get(k) for k in ("room_id", "item_id", "x", "y"))
        if any(type(v) is not int for v in (room_id, item_id, x, y)) or not (
                room_id > 0 and item_id > 0 and 0 <= x < ROOM_WIDTH and 0 <= y < ROOM_HEIGHT):
            return error("Choose a valid room, item and tile.")
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            con.execute("BEGIN IMMEDIATE")
            room = con.execute("SELECT owner_id FROM player_rooms WHERE id=?", (room_id,)).fetchone()
            if room is None or room["owner_id"] != u["id"]:
                return error("You can only decorate your own rooms.", 403)
            occupied = con.execute("SELECT id FROM furniture_items WHERE room_id=? AND x=? AND y=?",
                                   (room_id, x, y)).fetchone()
            if occupied:
                return error("That tile already has furniture.", 409)
            changed = con.execute(
                "UPDATE furniture_items SET room_id=?,x=?,y=? "
                "WHERE id=? AND owner_id=? AND room_id IS NULL",
                (room_id, x, y, item_id, u["id"])
            )
            if changed.rowcount != 1:
                return error("That item is unavailable in your inventory.", 409)
            return jsonify(ok=True)

    @app.post("/api/homes/pickup")
    def pickup_furniture():
        data = request.get_json()
        room_id, item_id = data.get("room_id"), data.get("item_id")
        if type(room_id) is not int or type(item_id) is not int or room_id <= 0 or item_id <= 0:
            return error("Invalid furniture selection.")
        with connect() as con:
            u = current(con)
            if u is None:
                return error("Log in first.", 401)
            room = con.execute("SELECT owner_id FROM player_rooms WHERE id=?", (room_id,)).fetchone()
            if room is None or room["owner_id"] != u["id"]:
                return error("You can only edit your own rooms.", 403)
            changed = con.execute(
                "UPDATE furniture_items SET room_id=NULL,x=NULL,y=NULL "
                "WHERE id=? AND owner_id=? AND room_id=?",
                (item_id, u["id"], room_id)
            )
            if changed.rowcount != 1:
                return error("Furniture not found in this room.", 404)
            return jsonify(ok=True)
