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
# Task: three-step checkout form

Build a single HTML file (all CSS/JS inline, no frameworks, no build tools, no
network calls) implementing a three-step checkout flow.

## Deliverable
- `checkout.html`

## Requirements

R1. Step 1 collects shipping details: full name, address line, city, postal code,
    country (a select with at least 5 countries).
R2. Step 2 collects payment details: cardholder name, card number, expiry (MM/YY),
    CVC.
R3. Step 3 shows a read-only summary of everything entered in steps 1 and 2, with
    the card number masked except the last 4 digits, and a "Place order" button.
R4. Next/Back controls move between steps. Only one step is visible at a time.
R5. A step indicator shows which of the three steps is current.
R6. "Place order" replaces the form with a confirmation message containing an
    order number.

Open `checkout.html` directly in a browser (`file://`) — it must work with no server.

--- END SPEC ---

PAGE UNDER AUDIT: file:///E:/GitHub/superpowers-custom/benchmark2/runs/B_GT/checkout.html

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
