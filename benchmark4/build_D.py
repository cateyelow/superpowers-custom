"""Build the pipeline arm for the CLI domain.

Same shape as the two previous domains: pass 1 is arm V's finished review,
reused verbatim so the pipeline cannot lose anything V found; pass 2 reads it
together with the probe output and appends only what it reproduces itself.

The blind-spot paragraph is carried in from the probe's own output rather than
written here — in the API domain that paragraph, not the probe's findings, is
what produced the gain.
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
TOOLS = {'R': 'csvq.py', 'S': 'snap.py'}

HEAD = """# Second pass — machine experiments over a finished review

A reviewer has already reviewed this tool and written the report below. Their
pass is done and it stands. An automated probe then drove the tool: documented
exit codes, stream discipline, malformed and missing arguments, stdin versus a
named file, encoding and quoting cases, whether a failed run damages an existing
output file, and whether the tool can read back its own output.

**You are ADDING to the report, not rewriting it.** Every existing record stays
exactly as written, with its numbering. Append new records numbered onward.

## What to do

1. Read the existing report and the experiment results below.
2. For each result, decide whether it is a defect the report does NOT already
   cover. Skip anything already reported, however differently worded.
3. **Reproduce it yourself by running the tool before you add it.** Cite your
   own command, output and exit code in `repro`.
4. Append only what survives. Adding nothing is a valid outcome.

## The probe over-reports — you are the filter

It knows the spec only through a hand-written plan, so it can be wrong about
what "success" means for a given subcommand. Two known ways it misleads:

- It may flag a non-zero exit that is CORRECT (a checking subcommand is supposed
  to exit non-zero when the thing it checks is bad).
- It may flag an error-message format that the spec does not actually require in
  that position.

Check the spec yourself before accepting any record. A wrong entry costs you
more than a missed one.

"""

TAIL = """
## Output contract (follow exactly)

Write the COMPLETE report to the path given to you: every record from the
existing report above, unchanged and in its original order, followed by any
records you are adding. Use the same record shape:

```
DEFECT <n>
what: <one line — the problem, in terms of what a user experiences>
where: <file:line, or the option and code path>
repro: <the exact command YOU ran, the output, and the exit code>
severity: blocking | minor
category: spec | exit-code | stream | parsing | correctness | robustness
```

Rules:
- Do not edit, merge, renumber or delete an existing record.
- Add only defects you reproduced yourself by running the tool.
- One record per distinct defect.
- If you are adding nothing, write the existing report out unchanged.
- Work in your own scratch directory under the system temp dir; never modify
  anything in the artifact directory.
- Your final reply must be ONLY the total number of records in the file you wrote.
"""


def rd(*parts):
    with open(os.path.join(BASE, *parts), encoding='utf-8') as f:
        return f.read()


for art, tool in TOOLS.items():
    prior = os.path.join(BASE, 'reports', '%s_V.txt' % art)
    if not os.path.isfile(prior):
        print('%s: pass-1 report missing, skipped' % art)
        continue
    src = os.path.join(BASE, 'artifacts', art, tool).replace(os.sep, '/')
    body = (HEAD
            + '\n--- SPEC THE TOOL WAS BUILT FROM ---\n'
            + rd('artifacts', art, 'spec.md')
            + '--- END SPEC ---\n\n'
            + 'TOOL SOURCE: ' + src + '\n'
            + 'RUN IT AS: python ' + src + ' [options]\n\n'
            + '--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---\n'
            + rd('reports', '%s_V.txt' % art)
            + '\n--- END EXISTING REPORT ---\n\n'
            + '## Probe results\n\n'
            + rd('probe_out', '%s.md' % art)
            + '\n'
            + TAIL)
    out = os.path.join(BASE, 'prompts', '%s_D.md' % art)
    with open(out, 'w', encoding='utf-8', newline='') as f:
        f.write(body)
    n = sum(1 for line in open(prior, encoding='utf-8') if line.startswith('DEFECT '))
    print('%s_D.md  %6d bytes  (pass-1 records: %d)' % (art, os.path.getsize(out), n))
