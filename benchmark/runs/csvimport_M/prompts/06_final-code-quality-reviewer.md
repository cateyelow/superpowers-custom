FINAL whole-implementation code quality review. All tasks of the plan are complete; review the ENTIRE implementation from its starting point (empty src/ directory — greenfield, so the whole codebase is the change). This project is NOT a git repository, so there is no diff. Read the actual source files:
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/parser.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/importCsv.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/parser.test.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/package.json
You may also run the tests: cd /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M && node --test src/

## What Was Implemented (plan's task list summary)

Task 1 (the plan's only task): CSV contact-import CLI —
- src/parser.js: pure parseCsv(content) -> { contacts, errors } with HeaderError for fatal header conditions; hand-rolled character-level CSV tokenizer (quoted fields, escaped "" quotes, CRLF/LF, BOM) tracking original 1-based line numbers; exact header set {name,email,phone} enforced in any order (missing/unexpected/duplicate columns fatal); row validation (field count, non-empty name, syntactic email, case-insensitive duplicate email, phone normalized to digits by stripping spaces/dashes/parens).
- src/importCsv.js: thin CLI wrapper — --help/-h exit 0, argc errors exit 2, unreadable input/bad header/unwritable output exit 2, atomic temp+rename JSON write with trailing newline, per-row errors to stderr as "line <n>: <reason>", summary "imported <k>/<total> rows" to stdout, exit 0 all imported / 1 some rejected.
- src/parser.test.js: 28 tests / 8 suites — in-memory-string parser tests (quoted comma + escaped quotes, line numbers with mixed valid/invalid, duplicate email, header-only, LF/CRLF equivalence, BOM, exact-header enforcement) plus CLI end-to-end suite on mkdtemp fixtures (exit 0/1/2, JSON shape + trailing newline, stdout/stderr, no stray temp files).
- src/package.json: {"type":"module","main":"parser.test.js"} — ESM flag plus a documented workaround so the constraint-mandated literal command `node --test src/` works on this host's Node v22.19.0 (bare directory arg resolves via CJS main instead of test-file scanning).

One review round of fixes was already applied (exact header set enforcement) and re-approved for spec compliance; per-task quality review approved with no critical/important issues.

## Task Context (plan's goal statement)

Build a Node CLI (ESM, zero dependencies, Node 20+, no TypeScript) that imports a contacts CSV into a normalized JSON file ({ contacts: [{name,email,phone}] }, atomic write, trailing newline), with robust malformed-input handling: expected header name,email,phone (exact set, any order; missing column -> exit 2 naming it), correct CSV quoting semantics, per-row validation with stderr reports "line <n>: <reason>" using original 1-based line numbers (header = line 1), case-insensitive duplicate-email rejection ("duplicate email"), exit codes 0/1/2, header-only file OK (empty contacts, "imported 0/0 rows", exit 0), CRLF+BOM tolerance, pure parser module (no fs/process) with thin CLI wrapper, --help exit 0, and a test suite green via `node --test src/` covering R2/R5/R6/R8/R9 with in-memory strings plus CLI-wrapper end-to-end coverage.

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
