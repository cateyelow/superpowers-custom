# UI-gate A/B — results

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
