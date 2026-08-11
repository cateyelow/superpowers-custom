# Harness D — deterministic probe, scored against the same round-2 ground truth

Probe = `probe2.py`, run with no agent involved. Scored by hand against
`ground_truth2/{A,B,C}.txt`, the same reference V/C/N were scored against.
A hit requires the probe to report the same element AND the same measured
quantity as the reference defect.

## Probe alone

| Artifact | GT | probe hits | which |
|---|---|---|---|
| A upload   | 18 | **8**  | R9, R11, R12, R13, **R14**, **R15**, R16, R17 |
| B checkout | 11 | **3**  | R7, R8, **R9** |
| C table    | 5  | **4**  | R2, R3, R4, R5 |
| **Mean recall** | | **50.6%** | (44.4 / 27.3 / 80.0) |

vs V (stock upstream superpowers) = 74.9%. **The probe alone loses, decisively
and by design** — it cannot judge behaviour. Every defect it misses on A
(R1–R8, R10, R18) and B (R1–R6, R10, R11) is a logic/state/flow defect: a dead
Remove button mid-upload, a past expiry date accepted, focus dumped to `<body>`.
No amount of measuring finds those. That is the agent's half of the job.

## What matters: the probe covers exactly what the agents systematically miss

Cross-referencing `judging3/*/score.txt` (V and N scored on the same reference):

| Defect | N | V | probe | note |
|---|---|---|---|---|
| A-R14 focus ring 1.5:1 | MISS | MISS | **HIT** | **neither agent found it** |
| A-R15 drop-zone boundary 2.27:1 | HIT | MISS | **HIT** | recovers V's miss |
| A-R16 disabled label 1.98:1 | MISS | HIT | **HIT** | |
| A-R9 control nested in control | MISS | HIT | **HIT** | |
| B-R9 control boundaries 1.47:1 | MISS | MISS | **HIT** | **neither agent found it** |
| C-R2/R3 boundaries 1.53:1 | MISS | HIT | **HIT** | |
| C-R5 touch target 38px | MISS | HIT | **HIT** | |

The pattern is not random. **Both agents reliably catch TEXT contrast (A-R11,
R12, R13 — hit by both) and reliably miss NON-TEXT contrast: control
boundaries and focus indicators.** A-R14 and B-R9 were missed by *every* agent
arm run so far, and both are pure arithmetic on a computed style.

Union of V + probe:

| Artifact | V alone | + probe adds | union |
|---|---|---|---|
| A | 11/18 | R14, R15 | **13/18** (72.2%) |
| B | 7/11  | R9       | **8/11** (72.7%) |
| C | 5/5   | —        | **5/5** (100%) |
| **Mean** | **74.9%** | | **81.6%** |

## Noise the probe generates (why it cannot be piped straight to a report)

- `.upload-button:hover` box-shadow at 1.5:1 — a decorative hover shadow is not
  a focus indicator; no contrast minimum applies. **False positive.**
- `#search` / `#department` at 42px flagged `under-44` on C — the reference
  explicitly treats 42px as acceptable and calls out only the 38px buttons.
  **False positive.**
- `#clear-all` 61.5x33 — real measurement, but 33px clears WCAG 2.5.8's 24px
  minimum; only the 44px *guidance* is unmet. Over-reported as a defect.
- `:disabled` label contrast — WCAG-exempt. Reported (flagged `disabled: true`)
  because the reference DID accept A-R16 on legibility grounds, but the probe
  cannot tell R16's "this is the page's load state" from ordinary greying.

So the probe's output is **evidence, not findings**. Roughly a third of what it
emits needs a judgement call the probe cannot make. That is what fixes the
harness shape: probe measures → agent triages and adds behaviour. Piping the
probe's raw list into a report would trade V's misses for a pile of new false
alarms and lose on precision what it gained on recall.

## Bugs found in the probe itself (both silently zeroed a whole category)

1. **`[tabindex]` matched `tabindex="-1"`.** Programmatic focus targets are not
   controls; produced a false touch-target finding on `<h2 tabindex="-1">`.
2. **CSSOM walk collected nothing.** Since CSS Nesting shipped, a plain
   `CSSStyleRule` also exposes a (usually empty) `.cssRules`, so
   `if (r.cssRules) recurse; else collect;` recursed into *every* style rule
   and collected zero. This silently disabled the entire pseudo-class scan —
   every focus-ring and placeholder defect was invisible until fixed. The
   symptom was an empty result, not an error.
3. **Authored CSS colour syntax.** CSSOM returns `#98a2b3` and
   `rgb(64 95 216 / 28%)`, not the computed `rgb(r, g, b)` form. Hand-parsing
   dropped every pseudo finding; fixed by normalising through a throwaway
   element and reading back the computed value.
