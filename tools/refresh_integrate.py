#!/usr/bin/env python3
"""Fold a refresh pass's verified agent output into the shipped data.

  python3 tools/refresh_integrate.py data/research/2026-10-18-refresh          # dry run
  python3 tools/refresh_integrate.py data/research/2026-10-18-refresh --apply  # write

Run AFTER tools/repair_pass_quotes.py and tools/verify_pass_quotes.py, so every
source still marked `fetched` has a quote that is really on its page. This tool
only trusts `fetched` sources; `snippet-only` facts never ship on their own.

  items (Type N)      -> data/research/news/refresh-<date>.json, then run
                         tools/merge_news.py data/research/news to rebuild data/news.json.
                         Dropped: ids or source urls already on the News tab, and
                         items with no fetched source.
  checks (Type G)     -> `outdated` / `wrong` with a fetched source and a correction:
                         the claim is replaced in data/<file>.json ONLY when it occurs
                         verbatim, exactly once, inside the record with that id; the
                         check's fetched sources are appended to the record. Anything
                         else is listed under "needs a human" in REPORT.md.
  dockets (Type F)    -> appended to data/dockets.json when the id and url are new.
  applications        -> appended to data/segments.json once `group` names one of its groups.
  regions             -> listed in REPORT.md for hand curation (group, price_short, position).

Writes <pass>/REPORT.md either way (the PR body quotes it). Stdlib only.
"""
import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
NEWS_PASS = DATA / "research" / "news"


def fetched(rec: dict) -> list:
    return [s for s in rec.get("sources") or [] if isinstance(s, dict) and s.get("status") == "fetched"]


def load_pass(pass_dir: pathlib.Path) -> dict:
    out = {"items": [], "checks": [], "dockets": [], "applications": [], "regions": []}
    for f in sorted(pass_dir.glob("*.json")):
        doc = json.loads(f.read_text())
        if doc.get("_meta", {}).get("incomplete"):
            continue
        for key in out:
            for rec in doc.get(key, []):
                rec["_file"] = f.name
                out[key].append(rec)
    return out


def find_record(node, rec_id):
    """Depth-first search for the dict whose id is rec_id; returns it or None."""
    if isinstance(node, dict):
        if node.get("id") == rec_id:
            return node
        node = list(node.values())
    if isinstance(node, list):
        for child in node:
            hit = find_record(child, rec_id)
            if hit is not None:
                return hit
    return None


def resolve(doc, target: str):
    """A record id, or a key path into a nested document such as
    `displaced_alternatives[1].note` (costs.json rows carry no ids). A path ending
    on a string field resolves to the dict holding it."""
    if not re.search(r"[.\[]", target or ""):
        return find_record(doc, target)
    node, parent = doc, None
    for key, idx in re.findall(r"([^.\[\]]+)|\[(\d+)\]", target):
        parent = node
        try:
            node = node[int(idx)] if idx else node[key]
        except (KeyError, IndexError, TypeError):
            # `microreactor_lcoe.<row id>`: a list step addressed by a record id
            node = find_record(node, key) if key and isinstance(node, list) else None
            if node is None:
                return None
    return node if isinstance(node, dict) else parent if isinstance(parent, dict) else None


def replace_once(node, old: str, new: str) -> int:
    """Replace `old` inside string values of node (not in sources). Returns hit count;
    only mutates when exactly one string holds exactly one occurrence."""
    hits = []

    def walk(n, parent, key):
        if isinstance(n, str):
            if old in n:
                hits.append((parent, key, n.count(old)))
        elif isinstance(n, dict):
            for k, v in n.items():
                if k != "sources":
                    walk(v, n, k)
        elif isinstance(n, list):
            for i, v in enumerate(n):
                walk(v, n, i)

    walk(node, None, None)
    total = sum(c for _, _, c in hits)
    if total == 1:
        parent, key, _ = hits[0]
        parent[key] = parent[key].replace(old, new)
    return total


def dump(path: pathlib.Path, doc: dict) -> None:
    """Rewrite a data file in the layout it already has (some are indent=1, some 2),
    so an integration diff shows content, not re-serialization churn."""
    old = path.read_text()
    indent = 1 if old.startswith("{\n \"") else 2
    path.write_text(json.dumps(doc, indent=indent, ensure_ascii=False) + ("\n" if old.endswith("\n") else ""))


def clean(rec: dict) -> dict:
    return {k: v for k, v in rec.items() if not k.startswith("_")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pass_dir", type=pathlib.Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    pass_dir = args.pass_dir.resolve()
    date = pass_dir.name.replace("-refresh", "")
    p = load_pass(pass_dir)
    report = [f"# Refresh {date}: integration report", ""]

    # --- news items
    news = json.loads((DATA / "news.json").read_text())["items"]
    have_ids = {i["id"] for i in news}
    have_urls = {s.get("url") for i in news for s in i.get("sources", [])}
    ship, dropped = [], []
    for it in sorted(p["items"], key=lambda r: r.get("date", ""), reverse=True):
        urls = {s.get("url") for s in it.get("sources", [])}
        if it["id"] in have_ids or it["id"] in {s["id"] for s in ship}:
            dropped.append(f"{it['id']}: already on the News tab")
        elif urls & have_urls:
            dropped.append(f"{it['id']}: its source is already cited by a News item")
        elif not fetched(it):
            dropped.append(f"{it['id']}: no fetched source after quote repair")
        else:
            ship.append(clean(it))
    report += [f"## News: {len(ship)} added", ""]
    report += [f"- {r['date']} {r['headline']}" for r in ship] or ["- none"]
    if dropped:
        report += ["", "Dropped:"] + [f"- {d}" for d in dropped]
    if args.apply and ship:
        NEWS_PASS.joinpath(f"refresh-{date}.json").write_text(json.dumps(
            {"_meta": {"captured": date, "agent": f"refresh-{date}",
                       "scope": "daily refresh: haiku agents, quotes repaired and verified offline"},
             "items": ship}, indent=2, ensure_ascii=False) + "\n")

    # --- checks
    applied, manual, confirmed = [], [], 0
    docs = {}
    for c in p["checks"]:
        verdict = c.get("verdict")
        if verdict == "confirmed":
            confirmed += 1
            continue
        if verdict not in ("outdated", "wrong"):
            continue
        tag = f"{c.get('file')}/{c.get('target')}: {verdict}"
        path = DATA / f"{c.get('file')}.json"
        if not fetched(c):
            manual.append(f"{tag}: no fetched source; not applied")
            continue
        if not path.exists():
            manual.append(f"{tag}: no data file {path.name}")
            continue
        doc = docs.setdefault(path, json.loads(path.read_text()))
        rec = resolve(doc, c.get("target"))
        if rec is None:
            manual.append(f"{tag}: no record with that id")
            continue
        if replace_once(json.loads(json.dumps(rec)), c["correction"], c["correction"]) and \
                not replace_once(json.loads(json.dumps(rec)), c.get("claim", ""), ""):
            continue  # already applied on an earlier run of this pass
        n = replace_once(rec, c.get("claim", ""), c["correction"])
        if n != 1:
            manual.append(f"{tag}: claim found {n} times, apply by hand -> {c['correction']!r}")
            continue
        if isinstance(rec.get("sources"), list):
            seen = {s.get("url") for s in rec["sources"] if isinstance(s, dict)}
            rec["sources"] += [clean(s) for s in fetched(c) if s.get("url") not in seen]
        applied.append(f"{tag}: {c['claim']!r} -> {c['correction']!r}")
    report += ["", f"## Validation of shipped data: {confirmed} confirmed, {len(applied)} corrected, "
               f"{len(manual)} need a human", ""]
    report += [f"- corrected {a}" for a in applied]
    report += [f"- needs a human: {m}" for m in manual]

    # --- dockets
    dk_path = DATA / "dockets.json"
    dk = docs.setdefault(dk_path, json.loads(dk_path.read_text()))
    dk_ids = {d["id"] for d in dk["dockets"]}
    dk_urls = {d.get("url") for d in dk["dockets"]}
    new_dk = [clean(d) for d in p["dockets"]
              if d["id"] not in dk_ids and d.get("url") not in dk_urls and fetched(d)]
    dk["dockets"] += new_dk
    report += ["", f"## Utility filings: {len(new_dk)} added", ""]
    report += [f"- {d['forum']} {d.get('date', '')}: {d['id']}" for d in new_dk] or ["- none"]

    # --- applications: ship once a human/agent has set `group` to a segments.json group id
    sg_path = DATA / "segments.json"
    sg = docs.setdefault(sg_path, json.loads(sg_path.read_text()))
    groups = {g["id"] for g in sg["_meta"].get("groups", [])}
    sg_ids = {r["id"] for r in sg["segments"]}
    new_sg = [clean(a) for a in p["applications"]
              if a.get("group") in groups and a["id"] not in sg_ids and fetched(a)]
    sg["segments"] += new_sg
    report += ["", f"## Applications: {len(new_sg)} added", ""]
    report += [f"- {a['name']} ({a['power_class']})" for a in new_sg] or ["- none"]

    # --- curated-only records
    held = [a for a in p["applications"] if a.get("group") not in groups] + p["regions"]
    if held:
        report += ["", "## Held for curation (set `group` to a segments.json group id, or add regions by hand)", ""]
        report += [f"- {r['_file']}: {r['id']}" for r in held]

    if args.apply:
        for path, doc in docs.items():
            dump(path, doc)
    (pass_dir / "REPORT.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    print(f"\n{'applied' if args.apply else 'dry run'}; report at {pass_dir.relative_to(ROOT)}/REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
