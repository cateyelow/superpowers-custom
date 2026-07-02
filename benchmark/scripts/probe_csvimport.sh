#!/usr/bin/env bash
# Deterministic behavioral probe for the csvimport task.
# Usage: probe_csvimport.sh <run_src_dir>
# Prints PROBE <id> PASS|FAIL lines. Never aborts.
SRC="$1"
CLI="$SRC/importCsv.js"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

r() { # r <id> <expected_exit> — runs CLI on $T/in.csv → $T/out.json, captures streams
  node "$CLI" "$T/in.csv" "$T/out.json" > "$T/stdout" 2> "$T/stderr"
  local code=$?
  [ "$code" -eq "$2" ] && echo "PROBE $1_exit PASS" || echo "PROBE $1_exit FAIL (exit $code, want $2)"
}

# P1: --help exits 0
node "$CLI" --help > /dev/null 2>&1 && echo "PROBE help_exit0 PASS" || echo "PROBE help_exit0 FAIL"

# P2: missing column header → exit 2, names the column
printf 'name,email\nKim,kim@a.com\n' > "$T/in.csv"
r badheader 2
grep -qi phone "$T/stderr" && echo "PROBE badheader_names_col PASS" || echo "PROBE badheader_names_col FAIL"

# P3: quoted comma + escaped quote + invalid email + dup email; line numbers on stderr
cat > "$T/in.csv" <<'EOF'
name,email,phone
"Kim, Minsu",kim@a.com,010-1234-5678
Lee,not-an-email,01011112222
"Park ""PK"" Jun",park@b.com,010 2222 3333
Choi,KIM@A.COM,010-3333-4444
EOF
r mixed 1
python3 - "$T/out.json" <<'PY'
import json,sys
try:
    d=json.load(open(sys.argv[1]))
    c=d.get("contacts",[])
    names=[x["name"] for x in c]
    ok = (len(c)==2 and "Kim, Minsu" in names and 'Park "PK" Jun' in names
          and all(x["phone"].isdigit() for x in c))
    print("PROBE quoted_fields", "PASS" if ok else f"FAIL {names}")
except Exception as e:
    print("PROBE quoted_fields FAIL", e)
PY
grep -q 'line 3' "$T/stderr" && echo "PROBE lineno_invalid_email PASS" || echo "PROBE lineno_invalid_email FAIL"
grep -q 'line 5' "$T/stderr" && grep -qi 'duplicate email' "$T/stderr" && echo "PROBE dup_email_lineno PASS" || echo "PROBE dup_email_lineno FAIL"
grep -q 'imported 2/4 rows' "$T/stdout" && echo "PROBE summary_line PASS" || echo "PROBE summary_line FAIL ($(cat "$T/stdout"))"

# P4: header-only → exit 0, empty contacts, imported 0/0
printf 'name,email,phone\n' > "$T/in.csv"
r headeronly 0
python3 -c "import json,sys; d=json.load(open('$T/out.json')); sys.exit(0 if d=={'contacts':[]} else 1)" \
  && echo "PROBE empty_contacts PASS" || echo "PROBE empty_contacts FAIL"
grep -q 'imported 0/0 rows' "$T/stdout" && echo "PROBE zero_summary PASS" || echo "PROBE zero_summary FAIL"

# P5: BOM + CRLF
printf '\xef\xbb\xbfname,email,phone\r\nKim,kim@a.com,010-1234-5678\r\n' > "$T/in.csv"
r bomcrlf 0
python3 -c "
import json,sys
d=json.load(open('$T/out.json'))
c=d['contacts']
sys.exit(0 if len(c)==1 and c[0]['name']=='Kim' and c[0]['phone']=='01012345678' else 1)" \
  && echo "PROBE bom_crlf_normalize PASS" || echo "PROBE bom_crlf_normalize FAIL"

# P6: all-valid → exit 0; trailing newline on output
printf 'name,email,phone\nKim,kim@a.com,010-1234-5678\n' > "$T/in.csv"
r allvalid 0
[ "$(tail -c 1 "$T/out.json" | od -An -c | tr -d ' ')" = '\n' ] && echo "PROBE trailing_newline PASS" || echo "PROBE trailing_newline FAIL"

# P7: unreadable input → exit 2
node "$CLI" "$T/nope.csv" "$T/out2.json" > /dev/null 2>&1
[ $? -eq 2 ] && echo "PROBE missing_input_exit2 PASS" || echo "PROBE missing_input_exit2 FAIL"

# P8: parser purity — module must not import fs / call process.exit (comments stripped)
sed -e 's://.*$::' "$SRC/parser.js" | grep -Eq "from ['\"]node:fs|from ['\"]fs['\"]|require\(['\"](node:)?fs|process\.exit\(" \
  && echo "PROBE parser_purity FAIL" || echo "PROBE parser_purity PASS"
