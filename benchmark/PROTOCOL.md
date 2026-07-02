# SDD skill before/after behavioral benchmark — protocol

Pre-registered before results were seen (2026-07-02). Compares the subagent-driven-development
skill cluster at `0f51648` (**condition K**, pre-audit) vs `22cc984` (**condition M**, deployed)
— see KEY.md (judges must never read it).

## Setup
- 3 tasks × 2 conditions = 6 runs under `runs/<task>_<K|M>/`, each an isolated directory holding
  an anonymized `workflow/` snapshot, `task.md`, and required artifacts (`src/`, `prompts/`,
  `process.json`, `codex_*.out`).
- Each run: a fresh controller agent follows its pinned workflow literally, dispatching REAL
  implementer subagents (nested Agent dispatch verified by probe) and running REAL Codex reviews
  (host-safe exec form). Identical controller prompt across conditions except the base path.
- Symmetric deviations from the skill text (applied to BOTH arms, excluded from comparison):
  no git worktrees (dir isolation instead), max 2 fix rounds per gate (cost bound), and an
  absolute browser-safety rule (never browser_close — the K-snapshot's mandate would kill the
  shared logged-in Chrome; that fix is considered validated by the earlier live smoke test, not
  by this A/B).

## Metrics (in order of authority)
1. **Deterministic probes** — `scripts/probe_ratelimit.mjs` (11 checks), `scripts/probe_csvimport.sh`
   (~14 checks), `scripts/signup_checklist.md` executed verbatim by a checker agent per signup run
   (13 checks). Run by the orchestrator, not the run's own controller.
2. **Run's own test suite** — `node --test src/` green or not.
3. **Blind requirement coverage** — per task, one judge receives BOTH candidates' `src/` under
   anonymized names (order randomized) plus the task spec, and scores each R1–R12 as
   FULL / PARTIAL / MISSING with cited evidence. Judges never see `process.json`, `prompts/`,
   `workflow/`, codex outputs, or condition names.
4. **Process conformance** (manipulation check, not blind) — from `process.json` + `prompts/`:
   which gates actually ran (spec review, quality review, browser eval, final review), fix rounds,
   and whether implementer dispatches carried an explicit acceptance-criteria block.

## Decision rule (pre-registered)
- M is confirmed better only if: total deterministic-probe passes(M) ≥ passes(K) AND blind
  coverage (FULL=1, PARTIAL=0.5) for M ≥ K, with at least one strict improvement somewhere.
- Any metric where M < K − 1 point ⇒ investigate before claiming anything; report regressions
  verbatim either way.
- n=3 tasks: results are directional evidence, not statistics. Report per-task, no averaging away
  a regression.

## Threats to validity (acknowledged upfront)
- Same underlying model in both arms shares training priors; deltas measure SKILL TEXT effect only.
- The session-level "code review = Codex, never self-review" preamble reaches both arms' agents,
  shrinking the measurable final-gate delta (K's final gate said "code reviewer subagent").
- Single run per cell (no repeats): noise from sampling is uncontrolled; treat small deltas as ties.
