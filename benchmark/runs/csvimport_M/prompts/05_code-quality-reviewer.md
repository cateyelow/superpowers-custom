Review the code quality of the changes. This project is NOT a git repository, so there is no diff — the implementation is entirely new code (greenfield). Read the actual source files:
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/parser.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/importCsv.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/parser.test.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/package.json
You may also run the tests: cd /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M && node --test src/

## What Was Implemented

- src/parser.js — pure module: parseCsv(content) -> { contacts, errors }; exported HeaderError class thrown for fatal header conditions (missing / unexpected / duplicate columns, messages combinable). Hand-rolled character-level CSV tokenizer (quoted fields, escaped "" quotes, CRLF/LF, BOM) that tracks original 1-based line numbers through multi-line quoted fields. Row validation: wrong field count, empty name, syntactic email check (/^[^\s@]+@[^\s@]+\.[^\s@]+$/), case-insensitive duplicate email ("duplicate email"), phone normalized by stripping [\s\-()] then required to be all digits.
- src/importCsv.js — thin CLI wrapper: --help/-h (stdout, exit 0), argc check (usage to stderr, exit 2), reads input (unreadable -> exit 2), calls parser (HeaderError -> exit 2), writes { contacts } JSON + trailing newline atomically (temp file in same dir + rename, temp unlinked on failure; unwritable -> exit 2), prints per-row errors to stderr as "line <n>: <reason>", prints "imported <k>/<total> rows" to stdout, exit 0 if no rejected rows else 1.
- src/parser.test.js — 28 tests / 8 suites: parser-level in-memory-string tests for quoted commas + escaped quotes, line-number correctness with mixed valid/invalid rows, duplicate email, header-only file, LF vs CRLF equivalence, BOM tolerance, exact-header-set enforcement (missing/unexpected/duplicate columns), plus a CLI end-to-end suite (spawns node src/importCsv.js on mkdtemp fixtures; exit 0/1/2 cases, JSON output shape + trailing newline, stdout summary, stderr lines, no stray temp files).
- src/package.json — {"type":"module","main":"parser.test.js"}. The "main" pointing at the test file is a documented workaround: on this host's Node v22.19.0, `node --test src/` with a bare directory argument resolves the directory as a CJS module (package.json main / index.js) instead of scanning for test files; the constraint requires that literal command to work.

Test status: node --test src/ -> 28/28 pass, exit 0.

## Task Context

Standalone zero-dependency Node 20+ ESM CLI that imports a contacts CSV (header name,email,phone in any order, exact set) into { contacts: [...] } JSON with atomic write; invalid rows are reported to stderr with original line numbers without aborting; exit codes 0/1/2. The spec mandates the parser be pure (no fs/process/console) and the CLI be a thin wrapper. Tests must run via `node --test src/`. This is the entire project — one task, greenfield; this is both the per-task and the final whole-implementation quality review.

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
