"""Build the third arm: NO superpowers skill at all.

The user's original question was "superpowers present vs absent", not
"custom fork vs upstream". Arm N carries no skill block — only the task, the
spec, the host's standing browser-verification rule (which is CLAUDE.md, not
superpowers, so it must stay in every arm), and the same output contract.

Scored against the SAME round-2 ground truth as arms V and C.
"""
import os
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'prompts', 'built2')
RUNS = os.path.join(BASE, 'runs2')

ARTIFACTS = (('A', 'upload.html'), ('B', 'checkout.html'), ('C', 'table.html'))


def rd(*parts):
    with open(os.path.join(BASE, *parts), encoding='utf-8') as f:
        return f.read()


head = rd('prompts', 'head_N.md')
tail = rd('prompts', 'browser_access.md') + rd('prompts', 'common_tail.md')

for art, name in ARTIFACTS:
    src = os.path.join(BASE, 'artifacts', art, name)
    cell = os.path.join(RUNS, '%s_N' % art)
    os.makedirs(cell, exist_ok=True)
    dst = os.path.join(cell, name)
    shutil.copyfile(src, dst)

    body = (head
            + '--- SPEC THE PAGE WAS BUILT FROM ---\n'
            + rd('artifacts', art, 'spec.md')
            + '--- END SPEC ---\n\n'
            + 'PAGE UNDER REVIEW: file:///' + dst.replace(os.sep, '/') + '\n\n'
            + tail)
    path = os.path.join(OUT, '%s_N.md' % art)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(body)
    print('%s_N.md  %6d bytes  (no skill block)' % (art, os.path.getsize(path)))
