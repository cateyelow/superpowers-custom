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
