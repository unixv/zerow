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


if __name__ == "__main__":
    unittest.main()
