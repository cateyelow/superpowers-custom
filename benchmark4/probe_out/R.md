# CLI experiments

Each record is a command sequence that broke an invariant. Reproduce it yourself before reporting it.

**This probe is blind to:** algorithmic correctness (is the sort stable? is numeric comparison applied where the spec says?), whether an answer is semantically RIGHT, performance and large inputs, concurrent invocation, signal handling, TTY behaviour, and whether the help text matches the options actually implemented. If the existing report is thin in those areas, that is where to look — the probe saying nothing about them is not evidence.

## EXIT-CODE
- `ragged.csv` — a row with more fields than the header exits 2, but the spec documents 1 for this class of failure. stderr: 'csvq: ragged.csv: line 3: expected 3 fields, got 4'

## ENCODING
- `empty.csv` — a completely empty file exits 1: "csvq: unknown column: 'name'\r\ncsvq: try 'csvq --help' for more information"

