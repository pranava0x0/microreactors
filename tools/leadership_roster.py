#!/usr/bin/env python3
"""Build a roster of microreactor company leadership from company websites.

Fetches each company's own leadership page, extracts name/title pairs, and
writes data/research/leadership/roster.json. Company pages are the only source
that is authoritative about who works there and what their title is; press
coverage gets both wrong routinely.

  python3 tools/leadership_roster.py            # fetch all, write roster
  python3 tools/leadership_roster.py --dry      # report only
  python3 tools/leadership_roster.py --only antares,radiant

Two rules this tool follows, both learned in this repo:

  * It prints how many pages it actually READ, not how many it tried. A roster
    built from 3 of 12 reachable pages looks identical to a complete one unless
    the count is on screen.
  * A host that blocks automated clients is recorded as blocked, never as
    "no leadership found". Those two states are different and the difference
    is the whole point of the absences list.

What this tool is, precisely: a REACHABILITY PROBE with a candidate extractor
attached. The reachability half is exact and is the point - it tells you which
companies can be read at all and which block automated clients, which is what
decides where a human or an agent has to go instead.

The name extraction is a heuristic over sixteen different site templates and it
OVER-COLLECTS on purpose. Nav text sometimes wins the nearest-name race, so every
row keeps its raw context for triage. Do not treat `people` as a roster. An
earlier version filtered harder and looked much cleaner while silently dropping
a real CTO and a real CEO; over-collecting noise you can see beats under-
collecting people you cannot. Authoritative rosters come from the research pass
in data/research/2026-08-29-voices/, which cites a source per person.
Stdlib only, like every tool here.
"""
import argparse
import html
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "research" / "leadership"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# id -> (display name, [leadership page URLs])
COMPANIES: Dict[str, Tuple[str, List[str]]] = {
    "antares":     ("Antares Nuclear", ["https://antaresindustries.com/leadership-team"]),
    "radiant":     ("Radiant Industries", ["https://www.radiantnuclear.com/about",
                                            "https://www.radiantnuclear.com/company"]),
    "oklo":        ("Oklo", ["https://oklo.com/who-we-are/leadership/default.aspx"]),
    "lastenergy":  ("Last Energy", ["https://www.lastenergy.com/about",
                                     "https://www.lastenergy.com/company"]),
    "xenergy":     ("X-energy", ["https://x-energy.com/company", "https://x-energy.com/about"]),
    "aalo":        ("Aalo Atomics", ["https://aalo.com/team"]),
    "bwxt":        ("BWXT", ["https://www.bwxt.com/about-us/leadership"]),
    "westinghouse":("Westinghouse", ["https://www.westinghousenuclear.com/about/leadership/"]),
    "generalatomics": ("General Atomics", ["https://www.ga.com/leadership"]),
    "kairos":      ("Kairos Power", ["https://kairospower.com/company"]),
    "nano":        ("NANO Nuclear Energy", ["https://nanonuclearenergy.com/management-team/",
                                             "https://nanonuclearenergy.com/about-us/"]),
    "deepfission": ("Deep Fission", ["https://www.deepfission.com/about-us/executive-leadership",
                                      "https://ir.deepfission.com/company-info/executive-team"]),
    "valar":       ("Valar Atomics", ["https://www.valaratomics.com/"]),
    "zeno":        ("Zeno Power", ["https://www.zenopower.com/our-team"]),
    "standard":    ("Standard Nuclear", ["https://ir.standardnuclear.com/company-information/executive-team",
                                          "https://ir.standardnuclear.com/governance/board-of-directors"]),
    "terrapower":  ("TerraPower", ["https://www.terrapower.com/people/", "https://www.terrapower.com/about/"]),
}

TITLE_RE = re.compile(
    r"\b(Chief [A-Z][a-z]+(?: [A-Z][a-z]+)? Officer|CEO|CTO|COO|CFO|CNO|"
    r"Chief Executive(?: Officer)?|Chief Nuclear Officer|Chief Technology Officer|"
    r"Chief Operating Officer|Chief Financial Officer|Chief Commercial Officer|"
    r"Co-?[Ff]ounder|Founder|President|Executive Chair(?:man|woman|person)?|"
    r"Chair(?:man|woman|person)? of the Board|"
    r"(?:Senior )?Vice President(?: of [A-Z][a-z]+)?|SVP|EVP|"
    r"Head of [A-Z][A-Za-z ]{2,30}|Director of [A-Z][A-Za-z ]{2,30}|"
    r"General Counsel|Chief of Staff)\b")
NAME_RE = re.compile(r"\b((?:Dr\.\s+)?[A-Z][a-z’'\-]{1,15}(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-zA-Z’'\-]{1,20}){1,2})\b")
STOP = {"United States", "New York", "Los Angeles", "San Antonio", "Idaho National",
        "Privacy Policy", "Terms Of", "All Rights", "Learn More", "Contact Us",
        "Our Team", "Leadership Team", "The Company", "About Us", "Read More",
        "Executive Officer", "Executive Chairman", "Managing Partner", "Board Member",
        "Nuclear Engineering", "Mission Engineering", "Product Officer", "Legal Officer",
        "Financial Officer", "Technology Officer", "Operating Officer", "Commercial Officer",
        "West Point", "Ultra Safe", "Ultra Safe Nuclear", "Standard Nuclear", "Kairos Power",
        "Team Leadership", "Leadership Team Contacts", "Our Leadership", "Meet The"}
# Any word that only ever appears inside a job title. A name containing one is furniture,
# not a person: "Executive Officer Co-Founder" is a title fragment the window picked up.
TITLE_WORDS = {"officer", "chief", "president", "founder", "director", "head", "vice",
               "chairman", "chairwoman", "chair", "counsel", "leadership", "team",
               "board", "engineering", "operations", "staff", "partner", "manager"}


def strip_html(raw: bytes) -> str:
    t = raw.decode("utf-8", errors="replace")
    t = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>|</(p|div|li|h[1-6])>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t))


class _Redirect308(urllib.request.HTTPRedirectHandler):
    """urllib does not follow 308 before Python 3.11, so a moved page reports as
    an error rather than a redirect. Three companies in the registry moved their
    leadership pages behind a 308."""

    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_301(req, fp, 301, msg, headers)


_OPENER = urllib.request.build_opener(_Redirect308)


def fetch(url: str, timeout: int = 25) -> Tuple[Optional[bytes], str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/html,application/xhtml+xml"})
    try:
        with _OPENER.open(req, timeout=timeout) as r:
            return r.read(), ""
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 - surface the reason, never swallow
        return None, type(e).__name__


def people(text: str) -> List[Dict[str, str]]:
    """Every title hit, with the nearest person-shaped name and its context."""
    out: List[Dict[str, str]] = []
    seen = set()
    for m in TITLE_RE.finditer(text):
        lo, hi = max(0, m.start() - 130), min(len(text), m.end() + 130)
        window = text[lo:hi]
        best = ""
        # prefer a name immediately before the title, else the nearest after
        before = NAME_RE.findall(text[lo:m.start()])
        after = NAME_RE.findall(text[m.end():hi])
        for cand in list(reversed(before)) + after:
            c = " ".join(cand.split())
            if c in STOP or not 2 <= len(c.split()) <= 3:
                continue
            if TITLE_RE.search(c):
                continue
            if any(w.strip(".,").lower() in TITLE_WORDS for w in c.split()):
                continue
            best = c
            break
        key = (best, m.group(0))
        if not best or key in seen:
            continue
        seen.add(key)
        out.append({"name": best, "title": m.group(0),
                    "context": re.sub(r"\s+", " ", window).strip()[:240]})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    ids = [x.strip() for x in a.only.split(",") if x.strip()] or list(COMPANIES)
    unknown = [i for i in ids if i not in COMPANIES]
    if unknown:
        print(f"unknown company id(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    roster: Dict[str, dict] = {}
    pages_read = pages_tried = 0
    for cid in ids:
        name, urls = COMPANIES[cid]
        rec = {"company": name, "people": [], "pages_read": [], "blocked": []}
        for url in urls:
            pages_tried += 1
            raw, err = fetch(url)
            if raw is None:
                rec["blocked"].append({"url": url, "reason": err})
                continue
            pages_read += 1
            rec["pages_read"].append(url)
            txt = strip_html(raw)
            for p in people(txt):
                if not any(q["name"] == p["name"] and q["title"] == p["title"]
                           for q in rec["people"]):
                    p["source"] = url
                    rec["people"].append(p)
        roster[cid] = rec
        flag = "" if rec["people"] else ("  <- BLOCKED" if rec["blocked"] and not rec["pages_read"]
                                         else "  <- reachable but no titles matched")
        print(f"  {name:<22} {len(rec['people']):>3} people   "
              f"{len(rec['pages_read'])}/{len(urls)} pages{flag}")

    print(f"\nread {pages_read} of {pages_tried} pages across {len(ids)} companies")
    named = sum(len(r["people"]) for r in roster.values())
    blocked = [ (r['company'], b['url'], b['reason'])
                for r in roster.values() for b in r["blocked"] ]
    print(f"{named} name/title pairs · {len(blocked)} page(s) blocked")
    for c, u, why in blocked:
        print(f"    blocked {why:<9} {c}: {u}")

    if not a.dry:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / "roster.json"
        payload = {"_meta": {"captured": "2026-08-29",
                             "tool": "tools/leadership_roster.py",
                             "pages_read": pages_read, "pages_tried": pages_tried,
                             "caveat": "Extraction is heuristic and over-collects. "
                                       "Every row keeps its context so noise is visible."},
                   "companies": roster}
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
