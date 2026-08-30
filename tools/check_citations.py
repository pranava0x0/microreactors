#!/usr/bin/env python3
"""Claim-coverage scanner: every record whose prose carries a hard number must
carry a source, be registered uncited, or sit on the explicit allowlist below.

This codifies what the research passes verified by hand, so future edits are
checked for free: add a number without a source and this fails. Run directly
(python3 tools/check_citations.py) or via the test suite, which imports it.
"""
import json
import pathlib
import re
import sys
from typing import Any, Dict, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# A "hard number": money, quantities with units, percentages, or years.
NUMBER_RE = re.compile(
    r"(\$\s?\d|\d+(\.\d+)?\s?(MWe|MWt|MWh|MW|GWh|GW|kWe|kWh|kW|TWh)\b"
    r"|\d+(\.\d+)?\s?%|\b(19|20)\d{2}\b|\d+\s?(acres?|tonnes?|hours?)\b|/kW\b|/MWh\b)")

# Records allowed to carry numbers without their own source, each with the
# reason. Keep this list short; every entry is a debt the page must label.
ALLOWLIST: Dict[str, str] = {
    "costs.json:reading": "narrative recap of the cited bands directly above it",
    "mechanisms.json:intro": "labelled proposal; numbers restate cited precedents below",
    "mechanisms.json:proposal": "labelled proposal; numbers restate cited precedents below",
    "policy.json:idea": "site's own proposals, deliberately uncited; numbers restate cited rows",
    "sectors.json:uncited": "registered in _meta.uncited and marked 'no source yet' on the page",
}


def has_source(rec: Dict[str, Any]) -> bool:
    return bool(rec.get("sources") or rec.get("source"))


def prose_of(rec: Dict[str, Any]) -> str:
    out: List[str] = []
    for k, v in rec.items():
        if k in ("sources", "source", "url", "milestones") or k.startswith("_"):
            continue
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, (int, float)) and k not in ("binding",):
            out.append(str(v))
    return " ".join(out)


def check() -> List[Tuple[str, str]]:
    """Return (where, why) violations. Empty list = fully covered."""
    violations: List[Tuple[str, str]] = []

    def need(rec: Dict[str, Any], where: str, allow_key: str = "") -> None:
        if has_source(rec):
            return
        if allow_key in ALLOWLIST:
            return
        if NUMBER_RE.search(prose_of(rec)):
            violations.append((where, "carries numbers but no source"))

    opps = json.loads((DATA / "opportunities.json").read_text())
    for o in opps["opportunities"]:
        need(o, f"opportunities:{o['id']}")

    vendors = json.loads((DATA / "vendors.json").read_text())
    for v in vendors["vendors"]:
        need(v, f"vendors:{v['id']}")
        for m in v.get("milestones", []):
            need(m, f"vendors:{v['id']}:milestone:{m['label'][:32]}")

    costs = json.loads((DATA / "costs.json").read_text())
    for r in costs["microreactor_lcoe"] + costs["displaced_alternatives"]:
        need(r, f"costs:{r.get('scenario') or r.get('alternative')}")
    inc = costs["incentives"]
    for p in inc["points"]:
        need(p, "costs:incentives")
    # The block's own summary prose (question/answer/caveat) carries numbers
    # too; it is covered by the union of its points' sources, checked as one
    # record so nothing typed there can bypass the citation contract.
    inc_sources = [s for p in inc["points"] for s in (p.get("sources") or ([p["source"]] if p.get("source") else []))]
    need({"question": inc.get("question", ""), "answer": inc.get("answer", ""),
          "caveat": inc.get("caveat", ""), "sources": inc_sources},
         "costs:incentives:summary-prose")

    # capex, learning_curve and archetypes carry the hardest numbers on the site
    # ($/kWe, the unit-1-to-unit-20 multipliers, per-archetype LCOE). They are
    # walked here explicitly because this gate hand-lists record shapes: a block
    # added to costs.json and not added here is silently uncovered, which has
    # already happened twice in this repo.
    for r in costs["capex"]["rows"]:
        # A capex row's claim is its low_kwe/high_kwe pair. Those are bare
        # integers, and NUMBER_RE only matches a digit carrying a unit or a
        # currency mark, so need() alone would pass a $14,500/kWe row that
        # cites nothing. Require the source outright.
        if not has_source(r):
            violations.append((f"costs:capex:{r['scenario'][:40]}", "capacity cost with no source"))
        need(r, f"costs:capex:{r['scenario'][:40]}")
    need({"note": costs["capex"].get("note", ""), "reading": costs["capex"].get("reading", ""),
          "sources": [s for r in costs["capex"]["rows"] for s in r.get("sources", [])]},
         "costs:capex:summary-prose")
    lc = costs["learning_curve"]
    need({"worked": lc.get("worked", ""), "floor": lc.get("floor", ""), "rates": lc.get("rates", ""),
          "formula": lc.get("formula", ""), "definitions_warning": lc.get("definitions_warning", ""),
          "classes": " ".join(c.get("detail", "") for c in lc.get("classes", [])),
          "sources": lc.get("sources", [])},
         "costs:learning_curve")
    arch = costs["archetypes"]
    arch_sources = arch.get("sources", [])
    for r in arch["rows"]:
        need(dict(r, sources=arch_sources), f"costs:archetypes:{r['archetype'][:40]}")
    need({"finding": arch.get("finding", ""), "convergence": arch.get("convergence", ""),
          "note": arch.get("note", ""), "sources": arch_sources},
         "costs:archetypes:summary-prose")

    sectors = json.loads((DATA / "sectors.json").read_text())
    uncited = set(sectors["_meta"].get("uncited", []))
    for s in sectors["sectors"]:
        for l in s["loads"]:
            key = "sectors.json:uncited" if l["label"] in uncited else ""
            need(l, f"sectors:{l['label'][:40]}", key)
        for c in [s.get("context")] if s.get("context") else []:
            need(c, f"sectors:{s['sector']}:context")

    mech = json.loads((DATA / "mechanisms.json").read_text())
    # The proposal prose is exempt by allowlist, but it must still pass through
    # need() so deleting the exemption (or adding numbers elsewhere) bites.
    need({"intro": mech.get("intro", "")}, "mechanisms:intro", "mechanisms.json:intro")
    for card in mech["proposal"]["cards"]:
        need({"title": card.get("title", ""), "paras": " ".join(card.get("paras", []))},
             f"mechanisms:proposal:{card.get('title', '')[:30]}", "mechanisms.json:proposal")
    for g in mech["precedent_groups"]:
        for p in g["items"]:
            need(p, f"mechanisms:{p['name'][:40]}")

    policy = json.loads((DATA / "policy.json").read_text())
    for g in policy["groups"]:
        for pw in g["pathways"]:
            key = "policy.json:idea" if pw.get("kind") == "idea" else ""
            need(pw, f"policy:{pw['name'][:40]}", key)

    bench = json.loads((DATA / "benchmarks.json").read_text())
    for sec in bench["sectors"]:
        for r in sec["records"]:
            need(r, f"benchmarks:{sec['sector']}:{r['name'][:40]}")

    inst = json.loads((DATA / "instruments.json").read_text())
    for g in inst["groups"]:
        for r in g["records"]:
            need(r, f"instruments:{g['group']}:{r['name'][:40]}")
            r_sources = r.get("sources") or []
            for p in r.get("precedents", []):
                idx = p.get("source_idx")
                p_sources = ([r_sources[idx]] if isinstance(idx, int) and 0 <= idx < len(r_sources)
                             else r_sources)
                need(dict(p, sources=p_sources),
                     f"instruments:{g['group']}:{r['name'][:40]}:precedent:{p.get('name', '')[:30]}")

    voices_p = DATA / "voices.json"
    if voices_p.exists():
        voices = json.loads(voices_p.read_text())
        for g in voices["groups"]:
            for q in g["voices"]:
                # A quote is a claim about who said what: it needs a source
                # whether or not it happens to contain a digit.
                if not has_source(q):
                    violations.append((f"voices:{q['id']}", "quote with no source"))
                need({"what_it_means": q.get("what_it_means", ""), "sources": q.get("sources", [])},
                     f"voices:{q['id']}:gloss")

    sites_p = DATA / "deployment_sites.json"
    if sites_p.exists():
        sites = json.loads(sites_p.read_text())
        for s in sites["sites"]:
            need(s, f"deployment_sites:{s['id']}")
        for nf in sites["_meta"].get("negative_findings", []):
            need(nf, f"deployment_sites:negative:{nf['finding'][:40]}")

    return violations


def main() -> int:
    v = check()
    if v:
        for where, why in v:
            print(f"UNCITED CLAIM  {where}: {why}")
        print(f"\n{len(v)} violation(s)")
        return 1
    print("citation coverage: every numbered claim is sourced, registered or allowlisted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
