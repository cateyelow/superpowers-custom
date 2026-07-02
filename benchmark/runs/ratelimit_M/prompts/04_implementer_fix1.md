Codex code quality review returned NEEDS_FIXES on your Task 1 implementation. Fix the issue below, re-verify, and report back. (Spec compliance review was APPROVED — do not change API surface or semantics beyond what the fix requires.)

## Important issue (blocks approval — MUST fix)

- `src/rateLimiter.js:39-44` accepts fractional `limit` values even though `limit` is a request count; the check path then produces nonsensical API output: with `limit: 1.5`, two requests are allowed and the second allowed request returns `remaining: -0.5` (reviewer reproduced this live). Fix: validate `Number.isInteger(limit)` at factory time (RangeError, consistent with the existing R9 validation style and message quality) and add an explicit test that a fractional limit (e.g. 1.5) throws RangeError. Do NOT require windowMs to be an integer — fractional milliseconds are semantically valid time; only `limit` is a count.

## Minor issues (non-blocking — handle as noted)

- `src/rateLimiter.test.js:45-68` does not test `NaN` or `Infinity` for limit/windowMs despite the validation rejecting them. This is trivially adjacent to the fix above: ADD these cases to the RangeError validation test while you are there.
- `src/index.js` shim "misleading as a production package entry" — noted for later; do NOT change it. It exists solely so the mandated `node --test src/` command works on Node >= 21 and is documented as such; the spec reviewer approved it.
- Performance suggestions (head-index queue, non-copying sweep) — noted for later; do NOT implement (YAGNI, spec has no perf requirement).

## Definition of Done for this fix round

1. `createRateLimiter({ limit: 1.5, windowMs: 100 })` throws RangeError at factory time; test asserts it (err.constructor === RangeError, consistent with existing tests).
2. NaN and Infinity cases for both limit and windowMs are covered in the validation tests.
3. No other behavior changes; API surface stays exactly { check, reset, stats } (+ non-enumerable _storeSize).
4. `node --test src/` from /home/ubuntu/Github/superpowers-custom/benchmark/runs/ratelimit_M exits 0, all tests pass.
5. Still zero dependencies, ESM, no TypeScript, no git operations, nothing touched outside the working directory.

Report back with Status (DONE / DONE_WITH_CONCERNS / BLOCKED), what you changed (file:line), and the fresh `node --test src/` summary line.
