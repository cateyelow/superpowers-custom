# benchmark4 (CLI tools) — blind key

Third domain. Same protocol as benchmark2 (web UI) and benchmark3 (HTTP API):
an implementer agent built each tool from a spec it was given alone; a separate
auditor produced the reference defect list with full source access and the tool
runnable; arm V is a stock-superpowers review; the pipeline arm reuses V's
report verbatim and appends only what a second pass reproduces by running the
tool itself.

The probe is domain-native (harness/cli_probe.py + a hand-written plan per
tool). What is under test is whether the METHOD transfers, not the code of the
web or API probes.

ARTIFACTS
  R  csvq.py  — a CSV query/filter tool (spec: artifacts/R/spec.md)
  S  snap.py  — a directory snapshot/verify tool (spec: artifacts/S/spec.md)

ASSIGNMENT (fixed before any scoring was read; alternated as in benchmark3):
  R_csvq  cand_1 = D   cand_2 = V
  S_snap  cand_1 = V   cand_2 = D

DECISION RULE (unchanged from benchmark2/3):
  R1  mean recall(D) > mean recall(V)
  R2  the direction holds on at least 2 of 2 artifacts (no losses)
  R3  D's false alarms do not exceed V's
D reuses V's report, so R1/R2 are near-guaranteed and R3 is the real test.

DOMAIN-SPECIFIC NOTE RECORDED IN ADVANCE
The CLI probe needed more per-tool adaptation than either earlier domain: what
counts as success differs per subcommand (a verify subcommand exits non-zero by
design), so the probe plan encodes the contract by hand and can be wrong about
it. Two probe errors were found and fixed before any arm ran — an unlaunchable
interpreter path producing ~40 phantom defects, and 6 more from treating a
correct non-zero exit as a failure. Both are recorded in harness/cli_probe.py.

RECORD COUNTS BEFORE SCORING
  reference: R=5  S=6
  arm V:     R=5  S=3
  arm D:     R=6  S=6

SCORING (blind judge, judging/*/score.txt) — unsealed after the fact
  R  D 3/5, 2 confirmed extras, 1 false alarm  |  V 3/5, 1 extra, 1 false alarm
  S  D 4/6, 2 confirmed extras, 0 false alarms |  V 2/6, 1 extra, 0 false alarms
  R1 63.4% vs 46.7% PASS | R2 0 losses PASS | R3 1 vs 1 PASS
