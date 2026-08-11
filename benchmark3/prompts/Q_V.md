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
