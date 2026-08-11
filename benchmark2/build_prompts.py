"""Assemble the 9 pinned prompts (3 artifacts x {V, C, ground truth}).

Each prompt is self-contained: arm head + arm skill text + spec + output
contract. The runner hands an agent only the prompt path, the artifact path and
the report path, so nothing about the experiment leaks into the agent's context.
"""
import hashlib
import os
import glob
import shutil
import sys

# Round 1 used file:// with the shared-Chrome Playwright MCP; MCP blocks file:
# URLs and its Chrome is shared across concurrent sessions, so cells reached the
# page by differing ad-hoc routes and could perturb each other. Round 2 pins an
# isolated per-cell browser. Round 1 output is kept for comparison.
ROUND = sys.argv[1] if len(sys.argv) > 1 else '1'
SUFFIX = '' if ROUND == '1' else ROUND

BASE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(BASE, 'artifacts')
OUT = os.path.join(BASE, 'prompts', 'built' + SUFFIX)
RUNS = os.path.join(BASE, 'runs' + SUFFIX)
os.makedirs(OUT, exist_ok=True)


def read(*parts):
    with open(os.path.join(BASE, *parts), encoding='utf-8') as f:
        return f.read()


tail = read('prompts', 'common_tail.md')
if ROUND != '1':
    tail = read('prompts', 'browser_access.md') + tail
heads = {'V': read('prompts', 'head_V.md'), 'C': read('prompts', 'head_C.md')}
skills = {
    'V': read('arms', 'V', 'requesting-code-review.md'),
    'C': read('arms', 'C', 'web-app-evaluation.md'),
}
gt_head = read('prompts', 'ground_truth.md')

def copy_for(art, cell, src):
    """Give each cell its own copy so no arm can perturb another's page."""
    d = os.path.join(RUNS, '%s_%s' % (art, cell))
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, os.path.basename(src))
    shutil.copyfile(src, dst)
    return dst.replace('\\', '/')


built = []
for art in ('A', 'B', 'C'):
    html = [p for p in glob.glob(os.path.join(ART, art, '*.html'))]
    if len(html) != 1:
        raise SystemExit('artifact %s: expected exactly 1 html, got %r' % (art, html))
    src = html[0]
    digest = hashlib.sha256(open(src, 'rb').read()).hexdigest()[:12]
    spec = read('artifacts', art, 'spec.md')
    print('%s  %s  sha256:%s' % (art, os.path.basename(src), digest))

    for arm in ('V', 'C'):
        page = copy_for(art, arm, src)
        body = (heads[arm] + skills[arm] + '\n--- END SKILL ---\n\n'
                '--- SPEC THE PAGE WAS BUILT FROM ---\n' + spec +
                '--- END SPEC ---\n\n'
                'PAGE UNDER REVIEW: file:///' + page + '\n\n' + tail)
        p = os.path.join(OUT, '%s_%s.md' % (art, arm))
        open(p, 'w', encoding='utf-8', newline='').write(body)
        built.append(p)

    page = copy_for(art, 'GT', src)
    body = (gt_head + spec + '\n--- END SPEC ---\n\n'
            'PAGE UNDER AUDIT: file:///' + page + '\n\n' + tail)
    p = os.path.join(OUT, '%s_GT.md' % art)
    open(p, 'w', encoding='utf-8', newline='').write(body)
    built.append(p)

print()
for p in sorted(built):
    print('%-12s %6d bytes' % (os.path.basename(p), os.path.getsize(p)))
