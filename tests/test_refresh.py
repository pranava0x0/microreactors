"""The refresh integrator edits shipped data unattended, so its matching rules are pinned here."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
import refresh_integrate as ri  # noqa: E402


class TestReplaceOnce(unittest.TestCase):
    def test_single_hit_is_replaced(self):
        rec = {"id": "x", "note": "base rate 19.35", "sources": [{"quote": "base rate 19.35"}]}
        self.assertEqual(ri.replace_once(rec, "19.35", "20.38"), 1)
        self.assertEqual(rec["note"], "base rate 20.38")
        self.assertEqual(rec["sources"][0]["quote"], "base rate 19.35", "quotes are never rewritten")

    def test_ambiguous_claim_is_left_alone(self):
        rec = {"id": "x", "a": "Not published", "b": "Not published"}
        self.assertEqual(ri.replace_once(rec, "Not published", "2028"), 2)
        self.assertEqual(rec, {"id": "x", "a": "Not published", "b": "Not published"})

    def test_missing_claim_changes_nothing(self):
        rec = {"id": "x", "a": "text"}
        self.assertEqual(ri.replace_once(rec, "absent", "new"), 0)


class TestResolve(unittest.TestCase):
    doc = {"rows": [{"id": "r1", "note": "n"}, {"note": "m"}], "vendors": [{"id": "v1"}]}

    def test_record_id(self):
        self.assertEqual(ri.resolve(self.doc, "v1"), {"id": "v1"})

    def test_index_path_ending_on_a_string_returns_its_dict(self):
        self.assertEqual(ri.resolve(self.doc, "rows[1].note"), {"note": "m"})

    def test_list_step_by_record_id(self):
        self.assertEqual(ri.resolve(self.doc, "rows.r1"), {"id": "r1", "note": "n"})

    def test_bad_path_is_none(self):
        self.assertIsNone(ri.resolve(self.doc, "rows[9].note"))
        self.assertIsNone(ri.resolve(self.doc, "nope"))


class TestDumpKeepsLayout(unittest.TestCase):
    def test_indent_and_trailing_newline_survive(self):
        for indent in (1, 2):
            for tail in ("", "\n"):
                with tempfile.TemporaryDirectory() as d:
                    p = pathlib.Path(d) / "f.json"
                    doc = {"a": [1, {"b": "é"}]}
                    p.write_text(json.dumps(doc, indent=indent, ensure_ascii=False) + tail)
                    before = p.read_text()
                    ri.dump(p, json.loads(before))
                    self.assertEqual(p.read_text(), before)


class TestNewsPassAppends(unittest.TestCase):
    def test_rerun_keeps_items_an_earlier_run_shipped(self):
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "refresh-2026-10-21.json"
            ri.write_news_pass(out, "2026-10-21", [{"id": "a"}])
            ri.write_news_pass(out, "2026-10-21", [{"id": "b"}])
            self.assertEqual([i["id"] for i in json.loads(out.read_text())["items"]], ["a", "b"])


class TestSourceOwner(unittest.TestCase):
    def test_group_target_attaches_to_the_pathway_holding_the_text(self):
        grp = {"id": "licensing", "pathways": [
            {"mechanism": "other", "sources": []},
            {"mechanism": "rate is $154", "sources": [{"url": "a"}]}]}
        self.assertIs(ri.source_owner(grp, "$154"), grp["pathways"][1])

    def test_flat_record_owns_its_own_sources(self):
        rec = {"id": "v", "status": "new text", "sources": []}
        self.assertIs(ri.source_owner(rec, "new text"), rec)

    def test_no_sources_anywhere_is_none(self):
        self.assertIsNone(ri.source_owner({"id": "x", "a": "t"}, "t"))


if __name__ == "__main__":
    unittest.main()
