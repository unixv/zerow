"""Lightweight regression checks for Atrium's contextual social player cards."""
import unittest
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding="utf-8")


class MeetupUITests(unittest.TestCase):
    def test_social_actions_are_available_in_room(self):
        self.assertIn('Meet explorers</h2>', HTML)
        self.assertIn('className="player-actions"', HTML)
        for action in ('Meet', 'Wave', 'Chat'):
            self.assertIn('textContent="' + action + '"', HTML)
        self.assertIn('min-height:40px', HTML)

    def test_greetings_are_not_auto_sent_or_injected_as_html(self):
        self.assertIn('message.value="Hi "+p.name+"! "', HTML)
        self.assertIn('Press Send to share it with the plaza.', HTML)
        self.assertIn('name.textContent=p.name+', HTML)
        self.assertNotIn('name.innerHTML=p.name', HTML)

    def test_meet_uses_latest_player_position_and_existing_authenticated_api(self):
        self.assertIn('people.find(person=>person.name===p.name)', HTML)
        self.assertIn('await moveTo(latest.x,latest.y)', HTML)
        self.assertIn('await api("/api/emote","POST",{emote:"wave"})', HTML)
        self.assertIn('if(p.name!==me&&me)', HTML)


if __name__ == "__main__":
    unittest.main()
