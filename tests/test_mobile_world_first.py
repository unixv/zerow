"""Atrium's mobile expedition panels must leave the world visible and dismiss cleanly."""
import pathlib
import unittest

HTML = (pathlib.Path(__file__).resolve().parents[1] / "static" / "index.html").read_text()

class MobileWorldFirstContract(unittest.TestCase):
    def test_both_drawers_have_accessible_close_controls(self):
        self.assertIn('data-close-expedition="mobileTrail"', HTML)
        self.assertIn('data-close-expedition="lanternMobile"', HTML)
        self.assertIn('aria-label="Close Discovery Trail"', HTML)
        self.assertIn('aria-label="Close Lantern Circle"', HTML)

    def test_world_first_drawer_is_bounded(self):
        self.assertIn("World-first mobile expedition drawers", HTML)
        self.assertIn("max-height:min(46%,280px)", HTML)
        self.assertIn("max-height:44%", HTML)
        self.assertIn("bottom:6px", HTML)
        self.assertIn("touch-action:manipulation", HTML)

    def test_dismissal_updates_accessibility_and_keyboard(self):
        self.assertIn("function closeExpeditionPanels()", HTML)
        self.assertIn('setAttribute("aria-expanded","false")', HTML)
        self.assertIn('e.key==="Escape"', HTML)
        self.assertIn("button.dataset.closeExpedition", HTML)

if __name__ == "__main__":
    unittest.main()
