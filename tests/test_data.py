"""Data-integrity gates. Run before any commit: python3 -m unittest discover tests

Every gate here exists because the dataset's whole value is that its claims are
cited. A row that ships without a source, a source that is just a homepage, or
an 'idea' dressed as a fact are the three failure classes these tests block.
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load(name):
    return json.loads((DATA / name).read_text())


def srcs_of(rec):
    out = list(rec.get("sources") or [])
    if rec.get("source"):
        out.append(rec["source"])
    return out


# Homepages that are knowingly weak citations are not allowed to hide: either
# the row's gaps note names the weakness, or the URL must carry a real path.
URL_RE = re.compile(r"^https://[^\s]+$")
BAND_RE = re.compile(r"^\d+(\.\d+)?–\d+(\.\d+)?\+? MW$")


class SourceShape(unittest.TestCase):
    def assert_source(self, s, where):
        self.assertTrue(s.get("label"), f"{where}: source missing label")
        url = s.get("url", "")
        self.assertRegex(url, URL_RE, f"{where}: bad url {url!r}")
        path = url.split("//", 1)[1]
        self.assertIn("/", path.rstrip("/"),
                      f"{where}: bare-homepage citation {url!r} — cite the page that carries the claim")

    def test_opportunities_all_cited(self):
        rows = load("opportunities.json")["opportunities"]
        self.assertGreater(len(rows), 0)
        for o in rows:
            ss = srcs_of(o)
            self.assertTrue(ss, f"opportunity {o['id']} has no source")
            for s in ss:
                self.assert_source(s, f"opportunity {o['id']}")

    def test_vendors_all_cited(self):
        vendors = load("vendors.json")["vendors"]
        self.assertGreater(len(vendors), 0)
        for v in vendors:
            ss = srcs_of(v)
            self.assertTrue(ss, f"vendor {v['id']} has no source")
            for s in ss:
                self.assert_source(s, f"vendor {v['id']}")

    def test_vendor_delivery_year_agrees_with_target_text(self):
        """first_delivery_year (drives the hero stat) duplicates a fact stated
        in first_delivery_target prose; duplicated values must be tested for
        agreement or they drift (CLAUDE.md single-source-of-truth)."""
        for v in load("vendors.json")["vendors"]:
            year = v.get("first_delivery_year")
            self.assertIsNotNone(year, f"{v['id']}: missing first_delivery_year")
            target = v.get("first_delivery_target") or ""
            milestones = " ".join(m["date"] for m in v.get("milestones", []))
            self.assertIn(str(year), target + " " + milestones,
                          f"{v['id']}: first_delivery_year {year} not stated in "
                          f"target text or milestones — copies drifted")

    def test_cost_bands_all_cited(self):
        costs = load("costs.json")
        rows = costs["microreactor_lcoe"] + costs["displaced_alternatives"]
        self.assertGreater(len(rows), 0)
        for r in rows:
            name = r.get("scenario") or r.get("alternative")
            ss = srcs_of(r)
            self.assertTrue(ss, f"cost band {name!r} has no source")
            for s in ss:
                self.assert_source(s, f"cost band {name!r}")

    def test_incentive_points_cited(self):
        inc = load("costs.json")["incentives"]
        self.assertTrue(inc["points"], "incentives block has no points")
        for p in inc["points"]:
            ss = srcs_of(p)
            self.assertTrue(ss, f"incentive point uncited: {p['fact'][:60]}")
            for s in ss:
                self.assert_source(s, "incentives")

    def test_precedents_cited(self):
        groups = load("mechanisms.json")["precedent_groups"]
        self.assertGreaterEqual(len(groups), 2, "precedent groups missing")
        n = 0
        for g in groups:
            for p in g["items"]:
                ss = srcs_of(p)
                self.assertTrue(ss, f"precedent {p.get('name')!r} has no source")
                for s in ss:
                    self.assert_source(s, f"precedent {p.get('name')!r}")
                n += 1
        self.assertGreaterEqual(n, 10, "precedent list suspiciously small")

    def test_policy_kinds_and_sources(self):
        groups = load("policy.json")["groups"]
        for g in groups:
            for pw in g["pathways"]:
                kind = pw.get("kind")
                self.assertIn(kind, ("enacted", "proposed", "program", "finding", "idea"),
                              f"pathway {pw.get('name')!r} bad kind {kind!r}")
                ss = srcs_of(pw)
                if kind == "idea":
                    self.assertFalse(ss, f"idea {pw.get('name')!r} carries a source — "
                                         "then it isn't an idea; reclassify it")
                else:
                    self.assertTrue(ss, f"{kind} pathway {pw.get('name')!r} has no source")
                    for s in ss:
                        self.assert_source(s, f"pathway {pw.get('name')!r}")


class DemandBands(unittest.TestCase):
    def test_band_format(self):
        sectors = load("sectors.json")["sectors"]
        loads = [l for s in sectors for l in s["loads"]]
        self.assertGreater(len(loads), 40)
        for l in loads:
            self.assertRegex(l["band"], BAND_RE, f"load {l['label']!r} band {l['band']!r}")

    def test_every_load_cited_or_registered_uncited(self):
        """A load either carries a source or its label sits in _meta.uncited —
        an explicit, visible register of what still needs evidence. Silence is
        the one state a band is not allowed to be in."""
        data = load("sectors.json")
        uncited_register = set(data["_meta"].get("uncited", []))
        loads = [l for s in data["sectors"] for l in s["loads"]]
        for l in loads:
            if srcs_of(l):
                self.assertNotIn(l["label"], uncited_register,
                                 f"{l['label']!r} is cited AND in the uncited register — remove it there")
            else:
                self.assertIn(l["label"], uncited_register,
                              f"{l['label']!r} has no source and is not registered as uncited")
        for label in uncited_register:
            self.assertIn(label, {l["label"] for l in loads},
                          f"uncited register names unknown load {label!r}")

    def test_load_sources_shape(self):
        sectors = load("sectors.json")["sectors"]
        checker = SourceShape("assert_source")
        n = 0
        for s in sectors:
            for l in s["loads"]:
                for src in srcs_of(l):
                    checker.assert_source(src, f"load {l['label']!r}")
                    n += 1
        # Vacuity floor: once integrated, the demand table must carry real
        # citations. If this number is ever legitimately lower, the dataset
        # regressed — that is a finding, not a test to relax.
        self.assertGreaterEqual(n, 1, "no demand load carries any source at all")


class Register(unittest.TestCase):
    BANNED = ["delve", "leverage", "seamless", "cutting-edge", "game-chang",
              "it's worth noting", "in today's", "unlock", "empower",
              "harness the", "testament to", "ever-evolving"]

    @staticmethod
    def prose_of(node):
        """Authored prose only: source dicts (labels are external titles,
        quotes are verbatim) are exempt from the register rules."""
        if isinstance(node, dict):
            out = []
            for k, v in node.items():
                if k in ("sources", "source", "url", "label", "quote"):
                    continue
                out.extend(Register.prose_of(v))
            return out
        if isinstance(node, list):
            out = []
            for v in node:
                out.extend(Register.prose_of(v))
            return out
        if isinstance(node, str):
            return [node]
        return []

    def test_no_ai_register_in_authored_prose(self):
        for name in ("costs.json", "sectors.json", "mechanisms.json",
                     "policy.json", "opportunities.json", "vendors.json"):
            strings = self.prose_of(load(name))
            self.assertTrue(strings, f"{name}: prose extraction found nothing")
            text = " \n".join(strings).lower()
            for word in self.BANNED:
                self.assertNotIn(word, text, f"{name} contains banned register word {word!r}")

    def test_no_ai_register_in_markup(self):
        """index.html was outside this lint until 2026-08-23, which is how a
        section eyebrow shipped reading "rules that unlock the sale"."""
        html = (ROOT / "site" / "index.html").read_text()
        body = re.sub(r"<head>.*?</head>", "", html, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", body).lower()
        self.assertGreater(len(text), 500, "markup text extraction failed")
        for word in self.BANNED:
            i = text.find(word)
            self.assertEqual(i, -1, f"index.html contains banned register word {word!r}: "
                                    f"...{text[max(0, i - 40):i + 40].strip()}...")

    def test_structural_register_lint_passes(self):
        """tools/check_register.py, run as the tests run it: headline shapes
        (comma-tail, colon-setup) that no word list can catch."""
        sys.path.insert(0, str(ROOT / "tools"))
        import check_register
        self.assertEqual(check_register.check(), [],
                         "structural register hits — see tools/check_register.py")


if __name__ == "__main__":
    unittest.main()
