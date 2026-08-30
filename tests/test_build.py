"""Build gates: the generators are run, not just their output read, so a
generator change that stales the committed artifacts fails here (a test that
only reads site/data.js cannot see a broken build_data.py)."""
import json
import re
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(script):
    return subprocess.run([sys.executable, str(ROOT / "tools" / script)],
                          capture_output=True, text=True, cwd=ROOT, timeout=60)


class BuildSync(unittest.TestCase):
    def test_data_js_in_sync_and_idempotent(self):
        committed = (ROOT / "site" / "data.js").read_bytes()
        r1 = run("build_data.py")
        self.assertEqual(r1.returncode, 0, r1.stderr)
        first = (ROOT / "site" / "data.js").read_bytes()
        r2 = run("build_data.py")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        second = (ROOT / "site" / "data.js").read_bytes()
        self.assertEqual(first, second, "build_data.py is not idempotent")
        self.assertEqual(committed, second,
                         "site/data.js is stale — run python3 tools/build_data.py and commit it")

    def test_gaps_in_sync(self):
        committed = (ROOT / "data" / "gaps.json").read_bytes()
        r = run("build_gaps.py")
        self.assertEqual(r.returncode, 0, r.stderr)
        regenerated = (ROOT / "data" / "gaps.json").read_bytes()
        self.assertEqual(committed, regenerated,
                         "data/gaps.json is stale — run python3 tools/build_gaps.py and commit it")


class BundleConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        js = (ROOT / "site" / "data.js").read_text()
        payload = js.split("window.MR=", 1)[1].rsplit(";", 1)[0]
        cls.MR = json.loads(payload)

    def test_summary_counts_match_bundle(self):
        MR, s = self.MR, self.MR["summary"]
        self.assertEqual(s["opportunities"], len(MR["opportunities"]["opportunities"]))
        self.assertEqual(s["vendors"], len(MR["vendors"]["vendors"]))
        loads = [l for sec in MR["sectors"]["sectors"] for l in sec["loads"]]
        self.assertEqual(s["load_types"], len(loads))
        self.assertEqual(s["cited_loads"], sum(1 for l in loads if l.get("sources")))
        self.assertEqual(s["source_count"], len(MR["sources_index"]))
        self.assertEqual(sum(s["tracks"].values()), s["opportunities"])

    def test_sources_index_shape(self):
        reg = self.MR["sources_index"]
        self.assertGreater(len(reg), 20, "source register suspiciously small")
        for r in reg:
            for key in ("url", "label", "host", "uses"):
                self.assertTrue(r.get(key), f"register row missing {key}: {r}")
            self.assertTrue(r["uses"], f"register row has empty uses: {r['url']}")

    def test_citation_numbers_are_global_and_total(self):
        """One number per source URL, reused everywhere that URL is cited.

        The site renders "[?]" for a URL missing from source_numbers, so a
        source the walk never reached would ship a visibly broken citation.
        Walk the bundle independently of build_data.py's own walk and require
        every source dict it finds to carry a number.
        """
        reg = self.MR["sources_index"]
        nums = self.MR["source_numbers"]
        self.assertEqual([r["n"] for r in reg], list(range(1, len(reg) + 1)),
                         "register is not numbered 1..N in order")
        self.assertEqual(nums, {r["url"]: r["n"] for r in reg},
                         "source_numbers disagrees with the register")

        found = set()

        def walk(node):
            if isinstance(node, dict):
                url, label = node.get("url"), node.get("label")
                if isinstance(url, str) and url.startswith("http") and isinstance(label, str):
                    found.add(url)
                    return
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        for name in ("opportunities", "vendors", "costs", "sectors",
                     "mechanisms", "policy", "gaps"):
            walk(self.MR[name])
        self.assertGreater(len(found), 20, "source walk found suspiciously few sources")
        self.assertEqual(found - set(nums), set(),
                         "cited URLs with no register number would render as [?]")

    def test_app_js_hardcoded_citations_resolve(self):
        """app.js carries a few sources inline rather than in a data file. Nothing
        walked them, so three dangled unnoticed — one of them orphaned by an edit
        to policy.json that removed the only row citing that URL."""
        js = (ROOT / "site" / "assets" / "app.js").read_text()
        urls = re.findall(r'url:\s*"(https?://[^"]+)"', js)
        self.assertTrue(urls, "no inline citation found in app.js")
        unknown = [u for u in urls if u not in self.MR["source_numbers"]]
        self.assertEqual(unknown, [],
                         "inline app.js citations missing from the source register "
                         f"(they render as [?]): {unknown}")

    def test_static_html_citations_resolve(self):
        """Citations hand-written into index.html carry a [?] placeholder that
        app.js fills from the same register. The href still has to be a source
        the data cites, or the chip renders [?] to the reader."""
        html = (ROOT / "site" / "index.html").read_text()
        hrefs = re.findall(r'<a class="cite"[^>]*href="([^"]+)"', html)
        self.assertTrue(hrefs, "no static citation found in index.html")
        unknown = [h for h in hrefs if h not in self.MR["source_numbers"]]
        self.assertEqual(unknown, [],
                         "static citations not in the source register (they would "
                         f"render as [?]): {unknown}")

    def test_built_stamp_is_data_derived(self):
        """The stamp must equal the max _meta.captured across data files —
        never the wall clock — or CI cannot enforce artifact sync."""
        # Derived from the builder's own registry, never a second hand-typed list:
        # a literal here goes stale the day a data file is added, and this test
        # was already two files behind when that happened.
        sys.path.insert(0, str(ROOT / "tools"))
        import build_data

        captured = []
        for f in build_data.FILES:
            meta = json.loads((ROOT / "data" / f"{f}.json").read_text()).get("_meta", {})
            if isinstance(meta.get("captured"), str) and meta["captured"]:
                captured.append(meta["captured"])
        self.assertTrue(captured, "no data file carries _meta.captured")
        self.assertEqual(self.MR["summary"]["built"], max(captured))


if __name__ == "__main__":
    unittest.main()


class LazyPayloads(unittest.TestCase):
    """instruments and voices ship as separate files fetched when their panel
    opens. Three things can silently undo that: the split disappearing from the
    builder, a lazy dataset leaking back into the main bundle, and the loader
    caching a boolean instead of the in-flight promise (which double-fetches
    under concurrent callers and looks fine in a single-threaded read)."""

    def setUp(self):
        import json
        self.js = (ROOT / "site" / "data.js").read_text()
        i = self.js.index("{")
        self.bundle = json.loads(self.js[i:self.js.rindex("}") + 1])
        self.app = (ROOT / "site" / "assets" / "app.js").read_text()

    def test_lazy_datasets_are_absent_from_the_main_bundle(self):
        for name in self.bundle["lazy"]:
            self.assertNotIn(name, self.bundle,
                             f"{name} is declared lazy but still ships in data.js")
            self.assertTrue((ROOT / "site" / f"data-{name}.js").exists(),
                            f"data-{name}.js was not emitted")

    def test_citation_numbering_still_covers_lazy_data(self):
        """The register is built before the split, so a chip inside a lazy
        payload must still resolve to a number in the main bundle."""
        import json
        nums = self.bundle["source_numbers"]
        for name in self.bundle["lazy"]:
            chunk = (ROOT / "site" / f"data-{name}.js").read_text()
            payload = json.loads(chunk[chunk.index("=") + 1:chunk.rindex(";window.dispatchEvent")])
            urls = set()

            def walk(n):
                if isinstance(n, dict):
                    if isinstance(n.get("url"), str) and n["url"].startswith("http"):
                        urls.add(n["url"])
                    for v in n.values():
                        walk(v)
                elif isinstance(n, list):
                    for v in n:
                        walk(v)
            walk(payload)
            missing = [u for u in urls if u not in nums]
            self.assertEqual(missing, [], f"{name}: {len(missing)} urls have no citation number")

    def test_loader_caches_the_promise_not_a_boolean(self):
        self.assertIn("if (!LAZY[name])", self.app,
                      "loadLazy must guard on the cached promise")
        self.assertIn("LAZY[name] = new Promise", self.app)
        # the failure mode this replaces: a flag set after the fetch resolves
        self.assertNotIn("Loaded = true;", self.app)
