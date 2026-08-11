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

PAGE UNDER REVIEW: file:///E:/GitHub/superpowers-custom/benchmark2/runs2/B_D3/checkout.html

--- THE EXISTING REPORT (passes 1-2 — keep every record verbatim) ---
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

DEFECT 9
what: Every text field and the country select is a white box on a white card whose only boundary is a 1.47:1 hairline, so at a glance the form reads as a list of labels with no visible input areas.
where: checkout.html:158-168 `input, select { border: 1px solid var(--border); background: #fff }` with `--border: #d0d5dd` (checkout.html:14), inside `.checkout-card` whose background is `var(--surface)` = #ffffff (checkout.html:13, 40-42)
repro: Isolated headless Chromium at 1280x900, resting state, no focus/hover. getComputedStyle on all four sides of #full-name returned borderColor rgb(208,213,221), borderWidth 1px, borderStyle solid, backgroundColor rgb(255,255,255), boxShadow 'none', outlineStyle 'none'; the nearest painted ancestor background is MAIN.checkout-card rgb(255,255,255). Computed contrast border vs both the field fill and the card behind it = 1.47:1, against the 3:1 WCAG 1.4.11 minimum for the boundary of a control. Identical measurement on #address, #city, #postal-code and #country on step 1, and on #cardholder-name, #card-number, #expiry and #cvc after advancing to step 2 (nine controls, all 1.47:1); unchanged at 375px width (field 293x48, border still rgb(208,213,221)). Screenshot of the step-1 form shows the field outlines as faint grey ghosts. The same token also draws the secondary "Back" button (white fill on the white card, border 1.47:1). This is the resting state, not the focused one: after the 140ms transition settles a focused input does turn its border rgb(49,87,213) = 6.08:1, which is why I am not reporting the faint 4px focus halo.
severity: minor
category: contrast

--- END EXISTING REPORT ---

## Experiment results

# Behavioural experiments

Each record is a user-reachable sequence that broke an invariant. Reproduce it yourself before reporting it.

## SEMANTIC
- `#expiry` — an expiry already in the past ("01/20") passes validation — checkValidity() === true. The pattern checks the SHAPE only, never the date.

## CARET
- `#card-number` — typed a digit at offset 9 of '4111 1111 1111 1111'; the caret jumped to 21 (end of field, value now '4111 1111 9111 1111 1'), so continued typing lands in the wrong place
- `#card-number` — placed the caret just past the auto-inserted separator in '4111 1111 1111 1111' (offset 5) and pressed Backspace: nothing was removed (value unchanged) and the caret was thrown to 19

## ERROR-STATE
- `#full-name, #address, #city, #postal-code, #country` — 5 field(s) reject their value, but none sets aria-invalid and the page contains zero [aria-live] / [role=alert] / [role=status] elements. The only error signal is the browser's transient bubble. Validation messages seen: "Please fill out this field.", "Please fill out this field.", "Please fill out this field.". 5 of them also state the required format nowhere (no title, no aria-describedby).



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
what: <one line>
where: <file:line, or a CSS selector / element description>
repro: <how YOU observed it>
severity: blocking | minor
category: a11y | contrast | touch-target | responsive | state | logic | spec
```

Rules:
- Do not edit, merge, renumber or delete an existing record.
- Add only defects you reproduced yourself in the browser.
- One record per distinct defect.
- If you are adding nothing, write the existing report out unchanged.
- Your final reply to me must be ONLY the total number of records in the file you wrote.
