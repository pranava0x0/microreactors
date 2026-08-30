#!/usr/bin/env python3
"""Merge the news research pass into data/news.json.

  python3 tools/merge_news.py data/research/news
  python3 tools/merge_news.py data/research/news --check   # exit 1 on drift

Same contract as tools/merge_voices.py: builds from the pass, never from its own
output, and skips any agent file marked `_meta.incomplete` so a merge is safe to
run while a later agent is still writing into the same directory.

Sorts newest first and groups by month, because a news page whose first screen is
January is a news page nobody scrolls.
"""
import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "news.json"


def build(pass_dir: pathlib.Path) -> dict:
    items, skipped = [], []
    for f in sorted(pass_dir.glob("*.json")):
        d = json.loads(f.read_text())
        if d.get("_meta", {}).get("incomplete"):
            skipped.append(f.name)
            continue
        items.extend(d.get("items", []))
    seen, uniq = set(), []
    for it in sorted(items, key=lambda x: (x.get("date", ""), x.get("id", "")), reverse=True):
        if it.get("id") in seen:
            continue
        seen.add(it["id"])
        uniq.append(it)

    binding = sum(1 for i in uniq if i.get("binding"))
    cats = collections.Counter(i.get("category") for i in uniq)
    dates = [i["date"] for i in uniq if i.get("date")]
    meta = {
        "captured": "2026-08-30",
        "what_this_is":
            "Dated events in the microreactor market, newest first. Each one says what the "
            "instrument actually is, because the difference between a selection and a signed "
            "contract is the difference between a press release and a business.",
        "binding_note":
            f"{binding} of {len(uniq)} items rest on something executed - a signed contract, a "
            f"filed application, an achieved milestone. The other {len(uniq) - binding} are "
            "selections, letters of intent, memoranda and non-binding term sheets. Both are "
            "reported; only one is a commitment.",
        "window": f"{min(dates)} to {max(dates)}" if dates else "",
        "refresh":
            "tools/news_watch.py polls six trade and government RSS feeds plus SEC EDGAR "
            "full-text search and reports what is not yet written up here. It does not write this "
            "file: judging whether an instrument binds means reading the document.",
    }
    if skipped:
        meta["pending"] = ("Not yet merged, still being written: " + ", ".join(skipped))
    return {"_meta": meta,
            "categories": [{"id": k, "count": v} for k, v in cats.most_common()],
            "items": uniq}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pass_dir", type=pathlib.Path)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = json.dumps(build(a.pass_dir), indent=2, ensure_ascii=False) + "\n"
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            print("DRIFT data/news.json — re-run tools/merge_news.py", file=sys.stderr)
            return 1
        print("data/news.json matches the pass")
        return 0
    OUT.write_text(text)
    d = json.loads(text)
    print(f"wrote data/news.json — {len(d['items'])} items, "
          f"{sum(1 for i in d['items'] if i.get('binding'))} binding")
    for c in d["categories"]:
        print(f"    {c['id']:<16} {c['count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
