// Tests for the sliding-window rate limiter (src/rateLimiter.js).
//
// Every test drives time exclusively through the injected `now` clock (R12):
// no timer scheduling, no sleeps, no real timers anywhere in this file.

import { describe, test } from 'node:test';
import assert from 'node:assert/strict';
import { createRateLimiter } from './rateLimiter.js';

/** Manual, fully deterministic clock for injection via the `now` option. */
function makeClock(start = 0) {
  let t = start;
  return {
    now: () => t,
    advance(ms) {
      t += ms;
    },
    set(ms) {
      t = ms;
    },
  };
}

describe('factory shape (R1)', () => {
  test('returns an object with exactly the methods check, reset, stats', () => {
    const clock = makeClock();
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: clock.now });
    assert.deepEqual(Object.keys(limiter).sort(), ['check', 'reset', 'stats']);
    assert.equal(typeof limiter.check, 'function');
    assert.equal(typeof limiter.reset, 'function');
    assert.equal(typeof limiter.stats, 'function');
  });

  test('now defaults to Date.now (single call, no time-dependent assertion)', () => {
    // No clock injected; a single check must simply work and be allowed.
    // No sleeps and no timing assertions, so this stays deterministic.
    const limiter = createRateLimiter({ limit: 1, windowMs: 1000 });
    const result = limiter.check('k');
    assert.equal(result.allowed, true);
    assert.equal(result.remaining, 0);
    assert.equal(result.retryAfterMs, 0);
  });
});

describe('input validation at factory time (R9)', () => {
  const exactlyRangeError = (err) =>
    err instanceof RangeError && err.constructor === RangeError;

  test('limit: 0 throws RangeError', () => {
    assert.throws(() => createRateLimiter({ limit: 0, windowMs: 100 }), exactlyRangeError);
  });

  test('negative limit throws RangeError', () => {
    assert.throws(() => createRateLimiter({ limit: -3, windowMs: 100 }), exactlyRangeError);
  });

  test('windowMs: 0 throws RangeError', () => {
    assert.throws(() => createRateLimiter({ limit: 5, windowMs: 0 }), exactlyRangeError);
  });

  test('negative windowMs throws RangeError', () => {
    assert.throws(() => createRateLimiter({ limit: 5, windowMs: -100 }), exactlyRangeError);
  });

  test('fractional limit throws RangeError (limit is a request count)', () => {
    assert.throws(() => createRateLimiter({ limit: 1.5, windowMs: 100 }), exactlyRangeError);
  });

  test('NaN and Infinity limit throw RangeError', () => {
    assert.throws(() => createRateLimiter({ limit: NaN, windowMs: 100 }), exactlyRangeError);
    assert.throws(() => createRateLimiter({ limit: Infinity, windowMs: 100 }), exactlyRangeError);
  });

  test('NaN and Infinity windowMs throw RangeError', () => {
    assert.throws(() => createRateLimiter({ limit: 5, windowMs: NaN }), exactlyRangeError);
    assert.throws(() => createRateLimiter({ limit: 5, windowMs: Infinity }), exactlyRangeError);
  });

  test('valid arguments do not throw (fractional windowMs is valid time)', () => {
    assert.doesNotThrow(() => createRateLimiter({ limit: 1, windowMs: 1 }));
    assert.doesNotThrow(() => createRateLimiter({ limit: 1, windowMs: 0.5 }));
  });
});

describe('check() result shape and hostile string keys (R2)', () => {
  test('returns { allowed, remaining, retryAfterMs } with correct types', () => {
    const clock = makeClock();
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: clock.now });
    const result = limiter.check('key');
    assert.deepEqual(Object.keys(result).sort(), ['allowed', 'remaining', 'retryAfterMs']);
    assert.equal(typeof result.allowed, 'boolean');
    assert.equal(typeof result.remaining, 'number');
    assert.equal(typeof result.retryAfterMs, 'number');
  });

  test('never throws for prototype-ish and empty string keys, and they stay isolated', () => {
    const clock = makeClock();
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: clock.now });
    for (const key of ['__proto__', 'constructor', '', 'hasOwnProperty', 'toString']) {
      let result;
      assert.doesNotThrow(() => {
        result = limiter.check(key);
      });
      // Each hostile key gets its own fresh quota — proves keys are not
      // colliding through a shared prototype chain (structural via Map).
      assert.equal(result.allowed, true, `first check for ${JSON.stringify(key)}`);
      assert.equal(result.remaining, 0);
      assert.doesNotThrow(() => limiter.stats(key));
      assert.doesNotThrow(() => limiter.reset(key));
    }
  });
});

describe('sliding-window semantics (R3)', () => {
  test('requests expire individually as the window slides, not in buckets', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 3, windowMs: 100, now: clock.now });

    // Fill at varied timestamps: t=0, t=40, t=80.
    clock.set(0);
    assert.equal(limiter.check('k').allowed, true);
    clock.set(40);
    assert.equal(limiter.check('k').allowed, true);
    clock.set(80);
    assert.equal(limiter.check('k').allowed, true);

    // t=90: all three still in window -> denied.
    clock.set(90);
    assert.equal(limiter.check('k').allowed, false);

    // t=101: only the t=0 request has expired (window is (1, 101]); the
    // t=40 and t=80 requests are still counted -> exactly one slot free.
    clock.set(101);
    const afterFirstExpiry = limiter.check('k');
    assert.equal(afterFirstExpiry.allowed, true);
    assert.equal(afterFirstExpiry.remaining, 0);
    // Window now holds t=40, t=80, t=101 -> immediately denied again.
    assert.equal(limiter.check('k').allowed, false);

    // t=141: now the t=40 request has also expired (individually) -> one
    // more slot frees up, while t=80 and t=101 are still counted.
    clock.set(141);
    const afterSecondExpiry = limiter.check('k');
    assert.equal(afterSecondExpiry.allowed, true);
    assert.equal(afterSecondExpiry.remaining, 0);
    assert.equal(limiter.check('k').allowed, false);
  });
});

describe('retryAfterMs exactness (R4)', () => {
  test('is 0 when allowed', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: clock.now });
    assert.equal(limiter.check('k').retryAfterMs, 0);
    clock.set(30);
    assert.equal(limiter.check('k').retryAfterMs, 0);
  });

  test('is the exact ms until the OLDEST in-window request expires when denied', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: clock.now });
    clock.set(10);
    limiter.check('k'); // oldest, expires at t=110
    clock.set(20);
    limiter.check('k');

    clock.set(50);
    const denied = limiter.check('k');
    assert.equal(denied.allowed, false);
    assert.equal(denied.retryAfterMs, 60); // 10 + 100 - 50

    clock.set(109);
    const deniedLater = limiter.check('k');
    assert.equal(deniedLater.allowed, false);
    assert.equal(deniedLater.retryAfterMs, 1); // 10 + 100 - 109

    // Exactly when retryAfterMs said, the oldest expires and we are allowed.
    clock.set(110);
    assert.equal(limiter.check('k').allowed, true);
  });
});

describe('key isolation (R6)', () => {
  test('exhausting key A leaves key B untouched', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 3, windowMs: 100, now: clock.now });
    limiter.check('A');
    limiter.check('A');
    limiter.check('A');
    assert.equal(limiter.check('A').allowed, false);

    assert.equal(limiter.stats('B').remaining, 3);
    const b = limiter.check('B');
    assert.equal(b.allowed, true);
    assert.equal(b.remaining, 2);
    // And B's traffic does not change A either.
    assert.equal(limiter.check('A').allowed, false);
  });
});

describe('reset() and stats() (R7)', () => {
  test('reset(key) clears only that key', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: clock.now });
    limiter.check('A');
    limiter.check('B');
    assert.equal(limiter.check('A').allowed, false);
    assert.equal(limiter.check('B').allowed, false);

    limiter.reset('A');
    assert.equal(limiter.check('A').allowed, true); // A got its quota back
    assert.equal(limiter.check('B').allowed, false); // B is still exhausted
  });

  test('stats(key) returns { used, remaining, oldestMs } and never consumes quota', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 3, windowMs: 100, now: clock.now });

    // Unknown key: nothing used, nothing in window.
    assert.deepEqual(limiter.stats('k'), { used: 0, remaining: 3, oldestMs: null });

    clock.set(10);
    limiter.check('k');
    clock.set(30);
    limiter.check('k');

    clock.set(50);
    const s = limiter.stats('k');
    assert.deepEqual(Object.keys(s).sort(), ['oldestMs', 'remaining', 'used']);
    assert.equal(s.used, 2);
    assert.equal(s.remaining, 1);
    assert.equal(s.oldestMs, 40); // oldest in-window request (t=10) is 40ms old at t=50

    // Calling stats repeatedly never changes remaining (no quota consumed).
    for (let i = 0; i < 10; i += 1) {
      assert.equal(limiter.stats('k').remaining, 1);
    }
    assert.equal(limiter.check('k').allowed, true); // the slot is really still free
  });
});

describe('memory hygiene (R8)', () => {
  // Observable used here: `_storeSize()`, a documented non-enumerable debug
  // hook on the limiter that reports how many keys the internal Map holds.
  test('fully-expired one-off keys are removed from the internal store', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 2, windowMs: 100, now: clock.now });

    for (let i = 0; i < 500; i += 1) {
      limiter.check(`one-off-${i}`);
    }
    assert.equal(limiter._storeSize(), 500);

    // Advance past the window so every one-off key's requests have expired,
    // then trigger the module's sweep: any check() runs a global sweep once
    // at least windowMs has elapsed since the previous sweep.
    clock.advance(101);
    limiter.check('fresh');

    assert.equal(limiter._storeSize(), 1); // only 'fresh' remains

    // _storeSize is intentionally non-enumerable (API surface stays
    // exactly check/reset/stats).
    assert.equal(Object.keys(limiter).includes('_storeSize'), false);
  });

  test('a key touched after its requests expired is pruned per-key too', () => {
    const clock = makeClock(0);
    const limiter = createRateLimiter({ limit: 1, windowMs: 100, now: clock.now });
    limiter.check('a');
    assert.equal(limiter._storeSize(), 1);
    clock.set(100); // request at t=0 has just expired (trailing edge exclusive)
    assert.deepEqual(limiter.stats('a'), { used: 0, remaining: 1, oldestMs: null });
    assert.equal(limiter._storeSize(), 0);
  });
});

describe('burst edge (R10)', () => {
  test('exactly limit requests at one frozen timestamp are allowed; limit+1 is denied', () => {
    const clock = makeClock(1000); // frozen: never advanced in this test
    const limit = 5;
    const limiter = createRateLimiter({ limit, windowMs: 250, now: clock.now });

    for (let i = 1; i <= limit; i += 1) {
      const result = limiter.check('burst');
      assert.equal(result.allowed, true, `request #${i} must be allowed`);
      assert.equal(result.remaining, limit - i);
      assert.equal(result.retryAfterMs, 0);
    }

    const overflow = limiter.check('burst');
    assert.equal(overflow.allowed, false, `request #${limit + 1} must be denied`);
    assert.equal(overflow.remaining, 0);
    // Oldest request happened at the frozen timestamp -> full window remains.
    assert.equal(overflow.retryAfterMs, 250);
  });
});

describe('window boundary edge (R11)', () => {
  test('a request exactly windowMs after the first is allowed (trailing edge exclusive)', () => {
    const clock = makeClock(0);
    const limit = 3;
    const windowMs = 100;
    const limiter = createRateLimiter({ limit, windowMs, now: clock.now });

    // t=0: fill to limit.
    for (let i = 0; i < limit; i += 1) {
      assert.equal(limiter.check('k').allowed, true);
    }
    assert.equal(limiter.check('k').allowed, false);

    // t=windowMs-1: t=0 requests are still inside the window (0 > -1).
    clock.set(windowMs - 1);
    const stillDenied = limiter.check('k');
    assert.equal(stillDenied.allowed, false);
    assert.equal(stillDenied.retryAfterMs, 1);

    // t=windowMs exactly: window is (0, 100], the t=0 requests have just
    // expired, so a new request must be ALLOWED.
    clock.set(windowMs);
    const boundary = limiter.check('k');
    assert.equal(boundary.allowed, true);
    assert.equal(boundary.remaining, limit - 1); // all t=0 requests left together here
  });
});
