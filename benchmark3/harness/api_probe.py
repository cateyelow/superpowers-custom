"""Behavioural probe for an HTTP API — the same invariants, a different domain.

This is the portability test for the web result (benchmark2): the claim was
that the INVARIANT LIST transfers even though the implementation does not.
Nothing here shares a line of code with ui_behaviour_probe.py; what carries
over is the shape — drive the system the way a client does, break invariants
that are decidable, and never report anything a machine cannot check.

Web invariant        ->  API invariant
  RESPONSIVE         ->  CONCURRENCY: parallel requests must not corrupt state
  BOUNDARY           ->  BOUNDARY:    a declared constraint must actually reject
  SEMANTIC           ->  SEMANTIC:    valid-shaped but impossible values rejected
  IDEMPOTENT         ->  IDEMPOTENT:  repeating a terminal action must not
                                      silently succeed twice
  ERROR-STATE        ->  ERROR-SHAPE: every error is the declared JSON shape
  DROP-GUARD         ->  ROBUSTNESS:  malformed input is a 4xx, never a 5xx
  (no web analogue)  ->  INVARIANT:   a stated data invariant (never negative,
                                      never overlapping) must survive any
                                      sequence
  (no web analogue)  ->  METHOD/NOTFOUND: wrong verb / unknown id answer
                                      correctly rather than crashing

Usage:
    python api_probe.py --base http://127.0.0.1:8080 --plan plan.json
    python api_probe.py ... --json

`plan.json` describes the contract in machine terms — it is derived from the
spec, the way an OpenAPI document would be. An API is not self-describing the
way a DOM is, so the contract has to come from somewhere; that is a difference
in the domain, not a weakening of the method.

    {
      "list":        {"path": "/items", "collection_key": null},
      "detail":      {"path": "/items/{id}", "sample_id": "WIDGET-1"},
      "create":      {"path": "/reservations",
                      "body": {"sku": "WIDGET-1", "qty": 1},
                      "int_fields": ["qty"],
                      "id_field": "id"},
      "actions":     [{"path": "/reservations/{id}/release", "terminal": true},
                      {"path": "/reservations/{id}/fulfil", "terminal": true}],
      "error_shape": ["error", "code"],
      "invariants":  [{"kind": "non_negative", "path": "/items",
                       "fields": ["on_hand", "reserved", "available"]}],
      "capacity":    {"create_body": {"sku": "GADGET-2", "qty": 1}, "limit": 3,
                      "check": {"path": "/items/GADGET-2", "field": "available"}}
    }
"""
import argparse
import json
import queue
import threading
import urllib.error
import urllib.request


class Client:
    def __init__(self, base):
        self.base = base.rstrip('/')

    def call(self, method, path, body=None, raw=None, headers=None):
        url = self.base + path
        data = None
        hdrs = {'Content-Type': 'application/json'}
        if headers:
            hdrs.update(headers)
        if raw is not None:
            data = raw if isinstance(raw, bytes) else raw.encode()
        elif body is not None:
            data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                payload = r.read()
                status = r.status
        except urllib.error.HTTPError as e:
            payload = e.read()
            status = e.code
        except Exception as e:
            return {'status': None, 'error': repr(e)[:160], 'body': None, 'text': ''}
        text = payload.decode('utf-8', 'replace')
        try:
            parsed = json.loads(text) if text.strip() else None
        except Exception:
            parsed = None
        return {'status': status, 'body': parsed, 'text': text[:400], 'error': None}


def _fill(path, ident):
    return path.replace('{id}', str(ident))


class BodyFactory:
    """Yields a fresh create-body each call.

    Needed because some resources conflict with themselves: booking the same
    slot twice is legitimately rejected, so a fixed body would make every
    boundary probe fail for the WRONG reason and hide real defects behind
    "already booked". `vary` cycles one field through values that do not
    collide, so each experiment tests only what it means to test.
    """

    def __init__(self, create):
        self.base = dict((create or {}).get('body') or {})
        vary = (create or {}).get('vary') or {}
        self.field = vary.get('field')
        self.values = list(vary.get('values') or [])
        self.i = 0

    def next(self, **overrides):
        body = dict(self.base)
        if self.field and self.values:
            body[self.field] = self.values[self.i % len(self.values)]
            self.i += 1
        body.update(overrides)
        return body

    def peek_same(self, **overrides):
        """A body that deliberately does NOT advance — for collision tests."""
        body = dict(self.base)
        if self.field and self.values:
            body[self.field] = self.values[0]
        body.update(overrides)
        return body


def _shape_ok(body, keys):
    """Does the error body match the declared nesting, e.g. ['error','code']?"""
    node = body
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            return False
        node = node[k]
    return True


def probe_robustness(c, plan, out):
    """Malformed input must be a 4xx with the declared error shape, not a 5xx
    and not a stack trace."""
    create = plan.get('create')
    if not create:
        return
    shape = plan.get('error_shape') or []
    bf = BodyFactory(create)
    cases = [
        ('not JSON at all', {'raw': b'this is not json'}),
        ('empty body', {'raw': b''}),
        ('JSON array instead of object', {'raw': b'[1,2,3]'}),
        ('JSON null', {'raw': b'null'}),
        ('valid JSON, no fields', {'body': {}}),
        ('string where an integer belongs',
         {'body': bf.next(**{f: 'lots' for f in create.get('int_fields', [])})}),
        ('null where a value belongs',
         {'body': {k: None for k in bf.next()}}),
        ('deeply nested junk', {'body': bf.next(extra={'a': {'b': {'c': [1] * 50}}})}),
    ]
    for label, kw in cases:
        r = c.call('POST', create['path'], **kw)
        if r['status'] is None:
            out.append({'invariant': 'ROBUSTNESS', 'where': 'POST ' + create['path'],
                        'detail': f'{label}: the connection failed outright ({r["error"]}) — '
                                  f'the server did not answer'})
            continue
        if r['status'] >= 500:
            out.append({'invariant': 'ROBUSTNESS', 'where': 'POST ' + create['path'],
                        'detail': f'{label} -> HTTP {r["status"]}. The spec requires a 400 '
                                  f'for a malformed body, never a 5xx. Response began: '
                                  f'{r["text"][:120]!r}'})
        elif shape and r['status'] >= 400 and not _shape_ok(r['body'], shape):
            out.append({'invariant': 'ERROR-SHAPE', 'where': 'POST ' + create['path'],
                        'detail': f'{label} -> HTTP {r["status"]}, but the body is not the '
                                  f'declared {"/".join(shape)} shape: {r["text"][:120]!r}'})


def probe_boundary(c, plan, out):
    """A declared integer constraint must actually reject what it excludes."""
    create = plan.get('create')
    if not create or not create.get('int_fields'):
        return
    bf = BodyFactory(create)
    for field in create['int_fields']:
        for bad, why in ((0, 'zero'), (-1, 'negative'), (-999999, 'large negative'),
                         (10 ** 12, 'absurdly large'), (1.5, 'fractional'),
                         (True, 'boolean true (Python/JSON int-like)')):
            body = bf.next(**{field: bad})
            r = c.call('POST', create['path'], body=body)
            if r['status'] is None:
                continue
            if 200 <= r['status'] < 300:
                out.append({'invariant': 'BOUNDARY', 'where': 'POST ' + create['path'],
                            'detail': f'{field}={bad!r} ({why}) was ACCEPTED with HTTP '
                                      f'{r["status"]}. The spec requires a positive integer. '
                                      f'Created: {r["text"][:140]!r}'})
            elif r['status'] >= 500:
                out.append({'invariant': 'ROBUSTNESS', 'where': 'POST ' + create['path'],
                            'detail': f'{field}={bad!r} ({why}) caused HTTP {r["status"]} '
                                      f'instead of a 400: {r["text"][:120]!r}'})


def probe_notfound_and_method(c, plan, out):
    """Unknown ids and wrong verbs must answer, not crash."""
    detail = plan.get('detail')
    if detail:
        for weird, why in (('does-not-exist', 'unknown id'),
                           ('../etc/passwd', 'path traversal attempt'),
                           ('%00', 'null byte'),
                           ('9' * 300, 'very long id')):
            r = c.call('GET', _fill(detail['path'], weird))
            if r['status'] is None:
                out.append({'invariant': 'ROBUSTNESS', 'where': 'GET ' + detail['path'],
                            'detail': f'{why} ({weird[:24]!r}) killed the connection: {r["error"]}'})
            elif r['status'] >= 500:
                out.append({'invariant': 'NOTFOUND', 'where': 'GET ' + detail['path'],
                            'detail': f'{why} ({weird[:24]!r}) -> HTTP {r["status"]} instead of '
                                      f'404: {r["text"][:120]!r}'})
    lst = plan.get('list')
    if lst:
        for method in ('DELETE', 'PUT', 'PATCH'):
            r = c.call(method, lst['path'])
            if r['status'] is None:
                out.append({'invariant': 'METHOD', 'where': f'{method} {lst["path"]}',
                            'detail': f'the connection failed: {r["error"]}'})
            elif r['status'] >= 500:
                out.append({'invariant': 'METHOD', 'where': f'{method} {lst["path"]}',
                            'detail': f'HTTP {r["status"]} — an unsupported method should be '
                                      f'405 (or 404), not a server error: {r["text"][:120]!r}'})


def probe_idempotent(c, plan, out):
    """Repeating a terminal action must be an error, not a silent second success —
    and must not move the numbers twice."""
    create = plan.get('create')
    bf = BodyFactory(create)
    for action in plan.get('actions', []):
        if not create:
            break
        made = c.call('POST', create['path'], body=bf.next())
        if not made['body'] or made['status'] is None or made['status'] >= 300:
            continue
        ident = made['body'].get(create.get('id_field', 'id'))
        if ident is None:
            continue
        first = c.call('POST', _fill(action['path'], ident))
        second = c.call('POST', _fill(action['path'], ident))
        if first['status'] and 200 <= first['status'] < 300:
            if second['status'] and 200 <= second['status'] < 300:
                out.append({'invariant': 'IDEMPOTENT', 'where': 'POST ' + action['path'],
                            'detail': f'performed twice on the same id and BOTH succeeded '
                                      f'(HTTP {first["status"]}, then {second["status"]}). '
                                      f'The spec says a terminal action repeated is an error, '
                                      f'not a silent no-op. Second response: '
                                      f'{second["text"][:140]!r}'})
            elif second['status'] and second['status'] >= 500:
                out.append({'invariant': 'ROBUSTNESS', 'where': 'POST ' + action['path'],
                            'detail': f'repeating it produced HTTP {second["status"]} instead '
                                      f'of a 4xx: {second["text"][:120]!r}'})
    # cross-action: two different terminal actions on the same record
    acts = plan.get('actions', [])
    if create and len(acts) >= 2:
        made = c.call('POST', create['path'], body=bf.next())
        if made['body'] and made['status'] and made['status'] < 300:
            ident = made['body'].get(create.get('id_field', 'id'))
            a = c.call('POST', _fill(acts[0]['path'], ident))
            b = c.call('POST', _fill(acts[1]['path'], ident))
            if (a['status'] and a['status'] < 300) and (b['status'] and b['status'] < 300):
                out.append({'invariant': 'IDEMPOTENT', 'where':
                            f'{acts[0]["path"]} then {acts[1]["path"]}',
                            'detail': 'both terminal actions succeeded on the SAME record '
                                      f'(HTTP {a["status"]}, then {b["status"]}) — the record '
                                      'reached two different final states in sequence, so the '
                                      'stock movement is applied on top of an already-closed '
                                      'reservation'})


def probe_concurrency(c, plan, out):
    """The stated capacity must hold under parallel requests. This is the one
    experiment that cannot be done by reading the code and is nearly never done
    by hand."""
    cap = plan.get('capacity')
    if not cap:
        return
    create = plan.get('create')
    if not create:
        return
    same = cap.get('create_body')
    n = max(8, cap['limit'] * 4)
    results = queue.Queue()

    def hit():
        results.put(c.call('POST', create['path'], body=same))

    threads = [threading.Thread(target=hit) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    ok = 0
    fivexx = 0
    while not results.empty():
        r = results.get()
        if r['status'] and 200 <= r['status'] < 300:
            ok += 1
        elif r['status'] and r['status'] >= 500:
            fivexx += 1
    if ok > cap['limit']:
        out.append({'invariant': 'CONCURRENCY', 'where': 'POST ' + create['path'],
                    'detail': f'fired {n} identical requests in parallel against a stated '
                              f'capacity of {cap["limit"]}: {ok} of them SUCCEEDED. The '
                              f'availability check and the write are not atomic, so the '
                              f'limit can be oversold by concurrent clients.'})
    if fivexx:
        out.append({'invariant': 'CONCURRENCY', 'where': 'POST ' + create['path'],
                    'detail': f'{fivexx} of {n} parallel requests returned 5xx — the service '
                              f'errors under concurrent load rather than serialising'})
    # did the invariant survive?
    chk = cap.get('check')
    if chk:
        r = c.call('GET', chk['path'])
        if isinstance(r['body'], dict):
            v = r['body'].get(chk['field'])
            if isinstance(v, (int, float)) and v < 0:
                out.append({'invariant': 'INVARIANT', 'where': 'GET ' + chk['path'],
                            'detail': f'after the parallel burst, {chk["field"]} is {v} — '
                                      f'the spec states it can never go negative'})


def probe_invariants(c, plan, out):
    for inv in plan.get('invariants', []):
        r = c.call('GET', inv['path'])
        rows = r['body']
        if isinstance(rows, dict):
            rows = rows.get('items') or rows.get('data') or [rows]
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            for f in inv.get('fields', []):
                v = row.get(f)
                if isinstance(v, (int, float)) and v < 0:
                    out.append({'invariant': 'INVARIANT', 'where': 'GET ' + inv['path'],
                                'detail': f'{row.get("sku") or row.get("id")}: {f} = {v}, '
                                          f'which the spec says can never be negative'})


def probe_semantic(c, plan, out):
    """Values that parse but are impossible. Which ones make sense is
    domain-specific, so they are declared in the plan."""
    create = plan.get('create')
    bf = BodyFactory(create)
    for case in plan.get('semantic', []):
        if not create:
            break
        body = bf.next(**case['body'])
        r = c.call('POST', create['path'], body=body)
        if r['status'] and 200 <= r['status'] < 300:
            out.append({'invariant': 'SEMANTIC', 'where': 'POST ' + create['path'],
                        'detail': f'{case["why"]} was ACCEPTED with HTTP {r["status"]}: '
                                  f'{json.dumps(case["body"])} -> {r["text"][:140]!r}'})
        elif r['status'] and r['status'] >= 500:
            out.append({'invariant': 'ROBUSTNESS', 'where': 'POST ' + create['path'],
                        'detail': f'{case["why"]} caused HTTP {r["status"]} instead of a 400: '
                                  f'{r["text"][:120]!r}'})


def run(base, plan):
    c = Client(base)
    out = []
    for fn in (probe_robustness, probe_boundary, probe_notfound_and_method,
               probe_semantic, probe_idempotent, probe_concurrency, probe_invariants):
        try:
            fn(c, plan, out)
        except Exception as exc:
            out.append({'invariant': 'PROBE-ERROR', 'where': fn.__name__,
                        'detail': repr(exc)[:200]})
    seen, uniq = set(), []
    for f in out:
        k = (f['invariant'], f['where'], f['detail'][:70])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(f)
    return uniq


def as_markdown(findings):
    if not findings:
        return ('# API experiments\n\nNo invariant violations found. This does not '
                'mean the service is correct — only that these experiments passed.')
    L = ['# API experiments', '',
         'Each record is a request sequence that broke an invariant. Reproduce it '
         'yourself before reporting it.', '']
    order = ['CONCURRENCY', 'INVARIANT', 'IDEMPOTENT', 'BOUNDARY', 'SEMANTIC',
             'ROBUSTNESS', 'ERROR-SHAPE', 'NOTFOUND', 'METHOD', 'PROBE-ERROR']
    for inv in order:
        rows = [f for f in findings if f['invariant'] == inv]
        if not rows:
            continue
        L.append(f'## {inv}')
        for f in rows:
            L.append(f"- `{f['where']}` — {f['detail']}")
        L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--plan', required=True)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    with open(a.plan, encoding='utf-8') as f:
        res = run(a.base, json.load(f))
    print(json.dumps(res, indent=2) if a.json else as_markdown(res))
