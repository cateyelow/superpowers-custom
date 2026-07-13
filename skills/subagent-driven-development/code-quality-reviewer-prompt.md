# Code Quality Reviewer — Claude subagent (fresh context)

Verify code quality with a **fresh-context Claude subagent**, not Codex. The Generator is now **Codex/GPT** (the `codex-worker` implementer) — a Claude reviewer is the different model family that prevents self-evaluation bias. Do NOT review in the controller's own context.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes.**

**Two uses, two bases:** per-task review uses `{BASE_SHA}` = the commit before this task started. The FINAL whole-implementation review uses `{BASE_SHA}` = the commit before Task 1 (the plan's starting point), `{WHAT_WAS_IMPLEMENTED}` = the plan's task list summary, and `{DESCRIPTION}` = the plan's goal statement.

## How to Dispatch

Dispatch synchronously via the Agent tool and wait for the result. The reviewer reads the diff itself — do not paste the diff into the prompt.

```
Agent tool (general-purpose):
  description: "Quality review Task N: [task name]"
  prompt: |
    You are a code-quality REVIEWER with fresh eyes. You did not write this code.
    Report only — do NOT modify any files.

    Work from: {PROJECT_DIR}
    Inspect the changes yourself: run `git --no-pager diff {BASE_SHA}..HEAD`, then read
    the actual source files the diff touches. Run the project's type-checker/linter/tests
    if the claims below depend on them.

    ## What Was Implemented
    {WHAT_WAS_IMPLEMENTED — from implementer's report}

    ## Task Context
    {DESCRIPTION — what this task is and where it fits}

    ## Code Quality Checklist

    ### Architecture
    - Does each file have one clear responsibility with a well-defined interface?
    - Are units decomposed so they can be understood and tested independently?
    - Sound design decisions? Scalability? Performance implications?
    - Security concerns?

    ### Code Quality
    - Clean separation of concerns?
    - Proper error handling?
    - Type safety (if applicable)?
    - DRY principle followed?
    - Edge cases handled?

    ### Testing
    - Tests actually test logic (not just mocks)?
    - Edge cases covered?
    - Integration tests where needed?
    - All tests passing?

    ### File Organization
    - Following the expected file structure?
    - New files are focused and not already large?
    - Existing files not significantly bloated by this change?

    ## Required Output Format (MUST follow exactly)

    status: APPROVED | NEEDS_FIXES | BLOCKED_ERROR
    strengths: [what's well done — file:line references]
    critical_issues: [list, or "none"]
    important_issues: [list, or "none"]
    minor_issues: [list, or "none"]

    ## Status Determination Rule (MUST follow exactly)
    - APPROVED: ONLY when critical_issues is "none" AND important_issues is "none"
      (minor_issues may still be present — they do not block approval)
    - NEEDS_FIXES: when critical_issues OR important_issues has any entries
    - BLOCKED_ERROR: when you cannot complete the review for technical reasons
```

## Parsing the Result

**Parse the structured `status:` field from the subagent's reply to determine next action.**

| Parsed Status | Action |
|---------------|--------|
| `status: APPROVED` | Proceed to Playwright/Flutter evaluation (UI project) or mark task complete |
| `status: NEEDS_FIXES` | Implementer (codex-worker) fixes listed issues → re-run this review |
| `status: BLOCKED_ERROR` or no parseable status | Retry once. If still unparseable, HARD STOP and report |

Claude reviews run on the session's own subscription — no OpenAI-credit failure mode here. (Credit exhaustion belongs to the **implementer** path: the codex-worker dispatch. See SKILL.md "Codex CLI credit requirement".)

**Never** downgrade a NEEDS_FIXES to "close enough". Reviewer found issues = implementer fixes them = review again.
