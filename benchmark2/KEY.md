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
