#!/usr/bin/env python3
"""Copy a research pass's Type C answers onto the prospects they answer.

data/strategy.json is hand-curated, but the `findings` list under each prospect
or segment is not: it is generated from the `answers` records in the pass
folders named here, so a finding on the site always traces to a validated pass
record and never to an edit nobody can audit. Re-running is idempotent; a target
with no answers loses its `findings` key rather than keeping a stale one.

  python3 tools/merge_answers.py data/research/2026-09-02-prospects
  python3 tools/merge_answers.py data/research/2026-09-02-prospects --check   # exit 1 on drift

What is copied: id, the pass's capture date, status, the question, the finding,
the figures, the angles searched (for an absent), and the sources. What is not:
`for`, which becomes the parent. Hand-curated fields on the prospect (status,
next_question, documented) are left alone; updating them after reading a finding
is the integrator's judgement, made in the main session.

Stdlib only, like every tool in this repo.
"""
import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRATEGY = ROOT / "data" / "strategy.json"
COPY = ("status", "question", "finding", "figures", "searched", "sources")


def collect(pass_dirs: List[pathlib.Path]) -> Dict[str, List[Dict[str, Any]]]:
    by_target: Dict[str, List[Dict[str, Any]]] = {}
    for d in pass_dirs:
        for path in sorted(d.glob("*.json")):
            if path.name == "plan.json":
                continue
            doc = json.loads(path.read_text())
            if "answers" not in doc:
                continue
            captured = (doc.get("_meta") or {}).get("captured", "")
            for a in doc["answers"]:
                row = {"id": a["id"], "date": captured, "pass": f"data/research/{d.name}"}
                for k in COPY:
                    if a.get(k) not in (None, "", [], {}):
                        row[k] = a[k]
                by_target.setdefault(a["for"], []).append(row)
    for rows in by_target.values():
        rows.sort(key=lambda r: r["id"])
    return by_target


def with_findings(rec: Dict[str, Any], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rebuild the record so `findings` sits after `next_question` (prospects) or
    `first_deal` (segments) and before `refs`/`benchmark_ids`, in a stable order."""
    out: Dict[str, Any] = {}
    placed = False
    for k, v in rec.items():
        if k == "findings":
            continue
        if k in ("refs", "benchmark_ids") and findings and not placed:
            out["findings"] = findings
            placed = True
        out[k] = v
    if findings and not placed:
        out["findings"] = findings
    return out


def build(pass_dirs: List[pathlib.Path]) -> str:
    doc = json.loads(STRATEGY.read_text())
    answers = collect(pass_dirs)
    for key in ("prospects", "segments"):
        doc[key] = [with_findings(r, answers.get(r["id"], [])) for r in doc[key]]
    known = {r["id"] for key in ("prospects", "segments") for r in doc[key]}
    stray = sorted(set(answers) - known)
    if stray:
        print(f"answers name targets that do not exist in strategy.json: {stray}", file=sys.stderr)
        sys.exit(1)
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pass_dirs", type=pathlib.Path, nargs="+")
    ap.add_argument("--check", action="store_true", help="exit 1 if strategy.json would change")
    a = ap.parse_args()
    dirs = [p if p.is_absolute() else ROOT / p for p in a.pass_dirs]
    for d in dirs:
        if not d.is_dir():
            print(f"no such pass directory: {d}", file=sys.stderr)
            return 1
    text = build(dirs)
    n = sum(len(v) for v in collect(dirs).values())
    if a.check:
        if text != STRATEGY.read_text():
            print("data/strategy.json findings drift from the pass — run: python3 tools/merge_answers.py "
                  + " ".join(str(p) for p in a.pass_dirs))
            return 1
        print(f"strategy.json findings in sync ({n} answers)")
        return 0
    STRATEGY.write_text(text)
    print(f"wrote data/strategy.json with {n} findings from {len(dirs)} pass dir(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
