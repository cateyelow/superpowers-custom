# Spec Compliance Reviewer — Claude subagent (fresh context)

Verify spec compliance with a **fresh-context Claude subagent**, not Codex. The Generator is now **Codex/GPT** (the `codex-worker` implementer) — a Claude reviewer is the different model family, which is what eliminates self-evaluation bias (the core of the Generator-Evaluator pattern). Do NOT review in the controller's own context: the controller watched the implementation happen and is biased; the reviewer must see only the spec and the diff.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less)

**Only dispatch after implementer reports DONE.**

## How to Dispatch

Dispatch synchronously via the Agent tool and wait for the result. The reviewer reads the diff itself — do not paste the diff into the prompt.

```
Agent tool (general-purpose):
  description: "Spec review Task N: [task name]"
  prompt: |
    You are a spec-compliance REVIEWER with fresh eyes. You did not write this code.
    Report only — do NOT modify any files.

    Work from: {PROJECT_DIR}
    Inspect the changes yourself: run `git --no-pager diff {BASE_SHA}..HEAD`, then read
    the actual source files the diff touches.

    ## What Was Requested
    {FULL TEXT of task requirements — paste here}

    ## What Implementer Claims They Built
    {From implementer's report — paste here}

    ## CRITICAL: Do Not Trust the Report
    The implementer's report may be incomplete, inaccurate, or optimistic. Verify
    EVERYTHING by reading the actual diff and source files.

    DO NOT take their word. DO read the code changes.

    ## Check For

    1. Missing requirements — anything in spec that's not in the code?
    2. Extra/unneeded work — anything in code that's not in spec?
    3. Misunderstandings — correct feature but wrong approach?

    ## Required Output Format (MUST follow exactly)

    status: APPROVED | NEEDS_FIXES | BLOCKED_ERROR
    missing: [list of missing requirements, or "none"]
    extra: [list of extra/unneeded work, or "none"]
    misunderstandings: [list, or "none"]
    details: [file:line references for each issue]

    ## Status Determination Rule (MUST follow exactly)
    - APPROVED: ONLY when missing is "none" AND extra is "none" AND misunderstandings is "none"
    - NEEDS_FIXES: when any of missing, extra, or misunderstandings has entries
    - BLOCKED_ERROR: when you cannot complete the review for technical reasons
```

## Parsing the Result

**Parse the structured `status:` field from the subagent's reply to determine next action.**

| Parsed Status | Action |
|---------------|--------|
| `status: APPROVED` | Proceed to code quality review (also a Claude subagent) |
| `status: NEEDS_FIXES` | Implementer (codex-worker) fixes listed issues → re-run this review |
| `status: BLOCKED_ERROR` or no parseable status | Retry once. If still unparseable, **HARD STOP** and report to user |

Claude reviews run on the session's own subscription — there is no OpenAI-credit failure mode here. (Credit exhaustion now belongs to the **implementer** path: the codex-worker dispatch. See SKILL.md "Codex CLI credit requirement".)

**Never** downgrade a NEEDS_FIXES to "close enough". Reviewer found issues = implementer fixes them = review again.
