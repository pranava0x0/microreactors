"""The interaction-cost UAT must charge every journey from a fresh Home load.

Optional like test_layout_e2e: skips without Playwright. Guards the bug found
2026-10-31, where a second journey reused the loaded document and the
browser's anchor jump to #home handed it free scroll.
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

try:
    from playwright.sync_api import sync_playwright  # type: ignore
    _HAVE_PW = True
except ImportError:
    _HAVE_PW = False

import uat_paths  # noqa: E402

LEAD = [("see", "#home-lead")]


@unittest.skipUnless(_HAVE_PW, "Playwright not installed")
class FreshStartTest(unittest.TestCase):
    def test_journey_charges_scroll_from_page_top(self):
        vh = 1024
        with uat_paths.serve_site() as base, sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 768, "height": vh})
            page.goto(base, wait_until="networkidle")  # as main() does: no hash
            page.evaluate("scrollTo(0,0)")
            top = page.evaluate("document.querySelector('#home-lead').getBoundingClientRect().top")
            # Journeys share one page in main(); the free scroll only showed on
            # a journey that followed another.
            uat_paths.run_journey(page, base, uat_paths.JOURNEYS[0][1])
            runs = [uat_paths.run_journey(page, base, LEAD) for _ in range(2)]
            browser.close()
        expected = round(max(0, top - (vh - 200)) / vh, 2)
        self.assertGreater(expected, 0.5, "lead story should sit below the fold")
        for r in runs:
            self.assertAlmostEqual(r["screens"], expected, delta=0.02)


if __name__ == "__main__":
    unittest.main()
