# Task: filterable data table

Build a single HTML file (all CSS/JS inline, no frameworks, no build tools, no
network calls) implementing a data table over a built-in dataset.

## Deliverable
- `table.html`

## Requirements

R1. Embed a hardcoded dataset of 24 employee records, each with: name,
    department, role, location, and salary (a number).
R2. Render them in a table with a column per field.
R3. A text input filters rows as the user types, matching against name and role.
R4. A department dropdown filters rows to one department, and combines with the
    text filter.
R5. Clicking a column header sorts by that column; clicking again reverses the
    direction. Salary sorts numerically, the rest alphabetically.
R6. Paginate at 10 rows per page, with Previous/Next controls and a "Page X of Y"
    indicator that reflects the current filters.

Open `table.html` directly in a browser (`file://`) — it must work with no server.
