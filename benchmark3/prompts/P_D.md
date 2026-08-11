# Second pass — machine experiments over a finished review

A reviewer has already reviewed this service and written the report below.
Their pass is done and it stands. Two automated probes then drove the running
service: one exercising the contract it declares (boundaries, repeated terminal
actions, concurrency, error shape, unknown ids, wrong verbs) and one exercising
what the spec is silent about (injection, integer overflow, unicode and control
characters, Content-Type handling, oversized bodies).

**You are ADDING to the report, not rewriting it.** Every existing record stays
exactly as written, with its numbering. Append new records numbered onward.

## What to do

1. Read the existing report and the experiment results below.
2. For each result, decide whether it is a defect the report does NOT already
   cover. Skip anything already reported, however differently worded.
3. **Reproduce it yourself against the running service before you add it.**
   These are request sequences — reproducing means sending the requests. Cite
   your own request and response in `repro`.
4. Append only what survives. Adding nothing is a valid outcome.

## What the probes can and cannot tell you

A probe result names the invariant it broke. It is evidence, not proof, and it
over-reports in specific ways you must filter:

- `PAYLOAD` — a large body being accepted is only a defect if it actually
  threatens the service. A service that rejects oversized bodies with 413 is
  behaving correctly even if the probe records the connection closing.
- `CRASHED` — means the probe lost the connection. Confirm the service really
  died before treating it as a finding; it may have been restarted or busy.
- Anything reported as "killed the connection" deserves particular suspicion:
  distinguish a genuine crash or hang from a correct, abrupt rejection.

A probe reporting nothing does NOT mean there is nothing there. Both probes are
blind to whole classes of problem — request routing, header parsing, response
framing, HTTP method semantics, resource cleanup. If the existing report is
thin in those areas, that is your opportunity, not the probe's.


--- SPEC THE SERVICE WAS BUILT FROM ---
# Inventory reservation service

A single-file Python HTTP service backing a small warehouse. Stdlib only
(`http.server`, `json`, `sqlite3`, `threading`) — no third-party packages, so it
can be started with `python app.py` and listens on the port in `$PORT`
(default 8080). State lives in SQLite at the path in `$DB` (default `inv.db`),
created on first run.

## Data

An `items` table: `sku` (text, unique), `name` (text), `on_hand` (integer,
never negative), `reserved` (integer, never negative).
A `reservations` table: `id` (text), `sku` (text), `qty` (integer),
`status` (text: `held` | `released` | `fulfilled`), `created_at` (ISO-8601
UTC string).

Seed three items on first run: `WIDGET-1` ("Widget", 10 on hand),
`GADGET-2` ("Gadget", 3 on hand), `DOODAD-3` ("Doodad", 0 on hand).

## Endpoints

`GET /items` — list all items with `sku`, `name`, `on_hand`, `reserved`, and
`available` (on_hand minus reserved).

`GET /items/{sku}` — one item, same shape. 404 if unknown.

`POST /reservations` — body `{"sku": str, "qty": int}`. Holds `qty` units of
`sku`. Responds 201 with `{"id", "sku", "qty", "status", "created_at"}`.
A reservation may only be created when `available >= qty`. `qty` must be a
positive integer. Unknown sku is 404.

`POST /reservations/{id}/release` — returns the held units to availability and
sets status to `released`. Responds 200 with the reservation.

`POST /reservations/{id}/fulfil` — ships the held units: decrements `on_hand`
by `qty`, decrements `reserved` by `qty`, sets status to `fulfilled`. Responds
200 with the reservation.

`GET /reservations/{id}` — one reservation. 404 if unknown.

## Requirements

- Every error response is JSON: `{"error": {"code": str, "message": str}}`
  with an appropriate 4xx/5xx status.
- A malformed or non-JSON body is 400, never a 500.
- `on_hand` and `reserved` must never go negative, under any sequence of calls.
- The service is multi-threaded; concurrent requests must not corrupt counts.
- Reservations are immutable once `released` or `fulfilled` — releasing or
  fulfilling twice is an error, not a silent no-op.
- Include a short `README.md` section at the top of the file as a docstring
  describing how to run it.

Write the whole service in `app.py`. Keep it readable.
--- END SPEC ---

SERVICE SOURCE: E:/GitHub/superpowers-custom/benchmark3/artifacts/P/app.py
ARTIFACT DIRECTORY: E:/GitHub/superpowers-custom/benchmark3/artifacts/P

--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---
DEFECT 1
what: A client that posts deeply nested JSON gets 500 "internal_error" instead of a 400, breaking the stated rule that a malformed body is never a 500.
where: E:/GitHub/superpowers-custom/benchmark3/artifacts/P/app.py:228 (json.loads in parse_json_object catches only json.JSONDecodeError); the RecursionError falls through to the catch-all at app.py:507-509. Endpoint POST /reservations.
repro: POST /reservations with body = "[" * 1500 + "]" * 1500 (Content-Length set, Content-Type application/json) -> HTTP 500 {"error":{"code":"internal_error","message":"An unexpected error occurred."}}. Same with body = '{"a":' * 1500 + "1" + "}" * 1500 -> HTTP 500. Server stderr logged: unhandled error: RecursionError('maximum recursion depth exceeded while decoding a JSON array from a unicode string'). A 900-deep body returns 400 correctly, so the cutoff is Python's recursion limit.
severity: blocking
category: spec

DEFECT 2
what: A client that sends a JSON string containing an unpaired UTF-16 surrogate escape gets 500 "internal_error" instead of a 4xx.
where: E:/GitHub/superpowers-custom/benchmark3/artifacts/P/app.py:240-250 (parse_reservation_request only checks isinstance(sku, str), so a lone surrogate passes validation) and then app.py:281-283, where sqlite3 binds the value and raises UnicodeEncodeError inside transaction(); it reaches the catch-all at app.py:507-509. Endpoint POST /reservations.
repro: curl -X POST -H 'Content-Type: application/json' --data-binary '{"sku":"\ud800","qty":1}' http://127.0.0.1:8911/reservations -> HTTP 500 {"error":{"code":"internal_error","message":"An unexpected error occurred."}}. Also '{"sku":"WIDGET-1\udfff","qty":1}' -> HTTP 500. Server stderr logged: unhandled error: UnicodeEncodeError('utf-8', '\ud800', 0, 1, 'surrogates not allowed'). Contrast: '{"sku":"NOPE","qty":1}' -> HTTP 404, so the same code path returns a proper error for an ordinary unknown sku.
repro-note: the transaction does roll back cleanly; 150 concurrent 500-producing requests interleaved with valid reservations left item counts exactly correct, so this is a wrong status code and not data loss.
severity: blocking
category: validation

DEFECT 3
what: A request whose body is shorter than its Content-Length never gets any response at all and never times out; the connection and its worker thread stay pinned for as long as the client keeps the socket open.
where: E:/GitHub/superpowers-custom/benchmark3/artifacts/P/app.py:447 (body = self.rfile.read(length)) with no timeout set on InventoryHandler (class defined at app.py:420) and no socket timeout on the server, so the read blocks forever.
repro: Opened a socket and sent exactly: POST /reservations HTTP/1.1\r\nHost: x\r\nContent-Length: 100\r\n\r\n{"sku":"WI  (only 10 of the declared 100 body bytes). Waited 15 s: no bytes received at all, connection still open. Repeated with 60 such connections (Content-Length: 500, 4 body bytes each): the service process went from 1 thread to 61 threads, and was still at 61 threads after a further 25 s of complete idleness, i.e. nothing reaps them. Threads only dropped back to 1 when the client side closed the sockets. Other clients were still served (GET /items -> 200) during this, so it is thread/connection exhaustion rather than an immediate outage.
severity: blocking
category: robustness

DEFECT 4
what: Request framing is not validated, so an ambiguously framed request is accepted and the leftover bytes are executed as a second request; a client (or an intermediary that reads the framing differently) can smuggle an extra request past the front of the connection.
where: E:/GitHub/superpowers-custom/benchmark3/artifacts/P/app.py:432-435 in InventoryHandler._read_body: self.headers.get("Content-Length") silently takes the first of several headers, and int(raw_length) accepts values RFC 7230 forbids.
repro: (a) One socket, one write: POST /reservations HTTP/1.1\r\nHost: x\r\nContent-Length: 26\r\nContent-Length: 60\r\n\r\n{"sku":"WIDGET-1","qty":1}GET /items/GADGET-2 HTTP/1.1\r\nHost: x\r\n\r\n  -> the server returned TWO responses: HTTP/1.1 201 Created with {"id":"c4edff3a36204e85a86fb5a11022a939","sku":"WIDGET-1","qty":1,"status":"held",...} followed by HTTP/1.1 200 OK with {"sku":"GADGET-2","name":"Gadget","on_hand":3,"reserved":0,"available":3}. RFC 7230 3.3.3 requires a 400 for conflicting Content-Length values. (b) POST /reservations HTTP/1.1\r\nHost: x\r\nContent-Length: 2_6\r\n\r\n{"sku":"WIDGET-1","qty":1} -> HTTP/1.1 201 Created; Python's int() accepts the underscore, so a non-digit Content-Length is honoured instead of rejected.
severity: blocking
category: security

DEFECT 5
what: On every error where the server decides to hang up, it closes the socket without telling the client, so an HTTP/1.1 client that reuses what looks like a persistent connection loses its next request.
where: E:/GitHub/superpowers-custom/benchmark3/artifacts/P/app.py:453-466 (_send_json never emits a Connection header) and app.py:471-486 / app.py:430,438,442,445,450 which set self.close_connection = True. Affects 413 body_too_large, the chunked-body 400, the bad Content-Length 400s and every http.server-generated error.
repro: Sent POST /reservations HTTP/1.1 with Content-Length: 2000000 and 4 body bytes. Response headers were exactly: HTTP/1.1 413 Request Entity Too Large | Server: InventoryReservation/1.0 Python/3.11.9 | Date: ... | Content-Type: application/json; charset=utf-8 | Content-Length: 104 -- no Connection: close -- and the server then closed the socket (recv returned b''). Same for the chunked rejection (HTTP/1.1 400, no Connection header, socket closed). A pipelined follow-up request sent on that same connection (GET /items/WIDGET-1) was silently dropped and never answered.
severity: minor
category: error-shape

DEFECT 6
what: A malformed request line gets a reply with no HTTP status line and no headers, just a bare JSON body, so the client cannot see the 4xx status at all and generic HTTP clients treat the response as a protocol error.
where: E:/GitHub/superpowers-custom/benchmark3/artifacts/P/app.py:471-486, the send_error override routes through _send_json -> send_response, but at that point self.request_version is still the HTTP/0.9 default, so http.server suppresses the status line and all headers and only the body is written.
repro: Opened a socket and sent exactly: GARBAGE\r\n\r\n  -> received b'{\n  "error": {\n    "code": "bad_request",\n    "message": "Bad request syntax (\'GARBAGE\')"\n  }\n}\n' with nothing before it; the response does not start with "HTTP/". Same for POST /items\r\n\r\n -> b'{... "message": "Bad HTTP/0.9 request type (\'POST\')" ...}' with no status line. The spec requires every error response to carry an appropriate 4xx/5xx status, and here no status is transmitted.
severity: minor
category: error-shape

DEFECT 7
what: HEAD is rejected with 501 on resources that answer GET, so caches, health checks and any client that probes with HEAD cannot use the service.
where: E:/GitHub/superpowers-custom/benchmark3/artifacts/P/app.py:511-515 wires do_GET/do_POST/do_PUT/do_PATCH/do_DELETE but never do_HEAD, so BaseHTTPRequestHandler answers 501. app.py:462 already contains an "if self.command != 'HEAD'" guard in _send_json, so HEAD support was intended but is unreachable dead code.
repro: HEAD /items -> HTTP 501 (Content-Type application/json; charset=utf-8, body code "not_implemented"). HEAD /items/WIDGET-1 -> HTTP 501. The same paths answer GET with 200. OPTIONS /items likewise -> HTTP 501 {"error":{"code":"not_implemented","message":"Unsupported method ('OPTIONS')"}}.
severity: minor
category: spec

--- END EXISTING REPORT ---

## Probe results — contract experiments

# API experiments

No invariant violations found. This does not mean the service is correct — only that these experiments passed.


## Probe results — unspecified-attribute experiments

# Unspecified-attribute experiments

The spec is silent about these; each record is still a reproducible failure. Verify before reporting.

## UNICODE
- `POST /reservations` — lone surrogate escape in sku -> HTTP 500: '{\n  "error": {\n    "code": "internal_error",\n    "message": "An unexpected error occurred."\n  }\n}\n'

## PAYLOAD
- `POST /reservations` — a 1 MB body was ACCEPTED (HTTP 201) — unbounded request bodies are stored/parsed with no limit
- `POST /reservations` — a 8 MB body killed the connection (ConnectionAbortedError(10053, '현재 연결은 사용자의 호스트 시스템의 소프트웨어의 의해 중단되었습니다', None, 10053, None)) — there is no request size limit, so a client can exhaust the server this way

## ROBUSTNESS
- `POST /reservations` — a Content-Length longer than the body hung or dropped the connection: TimeoutError('timed out')



## How to run the service (required — identical for everyone)

Start it on the port you are given, with a fresh database:

```bash
cd <the artifact directory>
rm -f /tmp/rev_<port>.db
PORT=<port> DB=/tmp/rev_<port>.db python app.py > /tmp/rev_<port>.log 2>&1 &
sleep 2
curl -s http://127.0.0.1:<port>/...
```

Drive it with real requests for everything you claim — status codes, response
bodies, state after a sequence, behaviour under repeated or concurrent calls.
Measure rather than infer; a claim you did not observe does not belong in your
report.


## Output contract (follow exactly)

Write the COMPLETE report to the path given to you: every record from the
existing report above, unchanged and in its original order, followed by any
records you are adding. Use the same record shape:

```
DEFECT <n>
what: <one line — the problem, in terms of what a client experiences>
where: <file:line, or the endpoint and the code path>
repro: <the exact request(s) YOU sent and the response(s) you got>
severity: blocking | minor
category: spec | robustness | concurrency | validation | security | error-shape
```

Rules:
- Do not edit, merge, renumber or delete an existing record.
- Add only defects you reproduced yourself against the running service.
- One record per distinct defect.
- If you are adding nothing, write the existing report out unchanged.
- Your final reply must be ONLY the total number of records in the file you wrote.
