BLIND KEY — the scoring judge must never read this file.

V = vanilla arm  (upstream v6.2.0 44c9b2d — code review skill only, no browser-evaluation skill)
C = custom arm   (fork c95fbad — web-app-evaluation blind-signoff methodology)

CANDIDATE ASSIGNMENT (fixed before any report was read; alternated to cancel
order effects):

A_upload    cand_1 = V   cand_2 = C
B_checkout  cand_1 = C   cand_2 = V
C_table     cand_1 = V   cand_2 = C

ARTIFACT HASHES (identical copy handed to every cell of that artifact)

A  upload.html    sha256:9d967c29dd05
B  checkout.html  sha256:52810a855214
C  table.html     sha256:4610583c756a

--- ARM N ADDED 2026-08-11 (the user's original question: skill present vs absent) ---

N = no superpowers skill at all (task + spec + host standing rule only)
Scored against the SAME round-2 ground truth as V and C.

N-vs-V ASSIGNMENT (fixed before any N report was read; alternated):
A_upload    cand_1 = N   cand_2 = V
B_checkout  cand_1 = V   cand_2 = N
C_table     cand_1 = N   cand_2 = V

--- ARM D ADDED 2026-08-11 (candidate harness: deterministic probe + agent) ---

D = stock upstream superpowers, byte-identical head/skill/tail to arm V, PLUS a
block of machine measurements from harness_D/probe2.py (contrast, boundaries,
CSSOM pseudo-class styles, touch targets, names/roles, clipping — measured
across every state the probe could drive the page into, at 375/768/1280).
Verified: A_D.md/B_D.md/C_D.md differ from A_V.md/B_V.md/C_V.md ONLY by that
block and the per-cell page path. Scored against the SAME round-2 ground truth.

D-vs-V ASSIGNMENT (fixed before any D report was read; alternated):
A_upload    cand_1 = V   cand_2 = D
B_checkout  cand_1 = D   cand_2 = V
C_table     cand_1 = V   cand_2 = D

DECISION RULE (frozen before scoring, extends PROTOCOL.md):
D is confirmed better than V only if ALL of:
  R1  mean recall(D) > mean recall(V)
  R2  the direction holds on at least 2 of the 3 artifacts (ties do not count
      as wins, and D must not lose any artifact it is credited for)
  R3  D's false alarms do not exceed V's
If R1-R3 do not all hold, the probe is recorded as not established and the
harness is not adopted.

--- ARM D2 ADDED 2026-08-11 (probe delivered AFTER the review, not before) ---

D2 = pass 1 is arm V's EXISTING report, reused verbatim (so D2 cannot lose a
defect V found), + pass 2 which reads that report plus the probe output and
appends only what it verifies itself. Probe precision was raised first, on the
evidence of arm D's two false alarms and its dropped R5:
  - tap targets: buttons/links judged at 44px, text fields/selects at 24px
  - per-element overflow detection removed entirely (both variants were noise)
  - :hover / :active dropped from the pseudo scan (decoration, no threshold)
  - :disabled contrast moved to an explicitly "informational, not a defect"
    section
  - added dead_css.py: declarations the author wrote that lose to a
    higher-specificity rule (this is what C-R1 actually is)
D2 costs one extra agent pass per artifact. Stated, not hidden.

D2-vs-V ASSIGNMENT (fixed before any D2 report was read; alternated):
A_upload    cand_1 = D2  cand_2 = V
B_checkout  cand_1 = V   cand_2 = D2
C_table     cand_1 = D2  cand_2 = V

DECISION RULE: identical to arm D's (R1 mean recall, R2 >=2 of 3 artifacts,
R3 false alarms not exceeding V's). D2 starts from V's report, so R1/R2 are
near-guaranteed and R3 IS THE REAL TEST: the question is whether the second
pass adds true defects without adding junk. If R3 fails, the harness fails.

--- ARM D3 ADDED 2026-08-11 (behavioural experiments as a third pass) ---

D3 = D2's report reused verbatim as passes 1-2, + a third pass fed by
harness_D/behavior_probe.py, which DRIVES the page instead of measuring it:
presses row controls mid-operation with real mousedown/mouseup, types into the
middle of formatted fields with real key events, dispatches cancelable drop
events outside the drop zone, submits invalid values, and watches whether
changes land inside a live region. It reports one record per broken invariant
(RESPONSIVE / DROP-GUARD / FOCUS / SEMANTIC / BOUNDARY / CARET / IDEMPOTENT /
ANNOUNCE / ERROR-STATE).

Motivation: all 7 defects D2 still missed are behavioural, and every one of
them turned out to be a reachable experiment rather than a judgement call.

D3-vs-D2 ASSIGNMENT (fixed before any D3 report was read; alternated):
A_upload    cand_1 = D3  cand_2 = D2
B_checkout  cand_1 = D2  cand_2 = D3
C_table     cand_1 = D3  cand_2 = D2

DECISION RULE: unchanged (R1 mean recall, R2 >=2 of 3, R3 false alarms not
exceeding the baseline). Baseline for D3 is D2, not V. D3 starts from D2's
report so it cannot lose recall; R3 is again the real test.
