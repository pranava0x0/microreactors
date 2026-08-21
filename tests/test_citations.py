"""The claim-coverage scanner, wired in at its seam: the test calls the same
check() the CLI runs, so unhooking the scanner from the suite is impossible
without this file going red."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_citations  # noqa: E402
import check_links  # noqa: E402


class ClaimCoverage(unittest.TestCase):
    def test_every_numbered_claim_is_covered(self):
        violations = check_citations.check()
        self.assertEqual(violations, [],
                         "numbered claims without a source (fix the data or, with a "
                         "stated reason, the allowlist): " + str(violations))

    def test_link_sweep_collects_urls_offline(self):
        """The sweep's URL collection must survive contract changes in
        collect_sources — it crashed once when the tuple grew a field.
        Network-free: only the collection path runs."""
        urls = check_links.collect_urls()
        self.assertGreater(len(urls), 50, "URL collection suspiciously small")
        for u in urls[:5]:
            self.assertTrue(u.startswith("http"), u)

    def test_scanner_is_not_vacuous(self):
        """The number regex must actually fire on this dataset's shapes, or a
        regression to 'matches nothing' would make the suite pass forever."""
        for sample in ("$140", "5–20 MW", "99.9%", "signed 2026-04-22",
                       "1.2 MWe", "2 acres", "$148/hour becomes /kW no wait /MWh"):
            self.assertTrue(check_citations.NUMBER_RE.search(sample), sample)
        for clean in ("no numbers here", "TRISO fuel", "heat pipe"):
            self.assertFalse(check_citations.NUMBER_RE.search(clean), clean)


if __name__ == "__main__":
    unittest.main()
