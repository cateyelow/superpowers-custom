// Deterministic behavioral probe for the ratelimit task.
// Usage: node probe_ratelimit.mjs <path-to-rateLimiter.js>
// Prints one line per check: PROBE <id> PASS|FAIL <note>. Exit 0 always (score by output).
const target = process.argv[2];
const checks = [];
const check = (id, fn) => checks.push([id, fn]);

const mod = await import(new URL(target, `file://${process.cwd()}/`).href).catch(e => {
  console.log(`PROBE import FAIL ${e.message}`);
  process.exit(0);
});
const { createRateLimiter } = mod;

check('R1_factory_shape', () => {
  let t = 0;
  const rl = createRateLimiter({ limit: 2, windowMs: 1000, now: () => t });
  return typeof rl.check === 'function' && typeof rl.reset === 'function' && typeof rl.stats === 'function';
});

check('R2_check_shape', () => {
  let t = 0;
  const rl = createRateLimiter({ limit: 2, windowMs: 1000, now: () => t });
  const r = rl.check('a');
  return r.allowed === true && typeof r.remaining === 'number' && typeof r.retryAfterMs === 'number';
});

check('R9_factory_validation', () => {
  const bad = [{ limit: 0, windowMs: 1000 }, { limit: 5, windowMs: 0 }, { limit: -1, windowMs: 1000 }];
  return bad.every(opts => {
    try { createRateLimiter(opts); return false; } catch (e) { return e instanceof RangeError; }
  });
});

check('R10_burst_edge', () => {
  let t = 100;
  const rl = createRateLimiter({ limit: 3, windowMs: 1000, now: () => t });
  const rs = [rl.check('k'), rl.check('k'), rl.check('k'), rl.check('k')];
  return rs[0].allowed && rs[1].allowed && rs[2].allowed && !rs[3].allowed;
});

check('R11_boundary_exclusive', () => {
  let t = 0;
  const rl = createRateLimiter({ limit: 2, windowMs: 1000, now: () => t });
  rl.check('k'); rl.check('k');
  t = 999;
  if (rl.check('k').allowed) return false; // still inside window
  t = 1000; // exactly windowMs after first: first request expired
  return rl.check('k').allowed === true;
});

check('R4_retryAfter_exact', () => {
  let t = 0;
  const rl = createRateLimiter({ limit: 2, windowMs: 1000, now: () => t });
  rl.check('k'); // at t=0
  t = 300;
  rl.check('k'); // at t=300
  t = 400;
  const r = rl.check('k'); // denied; oldest (t=0) expires at t=1000 → 600ms
  return !r.allowed && r.retryAfterMs === 600;
});

check('R3_sliding_not_bucket', () => {
  let t = 0;
  const rl = createRateLimiter({ limit: 2, windowMs: 1000, now: () => t });
  rl.check('k'); // t=0
  t = 800; rl.check('k'); // t=800
  t = 1100; // first expired, second still in window → exactly 1 slot free
  const a = rl.check('k'); // should be allowed (uses the free slot)
  const b = rl.check('k'); // should be denied (window has 800, 1100)
  return a.allowed && !b.allowed;
});

check('R6_key_isolation', () => {
  let t = 0;
  const rl = createRateLimiter({ limit: 1, windowMs: 1000, now: () => t });
  rl.check('a');
  return rl.check('b').allowed === true;
});

check('R7_stats_no_consume', () => {
  let t = 0;
  const rl = createRateLimiter({ limit: 2, windowMs: 1000, now: () => t });
  rl.check('k');
  const s1 = rl.stats('k');
  const s2 = rl.stats('k');
  if (!s1 || s1.used !== 1 || s1.remaining !== 1) return false;
  if (!s2 || s2.used !== 1) return false; // stats consumed quota if used grew
  const r = rl.check('k');
  return r.allowed === true; // second real slot still available
});

check('R7_reset_scoped', () => {
  let t = 0;
  const rl = createRateLimiter({ limit: 1, windowMs: 1000, now: () => t });
  rl.check('a'); rl.check('b');
  rl.reset('a');
  return rl.check('a').allowed === true && rl.check('b').allowed === false;
});

check('R2_never_throws', () => {
  let t = 0;
  const rl = createRateLimiter({ limit: 1, windowMs: 1000, now: () => t });
  try { rl.check(''); rl.check('아주긴한글키'.repeat(50)); return true; } catch { return false; }
});

for (const [id, fn] of checks) {
  let ok = false, note = '';
  try { ok = fn(); } catch (e) { note = e.message; }
  console.log(`PROBE ${id} ${ok ? 'PASS' : 'FAIL'} ${note}`);
}
