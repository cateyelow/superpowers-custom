# Adjudication task

You are auditing a single-file web page against the spec it was built from.
Enumerate every **user-visible defect** the page has.

You have Playwright browser tools. Open the page with `file:///<ARTIFACT_PATH>`
and examine it directly — do not rely on reading the source alone. Exercise the
page: interact with every control, try the empty and error paths, resize the
viewport (test at 375px, 768px, and 1280px widths), and measure anything you
suspect (computed sizes, contrast ratios, focus order).

Audit for at least:
- spec violations (requirements in the spec that are not met as written)
- broken or dead controls, wrong results, state that desyncs
- keyboard operability and focus management
- screen-reader-relevant semantics (labels, roles, names, live regions)
- colour contrast of text and of interactive controls
- touch-target sizes
- layout breakage at the three viewport widths
- missing empty / error / in-progress states a user will actually hit

Be exhaustive and be honest: this list is the reference standard others are
scored against. Do NOT pad it with speculative or stylistic preferences — every
entry must be something you observed or measured, and that a competent reviewer
would agree is a defect.

The spec is below. The page is at the artifact path given above.

---
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

PAGE UNDER AUDIT: file:///E:/GitHub/superpowers-custom/benchmark2/runs2/A_GT/upload.html

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
