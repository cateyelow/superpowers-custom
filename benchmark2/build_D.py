"""Build arm D: stock upstream superpowers + a deterministic probe pass.

Arm D is arm V with ONE difference — the machine measurements from
harness_D/probe2.py are pasted in. Same skill block, same browser instructions,
same output contract, same spec, same artifact. So any difference in score is
attributable to the probe and nothing else.

The probe is run here (not by the agent) so every D cell gets byte-identical
evidence, the same way every arm gets a byte-identical artifact.
"""
import json
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'prompts', 'built2')
RUNS = os.path.join(BASE, 'runs2')
PROBE = os.path.join(BASE, 'harness_D', 'probe2.py')

ARTIFACTS = (('A', 'upload.html'), ('B', 'checkout.html'), ('C', 'table.html'))


def rd(*parts):
    with open(os.path.join(BASE, *parts), encoding='utf-8') as f:
        return f.read()


def render(findings, notes):
    """Probe JSON -> the block a reviewer reads. Grouped by what it measured,
    with the raw numbers kept intact so every claim stays checkable."""
    by = {}
    for f in findings:
        by.setdefault(f['type'], []).append(f)
    L = []
    L.append('States the probe reached: ' + ', '.join(
        sorted({f.get('state', '?') for f in findings})) or 'load')
    if notes:
        L.append('Probe log: ' + '; '.join(notes))
    L.append('')

    txt = [f for f in by.get('contrast', []) if f['kind'] == 'text']
    if txt:
        L.append('### Text contrast below the WCAG 1.4.3 minimum')
        for f in sorted(txt, key=lambda x: x['ratio']):
            flag = '  [in a :disabled control — WCAG-exempt]' if f.get('disabled') else ''
            L.append(f"- `{f['sel']}` — {f['ratio']}:1, needs {f['need']}:1 "
                     f"(state: {f['state']}, {f['viewport']}px) text: {f['text']!r}{flag}")
        L.append('')

    bd = [f for f in by.get('contrast', []) if f['kind'] == 'boundary']
    if bd:
        L.append('### Control boundaries below the WCAG 1.4.11 3:1 minimum')
        for f in sorted(bd, key=lambda x: x['ratio']):
            flag = '  [disabled]' if f.get('disabled') else ''
            L.append(f"- `{f['sel']}` — border {f['ratio']}:1 against its backdrop "
                     f"(state: {f['state']}){flag}")
        L.append('')

    st = by.get('contrast-state', [])
    if st:
        L.append('### Styles that only apply in a state (from the CSSOM — these '
                 'never show up in getComputedStyle of the resting element)')
        for f in sorted(st, key=lambda x: x['ratio']):
            comp = f"  composites to {f['composited']}" if f.get('composited') else ''
            L.append(f"- `{f['selector']}` {{ {f['prop']}: {f['declared']} }} — "
                     f"{f['ratio']}:1, needs {f['need']}:1 — {f['note']}"
                     f" (matches {f['count']} element(s), e.g. `{f['sample']}`){comp}")
        L.append('')

    tt = by.get('touch-target', [])
    if tt:
        L.append('### Interactive elements under 44x44 CSS px')
        for f in sorted(tt, key=lambda x: min(x['w'], x['h'])):
            L.append(f"- `{f['sel']}` — {f['w']} x {f['h']} px "
                     f"({f['severity']}, state: {f['state']}, {f['viewport']}px) {f['text']!r}")
        L.append('')

    nr = by.get('name-role', [])
    if nr:
        L.append('### Accessible name / role exposure')
        for f in nr:
            L.append(f"- `{f['sel']}` — {f['issue']} {f['text']!r}")
        L.append('')

    cl = by.get('clipped-overflow', []) + by.get('page-overflow', [])
    if cl:
        L.append('### Horizontal clipping / overflow')
        for f in cl:
            if f['type'] == 'page-overflow':
                L.append(f"- the document overflows at {f['viewport']}px "
                         f"(scrollWidth {f['docWidth']} > clientWidth {f['viewWidth']})")
            else:
                L.append(f"- `{f['sel']}` scrolls horizontally at {f['viewport']}px "
                         f"(scrollWidth {f['scrollWidth']} > clientWidth {f['clientWidth']}) "
                         f"— content is off-screen unless the user scrolls sideways")
        L.append('')

    return '\n'.join(L)


# Byte-identical to arm V's head + skill (build_prompts.py assembles it the same
# way). D must differ from V in exactly one thing: the probe block.
head = (rd('prompts', 'head_V.md')
        + rd('arms', 'V', 'requesting-code-review.md')
        + '\n--- END SKILL ---\n\n')

probe_intro = rd('prompts', 'probe_block.md')
tail = rd('prompts', 'browser_access.md') + rd('prompts', 'common_tail.md')

for art, name in ARTIFACTS:
    src = os.path.join(BASE, 'artifacts', art, name)
    cell = os.path.join(RUNS, '%s_D' % art)
    os.makedirs(cell, exist_ok=True)
    dst = os.path.join(cell, name)
    shutil.copyfile(src, dst)

    raw = subprocess.run([sys.executable, PROBE, dst],
                         capture_output=True, text=True, timeout=300)
    if raw.returncode != 0:
        print('PROBE FAILED for %s:\n%s' % (art, raw.stderr[:800]))
        sys.exit(1)
    data = json.loads(raw.stdout)
    with open(os.path.join(cell, 'probe.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    block = render(data['findings'], data.get('notes', []))

    body = (head
            + '--- SPEC THE PAGE WAS BUILT FROM ---\n'
            + rd('artifacts', art, 'spec.md')
            + '--- END SPEC ---\n\n'
            + 'PAGE UNDER REVIEW: file:///' + dst.replace(os.sep, '/') + '\n\n'
            + probe_intro + block + '\n'
            + tail)
    path = os.path.join(OUT, '%s_D.md' % art)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(body)
    print('%s_D.md  %6d bytes  (%d probe findings)'
          % (art, os.path.getsize(path), len(data['findings'])))
