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
