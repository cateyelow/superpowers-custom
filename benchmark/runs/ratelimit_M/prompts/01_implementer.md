You are implementing Task 1: sliding-window rate limiter module

## Task Description

Build a standalone JavaScript module (Node, no dependencies, ESM) implementing a sliding-window rate limiter, plus its test suite.

### Deliverables
- `src/rateLimiter.js` — the module
- `src/rateLimiter.test.js` — tests runnable with `node --test`

### Requirements

R1. Export a factory `createRateLimiter({ limit, windowMs, now })` returning `{ check(key), reset(key), stats(key) }`.
R2. `check(key)` returns `{ allowed: boolean, remaining: number, retryAfterMs: number }` — never throws for string keys.
R3. Sliding window semantics (NOT fixed buckets): a request at t is counted against the window (t-windowMs, t]. Requests expire individually as the window slides.
R4. `retryAfterMs` must be the exact ms until the OLDEST in-window request expires (0 when allowed).
R5. The `now` option is an injectable clock function defaulting to `Date.now`; ALL time reads go through it (no direct Date.now anywhere else).
R6. Keys are isolated: traffic on key A never affects key B's remaining count.
R7. `reset(key)` clears only that key; `stats(key)` returns `{ used, remaining, oldestMs }` without consuming quota.
R8. Memory hygiene: entries for a key whose requests have ALL expired are removed from the internal store (no unbounded growth across many one-off keys). Prove it in a test (inspect store size or document the observable proxy used).
R9. Input validation: non-positive `limit` or `windowMs` throws a `RangeError` at factory time (not at check time).
R10. Burst edge: exactly `limit` requests at the same timestamp are all allowed; request `limit+1` at that timestamp is denied.
R11. Window boundary edge: a request made exactly `windowMs` after the first one must be allowed when the first has just expired (boundary is exclusive at the trailing edge — test t=0 filled to limit, then t=windowMs).
R12. Tests must use the injected clock (no sleeps, no real timers) and cover R3, R4, R6, R8, R9, R10, R11 explicitly.

### Constraints
- Node 20+, ESM, zero dependencies, no TypeScript.
- All tests green via `node --test src/`.

## Context

This is a standalone greenfield module — there is no surrounding application, no framework, no existing code to integrate with. The two deliverable files are the entire codebase. The environment has Node v22 installed. The directory `src/` already exists (empty) at the working directory below.

ESM note: there is no package.json in the working directory, so use the `.js` extension with ESM syntax — you must create a minimal `package.json` containing `{"type": "module"}` in the working directory so that `node --test src/` treats `.js` files as ESM. That package.json must declare zero dependencies (no `dependencies`, no `devDependencies`).

Environment adaptations (override the generic instructions below where they conflict):
- Do NOT create git worktrees or branches, and do NOT commit — this directory sits inside an unrelated repo and isolation is already provided. Skip the "commit your work" step entirely.
- There is no type-checker or linter configured for this project (plain JS, zero deps). Your verification command is `node --test src/` run from the working directory — all tests must pass.
- Do not touch anything outside the working directory (except /tmp scratch).

## Acceptance Criteria (Definition of Done)

Each criterion must be verified by you before reporting DONE:

1. `src/rateLimiter.js` exists, is ESM, has zero imports of any dependency, and exports `createRateLimiter`.
2. `createRateLimiter({ limit, windowMs, now })` returns an object with exactly the methods `check`, `reset`, `stats` (R1).
3. `check(key)` returns `{ allowed, remaining, retryAfterMs }` with correct types and never throws for any string key, including keys like `"__proto__"`, `"constructor"`, and `""` (R2). Use a `Map` (not a plain object) for the store to make prototype-key safety structural.
4. Sliding-window semantics verified by a test: fill some requests at varied timestamps, advance the injected clock, and observe requests expiring INDIVIDUALLY (not all at once at a bucket boundary) (R3, R12).
5. A test asserts `retryAfterMs` equals the exact ms until the oldest in-window request leaves the window when denied, and equals 0 when allowed (R4, R12).
6. `now` defaults to `Date.now`; grep-level check: the string `Date.now` appears only as the default value of the `now` option, nowhere else in the module (R5).
7. A test proves key isolation: exhausting key A leaves key B's `remaining` untouched (R6, R12).
8. Tests prove `reset(key)` clears only that key, and `stats(key)` returns `{ used, remaining, oldestMs }` and does not consume quota (calling `stats` repeatedly never changes `remaining`) (R7).
9. Memory hygiene test: after many one-off keys' requests all expire (advance injected clock past windowMs, then trigger whatever sweep mechanism the module uses), the internal store no longer holds those keys. Expose a deliberate, documented observable for this (e.g. a `size()` or `_storeSize` accessor, or a documented non-enumerable debug hook) and use it in the test; document the choice in a comment (R8, R12).
10. `createRateLimiter({ limit: 0, ... })`, negative limit, `windowMs: 0`, negative windowMs each throw `RangeError` at factory call time — tests assert the error type is exactly RangeError (R9, R12).
11. Burst test: with the clock frozen at one timestamp, exactly `limit` checks are allowed and check number `limit+1` is denied (R10, R12).
12. Boundary test: at t=0 fill to limit; at t=windowMs exactly, a new check is ALLOWED because the t=0 requests have just expired (trailing edge exclusive — window is (t-windowMs, t]) (R11, R12).
13. No test uses `setTimeout`, sleeps, or real timers; every test drives time via the injected `now` function (R12).
14. `node --test src/` (run from the working directory) exits 0 with all tests passing.

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
2. Write tests (following TDD: write failing tests first, then implement)
3. Verify implementation works (`node --test src/` from the working directory)
4. Self-review (see below)
5. Report back

Work from: /home/ubuntu/Github/superpowers-custom/benchmark/runs/ratelimit_M

**While you work:** If you encounter something unexpected or unclear, **ask questions**.
It's always OK to pause and clarify. Don't guess or make assumptions.

## Code Organization

You reason best about code you can hold in context at once, and your edits are more
reliable when files are focused. Keep this in mind:
- Follow the file structure defined in the plan: exactly `src/rateLimiter.js` and `src/rateLimiter.test.js` (plus the minimal root `package.json` for ESM).
- Each file should have one clear responsibility with a well-defined interface
- If a file you're creating is growing beyond the plan's intent, stop and report
  it as DONE_WITH_CONCERNS — don't split files on your own without plan guidance
- This is greenfield; there are no existing patterns to follow. Keep it simple — YAGNI.

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
The controller can provide more context or a fuller spec, break the task into
smaller pieces, or (for genuinely ambiguous architectural work) escalate the model.

## Before Reporting Back: Self-Review

Review your work with fresh eyes. Ask yourself:

**Completeness:**
- Did I fully implement everything in the spec? All of R1–R12?
- Did I miss any requirements?
- Are there edge cases I didn't handle?

**Quality:**
- Is this my best work?
- Are names clear and accurate (match what things do, not how they work)?
- Is the code clean and maintainable?

**Discipline:**
- Did I avoid overbuilding (YAGNI)?
- Did I only build what was requested?

**Testing:**
- Do tests actually verify behavior (not just mock behavior)?
- Did I follow TDD?
- Are tests comprehensive — does every requirement R3, R4, R6, R8, R9, R10, R11 have an explicit test?

If you find issues during self-review, fix them now before reporting.

## Report Format

When done, report:
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What you implemented (or what you attempted, if blocked)
- What you tested and test results (paste the `node --test src/` summary line)
- Files changed
- Self-review findings (if any)
- Any issues or concerns

Use DONE_WITH_CONCERNS if you completed the work but have doubts about correctness.
Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need
information that wasn't provided. Never silently produce work you're unsure about.
