# Spec Compliance Reviewer — via Codex CLI

Verify spec compliance using **Codex CLI (OpenAI GPT)**, not a Claude subagent. Using a different model family than the Generator (Claude) eliminates self-evaluation bias — this is the core of the Generator-Evaluator pattern.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less)

**Only dispatch after implementer reports DONE.**

## How to Run

Use `codex review` with a heredoc to avoid shell injection from special characters in the spec text:

```bash
codex review --base {BASE_SHA} "$(cat <<'REVIEW_EOF'
You are reviewing whether an implementation matches its specification.

## What Was Requested
{FULL TEXT of task requirements — paste here}

## What Implementer Claims They Built
{From implementer's report — paste here}

## CRITICAL: Do Not Trust the Report
The implementer's report may be incomplete, inaccurate, or optimistic. Verify EVERYTHING by reading the actual diff.

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
REVIEW_EOF
)" 2>&1
```

## Parsing the Result

**You MUST parse the structured `status:` field from Codex output to determine next action.**

| Parsed Status | Action |
|---------------|--------|
| `status: APPROVED` | Proceed to code quality review (also via Codex) |
| `status: NEEDS_FIXES` | Implementer fixes listed issues → re-run this review |
| Credit/billing/rate-limit error in output | → **CREDIT STOP** (see below) |
| No parseable status / other error | Retry once. If still unparseable, **HARD STOP** and report to user |

**Decision logic (pseudo-code):**
```
exit_code, result = run_codex_review()

# Step 1: Check for CLI-level billing failure FIRST (exit code + specific error patterns)
# IMPORTANT: Only match CLI error messages, NOT review content about billing/credits features
if exit_code != 0 AND result matches /Error.*rate.limit|Error.*quota.*exceeded|Error.*insufficient.*funds|Error.*billing|429.*Too.Many.Requests/:
    STATUS = "BLOCKED_CREDIT"

# Step 2: Parse structured status from review output
elif result contains "status: APPROVED":
    STATUS = "APPROVED"
elif result contains "status: NEEDS_FIXES":
    STATUS = "NEEDS_FIXES"
else:
    STATUS = "BLOCKED_ERROR"

# Step 3: Act on status
if STATUS == "BLOCKED_CREDIT":
    HARD_STOP_CREDIT()
elif STATUS == "BLOCKED_ERROR":
    retry once, then HARD_STOP_ERROR()
elif STATUS == "NEEDS_FIXES":
    send issues to implementer, then re-run this review
elif STATUS == "APPROVED":
    proceed to code quality review
```

**IMPORTANT: Credit detection must NOT match review content.** A review saying "insufficient test coverage" or reviewing a billing feature is NOT a credit error. Only match when the CLI itself fails (non-zero exit code + error pattern from the OpenAI API).

## Credit Exhaustion — HARD STOP

If Codex returns any credit/billing/quota/rate-limit error:

```
⛔ HARD STOP: Codex CLI 크레딧이 소진되었습니다.

리뷰를 건너뛸 수 없습니다. 작업을 즉시 중단합니다.
OpenAI 계정에서 크레딧을 충전한 후 다시 진행해주세요.
https://platform.openai.com/account/billing

충전 완료 후 알려주시면 이어서 진행하겠습니다.
```

**This is a blocking state. The ONLY way to exit is user confirmation that credits are recharged.**

DO NOT: skip review, fall back to Claude, retry without credits, or proceed with any work.
