# CLI experiments

Each record is a command sequence that broke an invariant. Reproduce it yourself before reporting it.

**This probe is blind to:** algorithmic correctness (is the sort stable? is numeric comparison applied where the spec says?), whether an answer is semantically RIGHT, performance and large inputs, concurrent invocation, signal handling, TTY behaviour, and whether the help text matches the options actually implemented. If the existing report is thin in those areas, that is where to look — the probe saying nothing about them is not evidence.

## STREAM
- `nosuchcommand` — an unknown subcommand: the error message does not start with the documented 'snap: ' prefix: 'usage: snap [-h] COMMAND ...'
- `take` — take with no directory: the error message does not start with the documented 'snap: ' prefix: 'usage: snap take [-h] -o SNAPSHOT [-x GLOB] DIR'
- `take tree` — take with no -o: the error message does not start with the documented 'snap: ' prefix: 'usage: snap take [-h] -o SNAPSHOT [-x GLOB] DIR'
- `diff` — diff with no arguments: the error message does not start with the documented 'snap: ' prefix: 'usage: snap diff [-h] [--summary] [-q] SNAPSHOT DIR'
- `verify` — verify with no argument: the error message does not start with the documented 'snap: ' prefix: 'usage: snap verify [-h] SNAPSHOT'
- `take tree -o out.json --bogus-flag` — an unknown option: the error message does not start with the documented 'snap: ' prefix: 'usage: snap [-h] COMMAND ...'
- `verify truncated.json` — a snapshot truncated mid-JSON (verify must reject it cleanly) failed (exit 1) but still wrote 61 bytes to STDOUT: 'not valid JSON: Expecting value: line 1 column 26 (char 25)\r\n'. A failing run must put nothing on stdout.
- `verify empty.json` — a completely empty snapshot file (verify must reject it cleanly) failed (exit 1) but still wrote 59 bytes to STDOUT: 'not valid JSON: Expecting value: line 1 column 1 (char 0)\r\n'. A failing run must put nothing on stdout.
- `verify notjson.json` — a snapshot that is not JSON (verify must reject it cleanly) failed (exit 1) but still wrote 59 bytes to STDOUT: 'not valid JSON: Expecting value: line 1 column 1 (char 0)\r\n'. A failing run must put nothing on stdout.
- `verify wrongshape.json` — valid JSON that is not a snapshot (verify must reject it cleanly) failed (exit 1) but still wrote 124 bytes to STDOUT: 'missing top-level field "version"\r\nmissing or invalid top-level field "root"\r\nmissing or invalid top-level field "entrie'. A failing run must put nothing on stdout.
- `verify nullver.json` — a snapshot with a null version (verify must reject it cleanly) failed (exit 1) but still wrote 124 bytes to STDOUT: 'missing top-level field "version"\r\nmissing or invalid top-level field "root"\r\nmissing or invalid top-level field "entrie'. A failing run must put nothing on stdout.
- `verify bigver.json` — a snapshot from a future version (verify must reject it cleanly) failed (exit 1) but still wrote 148 bytes to STDOUT: 'unsupported format version 999999 (this is snap format 1)\r\nmissing or invalid top-level field "root"\r\nmissing or invalid'. A failing run must put nothing on stdout.

