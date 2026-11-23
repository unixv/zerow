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

    def test_mobile_workshop_keeps_room_visible(self):
        self.assertIn("height:min(48dvh,390px)", CSS)
        self.assertIn("transform:translateY(105%)", CSS)
        self.assertIn("bottom:calc(min(48dvh,390px) + 12px)", CSS)
        self.assertIn("@media(max-width:760px) and (max-height:550px)", CSS)

    def test_room_atmosphere_and_character_scale(self):
        self.assertIn("/* Atrium room atmosphere:", CSS)
        self.assertIn("width:clamp(35px,4vw,46px)", CSS)
        self.assertIn("height:clamp(58px,6.2vw,76px)", CSS)
        self.assertIn("width:clamp(25px,7.5vw,34px)", CSS)
        self.assertIn("height:clamp(43px,12vw,58px)", CSS)
        self.assertIn(".homes-furnishing{width:125%;height:195%", CSS)

    def test_accessibility_and_reduced_motion(self):
        self.assertIn(".homes-drawer-toggle:focus-visible", CSS)
        self.assertIn("@media(prefers-reduced-motion:reduce)", CSS)

if __name__ == "__main__":
    unittest.main()
