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
