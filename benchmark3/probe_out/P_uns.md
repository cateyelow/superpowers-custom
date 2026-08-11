# Unspecified-attribute experiments

The spec is silent about these; each record is still a reproducible failure. Verify before reporting.

## UNICODE
- `POST /reservations` — lone surrogate escape in sku -> HTTP 500: '{\n  "error": {\n    "code": "internal_error",\n    "message": "An unexpected error occurred."\n  }\n}\n'

## PAYLOAD
- `POST /reservations` — a 1 MB body was ACCEPTED (HTTP 201) — unbounded request bodies are stored/parsed with no limit
- `POST /reservations` — a 8 MB body killed the connection (ConnectionAbortedError(10053, '현재 연결은 사용자의 호스트 시스템의 소프트웨어의 의해 중단되었습니다', None, 10053, None)) — there is no request size limit, so a client can exhaust the server this way

## ROBUSTNESS
- `POST /reservations` — a Content-Length longer than the body hung or dropped the connection: TimeoutError('timed out')

