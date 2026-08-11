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
