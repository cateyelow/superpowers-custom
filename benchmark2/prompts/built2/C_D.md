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
# Task: filterable data table

Build a single HTML file (all CSS/JS inline, no frameworks, no build tools, no
network calls) implementing a data table over a built-in dataset.

## Deliverable
- `table.html`

## Requirements

R1. Embed a hardcoded dataset of 24 employee records, each with: name,
    department, role, location, and salary (a number).
R2. Render them in a table with a column per field.
R3. A text input filters rows as the user types, matching against name and role.
R4. A department dropdown filters rows to one department, and combines with the
    text filter.
R5. Clicking a column header sorts by that column; clicking again reverses the
    direction. Salary sorts numerically, the rest alphabetically.
R6. Paginate at 10 rows per page, with Previous/Next controls and a "Page X of Y"
    indicator that reflects the current filters.

Open `table.html` directly in a browser (`file://`) — it must work with no server.
--- END SPEC ---

PAGE UNDER REVIEW: file:///E:/GitHub/superpowers-custom/benchmark2/runs2/C_D/table.html

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

States the probe reached: filled, load
Probe log: seeded 2 field(s); searched for a no-match term

### Text contrast below the WCAG 1.4.3 minimum
- `#previous` — 2.34:1, needs 4.5:1 (state: load, 375px) text: 'Previous'  [in a :disabled control — WCAG-exempt]
- `#next` — 2.34:1, needs 4.5:1 (state: filled, 375px) text: 'Next'  [in a :disabled control — WCAG-exempt]

### Control boundaries below the WCAG 1.4.11 3:1 minimum
- `#search` — border 1.53:1 against its backdrop (state: load)
- `#department` — border 1.53:1 against its backdrop (state: load)
- `#previous` — border 1.53:1 against its backdrop (state: load)  [disabled]
- `#next` — border 1.53:1 against its backdrop (state: load)

### Styles that only apply in a state (from the CSSOM — these never show up in getComputedStyle of the resting element)
- `input:focus` { box-shadow: rgba(53, 106, 230, 0.18) 0px 0px 0px 3px } — 1.27:1, needs 3:1 — non-text contrast of the :focus indicator (matches 1 element(s), e.g. `#search`)  composites to rgb(219,228,251)
- `select:focus` { box-shadow: rgba(53, 106, 230, 0.18) 0px 0px 0px 3px } — 1.27:1, needs 3:1 — non-text contrast of the :focus indicator (matches 1 element(s), e.g. `#department`)  composites to rgb(219,228,251)
- `button:focus-visible` { box-shadow: rgba(53, 106, 230, 0.18) 0px 0px 0px 3px } — 1.27:1, needs 3:1 — non-text contrast of the :focus-visible indicator (matches 2 element(s), e.g. `#previous`)  composites to rgb(219,228,251)
- `.pagination button:hover:not(:disabled)` { border-color: rgb(152, 166, 184) } — 2.25:1, needs 3:1 — non-text contrast of the :hover indicator (matches 2 element(s), e.g. `#previous`)  composites to rgb(152,166,184)
- `.pagination button:disabled` { color: rgb(152, 162, 179) } — 2.34:1, needs 4.5:1 — disabled label — WCAG-exempt but often unreadable (matches 2 element(s), e.g. `#previous`)

### Interactive elements under 44x44 CSS px
- `#previous` — 94 x 38 px (under-44-below-touch-guidance, state: load, 375px) 'Previous'
- `#next` — 94 x 38 px (under-44-below-touch-guidance, state: load, 375px) 'Next'
- `#search` — 309 x 42 px (under-44-below-touch-guidance, state: load, 375px) ''
- `#department` — 309 x 42 px (under-44-below-touch-guidance, state: load, 375px) 'All departments\n          DesignEngineeringFinan'
- `#search` — 446.7 x 42 px (under-44-below-touch-guidance, state: load, 768px) ''
- `#department` — 223.3 x 42 px (under-44-below-touch-guidance, state: load, 768px) 'All departments\n          DesignEngineeringFinan'
- `#search` — 708 x 42 px (under-44-below-touch-guidance, state: load, 1280px) ''
- `#department` — 354 x 42 px (under-44-below-touch-guidance, state: load, 1280px) 'All departments\n          DesignEngineeringFinan'

### Accessible name / role exposure
- `th` — operable (tabindex=0 + handlers) but exposes no interactive role 'Name'

### Horizontal clipping / overflow
- `div.table-wrap` scrolls horizontally at 375px (scrollWidth 715 > clientWidth 349) — content is off-screen unless the user scrolls sideways

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
