"""Deterministic UI probe — the candidate harness's first stage.

Rationale (measured 2026-08-11): the adjudicated ground truth across three web
artifacts was dominated by defects that are COMPUTABLE, not judgement calls —
contrast ratios, touch-target sizes, missing interactive roles, viewport
overflow, focus loss. LLM reviewers missed them by skimming, not by being
unable to decide. A machine does not skim.

This probe enumerates every candidate element and measures. It produces
findings an LLM never has to "notice" — only triage.

Usage:  python probe.py <file-or-url> [--viewports 375,768,1280]
Output: JSON on stdout. Exit 0 always (findings are data, not failure).
"""
import json
import sys

from playwright.sync_api import sync_playwright

JS_MEASURE = r"""
() => {
  const out = {contrast: [], targets: [], roles: [], overflow: null, focusable: []};

  const parseRGB = (s) => {
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x));
    return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1};
  };
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(c.r) + 0.7152*f(c.g) + 0.0722*f(c.b);
  };
  const ratio = (a, b) => {
    const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1,l2) + 0.05) / (Math.min(l1,l2) + 0.05);
  };
  // walk up for the first opaque background
  const bgOf = (el) => {
    let n = el;
    while (n && n !== document.documentElement) {
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
    return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none'
           && parseFloat(st.opacity) > 0.05;
  };

  const INTERACTIVE = 'a,button,input,select,textarea,[role=button],[role=link],[tabindex]';

  // --- text contrast (WCAG 1.4.3) ---
  for (const el of document.querySelectorAll('body *')) {
    if (!visible(el)) continue;
    const direct = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
    if (!direct) continue;
    const st = getComputedStyle(el);
    const fg = parseRGB(st.color);
    if (!fg || fg.a < 0.99) continue;
    const size = parseFloat(st.fontSize);
    const bold = parseInt(st.fontWeight, 10) >= 700;
    const large = size >= 24 || (size >= 18.66 && bold);
    const need = large ? 3.0 : 4.5;
    const got = ratio(fg, bgOf(el));
    // WCAG exempts text in a disabled control
    const dis = el.closest('[disabled],[aria-disabled=true]') !== null;
    if (got < need && !dis) {
      out.contrast.push({sel: sel(el), ratio: +got.toFixed(2), need,
                         text: el.textContent.trim().slice(0, 40), kind: 'text'});
    }
  }

  // --- non-text contrast of interactive boundaries (WCAG 1.4.11) ---
  for (const el of document.querySelectorAll(INTERACTIVE)) {
    if (!visible(el)) continue;
    if (el.matches('[disabled],[aria-disabled=true]')) continue;
    const st = getComputedStyle(el);
    const bw = parseFloat(st.borderTopWidth) || 0;
    if (bw <= 0) continue;
    const bc = parseRGB(st.borderTopColor);
    if (!bc || bc.a < 0.99) continue;
    const got = ratio(bc, bgOf(el.parentElement || document.body));
    if (got < 3.0) {
      out.contrast.push({sel: sel(el), ratio: +got.toFixed(2), need: 3.0,
                         text: el.textContent.trim().slice(0, 40), kind: 'boundary'});
    }
  }

  // --- touch targets (WCAG 2.5.8 / 2.5.5) ---
  for (const el of document.querySelectorAll(INTERACTIVE)) {
    if (!visible(el)) continue;
    if (el.matches('[disabled],[aria-disabled=true]')) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 24 || r.height < 24) {
      out.targets.push({sel: sel(el), w: +r.width.toFixed(1), h: +r.height.toFixed(1),
                        text: el.textContent.trim().slice(0, 40), severity: 'under-24'});
    } else if (r.width < 44 || r.height < 44) {
      out.targets.push({sel: sel(el), w: +r.width.toFixed(1), h: +r.height.toFixed(1),
                        text: el.textContent.trim().slice(0, 40), severity: 'under-44'});
    }
  }

  // --- operable but not exposed as a control ---
  for (const el of document.querySelectorAll('[tabindex]:not([tabindex="-1"])')) {
    if (!visible(el)) continue;
    const tag = el.tagName.toLowerCase();
    const native = ['a','button','input','select','textarea'].includes(tag);
    if (native || el.getAttribute('role')) continue;
    out.roles.push({sel: sel(el), issue: 'focusable with no role',
                    text: el.textContent.trim().slice(0, 40)});
  }
  // controls with no accessible name
  for (const el of document.querySelectorAll(INTERACTIVE)) {
    if (!visible(el)) continue;
    const name = (el.getAttribute('aria-label') || el.getAttribute('title') || '').trim()
      || (el.labels && el.labels.length ? Array.from(el.labels).map(l=>l.textContent).join(' ').trim() : '')
      || el.textContent.trim();
    if (!name) out.roles.push({sel: sel(el), issue: 'no accessible name', text: ''});
  }

  out.overflow = {
    docWidth: document.documentElement.scrollWidth,
    viewWidth: document.documentElement.clientWidth,
    overflows: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  };
  out.focusable = Array.from(document.querySelectorAll(INTERACTIVE))
    .filter(visible).map(sel);
  return out;
}
"""


def run(target, viewports):
    url = target if '://' in target else 'file:///' + target.replace('\\', '/')
    report = {'target': url, 'viewports': {}}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        try:
            page = b.new_page()
            page.goto(url, wait_until='load')
            for w in viewports:
                page.set_viewport_size({'width': w, 'height': 900})
                page.wait_for_timeout(120)
                report['viewports'][str(w)] = page.evaluate(JS_MEASURE)

            # focus-loss probe: activate each control, see where focus lands
            page.set_viewport_size({'width': 1280, 'height': 900})
            page.wait_for_timeout(80)
            losses = []
            for s in report['viewports'][str(viewports[-1])]['focusable']:
                try:
                    el = page.query_selector(s)
                    if not el or not el.is_enabled():
                        continue
                    page.eval_on_selector(s, 'e => e.focus()')
                    page.keyboard.press('Enter')
                    page.wait_for_timeout(60)
                    active = page.evaluate('() => document.activeElement.tagName')
                    if active == 'BODY':
                        losses.append({'sel': s, 'after': 'focus fell to <body>'})
                except Exception:
                    continue
            report['focus_loss'] = losses
        finally:
            b.close()
    return report


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    vp = [375, 768, 1280]
    for a in sys.argv[1:]:
        if a.startswith('--viewports'):
            vp = [int(x) for x in a.split('=', 1)[1].split(',')]
    print(json.dumps(run(args[0], vp), indent=2))
