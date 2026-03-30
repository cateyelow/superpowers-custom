# Playwright Evaluator Dispatch Template

**Purpose:** Verify a specific browser flow works. Keep it focused — one flow per dispatch.

**Only dispatch after code quality review passes AND the app is confirmed running.**

## Dispatch (functional smoke — mandatory gate)

```
Agent tool (superpowers:playwright-evaluator):
  description: "Smoke test: [flow name]"
  prompt: |
    Evaluate this running web app.

    URL:
    [http://localhost:5173]

    Scope:
    [1-2 sentences on what changed]

    Requirements:
    - [requirement]
    - [requirement]

    Primary Flow:
    1. [step]
    2. [step]
    3. [expected result]

    Targeted Checks:
    - [highest-risk check]
    - [second check]

    Recheck:
    - [previous issue to verify, or "none"]

    Responsive Check:
    - no

    Important:
    - Use the browser only.
    - Do not read code.
    - Do not score the app.
    - Fail on any material issue in this scope.
```

## Dispatch (visual/responsive — optional 2nd pass)

Only run this if:
- The task changed layout or styling
- This is the final full-app evaluation

```
Agent tool (superpowers:playwright-visual-evaluator):
  description: "Visual check: [flow name]"
  prompt: |
    Re-run this flow at 375px, 768px, and 1280px.

    URL: [http://localhost:5173]

    Flow:
    1. [step]
    2. [step]
    3. [expected result]

    Check layout, overflow, contrast, mobile usability.
```

## Handling the Verdict

| Verdict | Action |
|---------|--------|
| `PASS` | Mark task complete (or run visual pass if applicable) |
| `FAIL` with `blocking` findings | Implementer fixes → Codex re-reviews → re-dispatch smoke test |
| `FAIL` with `minor` only | Judgment call — fix or note for later |

**Fix code MUST go through Codex review before next evaluation.**
