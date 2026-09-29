"""Applications > Alaska gates.

The dossier's opportunity table is a hand-typed join (data/alaska.json's
_meta.opportunity_rows maps each row to a strategy.json prospect_id and/or a
deployment_sites.json site_id) over data the rest of the site already owns.
A hand-typed join drifts the moment either source file gains a new Alaska row
without the map being updated — these tests make that drift fail loud instead
of silently leaving the new row off the dossier page.
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

sys.path.insert(0, str(ROOT / "tools"))
import build_data  # noqa: E402


def load(name):
    return json.loads((DATA / f"{name}.json").read_text())


class OpportunityJoinCoverage(unittest.TestCase):
    """Every Alaska prospect/site in the source files must be in the join map,
    and every id the map names must actually exist in that source file."""

    def setUp(self):
        self.ak = load("alaska")
        self.rows = self.ak["_meta"]["opportunity_rows"]
        self.strategy = load("strategy")
        self.sites = load("deployment_sites")

    def test_every_alaska_prospect_is_mapped(self):
        mapped = {r["prospect_id"] for r in self.rows if r.get("prospect_id")}
        alaska_prospects = {p["id"] for p in self.strategy["prospects"]
                            if "Alaska" in p.get("region", "")}
        missing = alaska_prospects - mapped
        self.assertFalse(missing,
                         f"strategy.json prospect(s) {missing} mention Alaska but are not in "
                         "alaska.json's _meta.opportunity_rows")

    def test_every_alaska_site_is_mapped(self):
        mapped = {r["site_id"] for r in self.rows if r.get("site_id")}
        alaska_sites = {s["id"] for s in self.sites["sites"]
                        if "Alaska" in s.get("region", "")}
        missing = alaska_sites - mapped
        self.assertFalse(missing,
                         f"deployment_sites.json site(s) {missing} mention Alaska but are not in "
                         "alaska.json's _meta.opportunity_rows")

    def test_mapped_ids_exist(self):
        prospect_ids = {p["id"] for p in self.strategy["prospects"]}
        site_ids = {s["id"] for s in self.sites["sites"]}
        for row in self.rows:
            if row.get("prospect_id"):
                self.assertIn(row["prospect_id"], prospect_ids,
                             f"opportunity_rows:{row['id']} names a prospect_id that does not exist")
            if row.get("site_id"):
                self.assertIn(row["site_id"], site_ids,
                             f"opportunity_rows:{row['id']} names a site_id that does not exist")
            self.assertTrue(row.get("prospect_id") or row.get("site_id"),
                            f"opportunity_rows:{row['id']} names neither a prospect nor a site")

    def test_every_row_has_a_known_buyer_model(self):
        model_ids = {m["id"] for m in self.ak["buyer_models"]}
        for row in self.rows:
            self.assertIn(row["buyer_model"], model_ids,
                         f"opportunity_rows:{row['id']} names an unknown buyer_model "
                         f"{row['buyer_model']!r}")


class BenchmarkPrecedentCoverage(unittest.TestCase):
    """The precedent table in build_data.ALASKA_BENCHMARK_IDS is a second
    hand-typed list over benchmarks.json; guard it the same way."""

    def test_every_alaska_benchmark_is_listed(self):
        bench = load("benchmarks")
        alaska_ids = {r["id"] for sec in bench["sectors"] for r in sec["records"]
                     if "Alaska" in json.dumps(r)}
        listed = set(build_data.ALASKA_BENCHMARK_IDS)
        missing = alaska_ids - listed
        self.assertFalse(missing,
                         f"benchmarks.json record(s) {missing} mention Alaska but are not in "
                         "build_data.ALASKA_BENCHMARK_IDS")
        stale = listed - alaska_ids
        self.assertFalse(stale,
                         f"build_data.ALASKA_BENCHMARK_IDS names {stale}, which no longer exists "
                         "in benchmarks.json or no longer mentions Alaska")


class AlaskaPageBuild(unittest.TestCase):
    """The join itself: build it once and check the joined shape is sane."""

    def setUp(self):
        bundle = {name: load(name) for name in build_data.FILES}
        build_data.build_alaska_page(bundle)
        self.ak = bundle["alaska"]

    def test_opportunity_rows_have_a_name_and_region(self):
        for row in self.ak["opportunity_rows"]:
            self.assertTrue(row.get("name"), f"{row['id']} has no name after the join")
            self.assertTrue(row.get("region"), f"{row['id']} has no region after the join")

    def test_precedent_rows_all_resolved(self):
        self.assertEqual(len(self.ak["precedent_rows"]), len(build_data.ALASKA_BENCHMARK_IDS))
        for row in self.ak["precedent_rows"]:
            self.assertTrue(row.get("id"))
            self.assertTrue(row.get("sources"), f"{row['id']} has no sources")

    def test_power_mix_regions_sum_close_to_100(self):
        for region in self.ak["power_mix"]["regions"]:
            total = sum(region["mix_2021"].values())
            self.assertAlmostEqual(total, 100, delta=2,
                                   msg=f"{region['id']} fuel mix sums to {total}, not ~100%")


if __name__ == "__main__":
    unittest.main()
