You are implementing Task 1: sliding-window rate limiter module

## Task Description

# Task: sliding-window rate limiter module

Build a standalone JavaScript module (Node, no dependencies, ESM) implementing a sliding-window rate limiter, plus its test suite.

## Deliverables
- `src/rateLimiter.js` — the module
- `src/rateLimiter.test.js` — tests runnable with `node --test`

## Requirements

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

## Constraints
- Node 20+, ESM, zero dependencies, no TypeScript.
- All tests green via `node --test src/`.

## Context

This is a standalone greenfield module — there is no surrounding application, no existing codebase patterns to follow, and no other tasks. The two deliverable files are the entire project. The host runs Node v22.19.0, so `node --test` is available natively. The project directory has no package.json; since the module must be ESM, use `.js` files with ESM syntax AND create a minimal `src/../package.json`? — NO: do NOT create a package.json at the project root unless `node --test src/` fails to treat the files as ESM. Preferred approach: name the files exactly `src/rateLimiter.js` and `src/rateLimiter.test.js` as the spec requires, and add a minimal `{ "type": "module" }` package.json at the project root ONLY if Node refuses to parse the ESM syntax without it (Node treats `.js` as CJS by default outside a `"type": "module"` package, so you will almost certainly need it — a root package.json with only `{ "type": "module" }` is acceptable and counts as zero dependencies).

For R8 (memory hygiene proof), the recommended observable proxy is to expose the internal store size in a way tests can inspect — e.g., a non-spec extra is NOT allowed by the spec reviewer, so prefer proving it through `stats(key)` semantics if possible; if that is not sufficient to genuinely prove store cleanup, expose a clearly-documented introspection hook (e.g., a `_storeSize()` or exported symbol) and document in a code comment that it exists solely to satisfy R8's testability requirement. Keep it minimal and documented — the spec explicitly says "inspect store size or document the observable proxy used", so a documented introspection hook is spec-sanctioned, not extra work.

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
2. Write tests (following TDD: write tests first, watch them fail, then implement)
3. Verify implementation works: run `node --test src/` from the project root and ensure ALL tests pass
4. Do NOT use git in any way — no init, no commit, no branches. This environment provides isolation already; just leave the files in place.
5. Self-review (see below)
6. Report back

Work from: /home/ubuntu/Github/superpowers-custom/benchmark/runs/ratelimit_K

**While you work:** If you encounter something unexpected or unclear, **ask questions**.
It's always OK to pause and clarify. Don't guess or make assumptions.

## Code Organization

You reason best about code you can hold in context at once, and your edits are more
reliable when files are focused. Keep this in mind:
- Follow the file structure defined in the plan: exactly `src/rateLimiter.js` and `src/rateLimiter.test.js` (plus at most a root `package.json` containing only `{ "type": "module" }` if ESM requires it)
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
- Did I fully implement everything in the spec? (Walk R1 through R12 one by one.)
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
- Did I actually RUN `node --test src/` and see every test pass? Paste the summary line.

If you find issues during self-review, fix them now before reporting.

## Report Format

When done, report:
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What you implemented (or what you attempted, if blocked)
- What you tested and test results (include the `node --test src/` summary output)
- Files changed
- Self-review findings (if any)
- Any issues or concerns

Use DONE_WITH_CONCERNS if you completed the work but have doubts about correctness.
Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need
information that wasn't provided. Never silently produce work you're unsure about.
