# Scoring task

You are scoring two independent defect reports about the SAME web page against a
reference list of defects that page actually has.

You will be given three files:
- `REFERENCE` — the adjudicated list of real defects in the page
- `CAND_1` — one reviewer's report
- `CAND_2` — another reviewer's report

You do not know who wrote either report or how they were produced. Do not
speculate about it. Score them purely on content.

## What to do

**Step 1 — recall.** For EACH numbered defect in REFERENCE, decide whether
CAND_1 reported it, and whether CAND_2 reported it. Match on substance, not
wording: the same underlying problem described differently is a MATCH. A vaguer
statement that would not lead a developer to the same fix is NOT a match. A
report that names the wrong element or wrong cause is NOT a match.

**Step 2 — extra findings.** For each item a candidate reported that has no
counterpart in REFERENCE, judge it on its own merits by opening the page
yourself (you have Playwright browser tools; the page path is given below) and
verifying the claim. Classify each as:
- `CONFIRMED_REAL` — you verified it, it is a genuine user-visible defect that
  REFERENCE simply missed
- `FALSE_ALARM` — not reproducible, not a defect, or purely stylistic preference

Judge extras strictly and identically for both candidates. Verify before you
confirm.

## Output contract

Write your scoring to the output path given below, in exactly this format:

```
REFERENCE_TOTAL: <n>

R1 | cand_1: HIT|MISS | cand_2: HIT|MISS | <ref defect one-liner>
R2 | cand_1: HIT|MISS | cand_2: HIT|MISS | <ref defect one-liner>
...

CAND_1_EXTRAS
- CONFIRMED_REAL | <one line> | <how you verified>
- FALSE_ALARM | <one line> | <why not a defect>

CAND_2_EXTRAS
- CONFIRMED_REAL | <one line> | <how you verified>
- FALSE_ALARM | <one line> | <why not a defect>

TOTALS
cand_1: hits=<n>/<REFERENCE_TOTAL>  confirmed_extras=<n>  false_alarms=<n>
cand_2: hits=<n>/<REFERENCE_TOTAL>  confirmed_extras=<n>  false_alarms=<n>
```

Your final reply to me must be ONLY the two TOTALS lines. The output file is the
deliverable.
