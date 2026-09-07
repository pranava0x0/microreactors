"""Schema, citation and arithmetic contract for data/strategy.json.

The file says what a unit has to cost to win each buyer and who has a structural
reason to buy. Two things can rot silently: a reference to a benchmark, site,
tracker row, instrument or news item that was renamed or deleted, and a derived
figure (the staffing floor, the per-unit table, the $/kWe-to-$/MWh conversion)
whose stored value drifts from the inputs it claims to be arithmetic on. Both
are recomputed here from the data, never re-typed.
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))


def load(name: str):
    return json.loads((DATA / name).read_text())


def crf(r: float, n: int) -> float:
    return r * (1 + r) ** n / ((1 + r) ** n - 1)


class TestStrategy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load("strategy.json")
        cls.meta = cls.doc["_meta"]
        cls.rungs = cls.doc["ladder"]["rungs"]
        cls.segments = cls.doc["segments"]
        cls.prospects = cls.doc["prospects"]
        sectors = load("sectors.json")["sectors"]
        cls.sector_names = {s["sector"] for s in sectors} | set(cls.meta["extra_sectors"])
        bench = load("benchmarks.json")
        cls.pools = {
            "benchmark": {r["id"] for s in bench["sectors"] for r in s["records"]},
            "opportunity": {o["id"] for o in load("opportunities.json")["opportunities"]},
            "site": {s["id"] for s in load("deployment_sites.json")["sites"]},
            "instrument": {r["id"] for g in load("instruments.json")["groups"] for r in g["records"]},
            "news": {n["id"] for n in load("news.json")["items"]},
        }

    # ---- shape -------------------------------------------------------------
    def test_ids_unique_and_present(self):
        for block in (self.rungs, self.segments, self.prospects):
            ids = [x["id"] for x in block]
            self.assertTrue(ids)
            self.assertEqual(len(ids), len(set(ids)), f"duplicate ids: {ids}")

    def test_required_fields(self):
        seg_req = ("id", "name", "sector", "incumbent", "price_form", "term", "clears",
                   "verdict", "blocker", "first_deal", "benchmark_ids", "sources")
        pro_req = ("id", "name", "advantage", "sector", "region", "load", "documented", "fit",
                   "sale_shape", "status", "next_question", "refs", "sources")
        for sg in self.segments:
            for k in seg_req:
                self.assertIn(k, sg, f"segment {sg.get('id')}: missing {k}")
        for p in self.prospects:
            for k in pro_req:
                self.assertIn(k, p, f"prospect {p.get('id')}: missing {k}")

    def test_enums_come_from_meta(self):
        advs = {a["id"] for a in self.meta["advantage_types"]}
        statuses = set(self.meta["status_values"])
        rung_ids = {r["id"] for r in self.rungs}
        for p in self.prospects:
            self.assertIn(p["advantage"], advs, p["id"])
            self.assertIn(p["status"], statuses, p["id"])
            self.assertIn(p["sector"], self.sector_names, f"{p['id']}: sector {p['sector']!r} "
                          "is neither an Applications sector nor declared in _meta.extra_sectors")
        for sg in self.segments:
            self.assertIn(sg["clears"], rung_ids, sg["id"])
            self.assertIn(sg["sector"], self.sector_names, sg["id"])
        for r in self.rungs:
            for sid in r["opens"]:
                self.assertIn(sid, {s["id"] for s in self.segments}, f"rung {r['id']} opens unknown segment {sid}")

    def test_every_advantage_type_is_used(self):
        """A declared type with zero prospects renders as an empty filter chip."""
        used = {p["advantage"] for p in self.prospects}
        for a in self.meta["advantage_types"]:
            self.assertIn(a["id"], used, f"advantage type {a['id']} has no prospect")

    # ---- citations ---------------------------------------------------------
    def assert_sources(self, rec, where):
        srcs = rec.get("sources") or []
        self.assertTrue(srcs, f"{where}: no sources")
        for s in srcs:
            self.assertTrue(s.get("label"), f"{where}: source missing label")
            url = s.get("url", "")
            self.assertRegex(url, r"^https://\S+$", f"{where}: bad url {url!r}")
            self.assertIn("/", url.split("//", 1)[1].rstrip("/"),
                          f"{where}: bare-homepage citation {url!r}")

    def test_everything_cited(self):
        for r in self.rungs:
            self.assert_sources(r, f"rung {r['id']}")
        for sg in self.segments:
            self.assert_sources(sg, f"segment {sg['id']}")
        for p in self.prospects:
            self.assert_sources(p, f"prospect {p['id']}")
        for inp in self.doc["floor"]["inputs"]:
            self.assert_sources(inp, f"floor input {inp['id']}")
        self.assert_sources(self.doc["floor"], "floor")
        self.assert_sources(self.doc["ladder"]["units"], "units")
        self.assert_sources(self.doc["ladder"]["conversion"], "conversion")

    def test_references_resolve(self):
        """Cross-references are by id into the other data files, so a renamed
        benchmark or a delisted site fails here instead of rendering a dead link."""
        for sg in self.segments:
            for bid in sg["benchmark_ids"]:
                self.assertIn(bid, self.pools["benchmark"], f"segment {sg['id']} names unknown benchmark {bid}")
        for p in self.prospects:
            self.assertTrue(p["refs"], f"prospect {p['id']} has no refs")
            for ref in p["refs"]:
                self.assertEqual(len(ref), 1, f"prospect {p['id']}: ref must be one {{kind: id}} pair")
                kind, rid = next(iter(ref.items()))
                self.assertIn(kind, self.pools, f"prospect {p['id']}: unknown ref kind {kind}")
                self.assertIn(rid, self.pools[kind], f"prospect {p['id']}: {kind} {rid} does not exist")

    def test_cited_urls_are_already_in_the_register(self):
        """The file's own contract: its hand-written rows fetch nothing new; they
        restate rows the site already verified, so every URL they cite must
        already be cited by another data file. The one place a new URL enters is
        a `findings` entry, which is generated from a validated research pass
        (tools/merge_answers.py) and carries its own fetched source, so findings
        are walked separately and excluded here."""
        import build_data
        others = set()

        def walk(n, out, skip_findings=False):
            if isinstance(n, dict):
                if isinstance(n.get("url"), str) and isinstance(n.get("label"), str):
                    out.add(n["url"])
                for k, v in n.items():
                    if skip_findings and k == "findings":
                        continue
                    walk(v, out, skip_findings)
            elif isinstance(n, list):
                for v in n:
                    walk(v, out, skip_findings)
        for name in build_data.FILES:
            if name != "strategy":
                walk(load(f"{name}.json"), others)
        mine, via_findings = set(), set()
        walk(self.doc, mine, skip_findings=True)
        for rec in self.prospects + self.segments:
            walk(rec.get("findings", []), via_findings)
        # A row may cite a URL its own findings brought in: the finding is where it
        # was verified, and the row's prose then restates it.
        self.assertEqual(mine - others - via_findings, set(),
                         "strategy.json cites URLs neither another file nor a finding has verified")

    # ---- arithmetic --------------------------------------------------------
    def test_floor_rows_recompute_from_inputs(self):
        F = self.doc["floor"]
        by_id = {i["id"]: i for i in F["inputs"]}
        self.assertEqual([r["input"] for r in F["rows"]], list(by_id))
        for row in F["rows"]:
            inp = by_id[row["input"]]
            self.assertEqual(row["usd_per_year"], inp["usd_per_year"])
            for m in F["sizes_mwe"]:
                want = round(inp["usd_per_year"] / (m * 8760 * F["cf"]), 1)
                self.assertAlmostEqual(row["per_mwh"][str(m)], want, places=1,
                                       msg=f"floor {row['input']} at {m} MWe")

    def test_mass_produced_floor_is_first_unit_times_38_percent(self):
        by_id = {i["id"]: i for i in self.doc["floor"]["inputs"]}
        self.assertEqual(by_id["inl-staff-mass-produced"]["usd_per_year"],
                         round(by_id["inl-staff-first-unit"]["usd_per_year"] * (1 - 0.62)))

    def test_units_table_recomputes_from_rungs(self):
        U = self.doc["ladder"]["units"]
        rung = {r["id"]: r for r in self.rungs}
        for row in U["rows"]:
            r = rung[row["rung"]]
            for m in U["sizes_mwe"]:
                lo, hi = row["usd_millions"][str(m)]
                self.assertAlmostEqual(lo, round(r["capex_low_kwe"] * m / 1000, 1), places=1)
                self.assertAlmostEqual(hi, round(r["capex_high_kwe"] * m / 1000, 1), places=1)

    def test_conversion_rows_recompute(self):
        for r in self.doc["ladder"]["conversion"]["rows"]:
            c = crf(r["real_rate"], r["life_years"])
            self.assertAlmostEqual(r["crf"], round(c, 4), places=4)
            self.assertAlmostEqual(r["usd_per_mwh_per_1000_kwe"], round(1000 * c / (8.76 * r["cf"]), 1), places=1)

    def test_all_in_floor_is_a_floor_above_the_overnight_range(self):
        """INL states the first unit's all-in cost as exceeding $22,000/kWe. It is
        carried as a separate floor, never as the top of the overnight range: a
        range whose ceiling is really a floor understates the buyer-facing price."""
        U = self.doc["ladder"]["units"]
        for r in self.rungs:
            if "all_in_min_kwe" in r:
                self.assertGreater(r["all_in_min_kwe"], r["capex_high_kwe"], r["id"])
                self.assertTrue(r.get("all_in_note"), f"{r['id']}: all-in floor without a note")
                row = next(x for x in U["rows"] if x["rung"] == r["id"])
                for m in U["sizes_mwe"]:
                    self.assertAlmostEqual(row["all_in_min_usd_millions"][str(m)],
                                           round(r["all_in_min_kwe"] * m / 1000, 1), places=1)
        first = next(r for r in self.rungs if r["id"] == "first-unit")
        self.assertIn("all_in_min_kwe", first, "the first-unit rung must carry INL's all-in floor")

    def test_floor_has_a_lone_site_case(self):
        """The fleet allocation (a guard shared across two reactors) cannot price a
        single reactor at an isolated site; that case must be its own row and cost
        more per reactor than the shared one."""
        by_id = {i["id"]: i for i in self.doc["floor"]["inputs"]}
        self.assertIn("lone-site-guards", by_id)
        self.assertGreater(by_id["lone-site-guards"]["usd_per_year"], by_id["guard-and-monitor"]["usd_per_year"])

    def test_rungs_descend_in_capital_cost(self):
        highs = [r["capex_high_kwe"] for r in self.rungs]
        self.assertEqual(highs, sorted(highs, reverse=True), "rungs must run from the first unit down")

    # ---- wiring ------------------------------------------------------------
    def test_page_wiring(self):
        html = (ROOT / "site" / "index.html").read_text()
        app = (ROOT / "site" / "assets" / "app.js").read_text()
        for sub in ('data-sub="win" id="economics-win"', 'data-sub="prospects" id="pipeline-prospects"'):
            self.assertIn(sub, html)
        self.assertEqual(len(re.findall(r'lazy: \{ name: "strategy"', app)), 2,
                         "both sub-tabs must load the strategy payload lazily")

    def test_findings_shape(self):
        """A finding is copied from a validated pass answer: it names a date, a
        status from the pass contract, and unless absent, at least one fetched
        source. An absent one lists what was searched."""
        for rec in self.prospects + self.segments:
            for f in rec.get("findings", []):
                self.assertIn(f.get("status"), ("answered", "partial", "absent"), rec["id"])
                self.assertRegex(f.get("date", ""), r"^\d{4}-\d{2}-\d{2}$", rec["id"])
                self.assertTrue(f.get("finding"), rec["id"])
                if f["status"] == "absent":
                    self.assertTrue(f.get("searched"), f"{rec['id']}: absent finding without angles")
                else:
                    self.assert_sources(f, f"finding {rec['id']}/{f.get('id')}")
                    self.assertTrue(any(s.get("status") == "fetched" for s in f["sources"]),
                                    f"{rec['id']}/{f.get('id')}: finding with no fetched source")

    def test_findings_match_their_pass(self):
        """`findings` are generated by tools/merge_answers.py from the pass
        folders below. A hand edit to a finding, or an edited answer that was
        never re-merged, is drift and fails here."""
        import subprocess
        passes = [ROOT / "data" / "research" / "2026-09-02-prospects"]
        for p in passes:
            self.assertTrue(p.is_dir(), p)
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "merge_answers.py"),
                            *[str(p.relative_to(ROOT)) for p in passes], "--check"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_summary_counts_match(self):
        bundle = json.loads((ROOT / "site" / "data.js").read_text().split("window.MR=", 1)[1].rsplit(";", 1)[0])
        self.assertEqual(bundle["summary"]["prospects"], len(self.prospects))
        self.assertEqual(bundle["summary"]["segments"], len(self.segments))
        self.assertIn("strategy", bundle["lazy"])


if __name__ == "__main__":
    unittest.main()
