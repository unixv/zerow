"""Atrium shared seating regression contracts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SharedSeatingTests(unittest.TestCase):
    def test_server_validates_room_membership_and_seat_occupancy(self):
        source = (ROOT / "rooms.py").read_text()
        self.assertIn('def sit_in_home(room_id):', source)
        self.assertIn('def stand_in_home(room_id):', source)
        self.assertIn('seat["sku"] not in ("chair","sofa")', source)
        self.assertIn('abs(seat["x"]-visitor["x"])+abs(seat["y"]-visitor["y"]) > 1', source)
        self.assertIn('seat_item_id=?', source)
        self.assertIn('AND user_id<>? AND seen>?', source)
        self.assertIn('seat_item_id=NULL WHERE user_id=?', source)
        self.assertIn('SET seat_item_id=NULL WHERE seat_item_id=?', source)

    def test_player_can_sit_and_stand_without_losing_room_controls(self):
        source = (ROOT / "static/rooms.js").read_text()
        css = (ROOT / "static/rooms.css").read_text()
        self.assertIn('async function sitAt(item)', source)
        self.assertIn('"/sit","POST",{item_id:item.id}', source)
        self.assertIn('"/stand","POST",{}', source)
        self.assertIn('event.shiftKey', source)
        self.assertIn('homes-character-seated', css)
        self.assertIn('person.seat_item_id', source)



class SharedSeatingRuntimeTests(unittest.TestCase):
    """Exercise two real Flask sessions against isolated SQLite state."""

    def setUp(self):
        import importlib
        import os
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ZEROW_DB"] = str(Path(self.tmp.name) / "atrium.sqlite3")
        import app
        self.game = importlib.reload(app)
        self.alice = self.game.app.test_client()
        self.bob = self.game.app.test_client()
        self.eve = self.game.app.test_client()
        for client, name in ((self.alice, "SeatAlice"), (self.bob, "SeatBob"),
                             (self.eve, "SeatEve")):
            response = self.post(client, "/api/register",
                                 {"name": name, "password": "isolated-seat-test-password"})
            self.assertEqual(response.status_code, 200, response.json)
        created = self.post(self.alice, "/api/homes/create", {"name": "Social Lounge"})
        self.assertEqual(created.status_code, 200, created.json)
        self.room_id = created.json["room_id"]
        bought = self.post(self.alice, "/api/homes/buy", {"sku": "chair"})
        self.assertEqual(bought.status_code, 200, bought.json)
        self.seat_id = bought.json["item_id"]
        placed = self.post(self.alice, "/api/homes/place",
                           {"room_id": self.room_id, "item_id": self.seat_id, "x": 1, "y": 0})
        self.assertEqual(placed.status_code, 200, placed.json)

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def post(client, path, payload):
        return client.post(path, json=payload, headers={"Origin": "http://localhost"})

    def visit(self, client):
        return self.post(client, f"/api/homes/{self.room_id}/visit", {})

    def sit(self, client, seat_id=None):
        return self.post(client, f"/api/homes/{self.room_id}/sit",
                         {"item_id": self.seat_id if seat_id is None else seat_id})

    def social(self, client):
        response = client.get(f"/api/homes/{self.room_id}/social")
        self.assertEqual(response.status_code, 200, response.json)
        return {person["name"]: person for person in response.json["visitors"]}

    def test_two_players_share_exclusive_seat_and_stand(self):
        self.assertEqual(self.visit(self.alice).status_code, 200)
        self.assertEqual(self.visit(self.bob).status_code, 200)
        self.assertEqual(self.sit(self.alice).status_code, 200)
        self.assertEqual(self.social(self.bob)["SeatAlice"]["seat_item_id"], self.seat_id)
        self.assertEqual(self.sit(self.bob).status_code, 409)
        self.assertIsNone(self.social(self.alice)["SeatBob"]["seat_item_id"])
        self.assertEqual(self.post(self.alice, f"/api/homes/{self.room_id}/stand", {}).status_code, 200)
        self.assertEqual(self.sit(self.bob).status_code, 200)
        self.assertEqual(self.social(self.alice)["SeatBob"]["seat_item_id"], self.seat_id)

    def test_seating_rejects_unjoined_invalid_and_distant_players(self):
        self.assertEqual(self.sit(self.eve).status_code, 403)
        self.assertEqual(self.visit(self.eve).status_code, 200)
        for invalid in (True, "1", -1, 0, None):
            self.assertEqual(self.sit(self.eve, invalid).status_code, 400)
        self.assertEqual(self.sit(self.eve, 999999).status_code, 409)
        self.assertEqual(self.post(self.eve, f"/api/homes/{self.room_id}/move",
                                   {"x": 0, "y": 1}).status_code, 200)
        self.assertEqual(self.post(self.eve, f"/api/homes/{self.room_id}/move",
                                   {"x": 0, "y": 2}).status_code, 200)
        self.assertEqual(self.sit(self.eve).status_code, 409)

    def test_walking_leaving_and_pickup_clear_seat(self):
        self.assertEqual(self.visit(self.alice).status_code, 200)
        self.assertEqual(self.visit(self.bob).status_code, 200)
        self.assertEqual(self.sit(self.bob).status_code, 200)
        self.assertEqual(self.post(self.bob, f"/api/homes/{self.room_id}/move",
                                   {"x": 0, "y": 1}).status_code, 200)
        self.assertIsNone(self.social(self.alice)["SeatBob"]["seat_item_id"])
        self.assertEqual(self.sit(self.bob).status_code, 200)
        self.assertEqual(self.post(self.bob, "/api/homes/leave", {}).status_code, 200)
        self.assertNotIn("SeatBob", self.social(self.alice))
        self.assertEqual(self.sit(self.alice).status_code, 200)
        self.assertEqual(self.post(self.bob, "/api/homes/pickup",
                                   {"room_id": self.room_id, "item_id": self.seat_id}).status_code, 403)
        self.assertEqual(self.post(self.alice, "/api/homes/pickup",
                                   {"room_id": self.room_id, "item_id": self.seat_id}).status_code, 200)
        self.assertIsNone(self.social(self.alice)["SeatAlice"]["seat_item_id"])


if __name__ == "__main__":
    unittest.main()
