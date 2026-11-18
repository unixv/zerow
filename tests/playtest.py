"""Exercise the real ZeroW UI as two registered users in Chromium.

Run with:
  python -m playwright install chromium
  ZEROW_BASE_URL=http://127.0.0.1:8000 python tests/playtest.py
An isolated SQLite database should be used for automated tests.
"""
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get("ZEROW_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ARTIFACTS = Path(os.environ.get("ZEROW_PLAYTEST_ARTIFACTS", "playtest-artifacts"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)
NAME_A, NAME_B = "playtest_alice", "playtest_bob"
PASSWORD = "LocalPlaytestPassword-123456"


def register(page, name):
    page.goto(BASE + "/", wait_until="domcontentloaded")
    expect(page.get_by_text("Welcome to Atrium")).to_be_visible(timeout=15000)
    page.locator("#nickname").fill(name)
    page.locator("#password").fill(PASSWORD)
    page.locator("#authSubmit").click()
    expect(page.locator("#joinScreen")).to_be_hidden(timeout=15000)
    expect(page.locator("#logout")).to_be_visible()
    expect(page.locator("#members")).to_contain_text(name, timeout=15000)


def login(page, name):
    page.goto(BASE + "/", wait_until="domcontentloaded")
    expect(page.get_by_text("Welcome to Atrium")).to_be_visible()
    page.locator("#authToggle").click()
    page.locator("#nickname").fill(name)
    page.locator("#password").fill(PASSWORD)
    page.locator("#authSubmit").click()
    expect(page.locator("#joinScreen")).to_be_hidden(timeout=15000)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        a = browser.new_context(viewport={"width": 1200, "height": 820})
        b = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True,
                                device_scale_factor=1, has_touch=True)
        alice, bob = a.new_page(), b.new_page()
        for page in (alice, bob):
            page.on("pageerror", lambda exc: errors.append(str(exc)))

        try:
            print("Registering two permanent test accounts")
            register(alice, NAME_A)
            register(bob, NAME_B)
            expect(alice.locator("#members")).to_contain_text(NAME_B, timeout=10000)
            expect(bob.locator("#members")).to_contain_text(NAME_A, timeout=10000)

            print("Player A sends chat; player B sees it")
            alice.locator("#message").fill("Hello from browser playtest")
            alice.locator("#send").click()
            expect(bob.locator("#lines")).to_contain_text("Hello from browser playtest", timeout=10000)

            print("Player B sends a reply")
            bob.locator("#message").fill("Reply from mobile player")
            bob.locator("#send").click()
            expect(alice.locator("#lines")).to_contain_text("Reply from mobile player", timeout=10000)

            print("Recovering missed chat after temporary browser network loss")
            a.set_offline(True)
            # Keep the browser open while its polling requests cannot reach Flask.
            alice.wait_for_timeout(2500)
            bob.locator("#message").fill("Message sent while Alice was offline")
            bob.locator("#send").click()
            expect(bob.locator("#lines")).to_contain_text(
                "Message sent while Alice was offline", timeout=10000
            )
            a.set_offline(False)
            expect(alice.locator("#joinScreen")).to_be_hidden(timeout=10000)
            expect(alice.locator("#lines")).to_contain_text(
                "Message sent while Alice was offline", timeout=15000
            )
            expect(alice.locator("#logout")).to_be_visible()

            print("Moving player A by clicking the game canvas")
            canvas = alice.locator("#world")
            bounds = canvas.bounding_box()
            assert bounds, "Game canvas is not visible"
            # Click center tile (6,4), accounting for responsive canvas scaling.
            canvas.click(position={"x": bounds["width"] * 6.5 / 16,
                                   "y": bounds["height"] * 4.5 / 11})
            # Confirm the live game UI sends movement and the shared API reflects it.
            alice.wait_for_function("""async () => {
              const state=await fetch('/api/state').then(r=>r.json());
              return state.players.some(p=>p.name==='playtest_alice' && p.x===6 && p.y===4);
            }""", timeout=10000)

            print("Keyboard exploration moves player A using WASD and arrows")
            alice.locator("#world").focus()
            alice.keyboard.press("d")
            alice.wait_for_function("""async () => {
              const state=await fetch('/api/state').then(r=>r.json());
              return state.players.some(p=>p.name==='playtest_alice' && p.x===7 && p.y===4);
            }""", timeout=10000)
            alice.keyboard.press("ArrowLeft")
            alice.wait_for_function("""async () => {
              const state=await fetch('/api/state').then(r=>r.json());
              return state.players.some(p=>p.name==='playtest_alice' && p.x===6 && p.y===4);
            }""", timeout=10000)

            print("Chat typing and arrow-key editing must not move the avatar")
            chat_input = alice.locator("#message")
            chat_input.focus()
            alice.keyboard.type("wasd")
            alice.keyboard.press("ArrowLeft")
            alice.keyboard.press("ArrowRight")
            expect(chat_input).to_have_value("wasd")
            alice.wait_for_timeout(500)
            alice.wait_for_function("""async () => {
              const state=await fetch('/api/state').then(r=>r.json());
              return state.players.some(p=>p.name==='playtest_alice' && p.x===6 && p.y===4);
            }""", timeout=10000)
            chat_input.fill("")

            print("Mobile touch moves player B and persists across reload")
            mobile_canvas = bob.locator("#world")
            mobile_bounds = mobile_canvas.bounding_box()
            assert mobile_bounds, "Mobile game canvas is not visible"
            # Tap tile (8, 5) using the actual touch-enabled mobile context.
            mobile_canvas.tap(position={"x": mobile_bounds["width"] * 8.5 / 16,
                                        "y": mobile_bounds["height"] * 5.5 / 11})
            bob.wait_for_function("""async () => {
              const state = await fetch('/api/state').then(r => r.json());
              return state.players.some(p => p.name === 'playtest_bob' && p.x === 8 && p.y === 5);
            }""", timeout=10000)
            bob.reload()
            expect(bob.locator("#joinScreen")).to_be_hidden(timeout=10000)
            bob.wait_for_function("""async () => {
              const state = await fetch('/api/state').then(r => r.json());
              return state.players.some(p => p.name === 'playtest_bob' && p.x === 8 && p.y === 5);
            }""", timeout=10000)

            print("Reloading preserves session")
            alice.reload()
            expect(alice.locator("#joinScreen")).to_be_hidden(timeout=10000)

            print("Logout, then login to same permanent account")
            alice.locator("#logout").click()
            expect(alice.locator("#joinScreen")).to_be_visible(timeout=10000)
            expect(alice.locator("#logout")).to_be_hidden()
            expect(alice.locator("#message")).to_be_disabled()
            expect(alice.locator("#members")).not_to_contain_text(NAME_A)
            login(alice, NAME_A)
            expect(alice.locator("#lines")).to_contain_text("Reply from mobile player", timeout=10000)
            alice.wait_for_function("""async () => {
              const state=await fetch('/api/state').then(r=>r.json());
              return state.players.some(p=>p.name==='playtest_alice' && p.x===6 && p.y===4);
            }""", timeout=10000)

            print("Revoked session clears previously rendered chat and player state")
            # Simulate server-side revocation without a page reload: the old UI
            # must not continue displaying private account state.
            a.clear_cookies()
            expect(alice.locator("#joinScreen")).to_be_visible(timeout=10000)
            expect(alice.locator("#lines")).to_be_empty(timeout=10000)
            expect(alice.locator("#members")).not_to_contain_text(NAME_A)
            expect(alice.locator("#message")).to_be_disabled()
            login(alice, NAME_A)
            expect(alice.locator("#lines")).to_contain_text(
                "Reply from mobile player", timeout=10000)

            print("Exploration guide and atmosphere work on desktop and mobile")
            for page in (alice, bob):
                page.locator("#exploreGuide").click()
                expect(page.locator("#worldtip")).to_be_visible()
                expect(page.locator("#tipTitle")).to_have_text("Welcome to the Atrium plaza")
                page.locator("#tipClose").click()
                expect(page.locator("#worldtip")).to_be_hidden()
                toggle = page.locator("#sceneToggle")
                expect(toggle).to_have_attribute("aria-pressed", "false")
                toggle.click()
                expect(toggle).to_have_attribute("aria-pressed", "true")
                expect(toggle).to_have_text("Daylight mode")
                toggle.click()
                expect(toggle).to_have_attribute("aria-pressed", "false")
                expect(toggle).to_have_text("Evening mode")

            print("Landmark discovery works through actual canvas clicks on both viewports")
            for page in (alice, bob):
                world = page.locator("#world")
                bounds = world.bounding_box()
                assert bounds, "Atrium canvas is not visible"
                # Moonwell Fountain is centered at tile (7, 2) in the 16x11 world.
                world.click(position={"x": bounds["width"] * 7.5 / 16,
                                      "y": bounds["height"] * 2.5 / 11})
                expect(page.locator("#worldtip")).to_be_visible()
                expect(page.locator("#tipTitle")).to_have_text("Moonwell Fountain")
                expect(page.locator("#tipBody")).to_contain_text("heart of Atrium")
                page.locator("#tipClose").click()
                expect(page.locator("#worldtip")).to_be_hidden()

            print("Quick greetings prefill chat without sending automatically")
            previous = alice.locator("#lines").inner_text()
            alice.locator('[data-quick="Meet me by the fountain!"]').click()
            expect(alice.locator("#message")).to_have_value("Meet me by the fountain!")
            assert alice.locator("#lines").inner_text() == previous, "Quick greeting sent chat without confirmation"
            alice.locator("#message").fill("")
            alice.locator("#chatFocus").click()
            expect(alice.locator("#message")).to_be_focused()

            print("Wardrobe changes persist and are visible to the other player")
            alice.locator("#avatarSettings").click()
            expect(alice.locator("#wardrobe")).to_be_visible()
            alice.locator("#avatarColors").get_by_role("button", name="Ocean").click()
            alice.locator("#avatarStyles").get_by_role("button", name="Crown").click()
            expect(alice.locator("#avatarColors").get_by_role("button", name="Ocean")).to_have_attribute("aria-pressed", "true")
            expect(alice.locator("#avatarStyles").get_by_role("button", name="Crown")).to_have_attribute("aria-pressed", "true")
            alice.locator("#wardrobeSave").click()
            expect(alice.locator("#wardrobe")).to_be_hidden(timeout=10000)
            bob.wait_for_function("""async () => {
              const state = await fetch('/api/state').then(r => r.json());
              return state.players.some(p => p.name === 'playtest_alice'
                && p.avatar_color === 'ocean' && p.avatar_style === 'crown');
            }""", timeout=10000)
            alice.reload()
            expect(alice.locator("#joinScreen")).to_be_hidden(timeout=10000)
            alice.locator("#avatarSettings").click()
            expect(alice.locator("#avatarColors").get_by_role("button", name="Ocean")).to_have_attribute("aria-pressed", "true")
            expect(alice.locator("#avatarStyles").get_by_role("button", name="Crown")).to_have_attribute("aria-pressed", "true")
            alice.locator("#wardrobeClose").click()
            alice.locator("#logout").click()
            login(alice, NAME_A)
            alice.locator("#avatarSettings").click()
            expect(alice.locator("#avatarColors").get_by_role("button", name="Ocean")).to_have_attribute("aria-pressed", "true")
            expect(alice.locator("#avatarStyles").get_by_role("button", name="Crown")).to_have_attribute("aria-pressed", "true")
            alice.locator("#wardrobeClose").click()
            bob.locator("#avatarSettings").click()
            expect(bob.locator("#avatarColors").get_by_role("button", name="Moss")).to_have_attribute("aria-pressed", "true")
            expect(bob.locator("#avatarStyles").get_by_role("button", name="Classic")).to_have_attribute("aria-pressed", "true")
            bob.locator("#wardrobeClose").click()

            print("Atrium Discovery Trail: all four landmarks, persistence, and account isolation")
            stops = ["Moonwell Fountain", "North Grove", "South Grove", "Lantern Walk"]
            desktop_stops = alice.locator("#trailStops")
            mobile_toggle = bob.locator("#trailToggle")
            mobile_toggle.click()
            expect(mobile_toggle).to_have_attribute("aria-expanded", "true")
            expect(bob.locator("#mobileTrail")).to_be_visible()
            for index, name in enumerate(stops, 1):
                alice.locator("#trailStops").get_by_role("button", name=name).click()
                expect(alice.locator("#trailStatus")).to_contain_text(f"{index} of 4")
                expect(desktop_stops.get_by_role("button", name=name)).to_have_attribute("aria-pressed", "true")
                bob.locator("#mobileTrailStops").get_by_role("button", name=name).click()
                expect(bob.locator("#mobileTrailStatus")).to_contain_text(f"{index} of 4")
                expect(bob.locator("#mobileTrailStops").get_by_role("button", name=name)).to_have_attribute("aria-pressed", "true")
            expect(alice.locator("#trailStatus")).to_contain_text("Trail complete")
            expect(bob.locator("#mobileTrailStatus")).to_contain_text("Trail complete")
            alice.reload()
            bob.reload()
            expect(alice.locator("#trailStatus")).to_contain_text("Trail complete")
            bob.locator("#trailToggle").click()
            expect(bob.locator("#mobileTrailStatus")).to_contain_text("Trail complete")
            alice.locator("#logout").click()
            expect(alice.locator("#trailStatus")).to_contain_text("0 of 4")
            login(alice, NAME_A)
            expect(alice.locator("#trailStatus")).to_contain_text("Trail complete")
            # A fresh browser context for Bob must not inherit Alice's browser-local trail.
            isolated = browser.new_context(viewport={"width": 1200, "height": 820})
            isolated_page = isolated.new_page()
            login(isolated_page, NAME_B)
            expect(isolated_page.locator("#trailStatus")).to_contain_text("0 of 4")
            isolated.close()

            print("Screenshots for UX review")
            alice.screenshot(path=str(ARTIFACTS / "desktop-lobby.png"), full_page=True)
            bob.screenshot(path=str(ARTIFACTS / "mobile-lobby.png"), full_page=True)
            assert not errors, "Browser JavaScript errors: " + "; ".join(errors)
            print("PLAYTEST PASSED: registration, two-player chat, movement, sessions, login, desktop/mobile")
        except Exception:
            alice.screenshot(path=str(ARTIFACTS / "desktop-failure.png"), full_page=True)
            bob.screenshot(path=str(ARTIFACTS / "mobile-failure.png"), full_page=True)
            raise
        finally:
            a.close()
            b.close()
            browser.close()


if __name__ == "__main__":
    main()
