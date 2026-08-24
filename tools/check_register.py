#!/usr/bin/env python3
"""Structural AI-register lint over display copy.

The word list in tests/test_data.py catches single words (delve, unlock). It
cannot catch a *shape*, and shapes are what a generated headline defaults to.
This checks the two that clustered hardest on this site before the 2026-08-23
sweep, both on short strings only, because both are headline constructions:

  comma-tail    "Published cost bands, sourced" — a phrase with an adverb or
                participle stapled on after a comma (also "..., stated
                carefully", "..., precisely stated", "..., honestly stated").
  colon-setup   "The gap: no battery major has signed a nuclear pairing" — a
                label, a colon, then the sentence that was the actual point.
                Ten of thirty-two policy names ran this template.

Scope differs per pattern, because their false positives do. comma-tail is
checked on every short display string (it produced no false positive across
741 of them). colon-setup is checked only on strings sitting under a heading
key, since "Equinix 20-unit deal: no per-unit price published" is a fine note
and a bad headline. Heading keys are matched by key NAME, not by a list of
paths, so a new heading field is covered the day it is added as long as it is
called one of the usual things. Anything legitimately matching goes in ALLOW
with a reason, the same convention tools/check_citations.py uses.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, SITE = ROOT / "data", ROOT / "site"
FILES = ["opportunities", "vendors", "costs", "sectors", "mechanisms", "policy", "gaps"]

HEAD_MAX = 80

# Source metadata is external text: titles and verbatim quotes are not ours to
# rewrite, and _meta is internal notes the site never renders. Source labels are
# covered by skipping the "sources"/"source" containers, so "label" itself stays
# in scope for load and milestone labels, which are ours.
SKIP_KEYS = {"sources", "source", "url", "quote", "_meta"}

# Keys whose values render as a heading, a card title or a row name. "label"
# is deliberately absent: it is shared with vendor timeline milestones, where
# "ANPI goal: at least one reactor operating on a base" is the natural form and
# not a headline reveal. The cost of that exemption is that load labels go
# colon-unchecked; they are descriptive noun phrases and none has ever taken
# the shape.
HEADING_KEYS = {"name", "title", "scenario", "alternative", "sector", "target"}

COMMA_TAIL = re.compile(
    r",\s+(?:\w+ly\s+)?"
    r"(?:stated|sourced|said|put|noted|explained|argued|framed|quantified|"
    r"industrialized|detailed|precisely|honestly|carefully|plainly|briefly|"
    r"in detail|in brief)\s*[.!]?$", re.I)
COLON_SETUP = re.compile(r"^[^:]{4,60}:\s+\S")

ALLOW = {
    # A statute or docket number followed by its plain-English gloss is a
    # citation convention, not a headline reveal.
    "10 U.S.C. 2920": "statute number plus gloss",
}


def strings(node, out, key=""):
    """Collect (key, string) so a check can ask what kind of slot it filled."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k not in SKIP_KEYS:
                strings(v, out, k)
    elif isinstance(node, list):
        for v in node:
            strings(v, out, key)
    elif isinstance(node, str):
        out.append((key, node))


def display_strings():
    out = []
    for name in FILES:
        strings(json.loads((DATA / f"{name}.json").read_text()), out)
    html = (SITE / "index.html").read_text()
    for tag in ("h1", "h2", "h3"):
        out += [("name", re.sub(r"<[^>]+>", "", x).strip())
                for x in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.S)]
    out += [("name", re.sub(r"<[^>]+>", "", x).strip())
            for x in re.findall(r'<p class="eyebrow">(.*?)</p>', html, re.S)]
    return [(k, s) for k, s in out if s]


def check():
    found = []
    for key, s in display_strings():
        if len(s) > HEAD_MAX or any(a in s for a in ALLOW):
            continue
        if COMMA_TAIL.search(s):
            found.append(("comma-tail", s))
        elif key in HEADING_KEYS and COLON_SETUP.match(s):
            found.append(("colon-setup", s))
    return found


def main() -> int:
    all_strings = display_strings()
    heads = [s for k, s in all_strings if k in HEADING_KEYS]
    if len(all_strings) < 200 or len(heads) < 50:
        print(f"extraction found {len(all_strings)} strings / {len(heads)} headings "
              "— stale?", file=sys.stderr)
        return 2
    found = check()
    for kind, s in found:
        print(f"{kind}: {s}", file=sys.stderr)
    print(f"{len(all_strings)} display strings scanned, {len(heads)} under a heading key, "
          f"{len(found)} register hits")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
