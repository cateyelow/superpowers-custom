You are implementing Task 1: CSV contact-import CLI

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

This is a greenfield, standalone deliverable — there is no existing codebase, framework, or app around it. The project root is `/home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_K` and ALL code goes in its `src/` subdirectory (currently empty). There is no package.json; do not create one unless required — plain `.js` files with ESM syntax must work, so if Node treats `.js` as CJS without a package.json, create a minimal `{ "type": "module" }` package.json in the project root (that is acceptable and expected for ESM). Node on this host is v22.19.0.

Architectural intent: `src/parser.js` holds ALL parsing/validation/normalization logic as pure functions (string in → data out, no fs, no process). `src/importCsv.js` is a thin CLI wrapper: argv handling, --help, reading the input file, calling the parser, printing errors/summary, atomic write, exit codes. `src/parser.test.js` tests the parser with in-memory strings; CLI-level behavior (atomic write, exit codes) may be tested with temp files/child processes where needed.

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
2. Write tests (follow TDD: write failing tests first, then implement)
3. Verify implementation works: run `node --test src/` from the project root and make sure every test passes
4. Do NOT commit and do NOT create git branches/worktrees — this directory is intentionally not under your git control; verification is via tests, not commits
5. Self-review (see below)
6. Report back

Work from: /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_K

**While you work:** If you encounter something unexpected or unclear, **ask questions**.
It's always OK to pause and clarify. Don't guess or make assumptions.

## Code Organization

You reason best about code you can hold in context at once, and your edits are more
reliable when files are focused. Keep this in mind:
- Follow the file structure defined in the plan (the three deliverable files above)
- Each file should have one clear responsibility with a well-defined interface
- If a file you're creating is growing beyond the plan's intent, stop and report
  it as DONE_WITH_CONCERNS — don't split files on your own without plan guidance
- If an existing file you're modifying is already large or tangled, work carefully
  and note it as a concern in your report
- In existing codebases, follow established patterns. Improve code you're touching
  the way a good developer would, but don't restructure things outside your task.

## When You're in Over Your Head

It is always OK to stop and say "this is too hard for me." Bad work is worse than
no work. You will not be penalized for escalating.

**STOP and escalate when:**
- The task requires architectural decisions with multiple valid approaches
- You need to understand code beyond what was provided and can't find clarity
- You feel uncertain about whether your approach is correct
- The task involves restructuring existing code in ways the plan didn't anticipate
- You've been reading file after file trying to understand the system without progress

**How to escalate:** Report back with status BLOCKED or NEEDS_CONTEXT. Describe
specifically what you're stuck on, what you've tried, and what kind of help you need.
The controller can provide more context, re-dispatch with a more capable model,
or break the task into smaller pieces.

## Before Reporting Back: Self-Review

Review your work with fresh eyes. Ask yourself:

**Completeness:**
- Did I fully implement everything in the spec?
- Did I miss any requirements?
- Are there edge cases I didn't handle?

**Quality:**
- Is this my best work?
- Are names clear and accurate (match what things do, not how they work)?
- Is the code clean and maintainable?

**Discipline:**
- Did I avoid overbuilding (YAGNI)?
- Did I only build what was requested?
- Did I follow existing patterns in the codebase?

**Testing:**
- Do tests actually verify behavior (not just mock behavior)?
- Did I follow TDD if required?
- Are tests comprehensive?

If you find issues during self-review, fix them now before reporting.

## Report Format

When done, report:
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What you implemented (or what you attempted, if blocked)
- What you tested and test results
- Files changed
- Self-review findings (if any)
- Any issues or concerns

Use DONE_WITH_CONCERNS if you completed the work but have doubts about correctness.
Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need
information that wasn't provided. Never silently produce work you're unsure about.
