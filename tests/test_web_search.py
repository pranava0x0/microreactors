"""tools/web_search.py, offline: the two endpoint parsers must fire on their
own markup (a regex that goes quiet reports every query as empty, which reads
exactly like a quiet web), and a partial plan re-run must keep the topics it
did not touch."""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import web_search as ws  # noqa: E402

HTML_PAGE = (
    '<div class="result"><a rel="nofollow" class="result__a" '
    'href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.cvea.org%2Fpress%2Frelease.html&amp;rut=1">'
    'Reactor Project <b>Tabled</b> by CVEA</a><a class="result__snippet" href="x">'
    'Since 2021, CVEA &amp; USNC studied a 10 MW unit</a></div>')
LITE_PAGE = (
    '<tr><td><a rel="nofollow" href="https://rca.alaska.gov/x/order.pdf" class=\'result-link\'>'
    'RCA order</a></td></tr><tr><td class=\'result-snippet\'>Doyon tariff filing</td></tr>')


class Parsers(unittest.TestCase):
    def test_html_endpoint(self):
        rows = ws.parse(HTML_PAGE)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://www.cvea.org/press/release.html")
        self.assertEqual(rows[0]["title"], "Reactor Project Tabled by CVEA")
        self.assertEqual(rows[0]["host"], "cvea.org")
        self.assertIn("CVEA & USNC", rows[0]["snippet"])

    def test_lite_endpoint(self):
        rows = ws.parse(LITE_PAGE, ws.LITE)
        self.assertEqual([r["url"] for r in rows], ["https://rca.alaska.gov/x/order.pdf"])
        self.assertEqual(rows[0]["snippet"], "Doyon tariff filing")

    def test_parsers_are_not_cross_wired(self):
        self.assertEqual(ws.parse(HTML_PAGE, ws.LITE), [])
        self.assertEqual(ws.parse(LITE_PAGE), [])

    def test_denied_host_dropped(self):
        page = HTML_PAGE.replace("www.cvea.org", "www.pinterest.com")
        self.assertEqual(ws.parse(page), [])


class PlanRuns(unittest.TestCase):
    def test_only_keeps_untouched_topics(self):
        plan = {"title": "t", "topics": [
            {"id": "a", "issue": 1, "queries": ["qa"]},
            {"id": "b", "issue": 2, "queries": ["qb"]}]}
        calls = []

        def fake(query, pause):
            calls.append(query)
            return [{"title": "T " + query, "url": "https://x.org/" + query, "host": "x.org",
                     "snippet": "s"}]
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d)
            orig = ws.run_query
            ws.run_query = fake
            try:
                ws.run_plan(plan, out, 8, 0)
                first_a = (out / "a.json").read_text()
                ws.run_plan(plan, out, 8, 0, only=["b"])
            finally:
                ws.run_query = orig
            self.assertEqual(calls, ["qa", "qb", "qb"], "only=[b] must not re-run a")
            self.assertEqual((out / "a.json").read_text(), first_a)
            digest = (out / "digest.md").read_text()
            self.assertIn("## a (issue #1)", digest)
            self.assertIn("https://x.org/qb", digest)
            self.assertEqual(json.loads((out / "b.json").read_text())["_meta"]["hits"], 1)


if __name__ == "__main__":
    unittest.main()
