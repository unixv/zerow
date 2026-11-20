"""Atrium personal sky settings: isolated SQLite and UI contract regression."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import app as atrium


class SceneStudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.object(atrium, "DB", Path(self.tmp.name) / "atrium.sqlite3")
        self.patch.start()
        self.client = atrium.app.test_client()
        with atrium.connect() as con:
            for name in ("skyone", "skytwo"):
                con.execute("INSERT INTO users(name,password_hash,created,last_login) VALUES(?,?,?,?)",
                            (name, "unused", time.time(), time.time()))
            user = con.execute("SELECT id FROM users WHERE name='skyone'").fetchone()["id"]
            con.execute("INSERT INTO sessions(token_hash,user_id,expires) VALUES(?,?,?)",
                        (atrium.token_hash("s" * 40), user, time.time() + 3600))
        self.client.set_cookie("zerow_session", "s" * 40)
        self.origin = {"Origin": "http://localhost"}

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_scene_saved_across_browser_sessions(self):
        self.assertEqual(self.client.get("/api/state").json["scene"], {"mode": "day", "ambience": True})
        response = self.client.post("/api/scene", headers=self.origin,
                                    json={"mode": "night", "ambience": False})
        self.assertEqual(response.status_code, 200)
        other_browser = atrium.app.test_client()
        other_browser.set_cookie("zerow_session", "s" * 40)
        self.assertEqual(other_browser.get("/api/state").json["scene"],
                         {"mode": "night", "ambience": False})
        self.assertEqual(self.client.post("/api/scene", headers=self.origin,
                                         json={"mode": "dusk", "ambience": True}).status_code, 200)
        self.assertEqual(other_browser.get("/api/state").json["scene"]["mode"], "dusk")
        with atrium.connect() as con:
            self.assertEqual(con.execute("SELECT scene_mode FROM users WHERE name='skytwo'").fetchone()[0], "day")

    def test_invalid_and_unauthorized_writes(self):
        for payload in ({"mode": "storm", "ambience": True},
                        {"mode": "night", "ambience": 1},
                        {"mode": None, "ambience": False},
                        {"mode": "day"}):
            self.assertEqual(self.client.post("/api/scene", headers=self.origin, json=payload).status_code, 400)
        self.assertEqual(self.client.post("/api/scene", json={"mode": "day", "ambience": True}).status_code, 403)
        self.assertEqual(atrium.app.test_client().post("/api/scene", headers=self.origin,
                         json={"mode": "night", "ambience": True}).status_code, 401)
        self.assertEqual(self.client.get("/api/state").json["scene"]["mode"], "day")

    def test_studio_ui_has_accessible_controls(self):
        html = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text()
        for mode in ("day", "dusk", "night"):
            self.assertIn('data-scene="' + mode + '"', html)
        self.assertIn('aria-label="Atrium scene studio"', html)
        self.assertIn('"/api/scene","POST"', html)
        self.assertIn('sceneLoadedFor!==result.me', html)


if __name__ == "__main__":
    unittest.main()
