#!/usr/bin/env python3
r"""csvq - a small CSV query tool.

Usage:
    python csvq.py [options] [FILE]

Reads CSV from FILE, or from standard input when FILE is absent or "-".
Rows may be filtered with --where, ordered with --sort/--reverse, capped with
--limit and projected onto a subset of columns with --columns; the result is
written as CSV (default), TSV or JSON, to stdout or to --output.

Examples:
    python csvq.py -c name,age -w 'age >= 30' -s age -n 10 people.csv
    python csvq.py -f json -w 'city ~ "New "' -o out.json people.csv
    python csvq.py -d '\t' -H -c 1,3 --count < people.tsv

Run "python csvq.py --help" for the full option list.
"""

import csv
import io
import json
import math
import os
import sys
import tempfile

PROG = "csvq"

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_IO = 2

USAGE = """usage: csvq [options] [FILE]

Query a CSV file, or standard input when FILE is absent or '-'.

options:
  -c, --columns LIST     comma-separated column names to output, in that order
  -w, --where EXPR       keep only rows matching EXPR (see below)
  -s, --sort COLUMN      sort output rows by COLUMN
  -r, --reverse          reverse the sort
  -n, --limit N          output at most N rows
  -d, --delimiter CHAR   input delimiter (default ,)
  -o, --output FILE      write to FILE instead of stdout
  -H, --no-header        the input has no header row; refer to columns as 1,2,3
  -f, --format FORMAT    csv (default) | tsv | json
      --count            print only the number of matching rows
  -h, --help             show this help and exit

EXPR is COLUMN OP VALUE, where OP is one of =, !=, <, <=, >, >= or ~ (substring).
Comparisons are numeric when both sides parse as numbers, otherwise string.
A value may be quoted with double quotes to include spaces, for example:

    csvq -w 'name = "Ada Lovelace"' people.csv

--count reports how many rows would have been written, that is after --where
and --limit have been applied.
"""


class UsageError(Exception):
    """A problem with the command line: exits 1."""


class FileError(Exception):
    """The input could not be read or the output could not be written: exits 2."""


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------

FLAGS = {
    "-r": "reverse",
    "--reverse": "reverse",
    "-H": "no_header",
    "--no-header": "no_header",
    "--count": "count",
    "-h": "help",
    "--help": "help",
}

VALUED = {
    "-c": "columns",
    "--columns": "columns",
    "-w": "where",
    "--where": "where",
    "-s": "sort",
    "--sort": "sort",
    "-n": "limit",
    "--limit": "limit",
    "-d": "delimiter",
    "--delimiter": "delimiter",
    "-o": "output",
    "--output": "output",
    "-f": "format",
    "--format": "format",
}

FORMATS = ("csv", "tsv", "json")


def parse_args(argv):
    """Turn argv into (options dict, input path or None)."""
    opts = {
        "columns": None,
        "where": None,
        "sort": None,
        "reverse": False,
        "limit": None,
        "delimiter": ",",
        "output": None,
        "no_header": False,
        "format": "csv",
        "count": False,
        "help": False,
    }
    positional = []
    rest_are_positional = False
    i = 0

    def take_value(name, inline, index):
        """Return (value, next index) for an option that needs an argument."""
        if inline is not None:
            return inline, index
        if index >= len(argv):
            raise UsageError("option %s requires an argument" % name)
        return argv[index], index + 1

    while i < len(argv):
        arg = argv[i]
        i += 1
        if rest_are_positional:
            positional.append(arg)
        elif arg == "--":
            rest_are_positional = True
        elif arg.startswith("--"):
            name, sep, inline = arg.partition("=")
            if name in FLAGS:
                if sep:
                    raise UsageError("option %s does not take a value" % name)
                opts[FLAGS[name]] = True
            elif name in VALUED:
                value, i = take_value(name, inline if sep else None, i)
                opts[VALUED[name]] = value
            else:
                raise UsageError("unknown option: %s" % name)
        elif arg.startswith("-") and arg != "-":
            j = 1
            while j < len(arg):
                name = "-" + arg[j]
                j += 1
                if name in FLAGS:
                    opts[FLAGS[name]] = True
                elif name in VALUED:
                    inline = arg[j:] if j < len(arg) else None
                    j = len(arg)
                    value, i = take_value(name, inline, i)
                    opts[VALUED[name]] = value
                else:
                    raise UsageError("unknown option: %s" % name)
        else:
            positional.append(arg)

    if opts["help"]:
        return opts, None

    if len(positional) > 1:
        raise UsageError("too many arguments: %s" % " ".join(positional[1:]))

    if opts["limit"] is not None:
        text = opts["limit"]
        try:
            opts["limit"] = int(text, 10)
        except ValueError:
            raise UsageError("invalid value for --limit: %r" % text)
        if opts["limit"] < 0:
            raise UsageError("--limit must not be negative")

    delimiter = opts["delimiter"]
    if delimiter == "\\t":  # a literal backslash-t, which shells make easy to type
        delimiter = "\t"
    if len(delimiter) != 1:
        raise UsageError("--delimiter must be a single character")
    if delimiter in ("\r", "\n"):
        raise UsageError("--delimiter must not be a newline")
    opts["delimiter"] = delimiter

    if opts["format"] not in FORMATS:
        raise UsageError(
            "invalid format: %r (expected %s)" % (opts["format"], ", ".join(FORMATS))
        )

    return opts, (positional[0] if positional else None)


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------


def open_input(path):
    """Return (text stream, close_it) for the input, decoding any UTF-8 BOM."""
    if path is None or path == "-":
        try:
            stream = io.TextIOWrapper(
                sys.stdin.buffer, encoding="utf-8-sig", newline=""
            )
        except (AttributeError, ValueError) as exc:  # stdin already text/detached
            raise FileError("cannot read standard input: %s" % exc)
        return stream, False
    try:
        return open(path, "r", encoding="utf-8-sig", newline=""), True
    except OSError as exc:
        raise FileError("cannot read %s: %s" % (path, exc.strerror or exc))


def read_table(stream, path, delimiter, no_header):
    """Read the input into (column names, rows).

    Short rows are padded with empty strings; a long row is an error naming the
    line it ends on.  Completely blank lines are skipped.
    """
    label = "standard input" if path in (None, "-") else path
    reader = csv.reader(stream, delimiter=delimiter)
    names = None
    width = 0
    rows = []
    try:
        for record in reader:
            if not record:  # blank line
                continue
            if names is None:
                if no_header:
                    width = len(record)
                    names = [str(n + 1) for n in range(width)]
                else:
                    names = record
                    width = len(record)
                    continue
            if len(record) > width:
                raise FileError(
                    "%s: line %d: expected %d field%s, got %d"
                    % (
                        label,
                        reader.line_num,
                        width,
                        "" if width == 1 else "s",
                        len(record),
                    )
                )
            if len(record) < width:
                record = record + [""] * (width - len(record))
            rows.append(record)
    except csv.Error as exc:
        raise FileError("%s: line %d: %s" % (label, reader.line_num, exc))
    except UnicodeDecodeError as exc:
        raise FileError("%s: not valid UTF-8: %s" % (label, exc.reason))
    except OSError as exc:
        raise FileError("cannot read %s: %s" % (label, exc.strerror or exc))

    if names is None:  # empty input
        names = []
    return names, rows


# --------------------------------------------------------------------------
# columns, filtering and sorting
# --------------------------------------------------------------------------


def make_resolver(names):
    """Return a function mapping a column name to its index."""
    index = {}
    for position, name in enumerate(names):
        index.setdefault(name, position)

    def resolve(name):
        if name in index:
            return index[name]
        stripped = name.strip()
        if stripped in index:
            return index[stripped]
        raise UsageError("unknown column: %r" % name)

    return resolve


def as_number(text):
    """Return text as a float, or None when it is not a plain number."""
    stripped = text.strip()
    if not stripped or "_" in stripped:
        return None
    try:
        value = float(stripped)
    except (ValueError, OverflowError):
        return None
    if math.isnan(value):
        return None
    return value


OPERATORS = ("!=", "<=", ">=", "=", "<", ">", "~")


def unquote(text):
    """Strip surrounding double quotes, turning a doubled quote into one."""
    if len(text) >= 2 and text.startswith('"') and text.endswith('"'):
        return text[1:-1].replace('""', '"')
    return text


def split_where(expr):
    """Split EXPR into (column, operator, value)."""
    text = expr.strip()
    if not text:
        raise UsageError("empty --where expression")

    start = 0
    if text.startswith('"'):  # a quoted column name may contain operator characters
        pos = 1
        while pos < len(text):
            if text[pos] == '"':
                if pos + 1 < len(text) and text[pos + 1] == '"':
                    pos += 2
                    continue
                break
            pos += 1
        if pos >= len(text):
            raise UsageError("unterminated quote in expression: %r" % expr)
        start = pos + 1

    for pos in range(start, len(text)):
        for op in OPERATORS:
            if text.startswith(op, pos):
                column = text[:pos].strip()
                value = text[pos + len(op):].strip()
                if not column:
                    raise UsageError("missing column in expression: %r" % expr)
                return unquote(column), op, unquote(value)
    raise UsageError(
        "malformed expression: %r (expected COLUMN OP VALUE, OP one of %s)"
        % (expr, " ".join(OPERATORS))
    )


class Condition:
    """A single COLUMN OP VALUE test."""

    def __init__(self, index, op, value):
        self.index = index
        self.op = op
        self.value = value
        self.number = as_number(value)

    def matches(self, row):
        field = row[self.index]
        if self.op == "~":
            return self.value in field
        left, right = field, self.value
        if self.number is not None:
            field_number = as_number(field)
            if field_number is not None:
                left, right = field_number, self.number
        op = self.op
        if op == "=":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == "<=":
            return left <= right
        if op == ">":
            return left > right
        return left >= right


def sort_rows(rows, index, reverse):
    """Stable sort by column, numerically when every value is a number."""
    numbers = [as_number(row[index]) for row in rows]
    if numbers and all(number is not None for number in numbers):
        keys = numbers
    else:
        keys = [row[index] for row in rows]
    order = sorted(range(len(rows)), key=keys.__getitem__, reverse=reverse)
    return [rows[position] for position in order]


# --------------------------------------------------------------------------
# rendering and writing
# --------------------------------------------------------------------------


def render(names, rows, selected, opts):
    """Build the complete output as a single string."""
    if opts["count"]:
        return "%d\n" % len(rows)

    headings = [names[index] for index in selected]

    if opts["format"] == "json":
        records = [
            dict(zip(headings, (row[index] for index in selected))) for row in rows
        ]
        return json.dumps(records, indent=2, ensure_ascii=False) + "\n"

    buffer = io.StringIO()
    writer = csv.writer(
        buffer,
        delimiter="\t" if opts["format"] == "tsv" else ",",
        lineterminator="\n",
    )
    if not opts["no_header"]:
        writer.writerow(headings)
    for row in rows:
        writer.writerow([row[index] for index in selected])
    return buffer.getvalue()


def write_output(text, path):
    """Write text to stdout, or atomically replace path with it."""
    if path is None:
        try:
            sys.stdout.reconfigure(encoding="utf-8", newline="")
        except (AttributeError, ValueError, OSError):
            pass
        try:
            sys.stdout.write(text)
            sys.stdout.flush()
        except BrokenPipeError:
            # The reader (a pager, head, ...) went away: stop quietly.
            try:
                devnull = os.open(os.devnull, os.O_WRONLY)
                os.dup2(devnull, sys.stdout.fileno())
            except OSError:
                pass
        except OSError as exc:
            raise FileError("cannot write to standard output: %s" % (exc.strerror or exc))
        return

    destination = os.path.abspath(path)
    directory = os.path.dirname(destination) or "."
    try:
        handle, temporary = tempfile.mkstemp(dir=directory, prefix=".csvq-", suffix=".tmp")
    except OSError as exc:
        raise FileError("cannot write %s: %s" % (path, exc.strerror or exc))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except OSError as exc:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise FileError("cannot write %s: %s" % (path, exc.strerror or exc))


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


def build_output(opts, path):
    stream, close_it = open_input(path)
    try:
        names, rows = read_table(stream, path, opts["delimiter"], opts["no_header"])
    finally:
        if close_it:
            stream.close()

    resolve = make_resolver(names)

    if opts["columns"] is None:
        selected = list(range(len(names)))
    else:
        selected = [resolve(name) for name in opts["columns"].split(",")]

    if opts["where"] is not None:
        column, op, value = split_where(opts["where"])
        condition = Condition(resolve(column), op, value)
        rows = [row for row in rows if condition.matches(row)]

    if opts["sort"] is not None:
        rows = sort_rows(rows, resolve(opts["sort"]), opts["reverse"])
    elif opts["reverse"]:
        rows = rows[::-1]

    if opts["limit"] is not None:
        rows = rows[: opts["limit"]]

    return render(names, rows, selected, opts)


def fail(message, code, hint=False):
    sys.stderr.write("%s: %s\n" % (PROG, message))
    if hint:
        sys.stderr.write("%s: try '%s --help' for more information\n" % (PROG, PROG))
    return code


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        opts, path = parse_args(argv)
    except UsageError as exc:
        return fail(exc, EXIT_USAGE, hint=True)

    if opts["help"]:
        sys.stdout.write(USAGE)
        return EXIT_OK

    try:
        text = build_output(opts, path)
        write_output(text, opts["output"])
    except UsageError as exc:
        return fail(exc, EXIT_USAGE, hint=True)
    except FileError as exc:
        return fail(exc, EXIT_IO)
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stderr.write("%s: interrupted\n" % PROG)
        sys.exit(130)
