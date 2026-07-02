You are reviewing whether an implementation matches its specification.
There is no git repo here. Read the actual source files in /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_K:
- src/parser.js
- src/importCsv.js
- src/parser.test.js
- src/index.js
- package.json

## What Was Requested

Task: CSV contact-import CLI

Build a Node CLI (ESM, zero dependencies) that imports a contacts CSV into a normalized JSON file, with robust malformed-input handling, plus its test suite.

Deliverables:
- src/importCsv.js — CLI entry: node src/importCsv.js <input.csv> <output.json>
- src/parser.js — parsing/normalizing logic as a pure module (CLI is a thin wrapper)
- src/parser.test.js — tests runnable with node --test

Requirements:
R1. Expected header: name,email,phone (exact set, any order). A file whose header is missing a required column exits with code 2 and a message naming the missing column(s).
R2. CSV parsing must handle quoted fields containing commas and escaped quotes ("") — a hand-rolled split(',') that breaks on "Kim, Minsu" fails this.
R3. Rows are validated: email must be syntactically valid; phone is normalized to digits-only (strip spaces, dashes, parentheses); name must be non-empty after trimming.
R4. Valid rows are written to <output.json> as { contacts: [{ name, email, phone }] } with a trailing newline; the file is written atomically (write temp file then rename) so a crash never leaves a half-written output.
R5. Invalid rows do NOT abort the run: they are collected and reported to stderr as `line <n>: <reason>` (n = 1-based line number in the ORIGINAL file, counting the header as line 1).
R6. Duplicate emails (case-insensitive) after the first occurrence are rejected as invalid rows with reason `duplicate email`.
R7. Exit codes: 0 = all rows imported; 1 = completed but some rows rejected; 2 = fatal (unreadable input, bad header, unwritable output). Stdout gets a one-line summary `imported <k>/<total> rows` in ALL non-fatal cases.
R8. Empty data file (header only) is NOT an error: writes { contacts: [] }, prints `imported 0/0 rows`, exits 0.
R9. CRLF and LF line endings both work; a UTF-8 BOM on the header line is tolerated.
R10. The parser module never touches the filesystem or process.exit (pure: string in → { contacts, errors } out); only the CLI wrapper does I/O and exit codes.
R11. Tests cover R2 (quoted comma + escaped quote), R5 (line numbers correct with a mix of valid/invalid), R6, R8, and R9 explicitly, using in-memory strings (no fixture files needed except where testing the CLI wrapper's atomic write).
R12. --help prints usage and exits 0.

Constraints:
- Node 20+, ESM, zero dependencies, no TypeScript.
- All tests green via `node --test src/`.

## What Implementer Claims They Built

- src/parser.js — pure parsing module. RFC 4180-style character-level tokenizer (commas inside quotes, "" escapes, newlines inside quoted fields), BOM strip, LF/CRLF/lone-CR handling, per-record original 1-based line number tracking. Header validation (throws HeaderError naming missing columns), row validation (name trimmed non-empty / email regex / phone strips spaces-dashes-parens then digits-only / case-insensitive duplicate email → reason `duplicate email`). No fs/process access (R10).
- src/importCsv.js — thin CLI wrapper: --help (exit 0), arg validation, file read, `line <n>: <reason>` to stderr, `imported <k>/<total> rows` to stdout, temp-file+rename atomic write (temp cleaned up on failure), exit codes 0/1/2.
- src/parser.test.js — 32 tests: R2 (quoted comma, escaped quotes, line numbers after quoted newline), R5 (original line numbers with valid/invalid mix), R6 (case-insensitive duplicates; rejected rows don't claim an email), R8, R9 (CRLF, BOM, BOM+CRLF) plus header/validation/field-count cases. CLI tested via temp dir + child processes: exit codes, summary, trailing newline, atomic write (no temp leftovers).
- package.json — minimal { "type": "module" } (allowed/expected by the task for ESM).
- src/index.js — a 6-line shim NOT in the deliverables list, added because on Node v22 `node --test src/` does NOT scan the directory: it executes `src` as a single test entry, which resolves to src/index.js. Without the shim the constraint command runs 0 tests (MODULE_NOT_FOUND-style failure). The shim imports the test suite so `node --test src/` runs all 32 tests. The controller independently verified this: with the shim `node --test src/` = 32 pass / exit 0; without it = 0 pass / 1 fail. Treat the shim as justified by the constraint "All tests green via node --test src/" unless you find a better zero-dependency alternative that keeps the exact command working.
- Test run: node --test src/ → 32 pass / 0 fail, exit 0 (Node v22.19.0).
- Decisions where spec was silent: unknown or duplicated header columns are fatal (exit 2, naming columns); phone with leftover non-digits (e.g. `+`) → `invalid phone`; fully empty lines are silently skipped, line numbers stay physical; one reason reported per invalid row (name → email → phone → duplicate order); rejected rows do not reserve an email for duplicate detection; JSON is 2-space pretty-printed + trailing newline.

## CRITICAL: Do Not Trust the Report
The implementer's report may be incomplete, inaccurate, or optimistic. Verify EVERYTHING by reading the actual source files.

DO NOT take their word. DO read the code changes. You may also run the tests (`cd /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_K && node --test src/`) and exercise the CLI to verify behavior.

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
