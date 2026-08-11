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
