
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
