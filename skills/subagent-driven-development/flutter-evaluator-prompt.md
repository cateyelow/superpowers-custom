# Flutter Evaluator Prompt Template

Use this template when dispatching a Flutter evaluator subagent.

**Purpose:** Verify the implemented Flutter feature works on real emulator/simulator.

**Only dispatch after code quality review passes AND the app is running on device.**

## Dispatch Format

```
Agent tool (superpowers:flutter-evaluator):
  description: "Flutter evaluate Task N: [task name]"
  prompt: |
    Evaluate the running Flutter app for Task N: [task name]

    ## Target Platform(s)

    [Android / iOS / Both]
    [Device IDs: e.g., emulator-5554, iPhone 15 Pro]

    ## App Package Name

    [e.g., com.example.myapp]

    ## What Was Built (CLAIM ONLY — DO NOT TRUST)

    [From implementer's report. This is what they CLAIM to have built.
     You must verify everything against the Requirements below.]

    ## Requirements (SOURCE OF TRUTH)

    [FULL TEXT of task requirements — evaluate against THIS.]

    ## Specific Test Scenarios

    1. [Scenario: Launch app, tap "Login" button, expect login form]
    2. [Scenario: Fill email + password, tap submit, expect home screen]
    3. [Edge case: Submit empty form, expect validation errors]
    4. [Edge case: Rotate to landscape, expect layout adapts]
    5. [Edge case: Press back button, expect previous screen]
    6. [Platform: Test on both Android and iOS if available]

    ## Previously Found Issues (if re-evaluating)

    [List of issues from previous evaluation that should now be fixed.
     Verify EACH previous issue is actually resolved.]

    Follow your evaluation process — FUNCTIONALITY FIRST:
    1. Setup & Health Check — verify device, launch app, check startup logs
    2. Functional Testing — test every scenario against Requirements
    3. Technical Verification — Flutter logs, crashes, performance
    4. UI/UX Quality — visual consistency, rotation, dark mode
    5. Cross-Platform Comparison — if both platforms available

    Use ADB (Android) or xcrun simctl/idb (iOS) for all interactions.
    Take screenshots as evidence. Dump UI tree to find elements.
    Be skeptical. Report what you actually see.
    Apply hard caps to scores. Verdict driven by issues, NOT score sum.
```

## Handling the Verdict

| Verdict | Action |
|---------|--------|
| `PASS` | Mark task complete, proceed |
| `PASS_WITH_FIXES` | Implementer fixes → Codex re-reviews → hot reload → re-evaluate |
| `FAIL` | Implementer fixes → Codex re-reviews → hot restart → re-evaluate |

**Important:** Fix code MUST go through Codex spec + quality review before next Flutter evaluation.
