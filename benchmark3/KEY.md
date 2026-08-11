# benchmark3 (HTTP API) — blind key

Portability test for the benchmark2 web result. Same protocol: an implementer
agent built each service from a spec it was given alone; a separate auditor
produced the reference defect list with full source access and a running
service; arm V is a stock-superpowers review; the pipeline arm reuses V's report
verbatim and appends only what a second pass reproduces from probe output.

Probes are domain-native (harness/api_probe.py, harness/unspecified.py). What is
under test is whether the METHOD transfers, not the web probe's code.

ASSIGNMENT (fixed before any scoring was read; alternated):
P_inventory  cand_1 = D   cand_2 = V
Q_booking    cand_1 = V   cand_2 = D

DECISION RULE (same as benchmark2):
  R1  mean recall(D) > mean recall(V)
  R2  the direction holds on at least 2 of 2 artifacts (no losses)
  R3  D's false alarms do not exceed V's
D reuses V's report, so R1/R2 are near-guaranteed and R3 is the real test.

RECORD COUNTS BEFORE SCORING
  reference: P=4  Q=9
  arm V:     P=7  Q=8
  arm D:     P=10 Q=11
