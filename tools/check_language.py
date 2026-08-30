#!/usr/bin/env python3
"""Plain-language lint over the site's authored copy.

Three gates now look at display copy and they divide the work cleanly:

  tests/test_data.py     single banned WORDS (delve, unlock, tapestry)
  tools/check_register.py headline SHAPES (comma-tail, colon-setup)
  this                   plain-language MOVES, per DESIGN.md 11.2

The moves here all shipped on this site, read fine sentence by sentence, and
made the page colder to read. They are the ones a word list cannot catch
because each is a habit rather than a term:

  ui-narration    prose describing the interface instead of using it —
                  "each card carries a cited roadmap", "every figure links to
                  its source", "they carry no citation". The chips and the
                  register already say this, visibly, on every row.
  meta-commentary a sentence about the previous sentence — "and that
                  disagreement is the useful part", "which is what matters".
  throat-clearing an opener that delays the point — "It is worth noting that".
  register-drift  formal or British forms in copy read on a phone —
                  "realised", "utilise", "whilst", "in order to".
  hedge-stack     three or more qualifiers in one sentence; one is honest,
                  three is a shrug.
  em-dash-pile    more than two em dashes in a paragraph, where the prose
                  turns into an aside about an aside.

Scope. It reuses check_register's collectors, so it sees the same data files
(derived from the builder's registry) and the same markup, and it inherits the
same exclusions: source labels, URLs, verbatim quotes and _meta notes are
external or internal text, not ours to rewrite. It additionally reads the
display strings hard-coded in site/assets/app.js, which no other gate walks —
that omission is exactly how three dangling citations lived there unnoticed.

Anything that legitimately matches goes in ALLOW with a reason, the same
convention check_citations.py and check_register.py use.

  python3 tools/check_language.py           # exit 1 on any finding
  python3 tools/check_language.py --verbose # show every string scanned
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_register as cr  # collectors, exclusions and FILES live there

APP_JS = ROOT / "site" / "assets" / "app.js"

# Quoted regulatory language is the source's wording, not ours. These appear
# inside authored prose describing a rule, so the whole string cannot be
# skipped by key the way a "quote" field is.
QUOTED_TERM = re.compile(r"[\"“'‘]([^\"”'’]{3,60})[\"”'’]")

PATTERNS = {
    "ui-narration": re.compile(
        r"\b(?:carr(?:y|ies|ying)\s+(?:a\s+)?cit\w*"
        r"|links?\s+to\s+its\s+source"
        r"|carry\s+no\s+citation"
        r"|proven\s+by\s+a\s+contract"
        r"|each\s+(?:card|row|entry)\s+carries"
        r"|every\s+figure\s+links)", re.I),
    "meta-commentary": re.compile(
        r"\b(?:is\s+the\s+useful\s+part"
        r"|is\s+what\s+matters"
        r"|that\s+is\s+worth\s+knowing"
        r"|which\s+is\s+the\s+point"
        r"|the\s+useful\s+thing\s+here)", re.I),
    "throat-clearing": re.compile(
        r"^\s*(?:It(?:'|’)?s?\s+worth\s+noting"
        r"|It\s+is\s+worth\s+noting"
        r"|Importantly[,\s]"
        r"|Crucially[,\s]"
        r"|Notably[,\s]"
        r"|Needless\s+to\s+say)", re.I),
    "register-drift": re.compile(
        r"\b(?:realis(?:e|ed|es|ing|ation)"
        r"|utilis(?:e|ed|es|ing|ation)"
        r"|whilst|amongst|endeavour(?:s|ed|ing)?"
        r"|in\s+order\s+to|prior\s+to\s+the)\b", re.I),
    # Deliberately excludes may/might/could: in a rule they mean "permitted",
    # not "hedged", and treating them as hedges turned a regulatory sentence
    # into a false positive. Counted as DISTINCT words in one sentence, so the
    # same qualifier repeated is not a stack.
    "hedge-stack": None,
}
# Em dashes are counted, not matched, because the tell is density.
EM_DASH_MAX = 2

HEDGES = ("perhaps", "arguably", "roughly", "somewhat", "relatively", "generally",
          "typically", "often", "possibly", "potentially", "seemingly", "broadly",
          "largely", "fairly", "quite")
HEDGE_MIN = 3


def hedge_stack(text: str) -> str:
    """Three or more DISTINCT hedges inside one sentence."""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        found = {h for h in HEDGES if re.search(rf"\b{h}\b", sentence, re.I)}
        if len(found) >= HEDGE_MIN:
            return ", ".join(sorted(found))
    return ""
# Below this length a string is a label, where none of these moves applies.
MIN_LEN = 45

ALLOW = {
    # Reason required for every entry.
    "waste-heat utilisation": ("CPUC's own term of art in P.U. Code 216.6(a); "
                               "rewriting it would misquote the eligibility rule"),
    "Electrical Efficiency E/F_HHV": "verbatim SGIP handbook formula",
    "Endeavour": ("legal entity name as filed - Deep Fission's Form 10-K names "
                  "'Endeavour Energy, LLC'; the -our spelling is the counterparty's "
                  "own, not our register drifting"),
}


def allowed(text: str) -> str:
    for frag, reason in ALLOW.items():
        if frag.lower() in text.lower():
            return reason
    return ""


def unescape_js(raw: str) -> str:
    """Resolve \\uXXXX escapes without touching literal UTF-8.

    The obvious `raw.encode().decode("unicode_escape")` round-trips through
    latin-1 and mangles any character already written literally in the source:
    "100°C–200°C" came back as "100Â°Câ\x80\x9320…", which silently broke the
    em-dash count for every app.js string.
    """
    out = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), raw)
    return out.replace('\\"', '"').replace("\\\\", "\\")


def app_js_strings():
    """Display copy hard-coded in app.js: the object literals that carry card
    prose. Only fields that reach the page, never selectors or class names."""
    src = APP_JS.read_text()
    out = []
    for key in ("title", "incumbent", "why", "edge", "label", "k"):
        for m in re.finditer(rf'\b{key}:\s*"((?:[^"\\]|\\.){{{MIN_LEN},}})"', src):
            out.append((key, unescape_js(m.group(1))))
    return out


def display_strings_all():
    """Every authored string this gate looks at: the data files and markup that
    check_register already walks, plus the display copy hard-coded in app.js."""
    return cr.display_strings() + app_js_strings()


def findings():
    out = []
    for key, text in display_strings_all():
        if len(text) < MIN_LEN:
            continue
        why = allowed(text)
        if why:
            continue
        # Strip quoted source wording before matching: a rule that says
        # "waste-heat utilisation" is the regulator's phrasing, not ours.
        scrubbed = QUOTED_TERM.sub(" ", text)
        for name, rx in PATTERNS.items():
            if rx is None:
                continue
            m = rx.search(scrubbed)
            if m:
                out.append((name, key, m.group(0).strip(), text))
        stacked = hedge_stack(scrubbed)
        if stacked:
            out.append(("hedge-stack", key, stacked, text))
        if text.count("—") > EM_DASH_MAX:
            out.append(("em-dash-pile", key, f"{text.count('—')} em dashes", text))
    # A markup string also appears inside every ancestor's joined text, so one
    # bad sentence would otherwise be reported once per level of nesting.
    # Report the most specific string carrying each finding: the shortest one,
    # since the ancestors are the same sentence plus surrounding page furniture.
    best = {}
    for name, key, tok, text in out:
        sig = (name, tok) if key == "markup" else (name, tok, text[:120])
        if sig not in best or len(text) < len(best[sig][3]):
            best[sig] = (name, key, tok, text)
    return list(best.values())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    scanned = [t for _, t in display_strings_all() if len(t) >= MIN_LEN]
    hits = findings()
    for name, key, tok, text in hits:
        print(f"{name}: <{tok}>\n    [{key}] {text[:150]}")
    if a.verbose:
        for t in scanned:
            print("  scanned:", t[:110])
    print(f"\n{len(scanned)} authored strings scanned, {len(hits)} finding(s), "
          f"{len(ALLOW)} allowed")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
