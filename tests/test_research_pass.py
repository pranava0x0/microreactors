"""Gates for the deep research pass and the datasets derived from it.

Two distinct failures are covered:
  * a research file that drifts from the contract its agents were held to, and
  * a research file edited without re-running the merge, so data/ and the pass
    disagree about what the site is showing.
"""
import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Every pass folder merged into data/instruments.json and data/benchmarks.json.
# A pass that stops contributing to those files should drop out of this list;
# one still contributing but missing here would pass validate/report on its own
# while test_derived_datasets_match_the_pass silently stopped covering it.
PASS_DIRS = (
    ROOT / "data" / "research" / "deep-2026-08-24",
    ROOT / "data" / "research" / "2026-08-28-apps",
)
DERIVED = ("data/instruments.json", "data/benchmarks.json")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=ROOT,
                          capture_output=True, text=True, check=False)


class ResearchPass(unittest.TestCase):
    def test_pass_satisfies_its_contract(self):
        """Every record still validates: sources deep-linked and status-tagged,
        cases carry a number, mechanisms carry a precedent, ids unique."""
        for pass_dir in PASS_DIRS:
            r = run("tools/research_pass.py", "validate", str(pass_dir.relative_to(ROOT)))
            self.assertEqual(r.returncode, 0, pass_dir.name + "\n" + r.stdout + r.stderr)

    def test_voices_meta_carries_every_field_the_renderer_reads(self):
        """site/assets/app.js reads _meta.what_this_is and _meta.roster_note.
        Extracting the curated base dropped what_this_is, and the sub-tab
        rendered an empty paragraph on every visit - invisible to a browser
        check that counted rows and citations but never read the prose."""
        import json
        meta = json.loads((ROOT / "data" / "voices.json").read_text())["_meta"]
        app = (ROOT / "site" / "assets" / "app.js").read_text()
        for field in re.findall(r"D\.voices\._meta\.(\w+)", app):
            self.assertIn(field, meta, f"app.js renders _meta.{field}, which voices.json lacks")
            self.assertTrue(str(meta[field]).strip(), f"_meta.{field} is empty")

    def test_voices_matches_its_pass(self):
        """data/voices.json is derived from the 2026-08-29 pass plus the curated
        base. Nothing runs merge_voices.py automatically, so without this an edit
        to a research file that never reaches data/ ships as silent drift."""
        r = run("tools/merge_voices.py", "data/research/2026-08-29-voices", "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_news_matches_its_pass(self):
        """data/news.json is built from data/research/news by merge_news.py.
        It drifted once: PR #21 hand-edited eight items into the output, the seed
        pass sat marked incomplete, and nothing noticed that the file was no
        longer reproducible or even in date order."""
        r = run("tools/merge_news.py", "data/research/news", "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_derived_datasets_match_the_pass(self):
        """data/instruments.json and data/benchmarks.json are generated. Editing a
        research file without re-running the merge would silently leave the site
        rendering the older copy."""
        rel_dirs = [str(p.relative_to(ROOT)) for p in PASS_DIRS]
        r = run("tools/merge_research.py", *rel_dirs, "--check")
        self.assertEqual(r.returncode, 0,
                         "run: python3 tools/merge_research.py "
                         f"{' '.join(rel_dirs)}\n" + r.stdout + r.stderr)

    def test_every_derived_record_is_rendered_by_a_known_bucket(self):
        """The renderers key off `group` and `sector`. A record carrying a value
        no renderer knows about would build cleanly and never appear on the page."""
        sys.path.insert(0, str(ROOT / "tools"))
        import merge_research

        inst = json.loads((ROOT / "data" / "instruments.json").read_text())
        bench = json.loads((ROOT / "data" / "benchmarks.json").read_text())
        self.assertTrue(inst["groups"] and bench["sectors"])
        for g in inst["groups"]:
            self.assertIn(g["group"], merge_research.GROUP_ORDER, "unrendered instrument group")
        for s in bench["sectors"]:
            self.assertIn(s["sector"], merge_research.SECTOR_ORDER, "unrendered benchmark sector")

    def test_capture_date_handles_both_pass_folder_shapes(self):
        """Pass folders are named `<slug>-<date>` by hand and `<date>-<slug>` by
        research_pass.py init. Splitting on the first hyphen only handled the
        first, turning "2026-08-25-my-pass" into "08-25-my-pass" — which sorts
        below every real ISO date and would silently freeze the site's build
        stamp, since build_data takes the max captured date across data files."""
        sys.path.insert(0, str(ROOT / "tools"))
        import merge_research

        for name, want in [("deep-2026-08-24", "2026-08-24"),
                           ("2026-08-25-my-pass", "2026-08-25"),
                           ("x-2026-01-02-y", "2026-01-02")]:
            self.assertEqual(merge_research.capture_date(name), want, name)
        with self.assertRaises(SystemExit):
            merge_research.capture_date("no-date-here")

    def test_derived_files_are_not_hand_edited(self):
        """Each carries the generator that owns it, so the next reader does not
        edit the wrong file."""
        for rel in DERIVED:
            meta = json.loads((ROOT / rel).read_text())["_meta"]
            self.assertEqual(meta.get("generated_by"), "tools/merge_research.py", rel)
            self.assertTrue(meta.get("pass"), f"{rel} does not name its research pass")

    def test_news_capture_date_comes_from_complete_pass_files(self):
        """A static date made a refreshed pass look stale until somebody edited code."""
        import tempfile
        sys.path.insert(0, str(ROOT / "tools"))
        import merge_news
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            (folder / "old.json").write_text(json.dumps({
                "_meta": {"captured": "2026-08-18"}, "items": []}))
            (folder / "new.json").write_text(json.dumps({
                "_meta": {"captured": "2026-08-31"}, "items": []}))
            (folder / "partial.json").write_text(json.dumps({
                "_meta": {"captured": "2099-01-01", "incomplete": True}, "items": []}))
            self.assertEqual(merge_news.build(folder)["_meta"]["captured"], "2026-08-31")

    def test_extended_record_types_fire_both_ways(self):
        """Types D-G (precedent, region, docket, check), added 2026-09-26. A gate
        that has only ever seen passing input measures nothing, so each type gets
        a record that must pass and one that must fail for its own rule."""
        import tempfile
        src = {"label": "Publisher — Document 2026", "url": "https://example.test/doc",
               "quote": "a verbatim span", "status": "fetched"}
        good = {
            "precedents": [{"id": "p1", "mechanism": "advance-market-commitment",
                            "sector": "carbon removal", "name": "Frontier", "year": "2022",
                            "size": "$925M", "how_it_works": "x", "outcome": "x",
                            "microreactor_read": "x", "sources": [src]}],
            "regions": [{"id": "r1", "region": "Greenland", "power_system": "17 towns",
                         "nuclear_position": "x", "microreactor_read": "x", "sources": [src]}],
            "dockets": [{"id": "d1", "forum": "GA PSC", "utility": "Georgia Power",
                         "type": "IRP", "date": "2025-01-31", "docket": "56002",
                         "what_it_says": "x", "sources": [src]}],
            "checks": [{"id": "c1", "target": "janus", "file": "opportunities",
                        "claim": "x", "verdict": "confirmed", "evidence": "x",
                        "sources": [src]},
                       {"id": "c2", "target": "dome", "file": "opportunities",
                        "claim": "x", "verdict": "unverifiable", "evidence": "x"}],
            "items": [{"id": "n1", "date": "2026-09-09", "headline": "x", "category": "award",
                       "what_happened": "x", "why_it_matters": "x", "binding": False,
                       "sources": [src]}],
        }
        bad = {
            # nuclear sector, and no number anywhere
            "precedents": [dict(good["precedents"][0], id="p2", sector="nuclear fleet",
                                size="large", outcome="it worked")],
            # no number in price, power_system or loads
            "regions": [dict(good["regions"][0], id="r2", power_system="diesel towns")],
            # unknown type, and neither docket nor url
            "dockets": [{k: v for k, v in dict(good["dockets"][0], id="d2", type="memo").items()
                         if k != "docket"}],
            # outdated with no correction
            "checks": [dict(good["checks"][0], id="c3", verdict="outdated")],
            # unknown category, a non-ISO date, and the same url twice
            "items": [dict(good["items"][0], id="n2", category="rumour", date="Sept 9",
                           sources=[src, src])],
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, doc in (("good", good), ("bad", bad)):
                folder = pathlib.Path(tmp) / name
                folder.mkdir()
                for key, recs in doc.items():
                    (folder / f"{key}.json").write_text(json.dumps(
                        {"_meta": {"captured": "2026-09-26", "absences": ["x"]}, key: recs}))
            ok = run("tools/research_pass.py", "validate", str(pathlib.Path(tmp) / "good"))
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            ko = run("tools/research_pass.py", "validate", str(pathlib.Path(tmp) / "bad"))
            self.assertEqual(ko.returncode, 1, ko.stdout)
            for rule in ("non-nuclear", "no number in size", "no number in price",
                         "type 'memo'", "neither a docket", "must carry a correction",
                         "category 'rumour'", "is not YYYY-MM-DD", "the same url is listed twice"):
                self.assertIn(rule, ko.stdout)

    def test_quote_repair_keeps_literal_source_text(self):
        """Normal form is for matching only; a written quote remains source text."""
        sys.path.insert(0, str(ROOT / "tools"))
        import repair_quotes
        raw = "The Site’s stated target is 10 MW—firm power for remote loads."
        normal = repair_quotes.norm(raw)
        run = repair_quotes.longest_present_run(normal, normal)
        self.assertEqual(repair_quotes.original_span(run, raw), raw)
        source = {"url": "https://example.test", "quote": raw}
        record = {"source": source}
        self.assertEqual(repair_quotes.sources_for(record), [source])
        self.assertNotIn("sources", record)


if __name__ == "__main__":
    unittest.main()
