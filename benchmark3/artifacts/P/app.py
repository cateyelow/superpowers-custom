"""
# Inventory reservation service

A single-file HTTP service backing a small warehouse. Standard library only
(`http.server`, `json`, `sqlite3`, `threading`) -- no third-party packages.

## Running

    python app.py

Environment variables:

  * `PORT` -- TCP port to listen on (default `8080`).
  * `DB`   -- path to the SQLite database file (default `inv.db`). The file and
              its schema are created on first run and seeded with three items:
              `WIDGET-1` ("Widget", 10 on hand), `GADGET-2` ("Gadget", 3 on
              hand) and `DOODAD-3` ("Doodad", 0 on hand).

Example:

    PORT=9000 DB=/tmp/warehouse.db python app.py

## Endpoints

    GET  /items                       list every item
    GET  /items/{sku}                 one item (404 if unknown)
    POST /reservations                body {"sku": str, "qty": int} -> 201
    GET  /reservations/{id}           one reservation (404 if unknown)
    POST /reservations/{id}/release   return held units to availability
    POST /reservations/{id}/fulfil    ship held units

An item is reported as `{"sku", "name", "on_hand", "reserved", "available"}`
where `available = on_hand - reserved`. A reservation is reported as
`{"id", "sku", "qty", "status", "created_at"}` with `status` one of `held`,
`released` or `fulfilled`.

Every error response is JSON of the form:

    {"error": {"code": "...", "message": "..."}}

## Notes

Requests are served on a thread per connection. All database work happens
inside a single lock-guarded `BEGIN IMMEDIATE` transaction, so read-check-write
sequences (for example "is enough stock available? then reserve it") are
atomic and concurrent requests cannot corrupt the counts. `CHECK` constraints
on the `items` table are a second line of defence: `on_hand` and `reserved` can
never go negative and `reserved` can never exceed `on_hand`.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sqlite3
import sys
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DEFAULT_PORT = 8080
DEFAULT_DB = "inv.db"

# Requests bigger than this are rejected rather than buffered.
MAX_BODY_BYTES = 1 << 20  # 1 MiB

STATUS_HELD = "held"
STATUS_RELEASED = "released"
STATUS_FULFILLED = "fulfilled"

SEED_ITEMS = (
    ("WIDGET-1", "Widget", 10),
    ("GADGET-2", "Gadget", 3),
    ("DOODAD-3", "Doodad", 0),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    sku      TEXT    PRIMARY KEY,
    name     TEXT    NOT NULL,
    on_hand  INTEGER NOT NULL DEFAULT 0 CHECK (on_hand >= 0),
    reserved INTEGER NOT NULL DEFAULT 0 CHECK (reserved >= 0),
    CHECK (reserved <= on_hand)
);

CREATE TABLE IF NOT EXISTS reservations (
    id         TEXT    PRIMARY KEY,
    sku        TEXT    NOT NULL REFERENCES items(sku),
    qty        INTEGER NOT NULL CHECK (qty > 0),
    status     TEXT    NOT NULL CHECK (status IN ('held', 'released', 'fulfilled')),
    created_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS reservations_sku_idx ON reservations(sku);
"""


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class ApiError(Exception):
    """An error that maps directly onto a JSON error response."""

    def __init__(self, status: int, code: str, message: str, headers: dict | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.headers = headers or {}

    def payload(self) -> dict:
        return {"error": {"code": self.code, "message": self.message}}


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #

_conn: sqlite3.Connection | None = None
_db_lock = threading.RLock()


def init_db(path: str) -> sqlite3.Connection:
    """Open (creating if needed) the database and seed it on first run."""
    global _conn

    conn = sqlite3.connect(
        path,
        check_same_thread=False,  # guarded by _db_lock instead
        isolation_level=None,  # we manage transactions explicitly
        timeout=30.0,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)

    if conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.executemany(
                "INSERT OR IGNORE INTO items (sku, name, on_hand, reserved) "
                "VALUES (?, ?, ?, 0)",
                SEED_ITEMS,
            )
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        conn.execute("COMMIT")

    _conn = conn
    return conn


@contextlib.contextmanager
def transaction():
    """Run a block inside an exclusive, immediately-locking transaction.

    The process-wide lock serialises writers within this process; the
    ``BEGIN IMMEDIATE`` protects against any other process sharing the file.
    Raising inside the block rolls the whole thing back.
    """
    assert _conn is not None, "init_db() must run before serving requests"
    with _db_lock:
        _conn.execute("BEGIN IMMEDIATE")
        try:
            yield _conn
        except BaseException:
            with contextlib.suppress(sqlite3.Error):
                _conn.execute("ROLLBACK")
            raise
        _conn.execute("COMMIT")


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string, e.g. 2026-01-31T12:00:00.123Z."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def item_json(row: sqlite3.Row) -> dict:
    return {
        "sku": row["sku"],
        "name": row["name"],
        "on_hand": row["on_hand"],
        "reserved": row["reserved"],
        "available": row["on_hand"] - row["reserved"],
    }


def reservation_json(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "sku": row["sku"],
        "qty": row["qty"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


# --------------------------------------------------------------------------- #
# Request payload validation
# --------------------------------------------------------------------------- #


def parse_json_object(body: bytes) -> dict:
    """Decode a request body that must be a JSON object, else raise ApiError."""
    if not body.strip():
        raise ApiError(400, "invalid_body", "A JSON object body is required.")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        raise ApiError(400, "invalid_body", "Request body must be UTF-8 encoded.")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ApiError(400, "invalid_json", f"Request body is not valid JSON: {exc.msg}.")
    if not isinstance(parsed, dict):
        raise ApiError(400, "invalid_body", "Request body must be a JSON object.")
    return parsed


def parse_reservation_request(body: bytes) -> tuple[str, int]:
    payload = parse_json_object(body)

    sku = payload.get("sku")
    if not isinstance(sku, str) or not sku.strip():
        raise ApiError(400, "invalid_sku", "'sku' is required and must be a non-empty string.")

    qty = payload.get("qty")
    # bool is a subclass of int, but True is not a quantity.
    if isinstance(qty, bool) or not isinstance(qty, int):
        raise ApiError(400, "invalid_qty", "'qty' is required and must be an integer.")
    if qty <= 0:
        raise ApiError(400, "invalid_qty", "'qty' must be a positive integer.")

    return sku.strip(), qty


# --------------------------------------------------------------------------- #
# Endpoint handlers -- each returns (status_code, payload)
# --------------------------------------------------------------------------- #


def list_items(_args: tuple, _body: bytes) -> tuple[int, list]:
    with _db_lock:
        rows = _conn.execute(
            "SELECT sku, name, on_hand, reserved FROM items ORDER BY sku"
        ).fetchall()
    return 200, [item_json(row) for row in rows]


def get_item(args: tuple, _body: bytes) -> tuple[int, dict]:
    (sku,) = args
    with _db_lock:
        row = _conn.execute(
            "SELECT sku, name, on_hand, reserved FROM items WHERE sku = ?", (sku,)
        ).fetchone()
    if row is None:
        raise ApiError(404, "item_not_found", f"No item with sku '{sku}'.")
    return 200, item_json(row)


def create_reservation(_args: tuple, body: bytes) -> tuple[int, dict]:
    sku, qty = parse_reservation_request(body)

    with transaction() as conn:
        item = conn.execute(
            "SELECT on_hand, reserved FROM items WHERE sku = ?", (sku,)
        ).fetchone()
        if item is None:
            raise ApiError(404, "item_not_found", f"No item with sku '{sku}'.")

        available = item["on_hand"] - item["reserved"]
        if available < qty:
            raise ApiError(
                409,
                "insufficient_stock",
                f"Only {available} unit(s) of '{sku}' are available, {qty} requested.",
            )

        reservation = {
            "id": uuid.uuid4().hex,
            "sku": sku,
            "qty": qty,
            "status": STATUS_HELD,
            "created_at": utc_now_iso(),
        }
        conn.execute(
            "UPDATE items SET reserved = reserved + ? WHERE sku = ?", (qty, sku)
        )
        conn.execute(
            "INSERT INTO reservations (id, sku, qty, status, created_at) "
            "VALUES (:id, :sku, :qty, :status, :created_at)",
            reservation,
        )

    return 201, reservation


def get_reservation(args: tuple, _body: bytes) -> tuple[int, dict]:
    (reservation_id,) = args
    with _db_lock:
        row = _conn.execute(
            "SELECT id, sku, qty, status, created_at FROM reservations WHERE id = ?",
            (reservation_id,),
        ).fetchone()
    if row is None:
        raise ApiError(404, "reservation_not_found", f"No reservation with id '{reservation_id}'.")
    return 200, reservation_json(row)


def _load_held_reservation(conn: sqlite3.Connection, reservation_id: str) -> sqlite3.Row:
    """Fetch a reservation that is still `held`, or raise the right ApiError."""
    row = conn.execute(
        "SELECT id, sku, qty, status, created_at FROM reservations WHERE id = ?",
        (reservation_id,),
    ).fetchone()
    if row is None:
        raise ApiError(404, "reservation_not_found", f"No reservation with id '{reservation_id}'.")
    if row["status"] != STATUS_HELD:
        raise ApiError(
            409,
            "reservation_not_held",
            f"Reservation '{reservation_id}' is already {row['status']} and cannot be changed.",
        )
    return row


def release_reservation(args: tuple, _body: bytes) -> tuple[int, dict]:
    (reservation_id,) = args
    with transaction() as conn:
        row = _load_held_reservation(conn, reservation_id)
        # Held units go back to availability; on_hand is untouched.
        conn.execute(
            "UPDATE items SET reserved = reserved - ? WHERE sku = ?",
            (row["qty"], row["sku"]),
        )
        conn.execute(
            "UPDATE reservations SET status = ? WHERE id = ?",
            (STATUS_RELEASED, reservation_id),
        )
        result = reservation_json(row)
        result["status"] = STATUS_RELEASED
    return 200, result


def fulfil_reservation(args: tuple, _body: bytes) -> tuple[int, dict]:
    (reservation_id,) = args
    with transaction() as conn:
        row = _load_held_reservation(conn, reservation_id)
        # The units ship: they leave the warehouse and stop being reserved.
        conn.execute(
            "UPDATE items SET on_hand = on_hand - ?, reserved = reserved - ? WHERE sku = ?",
            (row["qty"], row["qty"], row["sku"]),
        )
        conn.execute(
            "UPDATE reservations SET status = ? WHERE id = ?",
            (STATUS_FULFILLED, reservation_id),
        )
        result = reservation_json(row)
        result["status"] = STATUS_FULFILLED
    return 200, result


# --------------------------------------------------------------------------- #
# Routing
# --------------------------------------------------------------------------- #

ROUTES = (
    ("GET", re.compile(r"^/items$"), list_items),
    ("GET", re.compile(r"^/items/([^/]+)$"), get_item),
    ("POST", re.compile(r"^/reservations$"), create_reservation),
    ("GET", re.compile(r"^/reservations/([^/]+)$"), get_reservation),
    ("POST", re.compile(r"^/reservations/([^/]+)/release$"), release_reservation),
    ("POST", re.compile(r"^/reservations/([^/]+)/fulfil$"), fulfil_reservation),
)


def resolve(method: str, path: str):
    """Return (handler, decoded_args) or raise a 404/405 ApiError."""
    allowed = []
    for route_method, pattern, handler in ROUTES:
        match = pattern.match(path)
        if not match:
            continue
        if route_method == method:
            return handler, tuple(unquote(group) for group in match.groups())
        allowed.append(route_method)

    if allowed:
        permitted = ", ".join(sorted(set(allowed)))
        raise ApiError(
            405,
            "method_not_allowed",
            f"{method} is not allowed on {path}; try {permitted}.",
            {"Allow": permitted},
        )
    raise ApiError(404, "not_found", f"No route for {method} {path}.")


# --------------------------------------------------------------------------- #
# HTTP layer
# --------------------------------------------------------------------------- #


class InventoryHandler(BaseHTTPRequestHandler):
    server_version = "InventoryReservation/1.0"
    protocol_version = "HTTP/1.1"  # every response carries a Content-Length

    # -- plumbing ---------------------------------------------------------- #

    def _read_body(self) -> bytes:
        """Read the request body, always draining it so keep-alive stays sane."""
        if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
            self.close_connection = True
            raise ApiError(400, "invalid_body", "Chunked request bodies are not supported.")

        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            return b""
        try:
            length = int(raw_length)
        except (TypeError, ValueError):
            self.close_connection = True
            raise ApiError(400, "invalid_body", "Content-Length header is not an integer.")
        if length < 0:
            self.close_connection = True
            raise ApiError(400, "invalid_body", "Content-Length header is negative.")
        if length > MAX_BODY_BYTES:
            self.close_connection = True
            raise ApiError(413, "body_too_large", f"Request body exceeds {MAX_BODY_BYTES} bytes.")

        body = self.rfile.read(length)
        if len(body) != length:
            self.close_connection = True
            raise ApiError(400, "invalid_body", "Request body was shorter than Content-Length.")
        return body

    def _send_json(self, status: int, payload, extra_headers: dict | None = None) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            for name, value in (extra_headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            # Client hung up mid-response; nothing useful left to do.
            self.close_connection = True

    def _send_error(self, error: ApiError) -> None:
        self._send_json(error.status, error.payload(), error.headers)

    def send_error(self, code, message=None, explain=None):
        """Keep http.server's own errors (bad request line, 501, ...) in JSON."""
        try:
            short, long_message = self.responses[code]
        except KeyError:
            short, long_message = "Error", "Unknown error"
        self.close_connection = True
        self._send_json(
            code,
            {
                "error": {
                    "code": re.sub(r"[^a-z0-9]+", "_", short.lower()).strip("_") or "error",
                    "message": explain or message or long_message,
                }
            },
        )

    # -- dispatch ---------------------------------------------------------- #

    def _handle(self) -> None:
        try:
            path = urlsplit(self.path).path
            if len(path) > 1 and path.endswith("/"):
                path = path.rstrip("/") or "/"

            body = self._read_body()
            handler, args = resolve(self.command, path)
            status, payload = handler(args, body)
            self._send_json(status, payload)
        except ApiError as error:
            self._send_error(error)
        except sqlite3.Error as exc:
            self.log_message("database error: %s", exc)
            self._send_error(ApiError(500, "database_error", "The request could not be completed."))
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except Exception as exc:  # never leak a traceback to the client
            self.log_message("unhandled error: %r", exc)
            self._send_error(ApiError(500, "internal_error", "An unexpected error occurred."))

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_PATCH = _handle
    do_DELETE = _handle

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(
            "%s [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args)
        )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main() -> int:
    raw_port = os.environ.get("PORT", str(DEFAULT_PORT))
    try:
        port = int(raw_port)
    except ValueError:
        sys.stderr.write(f"PORT must be an integer, got {raw_port!r}\n")
        return 2

    db_path = os.environ.get("DB", DEFAULT_DB)
    init_db(db_path)

    server = ThreadingHTTPServer(("", port), InventoryHandler)
    server.daemon_threads = True
    sys.stderr.write(f"inventory service listening on port {port} (db={db_path})\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("shutting down\n")
    finally:
        server.server_close()
        if _conn is not None:
            with _db_lock:
                _conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
