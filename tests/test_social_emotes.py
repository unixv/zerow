"""Atrium social emotes: authenticated, shared, short-lived and rate-limited."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import app as game


class SocialEmoteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_db = game.DB
        game.DB = Path(self.tmp.name) / "atrium.sqlite3"
        self.alice = game.app.test_client()
        self.bob = game.app.test_client()

    def tearDown(self):
        game.DB = self.original_db
        self.tmp.cleanup()

    def post(self, client, path, data):
        return client.post(path, json=data, headers={"Origin": "http://localhost"})

    def test_two_players_see_expression_then_it_expires(self):
        self.assertEqual(self.post(self.alice, "/api/register", {"name": "AliceSocial", "password": "long-password-123"}).status_code, 200)
        self.assertEqual(self.post(self.bob, "/api/register", {"name": "BobSocial", "password": "long-password-123"}).status_code, 200)
        with patch.object(game.time, "time", return_value=1000000):
            self.assertEqual(self.post(self.alice, "/api/emote", {"emote": "wave"}).status_code, 200)
            state = self.bob.get("/api/state").get_json()
            self.assertEqual(next(p for p in state["players"] if p["name"] == "AliceSocial")["emote"], "wave")
            self.assertEqual(self.post(self.alice, "/api/emote", {"emote": "dance"}).status_code, 429)
        with patch.object(game.time, "time", return_value=1000008):
            state = self.bob.get("/api/state").get_json()
            self.assertEqual(next(p for p in state["players"] if p["name"] == "AliceSocial")["emote"], "")

    def test_validation_and_auth(self):
        self.assertEqual(self.post(self.alice, "/api/emote", {"emote": "wave"}).status_code, 401)
        self.post(self.alice, "/api/register", {"name": "SocialUser", "password": "long-password-123"})
        for value in ("<script>", "unknown", 123, None):
            self.assertEqual(self.post(self.alice, "/api/emote", {"emote": value}).status_code, 400)
        self.assertEqual(self.post(self.alice, "/api/emote", {"emote": "heart"}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
