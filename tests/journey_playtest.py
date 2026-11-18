"""Behavioral regressions from the November 18 live Atrium playthrough.

Run only against the isolated CI Flask server, after tests/playtest.py.
"""
import re

from playwright.sync_api import sync_playwright, expect
from playtest import ARTIFACTS, register


def total_text(count):
    return f"{count} community {'light' if count == 1 else 'lights'} across Atrium"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        desktop = browser.new_context(viewport={"width": 1200, "height": 820})
        mobile = browser.new_context(viewport={"width": 390, "height": 844},
                                     is_mobile=True, has_touch=True)
        a, b = desktop.new_page(), mobile.new_page()
        errors = []
        for page in (a, b):
            page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            register(a, "journey_alice")
            register(b, "journey_bob")
            print("Desktop world and compose controls fit the viewport")
            assert a.evaluate("document.documentElement.scrollHeight <= innerHeight + 1")
            canvas = a.locator("#world")
            before = canvas.bounding_box()
            stage = a.locator(".stage").bounding_box()
            assert before and stage
            assert before["y"] >= stage["y"]
            assert before["y"] + before["height"] <= stage["y"] + stage["height"] + 1
            assert a.locator("#send").bounding_box()["y"] < 820
            for toggle, panel in (("#trailToggle", "#mobileTrail"),
                                  ("#lanternToggle", "#lanternMobile")):
                a.locator(toggle).click()
                expect(a.locator(panel).get_by_role("button", name=re.compile("^Close"))).to_be_visible()
                after = canvas.bounding_box()
                assert abs(before["height"] - after["height"]) < 1, "Panel shrank world"
                a.locator(panel).get_by_role("button", name=re.compile("^Close")).click()
                expect(a.locator(panel)).to_be_hidden()
                expect(a.locator(toggle)).to_be_focused()

            print("Walking near a landmark records discovery")
            canvas.click(position={"x": before["width"] * 7.5 / 16,
                                   "y": before["height"] * 4.5 / 11})
            a.wait_for_function("!movePending")
            canvas.press("ArrowUp")
            expect(a.locator("#trailStatus")).to_contain_text("1 of 4")
            expect(a.locator("#tipTitle")).to_have_text("Moonwell Fountain")

            print("Lantern visits also discover landmarks; counts update across players")
            total = int(re.search(r"\d+", a.locator("#lanternDeskBanner").inner_text()).group())
            a.locator("#lanternDeskList").get_by_role("button", name=re.compile("^Light North Grove,")).click()
            expect(a.locator("#trailStatus")).to_contain_text("2 of 4")
            expect(a.locator("#lanternDeskBanner")).to_have_text(total_text(total + 1))
            b.locator("#lanternToggle").click()
            b.locator("#lanternMobileList").get_by_role("button", name=re.compile("^Light North Grove,")).tap()
            expect(b.locator("#mobileTrailStatus")).to_contain_text("1 of 4")
            focused = a.locator("#lanternDeskList").get_by_role("button", name=re.compile("^Light South Grove,"))
            focused.focus()
            expect(a.locator("#lanternDeskBanner")).to_have_text(total_text(total + 2), timeout=10000)
            expect(focused).to_be_focused()
            b.locator("#lanternMobile").get_by_role("button", name="Close Lantern Circle").tap()

            print("Mobile quick greetings do not overlap Send")
            b.locator("#message").fill("Mobile journey smoke test")
            b.locator("#send").tap()
            expect(a.locator("#lines")).to_contain_text("Mobile journey smoke test", timeout=10000)
            assert b.evaluate("document.documentElement.scrollWidth <= innerWidth")

            print("Account and wardrobe dialogs trap focus, dismiss, and restore focus")
            for opener, panel, last, first in (("#accountSettings", "#accountScreen", "#closeAccount", "#currentPassword"),
                                               ("#avatarSettings", "#wardrobe", "#wardrobeSave", "#avatarColors button:first-child")):
                a.locator(opener).click()
                expect(a.locator(panel)).to_have_attribute("aria-modal", "true")
                expect(a.locator(first)).to_be_focused()
                a.locator(last).focus()
                a.keyboard.press("Tab")
                expect(a.locator(first)).to_be_focused()
                a.keyboard.press("Escape")
                expect(a.locator(panel)).to_be_hidden()
                expect(a.locator(opener)).to_be_focused()

            print("Chat submission keeps a newer draft and prevents duplicate submits")
            pending = []
            a.route("**/api/chat", lambda route: pending.append(route))
            a.locator("#message").fill("First pending message")
            a.locator("#message").press("Enter")
            expect(a.locator("#send")).to_be_disabled()
            a.locator("#message").fill("Keep this newer draft")
            a.locator("#message").press("Enter")
            assert len(pending) == 1
            pending[0].continue_()
            expect(a.locator("#send")).to_be_enabled()
            expect(a.locator("#message")).to_have_value("Keep this newer draft")
            a.unroute("**/api/chat")

            a.screenshot(path=str(ARTIFACTS / "journey-desktop.png"), full_page=True)
            b.screenshot(path=str(ARTIFACTS / "journey-mobile.png"), full_page=True)

            print("Revocation closes security dialog and clears the old account's draft")
            a.locator("#accountSettings").click()
            desktop.clear_cookies()
            expect(a.locator("#joinScreen")).to_be_visible(timeout=10000)
            expect(a.locator("#accountScreen")).to_be_hidden()
            expect(a.locator("#message")).to_have_value("")
            expect(a.get_by_role("textbox", name="Username", exact=True)).to_be_focused()
            assert not errors, errors
            print("JOURNEY PLAYTEST PASSED")
        except Exception:
            a.screenshot(path=str(ARTIFACTS / "journey-desktop-failure.png"), full_page=True)
            b.screenshot(path=str(ARTIFACTS / "journey-mobile-failure.png"), full_page=True)
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
