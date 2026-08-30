#!/usr/bin/env python3
"""Promote a validated research pass into the site's curated datasets.

Research files under data/research/<pass>/ are raw agent output. This turns them
into the two hand-editable datasets the site renders:

  data/instruments.json  <- every Type A `mechanism` record, grouped by policy group
  data/benchmarks.json   <- every Type B `case` record, grouped by sector

Nothing is invented here: the pass has already been gated by research_pass.py, so
this only regroups, sorts and stamps provenance. Re-running is safe and produces
byte-identical output for identical input.

Records are ordered so the ones carrying the most evidence come first — a
mechanism with real precedents, or a case with a filing and a price, outranks one
with neither. That ordering is what the page's reading order inherits.

A pass accumulates: every subsequent call takes ALL the pass directories that
should be merged, not just the newest one — the output is rebuilt from scratch
each time, so a call naming only the new pass would silently drop every sector
an earlier pass had already contributed.

Usage:
  python3 tools/merge_research.py data/research/deep-2026-08-24
  python3 tools/merge_research.py data/research/deep-2026-08-24 data/research/apps-2026-08-28
  python3 tools/merge_research.py data/research/deep-2026-08-24 data/research/apps-2026-08-28 --check

Stdlib only, like every tool in this repo.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GROUP_ORDER = ["diesel", "batteries", "interconnection", "licensing"]
SECTOR_ORDER = [
    "Remote outposts & microgrids",
    "Off-grid mining & mineral processing",
    "Marine terminals",
    "Medical campuses",
    "Critical civic infrastructure",
    # Added 2026-08-28 (data/research/apps-2026-08-28): named to match the
    # Applications tab's own sector names (data/sectors.json) exactly.
    "Compute",
    "Manufacturing",
    "Agriculture & Food",
]


def evidence_rank(rec: dict, kind: str) -> tuple:
    """Sort key: richer evidence first, then alphabetical for stability."""
    fetched = sum(1 for s in rec.get("sources") or [] if s.get("status") == "fetched")
    if kind == "mechanism":
        depth = len(rec.get("precedents") or [])
        extra = 1 if rec.get("microreactor_edge") else 0
    else:
        depth = len(rec.get("filings") or [])
        extra = sum(1 for k in ("price", "capex", "displaced") if rec.get(k))
    return (-depth, -extra, -fetched, rec.get("name", ""))


def collect(pass_dirs: list):
    mechanisms, cases, provenance = [], [], []
    for pass_dir in pass_dirs:
        for path in sorted(pass_dir.glob("*.json")):
            doc = json.loads(path.read_text())
            meta = doc.get("_meta") or {}
            recs = doc.get("mechanisms") or doc.get("cases") or []
            if not recs:
                continue
            kind = "mechanism" if "mechanisms" in doc else "case"
            # Namespaced by pass so two passes can each hold a file with the
            # same basename without one's provenance entry shadowing the other's.
            from_tag = f"{pass_dir.name}/{path.name}"
            for r in recs:
                r = dict(r)
                r["_from"] = from_tag
                (mechanisms if kind == "mechanism" else cases).append(r)
            provenance.append({
                "file": from_tag, "kind": kind, "records": len(recs),
                "scope": meta.get("scope", ""),
                "incomplete": bool(meta.get("incomplete")),
                "absences": meta.get("absences") or [],
            })
    return mechanisms, cases, provenance


def bucket(records: list, key: str, order: list, kind: str) -> list:
    seen = {}
    for r in records:
        seen.setdefault(r.get(key), []).append(r)
    out = []
    for name in order + [k for k in sorted(seen) if k not in order]:
        if name not in seen:
            continue
        out.append({key: name,
                    "records": sorted(seen[name], key=lambda r: evidence_rank(r, kind))})
    return out


ISO_IN_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})")


def capture_date(dir_name: str) -> str:
    """The ISO date inside a pass directory name, wherever it sits.

    Pass folders are named either `<slug>-<date>` (deep-2026-08-24) or, when
    scaffolded by research_pass.py init, `<date>-<slug>` (2026-08-25-my-pass).
    Splitting on the first hyphen handled only the first shape and turned the
    second into "08-25-my-pass", which then sorted below every real ISO date and
    silently froze the site's build stamp.
    """
    m = ISO_IN_NAME.search(dir_name)
    if not m:
        raise SystemExit(f"pass directory {dir_name!r} carries no ISO date in its name")
    return m.group(1)


def build(pass_dirs: list) -> dict:
    mechanisms, cases, provenance = collect(pass_dirs)
    captured = max(capture_date(d.name) for d in pass_dirs)
    common = {
        "captured": captured,
        "pass": [f"data/research/{d.name}" for d in pass_dirs],
        "generated_by": "tools/merge_research.py",
        "provenance": provenance,
    }
    instruments = {
        "_meta": dict(common, purpose=(
            "How a deal to displace diesel, pair with storage or interconnect actually gets "
            "signed: the instrument, who has signed one outside nuclear, what changes when the "
            "asset is a reactor of any size, and what a 1-20 MW factory-built unit changes on "
            "top of that. Precedents are non-nuclear by design except in mech-nuclear-"
            "structures.json, where the inversion is the point.")),
        "groups": bucket(mechanisms, "group", GROUP_ORDER, "mechanism"),
    }
    benchmarks = {
        "_meta": dict(common, purpose=(
            "The price a reactor has to beat, taken from deals that were actually signed. Each "
            "row is a real contract, award or rate order with a number attached and, where one "
            "exists, the filing that proves it.")),
        "sectors": bucket(cases, "sector", SECTOR_ORDER, "case"),
    }
    return {"data/instruments.json": instruments, "data/benchmarks.json": benchmarks}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pass_dirs", type=pathlib.Path, nargs="+")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the committed files differ from what this would write")
    a = ap.parse_args()
    pass_dirs = [p if p.is_absolute() else ROOT / p for p in a.pass_dirs]
    for pass_dir in pass_dirs:
        if not pass_dir.is_dir():
            print(f"no such pass directory: {pass_dir}", file=sys.stderr)
            return 1

    rerun = " ".join(str(p) for p in a.pass_dirs)
    drift = 0
    for rel, doc in build(pass_dirs).items():
        text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
        target = ROOT / rel
        n = sum(len(g["records"]) for g in (doc.get("groups") or doc.get("sectors")))
        if a.check:
            current = target.read_text() if target.exists() else ""
            if current != text:
                print(f"DRIFT {rel} — re-run tools/merge_research.py {rerun}")
                drift = 1
            else:
                print(f"ok    {rel} ({n} records)")
        else:
            target.write_text(text)
            print(f"wrote {rel} ({n} records)")
    return drift


if __name__ == "__main__":
    sys.exit(main())
