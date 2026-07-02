// Sliding-window rate limiter (ESM, zero dependencies).
//
// Semantics
// - A request made at time t is counted against the window (t - windowMs, t]:
//   the trailing edge is EXCLUSIVE, so a request recorded at timestamp ts has
//   expired once now() - windowMs >= ts. Requests expire individually as the
//   window slides — there are no fixed buckets.
// - All time reads go through the injectable `now` clock (defaulting to the
//   system clock); nothing else in this module reads time directly.
//
// Memory hygiene (R8)
// - Per key: whenever a key is touched (check/stats), its expired timestamps
//   are pruned and the key is deleted from the store once empty.
// - Globally: check() and stats() run a full sweep of the store at most once
//   per windowMs (tracked via lastSweepAt), so one-off keys that are never
//   touched again are still removed and the store cannot grow without bound.
// - Observable: the returned limiter carries a NON-ENUMERABLE debug hook
//   `_storeSize()` reporting the number of keys currently in the internal
//   Map. It exists solely so tests can prove the hygiene property; it is a
//   pure read (no sweep, no quota impact) and keeps the enumerable API
//   surface at exactly { check, reset, stats }.

/**
 * Create a sliding-window rate limiter.
 *
 * @param {object} options
 * @param {number} options.limit    Max requests allowed per key per window
 *   (positive integer — it is a request count).
 * @param {number} options.windowMs Window length in milliseconds (> 0;
 *   fractional ms are semantically valid time).
 * @param {() => number} [options.now] Injectable clock returning epoch ms;
 *   the only source of time for the limiter. Defaults to the system clock.
 * @returns {{
 *   check(key: string): { allowed: boolean, remaining: number, retryAfterMs: number },
 *   reset(key: string): void,
 *   stats(key: string): { used: number, remaining: number, oldestMs: number | null },
 * }}
 * @throws {RangeError} At factory time when limit is not a positive integer
 *   or windowMs is not a positive finite number.
 */
export function createRateLimiter({ limit, windowMs, now = Date.now } = {}) {
  if (!Number.isInteger(limit) || limit <= 0) {
    throw new RangeError(`limit must be a positive integer, got ${limit}`);
  }
  if (!Number.isFinite(windowMs) || windowMs <= 0) {
    throw new RangeError(`windowMs must be a positive number, got ${windowMs}`);
  }

  /** @type {Map<string, number[]>} key -> ascending in-window request timestamps.
   * A Map (not a plain object) makes hostile keys like "__proto__" or
   * "constructor" structurally safe. */
  const store = new Map();
  let lastSweepAt = now();

  /**
   * Drop this key's expired timestamps (ts <= t - windowMs) and delete the
   * key entirely once empty. Returns the key's live in-window timestamps.
   */
  function prune(key, t) {
    const timestamps = store.get(key);
    if (timestamps === undefined) return [];
    const cutoff = t - windowMs;
    let expired = 0;
    while (expired < timestamps.length && timestamps[expired] <= cutoff) expired += 1;
    if (expired > 0) timestamps.splice(0, expired);
    if (timestamps.length === 0) {
      store.delete(key);
      return [];
    }
    return timestamps;
  }

  /** Full-store sweep, rate-limited to at most once per windowMs. */
  function sweepIfDue(t) {
    if (t - lastSweepAt < windowMs) return;
    lastSweepAt = t;
    for (const key of [...store.keys()]) prune(key, t);
  }

  function check(key) {
    const t = now();
    sweepIfDue(t);
    const timestamps = prune(key, t);
    if (timestamps.length >= limit) {
      // Oldest in-window request (ascending order -> index 0) expires exactly
      // at timestamps[0] + windowMs.
      return { allowed: false, remaining: 0, retryAfterMs: timestamps[0] + windowMs - t };
    }
    const list = store.get(key) ?? [];
    list.push(t);
    store.set(key, list);
    return { allowed: true, remaining: limit - list.length, retryAfterMs: 0 };
  }

  function reset(key) {
    store.delete(key);
  }

  function stats(key) {
    const t = now();
    sweepIfDue(t);
    const timestamps = prune(key, t);
    const used = timestamps.length;
    return {
      used,
      remaining: Math.max(0, limit - used),
      // Age in ms of the oldest in-window request; null when none in window.
      oldestMs: used === 0 ? null : t - timestamps[0],
    };
  }

  const limiter = { check, reset, stats };
  // Documented debug hook for memory-hygiene tests (see header comment).
  Object.defineProperty(limiter, '_storeSize', {
    value: () => store.size,
    enumerable: false,
  });
  return limiter;
}
