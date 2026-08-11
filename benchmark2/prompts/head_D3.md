# Third pass — behavioural experiments over a finished review

Two passes are already done on this page: a reviewer reviewed it, and a
deterministic probe measured its static properties. Their combined report is
below and it stands.

Your pass is different in kind. A behavioural probe DROVE the page — it clicked
controls mid-operation, typed into the middle of formatted fields, dispatched
drop events outside the drop zone, submitted invalid values, and watched what
the DOM announced. Each record below is a sequence that broke an invariant.

**You are ADDING to the report, not rewriting it.** Every existing record stays
exactly as written, with its numbering. Append new records numbered onward.

## What to do

1. Read the existing report and the experiment results below.
2. For each experiment result, decide whether it is a defect the report does
   NOT already cover. Skip anything already reported, however differently
   worded.
3. **Reproduce it yourself in the browser before you add it.** These are
   sequences, so reproducing means performing the sequence — not re-reading the
   probe's text. Cite your own observation in `repro`.
4. Append only what survives. Adding nothing is a valid outcome.

## What the experiments can and cannot tell you

Each result names the invariant it broke:

- `RESPONSIVE` — a control did not respond while an async operation was running
- `DROP-GUARD` — a page that accepts dropped files left the browser default in
  place outside its drop zone
- `FOCUS` — activating a control dropped focus to `<body>`
- `SEMANTIC` — a value that is syntactically valid but impossible was accepted
- `BOUNDARY` — a declared constraint did not actually reject values outside it
- `CARET` — editing mid-string moved the caret to the end
- `IDEMPOTENT` — identical input twice duplicated silently
- `ANNOUNCE` — a visible change happened outside any live region
- `ERROR-STATE` — rejected input exposed no programmatic error state

A broken invariant is strong evidence but not automatic proof of a defect. A
`FOCUS` result on a control that legitimately removes itself, or an `ANNOUNCE`
result on a change no user needs told about, is not worth reporting. Judge it,
then verify it.

