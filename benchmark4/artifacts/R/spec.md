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
