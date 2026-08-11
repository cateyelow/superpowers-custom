# Second pass — machine-measurement sweep over a finished review

A reviewer has already reviewed this page and written the report below. Their
pass is done and it stands. Your job is the second half of the process: a
deterministic probe measured the page, and you decide what the measurements
mean.

**You are ADDING to the report, not rewriting it.** Every record already in it
stays exactly as written, with its numbering. You append new records, numbered
onward from the last one.

## What to do

1. Read the existing report and the probe output below.
2. For each probe measurement, decide whether it is a defect the existing
   report does NOT already cover. Skip anything already reported, even if the
   existing record words it differently.
3. **Verify every candidate in the browser yourself before you add it.** Cite
   your own measurement in `repro`, not the probe's.
4. Append only what survives. If the probe found nothing the report missed,
   append nothing — that is a valid outcome and better than padding.

## The probe over-reports — you are the filter

It measures; it cannot judge. It emits things no criterion forbids:

- **Decorative hover shadows.** A `:hover` box-shadow is not a focus indicator
  and has no contrast minimum. Not a defect.
- **Controls between 24 and 44 px.** These MEET WCAG 2.5.8 (24x24) and miss
  only the softer 44x44 touch guidance. Report one only if it is genuinely
  hard to hit — a primary action at mobile width, not a secondary text input
  that happens to be 42 px tall.
- **`:disabled` text contrast.** WCAG explicitly exempts inactive controls. It
  is a real defect only when that disabled state is the page's resting state or
  carries a status message the user must read.
- **Elements measured in a state the user cannot actually reach.**

A false entry costs you more than a missed one. When you cannot verify it in
the browser, drop it.

