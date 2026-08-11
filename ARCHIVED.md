# ARCHIVED — 2026-08-11

This fork is **retired**. The host no longer loads it: `superpowers` now tracks
stock upstream (`obra/superpowers`, v6.2.0), and
`my-claude-config/scripts/win/plugin_protect.py` no longer re-pins this repo.

The clone is kept **only as the record of why**. Nothing here is live.

## Why it was retired

The fork's one testable asset — the `web-app-evaluation` browser gate — lost a
pre-registered blind A/B against stock upstream.

| | vanilla | custom |
|---|---|---|
| Mean UI-defect recall | **74.9%** | 54.2% |
| Verified real defects found | **28** | 22 |
| False alarms | 1 | 2 |
| Artifacts won (of 3) | **2** | 0 (1 tie) |

Design: 3 web artifacts, **implementation held fixed** so both arms reviewed a
byte-identical page (removing the implementer-sampling variance that swamped the
earlier 2026-07-02 benchmark), isolated per-cell headless browsers, blind
adjudication, blind scoring, candidate labels alternated. Protocol frozen before
any result was seen.

Observed mechanism, not just a number: naming contrast in a checklist produced
box-ticking on the wrong elements. In artifact C the custom arm flagged a
**WCAG-exempt disabled control** while missing **two real 1.53:1 violations**
that the checklist-free arm caught 5/5.

Everything else this fork was credited with turned out to be owned elsewhere and
survived its removal:

- host-safe codex invocation → `~/.claude/agents/codex-worker.md`
- GPT-implements / Claude-reviews split → `my-claude-config/CLAUDE.md`
- ledger, five-round breaker, scoped re-review, plan-scoped workspace →
  **upstream v6.2.0 itself**
- never-idle-wait rule → moved into `my-claude-config/CLAUDE.md`
- `flutter-app-evaluation` + `flutter-evaluator` → migrated to
  `my-claude-config/skills/` and `agents/` (never measured; this box has 5+
  Flutter projects, so it was kept rather than discarded)

## What is worth reading here

- `benchmark2/` — the A/B that retired this fork. `PROTOCOL.md` (pre-registered),
  `RESULTS.md`, `KEY.md`, 18 defect reports, 6 scorecards, both rounds.
  Round 1 is included and marked contaminated: cells were handed `file://` paths
  that the Playwright MCP blocks, and six cells shared one CDP Chrome. That
  contamination was biased **against** the custom arm, which drives the browser
  ~2x more — so round 2 (isolated) is the valid run. Both rounds agreed anyway.
- `benchmark/` — the earlier 2026-07-02 SDD skill-text A/B (K vs M, tied). Its
  own limits are documented in `benchmark2/PROTOCOL.md`: ceiling effects,
  features that never fired, n=1 per cell, session-preamble contamination.

## If you are tempted to re-fork

Don't add a gate on the strength of it sounding right. Re-run `benchmark2/` with
the gate in one arm. That harness exists precisely because two prior rounds of
skill-text intuition failed to survive measurement.
