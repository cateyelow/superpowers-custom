# Pre-ship review

You are reviewing a newly implemented single-file web page before it ships. You
did not build it and have no history with it.

The project's standing rule is that a change is not done until the exact
user-visible flow has been verified in a real browser, so open the page and
check it rather than reading source alone.

Report every user-visible defect you find.

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

PAGE UNDER REVIEW: file:///E:/GitHub/superpowers-custom/benchmark2/runs2/C_N/table.html

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
