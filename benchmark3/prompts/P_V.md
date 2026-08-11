# Pre-ship review

You are reviewing a small HTTP service before it ships. You did not build it and
have no history with it.

Your team's review skill is pasted below — follow it. You are the reviewer
yourself; do not dispatch anyone else.

The project's standing rule is that a change is not done until the exact
behaviour has been verified for real, so RUN the service and drive it with
actual requests rather than reading source alone.

Report every defect you find.

--- TEAM SKILL: requesting-code-review ---
---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

# Requesting Code Review

Dispatch a code reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch code reviewer subagent:**

Dispatch a `general-purpose` subagent, filling the template at [code-reviewer.md](code-reviewer.md)

**Placeholders:**
- `{DESCRIPTION}` - Brief summary of what you built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch code reviewer subagent]
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types
  PLAN_OR_REQUIREMENTS: Task 2 from docs/superpowers/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll just review the diff myself instead of dispatching a reviewer" | You're the coordinator — reviewing the diff inline burns the context window you need to keep driving the work. Dispatch a reviewer subagent: the diff and the evaluation live in its context, and only the findings come back to you. |
| "The reviewer needs my whole session history to understand the change" | Hand it precisely crafted context, never your session's history. That keeps the reviewer on the work product, not your thought process. |

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: [code-reviewer.md](code-reviewer.md)

--- END SKILL ---

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
- If you find nothing, write exactly: NO DEFECTS FOUND
- Your final reply must be ONLY the number of defects you wrote.
