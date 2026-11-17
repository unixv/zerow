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
    expect(page.get_by_text("Welcome to ZeroW")).to_be_visible(timeout=15000)
    page.locator("#nickname").fill(name)
    page.locator("#password").fill(PASSWORD)
    page.locator("#authSubmit").click()
    expect(page.locator("#joinScreen")).to_be_hidden(timeout=15000)
    expect(page.locator("#logout")).to_be_visible()
    expect(page.locator("#members")).to_contain_text(name, timeout=15000)


def login(page, name):
    page.goto(BASE + "/", wait_until="domcontentloaded")
    expect(page.get_by_text("Welcome to ZeroW")).to_be_visible()
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

            print("Reloading preserves session")
            alice.reload()
            expect(alice.locator("#joinScreen")).to_be_hidden(timeout=10000)

            print("Logout, then login to same permanent account")
            alice.locator("#logout").click()
            expect(alice.locator("#joinScreen")).to_be_visible(timeout=10000)
            login(alice, NAME_A)
            expect(alice.locator("#lines")).to_contain_text("Reply from mobile player", timeout=10000)
            alice.wait_for_function("""async () => {
              const state=await fetch('/api/state').then(r=>r.json());
              return state.players.some(p=>p.name==='playtest_alice' && p.x===6 && p.y===4);
            }""", timeout=10000)

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
