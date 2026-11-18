"""Shared Lantern Circle integration tests with isolated SQLite and real sessions."""
import tempfile
import unittest
from pathlib import Path
import app as game


class LanternCircleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = game.DB
        game.DB = Path(self.tmp.name) / "atrium.sqlite3"
        self.alice = game.app.test_client()
        self.bob = game.app.test_client()

    def tearDown(self):
        game.DB = self.old_db
        self.tmp.cleanup()

    @staticmethod
    def post(client, path, payload):
        return client.post(path, json=payload, headers={"Origin": "http://localhost"})

    def test_cooperative_lighting_and_persistence(self):
        self.assertEqual(self.post(self.alice, "/api/lanterns/light", {"landmark": 0}).status_code, 401)
        self.post(self.alice, "/api/register", {"name": "LanternAlice", "password": "long-password-123"})
        self.post(self.bob, "/api/register", {"name": "LanternBob", "password": "long-password-123"})
        for invalid in (-1, 4, True, "0", None):
            self.assertEqual(self.post(self.alice, "/api/lanterns/light", {"landmark": invalid}).status_code, 400)
        self.assertEqual(self.post(self.alice, "/api/lanterns/light", {"landmark": 0}).status_code, 409)
        self.post(self.alice, "/api/move", {"x": 7, "y": 2})
        first = self.post(self.alice, "/api/lanterns/light", {"landmark": 0}).get_json()
        self.assertEqual(first, {"ok": True, "new": True, "count": 1})
        second = self.post(self.alice, "/api/lanterns/light", {"landmark": 0}).get_json()
        self.assertEqual(second, {"ok": True, "new": False, "count": 1})
        self.assertEqual(self.bob.get("/api/state").get_json()["lanterns"], {"counts": [1, 0, 0, 0], "mine": []})
        self.post(self.bob, "/api/move", {"x": 7, "y": 2})
        self.assertEqual(self.post(self.bob, "/api/lanterns/light", {"landmark": 0}).get_json()["count"], 2)
        self.post(self.alice, "/api/logout", {})
        self.post(self.alice, "/api/login", {"name": "LanternAlice", "password": "long-password-123"})
        self.assertEqual(self.alice.get("/api/state").get_json()["lanterns"], {"counts": [2, 0, 0, 0], "mine": [0]})


if __name__ == "__main__":
    unittest.main()
