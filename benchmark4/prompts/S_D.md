# Second pass — machine experiments over a finished review

A reviewer has already reviewed this tool and written the report below. Their
pass is done and it stands. An automated probe then drove the tool: documented
exit codes, stream discipline, malformed and missing arguments, stdin versus a
named file, encoding and quoting cases, whether a failed run damages an existing
output file, and whether the tool can read back its own output.

**You are ADDING to the report, not rewriting it.** Every existing record stays
exactly as written, with its numbering. Append new records numbered onward.

## What to do

1. Read the existing report and the experiment results below.
2. For each result, decide whether it is a defect the report does NOT already
   cover. Skip anything already reported, however differently worded.
3. **Reproduce it yourself by running the tool before you add it.** Cite your
   own command, output and exit code in `repro`.
4. Append only what survives. Adding nothing is a valid outcome.

## The probe over-reports — you are the filter

It knows the spec only through a hand-written plan, so it can be wrong about
what "success" means for a given subcommand. Two known ways it misleads:

- It may flag a non-zero exit that is CORRECT (a checking subcommand is supposed
  to exit non-zero when the thing it checks is bad).
- It may flag an error-message format that the spec does not actually require in
  that position.

Check the spec yourself before accepting any record. A wrong entry costs you
more than a missed one.


--- SPEC THE TOOL WAS BUILT FROM ---
# snap — a directory snapshot and diff tool

A single-file Python CLI, stdlib only, run as `python snap.py <command> ...`.

## Commands

```
  snap.py take DIR -o SNAPSHOT     record the state of DIR into SNAPSHOT (JSON)
  snap.py diff SNAPSHOT DIR        report what changed in DIR since SNAPSHOT
  snap.py verify SNAPSHOT          check the snapshot file itself is intact
  snap.py --help                   usage to stdout, exit 0
```

## take

Walks DIR recursively and records, for every regular file: the path relative to
DIR (using `/` as separator), the size in bytes, the mtime as an integer Unix
timestamp, and a SHA-256 of the contents. Also records the DIR it was taken
from and a format version. Symlinks are recorded as symlinks with their target,
never followed. Empty directories are recorded too.

Options: `-x, --exclude GLOB` (repeatable) skips matching paths.

## diff

Compares SNAPSHOT against the current state of DIR and prints, one per line:

```
+ path        a file that did not exist in the snapshot
- path        a file in the snapshot that is now missing
M path        a file whose contents changed
T path        a file whose contents are identical but whose mtime changed
```

Sorted by path. Exit code 0 when there are no differences, 1 when there are.
`--summary` prints only counts. `-q/--quiet` prints nothing and only sets the
exit code.

## verify

Checks the snapshot parses, has the expected version, and that every record has
the required fields. Exit 0 if intact, 1 if not, and print what is wrong.

## Behaviour

- Exit codes: 0 success (or "no differences"), 1 differences or a failed check,
  2 for a usage error, 3 when a path cannot be read.
- Errors go to stderr prefixed `snap: `; only the requested report goes to stdout.
- `take -o` writes atomically: an interrupted or failed run must not leave a
  truncated snapshot in place of a good one.
- A file that cannot be read is reported to stderr and does not abort the whole
  walk.
- Paths must round-trip on both Windows and POSIX (store `/`, compare `/`).

Include a short docstring describing usage. Write everything in `snap.py`.
--- END SPEC ---

TOOL SOURCE: E:/GitHub/superpowers-custom/benchmark4/artifacts/S/snap.py
RUN IT AS: python E:/GitHub/superpowers-custom/benchmark4/artifacts/S/snap.py [options]

--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---
DEFECT 1
what: A corrupt (non-UTF-8) snapshot makes the tool crash with a raw Python traceback instead of reporting what is wrong; `verify`, whose whole job is to detect a damaged snapshot, never gets to run its checks.
where: snap.py:305 (`read_snapshot`, `raw = handle.read()`); the UnicodeDecodeError is not a ValueError so the `json.loads` guard at snap.py:307-309 misses it, and both callers (`command_verify` snap.py:416-417, `command_diff` snap.py:380-381) catch only OSError.
repro: $ python -c "open('corrupt.snap','wb').write(b'\xff\xfe{')"
       $ python E:/GitHub/superpowers-custom/benchmark4/artifacts/S/snap.py verify corrupt.snap
       Traceback (most recent call last):
         File "...\snap.py", line 484, in <module>
           sys.exit(main())
         File "...\snap.py", line 477, in main
           return args.func(args)
         File "...\snap.py", line 416, in command_verify
           document, problems = read_snapshot(args.snapshot)
         File "...\snap.py", line 305, in read_snapshot
           raw = handle.read()
       UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte
       exit code 1
       (`snap.py diff corrupt.snap d` crashes identically. A deeply nested JSON file, `open('deep.json','w').write('['*3000+']'*3000)`, crashes the same call with RecursionError.)
severity: blocking
category: robustness

DEFECT 2
what: `take` walks into Windows directory junctions, so a directory containing a junction to one of its own ancestors is recorded 64 times over: the snapshot is filled with fabricated paths like `loop/loop/loop/f.txt`, and the command can never succeed (always exit 3). `verify` then declares that garbage snapshot intact.
where: snap.py:151-164 (`Scanner._record`): `item.is_symlink()` is False for a junction on Python 3.8+, so the junction falls through to `item.is_dir(follow_symlinks=False)` at snap.py:162 and is pushed onto the walk stack at snap.py:164. Real symlinks are handled correctly; junctions are not.
repro: $ mkdir j && printf x > j/f.txt
       $ cmd /c "mklink /J <abs>\j\loop <abs>\j"
       Junction created for ...\j\loop <<===>> ...\j
       $ python E:/GitHub/superpowers-custom/benchmark4/artifacts/S/snap.py take j -o j.snap
       snap: j/loop/loop/loop/... (64 levels) ...: the system cannot resolve the file name
       exit code 3
       $ python -c "import json;d=json.load(open('j.snap'));print(len(d['entries']),[e['path'] for e in d['entries']][:3])"
       65 ['f.txt', 'loop/f.txt', 'loop/loop/f.txt']
       $ python E:/GitHub/superpowers-custom/benchmark4/artifacts/S/snap.py verify j.snap
       snapshot ok: 65 entries, format version 1
       exit code 0
severity: blocking
category: correctness

DEFECT 3
what: A file that exists but cannot be read is reported on stdout as deleted (`- path`). The report actively states something false about the tree rather than saying the file could not be checked. Symmetrically, `take` silently omits such a file from the snapshot, so a later diff against a readable tree reports it as newly added (`+ path`).
where: snap.py:183-194 (`Scanner._digest` returns None on OSError) -> snap.py:172-174 (`_record` returns None, so the path is dropped from `entries`) -> snap.py:361 (`compare` sees it only in `old` and emits the "removed" marker).
repro: $ mkdir u && printf aaa > u/keep.txt && printf bbb > u/locked.txt
       $ python E:/GitHub/superpowers-custom/benchmark4/artifacts/S/snap.py take u -o u.snap        # exit 0
       $ icacls <abs>\u\locked.txt /deny "%USERNAME%:(R)"
       $ python E:/GitHub/superpowers-custom/benchmark4/artifacts/S/snap.py diff u.snap u
       snap: u/locked.txt: Permission denied          (stderr)
       - locked.txt                                   (stdout, but the file is still there)
       exit code 3
severity: minor
category: correctness

--- END EXISTING REPORT ---

## Probe results

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



## Output contract (follow exactly)

Write the COMPLETE report to the path given to you: every record from the
existing report above, unchanged and in its original order, followed by any
records you are adding. Use the same record shape:

```
DEFECT <n>
what: <one line — the problem, in terms of what a user experiences>
where: <file:line, or the option and code path>
repro: <the exact command YOU ran, the output, and the exit code>
severity: blocking | minor
category: spec | exit-code | stream | parsing | correctness | robustness
```

Rules:
- Do not edit, merge, renumber or delete an existing record.
- Add only defects you reproduced yourself by running the tool.
- One record per distinct defect.
- If you are adding nothing, write the existing report out unchanged.
- Work in your own scratch directory under the system temp dir; never modify
  anything in the artifact directory.
- Your final reply must be ONLY the total number of records in the file you wrote.
