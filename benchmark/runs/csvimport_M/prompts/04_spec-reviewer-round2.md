You are re-reviewing whether an implementation matches its specification (ROUND 2 — a previous review found one issue, which has since been fixed).
This project is NOT a git repository, so there is no diff. The implementation is entirely new code. Read the actual source files:
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/parser.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/importCsv.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/parser.test.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M/src/package.json
You may also run the tests: cd /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M && node --test src/

## Previous Review Finding (now claimed fixed — VERIFY the fix)

Round 1 returned NEEDS_FIXES: "R1 exact header set is not enforced; headers with extra columns are accepted." The fix mandate was: a header containing any column outside {name,email,phone} is fatal (CLI exit 2, message naming the unexpected column(s)); duplicated required column names are also fatal; missing-column behavior, any-order, trimming, and BOM tolerance retained; parser stays pure and signals via HeaderError; tests added for extra-column header (parser-level and CLI-level exit 2) and duplicate-column header.

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

## What Implementer Claims They Built (after the fix)

Same implementation as round 1 (pure parser with hand-rolled tokenizer tracking original line numbers, thin CLI wrapper with atomic temp+rename write, HeaderError for fatal header conditions, src/package.json {"type":"module","main":"parser.test.js"} as documented workaround so the literal command `node --test src/` works on this Node v22.19.0 build), PLUS the R1 fix: header validation now enforces the exact set {name,email,phone} — unexpected column(s) and duplicate column(s) are fatal HeaderError conditions (messages "unexpected column(s): <names>", "duplicate column(s): <names>", combinable with "missing required column(s): <names>"), CLI exits 2. New tests: parser-level extra column, parser-level duplicate column, parser-level combined missing+unexpected, CLI-level extra column exits 2 naming the column. Test suite now 28 tests / 8 suites, all passing, exit 0.

## CRITICAL: Do Not Trust the Report
The implementer's report may be incomplete, inaccurate, or optimistic. Verify EVERYTHING by reading the actual source files.

DO NOT take their word. DO read the code.

## Check For

1. Missing requirements — anything in spec that's not in the code? (Verify the round-1 R1 fix actually works.)
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
