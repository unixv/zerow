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
            alice.locator(".homes-drawer-toggle").click()
            alice.locator("#newHomeName").fill("The Fern Loft")
            alice.locator("#createHomeForm").get_by_role("button", name="Create").click()
            expect(alice.locator("#homesRoomTitle")).to_have_text("The Fern Loft")
            expect(alice.locator("#homeGrid button")).to_have_count(70)
            # Room creation is asynchronous; the reward control must not accept a dropped click.
            expect(alice.locator("#claimCoins")).to_be_enabled(timeout=12000)
            alice.locator("#claimCoins").click()
            expect(alice.locator("#homesWallet")).to_contain_text("400 coins")
            expect(alice.locator("#claimCoins")).to_be_disabled()

            print("Buying furniture, placing a chair, reloading and picking it up")
            alice.locator("#homesShop").get_by_role("button", name="Reading chair").click()
            expect(alice.locator("#homesWallet")).to_contain_text("365 coins")
            assert alice.locator("#homesInventory").evaluate("node => node.closest(\'#atriumRoomDrawer\') !== null"), "Inventory must live in the room tools drawer, not behind it"
            assert alice.locator("#homesInventory").evaluate("node => node.getBoundingClientRect().right <= node.closest(\'#atriumRoomDrawer\').getBoundingClientRect().right + 1"), "Inventory must fit inside room tools"
            # Growing shop/inventory lists must not overlap neighboring sections.
            assert alice.locator("#atriumRoomDrawer").evaluate("""drawer => {
                const sections = [...drawer.querySelectorAll(':scope > section')];
                return sections.every((section, index) => !index ||
                    section.getBoundingClientRect().top >=
                    sections[index - 1].getBoundingClientRect().bottom - 1);
            }"""), "Room tools sections overlap and intercept furniture clicks"
            # Inspect the actual hit target before clicking. A visible button may still
            # be covered by another drawer control, even if sections do not overlap.
            hit = alice.locator("#homesInventory").get_by_role("button", name="Reading chair").evaluate("""button => {
                button.scrollIntoView({block: 'center'});
                const rect = button.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const top = document.elementFromPoint(x, y);
                const describe = element => element && ({
                    tag: element.tagName, id: element.id, className: element.className,
                    text: (element.textContent || '').trim().slice(0, 90),
                    rect: (() => { const r = element.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })()
                });
                return {target: describe(button), top: describe(top),
                    drawer: describe(document.querySelector('#atriumRoomDrawer')),
                    inventory: describe(document.querySelector('#homesInventory')),
                    shop: describe(document.querySelector('#homesShop')),
                    sections: [...document.querySelectorAll('#atriumRoomDrawer > section')].map(describe),
                    hit: top === button || button.contains(top)};
            }""")
            print("ATRIUM INVENTORY HIT TEST:", hit, flush=True)
            assert hit["hit"], "Inventory Reading chair center is obstructed: " + repr(hit)
            alice.locator("#homesInventory").get_by_role("button", name="Reading chair").click()
            alice.get_by_role("button", name="Close room tools", exact=True).click()
            alice.locator("#homeGrid").get_by_role("button", name="Tile 2,2").click()
            expect(alice.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2")).to_be_visible()
            alice.screenshot(path=str(ARTIFACTS / "atrium-furnished-room-desktop.png"), full_page=True)
            alice.reload()
            alice.locator("#openRooms").click()
            expect(alice.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2")).to_be_visible()

            print("Second player visits room and can use seating without editing furniture")
            bob.locator("#openRooms").tap()
            expect(bob.locator("#homesOverlay")).to_be_visible()
            bob.locator(".homes-drawer-toggle").tap()
            bob.locator("#homesRooms").get_by_role("button", name="The Fern Loft").tap()
            # Selecting a room closes the drawer automatically; a second close tap
            # would target a button that is intentionally no longer present.
            expect(bob.locator(".homes-drawer-toggle")).to_have_attribute("aria-expanded", "false")
            expect(bob.locator("#homesRoomOwner")).to_contain_text("Visiting roomplayer_a")
            expect(bob.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2")).to_be_enabled()
            # The room is already visible after selecting it; the drawer can
            # overlay navigation buttons, so do not tap View room beneath it.
            assert bob.locator("#homeGrid").bounding_box()["y"] < 844, "390px room grid hidden below fold"
            bob.screenshot(path=str(ARTIFACTS / "atrium-furnished-room-mobile.png"), full_page=True)

            print("Two-player room gathering: visible roster, real chat and safe rendering")
            expect(alice.locator("#homesVisitorCount")).to_have_text("2 here", timeout=12000)
            expect(bob.locator("#homesVisitorCount")).to_have_text("2 here", timeout=12000)
            expect(alice.locator("#homesVisitors")).to_contain_text("roomplayer_b")
            expect(bob.locator("#homesVisitors")).to_contain_text("roomplayer_a")
            print("Walk together: touch and desktop tiles synchronize avatars")
            bob.locator("#homeGrid").get_by_role("button", name="Tile 1,0").tap()
            expect(bob.locator(".homes-walker-self")).to_have_attribute("aria-label", "roomplayer_b at 1,0", timeout=12000)
            expect(alice.locator(".homes-walker[aria-label='roomplayer_b at 1,0']")).to_be_visible(timeout=12000)
            alice.locator("#homeGrid").get_by_role("button", name="Tile 0,1").click()
            expect(bob.locator(".homes-walker[aria-label='roomplayer_a at 0,1']")).to_be_visible(timeout=12000)
            print("Shared seating: two browsers observe one occupied chair")
            seat = bob.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2")
            seat.tap()
            expect(bob.locator(".homes-walker-self.homes-character-seated")).to_be_visible(timeout=12000)
            expect(alice.locator(".homes-walker.homes-character-seated[aria-label^='roomplayer_b']")).to_be_visible(timeout=12000)
            bob.screenshot(path=str(ARTIFACTS / "atrium-seated-visitor-mobile.png"), full_page=True)
            alice.screenshot(path=str(ARTIFACTS / "atrium-seated-visitor-desktop.png"), full_page=True)
            alice.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2").click()
            expect(alice.locator("#homesStatus")).to_contain_text("already sitting", timeout=12000)
            seat.tap()
            expect(bob.locator(".homes-walker-self.homes-character-seated")).to_have_count(0, timeout=12000)
            alice.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2").click()
            expect(alice.locator(".homes-walker-self.homes-character-seated")).to_be_visible(timeout=12000)
            bob.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2").tap()
            expect(bob.locator("#homesStatus")).to_contain_text("already sitting", timeout=12000)
            alice.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2").click()
            expect(alice.locator(".homes-walker-self.homes-character-seated")).to_have_count(0, timeout=12000)
            bob.screenshot(path=str(ARTIFACTS / "atrium-shared-room-walking-mobile.png"), full_page=True)
            alice.screenshot(path=str(ARTIFACTS / "atrium-shared-room-walking-desktop.png"), full_page=True)
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
            expect(bob.locator("#homesRoomTitle")).to_have_text("The Fern Loft")
            expect(bob.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2")).to_be_enabled()
            assert bob.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "320px room causes horizontal page overflow"
            for selector in ("#closeHomes", "#homesRoomTitle"):
                bounds = bob.locator(selector).bounding_box()
                assert bounds and bounds["x"] >= -1 and bounds["x"] + bounds["width"] <= 321, f"{selector} outside 320px viewport"
            title = bob.locator("#homesRoomTitle").bounding_box()
            grid = bob.locator("#homeGrid").bounding_box()
            assert title and grid and title["y"] >= 0 and grid["y"] < 700, "320px room must appear in initial viewport"
            bob.locator("#shopHomes").tap()
            expect(bob.locator("#homesShop").get_by_role("button", name="Reading chair")).to_be_visible()
            bob.get_by_role("button", name="Close room tools", exact=True).tap()
            assert bob.locator("#homeGrid").bounding_box()["y"] < 700, "return to room should restore visibility"
            bob.screenshot(path=str(ARTIFACTS / "atrium-furnished-room-320px.png"), full_page=True)

            alice.locator("#homeGrid").get_by_role("button", name="Sit on Reading chair at 2,2").click(modifiers=["Shift"])
            expect(alice.locator("#homeGrid").get_by_role("button", name="Tile 2,2")).to_be_visible()
            expect(alice.locator("#homesWallet")).to_contain_text("365 coins")

            print("Rooms and balances survive returning-user login")
            alice.locator("#closeHomes").click()
            alice.locator("#logout").click()
            login(alice, "roomplayer_a")
            alice.locator("#openRooms").click()
            expect(alice.locator("#homesRoomTitle")).to_have_text("The Fern Loft")
            expect(alice.locator("#homesWallet")).to_contain_text("365 coins")
            # Returning players enter the room with tools closed. Open the
            # drawer explicitly instead of clicking the hidden shop shortcut.
            expect(alice.locator(".homes-drawer-toggle")).to_have_attribute("aria-expanded", "false")
            alice.locator(".homes-drawer-toggle").click()
            expect(alice.locator(".homes-drawer-toggle")).to_have_attribute("aria-expanded", "true")
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
