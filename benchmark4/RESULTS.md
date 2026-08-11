# benchmark4 — CLI tools

Third domain for the review pipeline. benchmark2 measured it on web UI,
benchmark3 on HTTP APIs; the question here is whether the method still holds
where the target is a process you invoke rather than a page you render or a
service you call.

## Protocol (identical to benchmark2/3)

1. An implementer agent built each tool from a spec it was given alone, with no
   knowledge of the benchmark.
2. A separate auditor produced the reference defect list with full source
   access and the tool runnable.
3. **arm V** — a stock-superpowers code review of the tool.
4. **arm D** — the pipeline: arm V's finished report is reused VERBATIM as pass
   1, then a second pass reads it alongside the probe output and appends only
   what it reproduces itself by running the tool.
5. A blind judge scores both against the reference, reproducing every extra
   finding before confirming it. Assignment was fixed in `KEY.md` before any
   scoring was read.

Because D reuses V's report, R1 (mean recall) and R2 (no losses) are
near-guaranteed by construction. **R3 — that D's false alarms do not exceed
V's — is the real test**, and it is the one a naive "just add a checklist"
approach fails.

## Artifacts

| | tool | what it does |
|---|---|---|
| R | `csvq.py` | CSV query/filter — select, where, order, output |
| S | `snap.py` | directory snapshot and verify |

## What this domain cost that the others did not

**The probe needed per-tool adaptation, and got the contract wrong twice.**

A web page is self-describing: every page shares one DOM contract, so one probe
runs anywhere. An HTTP API needs a hand-written `plan.json`, but the plan is
small and the verbs are standard. A CLI has neither property — what counts as
success differs *per subcommand*, so the plan has to encode the contract by
hand, and it can simply be wrong.

Two probe errors were found and fixed before any arm ran:

1. **~40 phantom defects from one broken invocation.** A path conversion made
   the interpreter unable to find the script. The probe's baseline check
   noticed and *logged* it, then carried on — so every subsequent case recorded
   "the tool failed". Fixed by aborting outright when the target does not
   respond at all.
2. **6 more from assuming exit 0 means success.** `verify` exits 1 **by
   design** when a snapshot is corrupt. The probe treated every non-zero exit
   as a defect. Fixed by moving those cases to `usage_errors` with an expected
   code.

Both are the same failure that appeared in the other two domains from different
directions — a probe that does not verify its own premises manufactures
findings. See `harness/cli_probe.py` for the recorded hazards.

## Results

### S — snap.py (reference: 6 defects)

| arm | hits | recall | confirmed extras | false alarms |
|---|---|---|---|---|
| V (superpowers alone) | 2/6 | 33.3% | 1 | 0 |
| D (pipeline)          | 4/6 | 66.7% | 2 | 0 |

Recall doubled with no rise in false alarms. The pipeline added the unvalidated
`excludes` field (`verify` certifies a snapshot that `diff` then reads as "every
file deleted"), symlink targets stored with the host separator so snapshots do
not round-trip, and — as a confirmed extra the reference itself missed — an
unlistable directory recorded as an *empty* directory, which `verify` then calls
intact.

**The probe found none of that.** Its 12 records were all stream discipline
(argparse usage text lacking the `snap: ` prefix; `verify` writing diagnostics
to stdout). Arm D adopted **zero** of them, and it was right to: the spec says
`verify` should "print what is wrong", so those diagnostics ARE the requested
report. That is the probe getting the contract wrong for the third time in this
domain.

So on S the probe's contribution to recall was **0%**, and the entire gain came
from the prompt naming the probe's blind spots:

> algorithmic correctness, whether an answer is semantically RIGHT, performance
> and large inputs, concurrent invocation, signal handling, TTY behaviour, and
> whether the help text matches the options actually implemented — if the
> existing report is thin in those areas, that is where to look; the probe
> saying nothing about them is not evidence.

This reproduces the API finding exactly, and sharpens it. Probe contribution to
recall across the three domains: web **50.6%** → API **23%** → CLI **0%**. The
method's value is not the measurement; it is that a second pass, told where the
machine cannot see, goes and looks there.

The other thing S demonstrates is that **noise placed after judgement is
harmless**: 12 wrong records produced 0 false alarms, because the reviewer had
already formed its own view and checked each claim against the spec. That is the
same ordering result as the web domain, from the opposite direction — there,
correct measurements placed *before* judgement cost recall.

### R — csvq.py (reference: 5 defects)

| arm | hits | recall | confirmed extras | false alarms |
|---|---|---|---|---|
| V (superpowers alone) | 3/5 | 60.0% | 1 | 1 |
| D (pipeline)          | 3/5 | 60.0% | 2 | 1 |

A tie on reference recall. The pipeline added one confirmed extra the reference
itself missed: `as_number()` routes every value through `float()`, so integers
past 2^53 collapse and `--where`/`--sort` silently return wrong rows with exit 0
(`id = 10000000000000000001` matched all three rows; `-s id` returned input
order). Both arms independently found the duplicate-header JSON data loss, and
both raised the same `--count`/`--limit` composition claim, which the judge
ruled a false alarm on both — the tool's own usage text documents the chosen
semantics.

**The anti-noise guidance killed a real defect.** The probe reported R3 exactly
— "a row with more fields than the header exits 2, but the spec documents 1" —
and the pipeline did not adopt it, so D missed a reference defect the machine
had handed it. The pass-2 prompt warned that "the probe may flag a non-zero exit
that is CORRECT (a checking subcommand is supposed to exit non-zero)", which was
written for S's `verify` and is right there; on R it suppressed a true finding.
Had R3 survived, D would have scored 4/5 (80%) and the domain result would have
been a clear win rather than a tie.

This is the **second** time a caveat written to suppress probe noise has
destroyed a true positive — the first was a real 38px tap-target finding in the
web domain. Both times the fix is the same: **raise probe precision, do not
write caveats around an imprecise probe.** The caveat is not free, and its cost
lands on exactly the findings the probe got right.

## Decision

| rule | | result |
|---|---|---|
| R1 | mean recall(D) > mean recall(V) | **63.4% vs 46.7%** ✓ |
| R2 | direction holds on ≥2 of 2 (no losses) | S win, R tie, **0 losses** ✓ |
| R3 | D's false alarms ≤ V's | **1 vs 1** ✓ |

All three pre-registered rules pass. The pipeline transfers to CLI tools.

## Across all three domains

| domain | V (superpowers alone) | D (pipeline) | Δ | probe's own contribution to recall |
|---|---|---|---|---|
| web UI (benchmark2) | 76.8% | **98.1%** | +21.3 | 50.6% |
| HTTP API (benchmark3) | 88.9% | **100%** | +11.1 | 23% |
| CLI (benchmark4) | 46.7% | **63.4%** | +16.7 | **0%** |

Three domains, three wins, no rise in false alarms anywhere. And the probe's own
contribution falls monotonically to zero while the gain persists — which is the
single most useful thing these three benchmarks establish. **What ports is not
the probe. What ports is running a second pass that has been told where the
first pass and the machine both cannot see.**

## Files

```
artifacts/{R,S}/     spec.md + the tool as built
ground_truth/        adjudicated reference defect lists
harness/cli_probe.py the probe + per-tool plans (plan_R.json, plan_S.json)
probe_out/           probe output handed to arm D
prompts/             judge.md, the pass-2 prompts built by build_D.py
reports/             {R,S}_{V,D}.txt
judging/{R,S}/       blinded cand_1/cand_2/reference + score.txt
KEY.md               assignment and decision rule, fixed before scoring
```
