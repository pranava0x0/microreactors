#!/usr/bin/env python3
"""Drive a deep research pass: scaffold it, then gate what the agents returned.

A "pass" is one folder under data/research/ holding the raw agent output for a
single set of questions, plus the contract those agents were held to. This tool
makes a pass repeatable:

  init      scaffold data/research/<date>-<slug>/ with the contract and a plan
  validate  check every agent JSON in a pass against the contract, exit 1 on error
  report    coverage summary: records per file, sectors/groups covered, absences

The validator is the load-bearing half. Research agents reliably return three
defects (AGENTS.md): placeholder fields, sources that were never fetched, and
records carrying no number at all. Each is a rule below, so junk fails here
rather than in the dataset.

Stdlib only, like every tool in this repo.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "data" / "research"
CONTRACT = "CONTRACT.md"

MECH_GROUPS = {"diesel", "batteries", "interconnection", "licensing"}
MECH_FAMILIES = {"commercial-contract", "regulatory-rule", "utility-tariff",
                 "public-procurement"}
CASE_SECTORS = {
    "Remote outposts & microgrids", "Marine terminals", "Medical campuses",
    "Critical civic infrastructure", "Off-grid mining & mineral processing",
}
SOURCE_STATUS = {"fetched", "snippet-only"}

MECH_REQUIRED = ["id", "group", "family", "name", "what_it_is", "nuclear_fit", "sources"]
CASE_REQUIRED = ["id", "sector", "name", "summary", "microreactor_read", "sources"]
# A case record with none of these carries no number, and is not a record.
CASE_NUMERIC_ANY = ["price", "capex", "displaced", "capacity", "term_years", "filings"]

PLACEHOLDER = re.compile(r"^\s*(tbd|todo|n/?a|unknown|none|\.\.\.|-+)\s*$", re.I)
# The claim's own date field is an ISO-ish date, so a trailing hyphen is expected.
CLAIM_YEAR = re.compile(r"^\s*((?:19|20)\d{2})")
# A source label is prose, where a 4-digit run inside a longer token is a contract
# number (N69450-16-C-1901), not a year. Require clean boundaries on both sides.
LABEL_YEAR = re.compile(r"(?<![\w\-/])(19|20)\d{2}(?![\w\-/])")


def fail(errors: list, path: pathlib.Path, rec_id: str, msg: str) -> None:
    errors.append(f"{path.name}[{rec_id}]: {msg}")


def check_sources(sources, path, rec_id, errors) -> None:
    if not isinstance(sources, list) or not sources:
        fail(errors, path, rec_id, "no sources")
        return
    for i, s in enumerate(sources):
        where = f"source[{i}]"
        if not isinstance(s, dict):
            fail(errors, path, rec_id, f"{where} is not an object")
            continue
        for k in ("label", "url", "quote", "status"):
            if not str(s.get(k, "")).strip():
                fail(errors, path, rec_id, f"{where} missing {k}")
        url = str(s.get("url", ""))
        if url and not url.startswith(("http://", "https://")):
            fail(errors, path, rec_id, f"{where} url is not absolute: {url}")
        # A bare homepage cites nothing: require a path, query or fragment.
        elif url:
            rest = url.split("://", 1)[1]
            if "/" not in rest.rstrip("/") and "?" not in rest and "#" not in rest:
                fail(errors, path, rec_id, f"{where} is a bare homepage: {url}")
        status = s.get("status")
        if status and status not in SOURCE_STATUS:
            fail(errors, path, rec_id, f"{where} status {status!r} not in {sorted(SOURCE_STATUS)}")


def check_impossible_citation(rec, sources, path, rec_id, errors) -> None:
    """A source published before the event it documents cannot document it.

    Flags any record whose own date is more than a year after the newest year
    appearing in every one of its sources' labels. Advisory-grade: source labels
    do not always carry a date, so silence here proves nothing.
    """
    claim = str(rec.get("signed") or rec.get("date") or "")
    m = CLAIM_YEAR.search(claim)
    if not m:
        return
    claim_year = int(m.group(0))
    horizon = dt.date.today().year + 1
    source_years = []
    for s in sources:
        years = [int(y.group(0)) for y in LABEL_YEAR.finditer(str(s.get("label", "")))
                 if 1900 <= int(y.group(0)) <= horizon]
        if years:
            source_years.append(max(years))
    if source_years and claim_year > max(source_years):
        fail(errors, path, rec_id,
             f"claim dated {claim_year} but newest dated source is {max(source_years)} "
             f"— a source cannot document a later event")


def check_record(rec, kind, path, errors, seen_ids) -> None:
    rec_id = str(rec.get("id", "<no id>"))
    required = MECH_REQUIRED if kind == "mechanism" else CASE_REQUIRED
    for k in required:
        v = rec.get(k)
        if v is None or (isinstance(v, str) and (not v.strip() or PLACEHOLDER.match(v))):
            fail(errors, path, rec_id, f"missing or placeholder field {k!r}")

    if rec_id in seen_ids:
        fail(errors, path, rec_id, f"duplicate id, also in {seen_ids[rec_id]}")
    else:
        seen_ids[rec_id] = path.name

    sources = rec.get("sources") or []
    check_sources(sources, path, rec_id, errors)
    check_impossible_citation(rec, sources, path, rec_id, errors)

    if kind == "mechanism":
        if rec.get("group") not in MECH_GROUPS:
            fail(errors, path, rec_id, f"group {rec.get('group')!r} not in {sorted(MECH_GROUPS)}")
        if rec.get("family") not in MECH_FAMILIES:
            fail(errors, path, rec_id, f"family {rec.get('family')!r} not in {sorted(MECH_FAMILIES)}")
        prec = rec.get("precedents") or []
        if not prec:
            fail(errors, path, rec_id, "no precedents — the precedent is the point of the record")
        for j, p in enumerate(prec):
            idx = p.get("source_idx")
            if idx is not None and not (isinstance(idx, int) and 0 <= idx < len(sources)):
                fail(errors, path, rec_id, f"precedent[{j}] source_idx {idx} out of range")
    else:
        if rec.get("sector") not in CASE_SECTORS:
            fail(errors, path, rec_id, f"sector {rec.get('sector')!r} not in {sorted(CASE_SECTORS)}")
        if not any(rec.get(k) for k in CASE_NUMERIC_ANY):
            fail(errors, path, rec_id,
                 "carries no number and no filing — needs one of " + ", ".join(CASE_NUMERIC_ANY))


def load_pass(pass_dir: pathlib.Path):
    """Yield (path, kind, records) for every agent JSON in the pass."""
    for path in sorted(pass_dir.glob("*.json")):
        try:
            doc = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            yield path, "unparseable", e
            continue
        if "mechanisms" in doc:
            yield path, "mechanism", doc
        elif "cases" in doc:
            yield path, "case", doc
        else:
            yield path, "unknown", doc


def cmd_validate(pass_dir: pathlib.Path) -> int:
    errors: list = []
    seen_ids: dict = {}
    files = records = 0
    for path, kind, doc in load_pass(pass_dir):
        files += 1
        if kind == "unparseable":
            errors.append(f"{path.name}: invalid JSON — {doc}")
            continue
        if kind == "unknown":
            errors.append(f"{path.name}: has neither 'mechanisms' nor 'cases'")
            continue
        meta = doc.get("_meta") or {}
        if not meta.get("absences"):
            errors.append(f"{path.name}: _meta.absences is empty — "
                          "a report of only successes hides its coverage gaps")
        for rec in doc["mechanisms" if kind == "mechanism" else "cases"]:
            records += 1
            check_record(rec, kind, path, errors, seen_ids)

    if not files:
        print(f"no agent JSON found in {pass_dir}", file=sys.stderr)
        return 1
    for e in errors:
        print("FAIL " + e)
    print(f"\n{files} file(s), {records} record(s), {len(errors)} error(s)")
    return 1 if errors else 0


def cmd_report(pass_dir: pathlib.Path) -> int:
    total = 0
    for path, kind, doc in load_pass(pass_dir):
        if kind in ("unparseable", "unknown"):
            print(f"{path.name}: {kind}")
            continue
        recs = doc["mechanisms" if kind == "mechanism" else "cases"]
        total += len(recs)
        buckets: dict = {}
        for r in recs:
            buckets.setdefault(r.get("group") or r.get("sector") or "?", []).append(r)
        fetched = sum(1 for r in recs for s in (r.get("sources") or [])
                      if s.get("status") == "fetched")
        snippet = sum(1 for r in recs for s in (r.get("sources") or [])
                      if s.get("status") == "snippet-only")
        print(f"\n{path.name}  ({kind}, {len(recs)} records; "
              f"{fetched} fetched / {snippet} snippet-only sources)")
        for b, rs in sorted(buckets.items()):
            print(f"  {b}: {len(rs)}")
        for a in (doc.get("_meta") or {}).get("absences", []):
            print(f"  absence: {a}")
    print(f"\ntotal {total} records")
    return 0


def cmd_init(slug: str, question: str, date: str) -> int:
    pass_dir = RESEARCH / f"{date}-{slug}"
    pass_dir.mkdir(parents=True, exist_ok=True)
    src = None
    for cand in sorted(RESEARCH.glob("*/" + CONTRACT), reverse=True):
        src = cand
        break
    if src and not (pass_dir / CONTRACT).exists():
        (pass_dir / CONTRACT).write_text(src.read_text())
        print(f"copied contract from {src.parent.name}")
    plan = pass_dir / "PLAN.md"
    if not plan.exists():
        plan.write_text(
            f"# Research pass — {date} — {slug}\n\n"
            f"## Question\n{question}\n\n"
            "## Seed (inline, before any agent)\n"
            "- [ ] Has someone already enumerated this? Find the existing dataset/report first.\n"
            "- [ ] 4–6 broad web searches across .gov, national labs, regulator dockets, trade press.\n"
            "- [ ] Cache anything primary with `tools/fetch_source.py` (main session only — agents must not).\n\n"
            "## Partition (one agent per line; each entity belongs to exactly one agent)\n"
            "| agent | output file | scope | skip-list |\n|---|---|---|---|\n\n"
            "## Gate\n"
            f"```bash\npython3 tools/research_pass.py validate data/research/{date}-{slug}\n"
            f"python3 tools/research_pass.py report data/research/{date}-{slug}\n```\n\n"
            "## Integration\n"
            "- [ ] Single writer: only the main session edits `data/*.json`.\n"
            "- [ ] Cache every shipping source, then `python3 tools/verify_quotes.py --cache`.\n"
            "- [ ] `python3 tools/build_gaps.py && python3 tools/build_data.py`\n"
            "- [ ] `python3 -m unittest discover -s tests`\n")
        print(f"wrote {plan.relative_to(ROOT)}")
    print(f"pass ready: {pass_dir.relative_to(ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="scaffold a new research pass")
    i.add_argument("slug")
    i.add_argument("--question", default="(fill in)")
    i.add_argument("--date", default=dt.date.today().isoformat())
    for name in ("validate", "report"):
        p = sub.add_parser(name, help=f"{name} a research pass")
        p.add_argument("pass_dir", type=pathlib.Path)
    a = ap.parse_args()
    if a.cmd == "init":
        return cmd_init(a.slug, a.question, a.date)
    pass_dir = a.pass_dir if a.pass_dir.is_absolute() else ROOT / a.pass_dir
    if not pass_dir.is_dir():
        print(f"no such pass directory: {pass_dir}", file=sys.stderr)
        return 1
    return cmd_validate(pass_dir) if a.cmd == "validate" else cmd_report(pass_dir)


if __name__ == "__main__":
    sys.exit(main())
