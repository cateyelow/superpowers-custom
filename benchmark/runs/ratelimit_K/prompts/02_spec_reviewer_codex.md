You are reviewing whether an implementation matches its specification.
There is no git repo here. Read the actual source files:
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/ratelimit_K/src/rateLimiter.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/ratelimit_K/src/rateLimiter.test.js
- /home/ubuntu/Github/superpowers-custom/benchmark/runs/ratelimit_K/src/package.json

## What Was Requested

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

## What Implementer Claims They Built

- src/rateLimiter.js: sliding-window rate limiter factory createRateLimiter({ limit, windowMs, now }) returning { check, reset, stats, _storeSize }.
  - Window (t - windowMs, t], trailing edge exclusive (expiry condition ts <= t - windowMs) — R3/R11.
  - retryAfterMs = oldest + windowMs - now when denied, 0 when allowed — R4.
  - All time reads go through injectable now (default Date.now); the only Date.now occurrence is the default-value position — R5.
  - Store is Map<key, timestamps[]>. Per-key prune on access + at most one amortized full sweep per windowMs evicts fully-expired keys — R8. Sweep runs only during API calls (no timers).
  - _storeSize(): introspection hook solely to prove R8 in tests; documented in a code comment as not part of the public rate-limiting contract. The spec's R8 explicitly sanctions "inspect store size or document the observable proxy used".
  - stats(key) = { used, remaining, oldestMs } without consuming quota. oldestMs interpreted as "age in ms of the oldest in-window request" (null when none) — documented assumption since spec doesn't define its meaning.
  - R9: RangeError at factory time for non-positive windowMs/limit, plus non-integer limit (blocks values like 0.5 that would produce remaining: -0.5).
- src/rateLimiter.test.js: describe blocks per requirement (R1/R2, R3, R4, R6, R7, R8, R9, R10, R11), all using a fake injected clock, zero sleeps/timers — R12.
- src/package.json = {"type":"module","main":"rateLimiter.test.js"}: required because on this host (Node v22.19.0) the test runner treats positional args as pure globs and spawns `src` as a single entry; without a resolvable main, `node --test src/` fails with MODULE_NOT_FOUND. The controller independently reproduced this: without the main field the acceptance command fails; with it, the full suite (19 tests) runs and passes. This file is an environment-mandated adaptation to satisfy the constraint "All tests green via node --test src/", not feature creep.
- Test results: node --test src/ → # tests 19, # pass 19, # fail 0.

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
