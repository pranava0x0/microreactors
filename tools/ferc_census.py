#!/usr/bin/env python3
"""Census FERC eLibrary: how many filings name a thing, and when.

`tools/ferc_elibrary.py` answers "find me filings"; this answers "is this
instrument actually being used, and is it growing?" — which is the question a
market map needs and which no publication answers.

Two traps are built in, because both were hit by hand before this existed:

  * **Docket concentration.** A phrase can look like a surge and be one
    proceeding. 45 filings named "co-located load" in 2024 and 42 of them sat in
    docket AD24-11, FERC's own technical conference. Filing counts are not deal
    counts. Every census reports its top dockets and flags any year where one
    docket carries most of the volume.
  * **A capped list is a floor, not a total.** eLibrary returns at most `--limit`
    rows. If totalHits exceeds what came back, the year-shape is unreliable and
    this says so instead of charting it.

Usage:
  python3 tools/ferc_census.py "Surplus Interconnection Service Agreement"
  python3 tools/ferc_census.py "co-located load" "black start service" --limit 200
  python3 tools/ferc_census.py "..." --out data/research/ferc/census.json

Stdlib only, like every tool in this repo.
"""
import argparse
import collections
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ELIBRARY = ROOT / "tools" / "ferc_elibrary.py"
FILELIST = "https://elibrary.ferc.gov/eLibrary/filelist?accession_number="
# A year in which one docket carries at least this share is a proceeding, not a market.
# Only applied above MIN_VOLUME filings — in a year with one filing, "one docket
# carries all of it" is arithmetic, not a finding.
CONCENTRATION = 0.5
MIN_VOLUME = 5


def search(phrase: str, limit: int) -> dict:
    """Run the repo's eLibrary client and return its parsed JSON."""
    out = subprocess.run(
        [sys.executable, str(ELIBRARY), phrase, "--desc-only",
         "--limit", str(limit), "--json"],
        capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise SystemExit(f"ferc_elibrary.py failed for {phrase!r}: {out.stderr.strip()}")
    return json.loads(out.stdout)


def base_docket(d: str) -> str:
    """ER26-803-000 -> ER26-803: sub-numbers are the same proceeding."""
    return re.sub(r"-\d{3}$", "", d)


def census(phrase: str, limit: int) -> dict:
    doc = search(phrase, limit)
    rows = doc.get("searchHits") or []
    total = doc.get("totalHits", len(rows))
    capped = total > len(rows)

    by_year = collections.Counter()
    dockets_by_year = collections.defaultdict(collections.Counter)
    all_dockets = collections.Counter()
    named = []  # filings whose description names a counterparty agreement

    for r in rows:
        year = (r.get("filedDate") or "")[-4:]
        by_year[year] += 1
        for d in (r.get("docketNumbers") or ["(none)"]):
            b = base_docket(d)
            dockets_by_year[year][b] += 1
            all_dockets[b] += 1
        desc = re.sub(r"\s+", " ", r.get("description") or "")
        if "Agreement with" in desc:
            named.append({"filed": r.get("filedDate"), "accession": r.get("acesssionNumber"),
                          "dockets": r.get("docketNumbers"), "description": desc,
                          "url": FILELIST + str(r.get("acesssionNumber"))})

    concentrated = []
    for year, cnt in sorted(by_year.items()):
        if cnt < MIN_VOLUME:
            continue
        top, n = dockets_by_year[year].most_common(1)[0]
        if n / cnt >= CONCENTRATION:
            concentrated.append({"year": year, "docket": top, "filings": n, "of": cnt,
                                 "note": "one docket carries most of this year's volume — "
                                         "a proceeding, not a market"})

    return {
        "phrase": phrase,
        "total_hits": total,
        "returned": len(rows),
        "capped": capped,
        "capped_note": ("totalHits exceeds the returned rows, so the year shape below is a "
                        "floor and must not be read as a trend") if capped else "",
        "by_year": dict(sorted(by_year.items())),
        "named_agreements_by_year": dict(sorted(
            collections.Counter(n["filed"][-4:] for n in named).items())),
        "distinct_dockets": len(all_dockets),
        "top_dockets": all_dockets.most_common(8),
        "single_docket_years": concentrated,
        "named_agreements": named,
    }


def render(c: dict) -> None:
    print(f"\n{c['phrase']!r}")
    print(f"  totalHits={c['total_hits']} returned={c['returned']}"
          + ("  ** CAPPED — year shape is a floor **" if c["capped"] else ""))
    print(f"  distinct dockets: {c['distinct_dockets']}")
    print("  filings by year:            " +
          "  ".join(f"{y}:{n}" for y, n in c["by_year"].items()))
    if c["named_agreements_by_year"]:
        print("  named counterparty agreements: " +
              "  ".join(f"{y}:{n}" for y, n in c["named_agreements_by_year"].items()))
    for w in c["single_docket_years"]:
        print(f"  ! {w['year']}: {w['filings']}/{w['of']} filings are docket {w['docket']} "
              f"— {w['note']}")
    if not c["single_docket_years"] and not c["capped"]:
        print("  no single-docket year and no cap: the year shape is usable")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phrases", nargs="+", help="exact phrases to census (description-only search)")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--out", type=pathlib.Path,
                    help="write the full census JSON here (named agreements included)")
    a = ap.parse_args()

    results = [census(p, a.limit) for p in a.phrases]
    for c in results:
        render(c)
    if a.out:
        out = a.out if a.out.is_absolute() else ROOT / a.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(
            {"_meta": {"source": "FERC eLibrary description-only search via tools/ferc_elibrary.py",
                       "limit": a.limit,
                       "caveat": "Filing counts are not deal counts. Check single_docket_years "
                                 "before reading any year shape as market activity."},
             "censuses": results}, indent=2, ensure_ascii=False) + "\n")
        print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
