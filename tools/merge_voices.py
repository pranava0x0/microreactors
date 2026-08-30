#!/usr/bin/env python3
"""Merge the leadership/voices research pass into data/voices.json.

  python3 tools/merge_voices.py data/research/2026-08-29-voices
  python3 tools/merge_voices.py <dir> --check   # exit 1 if data/ is out of sync

Reorganizes "In their words" around WHAT IS BEING SAID rather than who is saying
it. The first version grouped by the speaker's interest - builders, buyer,
skeptics - which is the right default when there are seventeen quotes and the
wrong one at a hundred and twenty, because a reader looking for what anyone said
about fuel supply had to read all three groups.

Speaker interest survives as a per-quote field, so a reader can still see at a
glance whether a claim comes from someone selling, someone buying, or someone
arguing it does not add up.

The buyer and skeptic groups are kept whole and last: those are arguments, not
topics, and folding them into "costs" would lose the fact that they are contested.
"""
import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "voices.json"
BASE = ROOT / "data" / "voices_curated.json"

# research topic -> (group id, display name, group note)
GROUPS = [
    ("costs", "What it costs", "Every statement by an operator that touches price, capital cost "
     "or unit economics. Only a minority carry a number, which is the finding: the sector "
     "argues about cost constantly and rarely quantifies it in public."),
    ("customers", "Who is buying", "Named counterparties and what they have actually signed."),
    ("orders", "Orders and backlog", "Units, megawatts and dollar values under contract. Watch "
     "for the difference between a letter of intent and something binding."),
    ("supply-chain", "Fuel and supply chain", "Fuel is the one cost line that gets no benefit "
     "from building more reactors, so who controls it decides who can be cheap. The split "
     "between companies betting on HALEU and companies deliberately avoiding it runs through "
     "this group."),
    ("units-manufacturing", "Manufacturing and units", "What serial production means to each "
     "company, and how many units a year they claim."),
    ("regulatory", "Licensing and regulation", "Which door each company is walking through, and "
     "what that costs them in schedule."),
    ("international", "International", "Markets outside the United States, and what changes there."),
]
KEEP_LAST = ("buyer", "skeptics")


def load_pass(pass_dir: pathlib.Path) -> Dict[str, List[dict]]:
    quotes, leaders = [], []
    for f in sorted(pass_dir.glob("*.json")):
        d = json.loads(f.read_text())
        quotes.extend(d.get("quotes", []))
        leaders.extend(d.get("leaders", []))
    return {"quotes": quotes, "leaders": leaders}


def build(pass_dir: pathlib.Path) -> Dict[str, Any]:
    # read the CURATED BASE, never OUT: building from your own output means the
    # second run sees a different input than the first and --check always drifts.
    existing = json.loads(BASE.read_text())
    keep = [g for g in existing["groups"] if g["id"] in KEEP_LAST]
    # the original "builders" group predates the pass; its quotes are already in
    # the corpus by topic, so it is folded in rather than kept as a fourth axis
    legacy = [g for g in existing["groups"] if g["id"] == "builders"]
    legacy_by_topic: Dict[str, List[dict]] = {}
    for g in legacy:
        for v in g["voices"]:
            t = {"Commercial market": "customers", "Business case": "costs",
                 "Government market": "orders", "Costs": "costs"}.get(v.get("topic"), "costs")
            legacy_by_topic.setdefault(t, []).append(v)

    p = load_pass(pass_dir)
    by_topic: Dict[str, List[dict]] = {}
    for q in p["quotes"]:
        by_topic.setdefault(q.get("topic", "costs"), []).append(q)

    groups = []
    for gid, name, note in GROUPS:
        voices = []
        for v in legacy_by_topic.get(gid, []):
            voices.append(v)
        for q in sorted(by_topic.get(gid, []), key=lambda x: (x.get("company", ""), x.get("date", ""))):
            voices.append({
                "id": q["id"], "speaker": q["speaker"],
                "role": q.get("role", ""), "org": q.get("company", ""),
                "date": q.get("date", ""), "venue": q.get("venue", ""),
                "topic": name, "quote": q["quote"],
                "what_it_means": q.get("what_it_means", ""),
                "sources": q.get("sources", []),
            })
        if voices:
            groups.append({"id": gid, "name": name, "note": note, "voices": voices})
    groups.extend(keep)

    leaders = sorted(p["leaders"], key=lambda l: (l.get("company", ""), l.get("name", "")))
    meta = dict(existing["_meta"])
    meta["captured"] = "2026-08-29"
    # State the verification mix rather than claiming it is uniform. Sources marked
    # snippet-only were corroborated by search and never page-read, and the roster
    # note sits above rows carrying both kinds.
    src = [s for l in leaders for s in l.get("sources", [])]
    snip = sum(1 for s in src if s.get("status") == "snippet-only")
    meta["roster_note"] = (
        f"{len(leaders)} named executives across {len({l.get('company') for l in leaders})} "
        f"companies, each with a source. Of {len(src)} citations here, {len(src) - snip} were "
        f"checked against the page they cite and {snip} rest on search results without a direct "
        "page read - those carry a dagger. Spans that could not be found in the page they claimed "
        "were demoted or dropped.")
    return {"_meta": meta, "groups": groups, "leaders": leaders}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pass_dir", type=pathlib.Path)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    built = build(a.pass_dir)
    text = json.dumps(built, indent=2, ensure_ascii=False) + "\n"
    if a.check:
        if OUT.read_text() != text:
            print("DRIFT data/voices.json — re-run tools/merge_voices.py", file=sys.stderr)
            return 1
        print("data/voices.json matches the pass")
        return 0
    OUT.write_text(text)
    nq = sum(len(g["voices"]) for g in built["groups"])
    print(f"wrote data/voices.json — {len(built['groups'])} groups, {nq} quotes, "
          f"{len(built['leaders'])} leaders")
    for g in built["groups"]:
        print(f"    {g['name']:<28} {len(g['voices'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
