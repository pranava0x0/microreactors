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
    for p in costs["incentives"]["points"]:
        need(p, "costs:incentives")

    sectors = json.loads((DATA / "sectors.json").read_text())
    uncited = set(sectors["_meta"].get("uncited", []))
    for s in sectors["sectors"]:
        for l in s["loads"]:
            key = "sectors.json:uncited" if l["label"] in uncited else ""
            need(l, f"sectors:{l['label'][:40]}", key)
        for c in [s.get("context")] if s.get("context") else []:
            need(c, f"sectors:{s['sector']}:context")

    mech = json.loads((DATA / "mechanisms.json").read_text())
    for g in mech["precedent_groups"]:
        for p in g["items"]:
            need(p, f"mechanisms:{p['name'][:40]}")

    policy = json.loads((DATA / "policy.json").read_text())
    for g in policy["groups"]:
        for pw in g["pathways"]:
            key = "policy.json:idea" if pw.get("kind") == "idea" else ""
            need(pw, f"policy:{pw['name'][:40]}", key)

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
