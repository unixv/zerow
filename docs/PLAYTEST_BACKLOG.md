# Atrium playtest backlog

Reviewed November 18, 2026. Production: https://atriumgame.fun/.
Scope: only unixv/zerow, publicly branded Atrium.

## Live browser evidence

The owner created the dedicated `oai` account in the cloud browser. Signed-in
play was verified, including another player appearing in the room. No credentials
are stored here. Do not reset this account or sign it out just to repeat testing.

| Feature | Actual live observation before this fix |
| --- | --- |
| Keyboard movement | Avatar moved onto Moonwell Fountain; trail stayed at 0/4. |
| Lantern travel | Lighting North Grove succeeded; trail still stayed at 0/4. |
| Discovery buttons | All four destinations recorded discoveries; 4/4 survived reload. |
| Lantern Circle | All four lights saved; revisit did not increase the count. |
| Lantern totals | Banner initially said zero while buttons showed existing lights; reload corrected it. |
| Desktop layout | World's lower tiles were clipped; Lantern Circle pushed almost the whole world below the visible stage. |
| Chat | Quick greeting prepared a draft; a custom QA chat message sent and appeared in history. |
| Avatar | Ocean/Crown saved and survived reload; cancelling Rose/Hoodie preserved the saved look. |
| Expressions | Wave, Cheer, Heart, Dance, Say hello were exercised; Wave animation visibly appeared. Other players' reception was not independently observed. |
| Scene | Day/evening and atmosphere controls toggled. These preferences reset on reload. |
| Account dialog | Open/Cancel worked; Escape failed to dismiss. No password change performed. |
| Session | Existing signed-in account and saved avatar/trail/lanterns survived reload. Logout/login not repeated live to retain the owner's session. |

## Fix bundle and acceptance criteria

- Walking, clicking, touch travel and lighting must use consistent discovery
  recording after successful movement, never after failed movement.
- The full canvas must fit inside its stage. Opening either expedition panel
  must preserve canvas size; both need a visible close control at every size.
- Mobile Send must remain reachable and clear of quick greetings. Recent CI
  runs on PRs #38/#39 failed because a quick-greeting button intercepted Send.
- Lantern totals must update on every state refresh, with stable controls that
  preserve keyboard focus during polling.
- Modal forms need labels, focus containment, Escape dismissal where appropriate,
  and focus restoration. Account revocation must dismiss stale dialogs.
- Clear chat/password drafts on sign-out; don't erase a new chat draft when an
  older submission completes; prevent repeated pending chat/auth submissions.

`tests/journey_playtest.py` covers these behaviors with two isolated accounts,
desktop and mobile views, real movement/taps, cross-player lantern updates,
network-delayed chat, modal keyboard navigation and session revocation. It runs
in the existing Player Playtest workflow after the broad original playthrough.
Keep isolated test results separate from production observations.

## Next substantial milestones

1. Finish verification and compatible integration of existing PRs #5, #9, #31,
   #33, #35, #38 and #39; diagnose failures instead of repeatedly leaving drafts.
2. Complete the contextual player directory and useful meetup interactions.
3. Add a coherent cooperative activity after the four-landmark tour, with clear
   progress and feedback; avoid accumulating decorative buttons without play value.
4. Persist discovery progress to the account so it follows the player across
   devices. Current progress is browser-local, unlike permanent lantern lights.
5. Add saved scene preferences and review 320px, tablet and short desktop layouts.
6. Expand two-player browser verification of expressions, chat scrollback,
   reconnection and avatar synchronization. Keep live mobile and cross-browser
   assertions marked untested until actually observed there.

Scheduled development should fix reproducible blockers first, then ship a
noticeable complete milestone. Scheduled QA should maintain this evidence and
coverage matrix, retest fixes, and close resolved backlog items with commit and
CI evidence. Never equate a green unit check with live Pi verification.

## Released fix verification

PR #40 merged as 51ec74366ed36563c6bf85a283b12f8b8d4e52df.
- Verify ZeroW passed (42 tests); Player Playtest run 44406118952 passed both
  the original playthrough and the new journey regression.
- After the Pi's automatic update, the public cloud-browser session showed
  the new labels, singular light counts, visible desktop panel close button,
  and full bounded canvas. Opening Lantern Circle preserved the actual canvas
  dimensions (644.36 by 443 pixels), rather than shrinking or displacing it.
- Account and wardrobe Escape dismissal and focus restoration were verified live.
- The dedicated account remained signed in with its saved avatar and progress.
- Fresh-discovery, mobile Send, delayed-chat and session-revocation regressions
  passed on isolated Chromium. Do not label those post-fix checks live mobile
  or fresh-account production verification.

The fix-bundle acceptance items above are implemented and covered. Keep the
next-milestone backlog active; this does not mean all possible game flaws are
resolved. Screenshots were inspected from CI and the live public browser.

## QA CI triage — November 18, 2026 (16:21 CST run)

This section records **isolated GitHub runner** evidence, not a fresh public-Pi browser session. The existing live observations above remain the production baseline.

| Coverage / PR | Current isolated evidence | Live production status |
| --- | --- | --- |
| Original browser playthrough and journey regression on released #40 | Player Playtest [44406118952](https://github.com/unixv/zerow/actions/runs/44406118952) passed both scenarios | Earlier post-release cloud-browser visual checks passed; not rerun in this triage |
| Lantern Circle two-player touch/click, idempotence, reload (#35) | Verify [44379528671](https://github.com/unixv/zerow/actions/runs/44379528671) and Playtest [44379528820](https://github.com/unixv/zerow/actions/runs/44379528820) passed on #35 head; still needs integration against latest main | Independent live two-player contribution untested |
| Stored chat HTML safety (#31) | Verify [44293524103](https://github.com/unixv/zerow/actions/runs/44293524103) and Playtest [44293524093](https://github.com/unixv/zerow/actions/runs/44293524093) passed on older PR head | Live injection not attempted |
| Mobile trail real taps (#33) | Verify [44303411633](https://github.com/unixv/zerow/actions/runs/44303411633) and Playtest [44303411681](https://github.com/unixv/zerow/actions/runs/44303411681) passed on older PR head | Live mobile untested |
| Session replacement (#9) | Verify [44054511400](https://github.com/unixv/zerow/actions/runs/44054511400) and Playtest [44054511426](https://github.com/unixv/zerow/actions/runs/44054511426) passed on older PR head; merge conflicts require rebase | Live second-browser replacement untested |
| Session expiry/logout unit coverage (#5) | Verify [44030146330](https://github.com/unixv/zerow/actions/runs/44030146330) failed on old head; requires diagnosis/rebase | Untested live |
| Two-player expression browser coverage (#38) | Verify [44400544672](https://github.com/unixv/zerow/actions/runs/44400544672) passed; Playtest [44400544524](https://github.com/unixv/zerow/actions/runs/44400544524) failed: #joinScreen stayed visible in a login/session assertion. Must diagnose/rebase, not infer a production expression defect | Cross-player expression reception untested live |
| Contextual player meetups (#39) | Verify [44401151106](https://github.com/unixv/zerow/actions/runs/44401151106) passed; Playtest [44401150832](https://github.com/unixv/zerow/actions/runs/44401150832) failed because mobile quick-greeting button intercepted Send. #40 subsequently fixed this class of UI issue on main, but #39 must be retested after integration | Meetup feature unverified live |
| Password changes, reconnect, avatar synchronization, chat scrollback, 320px/tablet/short desktop | Not established by these run results; retain as untested until explicit scenario evidence | Untested live |

**Merge gate:** The older passing PR checks are not evidence that combined changes pass on current main. Reconcile existing QA PRs without duplicating scenarios already in `tests/journey_playtest.py`; rerun both workflows on integration heads, inspect screenshots, then merge only verified compatible changes. Do not reset or sign out the dedicated production `oai` account.

## QA follow-up — November 18, 2026 (17:18 CST)

- Main `c449a42`: [Verify ZeroW 44412367661](https://github.com/unixv/zerow/actions/runs/44412367661) and [Player Playtest 44412367379](https://github.com/unixv/zerow/actions/runs/44412367379) passed on isolated GitHub runners. PR #42 changed world sizing; public Pi not rechecked here.
- [PR #41 Player Playtest 44411143112](https://github.com/unixv/zerow/actions/runs/44411143112) failed at `tests/playtest.py:252`: expected 2/4 discoveries, observed 1/4 after a destination click. A failing branch test, not evidence of a production regression; keep #41 blocked pending diagnosis.
- PR #38's cross-player expression test ran after a separate Bob login invalidated the original mobile session. Updated QA branch restores Bob's session before browser assertions and includes current-main playtest coverage. Both checks on new head required before merge. Live cross-player reception remains untested.
- Matrix: main registration/login, chat, movement, touch, session lifecycle, world expand = **passed isolated**; cross-player expression reception = **pending isolated #38**; password change, public mobile, network loss/reconnect, live cross-player expressions = **untested live**.

## Development integration — November 18, 2026 (17:24 CST)

- Reimplemented PR #41's Meet explorers directory against current main, preserving #40 mobile fixes and #42 world-first layout. The existing PR #41 had a failed isolated discovery test; its head is not approved for merge.
- New integrated branch includes real two-player Chromium assertions for Meet, Wave, and Chat draft behavior. **Not released until both workflows pass.**
- Live public Pi meetups, independent cross-player expression reception, and production mobile behavior remain untested. No production account was modified.

## QA verification — November 18, 2026 (18:22 CST)

- Current main `1e313893` inspected. Latest integration PR #43 commit `e65df204` passed [Verify ZeroW 44420638543](https://github.com/unixv/zerow/actions/runs/44420638543) and [Player Playtest 44420638461](https://github.com/unixv/zerow/actions/runs/44420638461) on isolated runners. Do not infer Pi deployment or production acceptance from those checks.
- Existing [QA PR #38](https://github.com/unixv/zerow/pull/38), head `f1d03f0a`, is mergeable but still draft. [Verify 44419643298](https://github.com/unixv/zerow/actions/runs/44419643298) and [Player Playtest 44419643696](https://github.com/unixv/zerow/actions/runs/44419643696) both passed on this exact head. Browser test asserts desktop Wave visible to Bob, mobile Heart visible to Alice, Bob's reauthenticated session, and expiry after reload. Artifact [14480463633](https://github.com/unixv/zerow/actions/runs/44419643696/artifacts/14480463633) exists; screenshots still need visual inspection before a QA-authorized merge.
- Current QA matrix: cross-player Wave/Heart synchronization and expiration = **passed isolated (#38)**, **untested live**; original desktop/mobile playthrough, movement, chat, session lifecycle = **passed isolated** on #43; 320px/tablet and short-desktop visual layout = **not independently reviewed**; password changes and network loss/reconnect = **untested in this run**. Preserve prior live observations separately.
- No new reproducible gameplay failure identified from the green runs. Older QA PRs #5, #9, #31, #33, #35 remain open and require integration/overlap review; PR #41 remains an older failed branch and must not be merged based on #43's success alone.

## Independent QA follow-up — November 18, 2026 (19:25 CST)

- Latest main `5cf7fb3` passed [Verify ZeroW 44428471249](https://github.com/unixv/zerow/actions/runs/44428471249) and [Player Playtest 44428471266](https://github.com/unixv/zerow/actions/runs/44428471266). These are isolated CI results, not Pi verification.
- Reviewed the actual artifact ZIP from [QA PR #38 Playtest 44419643696](https://github.com/unixv/zerow/actions/runs/44419643696), artifact 14480463633. It contains `desktop-lobby.png`, `mobile-lobby.png`, `journey-desktop.png`, `journey-mobile.png`, and a Flask server log. All four screenshots were visually inspected: the world and both players render, chat and Send are visible, the mobile game world fits horizontally, and the mobile journey screenshot shows the North Grove discovery panel. This completes the previously outstanding screenshot review for #38.
- [QA PR #38](https://github.com/unixv/zerow/pull/38) remains draft: the green checks were produced on its older branch head `f1d03f0`, before the latest main. It still requires rebasing/re-running both workflows before merging. Screenshot review is **passed isolated**, not production acceptance.
- New development [PR #44](https://github.com/unixv/zerow/pull/44) adds Atrium Homes. [Verify ZeroW 44436608452](https://github.com/unixv/zerow/actions/runs/44436608452) passed; [Player Playtest 44436608439](https://github.com/unixv/zerow/actions/runs/44436608439) was still running at review. Rooms, shop and currency are **not tested live**. No defect issue opened without reproducible evidence.
- Coverage matrix additions: desktop/mobile lobby visual composition **passed isolated (#38)**; two-player expressions **passed isolated (#38)**, **untested live**; room creation/shop/placement **pending isolated (#44)**, **untested live**; password changes, network loss/reconnect and live mobile play remain **untested live**.

## Atrium Homes release — November 18, 2026

- [PR #44](https://github.com/unixv/zerow/pull/44) merged as `4d7341cd`: player-owned public rooms, furniture catalog/inventory, tile placement and pickup, account wallets, 300 starter coins and 100 earnable daily coins. First room free; subsequent rooms cost 150 virtual coins. This is **in-game currency only**, with no real-money payment system.
- Server enforces currency balances, item ownership, room ownership, maximum room/inventory counts, occupied tiles, and single daily claims. Existing SQLite accounts, chat, and game state are preserved through additive schema changes.
- **Passed isolated CI:** [Verify ZeroW 44438357150](https://github.com/unixv/zerow/actions/runs/44438357150) and [Player Playtest 44438357072](https://github.com/unixv/zerow/actions/runs/44438357072). The latter runs the existing playtest and journey plus new `tests/rooms_playtest.py` (two users, shop, creation, placement, visitor restrictions, coins, reload/login persistence).
- **Prior defects caught by QA:** furniture inventory click inadvertently deselected automatically selected item; fixed before merging. Discovery Trail clicks could be dropped while another move was pending; movement requests now serialize with a bounded queue. The final full browser suite passed.
- **Live production:** atriumgame.fun deployment and new rooms UI are **not yet independently verified**. Do not label this a live Pi playtest. Verify new room creation, purchase, placement, visitor view, and 320px mobile layout on the live site before claiming production acceptance.
- **Next milestone:** avatars physically entering player rooms, room-specific presence/chat, privacy/guest permissions, furniture footprints and rotation, and optional payment-provider integration only after explicit scope and safety review.

## Independent QA verification — November 18, 2026 (20:20 CST)

- Confirmed [Atrium Homes PR #44](https://github.com/unixv/zerow/pull/44) is merged. Its final integration checks both passed: [Verify ZeroW 44438357150](https://github.com/unixv/zerow/actions/runs/44438357150) and [Player Playtest 44438357072](https://github.com/unixv/zerow/actions/runs/44438357072), on isolated runners. The playtest includes `tests/rooms_playtest.py`; this does **not** establish public Pi deployment or live gameplay acceptance.
- Investigated the earlier [failed Homes browser run 44436608439](https://github.com/unixv/zerow/actions/runs/44436608439) directly from job logs (job 135266937952). At failure the inventory UI still displayed `Select furniture from your inventory before choosing a tile` despite a visible `Reading chair` button. This was a pre-merge furniture-selection defect; subsequent final CI passed after the documented fix. Do not open a duplicate issue for the superseded head.
- [QA PR #38](https://github.com/unixv/zerow/pull/38) remains draft and currently reports mergeable=false against main; previously green runs/screenshots are not sufficient to merge without conflict reconciliation and both workflow reruns. QA PRs #33/#35 also remain draft and nonmergeable at this check. No unverified merge attempted.
- Coverage matrix: furniture purchase/placement/visitor restrictions/coin persistence = **passed isolated on merged #44**, **untested live**; expression cross-player/expiry = **passed isolated on older #38**, **untested live**, current-main integration **blocked**; public room UI, 320px layout, password changes, network loss/reconnect = **untested live**. Next: isolate PR overlap/conflicts, reconcile one QA scenario at a time, then test production rooms without altering other users' data.

## Independent QA — November 19, 2026 (00:20 CST)

- [PR #46](https://github.com/unixv/zerow/pull/46) latest head `6278e0de` corrected the discovery-count regular expression. The preceding [failed Chromium run 44458711520](https://github.com/unixv/zerow/actions/runs/44458711520) logged `Missing trail count: '1 of 4 landmarks discovered...'` because the regex did not match valid text. This was a test assertion defect, not a demonstrated game regression.
- Both current-head workflows passed: [Verify ZeroW 44465026373](https://github.com/unixv/zerow/actions/runs/44465026373) and [Player Playtest 44465026114](https://github.com/unixv/zerow/actions/runs/44465026114). Chromium artifact [14501144017](https://github.com/unixv/zerow/actions/runs/44465026114/artifacts/14501144017) is available; screenshot contents were **not independently visually inspected in this run**. Keep #46 draft until screenshot review and integration decision.
- Matrix: discovery count, first visit, revisit, completion and reload = **passed isolated on #46**; 320px Homes visitor layout = **pending isolated #45** (its head has not passed after this correction); live Pi Homes/mobile = **untested in this run**. No new production defect issue justified.

## Independent QA — November 19, 2026 (02:20 CST)

- [PR #46](https://github.com/unixv/zerow/pull/46) is now **merged** as `d078bc5b3fb989c014359fbb6bc920e1cff919cb`, superseding the previous pending-merge note. The last directly inspected checks on its branch were [Verify ZeroW 44465026373](https://github.com/unixv/zerow/actions/runs/44465026373) and [Player Playtest 44465026114](https://github.com/unixv/zerow/actions/runs/44465026114), both passed. This is isolated-runner evidence; the merge itself is not a new live Pi test.
- [QA PR #45](https://github.com/unixv/zerow/pull/45) remains **open, draft and nonmergeable**, based on head `e751acfa`; its earlier [Player Playtest 44451199944](https://github.com/unixv/zerow/actions/runs/44451199944) failed before the 320px Homes scenario. PR #46's merge fixes the shared discovery assertion on main but does not retroactively verify #45. Reconcile #45 against main, rerun both workflows and inspect the `atrium-furnished-room-320px.png` artifact before merging.
- Reviewed `tests/rooms_playtest.py` on main: two accounts cover room creation, daily coins, purchase, placement, pickup, visitor read-only access and account persistence at 1280px/390px. The 320px assertion remains **unmerged/untested on current main**. Production Homes and live mobile remain **untested** in this QA run; no live account was modified.
- No new reproducible application defect was established. No speculative issue or unverified merge was created. Latest workflow-run enumeration was unavailable through the available connector; the named runs above are the latest **directly inspected**, not asserted to be the latest repository-wide runs.


## Development candidate — November 19, 2026: account-synced Discovery Trail

- A new additive `trail_discoveries` SQLite table records each account's four landmark visits. No existing users, sessions, or browser-local progress are deleted.
- `POST /api/trail/discover` validates authentication, landmark index and proximity to the account's server-recorded position; repeat visits are idempotent. `GET /api/state` includes account discovery progress for other signed-in devices.
- The frontend merges server discoveries into the existing local trail cache and sends successful visits to the server. Existing browser-only discoveries remain visible locally but require a revisit to become verified server progress; do not claim historical browser-local visits were automatically migrated.
- New isolated tests cover repeat visits, cross-session progress, invalid inputs, and rejection of remote landmark claims. **Pending both required workflows and browser visual review; not released or verified on the Pi.**
- Next: a more substantial cooperative room activity and explicit multi-browser journey verification.

## Development candidate — November 19, 2026: Atrium Sky Studio

- Three selectable personal sky moods: Sunlit, Golden hour, and Starlight, with distinct plaza tile palettes, gradients and low-cost night stars. Existing lantern glow and world controls remain functional.
- The atmosphere animation switch and sky mode persist in additive account columns and synchronize when the same account signs in from another browser. The scene is a personal visual preference, not a shared global weather change.
- Authenticated POST /api/scene validates the strict mood enum and boolean setting; the existing JSON same-origin protection remains active. No existing accounts or furniture records are deleted.
- New isolated tests cover defaults, two-browser persistence, account isolation, invalid values, authentication and CSRF. Both workflows and Chromium screenshots must pass on the exact PR head before merging.
- **Not production-verified:** Real Pi performance, mobile interaction and production persistence remain untested until explicitly observed.
- Next substantial priority remains shared room presence, avatar movement and cooperative room activity. Older independent QA PRs are not superseded by this change.


## Sky Studio PR #52 CI triage — November 19, 2026

Initial head 5e22d21 failed both isolated workflows: Verify ZeroW run
[44629434216](https://github.com/unixv/zerow/actions/runs/44629434216)
failed an outdated source-string assertion after account-switch scene loading was
introduced; Player Playtest run [44629434233](https://github.com/unixv/zerow/actions/runs/44629434233)
failed the 1200×820 desktop world-width acceptance (600px minimum) because a
new studio toolbar consumed canvas height. Updated the assertion to retain
account-isolation coverage and moved the desktop studio into a floating dock
without taking another layout row. Both fixes require fresh CI and screenshot
review on the new PR head; do not merge on the previous failures. Live Pi
verification remains untested. On mobile the studio remains in normal flow.


## Development milestone — November 19, 2026: live room gatherings (PR pending)

- Added authenticated, room-scoped **visitor presence** (30-second expiry) and a
  lightweight **room conversation** panel to Atrium Homes. Players visiting the
  same room can see one another's names and exchange persistent messages;
  switching rooms changes the audience. The panel works with the existing
  320px-first room floor and furniture interactions.
- Server enforces room existence, active room membership before chat, session
  authentication, 280-character messages, 1.25-second chat cooldown and
  100-message-per-room retention. Messages are rendered with text nodes rather
  than HTML. Additive SQLite tables preserve existing accounts and furniture.
- New \`tests/test_room_social.py\` covers two-player presence, cross-room
  isolation, leaving, expiration, message retention, unauthorized requests,
  cooldown, and literal HTML payload storage. **Pending CI**; not yet verified
  in an isolated browser or on the public Raspberry Pi.
- Coverage matrix: room presence/chat = **implemented, unverified**;
  mobile live gameplay = **untested**; physical room avatar movement and
  interactive furniture remain **next milestone**. Keep both existing browser
  playtest entrypoints in the workflow.


### Room gathering CI follow-up — November 19, 2026

- PR #54 head `2ef5f51`: Verify ZeroW [44661182382](https://github.com/unixv/zerow/actions/runs/44661182382) passed; Player Playtest [44661180713](https://github.com/unixv/zerow/actions/runs/44661180713) failed in `tests/rooms_playtest.py` after daily claim: expected 365 coins after chair purchase but wallet remained 400. The buy click could be ignored while the preceding claim's asynchronous reload retained the shared `running` guard.
- Follow-up `1e25129`: disable shop buttons during the pending transaction, then restore their correct affordability state after completion; clear room-chat message signature when changing rooms so coincident message IDs cannot hide a different conversation. Both workflows and screenshot review remain required on the new head; no production Pi verification.

## Two-player room gathering browser acceptance — November 20, 2026

- Added a real two-context Chromium scenario to `tests/rooms_playtest.py`: desktop owner and mobile visitor both see the same two-person roster; visitor sends an HTML-shaped message that must render as inert text on the owner's screen; owner replies and visitor receives it. Dedicated desktop/mobile gathering screenshots are captured for inspection.
- This is **isolated browser coverage only**, not a production Pi or cloud-browser observation. The new scenario is **pending Verify ZeroW, ZeroW Player Playtest, and screenshot review on the new PR #54 head**. Existing API-level social tests passed on the preceding head, but do not substitute for this end-to-end check.
- PR #55's enlarged chat remains a separate unmerged release; review compatibility against current main before merging either PR. Walkable room avatars and direct furniture interaction remain unimplemented.


## November 20 — readable chat integration after room gatherings

- Reintegrated PR #55's docked desktop chat, streamlined controls and both browser regression suites onto main after PR #54's room gathering merge, without replacing room backend or QA branches.
- This integration is a new candidate, not an approved release. Verify ZeroW, ZeroW Player Playtest and desktop/mobile screenshot acceptance must pass on this exact head before merge.
- The earlier PR #55 head passed isolated checks before #54 merged, but those checks do not establish integration correctness. Production Raspberry Pi deployment and live room walkability remain unverified.
- Next gameplay milestone: synchronized avatars moving inside room floors, direct furniture placement and interaction, and room-local cooperative activity.

## Walkable shared rooms candidate — November 20, 2026

- New candidate milestone: 10×7 room floor now supports owner and guest tap/click walking. The browser computes a shortest unobstructed tile route; the server validates each adjacent step, room membership, room boundaries, and furniture collision. No new heavyweight runtime dependencies.
- Active visitors are rendered as moving, wardrobe-colored avatars with initials, positions and names, updated through the existing 3.5-second social poll. Room-specific chat and furniture ownership rules remain intact.
- New isolated regressions: `tests/test_room_social.py` covers two-player coordinates, blocked movement, invalid inputs, leave/rejoin; `tests/rooms_playtest.py` covers desktop click and mobile touch movement plus screenshots and cross-player reception.
- **Release gate:** This branch is not production. Run Verify ZeroW and ZeroW Player Playtest on the exact integration head; inspect walking screenshots at desktop, mobile and 320px. Confirm old room purchase, placement, pickup, visitor restrictions and chat tests still pass. Do not merge on failed checks.
- **Live evidence:** No public Pi walking verification yet. Prior live evidence is unchanged.
- **Remaining larger-game milestone:** replace initials with more expressive sprite avatars and add furniture interactions and cooperative activities. Do not claim those features exist yet.


## Room-first isometric milestone — November 20, 2026

The owner rejected the previous flat room-management grid as the primary gameplay
experience. Atrium must present an original, inhabitable isometric social room,
with the floor as the focal point. Never include external game names in
source, PRs, documentation, test names, or player-facing content.

Development branch `feat/atrium-isometric-room-first-20261120` begins this
transition without changing the SQLite schema or existing room APIs:
- Shared projection for all 70 floor tile controls and all visitor avatars.
- Isometric diamond floor, angled wall backdrop, depth-based layering,
  full-height visitor markers, responsive sizing, and keyboard-focus styling.
- Existing room movement, server-authoritative furniture placement,
  inventory, coins, and room chat remain wired to the same tile coordinates.

**Release gate:** This is a first visual iteration, not the complete target.
Before merging, require both Verify ZeroW and ZeroW Player Playtest green
on the exact head and inspect actual desktop, 320px, and mobile screenshots.
Check whether touch targets are usable, furniture labels/avatars remain visible,
walls do not cover the floor, movement and furniture selection still work,
and chat remains reachable. Mark production Pi visuals **untested** until
actually observed there. If screenshots show problems, fix and rerun CI.

**Following cohesive milestone:** original illustrated furniture sprites,
proper isometric wall/floor depth, walking/sitting animations, in-room speech
bubbles, and a room-first mobile navigator. Avoid superficial button changes.


## Isometric scene visual expansion — November 20, 2026

The draft isometric room PR now includes original CSS-drawn furniture for all eight existing catalog categories, full-body characters with nameplates, larger scene-first desktop layout, and a compact mobile layout. Existing SQLite items, room membership, wallet, movement API and chat remain unchanged. Static tests assert renderer hooks and catalog coverage. **Visual acceptance remains pending** until both required CI workflows pass on the updated head and fresh desktop/mobile/320px/two-player screenshots are inspected. Do not merge on static tests alone. Public Raspberry Pi deployment and signed-in live play are unverified for this revision.

Remaining major work: direct sitting and object interactions, speech bubbles, expressive animation, responsive scene viewport validation, and improved contextual room navigator/shop drawers. Keep the original pixel-art direction and Atrium-only naming.


## November 20 — room-first social interface candidate

- Room tools are now a contextual drawer instead of occupying permanent desktop width; the isometric room uses the full available stage and chat is taller.
- Recent room chat messages can appear as transient, text-only speech bubbles above the corresponding visitor. Character DOM nodes persist between polls, allowing walking transitions without recreating every avatar.
- No new dependencies or SQLite schema changes. Room selection closes the tools drawer; closing the game resets social state.
- **Unverified candidate:** both workflows and desktop/mobile screenshots must pass on the latest PR #59 head. Live Pi gameplay remains untested. Test the drawer, speech visibility/expiry, character motion, and existing movement/chat/purchase flows before merge.


## Room-first CI follow-up — November 20, 2026

- PR #59 commit `0a64472`: [Verify ZeroW 44861131412](https://github.com/unixv/zerow/actions/runs/44861131412) passed; [Player Playtest 44861131564](https://github.com/unixv/zerow/actions/runs/44861131564) failed because the new contextual drawer intentionally hides `#newHomeName`, while the old browser journey tried to fill it without opening the drawer. The original and journey playtests passed earlier in the same run. This is an isolated browser regression, not a live Pi observation.
- Updated `tests/rooms_playtest.py` to open the Rooms & furniture drawer before creating rooms and visiting rooms, and close it before interacting with the floor. Updated the walker renderer to retain the walking class and refresh position accessibility labels during social polling.
- Both required workflows must pass on the new integration head, followed by inspection of desktop, mobile, 320px, furnished-room and two-player screenshots. Do not merge while either check is missing or failing. Live Pi deployment and signed-in production room interactions remain unverified.


## Isometric room PR #59 CI follow-up — November 20, 2026

- Commit `f2b18b4` passed [Verify ZeroW 44866371470](https://github.com/unixv/zerow/actions/runs/44866371470), but [Player Playtest 44866371430](https://github.com/unixv/zerow/actions/runs/44866371430) failed at `tests/rooms_playtest.py:24`: the unscoped accessible-name query for `Rooms & furniture` matched both the plaza launch button and the room drawer toggle (Playwright strict-mode violation). The base and journey playtests passed before the room test failed.
- Corrective commit `2bbdf9a` scopes both room-tool toggle interactions to `.homes-drawer-toggle`. This is a test locator correction, not proof of completed visual acceptance. Both workflows must run again on the updated PR head; retain draft status and do not merge on prior checks.
- Public Pi, fresh desktop/mobile screenshots and live signed-in room play remain **unverified** for this candidate.


## Room-first PR #59 follow-up — November 21, 2026

- PR head `bfb5ef2` passed Verify ZeroW [44871297767](https://github.com/unixv/zerow/actions/runs/44871297767) but failed Player Playtest [44871298014](https://github.com/unixv/zerow/actions/runs/44871298014). The browser failed clicking the purchased Reading chair in `#homesInventory`: another button or the sidebar itself intercepted pointer events. This is a real drawer usability defect, not a selector ambiguity.
- Candidate `abea429` keeps the expanded room-tools drawer in normal block flow and gives its dynamically expanding inventory room to scroll, instead of grid layout potentially overlapping controls. The existing real-browser furniture purchase/select/place journey is the regression gate.
- **Unverified candidate:** both workflows must pass on this exact head; inspect updated desktop/mobile/320px screenshots before approving merge. No public Pi acceptance is claimed.

## Atrium isometric room PR #59 — November 21, 2026 drawer regression

- Latest inspected candidate `4db57d2`: Verify ZeroW [44875376197](https://github.com/unixv/zerow/actions/runs/44875376197) passed, but Player Playtest [44875376212](https://github.com/unixv/zerow/actions/runs/44875376212) failed at the furniture inventory click: other room-drawer controls intercepted pointer events. Previous CSS flow fix did not resolve the browser failure.
- Follow-up candidate uses explicit vertical flex layout for the expanded drawer and non-shrinking sections, and adds a Chromium geometry assertion that drawer sections cannot overlap. This is **not verified** until both workflows pass on the latest commit and screenshots are inspected.
- Do not merge PR #59 on earlier green results. Preserve existing account/coin/room data; Pi production remains unverified.

## November 21 room release gate

- On PR #59 commit `38061a3`, Verify ZeroW passed, while Player Playtest failed in `tests/rooms_playtest.py`: immediately after creating a room, the daily reward click was ignored and the wallet remained at 300 coins. The room-creation handler still held the shared `running` lock; the reward control appeared enabled and silently returned.
- Follow-up fix disables the reward control while room creation is pending, restores its correct state when the operation completes, and explicitly waits for readiness in the browser journey. This is an isolated CI diagnosis, not a production observation.
- Both required workflows must pass on the updated head; inspect fresh desktop/mobile screenshots before merging. Live Raspberry Pi deployment remains unverified.


## November 21 — room drawer containment follow-up

- PR #59 head `3fae240`: [Verify ZeroW 44894651797](https://github.com/unixv/zerow/actions/runs/44894651797) passed; [Player Playtest 44894651664](https://github.com/unixv/zerow/actions/runs/44894651664) failed again at `tests/rooms_playtest.py:45`. Playwright identified a button within `#atriumRoomDrawer` intercepting pointer events when selecting the purchased Reading chair from `#homesInventory`.
- Candidate `da1fae9` removes the accumulated competing drawer overrides and `display:contents` flattening. Drawer sections now remain ordinary block containers with intrinsic-height shop/inventory grids and one scroll owner. This addresses the actual hit-target failure rather than bypassing browser clickability checks.
- **Unverified:** rerun both workflows on the exact new head and inspect desktop/mobile/320px screenshots. Do not merge while either check fails. Production Raspberry Pi and signed-in live room gameplay remain untested for this release.

## November 21 room inventory hit-test root cause

GitHub Player Playtest run 44909384222 showed the Reading chair inventory button at x=35..164, y=507..555 while the room-tools drawer was open. The furniture shop's Floor lamp button at y=512..554 received the pointer event. The inventory was rendered in `.homes-main` **behind** the overlay drawer, not within the drawer; prior CSS changes could not solve this structural overlap. Commit bc6daf5 moves inventory into the drawer as its own section and updates placement guidance; commit 159bfb9 adds DOM containment and drawer-width assertions. This is an isolated runner finding, not a production Pi observation. Both required workflows and updated visual screenshots must pass before merging PR #59.

## November 21 — furniture selection passes; visitor test corrected

- PR #59 commit `d19e9f7`: [Verify ZeroW 44919018926](https://github.com/unixv/zerow/actions/runs/44919018926) passed; [Player Playtest 44919018916](https://github.com/unixv/zerow/actions/runs/44919018916) failed later in the two-player room scenario.
- Chromium's measured Reading chair inventory hit test returned `hit: true`: the selected button itself received pointer events. The previous furniture obstruction is resolved in the isolated runner.
- New failure: after the visitor selects a room, `renderRooms()` automatically closes the drawer, but the test attempted to tap the now-absent `Close room tools` button and timed out. Commit `a30be32` updates the browser test to assert that the drawer is closed instead of attempting a redundant tap. This is a test expectation correction, not a production Pi observation.
- Both workflows must pass on the latest commit and desktop/mobile screenshots must be reviewed before PR #59 can merge. Remaining visitor movement, chat, 320px and login checks have not yet completed in this run.


## November 21 — 320px viewport restoration candidate

- PR #59's previous head `03422a6` passed Verify ZeroW (run 44930263258) but failed Player Playtest (run 44930263225) at the 320×700 initial-room visibility assertion after the two-player journey. Earlier furniture selection, room visiting, movement, and shared chat steps reached completion.
- Candidate `f43984b` resets the nested room/content scroll positions when closing the tools drawer and on viewport resize, preventing stale scroll positions from hiding the selected room after mobile transitions. This is a proposed fix, not verified evidence of success.
- Both required workflows and desktop/mobile screenshot inspection remain outstanding on this head. No live Raspberry Pi verification; do not merge before the gates pass.


## November 21 — character renderer integration checkpoint

- PR #59 integrates directional full-body character presentation into its existing isometric projection: facing changes as players walk, lightweight stride animation, separate legs/arms, outfit-specific hair/headwear, persistent DOM nodes, and retained in-room speech bubbles. Commits `223f6ac` and `6ce0fe2`.
- The separate PR #58 is not merged; its orthographic placement must not overwrite PR #59's isometric coordinate projection. This integration preserves the room-first branch's multiplayer and chat logic.
- **Status: unverified candidate.** Run Verify ZeroW and ZeroW Player Playtest on the exact latest head; inspect two-player desktop, 320px and tablet screenshots for avatar position, leg/arm rendering, speech overlap, and furniture occlusion. No production Pi observation or visual acceptance is claimed. Keep draft until both workflows and visual acceptance pass.

## Shared seating integration — November 22, 2026

Draft [PR #64](https://github.com/unixv/zerow/pull/64) targets the isometric room candidate #59.
The proposed player milestone is shared chair/sofa seating with a distinct avatar pose,
authoritative occupancy, visitor interaction, stand-on-repeat-tap and owner Shift-click
pickup. The migration adds a nullable visitor-only seat reference; accounts, furniture
inventory and coin balances are not rewritten.

| Acceptance case | Status |
| --- | --- |
| Seat and stand server contracts | Added source regression; runtime not yet verified |
| Two users see the same occupied seat | Untested in browser |
| Two users cannot occupy one seat | Untested in browser |
| Remote seat releases after moving, leaving or pickup | Untested in browser |
| Visitor cannot pick up furniture | Existing permission boundary; recheck in browser |
| 320px and desktop furniture hit targets | Untested visual |
| Verify ZeroW and Player Playtest on exact PR head | Pending |
| Production Pi deployment and signed-in play | Not verified |

Do not merge #64 or #59 based on source checks alone. Expand isolated two-account
Chromium seating assertions, inspect updated screenshots, and integrate independent QA
#63 without overwriting its branch.


## November 22 — shared seating browser acceptance candidate

PR #64 commit `190db4c` extends the existing two-account Chromium room journey with
visitor seating, remote avatar pose synchronization, exclusive seat occupancy,
stand/reseat, owner pickup via Shift-click, and desktop/mobile seated screenshots.
It also updates chair accessibility-name expectations from pickup to sitting.
**These are newly added browser assertions, not passing evidence.** Both required
workflows must execute on the exact updated head; inspect the screenshots and
fix any failures before integrating PR #64. The public Pi has not been tested.

## November 22 — integrated release verification handoff

- PR #64 now targets `main` and includes the room-first scene, multiplayer seating, and the independent avatar-layer test correction. PRs #59 and #63 remain separate drafts; do not merge overlapping branches independently.
- The latest inspected PR #64 head `d552c957d1bd93d729b25dff61cf211c6434a7dc` returned **zero associated pull-request workflow runs**. A mergeable GitHub status is not a test pass. Both `Verify ZeroW` and `ZeroW Player Playtest` must pass on the *same final head* before release.
- This handoff update creates a new PR synchronization event to request CI evaluation. Verify that GitHub actually creates runs; if not, investigate workflow event filters and permissions rather than asserting success.
- Acceptance still requires two simultaneous authenticated browser players, seat exclusivity and cleanup, chair/sofa tap targets at 320px/390px/desktop, avatar depth and speech-bubble visual inspection, room chat, furniture permissions, and account/coin/SQLite regression coverage. Record isolated-run results separately from signed-in production Pi observations.
- Do not merge or claim production deployment until the required workflows and visual review succeed.
