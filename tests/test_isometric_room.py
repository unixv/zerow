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
        # Seated avatars project to their furniture tile; walkers use their own tile.
        self.assertIn("tileCenter(seat?seat.x:person.x,seat?seat.y:person.y)", source)
        self.assertIn("const seat=person.seat_item_id", source)
        self.assertIn("tileCenter(x,y)", source)

    def test_original_room_furnishings_and_characters(self):
        js = (ROOT / "static/rooms.js").read_text()
        css = (ROOT / "static/rooms.css").read_text()
        self.assertIn('furnishing.className="homes-furnishing"', js)
        # Assert the avatar's essential layers without freezing the exact
        # append call: additional visual layers (e.g. animated legs) are valid.
        append = re.search(r"avatar\.append\(([^)]*)\)", js)
        self.assertIsNotNone(append, "Avatar layers must be appended to the DOM")
        layers = [part.strip() for part in append.group(1).split(",")]
        self.assertEqual(len(layers), len(set(layers)), "Avatar layers must not repeat")
        for layer in ("shadow", "body", "face", "hair", "label", "bubble"):
            self.assertIn(layer, layers)
        self.assertEqual([layers.index(layer) for layer in
                          ("shadow", "body", "face", "hair", "label", "bubble")],
                         sorted(layers.index(layer) for layer in
                                ("shadow", "body", "face", "hair", "label", "bubble")))
        self.assertIn('label.textContent=person.name', js)
        for sku in ("chair", "sofa", "table", "lamp", "plant", "rug", "books", "flower"):
            self.assertIn('button[data-sku="' + sku + '"]', css)
        self.assertIn(".homes-character-face", css)
        self.assertIn(".homes-character-name", css)
        self.assertIn("@media(prefers-reduced-motion:reduce)", css)

    def test_room_first_social_interactions(self):
        js = (ROOT / "static/rooms.js").read_text()
        css = (ROOT / "static/rooms.css").read_text()
        for token in ("homes-drawer-toggle", "recentSpeech.set", "avatarNodes.clear()", "setDrawer(false)"):
            self.assertIn(token, js)
        for token in (".homes-speech-bubble[hidden]", ".homes-drawer-open .homes-sidebar", "@keyframes atrium-step"):
            self.assertIn(token, css)

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
