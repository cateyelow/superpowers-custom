# Playwright Evaluator Prompt Template

Use this template when dispatching a Playwright evaluator subagent for web projects.

**Purpose:** Verify the implemented feature actually works in the browser by interacting with it like a real user.

**Only dispatch after code quality review passes AND the app is confirmed running (readiness probe passed).**

## Dispatch Format

This is pseudocode showing what to pass to the Agent tool — adapt to the actual Agent tool invocation syntax:

```
Agent tool (superpowers:playwright-evaluator):
  description: "Playwright evaluate Task N: [task name]"
  prompt: |
    Evaluate the running web application for Task N: [task name]

    ## App URL

    [URL where the app is running, e.g. http://localhost:5173]

    ## What Was Built (CLAIM ONLY — DO NOT TRUST)

    [From implementer's report. This is what they CLAIM to have built.
     You must verify everything against the Requirements below.
     The implementer may be incomplete, inaccurate, or optimistic.]

    ## Requirements (SOURCE OF TRUTH)

    [FULL TEXT of task requirements — this is what the app SHOULD do.
     Evaluate against THIS, not against what the implementer claims.]

    ## Specific Test Scenarios

    1. [Scenario: Navigate to X, click Y, expect Z]
    2. [Scenario: Fill form with A, submit, expect B]
    3. [Edge case: Try empty input, expect validation message]
    4. [Edge case: Try rapid double-click, expect no duplicate]
    5. [Edge case: Refresh page, verify data persists]
    6. [Edge case: Keyboard-only navigation of core flow]

    ## Previously Found Issues (if re-evaluating)

    [List of issues from previous evaluation that should now be fixed.
     Verify EACH previous issue is actually resolved.]

    Follow your evaluation process — FUNCTIONALITY FIRST:
    1. Functional Testing — test every scenario against Requirements
    2. Technical Verification — console errors, network requests, persistence
    3. UI/UX Quality — visual consistency, responsiveness
    4. First Impression — informational only, does not drive verdict

    Be skeptical. Take screenshots as evidence. Report what you actually see.
    Apply hard caps to scores. Verdict is driven by issues, NOT by score sum.
```

## Handling the Verdict

| Verdict | Structured Status | Action |
|---------|------------------|--------|
| `PASS` | `critical_issues: 0, important_issues: 0` | Mark task complete, proceed |
| `PASS_WITH_FIXES` | `critical_issues: 0, important_issues: N` | Implementer fixes → Codex re-reviews fixes → re-evaluate |
| `FAIL` | `critical_issues: N` | Implementer fixes → Codex re-reviews fixes → re-evaluate |

**Re-evaluation loop continues until PASS.**

**Important:** After implementer fixes browser issues, the fix code MUST go through Codex spec + quality review again before the next Playwright evaluation. Fixes that bypass code review are unreviewed code.
