---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements — ALWAYS uses Codex CLI (GPT) for cross-model review, never self-review
---

# Requesting Code Review

**ALWAYS use Codex CLI (GPT) for code review. NEVER self-review.**

Self-review is biased — the model that wrote the code will always think it's good. A different model (GPT via Codex CLI) provides genuine independent evaluation. This is the Generator-Evaluator pattern.

**Core principle:** Review via Codex CLI, not self-review. Always.

## When to Request Review

**Mandatory:**
- After each task (any workflow)
- After completing major feature
- Before merge to main
- Before claiming work is complete

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request — via Codex CLI

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Run Codex CLI review (NOT a Claude subagent, NOT self-review):**

```bash
codex review --base ${BASE_SHA} "$(cat <<'REVIEW_EOF'
Review these code changes for production readiness.

## What Was Implemented
{DESCRIPTION — what was built and why}

## Requirements
{PLAN_OR_REQUIREMENTS — what it should do}

## Review Checklist

### Code Quality
- Clean separation of concerns?
- Proper error handling?
- Type safety? DRY? Edge cases?

### Architecture
- Sound design decisions?
- Scalability? Performance? Security?

### Testing
- Tests actually test logic (not just mocks)?
- Edge cases covered?
- All tests passing?

### Requirements
- All plan requirements met?
- No scope creep?
- No missing features?

## Required Output Format

status: APPROVED | NEEDS_FIXES
strengths: [what's well done — file:line]
critical_issues: [list, or "none"]
important_issues: [list, or "none"]
minor_issues: [list, or "none"]

Status rules:
- APPROVED only when critical_issues AND important_issues are both "none"
- NEEDS_FIXES when any critical or important issue exists
REVIEW_EOF
)" 2>&1
```

**3. Handle credit errors:**

If exit code is non-zero AND output matches `insufficient_quota|rate.limit|billing|429`:

```
⛔ HARD STOP: Codex CLI 크레딧이 소진되었습니다.
리뷰를 건너뛸 수 없습니다. 작업을 즉시 중단합니다.
https://platform.openai.com/account/billing
```

**4. Act on feedback:**

| Codex Status | Action |
|-------------|--------|
| `status: APPROVED` | Proceed (to Playwright/Flutter eval if UI project, or mark complete) |
| `status: NEEDS_FIXES` | Fix issues → re-run Codex review |
| Credit error | HARD STOP — user must recharge |

## What This Replaces

| Before (DON'T) | After (DO) |
|-----------------|------------|
| "Let me do the self-review" | `codex review --base ...` |
| Dispatch Claude code-reviewer subagent | `codex review --base ...` |
| "Looks good to me" | Parse `status: APPROVED` from Codex |
| Claiming completion without external review | Codex review is mandatory gate |

## Red Flags — STOP if you catch yourself doing these

| Thought | Reality |
|---------|---------|
| "Let me quickly review my own code" | NO. Use Codex CLI. Self-review is biased. |
| "The code looks correct to me" | YOUR opinion doesn't count. Codex reviews. |
| "I'll just do a quick self-review" | There is no such thing. Codex CLI or nothing. |
| "Self-review before Codex" | The implementer's self-review checklist is a pre-flight check only. The FORMAL review is ALWAYS Codex CLI. |
| "Codex is slow, let me skip it" | Speed is not an excuse. Quality requires independent review. |

## Example

```
[Just completed: Add verification function]

You: Let me request code review via Codex CLI.

$ codex review --base a7981ec "Review these changes..."

Codex (GPT):
  status: NEEDS_FIXES
  strengths: Clean architecture, real tests
  critical_issues: none
  important_issues: Missing progress indicators for long operations
  minor_issues: Magic number (100) for reporting interval

You: [Fix progress indicators, re-run Codex review]

$ codex review --base a7981ec "Review these changes..."

Codex (GPT):
  status: APPROVED
  strengths: Clean architecture, good progress reporting
  critical_issues: none
  important_issues: none

[Proceed to next task or Playwright/Flutter evaluation]
```

## Integration with Workflows

**Any workflow — code review = Codex CLI. No exceptions.**

**Subagent-Driven Development:**
- Codex spec review + Codex quality review per task

**Executing Plans / Ad-Hoc Development:**
- Codex review before merge or when feature complete

**Web/Flutter Projects:**
- Codex review THEN Playwright/Flutter evaluator
