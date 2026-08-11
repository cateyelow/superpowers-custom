#!/usr/bin/env python3
"""snap - record the state of a directory tree and report what changed.

Usage:
  snap.py take DIR -o SNAPSHOT [-x GLOB]...   record the state of DIR (JSON)
  snap.py diff SNAPSHOT DIR [--summary | -q]  report what changed since
  snap.py verify SNAPSHOT                     check the snapshot is intact
  snap.py --help                              this text

`take` walks DIR and records, for every regular file, its path relative to DIR
(always stored with `/` separators), its size, its mtime as an integer Unix
timestamp and a SHA-256 of its contents.  Symlinks are recorded as symlinks
with their target and are never followed; empty directories are recorded as
directories.  Excluded globs are stored in the snapshot so that `diff` applies
exactly the same filter.  The snapshot is written atomically.

`diff` prints one line per changed path, sorted by path:

  + path   a file that did not exist in the snapshot
  - path   a file in the snapshot that is now missing
  M path   a file whose contents changed
  T path   a file whose contents are identical but whose mtime changed

Exit codes: 0 success (or "no differences"), 1 differences or a failed check,
2 a usage error, 3 a path could not be read, 130 interrupted.  A path that
cannot be read is reported on stderr and does not abort the walk; the run then
finishes with exit code 3 because its report is incomplete.  Errors go to
stderr prefixed `snap: `; only the requested report goes to stdout.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import stat
import sys
import tempfile
import time

PROG = "snap"
FORMAT_VERSION = 1

EXIT_OK = 0
EXIT_DIFF = 1
EXIT_USAGE = 2
EXIT_IO = 3
EXIT_INTERRUPT = 130

CHUNK_SIZE = 1 << 16
MAX_REPORTED_PROBLEMS = 50

TYPE_FILE = "file"
TYPE_SYMLINK = "symlink"
TYPE_DIR = "dir"

# Fields every record of a given type must carry, and their JSON types.
REQUIRED_FIELDS = {
    TYPE_FILE: (("size", int), ("mtime", int), ("sha256", str)),
    TYPE_SYMLINK: (("target", str),),
    TYPE_DIR: (),
}


def warn(message):
    """Report a problem on stderr; stdout is reserved for the report."""
    sys.stderr.write("%s: %s\n" % (PROG, message))


def reason(exc):
    """A short, human readable reason for an OSError."""
    return getattr(exc, "strerror", None) or str(exc)


def to_slash(path):
    """Normalise a host path for storage.

    Only the host separator is rewritten, so a POSIX name that legitimately
    contains a backslash is left alone.
    """
    if os.sep != "/":
        path = path.replace(os.sep, "/")
    if os.altsep and os.altsep != "/":
        path = path.replace(os.altsep, "/")
    return path


def is_int(value):
    """True for a real JSON integer (bool is not an integer here)."""
    return isinstance(value, int) and not isinstance(value, bool)


# --------------------------------------------------------------------------
# scanning
# --------------------------------------------------------------------------


class Scanner(object):
    """Walks a directory tree and records one entry per path.

    Paths are relative to the root and always use `/`, so a snapshot taken on
    one platform compares correctly on another.  Unreadable paths are counted
    in `errors` and reported, but never abort the walk.
    """

    def __init__(self, root, excludes):
        self.root = root
        self.excludes = list(excludes or [])
        self.errors = 0

    def _fail(self, path, exc):
        self.errors += 1
        warn("%s: %s" % (to_slash(path), reason(exc)))

    def is_excluded(self, relpath, name):
        """A glob may match the whole relative path or just the base name."""
        for pattern in self.excludes:
            # fnmatchcase, not fnmatch: fnmatch normalises case *and*
            # separators on Windows, which would break `/`-based patterns.
            if fnmatch.fnmatchcase(relpath, pattern):
                return True
            if fnmatch.fnmatchcase(name, pattern):
                return True
        return False

    def scan(self):
        """Return {relative path: record} for the whole tree."""
        entries = {}
        directories = []
        stack = [(self.root, "")]
        while stack:
            dirpath, prefix = stack.pop()
            for item in self._listdir(dirpath):
                relpath = prefix + item.name
                if self.is_excluded(relpath, item.name):
                    continue
                record = self._record(item, relpath, directories, stack)
                if record is not None:
                    entries[relpath] = record
        self._add_empty_directories(entries, directories)
        return entries

    def _listdir(self, dirpath):
        try:
            with os.scandir(dirpath) as scan:
                return sorted(scan, key=lambda item: item.name)
        except OSError as exc:
            self._fail(dirpath, exc)
            return []

    def _record(self, item, relpath, directories, stack):
        """Build the record for one directory entry, or None if it has none."""
        try:
            if item.is_symlink():
                # Recorded as a symlink, never followed.  The target is stored
                # verbatim: it is opaque text, not a path we walk.
                return {
                    "path": relpath,
                    "type": TYPE_SYMLINK,
                    "target": os.readlink(item.path),
                }
            if item.is_dir(follow_symlinks=False):
                directories.append(relpath)
                stack.append((item.path, relpath + "/"))
                return None
            info = item.stat(follow_symlinks=False)
        except OSError as exc:
            self._fail(item.path, exc)
            return None
        if not stat.S_ISREG(info.st_mode):
            return None  # sockets, fifos, devices: not regular files
        digest = self._digest(item.path)
        if digest is None:
            return None
        return {
            "path": relpath,
            "type": TYPE_FILE,
            "size": info.st_size,
            "mtime": int(info.st_mtime),
            "sha256": digest,
        }

    def _digest(self, path):
        digest = hashlib.sha256()
        try:
            with open(path, "rb") as handle:
                while True:
                    block = handle.read(CHUNK_SIZE)
                    if not block:
                        break
                    digest.update(block)
        except OSError as exc:
            self._fail(path, exc)
            return None
        return digest.hexdigest()

    @staticmethod
    def _add_empty_directories(entries, directories):
        """Record directories that hold nothing the snapshot kept."""
        occupied = set()
        for path in list(entries) + directories:
            parts = path.split("/")
            for depth in range(1, len(parts)):
                occupied.add("/".join(parts[:depth]))
        for path in directories:
            if path not in occupied:
                entries[path] = {"path": path, "type": TYPE_DIR}


def implied_directories(entries):
    """Every directory the entries prove exists, explicit or as a parent."""
    directories = set()
    for path, record in entries.items():
        if record.get("type") == TYPE_DIR:
            directories.add(path)
        parts = path.split("/")
        for depth in range(1, len(parts)):
            directories.add("/".join(parts[:depth]))
    return directories


# --------------------------------------------------------------------------
# snapshot file handling
# --------------------------------------------------------------------------


def write_atomically(path, text):
    """Write `text` to `path` via a temporary file in the same directory.

    An interrupted or failed run leaves the previous snapshot untouched.
    """
    directory = os.path.dirname(os.path.abspath(path))
    handle, temporary = tempfile.mkstemp(prefix=".snap-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:  # includes KeyboardInterrupt
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def validate_snapshot(document):
    """Return a list of everything wrong with a parsed snapshot."""
    problems = []
    if not isinstance(document, dict):
        return ["top level is %s, expected an object" % type(document).__name__]

    version = document.get("version")
    if version is None:
        problems.append('missing top-level field "version"')
    elif not is_int(version):
        problems.append('field "version" is not an integer')
    elif version != FORMAT_VERSION:
        problems.append(
            "unsupported format version %d (this is snap format %d)"
            % (version, FORMAT_VERSION)
        )

    if not isinstance(document.get("root"), str):
        problems.append('missing or invalid top-level field "root"')

    entries = document.get("entries")
    if not isinstance(entries, list):
        problems.append('missing or invalid top-level field "entries"')
        return problems

    seen = set()
    for index, record in enumerate(entries):
        label = "entries[%d]" % index
        if not isinstance(record, dict):
            problems.append("%s: %s, expected an object" % (label, type(record).__name__))
            continue
        path = record.get("path")
        if not isinstance(path, str) or not path:
            problems.append('%s: missing or invalid field "path"' % label)
        else:
            label = "%s (%s)" % (label, path)
            if path in seen:
                problems.append("%s: duplicate path" % label)
            seen.add(path)
        kind = record.get("type")
        if kind not in REQUIRED_FIELDS:
            problems.append("%s: unknown type %r" % (label, kind))
            continue
        for field, expected in REQUIRED_FIELDS[kind]:
            value = record.get(field)
            if value is None:
                problems.append('%s: missing required field "%s"' % (label, field))
            elif expected is int and not is_int(value):
                problems.append('%s: field "%s" is not an integer' % (label, field))
            elif expected is str and not isinstance(value, str):
                problems.append('%s: field "%s" is not a string' % (label, field))
    return problems


def read_snapshot(path):
    """Return (document, problems).  Raises OSError if the file is unreadable."""
    with open(path, "r", encoding="utf-8") as handle:
        raw = handle.read()
    try:
        document = json.loads(raw)
    except ValueError as exc:
        return None, ["not valid JSON: %s" % exc]
    return document, validate_snapshot(document)


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def command_take(args):
    if not os.path.isdir(args.dir):
        warn("%s: not a directory" % args.dir)
        return EXIT_IO

    scanner = Scanner(args.dir, args.exclude)
    entries = scanner.scan()
    document = {
        "version": FORMAT_VERSION,
        "root": to_slash(os.path.abspath(args.dir)),
        "taken": int(time.time()),
        "excludes": scanner.excludes,
        "entries": [entries[path] for path in sorted(entries)],
    }
    try:
        write_atomically(args.output, json.dumps(document, indent=2, sort_keys=True) + "\n")
    except OSError as exc:
        warn("%s: %s" % (args.output, reason(exc)))
        return EXIT_IO
    return EXIT_IO if scanner.errors else EXIT_OK


def compare(old, new):
    """Return ([(marker, path), ...] sorted by path, {category: count})."""
    old_directories = implied_directories(old)
    new_directories = implied_directories(new)
    changes = []
    counts = {"added": 0, "removed": 0, "modified": 0, "touched": 0}

    def note(marker, path, category):
        changes.append((marker, path))
        counts[category] += 1

    for path in sorted(set(old) | set(new)):
        before = old.get(path)
        after = new.get(path)
        if before is None:
            # A directory that only became visible (its last file went away)
            # is not new: the snapshot already implied it.
            if after["type"] == TYPE_DIR and path in old_directories:
                continue
            note("+", path, "added")
        elif after is None:
            # Likewise, a recorded empty directory that merely gained content
            # has not been removed.
            if before["type"] == TYPE_DIR and path in new_directories:
                continue
            note("-", path, "removed")
        elif before["type"] != after["type"]:
            note("M", path, "modified")
        elif after["type"] == TYPE_FILE:
            if before["sha256"] != after["sha256"]:
                note("M", path, "modified")
            elif before["mtime"] != after["mtime"]:
                note("T", path, "touched")
        elif after["type"] == TYPE_SYMLINK:
            if before["target"] != after["target"]:
                note("M", path, "modified")
    return changes, counts


def command_diff(args):
    try:
        document, problems = read_snapshot(args.snapshot)
    except OSError as exc:
        warn("%s: %s" % (args.snapshot, reason(exc)))
        return EXIT_IO
    if problems:
        warn("%s: %s" % (args.snapshot, problems[0]))
        warn("not a usable snapshot; run '%s.py verify %s' for the full report"
             % (PROG, args.snapshot))
        return EXIT_DIFF
    if not os.path.isdir(args.dir):
        warn("%s: not a directory" % args.dir)
        return EXIT_IO

    # The same filter that produced the snapshot, or excluded files would all
    # look newly added.
    scanner = Scanner(args.dir, document.get("excludes"))
    new = scanner.scan()
    old = dict((record["path"], record) for record in document["entries"])
    changes, counts = compare(old, new)

    if not args.quiet:
        if args.summary:
            for category in ("added", "removed", "modified", "touched"):
                print("%-9s %d" % (category, counts[category]))
        else:
            for marker, path in changes:
                print("%s %s" % (marker, path))

    if scanner.errors:
        return EXIT_IO
    return EXIT_DIFF if changes else EXIT_OK


def command_verify(args):
    try:
        document, problems = read_snapshot(args.snapshot)
    except OSError as exc:
        warn("%s: %s" % (args.snapshot, reason(exc)))
        return EXIT_IO
    if problems:
        for problem in problems[:MAX_REPORTED_PROBLEMS]:
            print(problem)
        hidden = len(problems) - MAX_REPORTED_PROBLEMS
        if hidden > 0:
            print("... and %d more problems" % hidden)
        return EXIT_DIFF
    print("snapshot ok: %d entries, format version %d"
          % (len(document["entries"]), FORMAT_VERSION))
    return EXIT_OK


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Record the state of a directory tree and report what changed.",
        epilog=("diff markers: '+' added, '-' removed, 'M' contents changed, "
                "'T' same contents but new mtime.\n"
                "exit codes: 0 no differences, 1 differences or a failed check, "
                "2 usage error, 3 a path could not be read."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    commands.required = True

    take = commands.add_parser("take", help="record the state of DIR into SNAPSHOT")
    take.add_argument("dir", metavar="DIR", help="directory to record")
    take.add_argument("-o", "--output", metavar="SNAPSHOT", required=True,
                      help="snapshot file to write (written atomically)")
    take.add_argument("-x", "--exclude", metavar="GLOB", action="append", default=[],
                      help="skip paths matching GLOB (repeatable)")
    take.set_defaults(func=command_take)

    diff = commands.add_parser("diff", help="report what changed in DIR since SNAPSHOT")
    diff.add_argument("snapshot", metavar="SNAPSHOT", help="snapshot to compare against")
    diff.add_argument("dir", metavar="DIR", help="directory to compare")
    diff.add_argument("--summary", action="store_true", help="print only counts")
    diff.add_argument("-q", "--quiet", action="store_true",
                      help="print nothing, only set the exit code (overrides --summary)")
    diff.set_defaults(func=command_diff)

    verify = commands.add_parser("verify", help="check the snapshot file itself is intact")
    verify.add_argument("snapshot", metavar="SNAPSHOT", help="snapshot to check")
    verify.set_defaults(func=command_verify)

    return parser


def main(argv=None):
    # argparse reports usage errors on stderr as "snap: error: ..." and exits 2.
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        warn("interrupted")
        return EXIT_INTERRUPT


if __name__ == "__main__":
    sys.exit(main())
