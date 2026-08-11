## Machine measurements of this page (run for you before you started)

A deterministic probe opened this exact page in an isolated headless Chromium,
drove it through every state it could reach (load, all fields populated, later
wizard steps, files selected, no-results), and at 375 / 768 / 1280 measured
every element: text and non-text contrast ratios, control boundaries,
focus-indicator and placeholder styles pulled from the CSSOM, touch-target
boxes, accessible names and roles, and clipped scroll containers.

**This is evidence, not a findings list.** The probe measures; it cannot judge.
Known limits, which are your job:

- It over-reports. It flags things no criterion actually forbids — decorative
  hover shadows, controls between 24 and 44 px (which meet WCAG 2.5.8 and miss
  only the softer 44 px touch guidance), and `:disabled` text (WCAG-exempt,
  though a disabled label can still be a real legibility problem when it is the
  page's resting state or carries a status message). **Verify before reporting;
  drop what is not a defect.** A wrong entry in your report costs you.
- It is blind to behaviour. It cannot tell that a button is dead, that a caret
  jumps, that a past date is accepted, that focus is thrown away, that a live
  region floods, or that state gets stuck. **Every defect of that kind is
  yours to find, by driving the page yourself.** Do not let the list below
  narrow where you look — historically that is exactly where reviews go wrong.

Confirm anything you take from this list in your own browser session, and cite
your own measurement in `repro`.

