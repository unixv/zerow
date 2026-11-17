"""Atrium player-facing world smoke contract (no browser required)."""
import unittest
from pathlib import Path

PAGE = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding="utf-8")


class AtriumWorldTests(unittest.TestCase):
    def test_public_identity_is_atrium(self):
        self.assertIn("<title>Atrium — A World Together</title>", PAGE)
        self.assertIn("Welcome to Atrium", PAGE)
        self.assertIn("The Atrium · Central Plaza", PAGE)
        self.assertNotIn("Welcome to ZeroW", PAGE)

    def test_world_controls_and_existing_browser_contract(self):
        for token in ('id="world"', 'id="joinForm"', 'id="chatForm"', 'id="members"',
                      'id="accountSettings"', 'id="logout"', 'id="joinScreen"',
                      'canvas.addEventListener("click"', 'document.addEventListener("keydown"',
                      'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
                      'async function moveTo(x,y)', 'movePending'):
            with self.subTest(token=token):
                self.assertIn(token, PAGE)

    def test_scenery_and_character_rendering(self):
        for token in ('const scenery=', 't:"tree"', 't:"fountain"', 't:"lamp"',
                      'ctx.roundRect', 'ctx.ellipse', 'function draw()'):
            with self.subTest(token=token):
                self.assertIn(token, PAGE)


if __name__ == "__main__":
    unittest.main()
