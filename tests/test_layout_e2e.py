"""Cross-viewport layout gate. Optional: skips itself when Playwright (or its
browser) is absent, so `python3 -m unittest discover tests` stays one command
on a bare checkout while CI/dev machines with Playwright get the full check.

Covers the regressions this project actually shipped drafts of: horizontal
page scroll on one tab at one width, a clipped last tab, dead stat cells, and
an accordion that will not toggle.
"""
import contextlib
import http.server
import pathlib
import socket
import threading
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

try:
    from playwright.sync_api import sync_playwright  # type: ignore
    _HAVE_PW = True
except ImportError:
    _HAVE_PW = False

PANELS = ["pipeline", "economics", "vendors", "demand", "market", "policy", "evidence"]


@contextlib.contextmanager
def serve_site():
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(SITE), **kw)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}/index.html"
    finally:
        srv.shutdown()


@unittest.skipUnless(_HAVE_PW, "playwright not installed; layout gate skipped")
class Layout(unittest.TestCase):
    def test_all_tabs_all_widths(self):
        problems = []
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:  # browser binary missing
                self.skipTest(f"chromium unavailable: {e}")
            for width, height, coarse in ((375, 812, True), (768, 1024, False), (1280, 900, False)):
                ctx = browser.new_context(viewport={"width": width, "height": height},
                                          has_touch=coarse, is_mobile=coarse)
                page = ctx.new_page()
                page.goto(base, wait_until="networkidle")
                for panel in PANELS:
                    page.click(f"#tab-{panel}")
                    page.wait_for_timeout(60)
                    m = page.evaluate("""(panel) => {
                      const doc = document.documentElement;
                      const tabs = document.getElementById('tabs');
                      const lastTab = tabs.lastElementChild.getBoundingClientRect();
                      const tabsBox = tabs.getBoundingClientRect();
                      const visible = [...document.querySelectorAll('section[role=tabpanel]')]
                        .filter(p => !p.hidden).map(p => p.id);
                      let wide = null;
                      for (const el of document.getElementById(panel).querySelectorAll('*')) {
                        if (el.getBoundingClientRect().width > doc.clientWidth + 1) {
                          wide = el.className || el.tagName; break;
                        }
                      }
                      return {
                        scrollW: doc.scrollWidth, clientW: doc.clientWidth,
                        lastTabIn: lastTab.right <= tabsBox.right + 0.5,
                        visible, wide,
                        tabH: document.querySelector('.tab').getBoundingClientRect().height
                      };
                    }""", panel)
                    if m["scrollW"] > m["clientW"] + 1:
                        problems.append(f"{width}px {panel}: horizontal scroll {m['scrollW']}>{m['clientW']}")
                    if not m["lastTabIn"]:
                        problems.append(f"{width}px {panel}: last tab clipped")
                    if m["visible"] != [panel]:
                        problems.append(f"{width}px {panel}: visible={m['visible']}")
                    if m["wide"]:
                        problems.append(f"{width}px {panel}: overwide element {m['wide']}")
                    # Touch floor with half-pixel tolerance: device scaling makes
                    # exact-44 checks flake (TESTING.md 2026-08-10).
                    if coarse and m["tabH"] < 43.5:
                        problems.append(f"{width}px {panel}: tab height {m['tabH']}")
                if width == 375:
                    page.click("#tab-demand")
                    page.wait_for_timeout(50)
                    before = page.evaluate("document.querySelectorAll('details.sector[open]').length")
                    page.click("details.sector:nth-of-type(2) summary")
                    page.wait_for_timeout(50)
                    after = page.evaluate("document.querySelectorAll('details.sector[open]').length")
                    if after != before + 1:
                        problems.append(f"accordion toggle {before}->{after}")
                ctx.close()
            browser.close()
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
