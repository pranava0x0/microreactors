"""Gates for the plain-language checker.

Two halves, and the second matters as much as the first:

  * the site's copy is clean, and
  * the checker still WORKS.

A checker that silently stops matching looks exactly like clean copy. That is
not hypothetical — a date lint written earlier the same day was "fixed" into
matching nothing and passed everything. So each pattern is fed a sentence it is
supposed to catch, and each is fed one it must leave alone.
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_language as cl

# (pattern name, a string it MUST flag, a similar string it must NOT flag)
CASES = [
    ("ui-narration",
     "Each card carries a cited roadmap to first power for that vendor and its site.",
     "Each card sets out what that vendor has built and when it expects first power."),
    ("meta-commentary",
     "The sources disagree about first-unit capital cost, and that disagreement is the useful part.",
     "The sources disagree about first-unit capital cost, so the range below is wide."),
    ("throat-clearing",
     "It is worth noting that no microreactor has yet sold power under a commercial contract.",
     "No microreactor has yet sold power under a commercial contract anywhere."),
    ("register-drift",
     "No figure here is a realised price, and the bands were compiled in order to show the spread.",
     "No figure here is a price anyone has paid, and the bands show the spread."),
    ("hedge-stack",
     "This could arguably be roughly typical of the sector, though possibly not in every case.",
     "This is typical of the sector, though the two largest sites are exceptions."),
]

EM_DASH_BAD = ("The rule ignores nuclear — which is the opening — because the list is closed — "
               "and no performance route exists for anything not already named on it.")
EM_DASH_OK = ("The rule ignores nuclear, which is the opening, because the list is closed and no "
              "performance route exists for anything not already named on it.")


def flags(text: str):
    """Pattern names this checker would raise for one string."""
    scrubbed = cl.QUOTED_TERM.sub(" ", text)
    names = [n for n, rx in cl.PATTERNS.items() if rx is not None and rx.search(scrubbed)]
    if cl.hedge_stack(scrubbed):
        names.append("hedge-stack")
    if text.count("—") > cl.EM_DASH_MAX:
        names.append("em-dash-pile")
    return names


class CheckerStillWorks(unittest.TestCase):
    """Prove each pattern fires, so the gate cannot go quiet unnoticed."""

    def test_each_pattern_catches_its_own_bad_case(self):
        for name, bad, _ in CASES:
            with self.subTest(pattern=name):
                self.assertIn(name, flags(bad), f"{name} no longer catches its own example")

    def test_each_pattern_leaves_the_clean_rewrite_alone(self):
        for name, _, good in CASES:
            with self.subTest(pattern=name):
                self.assertNotIn(name, flags(good), f"{name} fires on an acceptable rewrite")

    def test_em_dash_density(self):
        self.assertIn("em-dash-pile", flags(EM_DASH_BAD))
        self.assertNotIn("em-dash-pile", flags(EM_DASH_OK))

    def test_permission_may_is_not_a_hedge(self):
        """A rule's "may" means permitted, not hedged. Conflating them turned a
        real regulatory sentence into a false positive."""
        rule = ("An emergency engine may run at most 100 hours per year, of which at most 50 "
                "hours may be non-emergency, and those hours may not be used for peak shaving.")
        self.assertNotIn("hedge-stack", flags(rule))

    def test_quoted_source_wording_is_scrubbed_before_matching(self):
        """A regulator's own term inside authored prose is not our register drift."""
        quoting = "The gate requires 'waste-heat utilisation' of at least five per cent."
        self.assertNotIn("register-drift", flags(quoting))

    def test_app_js_strings_keep_their_literal_unicode(self):
        """app.js mixes literal UTF-8 with \\uXXXX escapes. Decoding the whole
        string via unicode_escape round-trips through latin-1 and mangles the
        literal half — "100°C–200°C" became "100Â°Câ\x80\x9320…", which silently
        broke the em-dash count for every string this collector returns."""
        self.assertEqual(cl.unescape_js(r"a \u2014 b"), "a — b")
        self.assertEqual(cl.unescape_js("100°C–200°C"), "100°C–200°C")
        collected = [t for _, t in cl.app_js_strings()]
        self.assertTrue(collected, "no app.js display strings collected")
        for t in collected:
            self.assertNotIn("Â", t, f"mojibake in collected app.js string: {t[:60]}")
            self.assertNotIn("â\x80", t, f"mojibake in collected app.js string: {t[:60]}")

    def test_allow_entries_carry_a_reason(self):
        for frag, reason in cl.ALLOW.items():
            self.assertTrue(reason and len(reason) > 15,
                            f"ALLOW entry {frag!r} needs a real reason, not {reason!r}")


class SiteCopyIsClean(unittest.TestCase):
    def test_no_findings(self):
        r = subprocess.run([sys.executable, "tools/check_language.py"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_it_actually_scanned_something(self):
        """A collector that silently returns nothing would also exit 0."""
        self.assertGreater(len(cl.app_js_strings()), 3, "app.js display strings not collected")
        scanned = [t for _, t in cl.display_strings_all() if len(t) >= cl.MIN_LEN]
        self.assertGreater(len(scanned), 500, "suspiciously few authored strings scanned")


if __name__ == "__main__":
    unittest.main()
