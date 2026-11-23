"""Atrium immersive room layout contract; browser screenshots remain the visual gate."""
from pathlib import Path
import unittest

CSS = (Path(__file__).resolve().parents[1] / "static" / "rooms.css").read_text()
JS = (Path(__file__).resolve().parents[1] / "static" / "rooms.js").read_text()

class ImmersiveRoomLayoutTests(unittest.TestCase):
    def test_large_room_and_readable_chat(self):
        self.assertIn("aspect-ratio:1.62", CSS)
        self.assertIn("min-height:145px;max-height:260px", CSS)
        self.assertIn(".homes-chat input{min-height:44px;font-size:16px}", CSS)

    def test_mobile_and_short_desktop_have_dedicated_layouts(self):
        self.assertIn("@media(min-width:761px) and (max-height:760px)", CSS)
        self.assertIn("@media(max-width:350px)", CSS)
        self.assertIn("aspect-ratio:1.05", CSS)
        self.assertIn(".homes-roommessages{min-height:150px;max-height:230px}", CSS)

    def test_tools_drawer_dismissal_and_keyboard_safety(self):
        self.assertIn("homes-drawer-backdrop[hidden]", CSS)
        self.assertIn("width:min(340px,88vw)", CSS)
        self.assertIn('drawerBackdrop.addEventListener("click"', JS)
        self.assertIn('sidebar.setAttribute("aria-hidden",String(!open))', JS)
        self.assertIn('sidebar.inert=!open', JS)
        self.assertIn('setDrawer(false);drawerButton.focus();', JS)

    def test_accessibility_and_reduced_motion(self):
        self.assertIn(".homes-drawer-toggle:focus-visible", CSS)
        self.assertIn("@media(prefers-reduced-motion:reduce)", CSS)

if __name__ == "__main__":
    unittest.main()
