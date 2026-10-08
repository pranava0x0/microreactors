"""Contract for data/segments.json (Applications > Space and more) and the Type S gate.

Groups and statuses are derived from the file's own _meta and the validator, never
re-typed here. The validator half fires both ways: a record that must pass and one
that must fail for each Type S rule.
"""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import research_pass  # noqa: E402

STATUSES = {"operating", "contracted", "funded", "studied", "proposed", "cancelled"}


class TestSegments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((ROOT / "data" / "segments.json").read_text())

    def test_every_segment_has_a_known_group_a_status_and_a_source(self):
        groups = {g["id"] for g in self.doc["_meta"]["groups"]}
        ids = [s["id"] for s in self.doc["segments"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate segment id")
        for s in self.doc["segments"]:
            self.assertIn(s["group"], groups, s["id"])
            self.assertIn(s["status"], STATUSES, s["id"])
            self.assertTrue(s["sources"], f"{s['id']} has no source")
            self.assertTrue(any(c.isdigit() for c in s["power_class"] + s["what_it_says"]), s["id"])

    def test_every_group_is_used(self):
        used = {s["group"] for s in self.doc["segments"]}
        self.assertEqual({g["id"] for g in self.doc["_meta"]["groups"]}, used)

    def test_type_s_gate_fires_both_ways(self):
        src = {"label": "Publisher — Document 2026", "url": "https://example.test/doc",
               "quote": "a verbatim span", "status": "fetched"}
        good = {"id": "a1", "segment": "district heat", "name": "Pilot", "status": "studied",
                "power_class": "50 MWth", "what_it_says": "x", "microreactor_read": "x", "sources": [src]}
        bad = dict(good, id="a2", power_class="large", what_it_says="no figure here")
        with tempfile.TemporaryDirectory() as tmp:
            for name, rec in (("good", good), ("bad", bad)):
                d = pathlib.Path(tmp) / name
                d.mkdir()
                (d / "f.json").write_text(json.dumps(
                    {"_meta": {"captured": "2026-10-08", "absences": ["x"]}, "applications": [rec]}))
            self.assertEqual(research_pass.cmd_validate(pathlib.Path(tmp) / "good"), 0)
            self.assertEqual(research_pass.cmd_validate(pathlib.Path(tmp) / "bad"), 1)


if __name__ == "__main__":
    unittest.main()
