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
# csvq — a small CSV query tool

A single-file Python CLI, stdlib only, run as `python csvq.py [options] [FILE]`.
Reads CSV from FILE, or from stdin when FILE is absent or is `-`.

## Options

```
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
  -h, --help             usage to stdout, exit 0
```

`EXPR` is `COLUMN OP VALUE` where OP is one of `=`, `!=`, `<`, `<=`, `>`, `>=`,
`~` (substring). Comparisons are numeric when both sides parse as numbers,
otherwise string. Values may be quoted with double quotes to include spaces.

## Behaviour

- The header row is preserved in `csv`/`tsv` output and used as keys in `json`.
- `--sort` on a column whose values all parse as numbers sorts numerically;
  otherwise lexicographically. Sorting is stable.
- Unknown column names (in `--columns`, `--where` or `--sort`) are an error.
- A row with fewer fields than the header is padded with empty strings; a row
  with more fields is an error naming the line number.
- Exit codes: 0 on success, 1 on a usage error (bad option, unknown column,
  malformed expression), 2 when the input file cannot be read.
- Every error message goes to stderr, prefixed `csvq: `, and nothing but the
  requested data goes to stdout.
- `--output` writes atomically: if the run fails, the destination is left
  untouched rather than half-written.
- The tool must handle a quoted field containing the delimiter, embedded
  newlines, and a UTF-8 BOM at the start of the file.

Include a short docstring describing usage. Write everything in `csvq.py`.
--- END SPEC ---

TOOL SOURCE: E:/GitHub/superpowers-custom/benchmark4/artifacts/R/csvq.py
RUN IT AS: python E:/GitHub/superpowers-custom/benchmark4/artifacts/R/csvq.py [options]
