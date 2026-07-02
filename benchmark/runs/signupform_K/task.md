# Task: accessible signup form page

Build a single-file HTML page (all CSS/JS inline, no frameworks, no build tools) implementing a signup form with client-side validation.

## Deliverables
- `src/signup.html`

## Requirements

R1. Fields: email, password, password-confirm, nickname, a required terms checkbox, and a submit button.
R2. Email validation: syntactically valid email required; error shows AFTER first blur of the field, not while the user is still typing their first entry.
R3. Password rules: ≥10 chars AND at least one letter, one digit, one symbol. Show a live checklist of the three rules that ticks off as each is satisfied.
R4. Password-confirm must match; mismatch error appears on blur and clears as soon as the values match.
R5. Nickname: 2-12 chars, letters/digits/Korean only; validated on blur.
R6. Submit is disabled until ALL validations pass (including the checkbox); disabled state must be visually distinct AND carry `aria-disabled` semantics or native disabled.
R7. On submit: prevent default, show a success panel containing the entered email and nickname (password never displayed), and move keyboard focus to that panel.
R8. Every input has a programmatically associated `<label>` (for/id), and every error message is announced to screen readers via `aria-describedby` on the input plus `role="alert"` or `aria-live="polite"` on the error container.
R9. Keyboard-only flow works end-to-end: tab order follows visual order, checkbox toggles with Space, submit reachable and activatable with Enter — nothing requires a mouse.
R10. Errors must not shift layout when appearing (reserve space or use a technique that avoids cumulative layout shift).
R11. The page is usable at 375px wide with no horizontal scroll; touch targets (inputs, checkbox, button) are at least 44px tall.
R12. No console errors at load or during the full happy-path flow.

## Constraints
- Single file, vanilla JS, works from `file://` (no server required).
