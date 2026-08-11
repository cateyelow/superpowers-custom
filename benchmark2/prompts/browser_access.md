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

