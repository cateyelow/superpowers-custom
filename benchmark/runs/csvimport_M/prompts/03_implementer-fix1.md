The Codex spec compliance review of your Task 1 implementation returned NEEDS_FIXES with exactly one issue. Fix it now.

## Review Finding (verbatim)

status: NEEDS_FIXES
missing: [R1 exact header set is not enforced; headers with extra columns are accepted]
extra: [Extra CSV columns are tolerated and ignored, which is outside the requested exact set]
misunderstandings: [R1 "exact set, any order" was implemented as "required columns present, extra columns allowed"]
details: [src/parser.js:135 trims and reads header fields, src/parser.js:136-139 only checks for missing required columns, src/parser.js:141-146 selects required column indexes while preserving extra fields, src/parser.js:152-186 validates/imports rows with extra columns instead of treating the header as fatal]

## What to Change

R1 reads: "Expected header: `name,email,phone` (exact set, any order)." Enforce the EXACT set:
- A header containing any column outside {name,email,phone} is a fatal header error (same class as a missing column): CLI exits 2 with a message naming the unexpected column(s). Keep the existing behavior of naming missing column(s) too; a header can have both problems — report what applies.
- A duplicated required column name in the header (e.g. `name,email,email`) is also not the exact set — treat as fatal with a clear message. (Cheap to enforce while you are here; keep the message simple.)
- Keep: any order allowed, trimmed header cells, BOM tolerance, missing-column error naming the missing column(s), exit code 2 via the CLI wrapper only (parser stays pure — extend the existing HeaderError pathway).

## Also Required

- Add/adjust tests covering the new behavior: extra header column → HeaderError from parseCsv, and (in the CLI end-to-end suite or via the existing bad-header CLI test pattern) exit 2 with the unexpected column named. A duplicate-column header test too.
- All existing requirements stay intact (R2-R12). Do not change anything else.
- Re-run `node --test src/` from /home/ubuntu/Github/superpowers-custom/benchmark/runs/csvimport_M — must exit 0, all tests passing.
- Still NO git. Work only inside the base directory.

## Report Back

Same format as before: Status (DONE / DONE_WITH_CONCERNS / BLOCKED), what changed, test tail (pass/fail counts), files touched.
