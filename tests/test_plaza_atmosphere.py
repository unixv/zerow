"""Atrium visual atmosphere remains optional and never changes game state."""
from pathlib import Path
import unittest

HTML = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text()

class PlazaAtmosphereContract(unittest.TestCase):
    def test_atrium_brand_and_ambient_control(self):
        self.assertIn("<title>Atrium", HTML)
        self.assertIn('id="ambientToggle"', HTML)
        self.assertIn('aria-pressed="true" title="Toggle animated atmosphere"', HTML)
        self.assertIn('ambienceEnabled=!ambienceEnabled', HTML)

    def test_animation_pauses_in_background(self):
        self.assertIn('!document.hidden&&joinScreen.hidden', HTML)
        self.assertIn('},125);', HTML)

    def test_no_new_server_dependency_or_movement_override(self):
        self.assertIn('async function moveTo(x,y)', HTML)
        self.assertIn('await api("/api/move","POST",{x,y})', HTML)
        self.assertIn('await api("/api/chat","POST",{message:text})', HTML)

if __name__ == "__main__":
    unittest.main()
