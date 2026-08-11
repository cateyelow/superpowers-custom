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
