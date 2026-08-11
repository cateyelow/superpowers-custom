"""Build arm D2: the probe delivered AFTER a free-exploration review, not before.

Arm D failed because attention is conserved — a reviewer handed measurements up
front spends its budget confirming them and stops driving the page, losing
behavioural defects (A: gained R4/R14/R15, lost R2/R5/R7, net zero).

D2 changes only WHEN the measurements arrive. Pass 1 is arm V, already run and
already scored — its report is reused verbatim, so D2 cannot lose anything V
found. Pass 2 reads that report plus the probe output and appends only what
survives its own browser verification.

Cost note: D2 spends one extra agent pass per artifact. That is the price of
the harness and is stated rather than hidden.
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
DEADCSS = os.path.join(BASE, 'harness_D', 'dead_css.py')

ARTIFACTS = (('A', 'upload.html'), ('B', 'checkout.html'), ('C', 'table.html'))


def rd(*parts):
    with open(os.path.join(BASE, *parts), encoding='utf-8') as f:
        return f.read()


def render(findings, notes, dead):
    by = {}
    for f in findings:
        by.setdefault(f['type'], []).append(f)
    L = ['States the probe reached: ' + ', '.join(
        sorted({f.get('state', 'load') for f in findings}) or ['load'])]
    if notes:
        L.append('Probe log: ' + '; '.join(notes))
    L.append('')

    live = [f for f in by.get('contrast', [])
            if f['kind'] == 'text' and not f.get('disabled')]
    if live:
        L.append('### Text contrast below the WCAG 1.4.3 minimum')
        for f in sorted(live, key=lambda x: x['ratio']):
            L.append(f"- `{f['sel']}` — {f['ratio']}:1, needs {f['need']}:1 "
                     f"(state: {f['state']}, {f['viewport']}px) text: {f['text']!r}")
        L.append('')

    bd = [f for f in by.get('contrast', [])
          if f['kind'] == 'boundary' and not f.get('disabled')]
    if bd:
        L.append('### Control boundaries below the WCAG 1.4.11 3:1 minimum')
        for f in sorted(bd, key=lambda x: x['ratio']):
            L.append(f"- `{f['sel']}` — border {f['ratio']}:1 against its backdrop "
                     f"(state: {f['state']})")
        L.append('')

    st = [f for f in by.get('contrast-state', []) if ':disabled' not in f['selector']]
    if st:
        L.append('### Focus indicators and placeholder text (pulled from the CSSOM — '
                 'these never appear in getComputedStyle of the resting element)')
        for f in sorted(st, key=lambda x: x['ratio']):
            comp = f", composites to {f['composited']}" if f.get('composited') else ''
            L.append(f"- `{f['selector']}` {{ {f['prop']}: {f['declared']} }} — "
                     f"{f['ratio']}:1, needs {f['need']}:1{comp} "
                     f"(matches {f['count']}, e.g. `{f['sample']}`)")
        L.append('')

    tt = by.get('touch-target', [])
    if tt:
        L.append('### Tap targets below the size minimum '
                 '(buttons/links judged at 44px, text fields at 24px)')
        for f in sorted(tt, key=lambda x: min(x['w'], x['h'])):
            L.append(f"- `{f['sel']}` — {f['w']} x {f['h']} px ({f['severity']}, "
                     f"state: {f['state']}, {f['viewport']}px) {f['text']!r}")
        L.append('')

    nr = by.get('name-role', [])
    if nr:
        L.append('### Accessible name / role exposure')
        for f in nr:
            L.append(f"- `{f['sel']}` — {f['issue']} {f['text']!r}")
        L.append('')

    po = by.get('page-overflow', [])
    if po:
        L.append('### Document-level horizontal overflow')
        for f in po:
            L.append(f"- at {f['viewport']}px the document scrolls sideways "
                     f"(scrollWidth {f['docWidth']} > clientWidth {f['viewWidth']})")
        L.append('')

    if dead:
        L.append('### Declarations the author wrote that never take effect '
                 '(CSS specificity conflicts)')
        for f in dead:
            L.append(f"- `{f['element']}` [{f['state']}] — author wrote "
                     f"`{f['declared']}` (specificity {f['declared_specificity']}) "
                     f"but `{f['overridden_by']}` (specificity "
                     f"{f['winner_specificity']}) wins; computed value is "
                     f"`{f['computed']}`. Element text: {f['text']!r}")
        L.append('')

    dis = ([f for f in by.get('contrast', []) if f.get('disabled')]
           + [f for f in by.get('contrast-state', []) if ':disabled' in f['selector']])
    if dis:
        L.append('### Informational only — contrast inside disabled controls')
        L.append('WCAG exempts inactive controls, so these are NOT defects by '
                 'default. One is worth reporting only if that disabled state is '
                 "the page's resting state AND its text carries something the "
                 'user needs to read (a status or progress message).')
        for f in dis:
            who = f.get('sel') or f.get('selector')
            L.append(f"- `{who}` — {f['ratio']}:1 {f.get('text', '')!r}")
        L.append('')

    return '\n'.join(L)


for art, name in ARTIFACTS:
    prior = os.path.join(BASE, 'reports2', '%s_V.txt' % art)
    if not os.path.isfile(prior):
        raise SystemExit('missing pass-1 report: %s' % prior)

    cell = os.path.join(RUNS, '%s_D2' % art)
    os.makedirs(cell, exist_ok=True)
    dst = os.path.join(cell, name)
    shutil.copyfile(os.path.join(BASE, 'artifacts', art, name), dst)

    pr = subprocess.run([sys.executable, PROBE, dst],
                        capture_output=True, text=True, timeout=300)
    dc = subprocess.run([sys.executable, DEADCSS, dst],
                        capture_output=True, text=True, timeout=300)
    if pr.returncode or dc.returncode:
        raise SystemExit('probe failed for %s:\n%s%s' % (art, pr.stderr[:500], dc.stderr[:500]))
    data = json.loads(pr.stdout)
    dead = json.loads(dc.stdout)
    with open(os.path.join(cell, 'probe.json'), 'w', encoding='utf-8') as f:
        json.dump({'probe': data, 'dead_css': dead}, f, indent=2)

    body = (rd('prompts', 'head_D2.md')
            + '\n--- SPEC THE PAGE WAS BUILT FROM ---\n'
            + rd('artifacts', art, 'spec.md')
            + '--- END SPEC ---\n\n'
            + 'PAGE UNDER REVIEW: file:///' + dst.replace(os.sep, '/') + '\n\n'
            + '--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---\n'
            + rd('reports2', '%s_V.txt' % art)
            + '\n--- END EXISTING REPORT ---\n\n'
            + '## Probe output\n\n'
            + render(data['findings'], data.get('notes', []), dead)
            + '\n' + rd('prompts', 'browser_access.md')
            + '## Output contract (follow exactly)\n\n'
            + 'Write the COMPLETE report to the path given to you: every record '
            + 'from the existing report above, unchanged and in its original '
            + 'order, followed by any records you are adding. Use the same '
            + 'record shape:\n\n```\nDEFECT <n>\nwhat: <one line — the '
            + 'user-visible problem>\nwhere: <file:line, or a CSS selector / '
            + 'element description>\nrepro: <how YOU observed it — the steps or '
            + 'the measurement>\nseverity: blocking | minor\ncategory: a11y | '
            + 'contrast | touch-target | responsive | state | logic | spec\n```\n\n'
            + 'Rules:\n- Do not edit, merge, renumber or delete an existing '
            + 'record.\n- Add only defects you verified yourself in the browser.\n'
            + '- One record per distinct defect.\n- If you are adding nothing, '
            + 'write the existing report out unchanged.\n- Your final reply to me '
            + 'must be ONLY the total number of records in the file you wrote.\n')

    path = os.path.join(OUT, '%s_D2.md' % art)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(body)
    n_prior = sum(1 for line in open(prior, encoding='utf-8')
                  if line.startswith('DEFECT '))
    print('%s_D2.md  %6d bytes  (pass-1 records: %d, probe: %d, dead-css: %d)'
          % (art, os.path.getsize(path), n_prior, len(data['findings']), len(dead)))
