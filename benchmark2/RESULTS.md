# UI-gate A/B — results

# Arm D3 — behavioural experiments as a third pass: ADOPTED

Pre-registered in KEY.md before any D3 report was read. D3 = D2's report reused
verbatim as passes 1-2, plus a third pass fed by harness_D/behavior_probe.py,
which DRIVES the page rather than measuring it. Baseline is D2.

| Artifact | GT | D2 | D3 | D2 FA | D3 FA | winner |
|---|---|---|---|---|---|---|
| A upload   | 18 | 14/18 (77.8%) | **17/18 (94.4%)** | 1 | 1 | D3 |
| B checkout | 11 | 8/11 (72.7%)  | **11/11 (100%)**  | 0 | 0 | D3 |
| C table    | 5  | 5/5 (100%)    | 5/5 (100%)        | 0 | 0 | tie |
| **Mean recall** | | **83.5%** | **98.1%** | | | |

    R1  mean(D3) > mean(D2)   PASS   98.1% vs 83.5%, +14.6 points
    R2  D3 wins >= 2 of 3     PASS   2 wins, 1 tie, 0 losses
    R3  D3 false alarms <= D2 PASS   1 vs 1 — and D3's is INHERITED from D2's
                                     report, so all three additions are real

## The full ladder — same artifacts, same ground truth, same judging procedure

| Arm | A | B | C | mean recall |
|---|---|---|---|---|
| no skill at all          | 11/18 | 7/11  | 1/5 | 48.2% |
| stock superpowers (V)    | 12/18 | 7/11  | 5/5 | 76.8% |
| + static probe, after (D2)   | 14/18 | 8/11  | 5/5 | 83.5% |
| + behavioural probe, after (D3) | **17/18** | **11/11** | 5/5 | **98.1%** |

Against stock superpowers: **+21.3 points**, and as a miss rate 23.2% -> 1.9%,
i.e. **92% of what was being missed is now caught**, with no increase in false
alarms.

## Why the third pass works

Every one of the 7 defects D2 still missed was BEHAVIOURAL, and scoring them
showed none was a judgement call — each was an experiment nobody had run:

| D2 miss | invariant | how it was caught |
|---|---|---|
| A-R1 Remove dead mid-upload | RESPONSIVE | held a node reference, started the upload, pressed with a real mousedown/mouseup: `document.contains(ref) === false`, 33 mutation batches |
| A-R4 no drop guard | DROP-GUARD | dispatched a cancelable drop outside the zone; `defaultPrevented === false` |
| A-R18 duplicate files | IDEMPOTENT | selected the same file twice, counted rows, checked for a warning |
| B-R3 backspace no-op | CARET | real Backspace at the offset past an auto-inserted separator: value unchanged, caret thrown to 19 |
| B-R10 past expiry accepted | SEMANTIC | entered 01/20; `checkValidity() === true` |
| B-R11 no error state | ERROR-STATE | submitted invalid values; zero `aria-invalid`, zero live regions |
| A-R10 silent empty state | ANNOUNCE | detected, but the reviewer did not adopt it — the one defect still missed |

C produced ZERO experiment results, which is correct: all five of C's defects
are static. A probe that invents findings on a clean page would have cost
precision; this one stayed silent and the third pass appended nothing.

## Two implementation traps, same lesson

Both checks silently passed at first, and in both cases the workaround was
hiding the defect:

1. **CARET implemented in JS.** Assigning `el.value` then calling
   `setSelectionRange` overwrites whatever the page's own input handler did to
   the caret — which IS the defect. Real key events found it immediately.
2. **RESPONSIVE via Playwright element handles.** The handle goes stale the
   moment the list re-renders, `click()` throws, and the exception was
   swallowed. The staleness is the defect; measuring node survival directly
   found it.

**Drive the page the way a user does. A convenience shortcut in the experiment
masks the very failure the experiment exists to find.**

## Honest limits

- Scope is still three single-file web UIs. This says nothing yet about other
  frameworks. What transfers is the SHAPE — judgement pass, then deterministic
  measurement, then behavioural experiments, in that order — and the invariant
  list, which is not DOM-specific even though this implementation is.
- 98.1% is against an adjudicated reference built by an auditor with full source
  access. It is not "finds every possible defect".
- Cost is three agent passes plus two probe runs per artifact.
- One reference defect (A-R10) is still missed even though the probe flagged it,
  so the ceiling here is the reviewer's adoption, not the probe's coverage.

---


# Arm D2 — the same probe delivered AFTER the review: ADOPTED

Pre-registered in KEY.md (assignment + the same R1-R3 rules) before any D2
report was read. D2 = arm V's existing report reused verbatim as pass 1, plus a
second pass that reads it together with the probe output and appends only what
it verifies itself in the browser. Probe precision was raised first, on the
evidence of arm D's failures.

| Artifact | GT | V | D2 | V false alarms | D2 false alarms | winner |
|---|---|---|---|---|---|---|
| A upload   | 18 | 12/18 (66.7%) | **14/18 (77.8%)** | 0 | 0 | D2 |
| B checkout | 11 | 7/11 (63.6%)  | **8/11 (72.7%)**  | 0 | 0 | D2 |
| C table    | 5  | 5/5 (100%)    | 5/5 (100%)        | 0 | 0 | tie |
| **Mean recall** | | **76.8%** | **83.5%** | | | |

    R1  mean(D2) > mean(V)    PASS   83.5% vs 76.8%, +6.7 points
    R2  D2 wins >= 2 of 3     PASS   2 wins, 1 tie, 0 losses
    R3  D2 false alarms <= V  PASS   0 vs 0

**All three pass. Adopted.**

What D2 added, and nothing else:
- A: the drop-zone boundary at 2.27:1 (R15) and the button focus ring at 1.5:1
  (R14). **R14 had been missed by every agent arm ever run here** — no-skill,
  upstream, and the custom fork alike.
- B: control boundaries at 1.47:1 (R9), also missed by every previous arm.
- C: nothing. V had already found all five, so the second pass appended
  nothing and left the report byte-identical. It did not pad.

## Why the same probe wins here and lost as arm D

Only the delivery point changed.

Arm D put the measurements in front of the reviewer. It gained R4/R14/R15 and
lost R2/R5/R7 — all three losses behavioural — for a net zero. Attention is
conserved: budget spent confirming a list is budget not spent driving the page.

D2 puts the measurements after a finished review. Pass 1 is a normal review
with nothing to anchor on; pass 2 can only add. The floor is therefore V by
construction, and the only open question was whether the additions are real.
They were: 3 additions across 3 artifacts, all three confirmed against the
reference, zero false alarms.

The precision work mattered too, and arm C proves it: with v2's noisier output
the same page produced 2 false alarms and a dropped true positive. With the
per-element overflow check removed, tap-target floors split by control type,
`:hover` dropped and `:disabled` demoted to an explicitly non-defect section,
the second pass added nothing at all to C — the correct answer.

## Honest limits

- **+6.7 points is an improvement, not a transformation.** It does not make
  Claude Code "substantially better"; it closes one specific, reproducible gap.
- **The gap it closes is narrow and real.** Every agent arm measured here
  catches TEXT contrast and systematically misses NON-TEXT contrast — control
  boundaries and focus indicators. A-R14 and B-R9 were invisible to all of
  them and are pure arithmetic over computed style.
- **Scope is three single-file web UIs.** Nothing here supports a claim about
  other frameworks. The transferable claim is about the shape — a deterministic
  measurement pass, run after the judgement pass, on whatever the framework
  makes measurable — not about these particular checks.
- **It costs one extra agent pass per artifact.**

---


# Arm D — deterministic probe fed to the reviewer up front: REJECTED

Pre-registered in KEY.md before any D report was read (assignment + rules R1-R3).
D = arm V byte-for-byte, plus a block of machine measurements from
harness_D/probe2.py. Scored blind against the same round-2 ground truth by the
same judging procedure (judging4).

| Artifact | GT | V hits | D hits | V false alarms | D false alarms | winner |
|---|---|---|---|---|---|---|
| A upload   | 18 | 12/18 (66.7%) | 12/18 (66.7%) | 0 | 0 | tie |
| B checkout | 11 | 7/11 (63.6%)  | **8/11 (72.7%)** | 0 | 0 | D |
| C table    | 5  | **5/5 (100%)** | 4/5 (80%) | 0 | **2** | V |
| **Mean recall** | | **76.8%** | **73.1%** | | | |

    R1  mean(D) > mean(V)   FAIL  (73.1% < 76.8%)
    R2  D wins >= 2 of 3    FAIL  (1 win, 1 tie, 1 loss)
    R3  D false alarms <= V FAIL  (2 > 0)

**All three fail. The harness is not adopted in this form.**

## Why — the probe worked, the delivery did not

The probe's own hypothesis was CONFIRMED. On A it delivered exactly the two
defects it was built for, both of which V missed:

- A-R14 focus ring 1.5:1 — V MISS, D **HIT**
- A-R15 drop-zone boundary 2.27:1 — V MISS, D **HIT**

And on B it recovered R9 (control boundaries 1.47:1), which V missed. Every
non-text-contrast defect the probe targeted landed.

It lost anyway, for two separate reasons:

**1. Attention is conserved (artifact A).** D gained R4, R14, R15 and lost R2,
R5, R7 — a 3-for-3 wash. All three losses are behavioural: focus thrown away
when an upload starts, the widget stuck after "Clear all" mid-upload, focus
lost when a button disables itself. Time spent confirming measurements is time
not spent driving the page. The prompt explicitly warned "do not let the list
below narrow where you look"; the warning did not work. **This is the same
mechanism that sank the custom fork's checklist** — only the payload differs
(measured values instead of category names).

**2. Probe noise hurt in BOTH directions (artifact C).** The two false alarms
were both probe items the agent failed to filter (an intended `overflow-x:auto`
scroll container; a WCAG-exempt `:disabled` label). And R5 — pagination buttons
at 94x38, which the probe reported explicitly — was DROPPED, because the
anti-noise guidance I wrote ("24-44px meets WCAG 2.5.8") told the agent to
discount exactly that measurement. The reference counts 38px as a defect.

So imprecise probe output does not merely add noise: the instructions needed to
suppress the noise also suppress true positives. **A probe that cannot separate
a defect from a non-defect transfers that judgement to the agent, and the agent
gets it wrong in both directions.**

## What this does NOT show

It does not show the measurements are worthless — they are, individually, the
only thing that found A-R14 and B-R9, which no agent arm has ever caught. It
shows that handing them to a reviewer *before* they review is the wrong
delivery. Two things follow, and both are testable:
1. raise the probe's precision so it stops emitting non-defects;
2. deliver it *after* a free-exploration pass, so it can only add.

---


> **Arm N added 2026-08-11.** The original question was *superpowers present vs
> absent*, not *fork vs upstream*. Arm N (no skill text at all) was run on the
> same artifacts, same round-2 ground truth, same isolated conditions, and
> scored blind against V by one judge. See "Three-way result" below — it is the
> headline. The fork-vs-upstream sections that follow remain valid and unchanged.

## Three-way result (the actual question)

| Artifact | GT | N hits | V hits | C hits | N real | V real | C real |
|---|---|---|---|---|---|---|---|
| A upload   | 18 | 11 | 11 | 9 | 11 | 13 | 10 |
| B checkout | 11 | 7  | 7  | 8 | 8  | 8  | 8  |
| C table    | 5  | **1** | **5** | 2 | 1 | 6 | 4 |
| **Mean recall** | | **48.2%** | **74.9%** | **54.2%** | | | |

N = no superpowers skill. V = stock upstream v6.2.0. C = custom fork.
N and V were scored by the same judge (judging3); C's figures come from
judging2. Judge reproducibility is good: V's A and B scores are identical
across the two independent scorings (11/18+2 extras, 7/11+1 extra).

**Ranking: upstream > custom > nothing.**

Having superpowers beats not having it — but the benefit is not uniform. On A
and B the arms tie on hits (11-11, 7-7); the entire gap comes from artifact C,
where the skill-less arm reported just 2 defects and caught 1 of 5, while
upstream caught 5 of 5.

Reading: **the skill raises the floor on thoroughness, not the ceiling on
ability.** Where defects are plentiful and obvious (A: 18 in the reference; B:
11) an unaided reviewer finds them anyway. Where the page looks fine and the
defects are subtle (C: 5, mostly 1.53:1 border contrast and a missing
interactive role) the unaided arm glanced and moved on. The skill's value is
that it stops you from declaring a clean-looking page clean.

That also explains why the custom fork loses to upstream while still beating
nothing: its checklist does force engagement, but it directs that engagement at
named categories, and on C it spent the attention on a WCAG-exempt disabled
control while missing the two live violations upstream caught.

---

# Fork vs upstream (the earlier question)

Protocol: PROTOCOL.md (pre-registered, frozen before any result was seen).
Blind key + candidate assignment: KEY.md (judges never read it).
V = vanilla upstream v6.2.0 `44c9b2d`. C = custom fork `c95fbad`.

Two rounds were run. Round 1 is reported for transparency but is **not** the
basis of the verdict — its observation conditions were broken (below).

## Round 2 (isolated conditions — the valid run)

Every cell drove its own headless Chromium from Python against a byte-identical
copy of the page. Implementation was held fixed: both arms reviewed the SAME
artifact, so no implementer-sampling variance enters the comparison.

| Artifact | GT defects | V hits | C hits | V recall | C recall | V real total | C real total | Direction |
|---|---|---|---|---|---|---|---|---|
| A upload   | 18 | 11 | 9 | 61.1% | 50.0% | 13 | 10 | **V** |
| B checkout | 11 | 7 | 8 | 63.6% | 72.7% | 8 | 8 | tie |
| C table    | 5  | 5 | 2 | 100%  | 40.0% | 7 | 4 | **V** |
| **Total**  | 34 | 23 | 19 | **74.9%** (mean) | **54.2%** (mean) | **28** | **22** | |

"real total" = GT hits + extras the judge independently verified as genuine.
False alarms: V 1, C 2.

## Verdict (per the pre-registered decision rule)

The rule: C is confirmed better only if mean recall(C) > mean recall(V) **and**
the direction holds on at least 2 of 3 artifacts.

**Not met, and not close.** C won 0 of 3 artifacts (one tie, two losses) and its
mean recall is ~21 points lower. The custom `web-app-evaluation` gate did not
improve user-visible defect detection over the vanilla arm; it detected fewer
defects and raised one more false alarm.

## Round 1 (contaminated — reported, not used)

| Artifact | GT | V real total | C real total |
|---|---|---|---|
| A | 14 | 11 | 11 |
| B | 12 | 9 | 6 |
| C | 6 | 4 | 2 |
| Total | 32 | 24 | 19 |

Round 1's conditions were defective in two ways, both my design error:

1. Cells were handed `file://` paths, but the Playwright MCP on this host
   **blocks the `file:` protocol**. Each cell improvised its own route to the
   page (own Python browser, ad-hoc HTTP server), so conditions were not equal.
2. The MCP is configured against a **shared CDP Chrome** (`--cdp-endpoint
   127.0.0.1:9222`) and six cells ran concurrently. Observed directly in the tab
   list: three cells driving the same page in the same browser at once.

This was **not** neutral noise. The custom methodology demands more browser
interaction, so it was more exposed to the contention: round 1 tool-use counts
were V 35/56/44 vs C 95/63/96. Round 2 removed the contention and C's counts
dropped to 35/56/32 while its detection rose (A 10→11, B 6→8, C 2→5).

Both rounds point the same direction, so the conclusion does not rest on the
broken one — but round 1 alone would have overstated the gap against C.

## What the numbers do and do not license

**Do:** on single-file web UI, adding the custom gate's methodology *on top of a
session that already mandates blind browser verification* does not increase
defect detection.

**Do not:** conclude the gate is worthless in general. Three limits are real:

- **The blind property was given to both arms.** This host's CLAUDE.md already
  orders "verify the exact user-visible flow in a real browser," and both arms
  were fresh subagents with no build history — i.e. already blind, already
  browser-driven. What was measured is the *marginal* effect of the checklist
  text, not the value of blind browser evaluation itself. On a host without that
  standing rule the comparison could differ.
- **The skill was flattened.** `web-app-evaluation` dispatches a separate
  evaluator subagent; the runner told each cell "you are the evaluator" so the
  arms stayed comparable. That removes one layer the real skill provides.
- **n=3, one artifact class.** No frameworks, no multi-page apps, no build step.

## An observed failure mode worth keeping

In artifact C the custom arm's only false alarm was a contrast complaint about
*disabled* pagination buttons (2.34:1) — WCAG 1.4.3 explicitly exempts inactive
components. In the same run it **missed the two real 1.53:1 border-contrast
violations** on the live controls. Naming contrast in a checklist appears to
have produced mechanical box-ticking on the wrong elements rather than
measurement of the right ones. The vanilla arm, with no checklist, scored 5/5
there.

This is the concrete mechanism behind the headline number: the checklist
narrowed attention instead of widening it.

## Cost

Round 1: 9 cells + 3 judges. Round 2: 9 cells + 3 judges. ~2.6M subagent tokens
total, plus three codex generations for the artifacts.
