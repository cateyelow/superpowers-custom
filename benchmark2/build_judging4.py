"""Assemble the blind D-vs-V scoring cells (judging4).

Assignment is the one pre-registered in KEY.md before any D report was read:
  A: cand_1 = V, cand_2 = D
  B: cand_1 = D, cand_2 = V
  C: cand_1 = V, cand_2 = D
The judge is given only reference/cand_1/cand_2/page and never learns which is
which — same procedure that produced judging3.
"""
import os
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
ASSIGN = {'A': ('V', 'D'), 'B': ('D', 'V'), 'C': ('V', 'D')}
PAGES = {'A': 'upload.html', 'B': 'checkout.html', 'C': 'table.html'}

for art, (c1, c2) in ASSIGN.items():
    cell = os.path.join(BASE, 'judging4', art)
    os.makedirs(cell, exist_ok=True)
    missing = [a for a in (c1, c2)
               if not os.path.isfile(os.path.join(BASE, 'reports2', f'{art}_{a}.txt'))]
    if missing:
        print(f'{art}: SKIPPED — report(s) not written yet: {missing}')
        continue
    shutil.copyfile(os.path.join(BASE, 'reports2', f'{art}_{c1}.txt'),
                    os.path.join(cell, 'cand_1.txt'))
    shutil.copyfile(os.path.join(BASE, 'reports2', f'{art}_{c2}.txt'),
                    os.path.join(cell, 'cand_2.txt'))
    shutil.copyfile(os.path.join(BASE, 'ground_truth2', f'{art}.txt'),
                    os.path.join(cell, 'reference.txt'))
    shutil.copyfile(os.path.join(BASE, 'artifacts', art, PAGES[art]),
                    os.path.join(cell, 'page.html'))
    def records(name):
        with open(os.path.join(cell, name), encoding='utf-8') as f:
            return sum(1 for line in f if line.startswith('DEFECT '))

    n1, n2 = records('cand_1.txt'), records('cand_2.txt')
    print(f'{art}: cand_1={n1} records, cand_2={n2} records  -> {cell}')
