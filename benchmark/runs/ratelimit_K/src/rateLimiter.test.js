import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { createRateLimiter } from './rateLimiter.js';

/**
 * All tests drive time exclusively through the injected `now` clock (R5, R12):
 * no sleeps, no real timers. `makeClock` returns a controllable fake clock.
 *
 * Note on src/package.json: it exists so the acceptance command
 * `node --test src/` works on Node versions (e.g. v22.19.0) whose test
 * runner treats positional args as pure glob patterns and spawns the
 * matched `src` directory as a single entry instead of searching it for
 * test files. Its "main" points at this test file so that entry runs the
 * suite, and its "type": "module" marks both src files as ESM.
 */
function makeClock(start = 0) {
  let t = start;
  const now = () => t;
  now.set = (v) => { t = v; };
  now.advance = (ms) => { t += ms; };
  return now;
}

describe('R9: input validation at factory time', () => {
  test('non-positive limit throws RangeError', () => {
    assert.throws(() => createRateLimiter({ limit: 0, windowMs: 1000 }), RangeError);
    assert.throws(() => createRateLimiter({ limit: -1, windowMs: 1000 }), RangeError);
  });

  test('non-integer limit throws RangeError (a fractional quota is meaningless)', () => {
    assert.throws(() => createRateLimiter({ limit: 0.5, windowMs: 1000 }), RangeError);
  });

  test('non-positive windowMs throws RangeError', () => {
    assert.throws(() => createRateLimiter({ limit: 5, windowMs: 0 }), RangeError);
    assert.throws(() => createRateLimiter({ limit: 5, windowMs: -100 }), RangeError);
  });

  test('valid options do not throw, and check() never throws afterwards', () => {
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: makeClock() });
    // R2: check never throws for string keys, including exotic ones.
    for (const key of ['a', '', '__proto__', 'constructor', 'toString', '한국어 키']) {
      assert.doesNotThrow(() => limiter.check(key));
    }
  });
});

describe('R1/R2: factory shape and check() result shape', () => {
  test('factory returns { check, reset, stats }', () => {
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: makeClock() });
    assert.equal(typeof limiter.check, 'function');
    assert.equal(typeof limiter.reset, 'function');
    assert.equal(typeof limiter.stats, 'function');
  });

  test('check() returns { allowed, remaining, retryAfterMs } with correct types', () => {
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: makeClock() });
    const res = limiter.check('k');
    assert.deepEqual(res, { allowed: true, remaining: 1, retryAfterMs: 0 });
  });

  test('now defaults to Date.now (smoke test, single call, no timers)', () => {
    const limiter = createRateLimiter({ limit: 1, windowMs: 60_000 });
    assert.equal(limiter.check('k').allowed, true);
  });
});

describe('R10: burst edge at a single timestamp', () => {
  test('exactly `limit` requests at the same timestamp are allowed; limit+1 is denied', () => {
    const clock = makeClock(1000);
    const limiter = createRateLimiter({ limit: 3, windowMs: 100, now: clock });

    assert.deepEqual(limiter.check('k'), { allowed: true, remaining: 2, retryAfterMs: 0 });
    assert.deepEqual(limiter.check('k'), { allowed: true, remaining: 1, retryAfterMs: 0 });
    assert.deepEqual(limiter.check('k'), { allowed: true, remaining: 0, retryAfterMs: 0 });

    // limit+1-th request at the very same timestamp: denied, expires in windowMs.
    assert.deepEqual(limiter.check('k'), { allowed: false, remaining: 0, retryAfterMs: 100 });
  });
});

describe('R3: sliding-window semantics (individual expiry, not fixed buckets)', () => {
  test('requests expire individually as the window slides', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: clock });

    clock.set(0);
    assert.equal(limiter.check('k').allowed, true); // request @0
    clock.set(50);
    assert.equal(limiter.check('k').allowed, true); // request @50
    clock.set(60);
    assert.equal(limiter.check('k').allowed, false); // both in window

    // @120: request @0 has expired (0 <= 120-100) but @50 has not (50 > 20).
    clock.set(120);
    const res = limiter.check('k');
    assert.equal(res.allowed, true); // exactly one slot freed
    assert.equal(res.remaining, 0);  // @50 and @120 now occupy the window

    // A fixed-bucket implementation would have reset BOTH at the bucket edge;
    // sliding must still deny here because @50 and @120 are both in (20, 120].
    clock.set(130);
    assert.equal(limiter.check('k').allowed, false);

    // @151: @50 expired (50 <= 151-100), @120 remains -> one slot free again.
    clock.set(151);
    assert.equal(limiter.check('k').allowed, true);
  });
});

describe('R4: retryAfterMs is exact ms until the OLDEST in-window request expires', () => {
  test('single-slot limiter reports exact wait', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: clock });

    clock.set(0);
    assert.equal(limiter.check('k').retryAfterMs, 0); // allowed -> 0 (R2/R4)

    clock.set(30);
    // oldest (@0) expires at t=100 -> 70ms from now.
    assert.deepEqual(limiter.check('k'), { allowed: false, remaining: 0, retryAfterMs: 70 });

    clock.set(99);
    assert.equal(limiter.check('k').retryAfterMs, 1);
  });

  test('retryAfterMs tracks the oldest request as older ones expire', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: clock });

    clock.set(0);
    limiter.check('k');  // @0
    clock.set(40);
    limiter.check('k');  // @40
    clock.set(50);
    assert.equal(limiter.check('k').retryAfterMs, 50); // oldest is @0, expires @100

    clock.set(110);      // @0 expired; window holds only @40
    assert.equal(limiter.check('k').allowed, true); // @110 admitted
    clock.set(115);
    // window holds @40 and @110; oldest @40 expires at 140 -> 25ms.
    assert.equal(limiter.check('k').retryAfterMs, 25);
  });
});

describe('R11: window boundary is exclusive at the trailing edge', () => {
  test('a request exactly windowMs after the first is allowed once the first expires', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 3, windowMs: 100, now: clock });

    clock.set(0);
    limiter.check('k');
    limiter.check('k');
    limiter.check('k');
    assert.equal(limiter.check('k').allowed, false); // filled to limit @0

    clock.set(99); // one tick before the boundary: still denied
    assert.deepEqual(limiter.check('k'), { allowed: false, remaining: 0, retryAfterMs: 1 });

    clock.set(100); // exactly windowMs later: window is (0, 100], so requests @0 just expired
    const res = limiter.check('k');
    assert.equal(res.allowed, true);
    assert.equal(res.remaining, 2); // all three @0 expired simultaneously
  });
});

describe('R6: key isolation', () => {
  test('traffic on key A never affects key B', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: clock });

    limiter.check('A');
    limiter.check('A');
    assert.equal(limiter.check('A').allowed, false); // A exhausted

    // B is untouched: full quota.
    assert.deepEqual(limiter.check('B'), { allowed: true, remaining: 1, retryAfterMs: 0 });
    assert.deepEqual(limiter.stats('B'), { used: 1, remaining: 1, oldestMs: 0 });
    assert.deepEqual(limiter.stats('A'), { used: 2, remaining: 0, oldestMs: 0 });
  });
});

describe('R7: reset(key) and stats(key)', () => {
  test('reset(key) clears only that key', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: clock });

    limiter.check('A');
    limiter.check('B');
    assert.equal(limiter.check('A').allowed, false);
    assert.equal(limiter.check('B').allowed, false);

    limiter.reset('A');
    assert.equal(limiter.check('A').allowed, true);  // A cleared
    assert.equal(limiter.check('B').allowed, false); // B untouched
  });

  test('stats(key) reports without consuming quota', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: clock });

    // Unknown key: nothing used, no oldest entry.
    assert.deepEqual(limiter.stats('k'), { used: 0, remaining: 2, oldestMs: null });

    clock.set(10);
    limiter.check('k'); // @10
    clock.set(40);

    // oldestMs = age of the oldest in-window request = 40 - 10 = 30.
    const s = limiter.stats('k');
    assert.deepEqual(s, { used: 1, remaining: 1, oldestMs: 30 });

    // Repeated stats calls consume nothing: quota still allows one more.
    limiter.stats('k');
    limiter.stats('k');
    assert.equal(limiter.check('k').allowed, true);
    assert.equal(limiter.check('k').allowed, false);
  });

  test('stats(key) reflects expiry through the sliding window', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: clock });

    limiter.check('k'); // @0
    clock.set(100);     // expired at the boundary (R11)
    assert.deepEqual(limiter.stats('k'), { used: 0, remaining: 2, oldestMs: null });
  });
});

describe('R8: memory hygiene — fully-expired keys leave the store', () => {
  // _storeSize() is a documented introspection hook that exists solely to make
  // R8 testable; see the comment in rateLimiter.js.
  test('one-off keys are removed once all their requests expire', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: clock });

    for (let i = 0; i < 50; i++) limiter.check(`one-off-${i}`);
    assert.equal(limiter._storeSize(), 50);

    // Slide past the window: every request above is now expired.
    clock.set(100);
    limiter.check('fresh'); // any later call triggers the amortized sweep

    // All 50 dead keys were evicted; only the live 'fresh' key remains.
    assert.equal(limiter._storeSize(), 1);
  });

  test('stats() on a fully-expired key also evicts it', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: clock });

    limiter.check('k');
    assert.equal(limiter._storeSize(), 1);
    clock.set(100);
    limiter.stats('k');
    assert.equal(limiter._storeSize(), 0);
  });

  test('reset(key) removes the key from the store immediately', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: clock });

    limiter.check('k');
    assert.equal(limiter._storeSize(), 1);
    limiter.reset('k');
    assert.equal(limiter._storeSize(), 0);
  });
});
