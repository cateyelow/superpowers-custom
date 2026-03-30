# Code Quality Reviewer — via Codex CLI

Verify code quality using **Codex CLI (OpenAI GPT)**, not a Claude subagent. The Generator (Claude) wrote the code — a different model (GPT) reviews it to prevent self-evaluation bias.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes (also via Codex).**

## How to Run

Use `codex review` with a heredoc to avoid shell injection:

```bash
codex review --base {BASE_SHA} "$(cat <<'REVIEW_EOF'
Review the code quality of these changes.

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
REVIEW_EOF
)" 2>&1
```

## Parsing the Result

**Parse the structured `status:` field to determine next action.**

| Parsed Status | Action |
|---------------|--------|
| `status: APPROVED` | Proceed to Playwright evaluation (web project) or mark task complete |
| `status: NEEDS_FIXES` | Implementer fixes listed issues → re-run this review |
| Credit/billing/rate-limit error | → **CREDIT STOP** (see below) |
| No parseable status / other error | Retry once. If still unparseable, HARD STOP and report |

**Decision logic (same pattern as spec-reviewer):**
```
result = run_codex_review()

if result contains "rate limit" or "quota" or "credit" or "billing" or "insufficient":
    STATUS = "BLOCKED_CREDIT"
elif result contains "status: APPROVED":
    STATUS = "APPROVED"
elif result contains "status: NEEDS_FIXES":
    STATUS = "NEEDS_FIXES"
else:
    STATUS = "BLOCKED_ERROR"

# Same branching as spec-reviewer-prompt.md
```

## Credit Exhaustion — HARD STOP

Same as spec-reviewer-prompt.md:

```
⛔ HARD STOP: Codex CLI 크레딧이 소진되었습니다.

리뷰를 건너뛸 수 없습니다. 작업을 즉시 중단합니다.
OpenAI 계정에서 크레딧을 충전한 후 다시 진행해주세요.
https://platform.openai.com/account/billing

충전 완료 후 알려주시면 이어서 진행하겠습니다.
```

**Blocking state. ONLY exits on user confirmation. No fallback. No skipping.**
