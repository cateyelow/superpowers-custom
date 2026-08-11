# Scoring task

You are scoring two independent defect reports about the SAME HTTP service
against a reference list of defects that service actually has.

You will be given three files:
- `REFERENCE` — the adjudicated list of real defects
- `CAND_1` — one reviewer's report
- `CAND_2` — another reviewer's report

You do not know who wrote either report or how they were produced. Do not
speculate. Score them purely on content.

## What to do

**Step 1 — recall.** For EACH numbered defect in REFERENCE, decide whether
CAND_1 reported it, and whether CAND_2 reported it. Match on substance, not
wording: the same underlying problem described differently is a MATCH. A vaguer
statement that would not lead a developer to the same fix is NOT a match. A
report naming the wrong endpoint or the wrong cause is NOT a match.

**Step 2 — extra findings.** For each item a candidate reported that has no
counterpart in REFERENCE, judge it on its own merits by RUNNING the service and
reproducing the claim yourself. Classify each as:
- `CONFIRMED_REAL` — you reproduced it; a genuine defect REFERENCE missed
- `FALSE_ALARM` — not reproducible, not a defect, or a preference

Judge extras strictly and identically for both candidates. Reproduce before you
confirm. Start the service on the port you are given, with a fresh database:

```bash
cd <artifact directory>
rm -f /tmp/judge_<port>.db
PORT=<port> DB=/tmp/judge_<port>.db python app.py > /tmp/judge_<port>.log 2>&1 &
sleep 2
```

## Output contract

Write your scoring to the output path given below, in exactly this format:

```
REFERENCE_TOTAL: <n>

R1 | cand_1: HIT|MISS | cand_2: HIT|MISS | <ref defect one-liner>
R2 | cand_1: HIT|MISS | cand_2: HIT|MISS | <ref defect one-liner>
...

CAND_1_EXTRAS
- CONFIRMED_REAL | <one line> | <how you reproduced it>
- FALSE_ALARM | <one line> | <why not a defect>

CAND_2_EXTRAS
- CONFIRMED_REAL | <one line> | <how you reproduced it>
- FALSE_ALARM | <one line> | <why not a defect>

TOTALS
cand_1: hits=<n>/<REFERENCE_TOTAL>  confirmed_extras=<n>  false_alarms=<n>
cand_2: hits=<n>/<REFERENCE_TOTAL>  confirmed_extras=<n>  false_alarms=<n>
```

Your final reply must be ONLY the two TOTALS lines.
