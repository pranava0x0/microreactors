#!/usr/bin/env python3
"""Build data/dockets.json from the 2026-09-26 filings pass (re-runnable).

Keeps each docket record's facts, numbers and sources as the agent wrote them;
only removes repeated URLs and the agent's " -- " dashes, and orders the rows
newest first. The one derived sentence in _meta is counted, not typed.
"""
import collections
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "data" / "dockets.json"


def clean(t):
    return t.replace(" -- ", ", ").replace(" — ", ", ") if isinstance(t, str) else t


def main() -> None:
    rows = list(json.loads((HERE / "filings.json").read_text())["dockets"])
    follow = HERE.parent / "2026-09-28-alaska-greenland-pricing" / "filings-contracts.json"
    if follow.exists():
        rows.extend(json.loads(follow.read_text()).get("dockets", []))
    out_rows = []
    for r in rows:
        rec = {k: clean(v) for k, v in r.items() if k != "sources"}
        seen, srcs = set(), []
        for s in r.get("sources", []):
            if s["url"] not in seen:
                seen.add(s["url"])
                srcs.append(s)
        rec["sources"] = srcs
        out_rows.append(rec)
    by_id = {r["id"]: r for r in out_rows}
    assert len(by_id) == len(out_rows), "duplicate docket ids across research passes"
    out_rows = sorted(by_id.values(), key=lambda x: str(x.get("date", "")), reverse=True)
    size = collections.Counter(r.get("size_class", "unspecified") for r in out_rows)
    micro = size.get("micro", 0)
    out = {
        "_meta": {
            "captured": "2026-09-28",
            "what_this_is": (f"{len(out_rows)} utility plans, dockets and state laws that name advanced "
                             f"reactors. {micro} of them {'names' if micro == 1 else 'name'} a reactor of 1-20 MW; "
                             f"{size.get('small', 0)} model small modular reactors of 100-600 MW, and the "
                             f"rest name nuclear without a size. None of the nine Janus or ANPI host "
                             f"bases has a utility commission filing yet."),
            "method": ("The 2026-09-26 filings pass plus the 2026-09-28 contract-approval follow-up, "
                       "searched against commissions' own dockets, minutes and testimony; integrated "
                       "by data/research/2026-09-26-refresh/integrate_dockets.py."),
        },
        "dockets": out_rows,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out_rows)} dockets, sizes {dict(size)}")


if __name__ == "__main__":
    main()
