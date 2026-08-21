"""Build gates: the generators are run, not just their output read, so a
generator change that stales the committed artifacts fails here (a test that
only reads site/data.js cannot see a broken build_data.py)."""
import json
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

    def test_built_stamp_is_data_derived(self):
        """The stamp must equal the max _meta.captured across data files —
        never the wall clock — or CI cannot enforce artifact sync."""
        captured = []
        for f in ("opportunities", "vendors", "costs", "sectors", "mechanisms", "policy"):
            meta = json.loads((ROOT / "data" / f"{f}.json").read_text()).get("_meta", {})
            if meta.get("captured"):
                captured.append(meta["captured"])
        self.assertEqual(self.MR["summary"]["built"], max(captured))


if __name__ == "__main__":
    unittest.main()
