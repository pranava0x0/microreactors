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

        lazyPanel's first argument is the DATASET name, its second is the target
        element id; the PANEL id comes from the `if (id === "...")` guard around
        the call. Comparing the target against the dataset name is the wrong
        comparison - lazyPanel("voices", "voices", ...) is fine because that
        panel is #sources.
        """
        import re
        html = (ROOT / "site" / "index.html").read_text()
        app = (ROOT / "site" / "assets" / "app.js").read_text()

        guarded = re.findall(
            r'if \(id === "(\w+)"[^)]*\)\s*\{\s*lazyPanel\("(\w+)",\s*"([\w-]+)"',
            app,
        )
        # A regex that stops matching passes everything, so prove it still sees
        # every call site. One extra hit is the `function lazyPanel(` definition.
        call_sites = len(re.findall(r'\blazyPanel\(', app)) - 1
        self.assertEqual(len(guarded), call_sites,
                         f"matched {len(guarded)} guarded lazyPanel calls but app.js has "
                         f"{call_sites} call sites - the pattern has gone stale")

        for panel, _dataset, target in guarded:
            self.assertIn(f'id="{panel}"', html, f"panel #{panel} not in markup")
            self.assertIn(f'id="{target}"', html, f"lazyPanel target #{target} not in markup")
            self.assertNotEqual(panel, target,
                                f"lazyPanel writes its placeholder into #{target}, which is also "
                                f"the id of the panel it lives in - it would erase the panel")


if __name__ == "__main__":
    unittest.main()
