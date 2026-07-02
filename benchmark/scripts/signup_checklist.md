# Signup form deterministic checklist (run identically on every candidate page)

Open the given file:// URL in a NEW tab (never touch existing tabs, never call browser_close; close your tab when done). Execute every check below in order. For each, print exactly `CHECK <id> PASS|FAIL <one-line evidence>`.

1. `fields_present` — email, password, password-confirm, nickname inputs, a terms checkbox, and a submit button all exist.
2. `email_no_premature_error` — focus email, type `abc` (do NOT blur): no email error visible yet.
3. `email_error_after_blur` — blur the email field (still `abc`): an email error is now visible.
4. `pw_checklist_live` — focus password, type `abcdef`: letter rule ticked, digit and symbol not. Append `123` (→`abcdef123`): digit ticked. Append `!@` (→`abcdef123!@`, 11 chars): all three rules ticked.
5. `confirm_mismatch_blur` — type `abcdef123!@` in password, `abcdef123!` in confirm, blur confirm: mismatch error visible. Then append `@` so they match: error clears without needing another blur.
6. `nickname_rules` — enter `김` (1 char), blur: error. Replace with `김철수`, blur: no error.
7. `submit_gating` — with all fields valid but checkbox UNchecked: submit is disabled (native disabled or aria-disabled="true"). Check the checkbox: submit becomes enabled.
8. `submit_success_focus` — activate submit: page does not navigate; a success panel appears containing the entered email AND nickname and NOT the password; document.activeElement is inside that panel.
9. `labels_associated` — every input has a `<label for>` matching its id (evaluate in JS; report any input missing one).
10. `aria_errors` — error messages are wired via aria-describedby on the input AND the error container has role="alert" or aria-live (check at least the email error).
11. `keyboard_flow` — reload; using ONLY keyboard (tab/space/enter via browser_press_key), reach every field in visual order, toggle the checkbox with Space, and reach the submit button.
12. `mobile_375` — resize to 375×700: `document.documentElement.scrollWidth <= 375` (no horizontal scroll) AND each input/checkbox/button has rendered height ≥ 44px (report the smallest).
13. `console_clean` — after a full happy-path run, browser_console_messages shows no errors.

End with a line: `TOTAL <n_pass>/13`.
