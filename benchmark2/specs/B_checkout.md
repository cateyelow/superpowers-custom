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
