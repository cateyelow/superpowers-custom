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
