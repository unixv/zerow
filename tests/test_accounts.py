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
