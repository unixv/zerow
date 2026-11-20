"""Regression contract for Atrium's room character rendering."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RoomCharacterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = (ROOT / "static/rooms.js").read_text()
        cls.css = (ROOT / "static/rooms.css").read_text()

    def test_nodes_survive_presence_polling(self):
        self.assertIn("const avatarNodes = new Map()", self.js)
        self.assertIn("let avatar=avatarNodes.get(key)", self.js)
        self.assertIn("if(!avatar){", self.js)
        self.assertIn("avatarNodes.set(key,avatar)", self.js)
        self.assertIn("if(!active.has(key)){node.remove();avatarNodes.delete(key);}", self.js)
        self.assertIn("avatarNodes.clear()", self.js)

    def test_safe_name_and_color_rendering(self):
        self.assertIn('avatar.querySelector(".homes-character-name").textContent=person.name', self.js)
        self.assertIn('avatar.setAttribute("aria-label",person.name+', self.js)
        self.assertIn('colors[person.avatar_color]||"#8fc9bc"', self.js)
        self.assertNotIn("avatar.innerHTML", self.js)

    def test_character_parts_and_motion(self):
        for part in ("shadow", "legs", "body", "head", "hair", "face", "name"):
            self.assertIn('homes-character-' + part, self.js)
            self.assertIn('.homes-character-' + part, self.css)
        self.assertIn('avatar.dataset.facing=', self.js)
        self.assertIn("homes-character-moving", self.js)
        self.assertIn("prefers-reduced-motion:reduce", self.css)

    def test_tile_clicks_remain_available(self):
        self.assertIn("pointer-events:none", self.css)
        self.assertIn("await walkTo(x,y)", self.js)
        self.assertIn('"/api/homes/"+id+"/move"', self.js)


if __name__ == "__main__":
    unittest.main()
