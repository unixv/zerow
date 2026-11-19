"""Persistent Atrium Homes and earned-coin economy security regressions."""
import importlib
import os
import tempfile
import unittest
from pathlib import Path


class HomesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ZEROW_DB"] = str(Path(self.tmp.name) / "atrium.sqlite3")
        import app
        self.game = importlib.reload(app)
        self.alice = self.game.app.test_client()
        self.bob = self.game.app.test_client()
        self.post(self.alice, "/api/register",
                  {"name": "RoomAlice", "password": "room-password-alice"})
        self.post(self.bob, "/api/register",
                  {"name": "RoomBob", "password": "room-password-bob"})

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def post(client, path, data):
        return client.post(path, json=data, headers={"Origin": "http://localhost"})

    def create(self, name="Sunroom"):
        r = self.post(self.alice, "/api/homes/create", {"name": name})
        self.assertEqual(r.status_code, 200, r.json)
        return r.json["room_id"]

    def test_free_first_room_then_paid_rooms_and_limit(self):
        home = self.alice.get("/api/homes").json
        self.assertEqual(home["coins"], 300)
        self.assertEqual(len(home["mine"]), 0)
        room_id = self.create()
        self.assertEqual(self.alice.get("/api/homes").json["coins"], 300)
        self.assertEqual(self.alice.get(f"/api/homes/{room_id}").json["room"]["owner"], "RoomAlice")
        self.create("Second room")
        self.assertEqual(self.alice.get("/api/homes").json["coins"], 150)
        self.create("Third room")
        self.assertEqual(self.alice.get("/api/homes").json["coins"], 0)
        self.assertEqual(self.post(self.alice, "/api/homes/create",
                                   {"name": "Fourth room"}).status_code, 409)
        self.assertEqual(len(self.alice.get("/api/homes").json["mine"]), 3)
        self.assertEqual(self.post(self.alice, "/api/homes/create",
                                   {"name": "<script>alert(1)</script>"}).status_code, 400)

    def test_buy_place_pick_up_and_visitor_read_only(self):
        room_id = self.create()
        buy = self.post(self.alice, "/api/homes/buy", {"sku": "sofa"})
        self.assertEqual(buy.status_code, 200, buy.json)
        item_id = buy.json["item_id"]
        self.assertEqual(buy.json["coins"], 180)
        place = {"room_id": room_id, "item_id": item_id, "x": 4, "y": 3}
        self.assertEqual(self.post(self.alice, "/api/homes/place", place).status_code, 200)
        self.assertEqual(self.post(self.alice, "/api/homes/place", place).status_code, 409)
        visitor = self.bob.get(f"/api/homes/{room_id}").json
        self.assertFalse(visitor["room"]["editable"])
        self.assertEqual(visitor["items"][0]["sku"], "sofa")
        self.assertEqual(self.post(self.bob, "/api/homes/pickup",
                                   {"room_id": room_id, "item_id": item_id}).status_code, 403)
        self.assertEqual(self.post(self.bob, "/api/homes/place", place).status_code, 403)
        self.assertEqual(self.post(self.alice, "/api/homes/pickup",
                                   {"room_id": room_id, "item_id": item_id}).status_code, 200)
        self.assertEqual(self.alice.get(f"/api/homes/{room_id}").json["items"], [])
        self.assertEqual(self.post(self.alice, "/api/homes/place",
                                   {"room_id": room_id, "item_id": item_id,
                                    "x": 2, "y": 5}).status_code, 200)
        self.assertEqual(self.alice.get(f"/api/homes/{room_id}").json["items"][0]["x"], 2)

    def test_tile_collisions_and_boundary_validation(self):
        room_id = self.create()
        item_1 = self.post(self.alice, "/api/homes/buy", {"sku": "chair"}).json["item_id"]
        item_2 = self.post(self.alice, "/api/homes/buy", {"sku": "plant"}).json["item_id"]
        self.assertEqual(self.post(self.alice, "/api/homes/place",
                                   {"room_id": room_id, "item_id": item_1, "x": 0, "y": 0}).status_code, 200)
        self.assertEqual(self.post(self.alice, "/api/homes/place",
                                   {"room_id": room_id, "item_id": item_2, "x": 0, "y": 0}).status_code, 409)
        for x, y in ((-1, 1), (10, 1), (1, 7), (True, 0)):
            self.assertEqual(self.post(self.alice, "/api/homes/place",
                                       {"room_id": room_id, "item_id": item_2, "x": x, "y": y}).status_code, 400)
        self.assertEqual(len(self.alice.get(f"/api/homes/{room_id}").json["items"]), 1)
        self.assertEqual(self.post(self.alice, "/api/homes/buy", {"sku": "bad-sku"}).status_code, 400)

    def test_daily_coin_claim_is_one_per_day_and_purchase_is_bounded(self):
        self.assertEqual(self.post(self.alice, "/api/homes/claim", {}).json["coins"], 400)
        self.assertEqual(self.post(self.alice, "/api/homes/claim", {}).status_code, 409)
        self.create("Room one")
        self.create("Room two")
        self.create("Room three")
        self.assertEqual(self.alice.get("/api/homes").json["coins"], 100)
        self.assertEqual(self.post(self.alice, "/api/homes/buy", {"sku": "sofa"}).status_code, 409)
        self.assertEqual(self.alice.get("/api/homes").json["coins"], 100)
        self.assertEqual(self.post(self.alice, "/api/homes/buy", {"sku": "lamp"}).status_code, 200)
        self.assertEqual(self.alice.get("/api/homes").json["coins"], 30)

    def test_auth_isolation_and_existing_data(self):
        unauth = self.game.app.test_client()
        self.assertEqual(unauth.get("/api/homes").status_code, 401)
        self.assertEqual(self.post(unauth, "/api/homes/claim", {}).status_code, 401)
        room_id = self.create()
        own = self.alice.get("/api/homes").json
        other = self.bob.get("/api/homes").json
        self.assertEqual(len(own["mine"]), 1)
        self.assertEqual(other["mine"], [])
        self.assertTrue(any(r["id"] == room_id for r in other["rooms"]))
        self.assertEqual(other["coins"], 300)
        self.assertEqual(self.post(self.bob, "/api/homes/create",
                                   {"name": "Bob room"}).status_code, 200)
        self.assertEqual(self.alice.get("/api/state").json["me"], "RoomAlice")
        self.assertEqual(self.post(self.alice, "/api/chat", {"message": "Room launch"}).status_code, 200)
        self.assertEqual(self.alice.get("/api/state").json["messages"][-1]["body"], "Room launch")


if __name__ == "__main__":
    unittest.main()
