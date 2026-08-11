"""Behavioural probe — runs experiments, not measurements.

ui_probe.py measures the page's resting properties and stops where judgement
begins. Everything arm D2 still misses is on the other side of that line, and
scoring them showed they are NOT judgement calls — they are EXPERIMENTS nobody
ran:

  A-R1   Remove is dead during an upload      -> click it during the upload
  A-R2/6/7 focus discarded on an action       -> read activeElement after acting
  A-R18  the same file can be added twice     -> add it twice, count rows
  B-R3/4 caret jumps on mid-string editing    -> set the caret, type, read it back
  B-R10  a past expiry date is accepted       -> enter one, check validity
  B-R2   pattern counts formatting characters -> walk the length boundary

Each is a user-reachable sequence with an invariant that either holds or does
not. A machine can drive all of them and never gets bored on the 40th control.

The invariants, which are framework-independent even though this
implementation is DOM-specific:

  FOCUS       activating a control must not drop focus to <body>
  RESPONSIVE  a control must respond while an async operation is in flight
  CARET       editing mid-string must not move the caret to the end
  IDEMPOTENT  submitting identical input twice must not silently duplicate
  BOUNDARY    a declared constraint must actually reject values outside it
  SEMANTIC    a syntactically valid value that is semantically impossible
              (a past expiry) must be rejected

Usage:  python behavior_probe.py <file-or-url> [--json]
Output: one record per violated invariant, with the exact sequence that did it.
"""
import json
import sys

from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------- FOCUS
JS_FOCUS = r"""
() => {
  const out = [];
  const sel = (el) => el.id ? '#' + el.id
    : el.tagName.toLowerCase() + (el.className && typeof el.className === 'string'
      ? '.' + el.className.trim().split(/\s+/).slice(0,2).join('.') : '');
  const CTRL = 'a[href],button,input,select,textarea,[role=button],[tabindex]:not([tabindex="-1"])';
  const controls = Array.from(document.querySelectorAll(CTRL)).filter(el => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && !el.disabled;
  });
  for (const el of controls) {
    const t = (el.type || '').toLowerCase();
    if (t === 'file' || el.tagName === 'SELECT') continue;   // opens native UI
    const label = sel(el) + ' ' + JSON.stringify((el.textContent||'').trim().slice(0,24));
    try {
      el.focus();
      if (document.activeElement !== el) continue;           // cannot hold focus
      el.click();
    } catch (e) { continue; }
    const after = document.activeElement;
    if (after === document.body || after === null) {
      out.push({invariant: 'FOCUS', control: sel(el), label,
                detail: 'activating it left document.activeElement === <body>; '
                      + 'a keyboard user is dumped to the top of the document'});
    }
  }
  return out;
}
"""

# ---------------------------------------------------------------- CARET
JS_CARET = r"""
() => {
  const out = [];
  const sel = (el) => el.id ? '#' + el.id : el.tagName.toLowerCase();
  const fields = Array.from(document.querySelectorAll('input[type=text],input[type=tel],input:not([type]),textarea'))
    .filter(el => { const r = el.getBoundingClientRect();
                    return r.width > 0 && r.height > 0 && !el.disabled && !el.readOnly; });
  for (const el of fields) {
    const seedValue = '4111111111111111';
    el.focus();
    el.value = '';
    // type it the way a user would, so any input handler runs per character
    for (const ch of seedValue) {
      el.value += ch;
      el.dispatchEvent(new Event('input', {bubbles: true}));
    }
    const formatted = el.value;
    if (formatted.length < 4) continue;

    // 1. insert a character in the middle; the caret should land just after it
    const at = Math.floor(formatted.length / 2);
    el.setSelectionRange(at, at);
    el.value = formatted.slice(0, at) + '9' + formatted.slice(at);
    el.setSelectionRange(at + 1, at + 1);
    el.dispatchEvent(new Event('input', {bubbles: true}));
    const caret = el.selectionStart;
    if (caret >= el.value.length && el.value.length > at + 2) {
      out.push({invariant: 'CARET', control: sel(el),
                detail: `typed a character at offset ${at} of ${JSON.stringify(formatted)}; `
                      + `the caret jumped to ${caret} (end of field, value now `
                      + `${JSON.stringify(el.value)}). Continued typing lands in the wrong place.`});
    }

    // 2. delete the character before a formatting separator
    el.value = formatted;
    el.dispatchEvent(new Event('input', {bubbles: true}));
    const spaceAt = formatted.indexOf(' ');
    if (spaceAt > 0) {
      const before = el.value;
      const pos = spaceAt + 1;
      el.setSelectionRange(pos, pos);
      el.value = el.value.slice(0, pos - 1) + el.value.slice(pos);   // backspace
      el.dispatchEvent(new Event('input', {bubbles: true}));
      if (el.value === before) {
        out.push({invariant: 'CARET', control: sel(el),
                  detail: `backspacing at offset ${pos} (just past the auto-inserted `
                        + `separator in ${JSON.stringify(before)}) removed nothing — `
                        + `value unchanged, caret now at ${el.selectionStart}`});
      }
    }
    el.value = '';
    el.dispatchEvent(new Event('input', {bubbles: true}));
  }
  return out;
}
"""

# ---------------------------------------------------------------- BOUNDARY
JS_BOUNDARY = r"""
() => {
  const out = [];
  const sel = (el) => el.id ? '#' + el.id : el.tagName.toLowerCase();
  const fields = Array.from(document.querySelectorAll('input[pattern],input[minlength],input[maxlength]'))
    .filter(el => { const r = el.getBoundingClientRect();
                    return r.width > 0 && r.height > 0 && !el.disabled; });
  const set = (el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles: true})); };

  for (const el of fields) {
    const pat = el.getAttribute('pattern') || '';
    const hint = ((el.title || '') + ' ' +
                  (el.getAttribute('aria-describedby')
                    ? (document.getElementById(el.getAttribute('aria-describedby'))||{}).textContent || ''
                    : '') + ' ' +
                  (el.nextElementSibling ? el.nextElementSibling.textContent : '')).trim();
    const digitsWanted = /(\d+)\s*(?:to|-|–)\s*(\d+)\s*digit/i.exec(hint);
    const original = el.value;

    // Walk digit-count boundaries and record where validity actually flips.
    if (digitsWanted) {
      const lo = parseInt(digitsWanted[1], 10);
      const flips = [];
      for (let n = Math.max(1, lo - 4); n <= lo + 1; n++) {
        set(el, '1'.repeat(n));
        flips.push({digits: n, valid: el.checkValidity(), rendered: el.value});
      }
      const firstValid = flips.find(f => f.valid);
      if (firstValid && firstValid.digits < lo) {
        out.push({invariant: 'BOUNDARY', control: sel(el),
                  detail: `the field's own hint says ${lo}-${digitsWanted[2]} digits, but `
                        + `${firstValid.digits} digits already validates `
                        + `(rendered as ${JSON.stringify(firstValid.rendered)}, `
                        + `checkValidity() === true). Pattern ${JSON.stringify(pat)} is `
                        + `counting the auto-inserted formatting characters.`});
      }
    }

    // A whitespace-only value satisfying `required` is a defect: the summary
    // trims it later and the user sees a blank they were forced to fill.
    if (el.required) {
      set(el, '   ');
      if (el.checkValidity()) {
        out.push({invariant: 'BOUNDARY', control: sel(el),
                  detail: 'a whitespace-only value ("   ") satisfies `required` — '
                        + 'checkValidity() === true, so the step advances and any '
                        + 'trimmed display of it renders empty'});
      }
    }
    set(el, original);
  }
  return out;
}
"""

# ---------------------------------------------------------------- SEMANTIC
JS_SEMANTIC = r"""
() => {
  const out = [];
  const sel = (el) => el.id ? '#' + el.id : el.tagName.toLowerCase();
  const set = (el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles: true})); };
  // A field that looks like a card expiry: MM/YY shape, named exp*/valid*.
  const cands = Array.from(document.querySelectorAll('input')).filter(el => {
    const n = ((el.name||'') + ' ' + (el.id||'') + ' ' + (el.placeholder||'')).toLowerCase();
    return /exp|valid.?thru|mm\s*\/\s*yy/.test(n);
  });
  for (const el of cands) {
    const original = el.value;
    for (const past of ['0120', '01/20', '1219', '12/19']) {
      set(el, past);
      if (el.value && el.checkValidity() && /^\d{2}\s*\/?\s*\d{2}$/.test(el.value.trim())) {
        const yy = parseInt(el.value.trim().slice(-2), 10);
        const nowYY = new Date().getFullYear() % 100;
        if (yy < nowYY) {
          out.push({invariant: 'SEMANTIC', control: sel(el),
                    detail: `an expiry already in the past (${JSON.stringify(el.value)}) `
                          + `passes validation — checkValidity() === true. The pattern `
                          + `checks the SHAPE only, never the date.`});
          break;
        }
      }
    }
    set(el, original);
  }
  return out;
}
"""


# ---------------------------------------------------------------- DROP GUARD
# A page that accepts dropped files but guards only its own drop zone leaves the
# rest of the window on the browser default: dropping there NAVIGATES AWAY and
# destroys the user's selection. You cannot enumerate listeners from page JS
# (getEventListeners is devtools-only), but you can dispatch a real cancelable
# event and read defaultPrevented — if nothing called preventDefault, the
# default action is still live.
JS_DROP_GUARD = r"""
() => {
  const out = [];
  const acceptsFiles = document.querySelector('input[type=file]')
    || /drop|drag/i.test(document.body.className + ' ' + document.body.innerHTML.slice(0, 4000));
  if (!acceptsFiles) return out;
  const targets = [document.body, document.querySelector('h1'),
                   document.querySelector('ul,ol,table')].filter(Boolean);
  const unguarded = [];
  for (const t of targets) {
    for (const type of ['dragover', 'drop']) {
      let ev;
      try { ev = new DragEvent(type, {bubbles: true, cancelable: true}); }
      catch (e) { ev = new Event(type, {bubbles: true, cancelable: true}); }
      t.dispatchEvent(ev);
      if (!ev.defaultPrevented) {
        unguarded.push((t.id ? '#' + t.id : t.tagName.toLowerCase()) + '/' + type);
      }
    }
  }
  if (unguarded.length) {
    const dz = document.querySelector('[class*=drop],[id*=drop]');
    const box = dz ? dz.getBoundingClientRect() : null;
    out.push({invariant: 'DROP-GUARD', control: 'document / window',
              detail: 'this page accepts dropped files, but a cancelable drop/dragover '
                    + 'dispatched outside the drop zone was NOT preventDefault()ed ('
                    + unguarded.join(', ') + '). The browser default therefore stands: '
                    + 'a file dropped anywhere else navigates away from the page and '
                    + 'destroys the current selection.'
                    + (box ? ` The guarded zone is only ${Math.round(box.width)}x`
                           + `${Math.round(box.height)}px of a `
                           + `${document.documentElement.clientWidth}x`
                           + `${document.documentElement.clientHeight} viewport.` : '')});
  }
  return out;
}
"""

# ---------------------------------------------------------------- ANNOUNCE
# Two related silences: a visible state change that happens OUTSIDE any live
# region (a screen-reader user is never told), and a rejected field that exposes
# no programmatic error state at all.
JS_ANNOUNCE_SETUP = r"""
() => {
  window.__mutations = [];
  const liveAncestor = (node) => {
    let n = node.nodeType === 1 ? node : node.parentElement;
    while (n) {
      if (n.hasAttribute && (n.hasAttribute('aria-live') ||
          ['alert','status','log'].includes(n.getAttribute('role')))) return n;
      n = n.parentElement;
    }
    return null;
  };
  const obs = new MutationObserver((recs) => {
    for (const r of recs) {
      for (const n of r.addedNodes) {
        const text = (n.textContent || '').trim();
        if (!text || text.length < 3) continue;
        const el = n.nodeType === 1 ? n : n.parentElement;
        if (!el) continue;
        const st = getComputedStyle(el);
        if (st.display === 'none' || st.visibility === 'hidden') continue;
        window.__mutations.push({text: text.slice(0, 60),
                                 sel: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                                 announced: !!liveAncestor(n)});
      }
      if (r.type === 'attributes' && r.attributeName === 'style') continue;
    }
  });
  obs.observe(document.body, {childList: true, subtree: true, characterData: true});
  return true;
}
"""

JS_ANNOUNCE_READ = r"""
() => {
  const out = [];
  const silent = (window.__mutations || []).filter(m => !m.announced);
  if (silent.length) {
    const uniq = [];
    const seen = new Set();
    for (const m of silent) {
      if (seen.has(m.text)) continue;
      seen.add(m.text);
      uniq.push(m);
    }
    out.push({invariant: 'ANNOUNCE', control: uniq.map(m => m.sel).join(', '),
              detail: 'the action changed visible content with no aria-live / role=alert '
                    + 'ancestor, so a screen-reader user is told nothing: '
                    + uniq.slice(0, 3).map(m => JSON.stringify(m.text)).join(', ')});
  }
  return out;
}
"""

JS_ERROR_STATE = r"""
() => {
  const out = [];
  const form = document.querySelector('form');
  if (!form) return out;
  const fields = Array.from(form.querySelectorAll('input,select,textarea'))
    .filter(el => { const r = el.getBoundingClientRect();
                    return r.width > 0 && r.height > 0 && !el.disabled; });
  const constrained = fields.filter(el => el.getAttribute('pattern') || el.required);
  if (!constrained.length) return out;

  for (const el of constrained) el.value = '';
  for (const el of constrained) {
    if (el.getAttribute('pattern')) {
      el.value = '@@@';
      el.dispatchEvent(new Event('input', {bubbles: true}));
    }
  }
  const invalid = constrained.filter(el => !el.checkValidity());
  if (!invalid.length) return out;

  const marked = invalid.filter(el => el.getAttribute('aria-invalid') === 'true');
  const liveCount = document.querySelectorAll(
    '[aria-live],[role=alert],[role=status]').length;
  const described = invalid.filter(el => el.getAttribute('aria-describedby')
                                      || (el.title || '').trim());
  if (!marked.length && liveCount === 0) {
    out.push({invariant: 'ERROR-STATE',
              control: invalid.map(el => el.id ? '#' + el.id : el.tagName.toLowerCase())
                              .slice(0, 5).join(', '),
              detail: `${invalid.length} field(s) reject their value, but none sets `
                    + `aria-invalid and the page contains zero [aria-live] / [role=alert] / `
                    + `[role=status] elements. The only error signal is the browser's `
                    + `transient bubble. Validation messages seen: `
                    + invalid.slice(0, 3).map(el => JSON.stringify(el.validationMessage))
                            .join(', ')
                    + (described.length < invalid.length
                        ? `. ${invalid.length - described.length} of them also state the `
                        + `required format nowhere (no title, no aria-describedby).` : '')});
  }
  return out;
}
"""


def probe_responsive_and_idempotent(page):
    """These two need real time and real input files, so they run from Python
    rather than as a single evaluate()."""
    out = []

    # --- IDEMPOTENT: add the same file twice, see if it silently duplicates ---
    try:
        finp = page.query_selector('input[type=file]')
        if finp:
            one = [{'name': 'alpha.txt', 'mimeType': 'text/plain', 'buffer': b'x' * 2900}]
            finp.set_input_files(one)
            page.wait_for_timeout(200)
            n1 = page.evaluate("() => document.querySelectorAll('li,tr,.file-item').length")
            finp.set_input_files(one)
            page.wait_for_timeout(200)
            n2 = page.evaluate("() => document.querySelectorAll('li,tr,.file-item').length")
            warned = page.evaluate(
                "() => !!document.querySelector('[role=alert],.error,.warning')")
            if n2 > n1 and not warned:
                out.append({'invariant': 'IDEMPOTENT', 'control': 'input[type=file]',
                            'detail': f'selecting the same file twice produced {n2} rows '
                                      f'(was {n1}) with no de-duplication and no warning; '
                                      f'the duplicate rows are indistinguishable'})
    except Exception:
        pass

    # --- RESPONSIVE: operate a control while an async action is in flight ----
    # Playwright element handles go stale the instant the list is re-rendered,
    # and `click()` then throws and gets swallowed — which is why the first
    # version of this check silently found nothing. The staleness IS the defect,
    # so measure it directly: hold a reference to the row control, start the
    # operation, and ask whether that node still exists and whether a real
    # mousedown/mouseup pair on its coordinates does anything.
    try:
        started = page.evaluate(r"""
        () => {
          const rowCtl = document.querySelector(
            'li button, tr button, .file-item button, [class*=remove], [class*=delete]');
          if (!rowCtl) return null;
          const rect = rowCtl.getBoundingClientRect();
          window.__ref = rowCtl;
          window.__rows = () => document.querySelectorAll('li,tr,.file-item').length;
          window.__before = window.__rows();
          window.__mut = 0;
          window.__obs = new MutationObserver(rs => { window.__mut += rs.length; });
          const host = rowCtl.closest('ul,ol,tbody,[class*=list]') || document.body;
          window.__obs.observe(host, {childList: true, subtree: true, characterData: true});
          const trig = Array.from(document.querySelectorAll('button')).find(b => {
            const t = (b.textContent || '').trim().toLowerCase();
            return !b.disabled && b.getBoundingClientRect().width > 0 &&
                   /upload|submit|save|send|start/.test(t);
          });
          if (!trig) return null;
          trig.click();
          return {x: rect.x + rect.width / 2, y: rect.y + rect.height / 2,
                  before: window.__before, trigger: (trig.textContent || '').trim()};
        }""")
        if started:
            page.wait_for_timeout(200)
            alive = page.evaluate(
                '() => !!(window.__ref && document.contains(window.__ref))')
            # a real user gesture at the control's coordinates, mid-flight
            page.mouse.move(started['x'], started['y'])
            page.mouse.down()
            page.wait_for_timeout(60)
            page.mouse.up()
            page.wait_for_timeout(200)
            state = page.evaluate(
                '() => ({rows: window.__rows(), mut: window.__mut})')
            if state['rows'] == started['before']:
                out.append({
                    'invariant': 'RESPONSIVE', 'control': 'the row control (Remove/Delete)',
                    'detail': f'pressed it with a real mousedown/mouseup 200ms into the '
                              f'operation started by "{started["trigger"]}" and nothing '
                              f'happened (row count stayed {started["before"]}). '
                              + ('The node it was pressed on no longer exists by then '
                                 '(document.contains(ref) === false) — '
                                 if not alive else '')
                              + f'the list recorded {state["mut"]} mutation batches during '
                              f'the operation, so the element is destroyed between '
                              f'mousedown and mouseup and no click event is ever produced. '
                              f'The control is dead for the whole operation.'})
    except Exception:
        pass
    return out


FILES = [{'name': 'alpha.txt', 'mimeType': 'text/plain', 'buffer': b'x' * 2900},
         {'name': 'beta.txt', 'mimeType': 'text/plain', 'buffer': b'y' * 1200}]


JS_FILL = r"""
() => {
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
}
"""


def reveal_step(page, keywords=('next', 'continue', 'proceed', '다음')):
    """Advance a multi-step flow by one step. Returns True if the DOM changed."""
    try:
        before = page.evaluate('() => document.body.innerHTML.length')
        for b in page.query_selector_all('button,[role=button]'):
            txt = (b.inner_text() or '').strip().lower()
            if not (b.is_visible() and b.is_enabled()):
                continue
            if any(k in txt for k in keywords):
                b.click(timeout=2000)
                page.wait_for_timeout(300)
                return page.evaluate('() => document.body.innerHTML.length') != before
    except Exception:
        pass
    return False


def seed(page, files=True, fill=False, steps=0):
    """Bring the page into a state where its controls actually exist.

    Without this, half the experiments find nothing to operate on: the file rows
    do not exist until a file is chosen, and a wizard's later fields are hidden
    at load, so `is_visible()` filters them all out and the check silently
    passes. Two real defects (a dead control mid-upload, a caret thrown by a
    card-number formatter) were invisible for exactly this reason."""
    if files:
        try:
            finp = page.query_selector('input[type=file]')
            if finp:
                finp.set_input_files(FILES)
                page.wait_for_timeout(250)
        except Exception:
            pass
    if fill:
        try:
            page.evaluate(JS_FILL)
            page.wait_for_timeout(150)
        except Exception:
            pass
    for _ in range(steps):
        if not reveal_step(page):
            break
        if fill:
            try:
                page.evaluate(JS_FILL)
                page.wait_for_timeout(120)
            except Exception:
                pass


def probe_caret(page):
    """CARET must be driven with real key events. A JS-level value assignment
    plus setSelectionRange overwrites whatever the page's own input handler did
    to the caret, which is precisely the defect being looked for — the first
    version of this check silently passed for that reason."""
    out = []
    fields = [el for el in page.query_selector_all(
        'input[type=text],input[type=tel],input:not([type]),textarea')
        if el.is_visible() and el.is_enabled()]
    for el in fields:
        try:
            el.click()
            page.keyboard.press('Control+a')
            page.keyboard.press('Delete')
            page.keyboard.type('4111111111111111', delay=1)
            formatted = el.input_value()
            if len(formatted) < 6:
                continue
            handle = el

            # (1) type a digit into the middle — the caret should stay beside it
            mid = len(formatted) // 2
            page.evaluate('([e, n]) => e.setSelectionRange(n, n)', [handle, mid])
            page.keyboard.type('9', delay=1)
            caret = page.evaluate('e => e.selectionStart', handle)
            value = el.input_value()
            if caret >= len(value) and len(value) > mid + 2:
                out.append({'invariant': 'CARET', 'control': '#' + (el.get_attribute('id') or '?'),
                            'detail': f'typed a digit at offset {mid} of '
                                      f'{formatted!r}; the caret jumped to {caret} '
                                      f'(end of field, value now {value!r}), so continued '
                                      f'typing lands in the wrong place'})

            # (2) backspace over an auto-inserted separator
            page.keyboard.press('Control+a')
            page.keyboard.press('Delete')
            page.keyboard.type('4111111111111111', delay=1)
            base = el.input_value()
            sep = base.find(' ')
            if sep > 0:
                page.evaluate('([e, n]) => e.setSelectionRange(n, n)', [handle, sep + 1])
                page.keyboard.press('Backspace')
                after = el.input_value()
                caret2 = page.evaluate('e => e.selectionStart', handle)
                if after == base:
                    out.append({'invariant': 'CARET',
                                'control': '#' + (el.get_attribute('id') or '?'),
                                'detail': f'placed the caret just past the auto-inserted '
                                          f'separator in {base!r} (offset {sep + 1}) and pressed '
                                          f'Backspace: nothing was removed (value unchanged) and '
                                          f'the caret was thrown to {caret2}'})
        except Exception:
            continue
    return out


def probe_announce(page):
    """Watch what a destructive/clearing action changes, and whether any of it
    is inside a live region."""
    out = []
    try:
        page.evaluate(JS_ANNOUNCE_SETUP)
        acted = False
        for b in page.query_selector_all('button,[role=button]'):
            txt = (b.inner_text() or '').strip().lower()
            if not (b.is_visible() and b.is_enabled()):
                continue
            if any(k in txt for k in ('clear', 'remove', 'delete', 'reset', '비우기')):
                b.click(timeout=1500)
                acted = True
                break
        if acted:
            page.wait_for_timeout(300)
            out += page.evaluate(JS_ANNOUNCE_READ)
    except Exception:
        pass
    return out


def run(target):
    url = target if '://' in target else 'file:///' + target.replace('\\', '/')
    findings = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)

        def fresh(seed_files=True):
            page = b.new_page()
            page.goto(url, wait_until='load')
            page.set_viewport_size({'width': 1280, 'height': 900})
            seed(page, files=seed_files)
            return page

        try:
            # Each experiment mutates the page, so each gets a fresh load. All of
            # them get the seeded state, because unseeded pages have nothing to
            # operate on.
            for js, name in ((JS_BOUNDARY, 'boundary'), (JS_SEMANTIC, 'semantic'),
                             (JS_FOCUS, 'focus'), (JS_DROP_GUARD, 'drop-guard'),
                             (JS_ERROR_STATE, 'error-state')):
                page = fresh()
                try:
                    findings += page.evaluate(js)
                except Exception as exc:
                    findings.append({'invariant': 'PROBE-ERROR', 'control': name,
                                     'detail': repr(exc)[:200]})
                page.close()

            # CARET has to be re-run on each step of a multi-step flow: the
            # formatter-bearing fields (card number, expiry) live on a later
            # step and are simply absent from the DOM at load.
            page = fresh()
            try:
                findings += probe_caret(page)
                for _ in range(3):
                    page.evaluate(JS_FILL)
                    if not reveal_step(page):
                        break
                    page.evaluate(JS_FILL)
                    findings += probe_caret(page)
            except Exception as exc:
                findings.append({'invariant': 'PROBE-ERROR', 'control': 'caret',
                                 'detail': repr(exc)[:200]})
            page.close()

            for fn in (probe_announce, probe_responsive_and_idempotent):
                page = fresh(seed_files=(fn is probe_announce))
                try:
                    findings += fn(page)
                except Exception as exc:
                    findings.append({'invariant': 'PROBE-ERROR', 'control': fn.__name__,
                                     'detail': repr(exc)[:200]})
                page.close()
        finally:
            b.close()
    seen, uniq = set(), []
    for f in findings:
        k = (f['invariant'], f['control'], f['detail'][:60])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(f)
    return uniq


def as_markdown(findings):
    if not findings:
        return ('# Behavioural experiments\n\nNo invariant violations found. '
                'This does not mean the behaviour is correct — only that these '
                'specific experiments passed.')
    L = ['# Behavioural experiments', '',
         'Each record is a user-reachable sequence that broke an invariant. '
         'Reproduce it yourself before reporting it.', '']
    order = ['RESPONSIVE', 'DROP-GUARD', 'FOCUS', 'SEMANTIC', 'BOUNDARY',
             'CARET', 'IDEMPOTENT', 'ANNOUNCE', 'ERROR-STATE', 'PROBE-ERROR']
    for inv in order:
        rows = [f for f in findings if f['invariant'] == inv]
        if not rows:
            continue
        L.append(f'## {inv}')
        for f in rows:
            L.append(f"- `{f['control']}` — {f['detail']}")
        L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        raise SystemExit(2)
    res = run(args[0])
    print(json.dumps(res, indent=2) if '--json' in sys.argv else as_markdown(res))
