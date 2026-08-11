"""Appointment booking service for a small clinic.

Run it with the standard library only, no third-party packages:

    python app.py

Environment variables:
    PORT  TCP port to listen on              (default: 8080)
    DB    path to the SQLite database file   (default: appts.db)

The database is created on first run and seeded with two practitioners,
``dr-lee`` (30-minute slots) and ``dr-park`` (20-minute slots).  The clinic is
open 09:00-17:00 UTC and slots tile the day from 09:00 at each practitioner's
slot length.

Endpoints:
    GET  /practitioners
    GET  /practitioners/{id}/availability?date=YYYY-MM-DD
    GET  /practitioners/{id}/appointments?date=YYYY-MM-DD
    POST /appointments
    GET  /appointments/{id}
    POST /appointments/{id}/cancel

Every error response is ``{"error": {"code": ..., "message": ...}}``.
"""

import json
import os
import re
import sqlite3
import threading
import uuid
from datetime import date, datetime, time, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DB_PATH = os.environ.get("DB", "appts.db")
PORT = int(os.environ.get("PORT", "8080"))

OPENING_TIME = time(9, 0)
CLOSING_TIME = time(17, 0)

MAX_BODY_BYTES = 64 * 1024
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SEED_PRACTITIONERS = (
    ("dr-lee", "Dr Lee", 30),
    ("dr-park", "Dr Park", 20),
)

# One connection per thread (SQLite connections are not thread-safe), plus a
# process-wide lock held across the read-check-write section of a booking so
# two threads can never both decide the same slot is free.  `BEGIN IMMEDIATE`
# gives the same guarantee against other processes sharing the database file.
_local = threading.local()
_write_lock = threading.RLock()


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------


class ApiError(Exception):
    """An error that is rendered as a JSON error body with a 4xx status."""

    def __init__(self, status, code, message, headers=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.headers = headers or {}


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------


def get_conn():
    conn = getattr(_local, "conn", None)
    if conn is None:
        # isolation_level=None -> autocommit; transactions are explicit below.
        conn = sqlite3.connect(DB_PATH, timeout=30.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return conn


def init_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS practitioners (
            id           TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            slot_minutes INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id               TEXT PRIMARY KEY,
            practitioner_id  TEXT NOT NULL REFERENCES practitioners(id),
            patient_name     TEXT NOT NULL,
            starts_at        TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            status           TEXT NOT NULL CHECK (status IN ('booked', 'cancelled')),
            created_at       TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_appointments_practitioner_start
        ON appointments (practitioner_id, starts_at)
        """
    )
    # Defence in depth: the same practitioner can never hold two *booked*
    # appointments starting at the same instant, even if the check below is
    # somehow bypassed.  Cancelled rows are excluded so a freed slot is
    # re-bookable.
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_appointments_unique_booked_start
        ON appointments (practitioner_id, starts_at) WHERE status = 'booked'
        """
    )
    for practitioner_id, name, slot_minutes in SEED_PRACTITIONERS:
        conn.execute(
            "INSERT OR IGNORE INTO practitioners (id, name, slot_minutes) VALUES (?, ?, ?)",
            (practitioner_id, name, slot_minutes),
        )


def find_practitioner(practitioner_id):
    row = get_conn().execute(
        "SELECT id, name, slot_minutes FROM practitioners WHERE id = ?",
        (practitioner_id,),
    ).fetchone()
    if row is None:
        raise ApiError(
            404, "practitioner_not_found", "no practitioner with id %r" % practitioner_id
        )
    return row


def find_appointment(appointment_id):
    row = get_conn().execute(
        "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
    ).fetchone()
    if row is None:
        raise ApiError(
            404, "appointment_not_found", "no appointment with id %r" % appointment_id
        )
    return row


# --------------------------------------------------------------------------
# Time helpers
# --------------------------------------------------------------------------


def now_utc():
    return datetime.now(timezone.utc)


def fmt_utc(moment):
    """Canonical wire/storage format: 2030-01-01T09:00:00Z."""
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc_timestamp(value):
    """Parse an ISO-8601 UTC timestamp.  A naive value is taken as UTC."""
    if not isinstance(value, str) or not value.strip():
        raise ApiError(
            400,
            "invalid_starts_at",
            "starts_at must be an ISO-8601 UTC timestamp, e.g. 2030-01-01T09:00:00Z",
        )
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        raise ApiError(
            400,
            "invalid_starts_at",
            "starts_at is not a valid ISO-8601 timestamp: %s" % value,
        )
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    if moment.utcoffset() != timedelta(0):
        raise ApiError(
            400,
            "invalid_starts_at",
            "starts_at must be expressed in UTC (offset +00:00 or a trailing Z)",
        )
    return moment.astimezone(timezone.utc)


def parse_date_param(query):
    values = query.get("date") or []
    if not values or not values[-1].strip():
        raise ApiError(
            400, "missing_date", "query parameter 'date' is required, formatted YYYY-MM-DD"
        )
    text = values[-1].strip()
    if not DATE_RE.match(text):
        raise ApiError(400, "invalid_date", "date must be formatted YYYY-MM-DD, got %r" % text)
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ApiError(400, "invalid_date", "date is not a real calendar date: %r" % text)


def opening_hours(day):
    """The (opens, closes) datetimes for a given calendar day, in UTC."""
    opens = datetime.combine(day, OPENING_TIME, tzinfo=timezone.utc)
    closes = datetime.combine(day, CLOSING_TIME, tzinfo=timezone.utc)
    return opens, closes


def slot_starts(day, slot_minutes):
    """Every slot start on `day`; only slots that end by closing time count."""
    opens, closes = opening_hours(day)
    step = timedelta(minutes=slot_minutes)
    starts = []
    current = opens
    while current + step <= closes:
        starts.append(current)
        current += step
    return starts


def overlaps(start_a, end_a, start_b, end_b):
    """Half-open intervals: touching at an edge is not an overlap."""
    return start_a < end_b and start_b < end_a


def booked_intervals(conn, practitioner_id, day):
    """(start, end) of every booked appointment for that practitioner that day."""
    day_start = fmt_utc(datetime.combine(day, time(0, 0), tzinfo=timezone.utc))
    day_end = fmt_utc(datetime.combine(day + timedelta(days=1), time(0, 0), tzinfo=timezone.utc))
    rows = conn.execute(
        """
        SELECT starts_at, duration_minutes FROM appointments
        WHERE practitioner_id = ? AND status = 'booked'
          AND starts_at >= ? AND starts_at < ?
        """,
        (practitioner_id, day_start, day_end),
    ).fetchall()
    intervals = []
    for row in rows:
        start = parse_utc_timestamp(row["starts_at"])
        intervals.append((start, start + timedelta(minutes=row["duration_minutes"])))
    return intervals


# --------------------------------------------------------------------------
# Serialisation
# --------------------------------------------------------------------------


def practitioner_json(row):
    return {"id": row["id"], "name": row["name"], "slot_minutes": row["slot_minutes"]}


def appointment_json(row):
    return {
        "id": row["id"],
        "practitioner_id": row["practitioner_id"],
        "patient_name": row["patient_name"],
        "starts_at": row["starts_at"],
        "duration_minutes": row["duration_minutes"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def parse_json_object(raw):
    if not raw or not raw.strip():
        raise ApiError(400, "invalid_json", "request body must be a JSON object")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ApiError(400, "invalid_json", "request body is not valid JSON")
    if not isinstance(data, dict):
        raise ApiError(400, "invalid_json", "request body must be a JSON object")
    return data


def required_string(data, field):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ApiError(400, "invalid_" + field, "%s must be a non-empty string" % field)
    return value.strip()


# --------------------------------------------------------------------------
# Endpoint handlers: (match, query, body) -> (status, payload)
# --------------------------------------------------------------------------


def list_practitioners(match, query, body):
    rows = get_conn().execute(
        "SELECT id, name, slot_minutes FROM practitioners ORDER BY id"
    ).fetchall()
    return 200, [practitioner_json(row) for row in rows]


def get_availability(match, query, body):
    practitioner = find_practitioner(match.group("id"))
    day = parse_date_param(query)
    slot_minutes = practitioner["slot_minutes"]
    conn = get_conn()
    taken = booked_intervals(conn, practitioner["id"], day)

    free = []
    for start in slot_starts(day, slot_minutes):
        end = start + timedelta(minutes=slot_minutes)
        if not any(overlaps(start, end, busy_start, busy_end) for busy_start, busy_end in taken):
            free.append(fmt_utc(start))
    return 200, free


def list_practitioner_appointments(match, query, body):
    practitioner = find_practitioner(match.group("id"))
    day = parse_date_param(query)
    day_start = fmt_utc(datetime.combine(day, time(0, 0), tzinfo=timezone.utc))
    day_end = fmt_utc(datetime.combine(day + timedelta(days=1), time(0, 0), tzinfo=timezone.utc))
    rows = get_conn().execute(
        """
        SELECT * FROM appointments
        WHERE practitioner_id = ? AND starts_at >= ? AND starts_at < ?
        ORDER BY starts_at ASC, created_at ASC
        """,
        (practitioner["id"], day_start, day_end),
    ).fetchall()
    return 200, [appointment_json(row) for row in rows]


def get_appointment(match, query, body):
    return 200, appointment_json(find_appointment(match.group("id")))


def create_appointment(match, query, body):
    data = parse_json_object(body)

    practitioner_id = required_string(data, "practitioner_id")
    patient_name = required_string(data, "patient_name")
    starts_at = parse_utc_timestamp(data.get("starts_at"))

    duration = data.get("duration_minutes")
    if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0:
        raise ApiError(
            400, "invalid_duration_minutes", "duration_minutes must be a positive integer"
        )

    practitioner = find_practitioner(practitioner_id)
    slot_minutes = practitioner["slot_minutes"]

    if duration % slot_minutes != 0:
        raise ApiError(
            400,
            "invalid_duration_minutes",
            "duration_minutes must be a multiple of %d for practitioner %s"
            % (slot_minutes, practitioner["id"]),
        )

    if starts_at <= now_utc():
        raise ApiError(400, "starts_at_in_past", "starts_at must be in the future")

    ends_at = starts_at + timedelta(minutes=duration)
    opens, closes = opening_hours(starts_at.date())
    if starts_at < opens or ends_at > closes:
        raise ApiError(
            400,
            "outside_opening_hours",
            "the appointment must fit inside opening hours (%s-%s UTC)"
            % (OPENING_TIME.strftime("%H:%M"), CLOSING_TIME.strftime("%H:%M")),
        )

    offset_seconds = (starts_at - opens).total_seconds()
    if offset_seconds % (slot_minutes * 60) != 0:
        raise ApiError(
            400,
            "not_a_slot_boundary",
            "starts_at must land on a %d-minute slot boundary from %s UTC"
            % (slot_minutes, OPENING_TIME.strftime("%H:%M")),
        )

    row_id = uuid.uuid4().hex
    created_at = fmt_utc(now_utc())
    stored_start = fmt_utc(starts_at)
    conn = get_conn()

    # Checking for a clash and inserting must be atomic, otherwise two
    # concurrent requests could both see a free slot.
    with _write_lock:
        conn.execute("BEGIN IMMEDIATE")
        try:
            for busy_start, busy_end in booked_intervals(conn, practitioner["id"], starts_at.date()):
                if overlaps(starts_at, ends_at, busy_start, busy_end):
                    raise ApiError(
                        409,
                        "slot_unavailable",
                        "that time overlaps an existing booked appointment for %s"
                        % practitioner["id"],
                    )
            conn.execute(
                """
                INSERT INTO appointments
                    (id, practitioner_id, patient_name, starts_at,
                     duration_minutes, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'booked', ?)
                """,
                (row_id, practitioner["id"], patient_name, stored_start, duration, created_at),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            _rollback(conn)
            raise ApiError(
                409,
                "slot_unavailable",
                "that time overlaps an existing booked appointment for %s" % practitioner["id"],
            )
        except BaseException:
            _rollback(conn)
            raise

    return 201, appointment_json(find_appointment(row_id))


def cancel_appointment(match, query, body):
    appointment_id = match.group("id")
    conn = get_conn()

    with _write_lock:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute(
                "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
            ).fetchone()
            if row is None:
                raise ApiError(
                    404,
                    "appointment_not_found",
                    "no appointment with id %r" % appointment_id,
                )
            if row["status"] != "booked":
                raise ApiError(
                    409,
                    "already_cancelled",
                    "appointment %s is already cancelled" % appointment_id,
                )
            conn.execute(
                "UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,)
            )
            conn.execute("COMMIT")
        except BaseException:
            _rollback(conn)
            raise

    return 200, appointment_json(find_appointment(appointment_id))


def _rollback(conn):
    try:
        conn.execute("ROLLBACK")
    except sqlite3.Error:
        pass


# --------------------------------------------------------------------------
# Routing
# --------------------------------------------------------------------------

SEGMENT = r"(?P<id>[^/]+)"

ROUTES = (
    ("GET", re.compile(r"^/practitioners$"), list_practitioners),
    ("GET", re.compile(r"^/practitioners/%s/availability$" % SEGMENT), get_availability),
    ("GET", re.compile(r"^/practitioners/%s/appointments$" % SEGMENT), list_practitioner_appointments),
    ("POST", re.compile(r"^/appointments$"), create_appointment),
    ("GET", re.compile(r"^/appointments/%s$" % SEGMENT), get_appointment),
    ("POST", re.compile(r"^/appointments/%s/cancel$" % SEGMENT), cancel_appointment),
)


class Handler(BaseHTTPRequestHandler):
    server_version = "ClinicBooking/1.0"
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_PATCH(self):
        self._handle("PATCH")

    def do_DELETE(self):
        self._handle("DELETE")

    def do_HEAD(self):
        self._handle("HEAD")

    # -- plumbing ---------------------------------------------------------

    def _handle(self, method):
        try:
            status, payload = self._dispatch(method)
            self._send_json(status, payload)
        except ApiError as err:
            self._send_error(err)
        except Exception as exc:  # never leak a traceback / bare 500 page
            self.log_error("unhandled error: %r", exc)
            self._send_json(
                500,
                {"error": {"code": "internal_error", "message": "internal server error"}},
                close=True,
            )

    def _dispatch(self, method):
        parts = urlsplit(self.path)
        path = unquote(parts.path)
        if len(path) > 1:
            path = path.rstrip("/") or "/"
        query = parse_qs(parts.query, keep_blank_values=True)
        body = self._read_body() if method in ("POST", "PUT", "PATCH") else b""

        allowed = []
        for route_method, pattern, handler in ROUTES:
            match = pattern.match(path)
            if not match:
                continue
            if route_method != method:
                allowed.append(route_method)
                continue
            return handler(match, query, body)

        if allowed:
            raise ApiError(
                405,
                "method_not_allowed",
                "%s is not allowed on %s" % (method, path),
                headers={"Allow": ", ".join(sorted(set(allowed)))},
            )
        raise ApiError(404, "not_found", "no route for %s %s" % (method, path))

    def _read_body(self):
        header = self.headers.get("Content-Length")
        if header is None:
            if "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():
                raise ApiError(
                    411, "length_required", "a Content-Length header is required"
                )
            return b""
        try:
            length = int(header)
        except (TypeError, ValueError):
            raise ApiError(400, "invalid_content_length", "Content-Length is not a number")
        if length < 0:
            raise ApiError(400, "invalid_content_length", "Content-Length is negative")
        if length > MAX_BODY_BYTES:
            raise ApiError(413, "payload_too_large", "request body is too large")
        return self.rfile.read(length)

    def _send_error(self, err):
        self._send_json(
            err.status,
            {"error": {"code": err.code, "message": err.message}},
            headers=err.headers,
            close=True,
        )

    def _send_json(self, status, payload, headers=None, close=False):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        if close:
            # An error can be raised before the request body was drained, so
            # close rather than risk a desynchronised keep-alive connection.
            self.close_connection = True
            self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

def main():
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    print("listening on http://0.0.0.0:%d (database: %s)" % (PORT, DB_PATH), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
