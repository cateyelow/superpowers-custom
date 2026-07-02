You are reviewing whether an implementation matches its specification.
There is no git repo here; review the ACTUAL source files in the current directory:
- src/rateLimiter.js (the module)
- src/rateLimiter.test.js (the tests)
- src/index.js (an entry shim the implementer added — judge it, see claims below)
- package.json (ESM marker)

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

- src/rateLimiter.js: factory createRateLimiter({limit, windowMs, now}); window (t-windowMs, t] with exclusive trailing edge (ts <= t-windowMs means expired); store is Map<key, number[]> of ascending timestamps (prototype-key safe); retryAfterMs = oldest + windowMs - t when denied, 0 when allowed; all time reads via injected clock, the string Date.now appears exactly once as the option default; memory hygiene via per-key prune-on-touch + a global sweep at most once per windowMs (lastSweepAt), observable through a documented NON-ENUMERABLE _storeSize() debug hook so the enumerable API surface stays exactly {check, reset, stats}; RangeError at factory time for non-positive/NaN limit or windowMs.
- src/rateLimiter.test.js: 10 suites / 19 tests, all driving time via a manually injected clock (no timers/sleeps); explicit tests for R3 (individual expiry), R4 (exact retryAfterMs countdown), R6 (key isolation), R7 (reset single key; repeated stats never consumes quota), R8 (500 one-off keys swept, _storeSize()===1), R9 (4 cases asserting err.constructor === RangeError), R10 (frozen-clock burst, limit+1 denied), R11 (allowed at exactly t=windowMs, denied at windowMs-1).
- package.json: {"type": "module"} only, no dependency declarations (needed so `node --test src/` treats .js as ESM; there was no package.json before).
- src/index.js: a one-line entry shim (import './rateLimiter.test.js') with an explanatory comment. Claimed justification, MEASURED on this box: on the installed default Node v22.19.0 (and v24), `node --test src/` treats `src` as a single entry path (post-Node-21 glob rewrite), so without the shim the MANDATED verification command fails with MODULE_NOT_FOUND regardless of code quality; with the shim `node src` resolves to index.js, registers the suite, and pass/fail propagates. On Node 20 the shim is ignored (does not match the *.test.js discovery pattern). The controller independently reproduced: without index.js the command exits 1; with it, exit 0 and 19/19 pass.
- Reported test result: `node --test src/` -> tests 19, pass 19, fail 0, exit 0 (node v22.19.0; also verified on v20.20.0 and v24.18.0).
- Interpretation note: stats().oldestMs is not defined by the spec; implementer chose "age in ms of the oldest in-window request, null when none" and documented it.

## CRITICAL: Do Not Trust the Report
The implementer's report may be incomplete, inaccurate, or optimistic. Verify EVERYTHING by reading the actual source files listed above. You may run `node --test src/` yourself from the current directory to verify.

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
- Judgment guidance: an artifact that exists ONLY to make the spec's own mandated verification command (`node --test src/`) pass on the installed Node version, is minimal, and is documented, should be judged on whether it is in fact minimal and necessary — verify the claim rather than reflexively listing it as extra.
