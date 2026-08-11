# Second pass — machine-measurement sweep over a finished review

A reviewer has already reviewed this page and written the report below. Their
pass is done and it stands. Your job is the second half of the process: a
deterministic probe measured the page, and you decide what the measurements
mean.

**You are ADDING to the report, not rewriting it.** Every record already in it
stays exactly as written, with its numbering. You append new records, numbered
onward from the last one.

## What to do

1. Read the existing report and the probe output below.
2. For each probe measurement, decide whether it is a defect the existing
   report does NOT already cover. Skip anything already reported, even if the
   existing record words it differently.
3. **Verify every candidate in the browser yourself before you add it.** Cite
   your own measurement in `repro`, not the probe's.
4. Append only what survives. If the probe found nothing the report missed,
   append nothing — that is a valid outcome and better than padding.

## The probe over-reports — you are the filter

It measures; it cannot judge. It emits things no criterion forbids:

- **Decorative hover shadows.** A `:hover` box-shadow is not a focus indicator
  and has no contrast minimum. Not a defect.
- **Controls between 24 and 44 px.** These MEET WCAG 2.5.8 (24x24) and miss
  only the softer 44x44 touch guidance. Report one only if it is genuinely
  hard to hit — a primary action at mobile width, not a secondary text input
  that happens to be 42 px tall.
- **`:disabled` text contrast.** WCAG explicitly exempts inactive controls. It
  is a real defect only when that disabled state is the page's resting state or
  carries a status message the user must read.
- **Elements measured in a state the user cannot actually reach.**

A false entry costs you more than a missed one. When you cannot verify it in
the browser, drop it.


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

PAGE UNDER REVIEW: file:///E:/GitHub/superpowers-custom/benchmark2/runs2/C_D2/table.html

--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---
DEFECT 1
what: The "No employees match the current filters." empty-state message is jammed against the right edge of the table instead of centred in the empty area, so it reads as stray misplaced text.
where: table.html:140-144 (.empty { text-align: center }) is overridden by table.html:135-138 (td:last-child, th:last-child { text-align: right }); element #employee-rows td.empty
repro: Chromium 138 headless at 1280x800, typed "zzzz" into #search. getComputedStyle(td.empty).textAlign === "right" (the .empty rule loses on specificity: 0,1,1 vs 0,1,0). Measured the text's own Range rect vs the cell rect: text left 891.3 / right 1181.0 inside a cell spanning 81.0-1199.0, i.e. 810.3px of empty space on the left and 18.0px on the right. Screenshot confirms the sentence sitting in the far-right corner.
severity: minor
category: state

DEFECT 2
what: At mobile width the empty-state message is cut off — the user sees only "No employees " and must scroll the table sideways to find out that nothing matched.
where: #employee-rows td.empty inside .table-wrap (table.html:85-87, .table-wrap { overflow-x: auto }); caused by the right alignment at table.html:135-138
repro: Chromium 138 headless at 375x800, typed "zzzz" into #search. .table-wrap clientWidth 349 / scrollWidth 544; the message rect is left 249.0 -> right 538.7 while the wrapper's visible right edge is 362.0, so 176.7px of the 289.7px message is clipped (only ~39% readable). Scrolling .table-wrap fully right makes it visible again. Screenshot at 375px shows the truncated "No employees ".
severity: minor
category: responsive

DEFECT 3
what: When no rows match, the pagination indicator reads "Page 0 of 0" — a page number that does not exist.
where: table.html:370-371 (displayedPage = pageCount === 0 ? 0 : state.page; pageStatus.textContent = `Page ${displayedPage} of ${pageCount}`); element #page-status
repro: Chromium 138 headless at 1280x800. Typed "zzzz" into #search -> #page-status innerText "Page 0 of 0". Also reproduced by combining filters that cannot both match: #department = "Design" + #search = "maya" -> "Page 0 of 0". Same string visible in the 375px screenshot.
severity: minor
category: state

DEFECT 4
what: Paging with the keyboard throws focus away — activating Next on the second-to-last page (or Previous on page 2) disables that button, focus drops to <body>, and the next Tab restarts at the search box at the top of the page.
where: table.html:372-373 (previousButton.disabled / nextButton.disabled set inside render() while that button holds focus); #next and #previous
repro: Chromium 138 headless at 375x800. Focused #next and pressed Enter: page 2, document.activeElement still BUTTON:next. Pressed Enter again: "Page 3 of 3", #next becomes disabled and document.activeElement === document.body. One Tab then landed on INPUT:search, not on the pagination controls. Mirror case: on page 2, focused #previous and pressed Enter -> "Page 1 of 3", #previous disabled, activeElement === document.body.
severity: minor
category: a11y

DEFECT 5
what: The outlines of the search box, the department dropdown and both pagination buttons are too faint to reliably identify the controls — the border is the only thing separating these white controls from the white panel.
where: table.html:66-76 (input, select { border: 1px solid #c9d2df }) and table.html:155-164 (.pagination button { border: 1px solid #c9d2df }); #search, #department, #previous, #next
repro: Chromium 138 headless at 1280x800, computed styles read from the live page. borderTopColor rgb(201,210,223) against the effective background rgb(255,255,255) = 1.53:1 contrast for all four controls (WCAG 1.4.11 non-text contrast requires 3:1); border width 1px.
severity: minor
category: contrast

DEFECT 6
what: The Previous/Next pagination buttons are only 38px tall, below the 44px minimum touch target, making them fiddly to tap on a phone.
where: table.html:155-164 (.pagination button { min-width: 94px; min-height: 38px; padding: 7px 14px }); #previous, #next
repro: Chromium 138 headless, getBoundingClientRect() on both buttons = 94.0 x 38.0 CSS px at 1280x900, 768x800 and 375x800 (identical at every viewport — no mobile size-up). 38px < the 44x44 target of WCAG 2.5.5 and the Apple HIG 44pt guideline; they do clear the 24x24 WCAG 2.2 AA floor.
severity: minor
category: touch-target

DEFECT 7
what: The sortable column headers are announced to assistive tech as ordinary column headers with no indication that they can be activated, so a screen-reader user tabbing onto "Name" is not told it is a control.
where: table.html:221-225 (th[scope="col"][data-column] tabindex="0" with no role and no accessible hint); th[data-column]
repro: Chromium 138 headless at 1280x900. page.accessibility.snapshot() renders these nodes as `columnheader "NAME"`, `columnheader "DEPARTMENT"` etc. — no button/interactive role. Read from the DOM: getAttribute("role") === null on all five headers while tabIndex === 0 and Enter/Space do sort (verified: focused th[data-column="name"], pressed Enter -> rows re-ordered to Alexander Hall/Amelia Davis/Ava Martinez, indicator "▲"; pressed Space -> reversed). Sort *state* is conveyed correctly (aria-sort flips none -> ascending -> descending on the active column only), so only the interactivity is unannounced.
severity: minor
category: a11y

--- END EXISTING REPORT ---

## Probe output

States the probe reached: filled, load
Probe log: seeded 2 field(s); searched for a no-match term

### Control boundaries below the WCAG 1.4.11 3:1 minimum
- `#search` — border 1.53:1 against its backdrop (state: load)
- `#department` — border 1.53:1 against its backdrop (state: load)
- `#next` — border 1.53:1 against its backdrop (state: load)

### Focus indicators and placeholder text (pulled from the CSSOM — these never appear in getComputedStyle of the resting element)
- `input:focus` { box-shadow: rgba(53, 106, 230, 0.18) 0px 0px 0px 3px } — 1.27:1, needs 3:1, composites to rgb(219,228,251) (matches 1, e.g. `#search`)
- `select:focus` { box-shadow: rgba(53, 106, 230, 0.18) 0px 0px 0px 3px } — 1.27:1, needs 3:1, composites to rgb(219,228,251) (matches 1, e.g. `#department`)
- `button:focus-visible` { box-shadow: rgba(53, 106, 230, 0.18) 0px 0px 0px 3px } — 1.27:1, needs 3:1, composites to rgb(219,228,251) (matches 2, e.g. `#previous`)

### Tap targets below the size minimum (buttons/links judged at 44px, text fields at 24px)
- `#previous` — 94 x 38 px (under-44 — a tap target this size is hard to hit, state: load, 375px) 'Previous'
- `#next` — 94 x 38 px (under-44 — a tap target this size is hard to hit, state: load, 375px) 'Next'

### Accessible name / role exposure
- `th` — operable (tabindex=0 + handlers) but exposes no interactive role 'Name'

### Declarations the author wrote that never take effect (CSS specificity conflicts)
- `td.empty` [no-results] — author wrote `.empty { text-align: center }` (specificity 0-1-0) but `td:last-child { text-align: right }` (specificity 0-1-1) wins; computed value is `right`. Element text: 'No employees match the current filters.'

### Informational only — contrast inside disabled controls
WCAG exempts inactive controls, so these are NOT defects by default. One is worth reporting only if that disabled state is the page's resting state AND its text carries something the user needs to read (a status or progress message).
- `#previous` — 2.34:1 'Previous'
- `#previous` — 1.53:1 'Previous'
- `#next` — 2.34:1 'Next'
- `.pagination button:disabled` — 2.34:1 ''

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

Write the COMPLETE report to the path given to you: every record from the existing report above, unchanged and in its original order, followed by any records you are adding. Use the same record shape:

```
DEFECT <n>
what: <one line — the user-visible problem>
where: <file:line, or a CSS selector / element description>
repro: <how YOU observed it — the steps or the measurement>
severity: blocking | minor
category: a11y | contrast | touch-target | responsive | state | logic | spec
```

Rules:
- Do not edit, merge, renumber or delete an existing record.
- Add only defects you verified yourself in the browser.
- One record per distinct defect.
- If you are adding nothing, write the existing report out unchanged.
- Your final reply to me must be ONLY the total number of records in the file you wrote.
