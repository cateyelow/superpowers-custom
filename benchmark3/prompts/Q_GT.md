# Defect audit (reference list)

You are auditing a small HTTP service before it ships, to produce the DEFINITIVE
list of defects it has. You have the spec it was built from and its full source.
Be exhaustive and be strict: this list is the reference others will be measured
against, so a defect you miss is a defect nobody gets credit for finding, and a
non-defect you include penalises everyone.

## How to work

Read the source, then RUN the service and drive it with real requests. Confirm
every defect you report by observing it — include the request you sent and the
response you got. Do not report anything you have not reproduced.

Start it on a port nobody else is using:

```bash
cd <the artifact directory>
PORT=<your port> DB=/tmp/audit_<your port>.db python app.py &
sleep 2
curl -s http://127.0.0.1:<your port>/...
```

## What counts as a defect

- Any violation of the spec, including the "Requirements" section.
- Any way a client can corrupt state, exceed a stated limit, or get a 5xx.
- Anything that makes the service unsafe or unusable in ordinary operation even
  if the spec did not spell it out (crashes, injection, unbounded resource use,
  leaked internals in error responses).

Not a defect: style, naming, structure, missing tests, performance you have not
measured, or anything you merely suspect.

Consider at minimum: malformed and hostile input, wrong types, boundary values,
unicode and control characters, repeated and out-of-order operations,
concurrency, unknown ids, wrong HTTP verbs, error-response shape and status
codes, and the stated data invariants under any sequence of calls.

## Output contract (follow exactly)

Write your findings to the report path given to you, as a plain-text list, one
blank line between records:

```
DEFECT <n>
what: <one line — the problem, in terms of what a client experiences>
where: <file:line, or the endpoint and the code path>
repro: <the exact request(s) you sent and the response(s) you got>
severity: blocking | minor
category: spec | robustness | concurrency | validation | security | error-shape
```

Rules:
- Report only defects you actually reproduced against a running service.
- "blocking" = data can be corrupted or lost, a stated invariant can be broken,
  the service can be crashed or hung, or a documented behaviour is absent.
- One record per distinct defect.
- Your final reply must be ONLY the number of defects you wrote.

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
