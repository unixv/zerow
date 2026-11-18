"""Regression checks for the lightweight Atrium discovery UI contract."""
import pathlib
import unittest

HTML = (pathlib.Path(__file__).resolve().parents[1] / "static" / "index.html").read_text()


class DiscoveryTrailContractTests(unittest.TestCase):
    def test_progress_is_account_scoped_and_reset_on_logout(self):
        self.assertIn('trailStoragePrefix+me.toLowerCase()', HTML)
        self.assertIn('me=null;discovered.clear();renderTrail()', HTML)
        self.assertIn('if(me!==result.me){me=result.me;loadTrail();}', HTML)

    def test_both_landmark_interactions_require_successful_travel(self):
        self.assertIn('if(await moveTo(x,y)&&landmark)', HTML)
        self.assertIn('if(await moveTo(l.x,l.y)){showLandmark(l);discoverLandmark(l);}', HTML)
        self.assertIn('await refresh();return true;', HTML)
        self.assertIn('catch(err){notify(err.message);return false;}', HTML)

    def test_discovery_progress_has_mobile_and_desktop_controls(self):
        for selector in ('id="trailStops"', 'id="mobileTrailStops"', 'id="trailToggle"', 'id="trailProgress"', 'id="mobileTrailProgress"'):
            with self.subTest(selector=selector):
                self.assertIn(selector, HTML)


if __name__ == "__main__":
    unittest.main()
