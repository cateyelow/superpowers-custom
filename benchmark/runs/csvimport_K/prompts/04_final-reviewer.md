You are the FINAL reviewer for an entire completed implementation. Two earlier Codex reviews (per-task spec compliance, per-task code quality) both returned APPROVED. Your job now is a holistic final pass over the whole deliverable as it will be shipped: verify the complete implementation against the complete original specification, and check overall coherence, correctness, and test health end-to-end.

There is no git repo here. Read ALL the actual files in /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_K:
- src/parser.js
- src/importCsv.js
- src/parser.test.js
- src/index.js
- package.json

You may (and should) run the test suite and exercise the CLI to verify real behavior:
- cd /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_K && node --test src/
- node src/importCsv.js --help ; and real CSV inputs of your choosing against a temp dir

## The Complete Original Specification

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

## Known, already-adjudicated context (do not re-litigate unless you find it actually broken)
- src/index.js is a 6-line shim added because on Node v22 `node --test src/` executes `src` as a single entry (resolving to index.js) instead of scanning the directory; without it the mandated command runs 0 tests. It was accepted by both prior reviews as justified by the constraint.
- package.json is { "type": "module" } only, accepted as required for ESM .js files.
- Prior quality review noted 3 minor (non-blocking) issues: quoted lone-CR not counted as a physical line break for line numbering; duplicate header columns reported as "unexpected" rather than a distinct duplicate diagnostic; the index.js shim being awkward as production file organization. Minor issues do not block, but flag them again if you judge any of them actually critical/important.

## Check For
1. Any requirement (R1–R12) or constraint not fully satisfied end-to-end in the real, running artifact.
2. Cross-cutting defects a per-task review could miss: inconsistencies between modules, CLI/parser contract mismatches, test suite gaps against the spec's explicit coverage list.
3. Anything that would make a perfectionist reviewer reject the deliverable as shipped.

## Required Output Format (MUST follow exactly)

status: APPROVED | NEEDS_FIXES | BLOCKED_ERROR
requirements_check: [one line per R1..R12 and each constraint: PASS or FAIL with evidence]
critical_issues: [list, or "none"]
important_issues: [list, or "none"]
minor_issues: [list, or "none"]

## Status Determination Rule (MUST follow exactly)
- APPROVED: ONLY when critical_issues is "none" AND important_issues is "none" AND every requirements_check line is PASS
- NEEDS_FIXES: when critical_issues OR important_issues has any entries, or any requirements_check line is FAIL
- BLOCKED_ERROR: when you cannot complete the review for technical reasons
