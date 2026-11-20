"""Two-account Atrium room presence and conversation regressions."""
import importlib
import os
import tempfile
import time
import unittest
from pathlib import Path


class RoomSocialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        os.environ["ZEROW_DB"] = str(Path(self.temp.name) / "atrium.sqlite3")
        import app
        self.game = importlib.reload(app)
        self.alice = self.game.app.test_client()
        self.bob = self.game.app.test_client()
        self.anon = self.game.app.test_client()
        for client, name in ((self.alice, "SocialAlice"), (self.bob, "SocialBob")):
            self.post(client, "/api/register", {"name": name, "password": "safe-password-123"})
        self.room = self.post(self.alice, "/api/homes/create", {"name": "Social lounge"}).json["room_id"]

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def post(client, url, data):
        return client.post(url, json=data, headers={"Origin": "http://localhost"})

    def test_join_presence_chat_and_room_isolation(self):
        social = f"/api/homes/{self.room}/social"
        visit = f"/api/homes/{self.room}/visit"
        chat = f"/api/homes/{self.room}/chat"
        self.assertEqual(self.post(self.alice, chat, {"message": "No visit"}).status_code, 403)
        self.assertEqual(self.post(self.alice, visit, {}).status_code, 200)
        self.assertEqual(self.post(self.bob, visit, {}).status_code, 200)
        self.assertEqual({p["name"] for p in self.alice.get(social).json["visitors"]},
                         {"SocialAlice", "SocialBob"})
        self.assertEqual(self.post(self.bob, chat, {"message": "Hello room!"}).status_code, 200)
        self.assertEqual(self.alice.get(social).json["messages"][-1]["body"], "Hello room!")
        other = self.post(self.bob, "/api/homes/create", {"name": "Other lounge"}).json["room_id"]
        self.post(self.bob, f"/api/homes/{other}/visit", {})
        self.assertEqual(self.post(self.bob, chat, {"message": "Wrong room"}).status_code, 403)
        self.assertEqual(len(self.bob.get(f"/api/homes/{other}/social").json["messages"]), 0)
        self.assertEqual([p["name"] for p in self.alice.get(social).json["visitors"]], ["SocialAlice"])
        self.assertEqual(self.post(self.alice, "/api/homes/leave", {}).status_code, 200)
        self.assertEqual(self.alice.get(social).json["visitors"], [])
        self.assertEqual(len(self.alice.get(social).json["messages"]), 1)

    def test_shared_walk_coordinates_and_authoritative_boundaries(self):
        visit = f"/api/homes/{self.room}/visit"
        move = f"/api/homes/{self.room}/move"
        social = f"/api/homes/{self.room}/social"
        self.assertEqual(self.post(self.anon, move, {"x": 1, "y": 0}).status_code, 401)
        self.assertEqual(self.post(self.bob, move, {"x": 1, "y": 0}).status_code, 403)
        self.post(self.alice, visit, {})
        self.post(self.bob, visit, {})
        for coordinates in ({"x": -1, "y": 0}, {"x": 10, "y": 0},
                            {"x": True, "y": 0}, {"x": 1.5, "y": 0}):
            self.assertEqual(self.post(self.bob, move, coordinates).status_code, 400)
        self.assertEqual(self.post(self.bob, move, {"x": 2, "y": 0}).status_code, 400)
        self.assertEqual(self.post(self.bob, move, {"x": 1, "y": 0}).status_code, 200)
        self.assertEqual(self.post(self.bob, move, {"x": 1, "y": 1}).status_code, 200)
        bob = next(p for p in self.alice.get(social).json["visitors"] if p["name"] == "SocialBob")
        self.assertEqual((bob["x"], bob["y"], bob["self"]), (1, 1, 0))
        self.assertEqual(sum(p["self"] for p in self.alice.get(social).json["visitors"]), 1)
        self.assertEqual(sum(p["self"] for p in self.bob.get(social).json["visitors"]), 1)
        item = self.post(self.alice, "/api/homes/buy", {"sku": "chair"}).json["item_id"]
        self.assertEqual(self.post(self.alice, "/api/homes/place",
                                   {"room_id": self.room, "item_id": item, "x": 2, "y": 1}).status_code, 200)
        self.assertEqual(self.post(self.bob, move, {"x": 2, "y": 1}).status_code, 409)
        self.post(self.bob, "/api/homes/leave", {})
        self.assertEqual(self.post(self.bob, move, {"x": 1, "y": 2}).status_code, 403)
        self.post(self.bob, visit, {})
        bob = next(p for p in self.alice.get(social).json["visitors"] if p["name"] == "SocialBob")
        self.assertEqual((bob["x"], bob["y"]), (0, 0))

    def test_security_validation_and_expiry(self):
        visit = f"/api/homes/{self.room}/visit"
        chat = f"/api/homes/{self.room}/chat"
        self.assertEqual(self.post(self.anon, visit, {}).status_code, 401)
        self.assertEqual(self.anon.get(f"/api/homes/{self.room}/social").status_code, 401)
        self.assertEqual(self.post(self.alice, "/api/homes/99999/visit", {}).status_code, 404)
        self.post(self.alice, visit, {})
        for message in ("", "a"*281, "\x00", 4):
            self.assertEqual(self.post(self.alice, chat, {"message": message}).status_code, 400)
        payload = '<img src=x onerror=alert(1)>'
        self.assertEqual(self.post(self.alice, chat, {"message": payload}).status_code, 200)
        self.assertEqual(self.alice.get(f"/api/homes/{self.room}/social").json["messages"][-1]["body"], payload)
        self.assertEqual(self.post(self.alice, chat, {"message": "spam"}).status_code, 429)
        with self.game.connect() as con:
            con.execute("UPDATE room_visitors SET seen=? WHERE room_id=?", (time.time()-60,self.room))
        self.assertEqual(self.post(self.alice, chat, {"message": "Expired"}).status_code, 403)
        self.assertEqual(self.alice.get(f"/api/homes/{self.room}/social").json["visitors"], [])


if __name__ == "__main__":
    unittest.main()
