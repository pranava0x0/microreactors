"""Schema + citation contract for data/deployment_sites.json.

The dataset maps candidate deployment sites to the Applications tab's
categories, so its band labels must stay in lockstep with sectors.json —
derived membership checks, never a hand-copied list (CLAUDE.md single source
of truth). Every row carries sources; filings carry URLs; statuses come from
the file's own _meta enum so a new status must be declared before use.
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))


def load(name: str):
    return json.loads((DATA / name).read_text())


class TestDeploymentSites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load("deployment_sites.json")
        cls.sites = cls.doc["sites"]
        cls.meta = cls.doc["_meta"]
        sectors = load("sectors.json")["sectors"]
        cls.bands_by_sector = {s["sector"]: {l["label"] for l in s["loads"]}
                               for s in sectors}
        cls.tracker_ids = {o["id"] for o in load("opportunities.json")["opportunities"]}

    def test_rows_exist_and_ids_unique(self):
        self.assertGreater(len(self.sites), 0)
        ids = [s["id"] for s in self.sites]
        self.assertEqual(len(ids), len(set(ids)), "duplicate site ids")

    def test_required_fields(self):
        required = ("id", "name", "category", "band", "country", "region",
                    "status", "depth", "owner", "summary", "sources")
        for s in self.sites:
            for k in required:
                self.assertIn(k, s, f"{s.get('id', '?')}: missing {k}")

    def test_enums_come_from_meta(self):
        statuses = set(self.meta["status_values"])
        depths = set(self.meta["depth_values"])
        for s in self.sites:
            self.assertIn(s["status"], statuses,
                          f"{s['id']}: status {s['status']!r} not declared in _meta.status_values")
            self.assertIn(s["depth"], depths, f"{s['id']}: bad depth")

    def test_band_matches_sectors_file(self):
        """A row filed under one of the Applications tab's sectors must use one
        of that sector's exact load labels — otherwise the site list and the
        Applications page drift apart."""
        for s in self.sites:
            if s["category"] in self.bands_by_sector:
                self.assertIn(s["band"], self.bands_by_sector[s["category"]],
                              f"{s['id']}: band {s['band']!r} is not a load label "
                              f"of sector {s['category']!r}")

    def test_every_row_cited_with_full_urls(self):
        for s in self.sites:
            self.assertTrue(s["sources"], f"{s['id']}: no sources")
            for src in s["sources"]:
                self.assertTrue(src.get("label"), f"{s['id']}: source missing label")
                url = src.get("url", "")
                self.assertTrue(url.startswith("http"), f"{s['id']}: bad url {url!r}")
                path = url.split("://", 1)[-1]
                self.assertIn("/", path.rstrip("/"),
                              f"{s['id']}: bare homepage source {url!r}")

    def test_filings_have_forum_type_url(self):
        for s in self.sites:
            for f in s.get("filings", []):
                for k in ("forum", "type", "url"):
                    self.assertTrue(f.get(k), f"{s['id']}: filing missing {k}")
                self.assertTrue(f["url"].startswith("http"), f"{s['id']}: filing url")

    def test_tracker_ids_resolve(self):
        for s in self.sites:
            if s.get("tracker_id"):
                self.assertIn(s["tracker_id"], self.tracker_ids,
                              f"{s['id']}: tracker_id {s['tracker_id']!r} not in opportunities.json")

    def test_deep_rows_carry_documents(self):
        """depth=deep is a claim that primary documents were read; require at
        least two evidence entries (sources + filings) so a one-link row
        cannot masquerade as a deep dive."""
        for s in self.sites:
            if s["depth"] == "deep":
                self.assertGreaterEqual(len(s["sources"]) + len(s.get("filings", [])), 2,
                                        f"{s['id']}: deep row with <2 evidence entries")

    def test_scanner_covers_this_file(self):
        """check_citations must scan deployment_sites rows — mutation-checked:
        a numbered, source-less row must produce a violation."""
        import check_citations
        base = check_citations.check()
        self.assertEqual([v for v in base if v[0].startswith("deployment_sites")], [])
        # mutation: write a temp copy with a stripped row and re-run against it
        doc = json.loads(json.dumps(self.doc))
        doc["sites"][0]["sources"] = []
        doc["sites"][0]["summary"] = "carries 15 MWt and 2029 with no source"
        p = DATA / "deployment_sites.json"
        original = p.read_text()
        try:
            p.write_text(json.dumps(doc))
            mutated = check_citations.check()
            self.assertTrue([v for v in mutated if v[0].startswith("deployment_sites")],
                            "scanner failed to flag a source-less numbered site row")
        finally:
            p.write_text(original)


class TestQuoteCacheOffline(unittest.TestCase):
    """When the local cache is present, every quoted source that is in the
    source index must contain its quote (offline check — the cache is
    gitignored, so CI skips this)."""

    def test_quotes_match_cache(self):
        if not (DATA / "cache").is_dir() or not (DATA / "research" / "source_index.json").exists():
            self.skipTest("data/cache not present (gitignored; local-only check)")
        import verify_quotes
        self.assertEqual(verify_quotes.check_against_cache(), 0,
                         "a recorded quote no longer matches the cached source bytes")


if __name__ == "__main__":
    unittest.main()
