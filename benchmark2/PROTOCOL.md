# UI-gate A/B — protocol (pre-registered)

Written and frozen BEFORE any result was seen. Compares the **vanilla** upstream
superpowers v6.2.0 review gate against the **custom** fork's `web-app-evaluation`
blind-signoff gate.

## Why this design, and what it fixes

The 2026-07-02 benchmark returned "indistinguishable" but could not have returned
anything else. Four defects, all confirmed against its own artifacts:

1. **Ceiling.** Probes scored 11/11, 17/17; blind coverage 12/12 FULL in 4 of 6
   cells. No headroom to detect improvement.
2. **Features never fired.** Ledger, five-round breaker, plan-scoped workspace and
   trivial-task batching cannot activate on a 2-3 file greenfield single task.
   Observed fix rounds were 0,1,0,1,1,0 — the breaker needs 4+.
3. **n=1 per cell**, no repeats; its own protocol concedes sampling noise is
   uncontrolled.
4. **Contamination.** The session-level "review = Codex" rule reached both arms;
   all three K runs reviewed through Codex despite their skill text saying otherwise.

This protocol fixes all four:

1. **Ceiling** → the dependent variable is *defect recall on a naturally defective
   artifact*, not pass/fail on a fully specified probe. Recall has resolution.
2. **Features fire** → the gate under test IS the variable; it runs by construction.
3. **n** → 3 independent artifacts, and the largest noise source is eliminated
   outright (below).
4. **Contamination** → the vanilla arm has no `web-app-evaluation` skill *file*.
   A session rule cannot supply a methodology that does not exist on disk. The
   session's generic "verify in a real browser" instruction is deliberately left
   in place for BOTH arms — it is exactly the contamination we are measuring
   against, and the custom arm must beat it to earn its keep.

**The key move: implementation is held fixed.** Both arms receive the *same*
artifact. Prior work showed inter-implementer variance swamped the gate signal
("in every case the OTHER arm's implementer simply didn't make that mistake").
Fixing the artifact removes that variance and isolates the gate.

## Scope and honest limits

This measures ONE difference: the browser-evaluation gate. It does NOT measure
SDD end-to-end, ledger recovery, or the fix loop. That narrowing is deliberate —
prior analysis reduced the custom fork's non-cosmetic delta to (a) this gate,
(b) host-safety plumbing that keeps sessions from wedging, (c) self-review
avoidance already enforced session-wide. (b) and (c) are availability and
policy properties, not output-quality deltas, and are not A/B-able here.

## Materials

Three single-file web artifacts (no build, no deps), each opened directly by
`file://`. Specs are **deliberately incomplete**: they state the happy path and
stay silent on accessibility, touch targets, contrast, focus management, empty
and error states, and responsive behavior. Defects are expected to arise
naturally, as they did in the prior benchmark (a 24×24px touch target and a
3.71:1 disabled-button contrast both slipped every internal gate there).

- `A_upload` — drag-and-drop file upload widget
- `B_checkout` — three-step checkout form
- `C_table` — filterable/sortable data table

Each is generated ONCE by `codex-worker` from its incomplete spec, then frozen
and copied byte-identically into both arms.

## Arms

| | VANILLA (V) | CUSTOM (C) |
|---|---|---|
| Skill source | upstream v6.2.0 `44c9b2d` | fork `c95fbad` |
| Gate | `requesting-code-review` code review only — upstream ships no browser-evaluation skill | `web-app-evaluation`: operationalized checklist, blind evaluator with no build history, three viewports, final BLIND signoff |
| Session context | identical | identical |

Both arms are dispatched as fresh subagents with the arm's skill text pinned and
pasted verbatim; neither is told an experiment is running, nor which arm it is.

## Dependent variables

Primary: **recall against ground truth** — of the defects an independent
adjudicator confirms exist in the artifact, what fraction did the arm report?

Secondary:
- **Precision** — reported items that ground truth rejects (false alarms).
- **User-visible severity mix** — blocking vs minor, per ground truth's labels.

## Ground truth

Built per artifact by an adjudicator that receives the artifact and the
incomplete spec but **never** sees either arm's report, and is instructed to
enumerate user-visible defects with file:line or a reproduction step. Ground
truth is frozen before arm reports are compared to it. Items that only one arm
found are re-adjudicated on their merits, not by which arm found them
(a defect is real or not regardless of who reported it).

## Decision rule (pre-registered)

C is confirmed better only if mean recall(C) > mean recall(V) with the direction
holding on at least 2 of 3 artifacts. A single-artifact difference with mixed
direction elsewhere is reported as noise, not a win. If recall ties within one
defect on every artifact, the verdict is **indistinguishable on this axis** and
the gate is not carrying its cost.

Regressions are reported verbatim either way. n=3 is directional evidence, not
statistics; no averaging away a reversal.

## Threats acknowledged upfront

- Same underlying model in both arms; this measures GATE METHODOLOGY, not model.
- The adjudicator and the custom arm share a model family and may share blind
  spots; defects invisible to both are invisible to this experiment.
- Three artifacts of one kind (single-file web UI) — does not generalize to
  multi-page apps or frameworks.
- The custom arm's checklist prompts for viewport and contrast checks by name;
  if ground truth is dominated by those categories the result is partly
  definitional. Reported per-category to make that visible.
