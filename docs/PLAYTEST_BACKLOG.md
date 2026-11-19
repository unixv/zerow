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

## Planned economy milestone — November 18, 2026

- **PR in progress:** player-owned rooms and coin-based furniture shop, developed separately from existing QA PRs.
- **Player scope:** publicly browsable rooms; first room free, up to three total; furniture purchased with game-earned coins and placed onto a persistent 10×7 floor; owner-only edits and item pickup; visitor read-only.
- **Earn/spend model:** one-time 300 starter coins for registered users, 100 claimable once per 24 hours, additional rooms 150 coins; no real-money processor or financial credentials.
- **Safety:** additive SQLite columns/tables; server-side authorized purchase, coin deduction, placement and double-claim protection; no deliberate change to existing accounts, plaza chat, movement, lanterns, or deployment.
- **Isolated verification:** unit tests in `tests/test_rooms.py` and two-browser journey in `tests/rooms_playtest.py` added. Both workflows are **pending** on feature head until CI evidence confirms results.
- **Live coverage:** public Pi room-builder interactions **not tested**. Do not label this feature released or verified on production before merge/deployment and live exercise.
- **Next:** evaluate real-money purchases separately, and add multiplayer occupancy inside rooms after room browsing/editing is proven reliable.
