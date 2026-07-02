Review the code quality of the changes. There is no git repo here — read the actual source files in /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_K:
- src/parser.js
- src/importCsv.js
- src/parser.test.js
- src/index.js
- package.json

## What Was Implemented

- src/parser.js — pure parsing module. RFC 4180-style character-level CSV tokenizer (commas inside quotes, "" escapes, newlines inside quoted fields), BOM strip, LF/CRLF/lone-CR handling, per-record original 1-based line numbers. Header validation (throws HeaderError naming missing/unknown/duplicate columns), row validation (name trimmed non-empty / email regex / phone normalized by stripping spaces-dashes-parens, must be digits-only / case-insensitive duplicate email → `duplicate email`). No fs or process access.
- src/importCsv.js — thin CLI wrapper: --help (exit 0), arg validation, file read, `line <n>: <reason>` lines to stderr, `imported <k>/<total> rows` summary to stdout, atomic write via temp file + rename (temp cleaned on failure), exit codes 0 (all imported) / 1 (some rejected) / 2 (fatal: unreadable input, bad header, unwritable output).
- src/parser.test.js — 32 tests via node:test: parser tested with in-memory strings (quoting, escapes, line numbers, duplicates, header errors, BOM/CRLF, empty file), CLI tested end-to-end with child processes + temp dirs (exit codes, summary line, trailing newline, atomic write leftovers).
- src/index.js — 6-line shim so the exact constraint command `node --test src/` works on Node v22 (which executes `src` as a single entry resolving to index.js instead of scanning the dir). Verified: with shim 32 pass / exit 0, without shim 0 tests run.
- package.json — { "type": "module" } only.

Test status: `node --test src/` → 32 pass / 0 fail, exit 0 (Node v22.19.0).

## Task Context

Greenfield, standalone benchmark deliverable: a zero-dependency Node 20+ ESM CLI that imports a contacts CSV (header name,email,phone in any order) into `{ contacts: [...] }` JSON, collecting per-line validation errors to stderr without aborting, with exit codes 0/1/2 and atomic output writes. Spec compliance was already reviewed and APPROVED in a prior Codex review — this review is about whether the implementation is WELL-BUILT, not whether it matches the spec.

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
