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
# Task: drag-and-drop file upload widget

Build a single HTML file (all CSS/JS inline, no frameworks, no build tools, no
network calls) implementing a file upload widget.

## Deliverable
- `upload.html`

## Requirements

R1. A drop zone that accepts files dropped onto it, and also opens a file picker
    when clicked.
R2. Dropped/selected files appear in a list showing each file's name and its size
    in KB.
R3. Each listed file has a Remove control that takes it out of the list.
R4. An "Upload" button starts a simulated upload: each file shows a progress bar
    that animates from 0% to 100% over about 2 seconds, then shows "Done".
R5. While an upload is in progress the Upload button cannot start a second one.
R6. A "Clear all" control empties the list.

Open `upload.html` directly in a browser (`file://`) — it must work with no server.
--- END SPEC ---

PAGE UNDER REVIEW: file:///E:/GitHub/superpowers-custom/benchmark2/runs2/A_D2/upload.html

--- THE EXISTING REPORT (pass 1 — keep every record verbatim) ---
DEFECT 1
what: Tabbing off the drop zone lands on an invisible 1x1px control — focus disappears from the screen entirely, with no indicator anywhere on the page.
where: upload.html:304 <input id="file-input" type="file" multiple>, hidden by the CSS at upload.html:106-116 (position:absolute; width:1px; height:1px; clip:rect(0,0,0,0))
repro: Isolated headless Chromium (Python Playwright) at 1280x900. Pressed Tab repeatedly from page load and logged document.activeElement each time. Tab1 = DIV#drop-zone (554x180). Tab2 = INPUT#file-input, getBoundingClientRect() = 1x1 at (639.5, 397.2), computed clip = rect(0px, 0px, 0px, 0px) — a real tab stop with nothing visible. Tab3 = BODY. The a11y snapshot also exposes it as a nested `button "Choose Files"` inside the drop zone's own button node.
severity: minor
category: a11y

DEFECT 2
what: The drop zone's accessible name does not contain its visible label, so a speech-input user who says the words printed on it cannot activate it.
where: upload.html:300 — <div id="drop-zone" role="button" aria-label="Choose files or drop files here">, visible text at upload.html:302
repro: page.accessibility.snapshot() returns the drop zone as `button | "Choose files or drop files here"`. page.inner_text('#drop-zone') returns "↑ / Drop files here or click to browse / You can select multiple files". The visible string "Drop files here or click to browse" does not appear in the accessible name (WCAG 2.5.3 Label in Name).
severity: minor
category: a11y

DEFECT 3
what: Removing a file with the keyboard throws focus away to the document body, so the keyboard user loses their place in the list and must tab from the top again.
where: upload.html:474-475 (remove handler) → render() at upload.html:408 `fileList.replaceChildren(fragment)` destroys the focused button
repro: Added report.pdf and photo.png via the picker, ran document.querySelector('.remove-button').focus() (activeElement = BUTTON.remove-button "Remove"), pressed Enter. The item was removed (2 items → 1) and document.activeElement became BODY.
severity: minor
category: a11y

DEFECT 4
what: Activating Upload or Clear all by keyboard throws focus to the document body, because each button disables itself while it still holds focus.
where: upload.html:410-411 (`clearButton.disabled = ...`, `uploadButton.disabled = isUploading || ...`), buttons at upload.html:310 and upload.html:317
repro: With 2 files listed, focused #upload-button (activeElement = BUTTON#upload-button) and pressed Enter; 80 ms later document.activeElement was BODY, and it was still BODY when the upload finished 2.5 s later. Same test on #clear-all: focused it with 2 files listed, pressed Enter — list emptied and document.activeElement became BODY.
severity: minor
category: a11y

DEFECT 5
what: During a single upload the whole file list — which is an aria-live="polite" region — is torn down and rebuilt about 120 times, so a screen reader re-announces every file name, size and percentage continuously for the full 2 seconds.
where: upload.html:313 <ul id="file-list" aria-live="polite">; render() called from the requestAnimationFrame loop at upload.html:517, replacing all children at upload.html:408
repro: Attached a MutationObserver to #file-list ({childList:true, subtree:true, characterData:true}) before pressing Upload with 2 files. At completion (elapsed 2554 ms) the counter read 123 mutations. Confirmed #file-list's aria-live attribute is "polite".
severity: minor
category: a11y

DEFECT 6
what: The per-file "Remove" control is only 22 px tall — under the 24x24 CSS px minimum target size, making it easy to miss on touch.
where: .remove-button (upload.html:212-216, padding: 2px 0 2px 8px; font-size: 0.875rem), rendered at upload.html:382-388
repro: getBoundingClientRect() on .remove-button measured 61.1 x 22.0 px. Identical height at every viewport tested: 1280, 768, 375 and 320 px wide. (For comparison the Upload button measures 554 x 48.)
severity: minor
category: touch-target

DEFECT 7
what: Clearing or removing files while an upload is running leaves the Upload button stuck reading "Uploading…" and disabled for the rest of the 2-second timer, so a user who clears the list and adds a new file cannot start an upload and is shown a state that is not happening.
where: upload.html:478-481 (clear handler does not cancel the in-flight animation), interacting with upload.html:411-412 and the rAF loop at upload.html:508-527
repro: Added 2 files, clicked Upload, waited 300 ms, clicked Clear all. Sampled the DOM afterwards: at +0/+400/+900/+1500 ms the list was empty ({items: 0, empty state shown}) yet #upload-button was {disabled: true, text: "Uploading…"}. Only at +2200 ms did it return to {disabled: true, text: "Upload"}. Repeating with a file added after the clear: the new row showed status "Ready" while #upload-button stayed {disabled: true, text: "Uploading…"} until the phantom timer expired.
severity: minor
category: state

DEFECT 8
what: The drop zone's helper line "You can select multiple files" is too low contrast to read comfortably.
where: .drop-zone small (upload.html:102-104, color: #7a8499) on the drop zone background #f8faff, element at upload.html:303
repro: Measured in-browser from computed styles: color rgb(122,132,153) on rgb(248,250,255), font-size 13.33px, weight 400 → contrast ratio 3.60:1. WCAG AA requires 4.5:1 for text this size.
severity: minor
category: contrast

DEFECT 9
what: The "No files selected." empty-state message is too low contrast to read comfortably.
where: #empty-state / .empty-state (upload.html:167-174, color: #7a8499) on the card background #ffffff, element at upload.html:312
repro: Measured in-browser from computed styles: color rgb(122,132,153) on rgb(255,255,255), font-size 16px, weight 400 → contrast ratio 3.76:1, below the 4.5:1 AA minimum.
severity: minor
category: contrast

DEFECT 10
what: Each file's size and its status/percentage readout are too low contrast to read comfortably — this is the text that shows live upload progress ("47%") and the "Ready" state.
where: .file-meta (upload.html:199-205, color: #747e92) on the file row background #fbfcfe, spans built at upload.html:371-379
repro: Measured in-browser from computed styles with 2 files listed: color rgb(116,126,146) on rgb(251,252,254), font-size 13.6px, weight 400 → contrast ratio 3.98:1, below the 4.5:1 AA minimum. Same element shows "3.0 KB", "Ready" and, mid-upload, "47%".
severity: minor
category: contrast

DEFECT 11
what: The Upload button's label is nearly illegible whenever the button is disabled — including the "Uploading…" text that is the only on-button indication that an upload is running.
where: .upload-button:disabled (upload.html:263-267, background: #aeb8d5) with color #ffffff from upload.html:243, button at upload.html:317
repro: Measured in-browser from computed styles. On load: color rgb(255,255,255) on rgb(174,184,213) → 1.98:1. Mid-upload the same button reads "Uploading…" at the same 1.98:1 (screenshot taken at ~47% progress confirms the washed-out label). The enabled state measures 5.46:1, so the drop is specific to the disabled styling.
severity: minor
category: contrast

DEFECT 12
what: The drop zone's keyboard focus ring is suppressed and replaced by a border tint so faint it is nearly indistinguishable from the unfocused state — and it is identical to the hover style, so a keyboard user cannot tell focus from hover.
where: .drop-zone:hover, .drop-zone:focus-visible { border-color: #4e6ee8; background: #f1f4ff; outline: none; } — upload.html:72-77
repro: Read computed styles with the transition settled. Unfocused: border-color rgb(159,172,204), outline "none". After pressing Tab (element.matches(':focus-visible') === true): border-color rgb(78,110,232), outline "none 0px", box-shadow "none". Contrast between the focused and unfocused indicator colours = 1.96:1 (WCAG 2.2 Focus Appearance wants at least 3:1 for a change-of-contrast indicator). Dumped the stylesheet rules to confirm :focus-visible shares one declaration block with :hover, so the two states render identically.
severity: minor
category: a11y

--- END EXISTING REPORT ---

## Probe output

States the probe reached: files-selected, load
Probe log: selected 2 files

### Text contrast below the WCAG 1.4.3 minimum
- `small` — 3.6:1, needs 4.5:1 (state: load, 375px) text: 'You can select multiple files'
- `#empty-state` — 3.76:1, needs 4.5:1 (state: load, 375px) text: 'No files selected.'
- `span` — 3.98:1, needs 4.5:1 (state: files-selected, 375px) text: '2.8 KB'
- `span.file-status` — 3.98:1, needs 4.5:1 (state: files-selected, 375px) text: 'Ready'

### Control boundaries below the WCAG 1.4.11 3:1 minimum
- `#drop-zone` — border 2.27:1 against its backdrop (state: load)

### Focus indicators and placeholder text (pulled from the CSSOM — these never appear in getComputedStyle of the resting element)
- `.remove-button:focus-visible` { outline: rgba(64, 95, 216, 0.28) solid 3px } — 1.49:1, needs 3:1, composites to rgb(199,208,243) (matches 2, e.g. `button.remove-button`)
- `.remove-button:focus-visible` { outline-color: rgba(64, 95, 216, 0.28) } — 1.49:1, needs 3:1, composites to rgb(199,208,243) (matches 2, e.g. `button.remove-button`)
- `.upload-button:focus-visible` { outline: rgba(64, 95, 216, 0.28) solid 3px } — 1.5:1, needs 3:1, composites to rgb(202,210,244) (matches 1, e.g. `#upload-button`)
- `.upload-button:focus-visible` { outline-color: rgba(64, 95, 216, 0.28) } — 1.5:1, needs 3:1, composites to rgb(202,210,244) (matches 1, e.g. `#upload-button`)
- `.clear-button:focus-visible` { outline: rgba(64, 95, 216, 0.28) solid 3px } — 1.5:1, needs 3:1, composites to rgb(202,210,244) (matches 1, e.g. `#clear-all`)
- `.clear-button:focus-visible` { outline-color: rgba(64, 95, 216, 0.28) } — 1.5:1, needs 3:1, composites to rgb(202,210,244) (matches 1, e.g. `#clear-all`)

### Tap targets below the size minimum (buttons/links judged at 44px, text fields at 24px)
- `#file-input` — 1 x 1 px (under-24-FAILS-WCAG-2.5.8, state: load, 375px) ''
- `button.remove-button` — 61.1 x 22 px (under-24-FAILS-WCAG-2.5.8, state: files-selected, 375px) 'Remove'
- `#clear-all` — 61.5 x 33 px (under-44 — a tap target this size is hard to hit, state: load, 375px) 'Clear all'

### Accessible name / role exposure
- `#file-input` — no accessible name ''
- `#file-input` — focusable control nested inside another control (#drop-zone) ''

### Informational only — contrast inside disabled controls
WCAG exempts inactive controls, so these are NOT defects by default. One is worth reporting only if that disabled state is the page's resting state AND its text carries something the user needs to read (a status or progress message).
- `#clear-all` — 2.06:1 'Clear all'
- `#upload-button` — 1.98:1 'Upload'
- `.clear-button:disabled` — 2.06:1 ''

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
