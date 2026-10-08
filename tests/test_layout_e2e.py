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
    def test_voices_open_on_short_index(self):
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            page = browser.new_page(viewport={"width": 375, "height": 812})
            page.goto(base + "#sources/voices", wait_until="networkidle")
            groups = page.locator("#voices details.voicegroup")
            self.assertGreater(groups.count(), 1)
            self.assertEqual(page.locator("#voices details.voicegroup[open]").count(), 0)
            initial_height = page.evaluate("document.documentElement.scrollHeight")
            groups.first.locator("summary").click()
            self.assertEqual(page.locator("#voices details.voicegroup[open]").count(), 1)
            self.assertGreater(page.evaluate("document.documentElement.scrollHeight"), initial_height)
            browser.close()

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
                      const active = tabs.querySelector('[aria-selected="true"]').getBoundingClientRect();
                      const navrow = tabs.parentNode;
                      return {
                        scrollW: doc.scrollWidth, clientW: doc.clientWidth,
                        lastTabIn: lastTab.right <= tabsBox.right + 0.5,
                        tabOverflow: tabs.scrollWidth > tabs.clientWidth + 1,
                        activeIn: active.left >= tabsBox.left - 0.5 && active.right <= tabsBox.right + 0.5,
                        fade: navrow.classList.contains('more-left') || navrow.classList.contains('more-right'),
                        visible, wide, sub,
                        tabH: document.querySelector('.tab').getBoundingClientRect().height
                      };
                    }""", panel)
                    if m["scrollW"] > m["clientW"] + 1:
                        problems.append(f"{width}px {panel}: horizontal scroll {m['scrollW']}>{m['clientW']}")
                    # From 1280px all nine tabs sit on one row. Below it the strip
                    # scrolls (wrapping cost 143px of sticky chrome at 768px), which is
                    # only discoverable if the active tab is in view and an edge fade
                    # marks the side that hides more tabs (UAT 2026-09-26).
                    if width >= 1280 and not m["lastTabIn"]:
                        problems.append(f"{width}px {panel}: last tab clipped")
                    if width < 1280:
                        if not m["tabOverflow"]:
                            problems.append(f"{width}px {panel}: primary navigation should scroll")
                        if not m["activeIn"]:
                            problems.append(f"{width}px {panel}: active tab scrolled out of view")
                        if m["tabOverflow"] and not m["fade"]:
                            problems.append(f"{width}px {panel}: hidden tabs with no edge fade")
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
                    page.click("#demand-tab-overview")
                    page.wait_for_timeout(50)
                    before = page.evaluate("document.querySelectorAll('details.segcard[open]').length")
                    page.click("#demand-overview details.segcard >> nth=1 >> summary")
                    page.wait_for_timeout(50)
                    after = page.evaluate("document.querySelectorAll('details.segcard[open]').length")
                    if after != before + 1:
                        problems.append(f"accordion toggle {before}->{after}")
                ctx.close()
            browser.close()
        self.assertEqual(problems, [])


@unittest.skipUnless(_HAVE_PW, "playwright not installed; layout gate skipped")
class CustomerCostsMobile(unittest.TestCase):
    """The cost examples need plain labels and must stay inside a phone viewport."""

    def test_price_to_beat_uses_plain_labels_without_overflow(self):
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            ctx = browser.new_context(viewport={"width": 375, "height": 812},
                                      has_touch=True, is_mobile=True)
            page = ctx.new_page()
            page.goto(base + "?view=costs#economics/price-to-beat", wait_until="networkidle")
            page.wait_for_function("document.querySelectorAll('#benchmarks details.benchsector').length > 0")
            page.evaluate("""() => {
              document.querySelectorAll('#benchmarks details').forEach(d => { d.open = true; });
            }""")
            got = page.evaluate("""() => ({
              text: document.getElementById('benchmarks').innerText,
              dealTypes: [...document.querySelectorAll('#benchmarks .drow')]
                .filter(row => row.querySelector('.dlbl')?.textContent === 'Deal type')
                .map(row => row.lastElementChild.textContent),
              scrollW: document.documentElement.scrollWidth,
              clientW: document.documentElement.clientWidth
            })""")
            ctx.close()
            browser.close()
        self.assertIn("Deal type", got["text"])
        self.assertIn("Power purchase agreement", got["text"])
        self.assertIn("One contractor designs and builds it", got["text"])
        self.assertNotIn("Instrument", got["text"])
        self.assertNotIn("design-build", got["dealTypes"])
        self.assertLessEqual(got["scrollW"], got["clientW"] + 1)


@unittest.skipUnless(_HAVE_PW, "playwright not installed; layout gate skipped")
class Routing(unittest.TestCase):
    def test_register_search_restores_the_first_page(self):
        """The source register shows its first 30 rows until the reader searches
        or asks for all. Clearing a search used to leave all ~700 rows open and
        hide the Show all button (UAT 2026-09-26)."""
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            page = browser.new_page()
            page.goto(base + "#sources", wait_until="networkidle")
            page.wait_for_timeout(200)
            count = "[...document.querySelectorAll('.rrow')].filter(r => r.offsetParent).length"
            first = page.evaluate(count)
            page.fill("#regq", "alaska")
            page.wait_for_timeout(60)
            searched = page.evaluate(count)
            page.fill("#regq", "")
            page.wait_for_timeout(60)
            cleared = page.evaluate(count)
            button_back = page.is_visible("#regall")
            page.click("#regall")
            page.wait_for_timeout(60)
            everything = page.evaluate(count)
            browser.close()
        self.assertEqual(first, 30)
        self.assertGreater(searched, 0)
        self.assertEqual(cleared, 30, "clearing the search should restore the first page")
        self.assertTrue(button_back, "Show all should return with the first page")
        self.assertGreater(everything, 30)

    def test_deep_link_scrolls_its_tab_into_view(self):
        """On a phone the tab strip scrolls. Landing on #sources left its tab
        ~500px off-screen, so the page gave no sign of where the reader was."""
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            ctx = browser.new_context(viewport={"width": 375, "height": 812},
                                      has_touch=True, is_mobile=True)
            page = ctx.new_page()
            page.goto(base + "#sources", wait_until="networkidle")
            page.wait_for_timeout(80)
            got = page.evaluate("""() => {
              const tabs = document.getElementById('tabs'), box = tabs.getBoundingClientRect();
              const on = tabs.querySelector('[aria-selected="true"]').getBoundingClientRect();
              return {id: tabs.querySelector('[aria-selected="true"]').id,
                      inView: on.left >= box.left - 0.5 && on.right <= box.right + 0.5,
                      scrolled: tabs.scrollLeft > 0};
            }""")
            browser.close()
        self.assertEqual(got["id"], "tab-sources")
        self.assertTrue(got["scrolled"] and got["inView"], got)

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

    def test_merged_tab_hashes_land_on_their_new_sections(self):
        """Sites and Market design became sub-sections. Preserve direct links."""
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            page = browser.new_page()
            results = []
            for old_hash in ("sites", "market"):
                page.goto(base + "#" + old_hash, wait_until="networkidle")
                page.wait_for_timeout(80)
                results.append(page.evaluate("""() => ({
                  visible: [...document.querySelectorAll('section[role=tabpanel]')]
                    .filter(p => !p.hidden).map(p => p.id), hash: location.hash
                })"""))
            browser.close()
        self.assertEqual(results[0]["visible"], ["pipeline"])
        self.assertEqual(results[0]["hash"], "#pipeline/sites")
        self.assertEqual(results[1]["visible"], ["policy"])
        self.assertEqual(results[1]["hash"], "#policy/market-design")


@unittest.skipUnless(_HAVE_PW, "playwright not installed; layout gate skipped")
@unittest.skipUnless(_HAVE_PW, "playwright not installed; layout gate skipped")
class TabIntentPrefetch(unittest.TestCase):
    def test_hover_prefetches_once_and_a_sweep_does_not(self):
        """Resting on the Rules tab fetches its payload before the click; moving
        across the strip fetches nothing; a failed prefetch is retried on open."""
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            seen = []
            page.on("request", lambda r: seen.append(r.url.split("/")[-1].split("?")[0]))
            page.goto(base, wait_until="networkidle")
            page.hover("#tab-policy")
            page.mouse.move(5, 400)            # leave before the 150 ms rest
            page.wait_for_timeout(400)
            self.assertNotIn("data-instruments.js", seen, "a sweep must not prefetch")
            page.hover("#tab-policy")
            page.wait_for_timeout(500)
            self.assertEqual(seen.count("data-instruments.js"), 1)
            page.click("#tab-policy")
            page.wait_for_timeout(500)
            self.assertEqual(seen.count("data-instruments.js"), 1, "the open reuses the prefetch")
            self.assertGreater(page.locator("#pathways *").count(), 5)
            browser.close()

    def test_failed_lazy_load_is_retried_on_open(self):
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            calls = {"n": 0}

            def flaky(route):
                calls["n"] += 1
                route.abort() if calls["n"] == 1 else route.continue_()
            page.route("**/data-news.js*", flaky)
            page.goto(base, wait_until="networkidle")
            page.hover("#tab-news")
            page.wait_for_timeout(500)         # prefetch fails, quietly
            page.click("#tab-news")
            page.wait_for_timeout(800)
            self.assertEqual(calls["n"], 2, "open must request the file again")
            self.assertGreater(page.locator("#newslist *").count(), 5)
            browser.close()


class HomePage(unittest.TestCase):
    def test_featured_prices_link_to_their_sources(self):
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            page = browser.new_page(viewport={"width": 375, "height": 812})
            page.goto(base + "#home", wait_until="networkidle")
            box = page.locator(".glancebox", has=page.locator('a.glancecard[href="#demand/regions"]'))
            self.assertEqual(box.count(), 1)
            chips = box.locator(".glancecite a.cite")
            self.assertEqual(chips.count(), 3)
            self.assertTrue(all(chips.nth(i).get_attribute("href").startswith("https://")
                                and "?" not in chips.nth(i).inner_text()
                                for i in range(chips.count())))
            self.assertEqual(box.locator("a.glancecard a").count(), 0)
            box.locator("a.glancecard").click()
            self.assertTrue(page.url.endswith("#demand/regions"))
            browser.close()

    def test_home_is_a_directory_of_the_site_with_the_newest_headlines(self):
        """Home opens on one card per tab (each linking to a real panel) and then
        the headlines, newest first. The first-page list once trusted file order
        and promoted a 2026-08-17 story over three newer ones; a headline also
        has to open its own record, not the top of a 47-row list."""
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            page = browser.new_page()
            page.goto(base + "#home", wait_until="networkidle")
            page.wait_for_timeout(100)
            got = page.evaluate("""() => {
              const cards = [...document.querySelectorAll('#home-glance .glancecard')];
              const panels = [...document.querySelectorAll('#tabs [role=tab]')].map(t => t.dataset.panel);
              const dates = [...document.querySelectorAll('#home-lead .ndate, #home-headlist .ndate')]
                .map(e => e.textContent);
              return {cards: cards.map(c => c.getAttribute('href').slice(1)), panels,
                      empty: cards.filter(c => !c.querySelector('.ga').textContent.trim()).length,
                      undefinedText: cards.filter(c => /undefined|NaN/.test(c.textContent)).length,
                      lead: document.querySelectorAll('#home-lead .leadstory').length,
                      heads: document.querySelectorAll('#home-headlist li:not(.more)').length, dates};
            }""")
            first = page.locator("#home-headlist li:not(.more) a").first
            target = first.get_attribute("href")
            first.click()
            page.wait_for_timeout(300)
            opened = page.evaluate("""(id) => {
              const el = document.getElementById('n-' + id);
              return {visible: !document.getElementById('news').hidden, open: !!(el && el.open)};
            }""", target.split("/", 1)[1])
            browser.close()
        self.assertEqual(sorted(h.split("/", 1)[0] for h in got["cards"]),
                         sorted(p for p in got["panels"] if p != "home"))
        self.assertEqual(got["empty"], 0)
        self.assertEqual(got["undefinedText"], 0)
        self.assertEqual(got["lead"], 1)
        self.assertGreaterEqual(got["heads"], 5)
        self.assertEqual(got["dates"], sorted(got["dates"], reverse=True), "headlines not newest-first")
        self.assertEqual(opened, {"visible": True, "open": True})

    def test_site_filters_expose_the_selected_state(self):
        with serve_site() as base, sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as e:
                self.skipTest(f"chromium unavailable: {e}")
            page = browser.new_page()
            page.goto(base + "#pipeline/sites", wait_until="networkidle")
            page.wait_for_timeout(80)
            group_order = page.locator('.sitegroup').evaluate_all(
                '(nodes) => nodes.map(n => n.dataset.siteGroup)')
            remote_names = page.locator('[data-site-group="remote"] .sitecard h3').all_text_contents()
            mining_names = page.locator('[data-site-group="mining"] .sitecard h3').all_text_contents()
            marine_names = page.locator('[data-site-group="marine"] .sitecard h3').all_text_contents()
            page.locator('[data-site-filter="remote"]').click()
            state = page.locator('[data-site-filter="remote"]').get_attribute("aria-pressed")
            visible = page.locator('.sitegroup:not([hidden])').count()
            first_group = page.locator('.sitegroup:not([hidden])').first.get_attribute('data-site-group')
            browser.close()
        self.assertEqual(state, "true")
        self.assertEqual(visible, 1)
        self.assertEqual(first_group, "remote")
        self.assertEqual(group_order, ["remote", "mining", "marine", "other"])
        self.assertIn("Iqaluit isolated diesel grid", remote_names)
        self.assertIn("Tanbreez rare-earth project", mining_names)
        self.assertIn("DP World London Gateway (Thames Freeport)", marine_names)


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
