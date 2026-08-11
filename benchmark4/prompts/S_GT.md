# Defect audit (reference list)

You are auditing a small command-line tool before it ships, to produce the
DEFINITIVE list of defects it has. You have the spec it was built from and its
full source. Be exhaustive and strict: this list is the reference others are
measured against, so a defect you miss is one nobody gets credit for finding,
and a non-defect you include penalises everyone.

## How to work

Read the source, then RUN the tool and drive it with real invocations. Confirm
every defect by observing it — include the exact command, the output, and the
exit code. Do not report anything you have not reproduced.

Work in a scratch directory of your own (use the system temp dir), never in the
artifact directory.

## What counts as a defect

- Any violation of the spec, including exit codes, stream discipline
  (data on stdout, diagnostics on stderr), error message format, and the
  documented behaviours.
- Any input that produces a Python traceback instead of a clean error.
- Any way the tool loses or corrupts data, or writes a partial output file.
- Wrong results: a filter that keeps the wrong rows, a sort in the wrong order
  or that is not stable, numeric-vs-string comparison applied wrongly,
  quoting/escaping that does not round-trip.

Not a defect: style, structure, naming, missing tests, performance you have not
measured, or anything you merely suspect.

Consider at minimum: every documented option and their combinations; missing
and malformed option values; unknown columns; stdin vs a named file vs `-`;
empty input, header-only input, no trailing newline; quoted fields containing
the delimiter, quotes, and newlines; a UTF-8 BOM; CRLF; non-ASCII; rows with
too few and too many fields; the exact exit code for each failure class; and
whether a failing run can damage an existing output file.

## Output contract (follow exactly)

Write your findings to the report path given to you, one blank line between
records:

```
DEFECT <n>
what: <one line — the problem, in terms of what a user experiences>
where: <file:line, or the option and code path>
repro: <the exact command you ran, the output, and the exit code>
severity: blocking | minor
category: spec | exit-code | stream | parsing | correctness | robustness
```

Rules:
- Report only defects you actually reproduced.
- "blocking" = wrong results, data loss or corruption, a crash, or a documented
  behaviour that is absent.
- One record per distinct defect.
- Your final reply must be ONLY the number of defects you wrote.

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
