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


--- SPEC THE PAGE WAS BUILT FROM ---
# Task: three-step checkout form

Build a single HTML file (all CSS/JS inline, no frameworks, no build tools, no
network calls) implementing a three-step checkout flow.

## Deliverable
- `checkout.html`

## Requirements

R1. Step 1 collects shipping details: full name, address line, city, postal code,
    country (a select with at least 5 countries).
R2. Step 2 collects payment details: cardholder name, card number, expiry (MM/YY),
    CVC.
R3. Step 3 shows a read-only summary of everything entered in steps 1 and 2, with
    the card number masked except the last 4 digits, and a "Place order" button.
R4. Next/Back controls move between steps. Only one step is visible at a time.
R5. A step indicator shows which of the three steps is current.
R6. "Place order" replaces the form with a confirmation message containing an
    order number.

Open `checkout.html` directly in a browser (`file://`) — it must work with no server.
--- END SPEC ---

PAGE UNDER REVIEW: file:///E:/GitHub/superpowers-custom/benchmark2/runs2/B_D2/checkout.html

--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---
DEFECT 1
what: Keyboard focus on the Next / Back / Place order buttons is all but invisible — the focus ring measures 1.35:1 against the card behind it, so a keyboard user cannot tell which button is focused.
where: checkout.html:207-210 `button:focus-visible { outline: 3px solid var(--focus) }`, with `--focus: rgba(49, 87, 213, 0.2)` at checkout.html:18
repro: Clicked #postal-code, pressed Tab twice to land on the step-1 "Next" button (activeElement.matches(':focus-visible') === true). Computed outlineColor = rgba(49,87,213,0.2), outlineWidth 3px, outlineOffset 2px; composited over the card background rgb(255,255,255) that is rgb(213.8,221.4,246.6) = 1.35:1, versus the 3:1 minimum for a focus indicator. Same measurement on the step-2 "Back" button. Focused inputs by comparison get border-color rgb(49,87,213) = 6.08:1 plus a 4px halo, so the buttons are the only controls with no perceivable focus state (screenshots of the focused button vs focused input confirm it).
severity: minor
category: a11y

DEFECT 2
what: Pressing Enter in a text field never advances the form and produces no feedback of any kind — the form appears dead to that key.
where: checkout.html:628-641 (submit handler returns early when currentStep !== 2) combined with the `required` inputs inside the hidden steps
repro: Filled every step-1 field, focused #postal-code, pressed Enter: still on step 1, no visible message, and the console logged 4 errors — "An invalid form control with name='cardholderName' is not focusable" plus the same for cardNumber, expiry, cvc. Repeated on step 2 after filling every field (verified all 9 inputs/selects checkValidity() === true): pressed Enter, still on step 2, confirmation stayed hidden, nothing logged. Clicking the Next button in the same state works.
severity: minor
category: a11y

DEFECT 3
what: The step-indicator connector line is painted on top of the step labels, so "Shipping" and "Payment" look struck through.
where: checkout.html:87-96 `.step-indicator li:not(:last-child)::after` (position:absolute; top:16px; left:34px; width:calc(100% - 26px); z-index:0) overlapping `.step-label`
repro: At 1280x900 the ::after box resolves to x=383.0-545.7, y=193.5-195.5 while the "Shipping" label box is x=389.0-447.9, y=183.0-204.0 — a 58.9px x 2.0px overlap; the "Payment" label overlaps by 57.8px x 2.0px. Because the pseudo-element is positioned with z-index:0 it paints above the label text. Screenshot of `.step-indicator` at 1280 shows a line running through the middle of both words, and the same at 768. Not present at 375 where `.step-label` is clipped to 1x1.
severity: minor
category: responsive

DEFECT 4
what: Placeholder text in the payment fields is too faint to read reliably (2.58:1).
where: checkout.html:170-172 `input::placeholder { color: #98a2b3 }` — affects #card-number ("1234 5678 9012 3456"), #expiry ("MM/YY"), #cvc ("123")
repro: getComputedStyle(document.querySelector('#card-number'), '::placeholder').color = rgb(152,162,179) on the input background rgb(255,255,255), font-size 16px, weight 400 → measured contrast 2.58:1, below the 4.5:1 AA threshold for normal-size text. Every other text colour on the page measured >= 4.76:1.
severity: minor
category: contrast

DEFECT 5
what: Editing the middle of the card number jumps the caret to the end of the field, so the following keystroke lands in the wrong position.
where: checkout.html:614-617 `cardNumber.addEventListener("input", ...)` reassigns cardNumber.value without restoring the selection; element #card-number
repro: Typed 4111111111111111 → "4111 1111 1111 1111". Then setSelectionRange(2,2) and typed "9": value became "4191 1111 1111 1111 1" and selectionStart jumped from 3 to 21 (end of value). Same with deletion: caret set to 6, pressed Backspace → value "4111 1111 1111 111" and selectionStart = 18 (end) instead of 5.
severity: minor
category: state

DEFECT 6
what: The card number field accepts a 10-digit number even though the hint directly beneath it says "12 to 19 digits", and the review step then presents it as a normal masked card.
where: checkout.html:412 `pattern="[0-9 ]{12,23}"` on #card-number vs the hint text at checkout.html:413
repro: Typed 1234567890 into #card-number → field shows "1234 5678 90", which is 12 characters only because the formatter inserted 2 spaces; document.getElementById('card-number').checkValidity() returned true. Clicking Next advanced to step 3, where the summary rendered "•••• ••78 90". The pattern counts the auto-inserted spaces, so anything from 10 digits upward satisfies it.
severity: minor
category: logic

DEFECT 7
what: A name and address typed as spaces only pass validation, and the review step then shows both fields completely blank while the order can still be placed.
where: checkout.html:362 and 367 (`required` on #full-name / #address) with the `.trim()` in updateSummary(), checkout.html:590-591; rendered into dd#summary-full-name / dd#summary-address
repro: Entered "   " (three spaces) in Full name and in Address line, with a real city, postal code and country; clicked Next → advanced to step 2 with no complaint. Completed payment and clicked Next → step 3 summary shows the FULL NAME and ADDRESS LINE labels with empty values (verified textContent === '' for both, and captured in a screenshot of `.summary`). "Place order" then produced a confirmation with an order number for an order that has no name or address.
severity: minor
category: logic

DEFECT 8
what: The CVC is printed in clear text on the review step even though the field masks it while the user types it.
where: dd#summary-cvc at checkout.html:481, populated at checkout.html:598; the source input #cvc is type="password" (checkout.html:423)
repro: Entered 123 into the CVC field (rendered as dots, get_attribute('#cvc','type') === 'password'), clicked Next → the Payment panel of the review step displays "CVC 123" as readable text (textContent === '123'), confirmed in screenshots at both 1280 and 375. The card number immediately above it is masked to "•••• •••• •••• 1111", so the same screen hides the card but exposes the security code.
severity: minor
category: spec

--- END EXISTING REPORT ---

## Probe output

States the probe reached: load, step-2
Probe log: seeded 9 field(s); advanced to step 2; advanced to step 3

### Control boundaries below the WCAG 1.4.11 3:1 minimum
- `#full-name` — border 1.47:1 against its backdrop (state: load)
- `#address` — border 1.47:1 against its backdrop (state: load)
- `#city` — border 1.47:1 against its backdrop (state: load)
- `#postal-code` — border 1.47:1 against its backdrop (state: load)
- `#country` — border 1.47:1 against its backdrop (state: load)
- `#cardholder-name` — border 1.47:1 against its backdrop (state: step-2)
- `#card-number` — border 1.47:1 against its backdrop (state: step-2)
- `#expiry` — border 1.47:1 against its backdrop (state: step-2)
- `#cvc` — border 1.47:1 against its backdrop (state: step-2)
- `button.button-secondary` — border 1.47:1 against its backdrop (state: step-2)

### Focus indicators and placeholder text (pulled from the CSSOM — these never appear in getComputedStyle of the resting element)
- `input:focus` { box-shadow: 0 0 0 4px var(--focus) } — 1.35:1, needs 3:1, composites to rgb(214,221,247) (matches 4, e.g. `#full-name`)
- `select:focus` { box-shadow: 0 0 0 4px var(--focus) } — 1.35:1, needs 3:1, composites to rgb(214,221,247) (matches 1, e.g. `#country`)
- `button:focus-visible` { outline: 3px solid var(--focus) } — 1.35:1, needs 3:1, composites to rgb(214,221,247) (matches 1, e.g. `button.button-primary`)
- `input::placeholder` { color: rgb(152, 162, 179) } — 2.58:1, needs 4.5:1 (matches 4, e.g. `#full-name`)

## How to open the page (required — identical for everyone)

Do NOT use the Playwright MCP tools. On this machine they block `file:` URLs and
they drive a Chrome shared with other concurrent sessions, so your observations
would be corrupted by other people's clicks.

Drive your own isolated browser from Python instead. This is verified working
here:

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    pg.goto('file:///<PAGE_PATH>')
    # pg.evaluate(...) for computed styles, sizes, contrast
    # pg.set_viewport_size({'width': 375, 'height': 800}) for responsive checks
    # pg.click / pg.fill / pg.keyboard for interaction
    b.close()
```

Use it for everything you claim: computed styles and colours, element boxes and
touch-target sizes, focus order, viewport behaviour at 375 / 768 / 1280, and
actual interaction. Measure rather than infer — a claim you did not verify in
the browser does not belong in your report.

## Output contract (follow exactly)

Write the COMPLETE report to the path given to you: every record from the existing report above, unchanged and in its original order, followed by any records you are adding. Use the same record shape:

```
DEFECT <n>
what: <one line — the user-visible problem>
where: <file:line, or a CSS selector / element description>
repro: <how YOU observed it — the steps or the measurement>
severity: blocking | minor
category: a11y | contrast | touch-target | responsive | state | logic | spec
```

Rules:
- Do not edit, merge, renumber or delete an existing record.
- Add only defects you verified yourself in the browser.
- One record per distinct defect.
- If you are adding nothing, write the existing report out unchanged.
- Your final reply to me must be ONLY the total number of records in the file you wrote.
