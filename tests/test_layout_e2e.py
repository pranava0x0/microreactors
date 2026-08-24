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
import re
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

# Derived from the markup, never re-typed: a hand-written copy of this list
# goes stale silently the next time a panel is renamed (CLAUDE.md, single
# source of truth).
PANELS = re.findall(r'<section id="([\w-]+)" role="tabpanel"',
                    (SITE / "index.html").read_text())
assert len(PANELS) >= 5, "panel extraction from index.html failed"


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
                      // Sub-tab strip, where the panel has one: exactly one
                      // sub-panel showing, and no sub-tab parked off its edge.
                      const strip = document.querySelector('#' + panel + ' .subtabs');
                      let sub = null;
                      if (strip) {
                        const last = strip.lastElementChild.getBoundingClientRect();
                        const box = strip.getBoundingClientRect();
                        const btns = [...strip.querySelectorAll('.subtab')];
                        sub = {
                          shown: [...document.querySelectorAll('#' + panel + ' [data-sub]')]
                            .filter(e => !e.hidden).length,
                          selected: strip.querySelectorAll('[aria-selected="true"]').length,
                          lastIn: last.right <= box.right + 0.5,
                          overflow: strip.scrollWidth > strip.clientWidth + 1,
                          minH: Math.min(...btns.map(b => b.getBoundingClientRect().height)),
                          // DESIGN.md 8.7: lighter than the primary tabs means
                          // underline only. A box would show up as a radius or
                          // a side border.
                          boxed: btns.some(b => {
                            const c = getComputedStyle(b);
                            return parseFloat(c.borderRadius) > 0
                              || parseFloat(c.borderLeftWidth) > 0
                              || parseFloat(c.borderTopWidth) > 0;
                          })
                        };
                      }
                      return {
                        scrollW: doc.scrollWidth, clientW: doc.clientWidth,
                        lastTabIn: lastTab.right <= tabsBox.right + 0.5,
                        visible, wide, sub,
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
                    if m["sub"]:
                        sub = m["sub"]
                        if sub["shown"] != 1:
                            problems.append(f"{width}px {panel}: {sub['shown']} sub-panels visible")
                        if sub["selected"] != 1:
                            problems.append(f"{width}px {panel}: {sub['selected']} sub-tabs selected")
                        if not sub["lastIn"] or sub["overflow"]:
                            problems.append(f"{width}px {panel}: sub-tab strip clipped")
                        if sub["boxed"]:
                            problems.append(f"{width}px {panel}: sub-tabs are boxed, not underlined")
                        if coarse and sub["minH"] < 43.5:
                            problems.append(f"{width}px {panel}: sub-tab height {sub['minH']}")
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


@unittest.skipUnless(_HAVE_PW, "playwright not installed; layout gate skipped")
class Routing(unittest.TestCase):
    def test_legacy_evidence_hash_lands_on_sources(self):
        """The Sources tab shipped as "Evidence" until 2026-08-23. Anything
        already linked or bookmarked uses #evidence, and an unknown route
        silently strands the reader on the Tracker."""
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            page = browser.new_page()
            page.goto(base + "#evidence", wait_until="networkidle")
            page.wait_for_timeout(80)
            got = page.evaluate("""() => ({
              visible: [...document.querySelectorAll('section[role=tabpanel]')]
                .filter(p => !p.hidden).map(p => p.id),
              hash: location.hash
            })""")
            browser.close()
        self.assertEqual(got["visible"], ["sources"], "#evidence did not land on Sources")
        self.assertTrue(got["hash"].startswith("#sources"),
                        f"legacy hash not rewritten to canonical: {got['hash']}")


@unittest.skipUnless(_HAVE_PW, "playwright not installed; layout gate skipped")
class SourceRegisterMobile(unittest.TestCase):
    def test_host_shares_the_content_column(self):
        """Three children in a two-column grid: without an explicit placement
        the host auto-flows into column 1, where the number column sizes it and
        word-break renders a long domain almost vertically."""
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            ctx = browser.new_context(viewport={"width": 375, "height": 812},
                                      has_touch=True, is_mobile=True)
            page = ctx.new_page()
            page.goto(base + "#sources/register", wait_until="networkidle")
            page.wait_for_timeout(80)
            got = page.evaluate("""() => {
              const rows = [...document.querySelectorAll('#register .rrow')];
              const bad = [];
              let tallestHost = 0;
              for (const r of rows) {
                const rn = r.querySelector('.rn').getBoundingClientRect();
                const host = r.querySelector('.host').getBoundingClientRect();
                const body = r.children[1].getBoundingClientRect();
                if (host.left < rn.right) bad.push(r.id);
                if (Math.abs(host.left - body.left) > 1) bad.push(r.id + ':misaligned');
                tallestHost = Math.max(tallestHost, host.height);
              }
              return { rows: rows.length, bad: bad.slice(0, 5), tallestHost };
            }""")
            ctx.close()
            browser.close()
        self.assertGreater(got["rows"], 20, "register rows did not render")
        self.assertEqual(got["bad"], [], "host is not in the content column")
        self.assertLess(got["tallestHost"], 40,
                        f"a hostname wrapped to {got['tallestHost']}px — column too narrow")


if __name__ == "__main__":
    unittest.main()
