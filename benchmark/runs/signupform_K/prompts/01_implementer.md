You are implementing Task 1: Accessible signup form page (single-file HTML)

## Task Description

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

## Context

This is the only task in the plan — a standalone deliverable, no existing codebase, no dependencies. The entire deliverable is ONE static HTML file at:

    /home/ubuntu/Github/superpowers-custom/benchmark/runs/signupform_K/src/signup.html

It will be evaluated by opening it via a `file://` URL in a browser (no dev server), then reviewed against the requirements above by an independent reviewer, and finally exercised with keyboard-only interaction at 375px/768px/1280px viewports. Accessibility semantics (labels, aria-describedby, live regions, focus management) will be checked programmatically, so implement them exactly as specified, not approximately.

Environment adaptations (these OVERRIDE any generic instruction below):
- Work in place. Do NOT create git worktrees or branches, and do NOT commit — this directory is not a git repo for your purposes. "Commit your work" in the generic instructions is replaced by "save the file".
- There is no test framework and no package manager here. "Write tests" means: verify your own logic carefully (you may open the file with a quick `node`-free check such as reading it back, or reason through each requirement). A separate browser evaluator will run the real interaction tests afterward.
- Do not touch anything outside /home/ubuntu/Github/superpowers-custom/benchmark/runs/signupform_K/ (except /tmp scratch).

## Before You Begin

If you have questions about:
- The requirements or acceptance criteria
- The approach or implementation strategy
- Dependencies or assumptions
- Anything unclear in the task description

**Ask them now.** Raise any concerns before starting work.

## Your Job

Once you're clear on requirements:
1. Implement exactly what the task specifies
2. Verify implementation works (self-check every requirement R1–R12 against your code)
3. Save the file at the exact path above
4. Self-review (see below)
5. Report back

Work from: /home/ubuntu/Github/superpowers-custom/benchmark/runs/signupform_K

**While you work:** If you encounter something unexpected or unclear, **ask questions**.
It's always OK to pause and clarify. Don't guess or make assumptions.

## Code Organization

You reason best about code you can hold in context at once, and your edits are more
reliable when files are focused. Keep this in mind:
- Follow the file structure defined in the plan (exactly one file: src/signup.html)
- Each file should have one clear responsibility with a well-defined interface
- If a file you're creating is growing beyond the plan's intent, stop and report
  it as DONE_WITH_CONCERNS — don't split files on your own without plan guidance

## When You're in Over Your Head

It is always OK to stop and say "this is too hard for me." Bad work is worse than
no work. You will not be penalized for escalating.

**STOP and escalate when:**
- The task requires architectural decisions with multiple valid approaches
- You need to understand code beyond what was provided and can't find clarity
- You feel uncertain about whether your approach is correct
- You've been reading file after file trying to understand the system without progress

**How to escalate:** Report back with status BLOCKED or NEEDS_CONTEXT. Describe
specifically what you're stuck on, what you've tried, and what kind of help you need.

## Before Reporting Back: Self-Review

Review your work with fresh eyes. Ask yourself:

**Completeness:**
- Did I fully implement everything in the spec (all of R1–R12)?
- Did I miss any requirements?
- Are there edge cases I didn't handle? (e.g., password checklist while confirm is filled; error state after success panel; email with spaces; nickname with mixed Korean/Latin)

**Quality:**
- Is this my best work?
- Are names clear and accurate (match what things do, not how they work)?
- Is the code clean and maintainable?

**Discipline:**
- Did I avoid overbuilding (YAGNI)?
- Did I only build what was requested?

**Testing:**
- Did I mentally walk the full happy path AND each error path?
- Does the page work from file:// with zero console errors?

If you find issues during self-review, fix them now before reporting.

## Report Format

When done, report:
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What you implemented (or what you attempted, if blocked)
- What you verified and how
- Files changed
- Self-review findings (if any)
- Any issues or concerns

Use DONE_WITH_CONCERNS if you completed the work but have doubts about correctness.
Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need
information that wasn't provided. Never silently produce work you're unsure about.
