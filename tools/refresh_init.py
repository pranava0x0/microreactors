#!/usr/bin/env python3
"""Set up a refresh pass directory for the research agents.

  python3 tools/refresh_init.py                 # today's date
  python3 tools/refresh_init.py --date 2026-10-18

Creates data/research/<date>-refresh/ with:
  CONTRACT.md   copied from data/research/refresh-contract.md, date filled in
  prompts/*.md  one prompt per agent: data/research/refresh-prompts/_header.md + <agent>.md,
                date filled in. Pass the file's text to the agent verbatim.
  skip/*.json   what the site already holds, one file per data file, so an agent
                can check for duplicates and read the exact shipped text it is
                asked to validate. Regenerated every run from data/*.json; never
                committed (see .gitignore).

Idempotent: re-running rewrites skip/ and CONTRACT.md and leaves agent output alone.
Stdlib only.
"""
import argparse
import datetime as dt
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TEMPLATE = DATA / "research" / "refresh-contract.md"
PROMPTS = DATA / "research" / "refresh-prompts"

# data file -> the key holding its record list. A data file whose records an agent
# may validate or must not duplicate belongs here.
LISTS = {
    "news": "items",
    "opportunities": "opportunities",
    "vendors": "vendors",
    "dockets": "dockets",
    "regions": "regions",
    "segments": "segments",
    "deployment_sites": "sites",
    "arguments": "arguments",
}
TRIM = 400


def slim(value):
    """Keep ids and shipped text; reduce sources to label + url; cap long strings."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k == "sources" and isinstance(v, list):
                out[k] = [{"label": s.get("label", ""), "url": s.get("url", "")}
                          for s in v if isinstance(s, dict)]
            elif k in ("quote", "gaps"):
                continue
            else:
                out[k] = slim(v)
        return out
    if isinstance(value, list):
        return [slim(v) for v in value]
    if isinstance(value, str) and len(value) > TRIM:
        return value[:TRIM] + "..."
    return value


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    args = ap.parse_args()

    pass_dir = DATA / "research" / f"{args.date}-refresh"
    skip = pass_dir / "skip"
    skip.mkdir(parents=True, exist_ok=True)

    news = json.loads((DATA / "news.json").read_text())["items"]
    newest = max(i["date"] for i in news)
    contract = TEMPLATE.read_text().replace("{{DATE}}", args.date).replace("{{NEWEST_NEWS}}", newest)
    (pass_dir / "CONTRACT.md").write_text(contract)

    def fill(text: str) -> str:
        return text.replace("{{DATE}}", args.date).replace("{{NEWEST_NEWS}}", newest)

    prompts = pass_dir / "prompts"
    prompts.mkdir(exist_ok=True)
    header = (PROMPTS / "_header.md").read_text()
    agents = sorted(p.stem for p in PROMPTS.glob("*.md") if not p.name.startswith("_"))
    for name in agents:
        (prompts / f"{name}.md").write_text(fill(header + (PROMPTS / f"{name}.md").read_text()))

    counts = {}
    for name, key in LISTS.items():
        records = json.loads((DATA / f"{name}.json").read_text())[key]
        (skip / f"{name}.json").write_text(json.dumps(slim(records), indent=1, ensure_ascii=False))
        counts[name] = len(records)
    # policy and costs are nested documents, not flat record lists: ship them whole (trimmed).
    for name in ("policy", "costs"):
        d = json.loads((DATA / f"{name}.json").read_text())
        d.pop("_meta", None)
        (skip / f"{name}.json").write_text(json.dumps(slim(d), indent=1, ensure_ascii=False))
        counts[name] = "doc"

    print(f"{pass_dir.relative_to(ROOT)}  newest news {newest}")
    print(f"  prompts: {', '.join(agents)}")
    for k, v in counts.items():
        print(f"  skip/{k}.json  {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
