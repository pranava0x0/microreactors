#!/usr/bin/env python3
"""Build data/segments.json (Applications > Space and more) from verified-apps.json (re-runnable).

verified-apps.json holds Type S records drafted by a haiku agent and rewritten against
fetched pages by a Sonnet agent. Facts, numbers and sources are kept as written; this
adds only the group, which is curated here per record.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "data" / "segments.json"

GROUPS = [
    {"id": "space", "label": "Space and launch"},
    {"id": "heat", "label": "Heat, water and industry"},
    {"id": "ports-sites", "label": "Ports, broadcast and Arctic outposts"},
    {"id": "campuses", "label": "Universities"},
]
GROUP_OF = {
    "nasa-doe-fsp-lunar": "space", "westinghouse-evinci-lunar": "space",
    "draco-nuclear-thermal": "space", "jetson-intuitive-machines": "space",
    "starbase-spaceport": "space",
    "steady-energy-ldr50": "heat", "inl-marvel-desalination": "heat",
    "microreactor-ammonia-hydrogen": "heat", "microreactor-cement-calciner": "heat",
    "last-energy-london-gateway": "ports-sites", "terra-innovatum-waiken-broadcast": "ports-sites",
    "arctic-microreactor-canada": "ports-sites",
    "uiuc-kronos-mmr": "campuses", "penn-state-evinci": "campuses", "tamu-rellis-aalo": "campuses",
}
# Wording fixes made after the verifier pass (the page says 85 kWt or 20 kWe, a block of 1-20 MW is 12 to 1,000 times larger).
REPLACE = {"inl-marvel-desalination": [("MARVEL is about 100 times smaller than a 1-20 MW block",
                                        "MARVEL is one to two orders of magnitude smaller than a 1-20 MW block")]}
KEEP = ("id", "segment", "name", "status", "power_class", "timeline", "sponsor", "vendor",
        "what_it_says", "microreactor_read", "sources")


def clean(t):
    return t.replace(" -- ", ", ").replace(" — ", ", ") if isinstance(t, str) else t


def main() -> None:
    src = json.loads((HERE / "verified-apps.json").read_text())
    rows, missing = [], []
    for r in src["applications"]:
        if r["id"] not in GROUP_OF:
            missing.append(r["id"])
            continue
        rec = {k: clean(r[k]) for k in KEEP if r.get(k)}
        for old, new in REPLACE.get(r["id"], []):
            rec["microreactor_read"] = rec["microreactor_read"].replace(old, new)
        rec["group"] = GROUP_OF[r["id"]]
        rows.append(rec)
    if missing:
        raise SystemExit(f"no group for: {missing}")
    order = [g["id"] for g in GROUPS]
    rows.sort(key=lambda r: (order.index(r["group"]), r["id"]))
    indexed = {s["url"] for s in json.loads((ROOT / "data" / "research" / "source_index.json").read_text())["sources"]}
    urls = {s["url"] for r in rows for s in r["sources"]}
    fetched, total = len(urls & indexed), len(urls)
    out = {"_meta": {
        "captured": "2026-10-08",
        "what_this_is": f"{len(rows)} named projects and buyers outside the eight sector tabs: lunar and in-space power, a launch site, district and process heat, a port, broadcast data centres, an Arctic outpost and university research reactors.",
        "method": f"A search-seeded draft (data/research/2026-10-08-refresh/drafts/space-apps.json) rewritten against fetched pages by a second agent, then quote-checked offline. {fetched} of {total} distinct sources are cached and quote-checked offline; the rest sit on hosts that block scripts. The group is curated in that folder's integrate_segments.py.",
        "groups": GROUPS},
        "segments": rows}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} segments")


if __name__ == "__main__":
    main()
