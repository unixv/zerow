"""Atrium avatar wardrobe persistence, authorization and input validation."""
import tempfile
import unittest
from pathlib import Path
import app as game


class AvatarWardrobeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_db = game.DB
        game.DB = Path(self.tmp.name) / "atrium.sqlite3"
        self.client = game.app.test_client()

    def tearDown(self):
        game.DB = self.original_db
        self.tmp.cleanup()

    def post(self, path, payload):
        return self.client.post(path, json=payload, headers={"Origin": "http://localhost"})

    def test_avatar_requires_authentication_and_valid_choices(self):
        self.assertEqual(self.post("/api/avatar", {"color": "ocean", "style": "hoodie"}).status_code, 401)
        self.assertEqual(self.post("/api/register", {"name": "AtriumTester", "password": "long-password-123"}).status_code, 200)
        for invalid in ({"color": "<script>", "style": "classic"}, {"color": "moss", "style": "invisible"}, {"color": 42, "style": "crown"}):
            self.assertEqual(self.post("/api/avatar", invalid).status_code, 400)
        self.assertEqual(self.post("/api/avatar", {"color": "ocean", "style": "hoodie"}).status_code, 200)
        state = self.client.get("/api/state").get_json()
        self.assertEqual(state["avatar"], {"color": "ocean", "style": "hoodie"})
        self.assertEqual(state["players"][0]["avatar_color"], "ocean")
        self.assertEqual(state["players"][0]["avatar_style"], "hoodie")

    def test_avatar_survives_logout_and_login(self):
        self.post("/api/register", {"name": "WardrobeUser", "password": "long-password-123"})
        self.post("/api/avatar", {"color": "rose", "style": "crown"})
        self.post("/api/logout", {})
        self.post("/api/login", {"name": "WardrobeUser", "password": "long-password-123"})
        self.assertEqual(self.client.get("/api/state").get_json()["avatar"], {"color": "rose", "style": "crown"})


if __name__ == "__main__":
    unittest.main()
