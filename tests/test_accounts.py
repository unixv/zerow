"""Run: ZEROW_DB=./data/test.sqlite3 python3 -m unittest discover -s tests -v"""
import importlib
import os
import tempfile
import unittest
from pathlib import Path


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ZEROW_DB"] = str(Path(self.tmp.name) / "db.sqlite3")
        import app
        self.mod = importlib.reload(app)
        self.client = self.mod.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def post(self, route, data):
        return self.client.post(route, json=data, headers={"Origin": "http://localhost"})

    def test_register_persists_and_login_again(self):
        resp = self.post("/api/register", {"name": "alice_1", "password": "correct horse battery"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.client.get("/api/state").json["me"], "alice_1")
        self.assertEqual(self.post("/api/chat", {"message": "Hello world!"}).status_code, 200)
        self.assertEqual(self.post("/api/move", {"x": 3, "y": 4}).status_code, 200)
        self.assertEqual(self.post("/api/logout", {}).status_code, 200)
        self.assertIsNone(self.client.get("/api/state").json["me"])
        self.assertEqual(self.post("/api/login", {"name": "alice_1", "password": "correct horse battery"}).status_code, 200)
        state = self.client.get("/api/state").json
        self.assertEqual(state["players"][0]["x"], 3)
        self.assertEqual(state["messages"][-1]["body"], "Hello world!")

    def test_invalid_auth_and_duplicate(self):
        self.assertEqual(self.post("/api/register", {"name": "ab", "password": "long-password"}).status_code, 400)
        self.assertEqual(self.post("/api/register", {"name": "Bob", "password": "long-password"}).status_code, 200)
        self.assertEqual(self.post("/api/register", {"name": "bob", "password": "long-password"}).status_code, 409)
        self.assertEqual(self.post("/api/logout", {}).status_code, 200)
        self.assertEqual(self.post("/api/login", {"name": "Bob", "password": "wrong password"}).status_code, 401)
        self.assertEqual(self.post("/api/chat", {"message": "unauthenticated"}).status_code, 401)

    def test_change_password_revokes_sessions_and_preserves_data(self):
        self.assertEqual(self.post("/api/register", {
            "name": "Alice", "password": "initial-password-123"
        }).status_code, 200)
        self.assertEqual(self.post("/api/move", {"x": 4, "y": 7}).status_code, 200)
        self.assertEqual(self.post("/api/chat", {"message": "Account survives rotation"}).status_code, 200)
        self.assertEqual(self.post("/api/change-password", {
            "current_password": "wrong-password",
            "new_password": "replacement-password-123"
        }).status_code, 401)
        self.assertEqual(self.client.get("/api/state").json["me"], "Alice")
        self.assertEqual(self.post("/api/change-password", {
            "current_password": "initial-password-123",
            "new_password": "replacement-password-123"
        }).status_code, 200)
        self.assertIsNone(self.client.get("/api/state").json["me"])
        self.assertEqual(self.post("/api/login", {
            "name": "Alice", "password": "initial-password-123"
        }).status_code, 401)
        self.assertEqual(self.post("/api/login", {
            "name": "Alice", "password": "replacement-password-123"
        }).status_code, 200)
        state = self.client.get("/api/state").json
        self.assertEqual((state["players"][0]["x"], state["players"][0]["y"]), (4, 7))
        self.assertEqual(state["messages"][-1]["body"], "Account survives rotation")

    def test_password_change_validation_and_rate_limit(self):
        self.assertEqual(self.post("/api/change-password", {
            "current_password": "old", "new_password": "new-password-123"
        }).status_code, 401)
        self.assertEqual(self.post("/api/register", {
            "name": "Alice", "password": "initial-password-123"
        }).status_code, 200)
        self.assertEqual(self.post("/api/change-password", {
            "current_password": "initial-password-123", "new_password": "short"
        }).status_code, 400)
        self.assertEqual(self.post("/api/change-password", {
            "current_password": "initial-password-123", "new_password": "initial-password-123"
        }).status_code, 400)
        for _ in range(6):
            self.assertEqual(self.post("/api/change-password", {
                "current_password": "wrong-password", "new_password": "replacement-password-123"
            }).status_code, 401)
        self.assertEqual(self.post("/api/change-password", {
            "current_password": "initial-password-123", "new_password": "replacement-password-123"
        }).status_code, 429)

    def test_logout_removes_player_from_other_clients_immediately(self):
        observer = self.mod.app.test_client()
        self.assertEqual(self.post("/api/register", {
            "name": "Alice", "password": "alice-password-123"
        }).status_code, 200)
        self.assertEqual(self.client.get("/api/state").json["me"], "Alice")
        self.assertEqual(observer.post("/api/register", json={
            "name": "Bob", "password": "bob-password-123"
        }, headers={"Origin": "http://localhost"}).status_code, 200)
        self.assertEqual(len(observer.get("/api/state").json["players"]), 2)
        self.assertEqual(self.post("/api/logout", {}).status_code, 200)
        names = [p["name"] for p in observer.get("/api/state").json["players"]]
        self.assertEqual(names, ["Bob"])
        self.assertEqual(self.post("/api/login", {
            "name": "Alice", "password": "alice-password-123"
        }).status_code, 200)
        self.assertEqual(len(observer.get("/api/state").json["players"]), 1)
        self.assertEqual(self.client.get("/api/state").json["me"], "Alice")
        self.assertEqual(len(observer.get("/api/state").json["players"]), 2)

    def test_password_rotation_removes_presence_immediately(self):
        observer = self.mod.app.test_client()
        self.assertEqual(self.post("/api/register", {
            "name": "Alice", "password": "alice-password-123"
        }).status_code, 200)
        self.assertEqual(self.client.get("/api/state").json["me"], "Alice")
        self.assertEqual(observer.post("/api/register", json={
            "name": "Bob", "password": "bob-password-123"
        }, headers={"Origin": "http://localhost"}).status_code, 200)
        self.assertEqual(len(observer.get("/api/state").json["players"]), 2)
        self.assertEqual(self.post("/api/change-password", {
            "current_password": "alice-password-123",
            "new_password": "alice-password-456"
        }).status_code, 200)
        self.assertEqual([p["name"] for p in observer.get("/api/state").json["players"]], ["Bob"])

    def test_presence_heartbeat_is_throttled_without_losing_presence(self):
        from unittest.mock import patch
        import sqlite3

        with patch.object(self.mod.time, "time", return_value=1000.0):
            self.assertEqual(self.post("/api/register", {
                "name": "heartbeat", "password": "long-enough-password"
            }).status_code, 200)
            first = self.client.get("/api/state").json
        self.assertEqual(first["me"], "heartbeat")
        self.assertEqual(len(first["players"]), 1)

        with sqlite3.connect(os.environ["ZEROW_DB"]) as db:
            seen = db.execute("SELECT last_seen FROM users WHERE name='heartbeat'").fetchone()[0]
        self.assertEqual(seen, 1000.0)

        for t in (1001.0, 1005.0, 1009.0):
            with patch.object(self.mod.time, "time", return_value=t):
                result = self.client.get("/api/state").json
            self.assertEqual(len(result["players"]), 1)
            with sqlite3.connect(os.environ["ZEROW_DB"]) as db:
                unchanged = db.execute("SELECT last_seen FROM users WHERE name='heartbeat'").fetchone()[0]
            self.assertEqual(unchanged, 1000.0)

        with patch.object(self.mod.time, "time", return_value=1010.0):
            self.assertEqual(len(self.client.get("/api/state").json["players"]), 1)
        with sqlite3.connect(os.environ["ZEROW_DB"]) as db:
            updated = db.execute("SELECT last_seen FROM users WHERE name='heartbeat'").fetchone()[0]
        self.assertEqual(updated, 1010.0)

    def test_move_refreshes_presence_immediately(self):
        from unittest.mock import patch
        import sqlite3

        with patch.object(self.mod.time, "time", return_value=2000.0):
            self.post("/api/register", {"name": "moving", "password": "long-enough-password"})
            self.client.get("/api/state")
        with patch.object(self.mod.time, "time", return_value=2002.0):
            self.assertEqual(self.post("/api/move", {"x": 2, "y": 3}).status_code, 200)
        with sqlite3.connect(os.environ["ZEROW_DB"]) as db:
            seen, x, y = db.execute("SELECT last_seen,x,y FROM users WHERE name='moving'").fetchone()
        self.assertEqual((seen, x, y), (2002.0, 2, 3))

    def test_api_rejects_malformed_json_shapes_without_server_errors(self):
        cases = [
            ([], 400),
            ("text", 400),
            (42, 400),
        ]
        for payload, status in cases:
            for endpoint in ("/api/register", "/api/login", "/api/chat",
                             "/api/move", "/api/change-password", "/api/logout"):
                with self.subTest(endpoint=endpoint, payload=payload):
                    result = self.client.post(endpoint, json=payload,
                                              headers={"Origin": "http://localhost"})
                    self.assertEqual(result.status_code, status)
                    self.assertIn("error", result.json)

    def test_api_rejects_non_json_and_large_payloads(self):
        result = self.client.post("/api/register", data="name=Alice",
                                  headers={"Origin": "http://localhost"},
                                  content_type="application/x-www-form-urlencoded")
        self.assertEqual(result.status_code, 415)
        self.assertIn("error", result.json)
        result = self.client.post("/api/register", data="{",
                                  headers={"Origin": "http://localhost"},
                                  content_type="application/json")
        self.assertEqual(result.status_code, 400)
        result = self.client.post("/api/chat", data='{"message":"' + "x" * 5000 + '"}',
                                  headers={"Origin": "http://localhost"},
                                  content_type="application/json")
        self.assertEqual(result.status_code, 413)
        self.assertIn("error", result.json)

    def test_username_types_do_not_get_coerced_to_strings(self):
        for endpoint in ("/api/register", "/api/login"):
            for value in (123, [], {}, True):
                with self.subTest(endpoint=endpoint, value=value):
                    response = self.post(endpoint, {"name": value, "password": "valid-password-123"})
                    self.assertIn(response.status_code, (400, 401))
                    self.assertIn("error", response.json)

    def test_expired_session_disappears_without_erasing_account(self):
        import sqlite3
        from unittest.mock import patch

        observer = self.mod.app.test_client()
        with patch.object(self.mod.time, "time", return_value=1000.0):
            self.assertEqual(self.post("/api/register", {
                "name": "Alice", "password": "alice-password-123"
            }).status_code, 200)
            self.client.get("/api/state")
            self.assertEqual(observer.post("/api/register", json={
                "name": "Bob", "password": "bob-password-123"
            }, headers={"Origin": "http://localhost"}).status_code, 200)
            self.assertEqual(
                [p["name"] for p in observer.get("/api/state").json["players"]],
                ["Alice", "Bob"],
            )
            with sqlite3.connect(os.environ["ZEROW_DB"]) as db:
                db.execute(
                    "UPDATE sessions SET expires=999 WHERE user_id="
                    "(SELECT id FROM users WHERE name='Alice')"
                )
            self.assertEqual(
                [p["name"] for p in observer.get("/api/state").json["players"]],
                ["Bob"],
            )
            self.assertIsNone(self.client.get("/api/state").json["me"])
            with sqlite3.connect(os.environ["ZEROW_DB"]) as db:
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM users WHERE name='Alice'"
                ).fetchone()[0], 1)

    def test_chat_cooldown_index_preserves_legacy_messages(self):
        import sqlite3
        from unittest.mock import patch

        path = os.environ["ZEROW_DB"]
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE messages(id INTEGER PRIMARY KEY, name TEXT, body TEXT, created REAL)")
            db.execute("INSERT INTO messages VALUES(1, 'oldguest', 'historic', 1.0)")
        with patch.object(self.mod.time, "time", return_value=1000.0):
            self.assertEqual(self.post("/api/register", {
                "name": "Alice", "password": "alice-password-123"
            }).status_code, 200)
            self.assertEqual(self.post("/api/chat", {"message": "first"}).status_code, 200)
            self.assertEqual(self.post("/api/chat", {"message": "too soon"}).status_code, 429)
        with sqlite3.connect(path) as db:
            index = db.execute(
                "PRAGMA index_list(messages)"
            ).fetchall()
            self.assertIn("messages_user_latest_idx", [row[1] for row in index])
            plan = db.execute(
                "EXPLAIN QUERY PLAN SELECT created FROM messages "
                "WHERE user_id=? ORDER BY id DESC LIMIT 1", (1,)
            ).fetchall()
            # SQLite can use the covering index to locate this user's latest message.
            self.assertTrue(any("messages_user_latest_idx" in row[3] for row in plan), plan)
            self.assertEqual(db.execute(
                "SELECT body FROM messages WHERE id=1"
            ).fetchone()[0], "historic")
        with patch.object(self.mod.time, "time", return_value=1002.0):
            self.assertEqual(self.post("/api/chat", {"message": "after cooldown"}).status_code, 200)
        # Keep the mocked clock active: the test session was issued at t=1000.
        with patch.object(self.mod.time, "time", return_value=1002.0):
            messages = self.client.get("/api/state").json["messages"]
        self.assertEqual([m["body"] for m in messages],
                         ["historic", "first", "after cooldown"])

    def test_origin_check(self):
        r = self.client.post("/api/register", json={"name": "alice", "password": "long password"})
        self.assertEqual(r.status_code, 403)
        r = self.client.post("/api/register", json={"name": "alice", "password": "long password"},
                             headers={"Origin": "https://evil.example"})
        self.assertEqual(r.status_code, 403)

    def test_existing_message_schema_migrates(self):
        import sqlite3
        path = os.environ["ZEROW_DB"]
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE messages(id INTEGER PRIMARY KEY, name TEXT, body TEXT, created REAL)")
            db.execute("INSERT INTO messages VALUES(1,'oldguest','historic',1.0)")
        self.assertEqual(self.post("/api/register", {"name": "alice", "password": "long password"}).status_code, 200)
        state = self.client.get("/api/state").json
        self.assertEqual(state["messages"][0]["name"], "Guest · oldguest")


if __name__ == "__main__":
    unittest.main()
