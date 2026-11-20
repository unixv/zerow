"""Real Chromium rooms/shop playthrough using two permanent test accounts."""
from playwright.sync_api import sync_playwright, expect
from playtest import ARTIFACTS, register, login


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_context(viewport={"width": 1280, "height": 850})
        mobile = browser.new_context(viewport={"width": 390, "height": 844},
                                     is_mobile=True, has_touch=True)
        alice, bob = desktop.new_page(), mobile.new_page()
        errors = []
        for page in (alice, bob):
            page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            register(alice, "roomplayer_a")
            register(bob, "roomplayer_b")

            print("Creating a free home and earning the daily coin reward")
            alice.locator("#openRooms").click()
            expect(alice.locator("#homesOverlay")).to_be_visible()
            expect(alice.locator("#homesWallet")).to_contain_text("300 coins")
            alice.locator("#newHomeName").fill("The Fern Loft")
            alice.locator("#createHomeForm").get_by_role("button", name="Create").click()
            expect(alice.locator("#homesRoomTitle")).to_have_text("The Fern Loft")
            expect(alice.locator("#homeGrid button")).to_have_count(70)
            alice.locator("#claimCoins").click()
            expect(alice.locator("#homesWallet")).to_contain_text("400 coins")
            expect(alice.locator("#claimCoins")).to_be_disabled()

            print("Buying furniture, placing a chair, reloading and picking it up")
            alice.locator("#homesShop").get_by_role("button", name="Reading chair").click()
            expect(alice.locator("#homesWallet")).to_contain_text("365 coins")
            alice.locator("#homesInventory").get_by_role("button", name="Reading chair").click()
            alice.locator("#homeGrid").get_by_role("button", name="Tile 2,2").click()
            expect(alice.locator("#homeGrid").get_by_role("button", name="Pick up Reading chair at 2,2")).to_be_visible()
            alice.screenshot(path=str(ARTIFACTS / "atrium-furnished-room-desktop.png"), full_page=True)
            alice.reload()
            alice.locator("#openRooms").click()
            expect(alice.locator("#homeGrid").get_by_role("button", name="Pick up Reading chair at 2,2")).to_be_visible()

            print("Second player visits room but cannot edit furniture")
            bob.locator("#openRooms").tap()
            expect(bob.locator("#homesOverlay")).to_be_visible()
            bob.locator("#homesRooms").get_by_role("button", name="The Fern Loft").tap()
            expect(bob.locator("#homesRoomOwner")).to_contain_text("Visiting roomplayer_a")
            expect(bob.locator("#homeGrid").get_by_role("button", name="Pick up Reading chair at 2,2")).to_be_disabled()
            bob.locator("#viewHome").tap()
            assert bob.locator("#homeGrid").bounding_box()["y"] < 844, "390px room grid hidden below fold"
            bob.screenshot(path=str(ARTIFACTS / "atrium-furnished-room-mobile.png"), full_page=True)

            print("Two-player room gathering: visible roster, real chat and safe rendering")
            expect(alice.locator("#homesVisitorCount")).to_have_text("2 here", timeout=12000)
            expect(bob.locator("#homesVisitorCount")).to_have_text("2 here", timeout=12000)
            expect(alice.locator("#homesVisitors")).to_contain_text("roomplayer_b")
            expect(bob.locator("#homesVisitors")).to_contain_text("roomplayer_a")
            payload = "<img src=x onerror=alert(1)>"
            bob.locator("#homesChatDraft").fill(payload)
            bob.locator("#homesChatForm").get_by_role("button", name="Send").tap()
            expect(bob.locator("#homesChatDraft")).to_have_value("")
            expect(alice.locator("#homesRoomMessages")).to_contain_text(payload, timeout=12000)
            assert alice.locator("#homesRoomMessages img").count() == 0, "Room chat rendered HTML"
            alice.locator("#homesChatDraft").fill("Welcome to the Fern Loft!")
            alice.locator("#homesChatForm").get_by_role("button", name="Send").click()
            expect(bob.locator("#homesRoomMessages")).to_contain_text("Welcome to the Fern Loft!", timeout=12000)
            alice.screenshot(path=str(ARTIFACTS / "atrium-two-player-gathering-desktop.png"), full_page=True)
            bob.screenshot(path=str(ARTIFACTS / "atrium-two-player-gathering-mobile.png"), full_page=True)

            print("Narrow 320px Atrium Homes: visitor controls and viewport containment")
            bob.set_viewport_size({"width": 320, "height": 700})
            expect(bob.locator("#homesOverlay")).to_be_visible()
            bob.locator("#viewHome").tap()
            expect(bob.locator("#homesRoomTitle")).to_have_text("The Fern Loft")
            expect(bob.locator("#homeGrid").get_by_role("button", name="Pick up Reading chair at 2,2")).to_be_disabled()
            assert bob.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "320px room causes horizontal page overflow"
            for selector in ("#closeHomes", "#homesRoomTitle"):
                bounds = bob.locator(selector).bounding_box()
                assert bounds and bounds["x"] >= -1 and bounds["x"] + bounds["width"] <= 321, f"{selector} outside 320px viewport"
            title = bob.locator("#homesRoomTitle").bounding_box()
            grid = bob.locator("#homeGrid").bounding_box()
            assert title and grid and title["y"] >= 0 and grid["y"] < 700, "320px room must appear in initial viewport"
            bob.locator("#shopHomes").tap()
            expect(bob.locator("#homesShop").get_by_role("button", name="Reading chair")).to_be_visible()
            bob.locator("#viewHome").tap()
            assert bob.locator("#homeGrid").bounding_box()["y"] < 700, "return to room should restore visibility"
            bob.screenshot(path=str(ARTIFACTS / "atrium-furnished-room-320px.png"), full_page=True)

            alice.locator("#homeGrid").get_by_role("button", name="Pick up Reading chair at 2,2").click()
            expect(alice.locator("#homeGrid").get_by_role("button", name="Tile 2,2")).to_be_visible()
            expect(alice.locator("#homesWallet")).to_contain_text("365 coins")

            print("Rooms and balances survive returning-user login")
            alice.locator("#closeHomes").click()
            alice.locator("#logout").click()
            login(alice, "roomplayer_a")
            alice.locator("#openRooms").click()
            expect(alice.locator("#homesRoomTitle")).to_have_text("The Fern Loft")
            expect(alice.locator("#homesWallet")).to_contain_text("365 coins")
            expect(alice.locator("#homesInventory").get_by_role("button", name="Reading chair")).to_be_visible()
            assert not errors, "JavaScript errors: " + "; ".join(errors)
            print("ROOMS PLAYTEST PASSED: creation, currency, daily reward, shop, placement, visitor, persistence, pickup")
        except Exception:
            alice.screenshot(path=str(ARTIFACTS / "rooms-failure-desktop.png"), full_page=True)
            bob.screenshot(path=str(ARTIFACTS / "rooms-failure-mobile.png"), full_page=True)
            raise
        finally:
            desktop.close()
            mobile.close()
            browser.close()


if __name__ == "__main__":
    main()
