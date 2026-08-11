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

PAGE UNDER REVIEW: file:///E:/GitHub/superpowers-custom/benchmark2/runs2/A_D3/upload.html

--- THE EXISTING REPORT (passes 1-2 — keep every record verbatim) ---
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

DEFECT 13
what: The dashed outline that marks the drop target is too faint against the card behind it, so the area you can drop files onto barely reads as a distinct control — and its fill is effectively the same white as the card.
where: .drop-zone (upload.html:63 `border: 2px dashed #9faccc`, upload.html:65 `background: #f8faff`), element at upload.html:300 (role="button")
repro: Isolated headless Chromium (Python Playwright) on the file:// page at 1280x900. getComputedStyle('#drop-zone') → border-top-color rgb(159,172,204), border-top-style dashed, border-top-width 2px, background rgb(248,250,255), outline "none", box-shadow "none"; parent .upload-card background rgb(255,255,255). Computed contrast: border vs card 2.27:1, border vs its own fill 2.17:1 — both under the 3:1 WCAG 1.4.11 minimum for the visual boundary of a user interface component. The fill gives no fallback cue: it measures 1.04:1 against the card, so the 554x180 target area is delimited by nothing but that 2.27:1 dashes. Re-measured at a 375px viewport: still 2.27:1.
severity: minor
category: contrast

DEFECT 14
what: The keyboard focus ring on the Upload, Clear all and Remove buttons is a 28%-opacity wash that is almost invisible against the page, so a keyboard user cannot tell which button they are on.
where: shared rule `.upload-button:focus-visible, .clear-button:focus-visible, .remove-button:focus-visible { outline: 3px solid rgb(64 95 216 / 28%); outline-offset: 2px }` — upload.html:256-261; buttons at upload.html:317 (#upload-button), upload.html:310 (#clear-all) and upload.html:382-388 (.remove-button)
repro: Isolated headless Chromium (Python Playwright), 1280x900. Added 2 files via #file-input so all three buttons were enabled, then walked the page with the Tab key and confirmed element.matches(':focus-visible') === true at each stop. Computed styles while focused: outline "rgba(64, 95, 216, 0.28) solid 3px", outline-offset 2px, box-shadow unchanged from the resting state; unfocused the same elements report outline-style "none", so this wash is the only focus signal. Because outline-offset pushes it clear of the button, the ring is drawn over the surrounding surface — composited that gives rgb(202,210,244) on the white card for #upload-button and #clear-all (1.50:1) and rgb(199,208,243) on the rgb(251,252,254) file row for .remove-button (1.49:1). All three are far below the 3:1 a focus indicator needs.
severity: minor
category: a11y

--- END EXISTING REPORT ---

## Experiment results

# Behavioural experiments

Each record is a user-reachable sequence that broke an invariant. Reproduce it yourself before reporting it.

## RESPONSIVE
- `the row control (Remove/Delete)` — pressed it with a real mousedown/mouseup 200ms into the operation started by "Uploading…" and nothing happened (row count stayed 2). The node it was pressed on no longer exists by then (document.contains(ref) === false) — the list recorded 33 mutation batches during the operation, so the element is destroyed between mousedown and mouseup and no click event is ever produced. The control is dead for the whole operation.

## DROP-GUARD
- `document / window` — this page accepts dropped files, but a cancelable drop/dragover dispatched outside the drop zone was NOT preventDefault()ed (body/dragover, body/drop, h1/dragover, h1/drop, #file-list/dragover, #file-list/drop). The browser default therefore stands: a file dropped anywhere else navigates away from the page and destroys the current selection. The guarded zone is only 554x180px of a 1280x900 viewport.

## FOCUS
- `#clear-all` — activating it left document.activeElement === <body>; a keyboard user is dumped to the top of the document

## IDEMPOTENT
- `input[type=file]` — selecting the same file twice produced 2 rows (was 1) with no de-duplication and no warning; the duplicate rows are indistinguishable

## ANNOUNCE
- `#upload-button` — the action changed visible content with no aria-live / role=alert ancestor, so a screen-reader user is told nothing: "Upload"



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
