"""Assemble the ground-truth audit prompts for benchmark3."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

for art in ('P', 'Q'):
    with open(os.path.join(BASE, 'artifacts', art, 'spec.md'), encoding='utf-8') as f:
        spec = f.read()
    with open(os.path.join(BASE, 'prompts', 'gt.md'), encoding='utf-8') as f:
        head = f.read()
    src = os.path.join(BASE, 'artifacts', art, 'app.py').replace(os.sep, '/')
    body = (head
            + '\n--- SPEC THE SERVICE WAS BUILT FROM ---\n'
            + spec
            + '--- END SPEC ---\n\n'
            + 'SERVICE SOURCE: ' + src + '\n'
            + 'ARTIFACT DIRECTORY: ' + os.path.dirname(src) + '\n')
    out = os.path.join(BASE, 'prompts', '%s_GT.md' % art)
    with open(out, 'w', encoding='utf-8', newline='') as f:
        f.write(body)
    print('%s_GT.md  %d bytes' % (art, os.path.getsize(out)))
