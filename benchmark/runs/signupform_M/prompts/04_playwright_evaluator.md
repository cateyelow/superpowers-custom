Evaluate this running web app.

URL:
file:///home/ubuntu/Github/superpowers-custom/benchmark/runs/signupform_M/src/signup.html

(This is a static single-file deliverable — no dev server exists or is needed. Open the file:// URL directly.)

Scope:
A newly built single-file accessible signup form with client-side validation (email, password + live rule checklist, password-confirm, nickname, terms checkbox, disabled-until-valid submit, success panel with focus move).

Requirements:
- Fields present in visual order: email, password, password-confirm, nickname, terms checkbox, submit button.
- Email: NO error while typing into the pristine field; error appears after first blur with invalid value; after that first blur the error updates/clears live as the value is corrected.
- Password: a live checklist of three rules (10+ chars / at least one letter AND one digit / at least one symbol) that ticks items as they become satisfied, updating on every keystroke.
- Password-confirm: mismatch error appears on blur; clears as soon as values match (typing in either field), without needing another blur.
- Nickname: 2-12 chars, letters/digits/Korean only; validated on blur (e.g., "a" invalid, "ab" valid, "한글닉" valid, "bad name!" invalid).
- Submit is disabled (visually distinct + native disabled or aria-disabled) until ALL fields valid AND checkbox checked; re-disables if a field is made invalid again.
- On submit: no navigation (URL unchanged, no query string), a success panel appears showing the entered email and nickname (password NOT shown anywhere), and keyboard focus moves to that panel (document.activeElement is the panel).
- Accessibility: each input has an associated label (for/id); error messages are wired via aria-describedby + role="alert" or aria-live.
- Keyboard-only: tab order follows visual order; checkbox toggles with Space; submit activatable with Enter; the whole happy path works without a mouse.
- Errors appearing/disappearing cause no layout shift of the controls below them.
- No console errors at load or during the happy path.

Primary Flow (do this with the KEYBOARD wherever possible):
1. Open the file:// URL. Check console for errors. Verify submit is disabled.
2. Focus email, type "not-an-email" — verify NO error is visible while typing. Tab away (blur) — verify the email error appears. Refocus and correct to "user@example.com" — verify the error clears while typing (no blur needed).
3. Focus password, type "abc" — checklist all unticked except none/partial; type up to "abcdefghij" — length item ticks; add "1" — letter+digit item ticks; add "!" — symbol item ticks. Verify each transition.
4. Focus confirm, type "wrong", Tab away — mismatch error appears. Refocus and retype the exact password "abcdefghij1!" — error clears as soon as it matches.
5. Focus nickname, type "a", Tab away — error appears. Fix to "한글닉네임" or "nick123" — error clears.
6. Tab to the terms checkbox, press Space to check it. Verify submit becomes enabled and visually changes.
7. Tab to submit, press Enter. Verify: no navigation/URL change, success panel visible with the entered email and nickname, password NOT displayed anywhere, and document.activeElement is the success panel (use browser_evaluate to check).
8. Console check again: zero errors through the whole flow.

Targeted Checks:
- Layout shift: with the form reset (reload), measure the y-position (getBoundingClientRect().top via browser_evaluate) of the nickname input, then trigger the email error (invalid + blur) and re-measure — position must be identical.
- Regression guard: after the form is fully valid, change the password to something new (breaking confirm match) — submit must re-disable and the confirm mismatch error must appear.
- Checkbox Space toggle and uncheck: after checking, press Space again — submit must re-disable.
- aria wiring: via browser_evaluate, confirm each text input has aria-describedby pointing at existing element ids and that error containers have role="alert" or aria-live.

Recheck:
- none

Responsive Check:
- no

Important:
- Use the browser only.
- Do not read code.
- Do not score the app.
- Fail on any material issue in this scope.
- Before returning: close ONLY the tabs you opened (browser_tabs). NEVER call browser_close — on this host Playwright MCP attaches to the shared logged-in Chrome (CDP 127.0.0.1:9222) that other sessions depend on. Never touch pre-existing tabs. Only if you yourself launched an isolated browser may you close it fully.
