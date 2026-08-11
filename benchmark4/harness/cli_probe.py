"""Behavioural probe for a command-line tool.

Third domain. The rule learned in benchmark3 is applied here deliberately: do
NOT port another domain's invariant list. Enumerate where THIS domain's defects
live, then write experiments for that.

A CLI's contract surface is the process contract, which is neither a rendered
page nor an HTTP conversation:

  EXIT-CODE   the documented exit status must actually be produced
  STREAM      data on stdout, diagnostics on stderr, never mixed — this is what
              makes a tool pipeable, and it is broken constantly
  ARGV        malformed/missing/duplicated/adjacent options must produce a usage
              error, not a traceback
  STDIN       `-` and a piped stdin must behave exactly like a named file
  ATOMIC      a failed run must not leave a truncated output file where a good
              one was
  ENCODING    BOM, CRLF, non-ASCII and embedded newlines must survive
  ROUNDTRIP   output fed back in must parse to the same data (quoting bugs)
  IDEMPOTENT  running twice must produce the same bytes

BLIND SPOTS — state these to whoever reads the output, because naming them was
worth more than the findings themselves in the previous domain:
  - algorithmic correctness (is the sort actually stable? is numeric comparison
    applied where the spec says?)
  - anything requiring domain judgement about the RIGHT answer
  - performance, memory, very large inputs
  - concurrent invocation, signal handling, terminal/TTY behaviour
  - correctness of the help text against the implemented options

Usage:
    python cli_probe.py --cmd "python csvq.py" --workdir DIR --plan plan.json
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile


def run(cmd, args, cwd, stdin=None, timeout=30):
    try:
        p = subprocess.run(shlex.split(cmd) + args, cwd=cwd,
                           input=stdin if stdin is not None else None,
                           capture_output=True, timeout=timeout)
        return {'code': p.returncode, 'out': p.stdout, 'err': p.stderr}
    except subprocess.TimeoutExpired:
        return {'code': None, 'out': b'', 'err': b'<timed out>'}
    except Exception as e:
        return {'code': None, 'out': b'', 'err': repr(e).encode()}


def txt(b):
    return b.decode('utf-8', 'replace')


TRACEBACK = ('Traceback (most recent call last)', 'File "', 'Error: ')


def probe(cmd, cwd, plan):
    out = []

    def rec(inv, where, detail):
        out.append({'invariant': inv, 'where': where, 'detail': detail})

    good = plan['good_args']
    prefix = plan.get('err_prefix')

    # --- baseline: STOP unless the tool itself actually runs ---------------
    # HAZARD, now hit in THREE domains running: a browser that never loaded, a
    # server that had died, and here an interpreter that could not find the
    # script. In every case the probe happily recorded dozens of "defects" that
    # were one broken harness. Verify the target responds AT ALL, and abort —
    # do not merely log it and carry on, because every later experiment is then
    # measuring the harness, not the artifact.
    sanity = run(cmd, ['--help'], cwd)
    if sanity['code'] is None or (
            b'No such file' in sanity['err'] or b"can't open file" in sanity['err']):
        return [{'invariant': 'PROBE-ERROR', 'where': cmd,
                 'detail': 'the tool could not be launched at all — '
                           f'{txt(sanity["err"])[:200]!r}. No experiments were run; '
                           'fix the command or path first.'}]

    base = run(cmd, good, cwd, stdin=plan.get('stdin_bytes'))
    if base['code'] is None:
        return [{'invariant': 'PROBE-ERROR', 'where': ' '.join(good),
                 'detail': f'the documented example did not run: {txt(base["err"])[:200]}'}]
    if base['code'] != 0:
        rec('EXIT-CODE', ' '.join(good),
            f'the documented happy-path invocation exits {base["code"]} '
            f'(expected 0). stderr: {txt(base["err"])[:180]!r}')

    # --- ARGV: hostile and malformed arguments ----------------------------
    for args, why, want in plan.get('usage_errors', []):
        r = run(cmd, args, cwd, stdin=plan.get('stdin_bytes'))
        if r['code'] is None:
            rec('ARGV', ' '.join(args), f'{why}: the process hung or died — {txt(r["err"])[:160]}')
            continue
        if any(m in txt(r['err']) for m in TRACEBACK[:2]):
            rec('ARGV', ' '.join(args),
                f'{why} produced a Python traceback instead of a usage error '
                f'(exit {r["code"]}): {txt(r["err"]).strip().splitlines()[-1][:160]!r}')
        elif r['code'] != want:
            rec('EXIT-CODE', ' '.join(args),
                f'{why} exits {r["code"]}, but the spec documents {want} for this class '
                f'of failure. stderr: {txt(r["err"]).strip()[:160]!r}')
        if r['out'] and r['code'] != 0:
            rec('STREAM', ' '.join(args),
                f'{why} failed (exit {r["code"]}) but still wrote {len(r["out"])} bytes to '
                f'STDOUT: {txt(r["out"])[:120]!r}. A failing run must put nothing on stdout.')
        if prefix and r['code'] not in (0, None) and r['err']:
            first = txt(r['err']).strip().splitlines()[0] if r['err'].strip() else ''
            if first and not first.startswith(prefix):
                rec('STREAM', ' '.join(args),
                    f'{why}: the error message does not start with the documented '
                    f'{prefix!r} prefix: {first[:140]!r}')

    # --- STREAM: diagnostics must not be on stdout ------------------------
    if base['code'] == 0 and base['err']:
        rec('STREAM', ' '.join(good),
            f'a successful run wrote {len(base["err"])} bytes to stderr: '
            f'{txt(base["err"])[:140]!r}')

    # --- help --------------------------------------------------------------
    for flag in ('--help', '-h'):
        r = run(cmd, [flag], cwd)
        if r['code'] is None:
            rec('ARGV', flag, 'hung or crashed')
        else:
            if r['code'] != 0:
                rec('EXIT-CODE', flag, f'exits {r["code"]}; --help is documented as exit 0')
            if not r['out'] and r['err']:
                rec('STREAM', flag,
                    'usage went to STDERR, not stdout — `tool --help | less` gets nothing')

    # --- STDIN equivalence -------------------------------------------------
    se = plan.get('stdin_equiv')
    if se:
        viafile = run(cmd, se['file_args'], cwd)
        viadash = run(cmd, se['dash_args'], cwd, stdin=se['stdin_bytes'])
        viapipe = run(cmd, se['pipe_args'], cwd, stdin=se['stdin_bytes'])
        for label, r in (('with `-` as the filename', viadash),
                         ('with no filename at all', viapipe)):
            if r['code'] is None:
                rec('STDIN', label, f'hung or crashed: {txt(r["err"])[:160]}')
            elif r['out'] != viafile['out']:
                rec('STDIN', label,
                    f'reading the same data {label} produced different output than reading '
                    f'it from a file.\n      file: {txt(viafile["out"])[:100]!r}\n      '
                    f'stdin: {txt(r["out"])[:100]!r}')

    # --- ENCODING ----------------------------------------------------------
    for name, data, why in plan.get('encoding_cases', []):
        path = os.path.join(cwd, name)
        with open(path, 'wb') as f:
            f.write(data if isinstance(data, bytes) else data.encode())
        r = run(cmd, plan['encoding_args'] + [name], cwd)
        if r['code'] is None:
            rec('ENCODING', name, f'{why}: hung or crashed — {txt(r["err"])[:160]}')
        elif any(m in txt(r['err']) for m in TRACEBACK[:2]):
            rec('ENCODING', name,
                f'{why} produced a traceback: '
                f'{txt(r["err"]).strip().splitlines()[-1][:160]!r}')
        elif r['code'] != 0:
            rec('ENCODING', name,
                f'{why} exits {r["code"]}: {txt(r["err"]).strip()[:160]!r}')
        elif plan.get('encoding_expect') and plan['encoding_expect'] in name:
            pass

    # --- ATOMIC: a failing run must not clobber an existing output ---------
    at = plan.get('atomic')
    if at:
        dest = os.path.join(cwd, 'atomic_target.out')
        with open(dest, 'wb') as f:
            f.write(b'PRECIOUS-ORIGINAL-CONTENT')
        r = run(cmd, at['failing_args'] + ['atomic_target.out'] if at.get('append_dest')
                else at['failing_args'], cwd)
        with open(dest, 'rb') as f:
            after = f.read()
        if after != b'PRECIOUS-ORIGINAL-CONTENT':
            rec('ATOMIC', ' '.join(at['failing_args']),
                f'a run that failed (exit {r["code"]}) overwrote the destination anyway — '
                f'the original content is gone, replaced by {after[:80]!r}. The spec '
                f'requires the destination be left untouched on failure.')

    # --- IDEMPOTENT / ROUNDTRIP -------------------------------------------
    if base['code'] == 0:
        again = run(cmd, good, cwd, stdin=plan.get('stdin_bytes'))
        if again['out'] != base['out']:
            rec('IDEMPOTENT', ' '.join(good),
                'running the identical command twice produced different stdout')
    rt = plan.get('roundtrip')
    if rt and base['code'] == 0:
        tmp = os.path.join(cwd, 'roundtrip.csv')
        with open(tmp, 'wb') as f:
            f.write(base['out'])
        r = run(cmd, rt['args'] + ['roundtrip.csv'], cwd)
        if r['code'] is None or r['code'] != 0:
            rec('ROUNDTRIP', 'roundtrip.csv',
                f'the tool cannot read back its own output (exit {r["code"]}): '
                f'{txt(r["err"]).strip()[:160]!r}')
        elif r['out'] != base['out']:
            rec('ROUNDTRIP', 'roundtrip.csv',
                f'feeding the output back in does not reproduce it — quoting or escaping '
                f'is lossy.\n      first pass:  {txt(base["out"])[:110]!r}\n      '
                f'second pass: {txt(r["out"])[:110]!r}')
    return out


def as_markdown(f):
    header = ['# CLI experiments', '',
              'Each record is a command sequence that broke an invariant. '
              'Reproduce it yourself before reporting it.', '',
              '**This probe is blind to:** algorithmic correctness (is the sort '
              'stable? is numeric comparison applied where the spec says?), '
              'whether an answer is semantically RIGHT, performance and large '
              'inputs, concurrent invocation, signal handling, TTY behaviour, and '
              'whether the help text matches the options actually implemented. '
              'If the existing report is thin in those areas, that is where to '
              'look — the probe saying nothing about them is not evidence.', '']
    if not f:
        return '\n'.join(header + ['No invariant violations found.'])
    L = list(header)
    for inv in ('EXIT-CODE', 'STREAM', 'ARGV', 'STDIN', 'ENCODING', 'ATOMIC',
                'ROUNDTRIP', 'IDEMPOTENT', 'PROBE-ERROR'):
        rows = [x for x in f if x['invariant'] == inv]
        if not rows:
            continue
        L.append(f'## {inv}')
        for r in rows:
            L.append(f"- `{r['where']}` — {r['detail']}")
        L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cmd', required=True)
    ap.add_argument('--workdir', required=True)
    ap.add_argument('--plan', required=True)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    with open(a.plan, encoding='utf-8') as fh:
        plan = json.load(fh)
    for k in ('stdin_bytes',):
        if isinstance(plan.get(k), str):
            plan[k] = plan[k].encode()
    if plan.get('stdin_equiv') and isinstance(plan['stdin_equiv'].get('stdin_bytes'), str):
        plan['stdin_equiv']['stdin_bytes'] = plan['stdin_equiv']['stdin_bytes'].encode()
    plan['encoding_cases'] = [
        (n, d.encode('utf-8') if isinstance(d, str) else bytes(d), w)
        for n, d, w in plan.get('encoding_cases', [])]
    work = tempfile.mkdtemp(prefix='cliprobe_')
    # A fixture key containing '/' creates the intermediate directories, so a
    # tool that operates on a TREE (rather than a single file) can be given one.
    # Adapting the fixture format per tool is itself a portability cost worth
    # noting: a probe is never as generic as it looks.
    for name, content in plan.get('fixtures', {}).items():
        path = os.path.join(work, *name.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as fh:
            fh.write(content.encode() if isinstance(content, str) else bytes(content))
    for d in plan.get('fixture_dirs', []):
        os.makedirs(os.path.join(work, *d.split('/')), exist_ok=True)
    cmd = a.cmd.replace('{TOOL}', os.path.abspath(a.workdir))
    for pre in plan.get('setup', []):
        run(cmd, pre, work)
    res = probe(cmd, work, plan)
    print(json.dumps(res, indent=2) if a.json else as_markdown(res))
    sys.exit(0)
