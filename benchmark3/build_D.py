"""Build the pipeline arm for the API domain.

Same shape as benchmark2's arm D2/D3, transplanted: pass 1 is arm V's finished
review, reused verbatim so the pipeline cannot lose anything V found; pass 2
reads it together with the probe output and appends only what it reproduces
itself.

The probes are deliberately the ones written for this domain (api_probe.py +
unspecified.py). What is being tested is whether the METHOD transfers, not
whether the web probe's code does.
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

HEAD = """# Second pass — machine experiments over a finished review

A reviewer has already reviewed this service and written the report below.
Their pass is done and it stands. Two automated probes then drove the running
service: one exercising the contract it declares (boundaries, repeated terminal
actions, concurrency, error shape, unknown ids, wrong verbs) and one exercising
what the spec is silent about (injection, integer overflow, unicode and control
characters, Content-Type handling, oversized bodies).

**You are ADDING to the report, not rewriting it.** Every existing record stays
exactly as written, with its numbering. Append new records numbered onward.

## What to do

1. Read the existing report and the experiment results below.
2. For each result, decide whether it is a defect the report does NOT already
   cover. Skip anything already reported, however differently worded.
3. **Reproduce it yourself against the running service before you add it.**
   These are request sequences — reproducing means sending the requests. Cite
   your own request and response in `repro`.
4. Append only what survives. Adding nothing is a valid outcome.

## What the probes can and cannot tell you

A probe result names the invariant it broke. It is evidence, not proof, and it
over-reports in specific ways you must filter:

- `PAYLOAD` — a large body being accepted is only a defect if it actually
  threatens the service. A service that rejects oversized bodies with 413 is
  behaving correctly even if the probe records the connection closing.
- `CRASHED` — means the probe lost the connection. Confirm the service really
  died before treating it as a finding; it may have been restarted or busy.
- Anything reported as "killed the connection" deserves particular suspicion:
  distinguish a genuine crash or hang from a correct, abrupt rejection.

A probe reporting nothing does NOT mean there is nothing there. Both probes are
blind to whole classes of problem — request routing, header parsing, response
framing, HTTP method semantics, resource cleanup. If the existing report is
thin in those areas, that is your opportunity, not the probe's.

"""

TAIL = """
## Output contract (follow exactly)

Write the COMPLETE report to the path given to you: every record from the
existing report above, unchanged and in its original order, followed by any
records you are adding. Use the same record shape:

```
DEFECT <n>
what: <one line — the problem, in terms of what a client experiences>
where: <file:line, or the endpoint and the code path>
repro: <the exact request(s) YOU sent and the response(s) you got>
severity: blocking | minor
category: spec | robustness | concurrency | validation | security | error-shape
```

Rules:
- Do not edit, merge, renumber or delete an existing record.
- Add only defects you reproduced yourself against the running service.
- One record per distinct defect.
- If you are adding nothing, write the existing report out unchanged.
- Your final reply must be ONLY the total number of records in the file you wrote.
"""


def rd(*parts):
    with open(os.path.join(BASE, *parts), encoding='utf-8') as f:
        return f.read()


for art in ('P', 'Q'):
    prior = os.path.join(BASE, 'reports', '%s_V.txt' % art)
    if not os.path.isfile(prior):
        print('%s: pass-1 report missing, skipped' % art)
        continue
    src = os.path.join(BASE, 'artifacts', art, 'app.py').replace(os.sep, '/')
    body = (HEAD
            + '\n--- SPEC THE SERVICE WAS BUILT FROM ---\n'
            + rd('artifacts', art, 'spec.md')
            + '--- END SPEC ---\n\n'
            + 'SERVICE SOURCE: ' + src + '\n'
            + 'ARTIFACT DIRECTORY: ' + os.path.dirname(src) + '\n\n'
            + '--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---\n'
            + rd('reports', '%s_V.txt' % art)
            + '\n--- END EXISTING REPORT ---\n\n'
            + '## Probe results — contract experiments\n\n'
            + rd('probe_out', '%s_api.md' % art)
            + '\n\n## Probe results — unspecified-attribute experiments\n\n'
            + rd('probe_out', '%s_uns.md' % art)
            + '\n'
            + rd('prompts', 'tail_run.md').split('## Output contract')[0]
            + TAIL)
    out = os.path.join(BASE, 'prompts', '%s_D.md' % art)
    with open(out, 'w', encoding='utf-8', newline='') as f:
        f.write(body)
    n = sum(1 for line in open(prior, encoding='utf-8') if line.startswith('DEFECT '))
    print('%s_D.md  %6d bytes  (pass-1 records: %d)' % (art, os.path.getsize(out), n))
