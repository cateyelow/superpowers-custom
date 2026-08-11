# benchmark3 — does the method transfer off the web?

Portability test for benchmark2. Same protocol throughout: an implementer agent
built each service from a spec it saw alone; a separate auditor produced the
reference defect list with full source access and a running service; arm V is a
stock-superpowers review; the pipeline arm reuses V's report verbatim and
appends only what a second pass reproduces itself. Assignment and decision rule
were pre-registered in KEY.md before any scoring was read.

Probes are domain-native (`harness/api_probe.py`, `harness/unspecified.py`) and
share no code with the web probes. What was under test is whether the METHOD
transfers, not the implementation.

## Result

| Artifact | GT | superpowers (V) | pipeline (D) | V false alarms | D false alarms | V extras | D extras |
|---|---|---|---|---|---|---|---|
| P inventory | 4 | 4/4 (100%) | 4/4 (100%) | 0 | 0 | 3 | **5** |
| Q booking   | 9 | 7/9 (77.8%) | **9/9 (100%)** | 1 | 1 | 0 | 1 |
| **Mean recall** | | **88.9%** | **100%** | | | | |

    R1  mean(D) > mean(V)     PASS   100% vs 88.9%, +11.1 points
    R2  D wins on 2 of 2      FAIL   1 win, 1 tie, 0 losses
    R3  D false alarms <= V   PASS   1 vs 1

**R2 fails on a rule I wrote badly, not on the result.** benchmark2's rule was
"wins on >= 2 of 3"; with only two artifacts I wrote "2 of 2", which leaves no
room for a tie. P is a tie because BOTH arms scored 4/4 — there was nothing left
to win. The honest reading is: one win, one ceiling, no losses, and on the tied
artifact the pipeline still found **5 confirmed defects the reference itself
missed, against V's 3**.

## Both domains, same protocol

| Domain | artifacts | reference defects | superpowers | pipeline | miss rate |
|---|---|---|---|---|---|
| Web UI   | 3 | 34 | 76.8% | **98.1%** | 23.2% -> 1.9% |
| HTTP API | 2 | 13 | 88.9% | **100%**  | 11.1% -> 0% |

The method transfers. The SIZE of the gain does not, and neither does the reason
for it.

## What actually differed

**Defect density and distribution.** The web artifacts averaged 11.3 reference
defects each, the APIs 6.5. More importantly the web defects clustered on two
computable axes — contrast ratio and element size — so a 200-line probe covered
half of them. API defects are spread across HTTP parsing, routing, encoding,
response framing, date handling, thread lifetime. The API probes caught **3 of
13 (23%)** versus 50.6% for the static web probe.

**Where the reviewer starts.** V scored 88.9% on the APIs and 76.8% on the web,
because API source is readable and most of its defects are visible in the code.
Web UI defects live in the rendered result: you cannot see 1.47:1 by reading
CSS. So the API had a much lower ceiling to climb — and the pipeline still
reached it.

**What produced the gain was NOT the probe.** On Q the pipeline added three
records; two matched the reference (a GET body being parsed as a pipelined
request; `%2F` decoded before routing so a URL dispatches to a different
resource). Neither probe found either one. What found them was a sentence in
the second-pass prompt:

> A probe reporting nothing does NOT mean there is nothing there. Both probes
> are blind to whole classes of problem — request routing, header parsing,
> response framing, HTTP method semantics, resource cleanup. If the existing
> report is thin in those areas, that is your opportunity.

**Naming the probe's blind spots was worth more than the probe's findings.**
That sentence was unnecessary on the web, where the probe covered half the
surface. It was the main lever here.

**Probe noise became a lead, not a cost.** The P pipeline correctly rejected
three probe over-reports (a 1 MB body is within a declared 1 MiB limit; the 8 MB
"crash" did not crash — it verified with a 200 immediately after). Then it
diagnosed WHY the probe was confused and found a real defect underneath: the
service logs a 413 but the client receives zero bytes and a connection abort,
because the socket closes with megabytes of unread body in flight. A false
alarm, investigated rather than deleted, produced a blocking defect.

## Probe bug found here, worth keeping

The first API probe run reported 20+ "defects" that were all one thing: **the
service had already died and every subsequent ConnectionRefused was recorded as
a finding.** A browser is always there; a server is not. The probe now checks
liveness before starting and after anything that might kill the target, and
never turns "nothing is listening" into a defect.

This is the mirror image of the web lesson. There, a convenience shortcut in the
experiment HID real defects. Here, not checking the target's state FABRICATED
them. Same root cause: the experiment's own environment was not verified.
