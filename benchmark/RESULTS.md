# SDD skill before/after behavioral benchmark — results (2026-07-02)

Protocol: PROTOCOL.md (pre-registered). K = pre-audit `0f51648`, M = deployed `22cc984`.
Blind key + judge assignment: KEY.md. 6 runs completed, no cap hits, all gates executed.

## Scoreboard

| Metric | ratelimit K | ratelimit M | csvimport K | csvimport M | signupform K | signupform M |
|---|---|---|---|---|---|---|
| Deterministic probe | 11/11 | 11/11 | 17/17 | 17/17 | 13/13 (checker) | 11/13 (checker) |
| Own test suite | 19/19 | 22/22 | 32/32 | 28/28 | n/a (UI) | n/a (UI) |
| Blind coverage (FULL=1, PARTIAL=.5) | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 11.5/12 |
| Fix rounds used | 0 | 1 | 0 | 1 | 1 | 0 |
| Gates executed (spec/quality/final[/playwright]) | all | all | all | all | all (+3 UI evals) | all (+3 UI evals) |

## Verdict (per pre-registered decision rule)

**Indistinguishable.** M is not confirmed better (rule required M ≥ K everywhere plus one
strict win). K's only edge — signupform checker 13/13 vs 11/13 and coverage 12 vs 11.5 —
triggered the investigate clause; investigation attributes it to:

1. `pw_checklist_live` (M FAIL): the task spec itself is ambiguous — it lists FOUR conditions
   (≥10 chars, letter, digit, symbol) but says "checklist of the three rules". M merged
   letter+digit into one item (exactly 3 items); K showed 4. The blind coverage judge examined
   both and scored both FULL; only the checker's operationalization (a separate letter item)
   penalized M. Spec-authoring flaw, discounted to ~tie.
2. `mobile_375` / R11 (M FAIL, genuine): M's terms checkbox is 24×24px (44px met only via the
   adjacent label); K's is natively 44×44px. This is an implementer sampling difference — no
   edited skill text addresses touch-target sizing, and M's internal gates (implementer's own
   62-check verification, Codex quality+final reviews, playwright smoke + visual evaluator)
   ALL passed it, as K's gates passed K's real minor (3.71:1 disabled-button contrast).

Both CLI tasks were exact ties on every measure (probes, suites, blind coverage 12/12 FULL
for all four runs, and differential probes — fractional/NaN/Infinity limits, extra/duplicate
CSV header columns — behave identically K vs M).

## What the benchmark established beyond the tie

- **Spec completeness dominates; skill-text deltas of this size are below the noise floor at
  n=1/cell.** Replicates the 2026-06-19 measurement. All runs where the implementer got the
  full R1–R12 spec hit ceilings regardless of arm. K controllers even carried acceptance
  criteria spontaneously (the spec spelled them out), so M's mandatory AC-block template
  changed the dispatch prompt but could not change the outcome.
- **Final-gate contamination confirmed as pre-registered:** all THREE K runs ran their final
  review through Codex despite K's skill text saying "dispatch final code reviewer subagent"
  (Claude). The session-level "review = Codex" rule already enforces the behavior; the M skill
  edit codifies reality rather than changing it. The edit's value is consistency, not delta.
- **Fix rounds are implementer sampling noise, not review-depth signal.** M used 2 total fix
  rounds (fractional limit, loose header check) where K used 1 (email regex) — in every case
  the OTHER arm's implementer simply didn't make that mistake, and end states converged.
- **NEW defect found: pipeline-internal evaluators pass what independent checkers catch.**
  M's 24px checkbox and K's contrast miss both sailed through every internal gate; the blind
  external checkers caught them immediately. Independent adversarial evaluation ≠ pipeline
  self-evaluation, even when the pipeline uses a different model for code review.
- **NEW defect found: controller idle-wait stalls.** 3 of 6 controllers ended their turn to
  "wait" for a dispatched child instead of checking artifacts on disk; each needed a manual
  nudge (SendMessage) to resume, and two implementers finished unable to address their parent
  ("No agent named 'general-purpose' is currently addressable"). This is an SDD workflow gap
  on this host → fixed in skills/subagent-driven-development/SKILL.md (dispatch synchronously;
  never end the turn to wait; verify child completion by artifacts on disk).

## Costs

6 controller runs ≈ 470k subagent tokens (excl. children/codex), plus implementer children
(~65–96k each where dispatched as background), 3 blind judges ≈ 210k, 2 UI checkers ≈ 343k,
capability probe ≈ 22k. Codex reviews: 21 invocations, all completed under timeout.
