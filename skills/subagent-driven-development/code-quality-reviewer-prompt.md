# Code Quality Reviewer — via Codex CLI

Verify code quality using **Codex CLI (OpenAI GPT)**, not a Claude subagent. The Generator (Claude) wrote the code — a different model (GPT) reviews it to prevent self-evaluation bias.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes (also via Codex).**

**Two uses, two bases:** per-task review uses `{BASE_SHA}` = the commit before this task started. The FINAL whole-implementation review uses `{BASE_SHA}` = the commit before Task 1 (the plan's starting point), `{WHAT_WAS_IMPLEMENTED}` = the plan's task list summary, and `{DESCRIPTION}` = the plan's goal statement.

## How to Run

**Use the host-safe form.** On this host every `codex` run loads heavyweight MCP servers (`playwright` headed-Chrome, `serena`, `context7`) that can wedge codex so it never exits → the harness fires a completion notification only on process termination → you never get woken → infinite idle. `-c mcp_servers='{}'` loads zero MCP servers; `timeout -k 60 1200` guarantees termination (hence a guaranteed notification); `-s danger-full-access` avoids bwrap sandbox errors. Launch with `run_in_background: true` and **do not poll**.

```bash
cd {PROJECT_DIR} && git diff {BASE_SHA}..HEAD > /tmp/codex_review_diff.txt && \
timeout -k 60 1200 codex exec -s danger-full-access -c mcp_servers='{}' "$(cat <<'REVIEW_EOF'
Review the code quality of the changes. Read the diff at /tmp/codex_review_diff.txt and the actual source files.

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
REVIEW_EOF
)" < /dev/null > /tmp/codex_quality_review.out 2>&1
```

**Launch with `run_in_background: true`, then do NOT poll** (no `BashOutput`, no `Monitor`, no waiting this turn). The completion notification fires only when codex terminates; the `timeout -k 60 1200` wrapper guarantees that within ~20 min even on a hard hang. When it arrives, `Read /tmp/codex_quality_review.out` once and parse `status:`. **Exit 124/137 = codex hung or over-ran the timeout** → report the partial buffer and stop; do not silently relaunch.

## Parsing the Result

**Parse the structured `status:` field to determine next action.**

| Parsed Status | Action |
|---------------|--------|
| `status: APPROVED` | Proceed to Playwright/Flutter evaluation (UI project) or mark task complete |
| `status: NEEDS_FIXES` | Implementer fixes listed issues → re-run this review |
| Credit/billing/rate-limit error | → **CREDIT STOP** (see below) |
| No parseable status / other error | Retry once. If still unparseable, HARD STOP and report |

**Decision logic:**
```
exit_code, result = run_codex_exec()

# Credit detection: ONLY match CLI-level errors, NOT review content
if exit_code != 0 AND result matches /Error.*rate.limit|Error.*quota.*exceeded|Error.*insufficient.*(funds|quota)|Error.*billing|429.*Too.Many.Requests|insufficient_quota/:
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
