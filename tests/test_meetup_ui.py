"""Regression checks for Atrium's integrated contextual social directory."""
import unittest
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding="utf-8")

class MeetupUITests(unittest.TestCase):
    def test_meet_wave_chat_actions(self):
        self.assertIn('Meet explorers</h2>', HTML)
        self.assertIn('className="player-actions"', HTML)
        for action in ("Meet", "Wave", "Chat"):
            self.assertIn('textContent="' + action + '"', HTML)
        self.assertIn('await moveTo(latest.x,latest.y)', HTML)
        self.assertIn('await api("/api/emote","POST",{emote:"wave"})', HTML)
    def test_chat_draft_requires_send_and_escapes_player_names(self):
        self.assertIn('message.value="Hi "+p.name+"! "', HTML)
        self.assertIn("Press Send to share it with the plaza.", HTML)
        self.assertIn('name.textContent=p.name+', HTML)
        self.assertNotIn("name.innerHTML=p.name", HTML)
    def test_current_mobile_fixes_preserved(self):
        self.assertIn('data-close-expedition="mobileTrail"', HTML)
        self.assertIn('data-close-expedition="lanternMobile"', HTML)
        self.assertIn('id="send"', HTML)

if __name__ == "__main__":
    unittest.main()
