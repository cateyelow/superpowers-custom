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
