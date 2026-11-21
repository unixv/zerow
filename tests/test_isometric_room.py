"""Static regression checks for Atrium's lightweight isometric room projection."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class IsometricRoomTests(unittest.TestCase):
    def test_room_projection_matches_existing_ten_by_seven_floor(self):
        source = (ROOT / "static/rooms.js").read_text()
        self.assertIn("const tileCenter=(x,y)", source)
        self.assertIn("50+(x-y)*4.35", source)
        self.assertIn("15+(x+y)*4.65", source)
        self.assertIn("tileCenter(person.x,person.y)", source)
        self.assertIn("tileCenter(x,y)", source)

    def test_interactive_tiles_and_visitors_remain_available(self):
        js = (ROOT / "static/rooms.js").read_text()
        css = (ROOT / "static/rooms.css").read_text()
        self.assertIn('canvas.append(b)', js)
        self.assertIn('canvas.append(avatarLayer)', js)
        self.assertIn('await walkTo(x,y)', js)
        self.assertIn('homes-isometric', css)
        self.assertIn('button:focus-visible', css)
        self.assertIn('@media(max-width:760px)', css)


if __name__ == "__main__":
    unittest.main()
