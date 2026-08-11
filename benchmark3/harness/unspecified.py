"""Probe the quality attributes the spec is SILENT about.

Both API implementations satisfied every explicit requirement in their specs —
the probe correctly reported nothing. That is itself the finding: an API spec
enumerates its requirements ("never negative", "double-cancel is an error") and
an implementer follows the list. The web artifacts leaked defects because the
things that broke — contrast, focus, caret behaviour — were never in the spec.

So the fair analogue is what an API spec does not say: injection, oversized
payloads, integer overflow, unicode and control characters, missing or wrong
Content-Type, and whether an error leaks internals. That is where the same
"nobody ran this experiment" gap should live if it exists here at all.
"""
import json
import sys
import urllib.error
import urllib.request


def call(base, method, path, body=None, raw=None, headers=None, timeout=20):
    hdrs = {} if headers is None else dict(headers)
    data = None
    if raw is not None:
        data = raw if isinstance(raw, bytes) else raw.encode()
    elif body is not None:
        data = json.dumps(body).encode()
        hdrs.setdefault('Content-Type', 'application/json')
    req = urllib.request.Request(base.rstrip('/') + path, data=data,
                                 method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {'status': r.status, 'text': r.read().decode('utf-8', 'replace')[:400]}
    except urllib.error.HTTPError as e:
        # A server that rejects mid-upload (413) often closes the socket before
        # the body is readable, so e.read() raises on top of the HTTPError.
        # Losing the status here would silently turn a correct rejection into a
        # "connection died" finding.
        try:
            text = e.read().decode('utf-8', 'replace')[:400]
        except Exception as inner:
            text = f'<body unreadable: {inner!r}>'
        return {'status': e.code, 'text': text}
    except Exception as e:
        return {'status': None, 'text': repr(e)[:160]}


LEAKY = ('Traceback', 'File "', 'sqlite3.', 'line ', 'Exception', '<html')


def alive(base):
    """Is anything actually listening? A refused connection is not a defect."""
    r = call(base, 'GET', '/', timeout=5)
    return r['status'] is not None or 'ConnectionRefused' not in r['text']


def run(base, create_path, good_body, text_field, int_field):
    out = []

    # HAZARD (2026-08-11): the first run of this probe reported 20+ "defects"
    # that were all one thing — the server had already died, and every
    # subsequent ConnectionRefused was recorded as a finding. A browser is
    # always there; a server is not. Check liveness before starting, and again
    # after anything that could kill it, and never turn "nothing is listening"
    # into a defect record.
    if not alive(base):
        return [{'invariant': 'PROBE-ERROR', 'where': base,
                 'detail': 'nothing is listening at this address — start the service '
                           'before probing. No experiments were run.'}]

    def rec(inv, where, detail):
        # A refused connection means the process is gone. That is either the
        # previous experiment killing it (report it once, as a crash) or an
        # environment problem — never evidence about the case under test.
        if 'ConnectionRefused' in detail or 'ConnectionRefusedError' in detail:
            if not any(x['invariant'] == 'CRASHED' for x in out):
                out.append({'invariant': 'CRASHED', 'where': where,
                            'detail': 'the service stopped accepting connections part-way '
                                      'through the experiments; everything after this point '
                                      'could not be tested. The last case attempted was: '
                                      + detail[:160]})
            return
        out.append({'invariant': inv, 'where': where, 'detail': detail})

    # --- INJECTION -------------------------------------------------------
    for payload in ("' OR 1=1--", '"; DROP TABLE items;--', "%27%20OR%201=1"):
        b = dict(good_body)
        b[text_field] = payload
        r = call(base, 'POST', create_path, body=b)
        if r['status'] is None:
            rec('INJECTION', f'POST {create_path}',
                f'{payload!r} in {text_field} killed the connection: {r["text"]}')
        elif r['status'] >= 500:
            rec('INJECTION', f'POST {create_path}',
                f'{payload!r} in {text_field} -> HTTP {r["status"]}: {r["text"][:140]!r}')
        elif any(m in r['text'] for m in LEAKY):
            rec('LEAK', f'POST {create_path}',
                f'{payload!r} produced a response containing internals: {r["text"][:160]!r}')

    # --- OVERFLOW --------------------------------------------------------
    if int_field:
        for big, why in ((10 ** 30, 'far beyond 64-bit'), (2 ** 63, 'exactly 2^63'),
                         (-2 ** 63 - 1, 'below -2^63')):
            b = dict(good_body)
            b[int_field] = big
            r = call(base, 'POST', create_path, body=b)
            if r['status'] is None:
                rec('OVERFLOW', f'POST {create_path}',
                    f'{int_field}={why} killed the connection: {r["text"]}')
            elif r['status'] >= 500:
                rec('OVERFLOW', f'POST {create_path}',
                    f'{int_field}={why} -> HTTP {r["status"]}: {r["text"][:140]!r}')

    # --- UNICODE / CONTROL CHARACTERS ------------------------------------
    # NB: these must be built at runtime — a literal NUL in the source makes
    # the file itself unparseable ('source code cannot contain null bytes').
    cases = [('a null byte', chr(0)),
             ('control characters', chr(1) + chr(2) + chr(27)),
             ('right-to-left override', chr(0x202e)),
             ('astral plane emoji', chr(0x1f600) * 4),
             ('combining marks', 'a' + chr(0x301) * 200),
             ('lone surrogate escape', '\ud800')]
    for why, payload in cases:
        b = dict(good_body)
        b[text_field] = 'X' + payload
        r = call(base, 'POST', create_path, body=b)
        if r['status'] is None:
            rec('UNICODE', f'POST {create_path}',
                f'{why} in {text_field} killed the connection: {r["text"]}')
        elif r['status'] >= 500:
            rec('UNICODE', f'POST {create_path}',
                f'{why} in {text_field} -> HTTP {r["status"]}: {r["text"][:140]!r}')

    # --- CONTENT-TYPE ----------------------------------------------------
    body_bytes = json.dumps(good_body).encode()
    for hdr, why in (({}, 'no Content-Type header'),
                     ({'Content-Type': 'text/plain'}, 'Content-Type: text/plain'),
                     ({'Content-Type': 'application/xml'}, 'Content-Type: application/xml')):
        r = call(base, 'POST', create_path, raw=body_bytes, headers=hdr)
        if r['status'] is None:
            rec('CONTENT-TYPE', f'POST {create_path}',
                f'{why} killed the connection: {r["text"]}')
        elif r['status'] >= 500:
            rec('CONTENT-TYPE', f'POST {create_path}',
                f'{why} -> HTTP {r["status"]} instead of 400/415: {r["text"][:140]!r}')

    # --- OVERSIZED PAYLOAD ----------------------------------------------
    for size, why in ((1_000_000, '1 MB'), (8_000_000, '8 MB')):
        b = dict(good_body)
        b['pad'] = 'A' * size
        r = call(base, 'POST', create_path, body=b, timeout=40)
        if r['status'] is None:
            rec('PAYLOAD', f'POST {create_path}',
                f'a {why} body killed the connection ({r["text"]}) — there is no request '
                f'size limit, so a client can exhaust the server this way')
        elif r['status'] >= 500:
            rec('PAYLOAD', f'POST {create_path}',
                f'a {why} body -> HTTP {r["status"]}: {r["text"][:140]!r}')
        elif 200 <= r['status'] < 300:
            rec('PAYLOAD', f'POST {create_path}',
                f'a {why} body was ACCEPTED (HTTP {r["status"]}) — unbounded request bodies '
                f'are stored/parsed with no limit')

    if not alive(base):
        rec('CRASHED', f'POST {create_path}',
            'the service was alive at the start and is not listening after the '
            'oversized-payload experiments — an unbounded request body can take '
            'the process down')
        return out

    # --- HEADER-BASED TRUNCATION ----------------------------------------
    r = call(base, 'POST', create_path, raw=body_bytes,
             headers={'Content-Type': 'application/json',
                      'Content-Length': str(len(body_bytes) + 500)})
    if r['status'] is None:
        rec('ROBUSTNESS', f'POST {create_path}',
            f'a Content-Length longer than the body hung or dropped the connection: {r["text"]}')
    return out


def as_markdown(f):
    if not f:
        return ('# Unspecified-attribute experiments\n\nNo violations found.')
    L = ['# Unspecified-attribute experiments', '',
         'The spec is silent about these; each record is still a reproducible '
         'failure. Verify before reporting.', '']
    for inv in ('CRASHED', 'INJECTION', 'LEAK', 'OVERFLOW', 'UNICODE',
                'CONTENT-TYPE', 'PAYLOAD', 'ROBUSTNESS', 'PROBE-ERROR'):
        rows = [x for x in f if x['invariant'] == inv]
        if not rows:
            continue
        L.append(f'## {inv}')
        for r in rows:
            L.append(f"- `{r['where']}` — {r['detail']}")
        L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    base, cfg = sys.argv[1], json.loads(sys.argv[2])
    res = run(base, cfg['path'], cfg['body'], cfg['text_field'], cfg.get('int_field'))
    print(json.dumps(res, indent=2) if '--json' in sys.argv else as_markdown(res))
