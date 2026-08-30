"""Site contract: the HTML, CSS and JS agree with each other. These are the
checks a browser-less CI can make deterministically; interactive behaviour is
verified in the browser during development."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

HTML = (SITE / "index.html").read_text()
CSS = (SITE / "assets" / "site.css").read_text()
JS = (SITE / "assets" / "app.js").read_text()


class TabContract(unittest.TestCase):
    def tabs(self):
        tabs = re.findall(r'<button class="tab" role="tab" id="(tab-[\w-]+)" '
                          r'aria-controls="([\w-]+)" data-panel="([\w-]+)"', HTML)
        self.assertGreaterEqual(len(tabs), 5, "tab extraction found too few tabs — regex stale?")
        return tabs

    def test_every_tab_controls_a_real_panel(self):
        panel_ids = re.findall(r'<section id="([\w-]+)" role="tabpanel"', HTML)
        self.assertGreaterEqual(len(panel_ids), 5, "panel extraction failed")
        for tab_id, controls, panel in self.tabs():
            self.assertEqual(controls, panel, f"{tab_id}: aria-controls != data-panel")
            self.assertIn(panel, panel_ids, f"{tab_id} controls missing panel {panel!r}")
            self.assertIn(f'aria-labelledby="{tab_id}"', HTML,
                          f"panel {panel} not labelled by {tab_id}")

    def test_js_panel_list_matches_html(self):
        m = re.search(r'var PANELS = \[([^\]]+)\]', JS)
        self.assertIsNotNone(m, "PANELS array not found in app.js")
        js_panels = re.findall(r'"([\w-]+)"', m.group(1))
        html_panels = [t[2] for t in self.tabs()]
        self.assertEqual(js_panels, html_panels,
                         "app.js PANELS order/content diverged from the HTML tabs")

    def test_exactly_one_panel_visible_by_default(self):
        panels = re.findall(r'<section id="[\w-]+" role="tabpanel"[^>]*>', HTML)
        hidden = [p for p in panels if "hidden" in p]
        self.assertEqual(len(panels) - len(hidden), 1,
                         "exactly one panel must ship un-hidden as the default view")

    def test_tablist_present(self):
        self.assertIn('role="tablist"', HTML)


class RenderTargets(unittest.TestCase):
    def test_every_js_target_id_exists_in_html(self):
        ids = set(re.findall(r'\$\("([\w-]+)"\)', JS))
        self.assertGreaterEqual(len(ids), 10, "id extraction from app.js failed")
        for i in ids:
            self.assertRegex(HTML, f'id="{i}"', f"app.js writes to #{i} which is not in index.html")


class CssGuards(unittest.TestCase):
    def test_hidden_attribute_guard(self):
        """Panels are switched via [hidden]; any display rule on a section
        would silently override it without this guard (DESIGN.md 12.1)."""
        self.assertIn("[hidden]{display:none!important}", CSS.replace(" ", ""))

    def test_touch_targets_gated_on_coarse_pointer(self):
        self.assertIn("pointer:coarse", CSS)

    def test_details_marker_uses_unicode_escape(self):
        """content: glyphs must be unicode escapes, not raw UTF-8 (DESIGN.md 12.20)."""
        for m in re.finditer(r'content:"([^"]*)"', CSS):
            self.assertTrue(all(ord(c) < 128 for c in m.group(1)),
                            f"raw non-ASCII glyph in CSS content: {m.group(1)!r}")

    def test_no_hex_colors_outside_tokens(self):
        body = re.sub(r'/\*.*?\*/', '', CSS, flags=re.S)
        hexes = re.findall(r'#[0-9a-fA-F]{3,8}\b', body)
        self.assertEqual(hexes, [], f"hardcoded hex in site.css: {hexes} — use tokens")


class ScriptOrder(unittest.TestCase):
    def test_data_loads_before_app(self):
        d, a = HTML.find('src="data.js"'), HTML.find('src="assets/app.js"')
        self.assertGreater(d, -1)
        self.assertGreater(a, d, "data.js must load before app.js")


class MarkupIds(unittest.TestCase):
    """A duplicate id is invalid HTML and silently breaks getElementById.

    A render div was given id="news" inside <section id="news">, so the lazy
    loader's placeholder wrote into the SECTION and wiped the whole panel. It
    rendered zero rows with no console error and looked like a data problem.
    """

    def test_no_duplicate_ids(self):
        import collections
        import re
        html = (ROOT / "site" / "index.html").read_text()
        ids = re.findall(r'id="([^"]+)"', html)
        dupes = [i for i, n in collections.Counter(ids).items() if n > 1]
        self.assertEqual(dupes, [], f"duplicate id(s) in index.html: {dupes}")

    def test_every_lazy_panel_target_exists_and_is_not_its_panel(self):
        """The placeholder must land in a child of the panel, never the panel itself.

        Two call shapes reach lazyPanel: a direct call guarded by
        `if (id === "<panel>")` in activate(), and a `lazy: {name, el, render}`
        descriptor on a makeSubnav item, where the panel is makeSubnav's first
        argument. Both are checked, and both counts are reconciled against the
        raw number of call sites so a pattern that drifts fails loudly instead
        of passing over everything it stopped matching.
        """
        import re
        html = (ROOT / "site" / "index.html").read_text()
        app = (ROOT / "site" / "assets" / "app.js").read_text()

        guarded = re.findall(
            r'if \(id === "(\w+)"[^)]*\)\s*\{\s*lazyPanel\("\w+",\s*"([\w-]+)"', app)
        # 1 definition + 1 generic invocation inside makeSubnav are not call sites
        # that name a panel; every other one must have matched above.
        direct = len(re.findall(r'\blazyPanel\(', app)) - 2
        self.assertEqual(len(guarded), direct,
                         f"matched {len(guarded)} guarded lazyPanel calls but app.js has "
                         f"{direct} direct call sites - the pattern has gone stale")

        # Segment the file at each makeSubnav( rather than bracket-matching its
        # argument list: one call closes with `].concat(` instead of `]);`, and a
        # non-greedy `\[(.*?)\]\);` swallowed the next call whole, attributing the
        # Sources descriptors to the Market panel. Wrong panel, still unequal to
        # its target, so the assertion below passed on a deliberately broken file.
        calls = [(m.group(1), m.start()) for m in re.finditer(r'makeSubnav\("(\w+)"', app)]
        bounds = [st for _, st in calls] + [len(app)]
        subnav = []
        for i, (panel, _) in enumerate(calls):
            seg = app[bounds[i]:bounds[i + 1]]
            for el in re.findall(r'lazy:\s*\{[^}]*?el:\s*"([\w-]+)"', seg):
                subnav.append((panel, el))
        self.assertEqual(len(subnav), app.count("lazy: {"),
                         f"matched {len(subnav)} subnav lazy descriptors but app.js has "
                         f"{app.count('lazy: {')} - the pattern has gone stale")

        pairs = guarded + subnav
        self.assertTrue(pairs, "no lazy panel wiring found at all")
        for panel, target in pairs:
            self.assertIn(f'id="{panel}"', html, f"panel #{panel} not in markup")
            self.assertIn(f'id="{target}"', html, f"lazy target #{target} not in markup")
            self.assertNotEqual(panel, target,
                                f"the lazy placeholder is written into #{target}, which is also "
                                f"the id of the panel it lives in - it would erase the panel")


class ElementRefs(unittest.TestCase):
    """Every id app.js writes into must exist in the markup.

    render() calls replaceChildren on whatever $() returns, so one missing id
    throws at module scope and every render after it never runs - the page then
    loses whole panels with a single console error that names the wrong line.
    Hit while moving a paragraph between sections: the sub-tabs for five panels
    silently stopped being built."""

    def test_every_element_app_js_writes_to_exists(self):
        import re
        app = (ROOT / "site" / "assets" / "app.js").read_text()
        ids = set(re.findall(r'id="([\w-]+)"', (ROOT / "site" / "index.html").read_text()))
        refs = sorted(set(re.findall(r'\$\("([\w-]+)"\)', app)))
        self.assertGreater(len(refs), 20, "no $() references found - the pattern has gone stale")
        # PANELS are looked up with the same helper and are section ids
        missing = [r for r in refs if r not in ids]
        self.assertEqual(missing, [], f"app.js writes to ids that are not in index.html: {missing}")


class PanelOrder(unittest.TestCase):
    """The tab strip, the <section> order and app.js's PANELS are one decision in
    three places. A tab reordered in the markup alone leaves the keyboard order
    and the no-JS reading order disagreeing with what is on screen."""

    def _panels(self):
        import re
        html = (ROOT / "site" / "index.html").read_text()
        app = (ROOT / "site" / "assets" / "app.js").read_text()
        tabs = re.findall(r'<button class="tab"[^>]*data-panel="([\w-]+)"', html)
        secs = re.findall(r'^<section id="([\w-]+)"', html, re.M)
        panels = re.search(r'var PANELS = \[(.*?)\];', app).group(1)
        return tabs, secs, re.findall(r'"([\w-]+)"', panels)

    def test_tabs_sections_and_panels_agree(self):
        tabs, secs, panels = self._panels()
        self.assertTrue(tabs, "no tab buttons found")
        self.assertEqual(tabs, panels, "tab buttons and PANELS are in different orders")
        self.assertEqual(secs, panels, "<section> order and PANELS are in different orders")

    def test_only_the_landing_panel_starts_visible(self):
        import re
        html = (ROOT / "site" / "index.html").read_text()
        _, _, panels = self._panels()
        for m in re.finditer(r'^<section id="([\w-]+)"([^>]*)>', html, re.M):
            wants_hidden = m.group(1) != panels[0]
            self.assertEqual(" hidden" in m.group(2), wants_hidden,
                             f"#{m.group(1)}: hidden attribute disagrees with PANELS[0]")


if __name__ == "__main__":
    unittest.main()
