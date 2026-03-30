# Code Quality Reviewer — via Codex CLI

Verify code quality using **Codex CLI (OpenAI GPT)**, not a Claude subagent. The Generator (Claude) wrote the code — a different model (GPT) reviews it to prevent self-evaluation bias.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes (also via Codex).**

## Credit Check — MANDATORY

Same as spec-reviewer-prompt.md. If Codex returns any credit/billing/quota error:

```
⛔ HARD STOP: Codex CLI 크레딧이 소진되었습니다.

리뷰를 건너뛸 수 없습니다. 작업을 즉시 중단합니다.
OpenAI 계정에서 크레딧을 충전한 후 다시 진행해주세요.
https://platform.openai.com/account/billing

충전 완료 후 알려주시면 이어서 진행하겠습니다.
```

**STOP MEANS STOP.** No fallback. No skipping. No proceeding.

## How to Run

```bash
codex review --base {BASE_SHA} "Review the code quality of these changes.

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

## Output Format

### Strengths
[What's well done — be specific with file:line]

### Issues

#### Critical (Must Fix)
[Bugs, security issues, data loss risks]

#### Important (Should Fix)
[Architecture problems, missing error handling, test gaps]

#### Minor (Nice to Have)
[Code style, optimization, documentation]

### Assessment
Ready to proceed? [Yes / No / With fixes]" 2>&1
```

## Handling Results

| Codex Output | Action |
|-------------|--------|
| Ready: Yes | Proceed to Playwright evaluation (web) or mark complete |
| Ready: With fixes | Implementer fixes Important+ issues → re-run review |
| Ready: No | Implementer fixes Critical issues → re-run review |
| Credit/billing error | **HARD STOP** — tell user to recharge |
