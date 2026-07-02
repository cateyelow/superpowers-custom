You are implementing Task 1: Accessible signup form page (single-file HTML)

## Task Description

Build a single-file HTML page (all CSS/JS inline, no frameworks, no build tools) implementing a signup form with client-side validation.

### Deliverables
- `/home/ubuntu/Github/superpowers-custom/benchmark/runs/signupform_M/src/signup.html`

### Requirements

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

### Constraints
- Single file, vanilla JS, works from `file://` (no server required).

## Context

This is the only task of this plan — a standalone static deliverable, no existing codebase, no dependencies. The file will be opened directly via a `file://` URL in Chrome and evaluated by a Playwright browser evaluator (functional + accessibility + responsive at 375px/768px/1280px) and reviewed by a separate code reviewer. There is NO git repo here: do NOT run git init / commit — "commit your work" for this task means "the final file is saved at the deliverable path".

## Acceptance Criteria (Definition of Done)

Each of these must be verifiably true in a real browser loaded via file://:

1. The page contains exactly the form fields of R1, in visual order: email, password, password-confirm, nickname, terms checkbox, submit button.
2. Email (R2): typing an invalid email into a *pristine* email field shows NO error while typing; after the field loses focus once with an invalid value, the error appears; after that first blur, correcting the value updates/clears the error (live re-validation after first blur is the expected UX).
3. Password (R3): a live checklist that updates on every input event. The spec says "a live checklist of the three rules" — controller's ambiguity resolution (do not re-ask): use exactly THREE checklist items: (1) at least 10 characters, (2) contains at least one letter AND at least one digit, (3) contains at least one symbol. Each item visually ticks when satisfied (e.g., ✓ mark + color change — must include a non-color indicator, not color alone). The underlying validation must enforce all four atomic conditions (length ≥10, ≥1 letter, ≥1 digit, ≥1 symbol) — item (2) is only satisfied when BOTH a letter and a digit are present.
4. Confirm (R4): mismatch error appears on blur of the confirm field; once values match (checked on every input in EITHER password or confirm field), the error clears immediately without needing another blur. Also: if password changes after confirm was valid, submit-enabled state updates correctly.
5. Nickname (R5): validated on blur; valid = 2–12 chars, each char a Latin letter (a-z, A-Z), digit (0-9), or Korean (가-힣, allow ㄱ-ㅎ/ㅏ-ㅣ jamo optionally — at minimum 가-힣ㄱ-ㅎㅏ-ㅣ or just 가-힣; document your choice in a code comment). Spaces/symbols invalid. Error announced like other errors.
6. Submit (R6): disabled (native `disabled` attribute is fine, or `aria-disabled="true"` + click/Enter guard) until email valid AND password satisfies all conditions AND confirm matches AND nickname valid AND checkbox checked. Visually distinct disabled style (e.g., muted color + not-allowed cursor). Re-disables if any field becomes invalid again.
7. Submit flow (R7): submitting (Enter in a field or activating the button) prevents default (no navigation, file:// URL unchanged, no query string appended), hides or visually de-emphasizes the form, shows a success panel that displays the entered email and nickname (NEVER the password), and moves keyboard focus to the panel (panel has `tabindex="-1"` and receives `.focus()`; verify `document.activeElement` is the panel).
8. Accessibility (R8): every input (including the checkbox) has a `<label for>` matching input `id`; every error container has a stable `id` referenced by the input's `aria-describedby`; error containers carry `role="alert"` or `aria-live="polite"`; inputs get `aria-invalid="true"` when in error. The password checklist should also be referenced via `aria-describedby` on the password input.
9. Keyboard (R9): natural DOM order = visual order (no positive tabindex, no CSS order tricks); checkbox toggles with Space; Enter submits from the button and from text fields (when form valid); the whole happy path is possible with keyboard only.
10. Layout stability (R10): error message areas have reserved space (e.g., fixed min-height on the error slot) so appearing/disappearing errors cause zero layout shift of subsequent controls. The password checklist is always visible (does not pop in) or otherwise reserves its space.
11. Responsive (R11): at 375px viewport width there is no horizontal scrollbar (html/body and the form container fit); every input, the checkbox's clickable target (checkbox + label hit area), and the button are ≥44px tall. Include `<meta name="viewport" content="width=device-width, initial-scale=1">`.
12. Console (R12): zero console errors/warnings-as-errors at load and through the whole happy path.
13. File constraints: exactly ONE file, `src/signup.html`; all CSS in a `<style>` tag, all JS in a `<script>` tag; no external requests of any kind (no fonts, no CDNs, no images); works when opened via file:// (no module imports, no fetch).
14. Code quality: clear structure, one source of truth for validation state, named validator functions per field, no duplicated validation logic between blur/input/submit paths, comments where behavior is subtle (first-blur gating, focus move). Semantic HTML (form, fieldset where sensible, button type="submit").

## Before You Begin

If you have questions about the requirements, acceptance criteria, approach, dependencies, or anything unclear in the task description — **ask them now** (report NEEDS_CONTEXT). Raise any concerns before starting work. Note: the checklist-decomposition ambiguity in criterion 3 is already resolved for you (use the three items stated there); do not re-ask about it.

## Your Job

Once you're clear on requirements:
1. Implement exactly what the task specifies
2. Verify implementation works — since this is a static page with no test framework, verification = load the file in a real browser is the evaluator's job; YOUR verification = re-read your code against every acceptance criterion, and run `node -e` snippets to sanity-check your regexes (email, nickname, password classes) if node is available.
3. Save the file at the deliverable path (no git commit — no repo here)
4. Self-review (see below)
5. Report back

Work from: /home/ubuntu/Github/superpowers-custom/benchmark/runs/signupform_M

**While you work:** If you encounter something unexpected or unclear, **ask questions**. It's always OK to pause and clarify. Don't guess or make assumptions.

**Do NOT open a browser or use Playwright MCP tools yourself** — browser evaluation is a separate downstream stage. Do not touch anything outside your working directory (except /tmp scratch).

## Code Organization

You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Keep this in mind:
- Follow the file structure defined in the plan (a single HTML file)
- Each section (style / markup / script) should be cleanly organized within the file
- If the file is growing beyond reason, stop and report it as DONE_WITH_CONCERNS — don't split into multiple files (single-file is a hard constraint)

## When You're in Over Your Head

It is always OK to stop and say "this is too hard for me." Bad work is worse than no work. You will not be penalized for escalating.

**STOP and escalate when:**
- The task requires architectural decisions with multiple valid approaches beyond what's resolved above
- You feel uncertain about whether your approach is correct
- You've been going in circles without progress

**How to escalate:** Report back with status BLOCKED or NEEDS_CONTEXT. Describe specifically what you're stuck on, what you've tried, and what kind of help you need.

## Before Reporting Back: Self-Review

Review your work with fresh eyes. Ask yourself:

**Completeness:**
- Did I fully implement everything in the spec (all R1–R12 + all 14 acceptance criteria)?
- Did I miss any requirements?
- Are there edge cases I didn't handle (paste into fields, IME composition for Korean, checkbox via keyboard, Enter in each field, resubmit after success)?

**Quality:**
- Is this my best work?
- Are names clear and accurate (match what things do, not how they work)?
- Is the code clean and maintainable?

**Discipline:**
- Did I avoid overbuilding (YAGNI)? No localStorage, no fake API, no extra fields, no framework-like abstraction.
- Did I only build what was requested?

**Testing:**
- Did I sanity-check the regexes?
- Did I trace the happy path and each error path by hand through my code?

If you find issues during self-review, fix them now before reporting.

## Report Format

When done, report:
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What you implemented (or what you attempted, if blocked)
- What you tested/verified and how
- Files changed
- Self-review findings (if any)
- Any issues or concerns

Use DONE_WITH_CONCERNS if you completed the work but have doubts about correctness. Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need information that wasn't provided. Never silently produce work you're unsure about.
