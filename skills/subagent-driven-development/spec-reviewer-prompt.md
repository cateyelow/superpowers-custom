# Spec Compliance Reviewer — via Codex CLI

Verify spec compliance using **Codex CLI (OpenAI GPT)**, not a Claude subagent. Using a different model family than the Generator (Claude) eliminates self-evaluation bias — this is the core of the Generator-Evaluator pattern.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less)

**Only dispatch after implementer reports DONE.**

## Credit Check — MANDATORY BEFORE EVERY CODEX CALL

Before running any Codex review, check that credits are available. If the output contains `rate limit`, `quota`, `credit`, `billing`, `insufficient`, or any payment-related error:

```
⛔ HARD STOP: Codex CLI 크레딧이 소진되었습니다.

리뷰를 건너뛸 수 없습니다. 작업을 즉시 중단합니다.
OpenAI 계정에서 크레딧을 충전한 후 다시 진행해주세요.
https://platform.openai.com/account/billing

충전 완료 후 알려주시면 이어서 진행하겠습니다.
```

**DO NOT:**
- Skip review and continue to next task
- Fall back to Claude subagent for review
- Retry without credits
- Proceed with any further work

**STOP MEANS STOP.** Wait for explicit user confirmation that credits are recharged.

## How to Run

```bash
codex review --base {BASE_SHA} "You are reviewing whether an implementation matches its specification.

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

Report:
- ✅ Spec compliant (if everything matches)
- ❌ Issues: [list what's missing or extra, with file:line]" 2>&1
```

## Handling Results

| Codex Output | Action |
|-------------|--------|
| ✅ Spec compliant | Proceed to code quality review (also via Codex) |
| ❌ Issues found | Implementer fixes issues → re-run this review |
| Credit/billing error | **HARD STOP** — tell user to recharge |
| Other error | Retry once. If still failing, HARD STOP and report to user |
