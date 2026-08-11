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
# Appointment booking service

A single-file Python HTTP service for booking appointments with a small clinic.
Stdlib only (`http.server`, `json`, `sqlite3`, `threading`, `datetime`) — no
third-party packages. Starts with `python app.py`, listens on `$PORT`
(default 8080), state in SQLite at `$DB` (default `appts.db`).

## Data

A `practitioners` table: `id` (text), `name` (text), `slot_minutes` (integer).
An `appointments` table: `id` (text), `practitioner_id` (text),
`patient_name` (text), `starts_at` (ISO-8601 UTC string), `duration_minutes`
(integer), `status` (text: `booked` | `cancelled`), `created_at`.

Seed two practitioners on first run: `dr-lee` ("Dr Lee", 30-minute slots) and
`dr-park` ("Dr Park", 20-minute slots).

## Endpoints

`GET /practitioners` — list all.

`GET /practitioners/{id}/availability?date=YYYY-MM-DD` — the free slots for
that practitioner on that date, as a list of ISO-8601 UTC start times. The
clinic is open 09:00-17:00 UTC, and slots tile the day at `slot_minutes`
intervals from 09:00. A slot is free when no `booked` appointment overlaps it.

`POST /appointments` — body `{"practitioner_id", "patient_name", "starts_at",
"duration_minutes"}`. Responds 201 with the appointment.
  - `starts_at` must be a valid ISO-8601 UTC timestamp, in the future, and land
    exactly on one of the practitioner's slot boundaries.
  - The appointment must fit inside opening hours.
  - It must not overlap an existing `booked` appointment for that practitioner.
  - `duration_minutes` must be a positive multiple of the practitioner's
    `slot_minutes`.
  - `patient_name` must be a non-empty string after trimming.

`POST /appointments/{id}/cancel` — sets status to `cancelled`, freeing the
slot. Responds 200 with the appointment.

`GET /appointments/{id}` — one appointment. 404 if unknown.

`GET /practitioners/{id}/appointments?date=YYYY-MM-DD` — that practitioner's
appointments on that date, earliest first.

## Requirements

- Every error response is JSON: `{"error": {"code": str, "message": str}}`
  with an appropriate 4xx status.
- A malformed or non-JSON body is 400, never a 500.
- Two overlapping appointments for the same practitioner must never both be
  `booked`, under any sequence of calls.
- The service is multi-threaded; concurrent requests must not corrupt state.
- Cancelling an already-cancelled appointment is an error, not a silent no-op.
- Include a short docstring at the top describing how to run it.

Write the whole service in `app.py`. Keep it readable.
--- END SPEC ---

SERVICE SOURCE: E:/GitHub/superpowers-custom/benchmark3/artifacts/Q/app.py
ARTIFACT DIRECTORY: E:/GitHub/superpowers-custom/benchmark3/artifacts/Q

--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---
DEFECT 1
what: A syntactically deep (but well-formed) JSON request body makes POST /appointments return 500 "internal_error" instead of a 400. The spec states outright that a malformed / non-JSON body must be 400 and "never a 500", so any client sending a 10 KB body of nested brackets gets a server error.
where: app.py:289-298 parse_json_object() - json.loads() at app.py:293 raises RecursionError, which is not one of the caught (UnicodeDecodeError, ValueError) at app.py:294, so it escapes to the generic handler at app.py:529-535. Endpoint POST /appointments.
repro: python -c "import sys;sys.stdout.buffer.write(b'['*5000+b']'*5000)" > nest.json ; curl -s -w " [%{http_code}]" -X POST http://127.0.0.1:8912/appointments -H 'Content-Type: application/json' --data-binary @nest.json
  -> {"error": {"code": "internal_error", "message": "internal server error"}} [500]
  server log: unhandled error: RecursionError('maximum recursion depth exceeded while decoding a JSON object from a unicode string')
  (also reproduced at depth 20000 and 30000; the service stays up afterwards)
severity: blocking
category: robustness

DEFECT 2
what: A very large integer in duration_minutes crashes the booking request with a 500 instead of a 4xx validation error. duration_minutes is only checked for "positive int" and "multiple of slot_minutes", never for an upper bound, so it reaches timedelta() and overflows.
where: app.py:362-366 (duration validation) then app.py:382 `ends_at = starts_at + timedelta(minutes=duration)`. Endpoint POST /appointments.
repro: curl -s -w " [%{http_code}]" -X POST http://127.0.0.1:8912/appointments -H 'Content-Type: application/json' -d '{"practitioner_id":"dr-lee","patient_name":"A","starts_at":"2026-12-01T10:00:00Z","duration_minutes":300000000000000000000}'
  -> {"error": {"code": "internal_error", "message": "internal server error"}} [500]
  server log: unhandled error: OverflowError('Python int too large to convert to C int')
  (control: duration_minutes 45 -> 400 invalid_duration_minutes, 0 -> 400, -30 -> 400, "30" -> 400, 30.0 -> 400)
severity: blocking
category: validation

DEFECT 3
what: Any request naming the last representable calendar date (9999-12-31) returns 500 "internal_error" instead of a 4xx. It hits three of the six endpoints: both date-scoped GETs and POST /appointments. The date passes the YYYY-MM-DD validator, then `day + timedelta(days=1)` overflows while building the end-of-day bound.
where: app.py:252 in booked_intervals() and the duplicate at app.py:339 in list_practitioner_appointments(). Reached from get_availability() (app.py:325), list_practitioner_appointments() (app.py:340), and create_appointment() (app.py:411).
repro: curl -s -w " [%{http_code}]" "http://127.0.0.1:8912/practitioners/dr-lee/availability?date=9999-12-31"
  -> {"error": {"code": "internal_error", "message": "internal server error"}} [500]
  curl -s -w " [%{http_code}]" "http://127.0.0.1:8912/practitioners/dr-lee/appointments?date=9999-12-31"
  -> {"error": {"code": "internal_error", "message": "internal server error"}} [500]
  curl -s -w " [%{http_code}]" -X POST http://127.0.0.1:8912/appointments -H 'Content-Type: application/json' -d '{"practitioner_id":"dr-lee","patient_name":"A","starts_at":"9999-12-31T09:00:00Z","duration_minutes":30}'
  -> {"error": {"code": "internal_error", "message": "internal server error"}} [500]
  server log: unhandled error: OverflowError('date value out of range') (x3)
  (control: date=2026-02-30 -> 400 invalid_date, date=0000-01-01 -> 400 invalid_date)
severity: blocking
category: robustness

DEFECT 4
what: A patient_name containing a JSON escape for an unpaired surrogate (e.g. "\ud800bob") returns 500 instead of a 400. The body is accepted by json.loads, then blows up when the value is handed to SQLite. Nothing is persisted, so the client is left with a server error for what is really bad input.
where: app.py:301-305 required_string() does no codepoint validation; the failure surfaces at the INSERT, app.py:419-427, and is turned into a 500 by app.py:529-535. Endpoint POST /appointments.
repro: printf '{"practitioner_id":"dr-lee","patient_name":"\\ud800bob","starts_at":"2026-12-02T09:00:00Z","duration_minutes":30}' > sur.json ; curl -s -w " [%{http_code}]" -X POST http://127.0.0.1:8912/appointments -H 'Content-Type: application/json' --data-binary @sur.json
  -> {"error": {"code": "internal_error", "message": "internal server error"}} [500]
  server log: unhandled error: UnicodeEncodeError('utf-8', '\ud800bob', 0, 1, 'surrogates not allowed')
  follow-up GET /practitioners/dr-lee/appointments?date=2026-12-02 -> 200 [] (nothing written, transaction rolled back cleanly)
  (control: patient_name "a b" -> 201, patient_name "Kim <emoji>" -> 201)
severity: minor
category: robustness

DEFECT 5
what: A whole class of error responses comes back as an HTML page with Content-Type: text/html, not the JSON envelope the spec requires for "every error response". A client parsing the documented {"error": {...}} shape gets a parse failure instead of a usable error code.
where: class Handler (app.py:499-604) never overrides BaseHTTPRequestHandler.send_error / error_message_format, so every failure raised by the HTTP layer before dispatch bypasses _send_error() (app.py:582-588).
repro: curl -s -X TRACE http://127.0.0.1:8912/practitioners
  -> HTTP/1.1 501 Unsupported method ('TRACE'), Content-Type: text/html;charset=utf-8, body "<!DOCTYPE HTML>...<p>Error code: 501</p>..."
  raw socket sending 'GET /appointments/' + 'a'*70000 + ' HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n'
  -> HTTP/1.1 414 Request-URI Too Long, Content-Type: text/html;charset=utf-8, HTML body "<p>Error code: 414</p>"
  raw socket, GET /practitioners with 150 extra request headers -> HTTP/1.1 431 Too many headers, HTML body
  raw socket, request line 'BOGUS\r\n\r\n' -> HTML body, "Error code: 400", "Bad request syntax ('BOGUS')"
  raw socket, 'GET /practitioners HTTP/9.9' -> HTML body, "Error code: 505", "Invalid HTTP version (9.9)"
severity: minor
category: error-shape

DEFECT 6
what: GET /practitioners/{id}/availability advertises slots that can never be booked. For today's date it returns every slot from 09:00 on, including ones already in the past, and POST /appointments then rejects them with 400 starts_at_in_past. A client that books the first slot the availability endpoint offers fails.
where: get_availability() app.py:320-332 filters only on booked-appointment overlap and never compares against now_utc(); create_appointment() app.py:379 does reject the past. Endpoints GET /practitioners/{id}/availability vs POST /appointments.
repro: at 2026-08-11T14:07Z:
  curl -s "http://127.0.0.1:8912/practitioners/dr-lee/availability?date=2026-08-11"
  -> ["2026-08-11T09:00:00Z", "2026-08-11T09:30:00Z", ... "2026-08-11T16:30:00Z"]  (200)
  curl -s -w " [%{http_code}]" -X POST http://127.0.0.1:8912/appointments -H 'Content-Type: application/json' -d '{"practitioner_id":"dr-lee","patient_name":"A","starts_at":"2026-08-11T09:00:00Z","duration_minutes":30}'
  -> {"error": {"code": "starts_at_in_past", "message": "starts_at must be in the future"}} [400]
severity: minor
category: spec

DEFECT 7
what: HEAD is wired up but broken: HEAD on any valid GET route answers 405 Method Not Allowed instead of the resource's headers. The handler explicitly implements do_HEAD and suppresses the body for HEAD, so support was intended, but no route can ever match it.
where: app.py:518-519 do_HEAD -> _handle("HEAD"); the ROUTES table (app.py:489-496) only carries "GET"/"POST", so _dispatch (app.py:545-561) always falls into the 405 branch. The HEAD special case at app.py:603 is dead code.
repro: curl -s -I http://127.0.0.1:8912/practitioners
  -> HTTP/1.1 405 Method Not Allowed / Allow: GET / Content-Length: 93
  (control: curl -s http://127.0.0.1:8912/practitioners -> 200 with the practitioner list)
severity: minor
category: robustness

DEFECT 8
what: A request whose Content-Length is larger than the bytes actually sent hangs forever. The server blocks reading the missing bytes with no timeout, never answers, and holds the connection plus its worker thread indefinitely, so a client (or a flaky network) can pile up threads and sockets at will.
where: app.py:564-580 _read_body(), `return self.rfile.read(length)` at app.py:580; the handler never sets BaseHTTPRequestHandler.timeout and the socket has no read deadline.
repro: raw socket to 127.0.0.1:8912 sending
  POST /appointments HTTP/1.1 / Host: x / Content-Length: 500 / Connection: close / blank line / then only 10 bytes of body
  -> no bytes received at all; client gave up after 6.0s. Repeated with a 16s wait: still no response, connection still open.
  300 such connections opened at once: all 300 accepted and left hanging; server still answered GET /practitioners in 0.01s, so it is a per-connection hang plus unbounded thread/socket accumulation rather than an immediate outage.
severity: minor
category: robustness

--- END EXISTING REPORT ---

## Probe results — contract experiments

# API experiments

No invariant violations found. This does not mean the service is correct — only that these experiments passed.


## Probe results — unspecified-attribute experiments

# Unspecified-attribute experiments

The spec is silent about these; each record is still a reproducible failure. Verify before reporting.

## PAYLOAD
- `POST /appointments` — a 8 MB body killed the connection (ConnectionAbortedError(10053, '현재 연결은 사용자의 호스트 시스템의 소프트웨어의 의해 중단되었습니다', None, 10053, None)) — there is no request size limit, so a client can exhaust the server this way

## ROBUSTNESS
- `POST /appointments` — a Content-Length longer than the body hung or dropped the connection: TimeoutError('timed out')



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
