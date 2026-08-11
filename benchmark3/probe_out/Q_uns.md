# Unspecified-attribute experiments

The spec is silent about these; each record is still a reproducible failure. Verify before reporting.

## PAYLOAD
- `POST /appointments` — a 8 MB body killed the connection (ConnectionAbortedError(10053, '현재 연결은 사용자의 호스트 시스템의 소프트웨어의 의해 중단되었습니다', None, 10053, None)) — there is no request size limit, so a client can exhaust the server this way

## ROBUSTNESS
- `POST /appointments` — a Content-Length longer than the body hung or dropped the connection: TimeoutError('timed out')

