/**
 * Sliding-window rate limiter (ESM, zero dependencies).
 *
 * A request made at time t is counted against the window (t - windowMs, t]:
 * the trailing edge is exclusive, so a request timestamped exactly
 * `windowMs` ago has just expired. Requests expire individually as the
 * window slides — this is NOT a fixed-bucket counter.
 *
 * All time reads go through the injectable `now` clock (defaults to
 * Date.now); nothing else in this module touches the wall clock.
 */

/**
 * @param {object} options
 * @param {number} options.limit    Max requests per key per window. Must be a positive integer.
 * @param {number} options.windowMs Window length in ms. Must be > 0.
 * @param {() => number} [options.now] Injectable clock; defaults to Date.now.
 * @returns {{
 *   check(key: string): { allowed: boolean, remaining: number, retryAfterMs: number },
 *   reset(key: string): void,
 *   stats(key: string): { used: number, remaining: number, oldestMs: number | null },
 *   _storeSize(): number,
 * }}
 * @throws {RangeError} when `limit` is not a positive integer or `windowMs`
 *   is not a positive finite number.
 */
export function createRateLimiter({ limit, windowMs, now = Date.now } = {}) {
  if (!Number.isInteger(limit) || limit <= 0) {
    throw new RangeError(`limit must be a positive integer, got ${limit}`);
  }
  if (typeof windowMs !== 'number' || !Number.isFinite(windowMs) || windowMs <= 0) {
    throw new RangeError(`windowMs must be a positive finite number, got ${windowMs}`);
  }

  /** @type {Map<string, number[]>} key -> ascending in-window request timestamps */
  const store = new Map();

  // Amortized sweep bookkeeping: at most one full-store sweep per windowMs,
  // so keys that were hit once and never again ("one-off" keys) are evicted
  // within one window of any later activity. -Infinity makes the first call
  // sweep a trivially empty store and initialize the timestamp.
  let lastSweepAt = -Infinity;

  /**
   * Drop expired timestamps (ts <= t - windowMs) from a key's list and evict
   * the key entirely when nothing remains. Returns the live timestamp list.
   */
  function prune(key, t) {
    const timestamps = store.get(key);
    if (timestamps === undefined) return undefined;
    const cutoff = t - windowMs;
    let firstLive = 0;
    while (firstLive < timestamps.length && timestamps[firstLive] <= cutoff) {
      firstLive += 1;
    }
    if (firstLive === timestamps.length) {
      store.delete(key);
      return undefined;
    }
    if (firstLive > 0) timestamps.splice(0, firstLive);
    return timestamps;
  }

  /** Sweep every key at most once per windowMs (memory hygiene, R8). */
  function maybeSweep(t) {
    if (t - lastSweepAt < windowMs) return;
    lastSweepAt = t;
    for (const key of store.keys()) prune(key, t);
  }

  return {
    /**
     * Consume one slot for `key` if the window has capacity.
     * Never throws for string keys.
     */
    check(key) {
      const t = now();
      maybeSweep(t);
      const timestamps = prune(key, t);

      if (timestamps === undefined) {
        store.set(key, [t]);
        return { allowed: true, remaining: limit - 1, retryAfterMs: 0 };
      }
      if (timestamps.length < limit) {
        timestamps.push(t);
        return { allowed: true, remaining: limit - timestamps.length, retryAfterMs: 0 };
      }
      // Denied: the oldest in-window request expires at oldest + windowMs.
      return {
        allowed: false,
        remaining: 0,
        retryAfterMs: timestamps[0] + windowMs - t,
      };
    },

    /** Clear all state for `key` only; other keys are untouched. */
    reset(key) {
      store.delete(key);
    },

    /**
     * Report usage for `key` without consuming quota.
     * `oldestMs` is the age in ms of the oldest in-window request
     * (now - its timestamp), or null when the key has no live requests.
     */
    stats(key) {
      const t = now();
      const timestamps = prune(key, t);
      if (timestamps === undefined) {
        return { used: 0, remaining: limit, oldestMs: null };
      }
      return {
        used: timestamps.length,
        remaining: Math.max(0, limit - timestamps.length),
        oldestMs: t - timestamps[0],
      };
    },

    /**
     * Introspection hook: number of keys currently held in the internal
     * store. Exists SOLELY so tests can prove R8 (memory hygiene — fully
     * expired keys are evicted); it is not part of the limiter's public
     * rate-limiting contract.
     */
    _storeSize() {
      return store.size;
    },
  };
}
