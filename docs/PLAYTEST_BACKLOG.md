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


## November 20, 2026 — Plaza chat and toolbar candidate (PR #55)

- Screenshot-reported usability: plaza chat was only 148px tall on desktop, and multiple redundant shortcuts cluttered the world toolbar. These are owner-observed production UI concerns, not isolated test results.
- Candidate uses a larger floating chat panel without reducing canvas height, enlarges message/composer typography, and hides redundant Lantern Circle, evening and Chat shortcuts while keeping the Explore plaza guide reachable.
- Initial Chromium playtest failed when its Explore plaza control was hidden; restored that control and corrected a literal newline escape in the floating-panel CSS. Both required workflows and screenshot review must be repeated on the corrected head before merge.
- Rooms still require a genuinely walkable shared world with visible visitors and direct furniture interaction. PR #54 adds room presence/chat but does not satisfy this acceptance criterion.
- Production deployment and live Pi gameplay remain unverified for this candidate.


### November 20 — PR #55 browser regression triage

- Player Playtest run 44688136179 failed because the previous simplified toolbar hid `#sceneToggle`, while the browser script still clicked it. This is an isolated Chromium failure, not a production Pi observation.
- The visible Sky Studio now supplies the atmosphere control tested in `tests/playtest.py`; the chat input replaces the redundant chat-focus shortcut. The Lantern Circle button remains available for the mobile lantern journey. The exploration guide shortcut stays hidden to reduce toolbar clutter; existing landmark canvas tests still exercise discovery.
- Fresh Verify ZeroW and ZeroW Player Playtest results on commit 5012be6 are required before merge. Screenshots and production Pi remain unverified.
- Separate unresolved design milestone: Homes must become genuinely walkable shared rooms with avatars, interactive furniture and room-local social activity. Room gatherings alone are not a playable room.


### November 20 — PR #55 latest playtest triage

- Player Playtest [44695747838](https://github.com/unixv/zerow/actions/runs/44695747838) failed because the browser script expected `#exploreGuide` to be hidden, although the product intentionally retained the visible Explore plaza control. Corrected the assertion to verify the actual visible shortcut. This is isolated runner evidence, not live Pi evidence.
- Verify ZeroW [44695747851](https://github.com/unixv/zerow/actions/runs/44695747851) passed on the prior head. Both checks must pass on the corrected head before merge; inspect desktop/mobile screenshots.
- PR #54 checks passed on head 88b8a62, but screenshot review and release remain pending. Walkable rooms, avatars and direct furniture placement are still unimplemented.


## November 20, 2026 — PR #55 floating chat overlap triage

- Isolated Chromium Player Playtest run [44702149101](https://github.com/unixv/zerow/actions/runs/44702149101) failed while clicking the visible Starlight Sky Studio button: the enlarged floating chat's message list intercepted pointer events. This is a real layout interaction regression, not a stale test expectation.
- Repositioned the desktop floating chat to the lower-left, away from the lower-right Sky Studio dock, preserving the expanded conversation area and the world canvas. Mobile flow is unchanged.
- **Pending:** Both workflows on corrected head, screenshot inspection at desktop/mobile widths, and production Pi verification. Do not merge until verified.
