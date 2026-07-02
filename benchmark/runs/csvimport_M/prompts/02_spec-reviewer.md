You are reviewing whether an implementation matches its specification.
This project is NOT a git repository, so there is no diff. The implementation is entirely new code. Read the actual source files:
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/parser.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/importCsv.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/parser.test.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/package.json
You may also run the tests: cd /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M && node --test src/

## What Was Requested

# Task: CSV contact-import CLI

Build a Node CLI (ESM, zero dependencies) that imports a contacts CSV into a normalized JSON file, with robust malformed-input handling, plus its test suite.

## Deliverables
- `src/importCsv.js` — CLI entry: `node src/importCsv.js <input.csv> <output.json>`
- `src/parser.js` — parsing/normalizing logic as a pure module (CLI is a thin wrapper)
- `src/parser.test.js` — tests runnable with `node --test`

## Requirements

R1. Expected header: `name,email,phone` (exact set, any order). A file whose header is missing a required column exits with code 2 and a message naming the missing column(s).
R2. CSV parsing must handle quoted fields containing commas and escaped quotes (`""`) — a hand-rolled split(',') that breaks on `"Kim, Minsu"` fails this.
R3. Rows are validated: email must be syntactically valid; phone is normalized to digits-only (strip spaces, dashes, parentheses); name must be non-empty after trimming.
R4. Valid rows are written to `<output.json>` as `{ contacts: [{ name, email, phone }] }` with a trailing newline; the file is written atomically (write temp file then rename) so a crash never leaves a half-written output.
R5. Invalid rows do NOT abort the run: they are collected and reported to stderr as `line <n>: <reason>` (n = 1-based line number in the ORIGINAL file, counting the header as line 1).
R6. Duplicate emails (case-insensitive) after the first occurrence are rejected as invalid rows with reason `duplicate email`.
R7. Exit codes: 0 = all rows imported; 1 = completed but some rows rejected; 2 = fatal (unreadable input, bad header, unwritable output). Stdout gets a one-line summary `imported <k>/<total> rows` in ALL non-fatal cases.
R8. Empty data file (header only) is NOT an error: writes `{ contacts: [] }`, prints `imported 0/0 rows`, exits 0.
R9. CRLF and LF line endings both work; a UTF-8 BOM on the header line is tolerated.
R10. The parser module never touches the filesystem or process.exit (pure: string in → { contacts, errors } out); only the CLI wrapper does I/O and exit codes.
R11. Tests cover R2 (quoted comma + escaped quote), R5 (line numbers correct with a mix of valid/invalid), R6, R8, and R9 explicitly, using in-memory strings (no fixture files needed except where testing the CLI wrapper's atomic write).
R12. `--help` prints usage and exits 0.

## Constraints
- Node 20+, ESM, zero dependencies, no TypeScript.
- All tests green via `node --test src/`.

## What Implementer Claims They Built

- src/parser.js — pure module, parseCsv(content) -> { contacts, errors }, plus exported HeaderError class for the one fatal condition a pure function can still signal (throwing, not I/O). Hand-rolled character-level CSV tokenizer (not split(',')) that tracks real line numbers through quoted fields/escaped quotes/CRLF so R2 and R5 hold together correctly.
- src/importCsv.js — thin CLI shell: --help/-h, arg-count check, reads input, calls the parser, atomic temp-file+rename write, prints summary/per-row errors, sets exit code.
- src/parser.test.js — 24 tests across 8 suites, all in-memory strings except the CLI end-to-end suite (uses fs.mkdtemp/os.tmpdir(), cleaned up via before/after).
- src/package.json — {"type":"module","main":"parser.test.js"}. The "main" pointing at the test file is a documented workaround: on this Node v22.19.0 build, `node --test src/` with a bare directory argument resolves the directory via CJS directory-module resolution (package.json main / index.js) instead of scanning for test files; setting main to the test file makes the literal required command `node --test src/` work (verified: 24/24 pass, exit 0).
- Test results: node --test src/ from the base directory: 24 tests, 24 pass, 0 fail, exit code 0.
- Design decisions (documented): email regex /^[^\s@]+@[^\s@]+\.[^\s@]+$/; phone strips only [\s\-()] then requires /^\d+$/ (leading + rejected as invalid phone); wrong field count -> invalid row "wrong field count (expected N, got M)", blank lines fall under this; per-row check order: empty name -> invalid email -> duplicate email -> invalid phone; header check requires all three columns present (trimmed, case-sensitive, any order), extra columns tolerated and ignored; missing/wrong argc -> usage to stderr, exit 2; completely empty (0-byte) input -> header error naming all three columns; atomic write via .<basename>.tmp-<pid>-<timestamp> in same dir + rename, temp unlinked on failure.

## CRITICAL: Do Not Trust the Report
The implementer's report may be incomplete, inaccurate, or optimistic. Verify EVERYTHING by reading the actual source files.

DO NOT take their word. DO read the code.

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
