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
