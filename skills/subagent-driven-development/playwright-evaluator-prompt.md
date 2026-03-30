# Playwright Evaluator Prompt Template

Use this template when dispatching a Playwright evaluator subagent for web projects.

**Purpose:** Verify the implemented feature actually works in the browser by interacting with it like a real user.

**Only dispatch after code quality review passes AND the app is running.**

```
Agent tool (superpowers:playwright-evaluator):
  description: "Playwright evaluate Task N: [task name]"
  prompt: |
    Evaluate the running web application for Task N: [task name]

    ## App URL

    [URL where the app is running, e.g. http://localhost:5173]

    ## What Was Built

    [From implementer's report — what they claim to have built]

    ## Requirements

    [FULL TEXT of task requirements — what it SHOULD do]

    ## Specific Test Scenarios

    1. [Scenario: Navigate to X, click Y, expect Z]
    2. [Scenario: Fill form with A, submit, expect B]
    3. [Edge case: Try empty input, expect validation message]
    4. [Edge case: Try rapid double-click, expect no duplicate]

    ## Previously Found Issues (if re-evaluating)

    [List of issues from previous evaluation that should now be fixed]

    Follow your evaluation process:
    1. First Impression — screenshot landing page, check console
    2. Functional Testing — test every scenario above
    3. UI/UX Quality — visual consistency, responsiveness
    4. Technical Verification — console errors, network requests, state

    Be skeptical. Take screenshots as evidence. Report what you actually see.
```

**Evaluator returns:** Scores (5 categories, /10 each), Issues (Critical/Important/Minor), Verdict (PASS/FAIL/PASS_WITH_FIXES)

**Handling the verdict:**
- PASS → Mark task complete, proceed
- PASS_WITH_FIXES → Implementer fixes Important issues → re-evaluate
- FAIL → Implementer fixes Critical issues → re-evaluate
- Re-evaluation loop continues until PASS
