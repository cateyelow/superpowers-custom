"""Deterministic UI probe v2 — measures what a reviewer would have to notice.

v1 (probe.py) scored 34% recall against adjudicated ground truth vs 74.9% for an
LLM with the superpowers skill. Diagnosing every miss showed they were NOT
"things a machine can't judge" — they were three fixable gaps:

  1. STATE. Half the defective UI does not exist in the load-time DOM (the file
     list, the later wizard steps). A snapshot probe cannot see them. v2 drives
     the page into its reachable states and re-measures each one.
  2. PSEUDO. :focus-visible / :disabled / ::placeholder styles never appear in
     getComputedStyle of the resting element, so every focus-ring and
     placeholder contrast defect was invisible. v2 walks the CSSOM rules.
  3. A BUG OF MINE. `[tabindex]` matched tabindex="-1" (programmatic focus
     targets), producing a false touch-target finding on an <h2>.

What v2 still cannot do is decide whether a behaviour is WRONG — that a Remove
button is dead mid-upload, that a past expiry date is accepted. Those need an
agent. This probe's job is to make sure the agent never spends attention on
anything a machine can measure.

Usage:  python probe2.py <file-or-url> [--viewports=375,768,1280] [--no-seed]
Output: JSON on stdout.
"""
import json
import sys

from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------- measurement
JS_HELPERS = r"""
const parseRGB = (s) => {
  const m = String(s).match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const p = m[1].split(',').map(x => parseFloat(x));
  return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1};
};
const lum = (c) => {
  const f = (v) => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
  return 0.2126*f(c.r) + 0.7152*f(c.g) + 0.0722*f(c.b);
};
const over = (fg, bg) => fg.a >= 0.999 ? fg : ({
  r: fg.r*fg.a + bg.r*(1-fg.a),
  g: fg.g*fg.a + bg.g*(1-fg.a),
  b: fg.b*fg.a + bg.b*(1-fg.a), a: 1});
const ratio = (a, b) => {
  const l1 = lum(over(a, b)), l2 = lum(b);
  return (Math.max(l1,l2) + 0.05) / (Math.min(l1,l2) + 0.05);
};
const bgOf = (el) => {
  let n = el;
  while (n && n.nodeType === 1) {
    const c = parseRGB(getComputedStyle(n).backgroundColor);
    if (c && c.a > 0.99) return c;
    n = n.parentElement;
  }
  return {r:255, g:255, b:255, a:1};
};
const sel = (el) => {
  if (el.id) return '#' + el.id;
  const cls = (el.className && typeof el.className === 'string')
    ? '.' + el.className.trim().split(/\s+/).slice(0,2).join('.') : '';
  return el.tagName.toLowerCase() + cls;
};
const visible = (el) => {
  const r = el.getBoundingClientRect();
  const st = getComputedStyle(el);
  return r.width > 0 && r.height > 0 && st.visibility !== 'hidden'
         && st.display !== 'none' && parseFloat(st.opacity) > 0.05;
};
// FIX (v1 bug): tabindex="-1" is a programmatic focus target, not a control.
const INTERACTIVE = 'a[href],button,input,select,textarea,[role=button],[role=link],[role=checkbox],[role=tab],[tabindex]:not([tabindex="-1"])';
const isDisabled = (el) => el.matches('[disabled],[aria-disabled=true]') || !!el.closest('[disabled]');

// CSSOM rules carry AUTHORED syntax — "#98a2b3", "rgb(64 95 216 / 28%)",
// "3px solid <color>" shorthands. parseRGB only understands the COMPUTED
// rgb()/rgba() form, so v2's first cut silently dropped every pseudo-class
// finding. Let the engine normalise instead of parsing CSS by hand.
const normColor = (raw, shorthandProp) => {
  if (!raw) return null;
  const probe = document.createElement('span');
  probe.style.cssText = 'position:absolute;left:-9999px';
  document.body.appendChild(probe);
  try {
    if (shorthandProp) {
      probe.style.setProperty(shorthandProp, raw);
      const c = getComputedStyle(probe)[
        shorthandProp === 'outline' ? 'outlineColor'
        : shorthandProp === 'box-shadow' ? 'boxShadow' : 'borderTopColor'];
      const m = String(c).match(/rgba?\([^)]+\)/);
      return m ? parseRGB(m[0]) : null;
    }
    probe.style.color = '';
    probe.style.color = raw;
    if (!probe.style.color) return null;   // engine rejected it
    return parseRGB(getComputedStyle(probe).color);
  } finally { probe.remove(); }
};
const resolveVar = (raw) => {
  const m = String(raw).match(/var\((--[\w-]+)[^)]*\)/);
  if (!m) return raw;
  const v = getComputedStyle(document.documentElement).getPropertyValue(m[1]).trim();
  return v ? String(raw).replace(m[0], v) : raw;
};
"""

JS_MEASURE = JS_HELPERS + r"""
(() => {
  const out = {contrast: [], targets: [], roles: [], overflow: null, controls: []};
  const seen = new Set();
  const push = (arr, key, obj) => { if (!seen.has(key)) { seen.add(key); arr.push(obj); } };

  // --- resting text contrast (WCAG 1.4.3) ---
  for (const el of document.querySelectorAll('body *')) {
    if (!visible(el)) continue;
    if (!Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const st = getComputedStyle(el);
    const fg = parseRGB(st.color);
    if (!fg) continue;
    const size = parseFloat(st.fontSize);
    const large = size >= 24 || (size >= 18.66 && parseInt(st.fontWeight,10) >= 700);
    const need = large ? 3.0 : 4.5;
    const bg = bgOf(el);
    const got = ratio(fg, bg);
    if (got >= need) continue;
    const dis = isDisabled(el);
    push(out.contrast, 'txt|'+sel(el)+'|'+got.toFixed(2), {
      sel: sel(el), ratio: +got.toFixed(2), need, kind: 'text',
      disabled: dis,  // WCAG exempts these; reported so a human can still judge legibility
      text: el.textContent.trim().slice(0, 48)});
  }

  // --- non-text contrast: boundaries of controls (WCAG 1.4.11) ---
  for (const el of document.querySelectorAll(INTERACTIVE)) {
    if (!visible(el)) continue;
    const st = getComputedStyle(el);
    const bw = parseFloat(st.borderTopWidth) || 0;
    if (bw <= 0) continue;
    const bc = parseRGB(st.borderTopColor);
    if (!bc || bc.a < 0.05) continue;
    const backdrop = bgOf(el.parentElement || document.body);
    const got = ratio(bc, backdrop);
    if (got >= 3.0) continue;
    push(out.contrast, 'bd|'+sel(el)+'|'+got.toFixed(2), {
      sel: sel(el), ratio: +got.toFixed(2), need: 3.0, kind: 'boundary',
      disabled: isDisabled(el), text: el.textContent.trim().slice(0, 48)});
  }

  // --- touch targets (WCAG 2.5.8 / 2.5.5) ---
  // PRECISION (2026-08-11): a text field is dragged into, not tapped once, and
  // its hit area is the whole box — a 42px-tall input is not a touch defect and
  // the reference explicitly treats it as fine. Applying the 44px guidance to
  // text entry produced false alarms that then had to be suppressed by prompt
  // guidance, which in turn suppressed a REAL 38px button. Hold buttons and
  // links to 44; hold text entry to the 24px hard minimum only.
  const TEXT_ENTRY = 'input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit]),textarea,select';
  for (const el of document.querySelectorAll(INTERACTIVE)) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    const small = Math.min(r.width, r.height);
    const floor = el.matches(TEXT_ENTRY) ? 24 : 44;
    if (small >= floor) continue;
    push(out.targets, 'tt|'+sel(el)+'|'+r.width.toFixed(0)+'x'+r.height.toFixed(0), {
      sel: sel(el), w: +r.width.toFixed(1), h: +r.height.toFixed(1),
      severity: small < 24 ? 'under-24-FAILS-WCAG-2.5.8'
                           : 'under-44 — a tap target this size is hard to hit',
      disabled: isDisabled(el), text: el.textContent.trim().slice(0, 48)});
  }

  // --- name / role exposure (WCAG 4.1.2) ---
  for (const el of document.querySelectorAll('[tabindex]:not([tabindex="-1"])')) {
    if (!visible(el)) continue;
    const tag = el.tagName.toLowerCase();
    if (['a','button','input','select','textarea'].includes(tag)) continue;
    if (el.getAttribute('role')) continue;
    push(out.roles, 'role|'+sel(el)+'|'+el.textContent.trim().slice(0,20), {
      sel: sel(el), tag, issue: 'operable (tabindex=0 + handlers) but exposes no interactive role',
      text: el.textContent.trim().slice(0, 48)});
  }
  for (const el of document.querySelectorAll(INTERACTIVE)) {
    if (!visible(el)) continue;
    const name = (el.getAttribute('aria-label') || el.getAttribute('title') || '').trim()
      || (el.labels && el.labels.length ? Array.from(el.labels).map(l=>l.textContent).join(' ').trim() : '')
      || el.textContent.trim();
    if (name) continue;
    push(out.roles, 'name|'+sel(el), {sel: sel(el), tag: el.tagName.toLowerCase(),
                                      issue: 'no accessible name', text: ''});
  }
  // a control nested inside another control (duplicated in the a11y tree)
  for (const el of document.querySelectorAll(INTERACTIVE)) {
    if (!visible(el)) continue;
    const outer = el.parentElement && el.parentElement.closest(INTERACTIVE);
    if (!outer) continue;
    push(out.roles, 'nest|'+sel(el), {
      sel: sel(el), tag: el.tagName.toLowerCase(),
      issue: 'focusable control nested inside another control (' + sel(outer) + ')',
      text: el.textContent.trim().slice(0, 48)});
  }

  out.overflow = {
    docWidth: document.documentElement.scrollWidth,
    viewWidth: document.documentElement.clientWidth,
    overflows: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1};
  // PRECISION (2026-08-11): per-element overflow detection is DROPPED. Both
  // variants produced only false alarms: `overflow-x: auto` that scrolls is
  // working as designed (content is reachable), and `overflow: hidden` is an
  // ordinary layout tool — visually-hidden inputs, ellipsis truncation,
  // deliberate cropping. Neither is evidence of a defect on its own. The one
  // real clipping defect in the reference set (C-R1) is a CSS specificity
  // conflict, which dead_css.py detects directly and precisely.
  // Document-level overflow is still reported: nothing legitimately makes the
  // whole page scroll sideways at a supported width.
  out.clipped = [];
  out.controls = Array.from(document.querySelectorAll(INTERACTIVE)).filter(visible).map(sel);
  return out;
})()
"""

# Pseudo-class / pseudo-element styles never show up in getComputedStyle of the
# resting element. Walk the CSSOM instead — this is where focus rings and
# placeholders hide, and where v1 lost every one of those defects.
JS_PSEUDO = JS_HELPERS + r"""
(() => {
  const findings = [];
  // PRECISION (2026-08-11): :hover and :active are dropped. A hover shadow is
  // decoration, not a focus indicator, and no contrast minimum applies to it —
  // v2 emitted those and they were correctly rejected. Focus indicators
  // (1.4.11) and placeholder text (1.4.3) are the ones with real thresholds.
  const PSEUDO = /(:focus-visible|:focus|:disabled|::placeholder|:checked)/;
  const rules = [];
  for (const sheet of document.styleSheets) {
    let list; try { list = sheet.cssRules; } catch (e) { continue; }
    // HAZARD: since CSS Nesting shipped, a plain CSSStyleRule ALSO exposes a
    // (usually empty) .cssRules. An `if (r.cssRules) recurse; else collect;`
    // walk therefore recurses into every style rule and collects NOTHING —
    // this silently zeroed the whole pseudo-class scan. Collect first, then
    // recurse only into non-empty children.
    const walk = (rs) => { for (const r of rs) {
      if (r.selectorText) rules.push(r);
      if (r.cssRules && r.cssRules.length) walk(r.cssRules);
    }};
    walk(list);
  }
  for (const rule of rules) {
    if (!PSEUDO.test(rule.selectorText)) continue;
    for (const part of rule.selectorText.split(',')) {
      const s = part.trim();
      const m = s.match(PSEUDO);
      if (!m) continue;
      const base = s.slice(0, s.indexOf(m[0])).trim() || '*';
      let els = [];
      try { els = Array.from(document.querySelectorAll(base)).filter(visible); } catch (e) { continue; }
      if (!els.length) continue;
      const el = els[0];
      const backdrop = bgOf(el.parentElement || document.body);
      const own = bgOf(el);
      const st = rule.style;

      // focus indicator / border colour must reach 3:1 (WCAG 1.4.11).
      // A focus ring is drawn OUTSIDE the control, so it is judged against the
      // backdrop; a border replaces the control's own edge.
      const SHORTHAND = {'outline': 'outline', 'box-shadow': 'box-shadow',
                         'border': 'border', 'border-color': null,
                         'outline-color': null};
      for (const prop of ['outline', 'outline-color', 'border', 'border-color', 'box-shadow']) {
        const raw = st.getPropertyValue(prop);
        if (!raw || /^(none|0px|0)$/.test(raw.trim())) continue;
        const resolved = resolveVar(raw);
        const c = normColor(resolved, SHORTHAND[prop]);
        if (!c || c.a < 0.02) continue;
        const against = /outline|shadow/.test(prop) ? backdrop : own;
        const got = ratio(c, against);
        if (got >= 3.0) continue;
        findings.push({
          selector: s, prop, declared: raw.trim(), resolved: String(resolved).trim(),
          composited: `rgb(${Math.round(over(c, against).r)},${Math.round(over(c, against).g)},${Math.round(over(c, against).b)})`,
          ratio: +got.toFixed(2), need: 3.0, sample: sel(el), count: els.length,
          note: m[0] === '::placeholder' ? 'placeholder boundary'
                : `non-text contrast of the ${m[0]} indicator`});
      }

      // text colour in a state (placeholder / disabled label) must reach 4.5:1
      const col = st.getPropertyValue('color');
      if (col) {
        const resolved = resolveVar(col);
        const c = normColor(resolved, null);
        if (c) {
          // ::placeholder and :disabled paint over the element's OWN background
          const declBg = st.getPropertyValue('background-color') || st.getPropertyValue('background');
          const bgDecl = (declBg && normColor(resolveVar(declBg), null)) || own;
          const got = ratio(c, bgDecl);
          const size = parseFloat(getComputedStyle(el).fontSize) || 16;
          const need = size >= 24 ? 3.0 : 4.5;
          if (got < need) findings.push({
            selector: s, prop: 'color', declared: col.trim(), resolved: String(resolved).trim(),
            ratio: +got.toFixed(2), need, sample: sel(el), count: els.length,
            note: m[0] === '::placeholder' ? 'placeholder text contrast'
                  : (m[0] === ':disabled' ? 'disabled label — WCAG-exempt but often unreadable'
                                          : 'state text contrast')});
        }
      }
    }
  }
  return findings;
})()
"""

# ------------------------------------------------------------------- state fan
JS_SEED = r"""
(() => {
  // Fill every field with something plausible so downstream steps become
  // reachable and rendered rows exist. Deterministic, no randomness.
  const val = (el) => {
    const t = (el.type || '').toLowerCase();
    const n = ((el.name || '') + ' ' + (el.id || '')).toLowerCase();
    if (t === 'email') return 'a@b.co';
    if (t === 'tel') return '5551234567';
    if (t === 'number') return '1';
    if (/card|number/.test(n)) return '4111111111111111';
    if (/expiry|exp/.test(n)) return '1230';
    if (/cvc|cvv/.test(n)) return '123';
    if (/postal|zip/.test(n)) return '12345';
    return 'Test';
  };
  let n = 0;
  for (const el of document.querySelectorAll('input,textarea')) {
    const t = (el.type || '').toLowerCase();
    if (['file','submit','button','reset','hidden'].includes(t)) continue;
    if (t === 'checkbox' || t === 'radio') { if (!el.checked) { el.checked = true; n++; } }
    else { el.value = val(el); n++; }
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
  }
  for (const el of document.querySelectorAll('select')) {
    if (el.options.length > 1) { el.selectedIndex = 1; n++;
      el.dispatchEvent(new Event('change', {bubbles: true})); }
  }
  return n;
})()
"""


def measure_all(page, viewports, label, report):
    for w in viewports:
        page.set_viewport_size({'width': w, 'height': 900})
        page.wait_for_timeout(140)
        report['states'].setdefault(label, {})[str(w)] = page.evaluate(JS_MEASURE)
    page.set_viewport_size({'width': viewports[-1], 'height': 900})
    page.wait_for_timeout(80)
    report['states'][label]['pseudo'] = page.evaluate(JS_PSEUDO)


def run(target, viewports, seed=True):
    url = target if '://' in target else 'file:///' + target.replace('\\', '/')
    report = {'target': url, 'states': {}, 'notes': []}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        try:
            page = b.new_page()
            page.goto(url, wait_until='load')
            measure_all(page, viewports, 'load', report)

            if not seed:
                return report

            # --- state 2: every field populated -------------------------------
            try:
                filled = page.evaluate(JS_SEED)
                if filled:
                    page.wait_for_timeout(200)
                    measure_all(page, viewports, 'filled', report)
                    report['notes'].append(f'seeded {filled} field(s)')
            except Exception as exc:
                report['notes'].append(f'seed failed: {exc!r}')

            # --- state 3: a file selected (exposes list/row UI) ---------------
            try:
                inputs = page.query_selector_all('input[type=file]')
                if inputs:
                    inputs[0].set_input_files([{'name': 'alpha.txt', 'mimeType': 'text/plain',
                                                'buffer': b'x' * 2900},
                                               {'name': 'beta.txt', 'mimeType': 'text/plain',
                                                'buffer': b'y' * 1200}])
                    page.wait_for_timeout(250)
                    measure_all(page, viewports, 'files-selected', report)
                    report['notes'].append('selected 2 files')
            except Exception as exc:
                report['notes'].append(f'file seed failed: {exc!r}')

            # --- state 4..n: advance through whatever the buttons reveal ------
            page.set_viewport_size({'width': viewports[-1], 'height': 900})
            for step in range(1, 4):
                try:
                    before = page.evaluate('() => document.body.innerHTML.length')
                    btn = None
                    for cand in page.query_selector_all('button,[role=button],a[href="#"]'):
                        txt = (cand.inner_text() or '').strip().lower()
                        if not cand.is_visible() or not cand.is_enabled():
                            continue
                        if any(k in txt for k in ('next', 'continue', 'proceed', 'review', '다음')):
                            btn = cand
                            break
                    if not btn:
                        break
                    btn.click(timeout=2000)
                    page.wait_for_timeout(250)
                    page.evaluate(JS_SEED)
                    page.wait_for_timeout(150)
                    if page.evaluate('() => document.body.innerHTML.length') == before:
                        break
                    measure_all(page, viewports, f'step-{step + 1}', report)
                    report['notes'].append(f'advanced to step {step + 1}')
                except Exception:
                    break

            # --- empty/no-results state --------------------------------------
            try:
                srch = page.query_selector('input[type=search],#search,[name=search]')
                if srch:
                    srch.fill('zzzzzzzz')
                    page.wait_for_timeout(250)
                    measure_all(page, viewports, 'no-results', report)
                    report['notes'].append('searched for a no-match term')
            except Exception:
                pass
        finally:
            b.close()
    return report


def summarize(report):
    """Collapse every state/viewport into one deduplicated finding list."""
    out, seen = [], set()
    for state, byvw in report['states'].items():
        for vw, data in byvw.items():
            if vw == 'pseudo':
                for f in data:
                    k = ('pseudo', f['selector'], f['prop'], f['ratio'])
                    if k in seen:
                        continue
                    seen.add(k)
                    out.append({'type': 'contrast-state', 'state': state, **f})
                continue
            for c in data['contrast']:
                k = ('c', c['sel'], c['ratio'], c['kind'])
                if k in seen:
                    continue
                seen.add(k)
                out.append({'type': 'contrast', 'state': state, 'viewport': vw, **c})
            for t in data['targets']:
                k = ('t', t['sel'], t['w'], t['h'])
                if k in seen:
                    continue
                seen.add(k)
                out.append({'type': 'touch-target', 'state': state, 'viewport': vw, **t})
            for r in data['roles']:
                k = ('r', r['sel'], r['issue'])
                if k in seen:
                    continue
                seen.add(k)
                out.append({'type': 'name-role', 'state': state, 'viewport': vw, **r})
            for cl in data.get('clipped', []):
                k = ('x', cl['sel'], vw)
                if k in seen:
                    continue
                seen.add(k)
                out.append({'type': 'clipped-overflow', 'state': state, 'viewport': vw, **cl})
            if data['overflow']['overflows']:
                k = ('o', vw)
                if k not in seen:
                    seen.add(k)
                    out.append({'type': 'page-overflow', 'state': state, 'viewport': vw,
                                **data['overflow']})
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    vp = [375, 768, 1280]
    for a in sys.argv[1:]:
        if a.startswith('--viewports'):
            vp = [int(x) for x in a.split('=', 1)[1].split(',')]
    rep = run(args[0], vp, seed='--no-seed' not in sys.argv)
    rep['findings'] = summarize(rep)
    print(json.dumps(rep, indent=2))
