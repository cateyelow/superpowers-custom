Fix round 1 — final code review found one blocking issue in your signup form implementation at
/home/ubuntu/Github/superpowers-custom/benchmark/runs/signupform_K/src/signup.html

## Blocking issue (important, must fix)

R2 email syntax is under-enforced. The current pattern `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` accepts syntactically invalid addresses such as `a@b..com` (consecutive dots in the domain), which enables the submit button. Verified in a real browser: with email `a@b..com` and all other fields valid, submit becomes enabled.

Fix: tighten the email validation so that structurally invalid domains are rejected — at minimum: no consecutive dots, no leading/trailing dot or hyphen in domain labels, and a dot-separated domain with at least two labels. A solid vanilla-JS approach is a label-based regex such as:

  /^[A-Za-z0-9._%+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$/

(You may choose an equivalent or better formulation; keep it readable and keep the existing blur/typing timing semantics EXACTLY as they are — only the syntax acceptance changes.)

## Minor issue (fix while you're in there — small and safe)

Required fields are not programmatically marked. Add `aria-required="true"` to the email, password, password-confirm, nickname inputs and the terms checkbox. Do NOT add native `required` (it could interfere with the custom validation UX); aria-required is purely declarative and safe.

## Constraints for this fix
- Touch ONLY what these two items need. No refactoring, no other behavior changes.
- The file must remain a single self-contained HTML file working from file://.
- After editing, re-verify in your headless-Chrome harness at minimum: (a) `a@b..com` now shows an email error after blur and keeps submit disabled; (b) `user@example.com`, `a.b@sub.example.co` still pass; (c) the full happy path still works end-to-end with zero console errors; (d) blur-then-live timing for the email field is unchanged.
- Report back with Status (DONE / DONE_WITH_CONCERNS / BLOCKED), what you changed (file:line), and your verification results.
