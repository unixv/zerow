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

    def test_exploration_deck_and_social_controls(self):
        for token in ('id="exploreGuide"', 'id="sceneToggle"', 'id="chatFocus"',
                      'id="worldtip"', 'id="tipClose"', 'const landmarks=',
                      'function showLandmark(l)', 'aria-pressed', 'data-quick=',
                      'Evening mode', 'Moonwell Fountain', 'North Grove',
                      'South Grove', 'Lantern Walk', 'Message the Atrium plaza'):
            with self.subTest(token=token):
                self.assertIn(token, PAGE)

    def test_quick_greetings_are_prefilled_not_sent_without_confirmation(self):
        self.assertIn('message.value=button.dataset.quick', PAGE)
        self.assertIn('if(!me){notify("Log in to greet the plaza.")', PAGE)
        self.assertIn('document.querySelector("#chatForm").addEventListener("submit"', PAGE)
        self.assertNotIn('api("/api/chat","POST",{message:button.dataset.quick})', PAGE)

    def test_inline_script_has_no_literal_escaped_line_breaks(self):
        # A prior release inserted raw backslash-n tokens between JS statements,
        # preventing the entire game from initializing in Chromium.
        script = PAGE.split("<script>", 1)[1].split("</script>", 1)[0]
        self.assertNotIn(chr(92) + "n ", script)
        self.assertNotIn(chr(92) + "ncanvas.", script)
        self.assertNotIn(chr(92) + "ndocument.", script)

    def test_scenery_and_character_rendering(self):
        for token in ('const scenery=', 't:"tree"', 't:"fountain"', 't:"lamp"',
                      'ctx.roundRect', 'ctx.ellipse', 'function draw()'):
            with self.subTest(token=token):
                self.assertIn(token, PAGE)


if __name__ == "__main__":
    unittest.main()
