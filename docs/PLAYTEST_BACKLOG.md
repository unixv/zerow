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
