"""Regression checks for real multi-client session lifecycle and presence."""
import importlib
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path


class SessionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ZEROW_DB"] = str(Path(self.tmp.name) / "state.sqlite3")
        import app
        self.app = importlib.reload(app)
        self.a = self.app.app.test_client()
        self.b = self.app.app.test_client()
        self.watcher = self.app.app.test_client()
        self.assertEqual(self.post(self.a, "/api/register", {
            "name": "Alice", "password": "alice-test-password"
        }).status_code, 200)
        self.assertEqual(self.post(self.watcher, "/api/register", {
            "name": "Watcher", "password": "watcher-test-password"
        }).status_code, 200)

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def post(client, path, payload=None):
        return client.post(path, json=payload or {}, headers={"Origin": "http://localhost"})

    def visible(self):
        return {p["name"] for p in self.watcher.get("/api/state").json["players"]}

    def test_relogin_invalidates_old_browser_and_hides_stale_presence(self):
        self.assertIn("Alice", self.visible())
        self.assertEqual(self.post(self.b, "/api/login", {
            "name": "Alice", "password": "alice-test-password"
        }).status_code, 200)
        self.assertIsNone(self.a.get("/api/state").json["me"])
        self.assertNotIn("Alice", self.visible())
        self.assertEqual(self.b.get("/api/state").json["me"], "Alice")
        self.assertIn("Alice", self.visible())
        self.assertEqual(self.post(self.a, "/api/move", {"x": 4, "y": 5}).status_code, 401)

    def test_logout_removes_presence_without_erasing_account_or_position(self):
        self.assertEqual(self.post(self.a, "/api/move", {"x": 2, "y": 7}).status_code, 200)
        self.assertIn("Alice", self.visible())
        self.assertEqual(self.post(self.a, "/api/logout").status_code, 200)
        self.assertNotIn("Alice", self.visible())
        self.assertEqual(self.post(self.a, "/api/chat", {"message": "not authorized"}).status_code, 401)
        self.assertEqual(self.post(self.a, "/api/login", {
            "name": "Alice", "password": "alice-test-password"
        }).status_code, 200)
        players = self.a.get("/api/state").json["players"]
        self.assertEqual([(p["x"], p["y"]) for p in players if p["name"] == "Alice"], [(2, 7)])

    def test_expired_session_is_not_authenticated(self):
        self.assertEqual(self.a.get("/api/state").json["me"], "Alice")
        with sqlite3.connect(os.environ["ZEROW_DB"]) as con:
            con.execute("UPDATE sessions SET expires=? WHERE user_id=(SELECT id FROM users WHERE name='Alice')",
                        (time.time() - 5,))
        self.assertIsNone(self.a.get("/api/state").json["me"])
        self.assertEqual(self.post(self.a, "/api/move", {"x": 3, "y": 3}).status_code, 401)
        self.assertEqual(self.post(self.a, "/api/chat", {"message": "expired"}).status_code, 401)


if __name__ == "__main__":
    unittest.main()
