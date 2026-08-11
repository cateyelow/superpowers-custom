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
