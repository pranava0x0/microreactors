"""The pass validator's third record type, negative-tested in both directions:
a good answer must pass and each defect must fail, or the gate has gone quiet."""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import research_pass  # noqa: E402

GOOD = {"_meta": {"captured": "2026-09-02", "agent": "t", "scope": "t", "angles_run": ["a"],
                  "absences": ["x"]},
        "answers": [{"id": "doyon-fuel-cost", "for": "doyon-utilities",
                     "question": "q", "status": "partial", "finding": "f 2024",
                     "figures": {"rate": "$0.10/kWh"}, "searched": ["a"],
                     "sources": [{"label": "RCA — order", "url": "https://rca.alaska.gov/x/y.pdf",
                                  "quote": "a verbatim span", "status": "fetched"}]}]}


def run(doc):
    with tempfile.TemporaryDirectory() as d:
        (pathlib.Path(d) / "a.json").write_text(json.dumps(doc))
        errors, seen = [], {}
        for path, kind, loaded in research_pass.load_pass(pathlib.Path(d)):
            for rec in loaded["answers"]:
                research_pass.check_answer(rec, path, errors, seen)
        return errors


class Answers(unittest.TestCase):
    def test_known_good_passes(self):
        self.assertEqual(run(GOOD), [])

    def test_each_defect_fails(self):
        import copy
        cases = {
            "unknown prospect": lambda r: r.update({"for": "nobody"}),
            "bad status": lambda r: r.update({"status": "maybe"}),
            "finding without a fetched source": lambda r: r["sources"][0].update({"status": "snippet-only"}),
            "finding with no sources": lambda r: r.update({"sources": []}),
            "absent without searched": lambda r: r.update({"status": "absent", "searched": [], "sources": []}),
            "placeholder finding": lambda r: r.update({"finding": "TBD"}),
        }
        for name, mutate in cases.items():
            doc = copy.deepcopy(GOOD)
            mutate(doc["answers"][0])
            self.assertTrue(run(doc), f"{name}: validator stayed silent")

    def test_absent_with_angles_passes_without_sources(self):
        import copy
        doc = copy.deepcopy(GOOD)
        doc["answers"][0].update({"status": "absent", "sources": [], "searched": ["a", "b"]})
        self.assertEqual(run(doc), [])

    def test_mixed_file_yields_both_kinds(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "m.json").write_text(json.dumps({"cases": [], "answers": []}))
            kinds = sorted(k for _, k, _ in research_pass.load_pass(pathlib.Path(d)))
            self.assertEqual(kinds, ["answer", "case"])


if __name__ == "__main__":
    unittest.main()
