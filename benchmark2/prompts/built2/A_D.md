# Pre-ship review

You are reviewing a newly implemented single-file web page before it ships. You
did not build it and have no history with it.

Your team's review skill is pasted below — follow it. You are the reviewer
yourself; do not dispatch anyone else.

You also have Playwright browser tools. The project's standing rule is that a
change is not done until the exact user-visible flow has been verified in a real
browser, so open the page and check it rather than reading source alone.

Report every user-visible defect you find.

--- TEAM SKILL: requesting-code-review ---
---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

# Requesting Code Review

Dispatch a code reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch code reviewer subagent:**

Dispatch a `general-purpose` subagent, filling the template at [code-reviewer.md](code-reviewer.md)

**Placeholders:**
- `{DESCRIPTION}` - Brief summary of what you built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch code reviewer subagent]
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types
  PLAN_OR_REQUIREMENTS: Task 2 from docs/superpowers/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll just review the diff myself instead of dispatching a reviewer" | You're the coordinator — reviewing the diff inline burns the context window you need to keep driving the work. Dispatch a reviewer subagent: the diff and the evaluation live in its context, and only the findings come back to you. |
| "The reviewer needs my whole session history to understand the change" | Hand it precisely crafted context, never your session's history. That keeps the reviewer on the work product, not your thought process. |

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: [code-reviewer.md](code-reviewer.md)

--- END SKILL ---

--- SPEC THE PAGE WAS BUILT FROM ---
# Task: drag-and-drop file upload widget

Build a single HTML file (all CSS/JS inline, no frameworks, no build tools, no
network calls) implementing a file upload widget.

## Deliverable
- `upload.html`

## Requirements

R1. A drop zone that accepts files dropped onto it, and also opens a file picker
    when clicked.
R2. Dropped/selected files appear in a list showing each file's name and its size
    in KB.
R3. Each listed file has a Remove control that takes it out of the list.
R4. An "Upload" button starts a simulated upload: each file shows a progress bar
    that animates from 0% to 100% over about 2 seconds, then shows "Done".
R5. While an upload is in progress the Upload button cannot start a second one.
R6. A "Clear all" control empties the list.

Open `upload.html` directly in a browser (`file://`) — it must work with no server.
--- END SPEC ---

PAGE UNDER REVIEW: file:///E:/GitHub/superpowers-custom/benchmark2/runs2/A_D/upload.html

## Machine measurements of this page (run for you before you started)

A deterministic probe opened this exact page in an isolated headless Chromium,
drove it through every state it could reach (load, all fields populated, later
wizard steps, files selected, no-results), and at 375 / 768 / 1280 measured
every element: text and non-text contrast ratios, control boundaries,
focus-indicator and placeholder styles pulled from the CSSOM, touch-target
boxes, accessible names and roles, and clipped scroll containers.

**This is evidence, not a findings list.** The probe measures; it cannot judge.
Known limits, which are your job:

- It over-reports. It flags things no criterion actually forbids — decorative
  hover shadows, controls between 24 and 44 px (which meet WCAG 2.5.8 and miss
  only the softer 44 px touch guidance), and `:disabled` text (WCAG-exempt,
  though a disabled label can still be a real legibility problem when it is the
  page's resting state or carries a status message). **Verify before reporting;
  drop what is not a defect.** A wrong entry in your report costs you.
- It is blind to behaviour. It cannot tell that a button is dead, that a caret
  jumps, that a past date is accepted, that focus is thrown away, that a live
  region floods, or that state gets stuck. **Every defect of that kind is
  yours to find, by driving the page yourself.** Do not let the list below
  narrow where you look — historically that is exactly where reviews go wrong.

Confirm anything you take from this list in your own browser session, and cite
your own measurement in `repro`.

States the probe reached: files-selected, load
Probe log: selected 2 files

### Text contrast below the WCAG 1.4.3 minimum
- `#upload-button` — 1.98:1, needs 4.5:1 (state: load, 375px) text: 'Upload'  [in a :disabled control — WCAG-exempt]
- `#clear-all` — 2.06:1, needs 4.5:1 (state: load, 375px) text: 'Clear all'  [in a :disabled control — WCAG-exempt]
- `small` — 3.6:1, needs 4.5:1 (state: load, 375px) text: 'You can select multiple files'
- `#empty-state` — 3.76:1, needs 4.5:1 (state: load, 375px) text: 'No files selected.'
- `span` — 3.98:1, needs 4.5:1 (state: files-selected, 375px) text: '2.8 KB'
- `span.file-status` — 3.98:1, needs 4.5:1 (state: files-selected, 375px) text: 'Ready'

### Control boundaries below the WCAG 1.4.11 3:1 minimum
- `#drop-zone` — border 2.27:1 against its backdrop (state: load)

### Styles that only apply in a state (from the CSSOM — these never show up in getComputedStyle of the resting element)
- `.remove-button:focus-visible` { outline: rgba(64, 95, 216, 0.28) solid 3px } — 1.49:1, needs 3:1 — non-text contrast of the :focus-visible indicator (matches 2 element(s), e.g. `button.remove-button`)  composites to rgb(199,208,243)
- `.remove-button:focus-visible` { outline-color: rgba(64, 95, 216, 0.28) } — 1.49:1, needs 3:1 — non-text contrast of the :focus-visible indicator (matches 2 element(s), e.g. `button.remove-button`)  composites to rgb(199,208,243)
- `.upload-button:hover:not(:disabled)` { box-shadow: rgba(64, 95, 216, 0.28) 0px 10px 22px } — 1.5:1, needs 3:1 — non-text contrast of the :hover indicator (matches 1 element(s), e.g. `#upload-button`)  composites to rgb(202,210,244)
- `.upload-button:focus-visible` { outline: rgba(64, 95, 216, 0.28) solid 3px } — 1.5:1, needs 3:1 — non-text contrast of the :focus-visible indicator (matches 1 element(s), e.g. `#upload-button`)  composites to rgb(202,210,244)
- `.upload-button:focus-visible` { outline-color: rgba(64, 95, 216, 0.28) } — 1.5:1, needs 3:1 — non-text contrast of the :focus-visible indicator (matches 1 element(s), e.g. `#upload-button`)  composites to rgb(202,210,244)
- `.clear-button:focus-visible` { outline: rgba(64, 95, 216, 0.28) solid 3px } — 1.5:1, needs 3:1 — non-text contrast of the :focus-visible indicator (matches 1 element(s), e.g. `#clear-all`)  composites to rgb(202,210,244)
- `.clear-button:focus-visible` { outline-color: rgba(64, 95, 216, 0.28) } — 1.5:1, needs 3:1 — non-text contrast of the :focus-visible indicator (matches 1 element(s), e.g. `#clear-all`)  composites to rgb(202,210,244)
- `.clear-button:disabled` { color: rgb(174, 181, 194) } — 2.06:1, needs 4.5:1 — disabled label — WCAG-exempt but often unreadable (matches 1 element(s), e.g. `#clear-all`)

### Interactive elements under 44x44 CSS px
- `#file-input` — 1 x 1 px (under-24-FAILS-WCAG-2.5.8, state: load, 375px) ''
- `button.remove-button` — 61.1 x 22 px (under-24-FAILS-WCAG-2.5.8, state: files-selected, 375px) 'Remove'
- `#clear-all` — 61.5 x 33 px (under-44-below-touch-guidance, state: load, 375px) 'Clear all'

### Accessible name / role exposure
- `#file-input` — no accessible name ''
- `#file-input` — focusable control nested inside another control (#drop-zone) ''

## How to open the page (required — identical for everyone)

Do NOT use the Playwright MCP tools. On this machine they block `file:` URLs and
they drive a Chrome shared with other concurrent sessions, so your observations
would be corrupted by other people's clicks.

Drive your own isolated browser from Python instead. This is verified working
here:

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    pg.goto('file:///<PAGE_PATH>')
    # pg.evaluate(...) for computed styles, sizes, contrast
    # pg.set_viewport_size({'width': 375, 'height': 800}) for responsive checks
    # pg.click / pg.fill / pg.keyboard for interaction
    b.close()
```

Use it for everything you claim: computed styles and colours, element boxes and
touch-target sizes, focus order, viewport behaviour at 375 / 768 / 1280, and
actual interaction. Measure rather than infer — a claim you did not verify in
the browser does not belong in your report.

## Output contract (follow exactly)

Write your findings to the report path given above, as a plain-text list. Use
this exact record shape, one blank line between records:

```
DEFECT <n>
what: <one line — the user-visible problem>
where: <file:line, or a CSS selector / element description>
repro: <how you observed it — the steps or the measurement>
severity: blocking | minor
category: a11y | contrast | touch-target | responsive | state | logic | spec
```

Rules:
- Report only defects you actually observed or measured. Do not speculate.
- "blocking" = a user cannot complete the task, loses data, or cannot perceive
  or operate a control. Everything else is "minor".
- One record per distinct defect. Do not merge two problems into one record.
- If you find nothing, write exactly: NO DEFECTS FOUND
- Your final reply to me must be ONLY the number of defects you wrote, e.g. `7`.
  The report file is the deliverable.
