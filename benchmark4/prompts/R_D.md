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

--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---
DEFECT 1
what: If stdout is closed, the tool dies with a raw Python traceback instead of a "csvq: ..." message, and exits 1 (the usage-error code) rather than reporting an I/O failure.
where: csvq.py:430 in write_output (stdout branch). Line 426 already guards sys.stdout being None for reconfigure() via "except (AttributeError, ...)", but the sys.stdout.write(text) on line 430 is only wrapped in "except BrokenPipeError" / "except OSError", so AttributeError escapes to top level.
repro: `python E:/GitHub/superpowers-custom/benchmark4/artifacts/R/csvq.py people.csv >&-` (bash, stdout fd closed). stderr: "Traceback (most recent call last): ... File \"E:\\GitHub\\superpowers-custom\\benchmark4\\artifacts\\R\\csvq.py\", line 430, in write_output / sys.stdout.write(text) / AttributeError: 'NoneType' object has no attribute 'write'". exit code 1.
severity: blocking
category: robustness

DEFECT 2
what: An empty input prints a stray blank line to stdout instead of printing nothing, so a downstream consumer of a zero-row result sees one line of output.
where: csvq.py:415-416 in render() - the header row is written unconditionally for csv/tsv, and when the input is empty `headings` is [] so csv.writer emits a bare line terminator.
repro: `python E:/GitHub/superpowers-custom/benchmark4/artifacts/R/csvq.py empty.csv | od -c` where empty.csv is a zero-byte file. Output: "0000000  \n" (one byte of stdout). exit code 0. Same with `printf '' | python .../csvq.py` and with a file containing only blank lines. Contradicts the spec line "nothing but the requested data goes to stdout". (`-f json` correctly prints "[]", and `-H` correctly prints nothing, so only the default csv/tsv path is affected.)
severity: minor
category: stream

DEFECT 3
what: `--count` prints the truncated row count when `--limit` is also given, not the number of rows matching the filter, so `csvq --count -n 3` can never report more than 3 no matter how many rows match.
where: `--count` + `--limit`; csvq.py:493-494 applies the limit to `rows`, then csvq.py:398-399 returns len(rows) of the already-truncated list.
repro: `python E:/GitHub/superpowers-custom/benchmark4/artifacts/R/csvq.py --count people.csv` -> "5", exit 0. `python E:/GitHub/superpowers-custom/benchmark4/artifacts/R/csvq.py --count -n 3 people.csv` -> "3", exit 0, although 5 rows match. Likewise `--count -w 'age > 8'` -> "3" but `--count -w 'age > 8' -n 1` -> "1". Spec says `--count` prints "the number of matching rows".
severity: minor
category: spec

DEFECT 4
what: A valid CSV file containing a field longer than 128 KB is rejected as unreadable, so the file simply cannot be queried.
where: csvq.py:226 (csv.reader is created without ever raising csv.field_size_limit()), surfacing at csvq.py:256-257 where csv.Error is converted into a FileError.
repro: build the file with `python -c "import io; io.open('bigfield.csv','w',encoding='utf-8',newline='').write('a,b\n' + 'z'*200000 + ',2\n')"`, then `python E:/GitHub/superpowers-custom/benchmark4/artifacts/R/csvq.py bigfield.csv`. stderr: "csvq: bigfield.csv: line 2: field larger than field limit (131072)". exit code 2.
severity: minor
category: robustness

DEFECT 5
what: When the input header repeats a column name, JSON output silently drops one of those columns and reports the other column's value under that name, disagreeing with what `--columns` returns for the same name.
where: csvq.py:404-406 in render() builds each record with dict(zip(headings, ...)) so a repeated heading keeps the last value, while make_resolver at csvq.py:276-277 uses setdefault and therefore resolves the same name to the first column.
repro: dup.csv contains "a,a,b\n1,2,3\n". `python E:/GitHub/superpowers-custom/benchmark4/artifacts/R/csvq.py -f json dup.csv` -> `[ { "a": "2", "b": "3" } ]`, exit 0 (the value "1" is lost and key "a" holds column 2). The csv output of the same file is "a,a,b" / "1,2,3" (both columns kept) and `-c a dup.csv` returns "1", i.e. column 1.
severity: minor
category: correctness

--- END EXISTING REPORT ---

## Probe results

# CLI experiments

Each record is a command sequence that broke an invariant. Reproduce it yourself before reporting it.

**This probe is blind to:** algorithmic correctness (is the sort stable? is numeric comparison applied where the spec says?), whether an answer is semantically RIGHT, performance and large inputs, concurrent invocation, signal handling, TTY behaviour, and whether the help text matches the options actually implemented. If the existing report is thin in those areas, that is where to look — the probe saying nothing about them is not evidence.

## EXIT-CODE
- `ragged.csv` — a row with more fields than the header exits 2, but the spec documents 1 for this class of failure. stderr: 'csvq: ragged.csv: line 3: expected 3 fields, got 4'

## ENCODING
- `empty.csv` — a completely empty file exits 1: "csvq: unknown column: 'name'\r\ncsvq: try 'csvq --help' for more information"



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
