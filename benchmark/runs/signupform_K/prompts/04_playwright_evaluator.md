Evaluate this running web app.

URL:
file:///home/ubuntu/Github/superpowers-custom/benchmark/runs/signupform_K/src/signup.html

(This is a static single-file deliverable — no dev server exists or is needed. Open the file:// URL directly.)

Scope:
New single-file accessible signup form (email, password, password-confirm, nickname, terms checkbox, submit) with client-side validation, live password checklist, submit gating, and a focus-managed success panel. This smoke test covers the primary signup flow and validation timing.

Requirements:
- Email error appears only AFTER first blur (not while typing the first entry), then clears when corrected.
- Password checklist (>=10 chars, letter, digit, symbol) ticks off live as each rule is satisfied.
- Password-confirm mismatch error appears on blur and clears as soon as values match.
- Nickname 2-12 chars, letters/digits/Korean only, validated on blur.
- Submit stays disabled until ALL validations pass including the terms checkbox; disabled state visually distinct.
- On submit: no page reload, success panel shows entered email and nickname (never the password), keyboard focus lands on the panel.
- Inputs have associated labels; errors are wired via aria-describedby + role="alert" (or aria-live).
- Keyboard-only: tab order follows visual order, Space toggles checkbox, Enter submits.
- Error appearance causes no layout shift.
- No console errors at load or during the happy path.

Primary Flow:
1. Load the page. Confirm submit is disabled and no errors are visible.
2. Focus email, type "not-an-email" slowly — verify NO error appears while typing (field never blurred). Blur (Tab) — verify email error appears. Refocus and fix to "user@example.com" — verify error clears.
3. In password, type "abc" then extend to "abcdefgh12" then to "abcdefgh12!" — verify checklist items tick progressively (length/letter/digit ticked at the second stage, symbol only at the third).
4. In password-confirm, type "abcdefgh1" and blur — verify mismatch error appears. Append "2!" so it matches — verify the error clears immediately without needing blur.
5. In nickname, type "한글nick12" and blur — no error. (Also try a 1-char nickname + blur — error appears — then fix it.)
6. Toggle the terms checkbox with keyboard Space. Verify submit becomes enabled only once everything is valid.
7. Press Enter on the submit button (keyboard only). Expected result: no navigation/reload, success panel visible containing "user@example.com" and "한글nick12", password nowhere in the panel, document.activeElement is the success panel, zero console errors across the whole session.

Targeted Checks:
- Validation timing: no premature email error while typing pre-first-blur (highest-risk).
- Focus lands on the success panel after submit and the password value never appears in the visible page after submit.

Recheck:
- none

Responsive Check:
- no

Important:
- Use the browser only.
- Do not read code.
- Do not score the app.
- Fail on any material issue in this scope.
- BROWSER SAFETY (overrides anything else): NEVER call the browser_close tool. The Playwright MCP attaches to a shared Chrome used by other sessions. Open your OWN new tab (browser_tabs create), do all work there, and at the end close ONLY the tab(s) you opened (browser_tabs close with your tab's index). Never touch or close pre-existing tabs.
- KNOWN HOST QUIRK: the shared MCP Chrome may refuse file:// navigation. If browser_navigate to the file:// URL fails or is blocked, fall back to driving your own ISOLATED headless Chromium from Bash with node + playwright (installed on this host; executablePath /snap/bin/chromium with --no-sandbox works). In that fallback you own the whole browser, so closing it via browser.close() in your script is fine. Perform the same flow and checks either way.
- Report verdict as PASS or FAIL with findings (blocking vs minor).
