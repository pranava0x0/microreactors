"""Gates for the deep research pass and the datasets derived from it.

Two distinct failures are covered:
  * a research file that drifts from the contract its agents were held to, and
  * a research file edited without re-running the merge, so data/ and the pass
    disagree about what the site is showing.
"""
import json
import pathlib
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


if __name__ == "__main__":
    unittest.main()
