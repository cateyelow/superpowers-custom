You are implementing Task 1: CSV contact-import CLI (parser module + CLI wrapper + test suite)

## Task Description

Build a Node CLI (ESM, zero dependencies) that imports a contacts CSV into a normalized JSON file, with robust malformed-input handling, plus its test suite.

### Deliverables
- `src/importCsv.js` — CLI entry: `node src/importCsv.js <input.csv> <output.json>`
- `src/parser.js` — parsing/normalizing logic as a pure module (CLI is a thin wrapper)
- `src/parser.test.js` — tests runnable with `node --test`

### Requirements

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

### Constraints
- Node 20+, ESM, zero dependencies, no TypeScript.
- All tests green via `node --test src/`.

## Context

This is a greenfield, standalone deliverable. The working directory is /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M and ALL code goes into its `src/` subdirectory (currently empty). There is no package.json and you do not need one — but if Node requires one to treat `.js` files as ESM, create a minimal `src/package.json` with `{"type":"module"}` (that keeps the zero-dependency constraint; alternatively use a root package.json inside the base directory — your choice, but everything must stay inside /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M).

Architectural split mandated by the spec:
- `parser.js` is PURE: exported function(s) take the CSV content as a string and return `{ contacts, errors }` (errors carrying line number + reason). No fs, no process, no console.
- `importCsv.js` is the thin I/O shell: argv handling, `--help`, reading the input file, calling the parser, writing output atomically (temp file + rename in the same directory as the target so rename is atomic), printing the summary to stdout and per-row errors to stderr, and choosing the exit code.

Environment notes:
- Node v22 is installed. Run tests as `node --test src/` from the base directory.
- This directory is NOT a git repository and must not become one. Do NOT run any git commands, do NOT commit — the "commit your work" step of your normal process is replaced by simply leaving the files in place.
- Do not create files outside the base directory (except /tmp scratch if you need it).

## Acceptance Criteria (Definition of Done)

Each criterion must be verified by you before reporting:
1. `node --test src/` (cwd = base directory) exits 0 with all tests passing.
2. Tests explicitly cover, with in-memory strings: quoted field containing a comma AND a field with escaped `""` quotes (R2); a mixed valid/invalid file asserting the exact 1-based original line numbers in errors (R5, header = line 1, and the assertion must include a case where line numbering could drift, e.g. after an invalid or multi-field row); case-insensitive duplicate email rejected with reason `duplicate email` (R6); header-only input producing `{ contacts: [] }` and zero errors (R8); identical results for LF vs CRLF input and a BOM-prefixed header being accepted (R9).
3. At least one test exercises the CLI wrapper end-to-end (spawn `node src/importCsv.js` on a temp fixture) verifying: output JSON file content `{ contacts: [...] }` with trailing newline, stdout summary `imported <k>/<total> rows`, stderr `line <n>: <reason>` lines, and the exit code (0, 1, and 2 cases; 2 covered at least for missing input file or bad header). Temp fixtures go in a temp dir (`fs.mkdtemp` under `os.tmpdir()`), cleaned up after.
4. Manual smoke checks pass (run them yourself and confirm):
   - `--help` → usage on stdout, exit 0.
   - Missing args → usage/error, exit 2 (fatal usage error) — pick a sane behavior and document it in your report.
   - Header `email,name,phone` (reordered) works; header missing `phone` exits 2 naming `phone`.
   - A row `"Kim, Minsu",kim@x.com,010-1234-5678` imports with name `Kim, Minsu` and phone `01012345678`.
5. `parser.js` contains no `import` of `node:fs`/`node:process`/etc. and no `process.` or `console.` usage (R10).
6. Output file ends with exactly one trailing newline and is produced via temp-file-then-rename (R4).
7. No dependencies: no `node_modules`, no non-builtin imports.
8. There is no type-checker or linter configured for this project — state that explicitly in your report instead of claiming lint passes; your verification is the test suite plus the smoke checks above.

Design decisions you may make yourself (document them in the report): exact email regex (must reject clearly-invalid things like missing `@` or missing domain dot? — at minimum reject empty local part, missing `@`, spaces, missing domain; keep it simple and syntactic), behavior for rows with wrong field count (treat as invalid row with a clear reason, do not abort), whether extra whitespace around header names is tolerated (trimming header cells is fine), reason strings for invalid email/phone/name (short, human-readable, stable enough to test).

## Before You Begin

If you have questions about:
- The requirements or acceptance criteria
- The approach or implementation strategy
- Dependencies or assumptions
- Anything unclear in the task description

**Ask them now.** Raise any concerns before starting work.

## Your Job

Once you're clear on requirements:
1. Implement exactly what the task specifies
2. Write tests (following TDD: write failing tests first, then make them pass)
3. Verify implementation works (run `node --test src/` and the smoke checks)
4. Leave the files in place (NO git — see Context)
5. Self-review (see below)
6. Report back

Work from: /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M

**While you work:** If you encounter something unexpected or unclear, **ask questions**. It's always OK to pause and clarify. Don't guess or make assumptions.

## Code Organization

You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Keep this in mind:
- Follow the file structure defined in the plan (the three deliverable files, plus optionally a minimal package.json for ESM)
- Each file should have one clear responsibility with a well-defined interface
- If a file you're creating is growing beyond the plan's intent, stop and report it as DONE_WITH_CONCERNS — don't split files on your own without plan guidance
- In existing codebases, follow established patterns. This one is greenfield — keep it simple and idiomatic modern Node (node: prefixed builtin imports, const/let, no classes where functions do).

## When You're in Over Your Head

It is always OK to stop and say "this is too hard for me." Bad work is worse than no work. You will not be penalized for escalating.

**STOP and escalate when:**
- The task requires architectural decisions with multiple valid approaches
- You need to understand code beyond what was provided and can't find clarity
- You feel uncertain about whether your approach is correct
- You've been reading file after file trying to understand the system without progress

**How to escalate:** Report back with status BLOCKED or NEEDS_CONTEXT. Describe specifically what you're stuck on, what you've tried, and what kind of help you need.

## Before Reporting Back: Self-Review

Review your work with fresh eyes. Ask yourself:

**Completeness:**
- Did I fully implement everything in the spec (R1–R12)?
- Did I miss any requirements?
- Are there edge cases I didn't handle (quoted field at end of line, empty file with no header at all, quote inside unquoted field, trailing CRLF on last line, blank lines)?

**Quality:**
- Is this my best work?
- Are names clear and accurate (match what things do, not how they work)?
- Is the code clean and maintainable?

**Discipline:**
- Did I avoid overbuilding (YAGNI)? No flags/features beyond the spec.
- Did I only build what was requested?

**Testing:**
- Do tests actually verify behavior (not just mock behavior)?
- Did I follow TDD?
- Are tests comprehensive for R2, R5, R6, R8, R9 plus the CLI wrapper?

If you find issues during self-review, fix them now before reporting.

## Report Format

When done, report:
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What you implemented (or what you attempted, if blocked)
- What you tested and test results (paste the `node --test src/` tail: pass/fail counts)
- Files changed (absolute paths)
- Documented design decisions (email regex choice, wrong-field-count behavior, reason strings, missing-args behavior)
- Self-review findings (if any)
- Any issues or concerns

Use DONE_WITH_CONCERNS if you completed the work but have doubts about correctness. Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need information that wasn't provided. Never silently produce work you're unsure about.
