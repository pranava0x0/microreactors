#!/usr/bin/env python3
"""Derive data/gaps.json from the datasets themselves.

Hand-kept gap lists drift silently against the data they describe (see the
'hand-kept list' lesson in CLAUDE.md). This reads opportunities.json and
vendors.json and regenerates the register, so a filled-in field disappears
from the gap list automatically.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Fields the user explicitly asked to carry for every opportunity.
REQUIRED = ["sector", "owner", "timeline", "power_mw", "land_acres", "shell", "utility_filing"]

def load(name):
    return json.loads((DATA / name).read_text())

def main():
    opps = load("opportunities.json")["opportunities"]
    vendors = load("vendors.json")["vendors"]

    field_miss = {f: [] for f in REQUIRED}
    for o in opps:
        for f in REQUIRED:
            v = o.get(f)
            if v in (None, "", "Not specified", "Not published"):
                field_miss[f].append(o["id"])

    coverage = [
        {
            "field": f,
            "have": len(opps) - len(ids),
            "total": len(opps),
            "pct": round(100 * (len(opps) - len(ids)) / len(opps)),
            "missing_ids": ids,
        }
        for f, ids in sorted(field_miss.items(), key=lambda kv: len(kv[1]), reverse=True)
    ]

    row_notes = [
        {"id": o["id"], "name": o["name"], "track": o["track"], "gaps": o.get("gaps", [])}
        for o in opps if o.get("gaps")
    ]
    vendor_notes = [
        {"id": v["id"], "name": v["name"], "gaps": v.get("gaps", [])}
        for v in vendors if v.get("gaps")
    ]

    out = {
        "_meta": {
            "generated_by": "tools/build_gaps.py",
            "note": "Regenerate after any data edit: python3 tools/build_gaps.py",
        },
        "field_coverage": coverage,
        "row_gaps": row_notes,
        "vendor_gaps": vendor_notes,
        "next_pass": [
            {
                "target": "Utility filings",
                "why": f"{len(field_miss['utility_filing'])}/{len(opps)} rows have none.",
                "where": "FERC eLibrary; state PUC dockets (CO PUC for Buckley/Xcel, MT PSC for Malmstrom/NorthWestern); San Antonio city council agendas for JBSA/CPS Energy, which is municipally owned and so files locally rather than at a PUC.",
                "why_search_failed": "Web search does not index docket systems. This needs direct docket queries, not more searching.",
            },
            {
                "target": "Land area / site footprint",
                "why": f"{len(field_miss['land_acres'])}/{len(opps)} rows have none.",
                "where": "NRC ADAMS early site permit and construction permit filings; DoD installation master plans; NEPA environmental assessments.",
                "why_search_failed": "Only Westinghouse publishes a footprint figure (2 acres), and that is a design claim rather than an allocated parcel.",
            },
            {
                "target": "Shell / enclosure detail",
                "why": f"{len(field_miss['shell'])}/{len(opps)} rows have none.",
                "where": "Vendor technical datasheets; NRC pre-application meeting slides; DOE DOME experiment safety documentation.",
                "why_search_failed": "Press coverage reports mass and transportability but not containment or enclosure design.",
            },
        ],
    }
    (DATA / "gaps.json").write_text(json.dumps(out, indent=1))
    for c in coverage:
        bar = "#" * (c["pct"] // 5)
        print(f"{c['field']:16} {c['have']:2}/{c['total']:2}  {c['pct']:3}%  {bar}")
    print(f"\nrows with notes: {len(row_notes)}   vendors with notes: {len(vendor_notes)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
