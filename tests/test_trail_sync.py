"""Atrium account-backed discovery regression (isolated SQLite, no Pi access)."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import app as atrium


class TrailSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(atrium, "DB", Path(self.tmp.name) / "atrium.sqlite3")
        self.db_patch.start()
        self.client = atrium.app.test_client()\n        self.origin = {"Origin": "http://localhost"}
        with atrium.connect() as con:
            con.execute("INSERT INTO users(name,password_hash,x,y,created,last_login) VALUES(?,?,?,?,?,?)",
                        ("trailtester", "unused", 7, 2, time.time(), time.time()))
            user_id = con.execute("SELECT id FROM users WHERE name='trailtester'").fetchone()["id"]
            con.execute("INSERT INTO sessions(token_hash,user_id,expires) VALUES(?,?,?)",
                        (atrium.token_hash("t" * 40), user_id, time.time() + 3600))
        self.client.set_cookie("zerow_session", "t" * 40)

    def tearDown(self):
        self.db_patch.stop()
        self.tmp.cleanup()

    def test_account_progress_idempotent_and_available_to_new_session(self):
        first = self.client.post("/api/trail/discover", headers=self.origin, json={"landmark": 0})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json["discoveries"], [0])
        self.assertEqual(self.client.post("/api/trail/discover", headers=self.origin, json={"landmark": 0}).json["discoveries"], [0])
        self.assertEqual(self.client.get("/api/state").json["discoveries"], [0])
        other = atrium.app.test_client()
        other.set_cookie("zerow_session", "t" * 40)
        self.assertEqual(other.get("/api/state").json["discoveries"], [0])

    def test_rejects_unvisited_and_invalid_landmarks(self):
        self.assertEqual(self.client.post("/api/trail/discover", headers=self.origin, json={"landmark": 1}).status_code, 409)
        for value in [-1, 4, True, "0", None]:
            self.assertEqual(self.client.post("/api/trail/discover", headers=self.origin, json={"landmark": value}).status_code, 400)
        self.assertEqual(self.client.get("/api/state").json["discoveries"], [])

    def test_requires_authentication(self):
        guest = atrium.app.test_client()
        self.assertEqual(guest.post("/api/trail/discover", headers=self.origin, json={"landmark": 0}).status_code, 401)


if __name__ == "__main__":
    unittest.main()
