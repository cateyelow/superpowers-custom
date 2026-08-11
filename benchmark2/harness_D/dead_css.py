"""Detect declarations the author wrote that never take effect.

The one adjudicated defect probe2.py cannot see is C-R1: `.empty { text-align:
center }` is silently beaten by `td:last-child { text-align: right }` (0-1-1 vs
0-1-0), so the empty-state message renders right-aligned and, at 375px, is
pushed outside the scroll container's visible area.

That is not a contrast or size measurement — it is a CONFLICT. The author
declared an intent and another rule overrode it. This generalises well beyond
one page: a named, intent-bearing class (`.empty`, `.error`, `.active`) losing
to a positional or element selector is nearly always a bug, because the author
would not have written the declaration if they expected it to do nothing.

Run standalone:  python dead_css.py <file-or-url>
"""
import json
import sys

from playwright.sync_api import sync_playwright

JS = r"""
() => {
  // (a, b, c) specificity of a compound selector — enough for the comparison
  // we need; :not()/:is() inner weight is approximated by their contents.
  const spec = (s) => {
    let a = 0, b = 0, c = 0;
    let t = s.replace(/::?[\w-]+(\([^)]*\))?/g, (m) => {
      // pseudo-elements count as type, pseudo-classes as class
      if (m.startsWith('::')) { c++; return ' '; }
      if (/^:(not|is|has|where)\(/.test(m)) {
        const inner = m.slice(m.indexOf('(') + 1, -1);
        if (!/^:where\(/.test(m)) { const r = spec(inner); a += r[0]; b += r[1]; c += r[2]; }
        return ' ';
      }
      b++; return ' ';
    });
    t = t.replace(/#[\w-]+/g, () => { a++; return ' '; });
    t = t.replace(/\.[\w-]+/g, () => { b++; return ' '; });
    t = t.replace(/\[[^\]]*\]/g, () => { b++; return ' '; });
    t.split(/[\s>+~,]+/).forEach(p => { if (/^[a-zA-Z][\w-]*$/.test(p)) c++; });
    return [a, b, c];
  };
  const cmp = (x, y) => (x[0]-y[0]) || (x[1]-y[1]) || (x[2]-y[2]);

  const rules = [];
  for (const sheet of document.styleSheets) {
    let list; try { list = sheet.cssRules; } catch (e) { continue; }
    // NB: a plain CSSStyleRule also exposes .cssRules since CSS Nesting —
    // collect first, recurse only into non-empty children.
    const walk = (rs) => { for (const r of rs) {
      if (r.selectorText) rules.push(r);
      if (r.cssRules && r.cssRules.length) walk(r.cssRules);
    }};
    walk(list);
  }

  // Properties where a silently-lost declaration changes what the user sees.
  const WATCH = ['text-align', 'display', 'visibility', 'color',
                 'background-color', 'position', 'flex-direction',
                 'justify-content', 'align-items', 'overflow', 'width', 'height'];
  // A class whose NAME states an intent — losing one of these is the signal.
  const INTENT = /\.(empty|error|invalid|warning|success|active|selected|current|disabled|hidden|visible|open|expanded|collapsed|centered?|highlight)\b/;

  const out = [];
  const els = Array.from(document.querySelectorAll('body *'));
  for (const el of els) {
    const applies = [];
    for (const rule of rules) {
      for (const part of rule.selectorText.split(',')) {
        const s = part.trim();
        if (!s || /:(hover|active|focus|visited|target)/.test(s)) continue;
        let hit = false;
        try { hit = el.matches(s); } catch (e) { continue; }
        if (hit) applies.push({sel: s, style: rule.style, sp: spec(s)});
      }
    }
    if (applies.length < 2) continue;
    for (const prop of WATCH) {
      const decls = applies.filter(r => r.style.getPropertyValue(prop));
      if (decls.length < 2) continue;
      // winner = highest specificity; later source order breaks ties
      let win = decls[0];
      for (const d of decls.slice(1)) if (cmp(d.sp, win.sp) >= 0) win = d;
      for (const d of decls) {
        if (d === win) continue;
        const lost = d.style.getPropertyValue(prop);
        const kept = win.style.getPropertyValue(prop);
        if (lost.trim() === kept.trim()) continue;          // same value, no conflict
        if (!INTENT.test(d.sel)) continue;                  // only intent-bearing losers
        if (d.style.getPropertyPriority(prop) === 'important') continue;
        out.push({
          element: el.id ? '#' + el.id : el.tagName.toLowerCase() +
                   (el.className && typeof el.className === 'string'
                    ? '.' + el.className.trim().split(/\s+/).join('.') : ''),
          prop,
          declared: `${d.sel} { ${prop}: ${lost} }`,
          declared_specificity: d.sp.join('-'),
          overridden_by: `${win.sel} { ${prop}: ${kept} }`,
          winner_specificity: win.sp.join('-'),
          computed: getComputedStyle(el)[prop],
          text: (el.textContent || '').trim().slice(0, 60),
        });
      }
    }
  }
  return out;
}
"""


def run(target, seed_no_results=True):
    url = target if '://' in target else 'file:///' + target.replace('\\', '/')
    found = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        try:
            page = b.new_page()
            page.goto(url, wait_until='load')
            found += [dict(state='load', **f) for f in page.evaluate(JS)]
            if seed_no_results:
                el = page.query_selector('input[type=search],#search,[name=search]')
                if el:
                    el.fill('zzzzzzzz')
                    page.wait_for_timeout(250)
                    found += [dict(state='no-results', **f) for f in page.evaluate(JS)]
        finally:
            b.close()
    seen, uniq = set(), []
    for f in found:
        k = (f['element'], f['prop'], f['declared'])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(f)
    return uniq


if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), indent=2))
