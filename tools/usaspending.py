#!/usr/bin/env python3
"""Query USAspending.gov for federal awards, with the money stated honestly.

Federal award data is the best public source of real contract values in this
space: press releases announce projects, USAspending records what was actually
obligated. Two distinctions this tool refuses to blur, because quoting the wrong
one overstates the market by an order of magnitude on multi-year vehicles:

  * **obligated** — money actually put on contract to date
  * **potential**  — the ceiling if every option year is exercised

Both are reported for every award, never merged into one "value" — but only
`--detail` can fill in the ceiling. The search endpoint does not carry it at
all, and the per-award endpoint returns `base_and_all_options_value` as null for
a delivery order, because the ceiling lives on the parent IDV rather than the
order. So `potential` is honestly `null` far more often than not, and a null
there means "not published at this level", never "no ceiling".

**The distinction inverts on assistance awards, and the API does not warn you.**
On a contract, `total_obligation` is the conservative figure. On a multi-phase
cooperative agreement it can be the full federal *ceiling*: the Tanana Chiefs
Conference ERA award reports $26,062,370 while DOE's own announcement says only
$4.1M was released for Phase 1 — a 6x overstatement if read as money committed.
Never quote an assistance award's obligation without checking the awarding
agency's announcement for a phase release.

Keyword search is also weaker than it looks on assistance awards: DOE's Energy
Improvements in Rural or Remote Areas awards contain no text matching that
programme name and surface only under CFDA 81.255 (Clean Energy Demonstrations).
A programme that returns nothing by keyword is not absent — search its CFDA
number or its awarding agency instead.

It also reports whether the result set hit the page limit. A capped list is a
floor, not a total.

Usage:
  python3 tools/usaspending.py "microgrid" --years 2020 2026
  python3 tools/usaspending.py "shore power" "cold ironing" --awards contracts grants
  python3 tools/usaspending.py "energy savings performance contract" \
      --out data/research/awards/espc.json

No API key needed. Stdlib only, like every tool in this repo.
"""
import argparse
import datetime as dt
import json
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# USAspending award-type groups. Contracts and grants are what this project needs;
# the rest are here so a future question does not have to look them up again.
AWARD_GROUPS = {
    "contracts": ["A", "B", "C", "D"],
    "idvs": ["IDV_A", "IDV_B", "IDV_B_A", "IDV_B_B", "IDV_B_C", "IDV_C", "IDV_D", "IDV_E"],
    "grants": ["02", "03", "04", "05"],
    "direct_payments": ["06", "10"],
    "loans": ["07", "08"],
    "other": ["09", "11", "-1"],
}
# Field names differ between contract and assistance searches; request both sets.
CONTRACT_FIELDS = ["Award ID", "Recipient Name", "Awarding Agency", "Awarding Sub Agency",
                   "Start Date", "End Date", "Award Amount", "Total Outlays",
                   "Description", "Place of Performance State Code",
                   "Place of Performance City Code", "Contract Award Type"]
ASSIST_FIELDS = ["Award ID", "Recipient Name", "Awarding Agency", "Awarding Sub Agency",
                 "Start Date", "End Date", "Award Amount", "Total Outlays",
                 "Description", "Place of Performance State Code", "Assistance Listings"]


def post(payload: dict) -> dict:
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:400]
        raise SystemExit(f"USAspending HTTP {e.code}: {body}")


def search(keyword: str, group: str, start: str, end: str, limit: int) -> dict:
    fields = CONTRACT_FIELDS if group in ("contracts", "idvs") else ASSIST_FIELDS
    payload = {
        "filters": {
            "keywords": [keyword],
            "award_type_codes": AWARD_GROUPS[group],
            "time_period": [{"start_date": start, "end_date": end}],
        },
        "fields": fields,
        "limit": limit,
        "page": 1,
        "sort": "Award Amount",
        "order": "desc",
        "subawards": False,
    }
    return post(payload)


def award_detail(generated_id: str) -> dict:
    """Per-award record. The only place a contract ceiling can appear."""
    req = urllib.request.Request(
        f"https://api.usaspending.gov/api/v2/awards/{generated_id}/",
        headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return {}


def add_potential(rows: list) -> int:
    """Fill `potential` from the award endpoint. Returns how many were found."""
    found = 0
    for r in rows:
        gid = r.get("generated_id")
        if not gid:
            continue
        d = award_detail(gid)
        val = d.get("base_and_all_options_value") or d.get("base_exercised_options_val")
        if val is not None:
            r["potential"] = val
            found += 1
    return found


def normalise(rows: list, group: str) -> list:
    out = []
    for r in rows:
        out.append({
            "award_id": r.get("Award ID"),
            "recipient": r.get("Recipient Name"),
            "agency": r.get("Awarding Agency"),
            "sub_agency": r.get("Awarding Sub Agency"),
            "start": r.get("Start Date"),
            "end": r.get("End Date"),
            # USAspending's "Award Amount" is the obligated figure for this award;
            # outlays are what has actually been disbursed against it.
            "obligated": r.get("Award Amount"),
            "outlayed": r.get("Total Outlays"),
            # Filled by --detail only; see the note at the top about why this is
            # usually null even when a ceiling exists on the parent IDV.
            "potential": None,
            "state": r.get("Place of Performance State Code"),
            "type": r.get("Contract Award Type") or r.get("Assistance Listings"),
            "group": group,
            "generated_id": r.get("generated_internal_id"),
            "description": (r.get("Description") or "")[:400],
            "url": (f"https://www.usaspending.gov/award/{r.get('generated_internal_id')}"
                    if r.get("generated_internal_id") else
                    "https://www.usaspending.gov/search"),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keywords", nargs="+")
    ap.add_argument("--awards", nargs="+", default=["contracts", "grants"],
                    choices=sorted(AWARD_GROUPS))
    ap.add_argument("--years", nargs=2, default=["2018", str(dt.date.today().year)],
                    metavar=("FROM", "TO"))
    ap.add_argument("--limit", type=int, default=50, help="rows per keyword per award group")
    ap.add_argument("--detail", action="store_true",
                    help="fetch each award's ceiling (base_and_all_options_value). One extra "
                         "request per row, and frequently null — see the note above.")
    ap.add_argument("--out", type=pathlib.Path)
    a = ap.parse_args()
    start, end = f"{a.years[0]}-01-01", f"{a.years[1]}-12-31"

    results = []
    for kw in a.keywords:
        for group in a.awards:
            doc = search(kw, group, start, end, a.limit)
            rows = normalise(doc.get("results") or [], group)
            n_potential = add_potential(rows) if a.detail else 0
            meta = doc.get("page_metadata") or {}
            capped = bool(meta.get("hasNext"))
            total = sum(r["obligated"] or 0 for r in rows)
            print(f"{kw!r} / {group}: {len(rows)} awards, "
                  f"${total:,.0f} obligated in this page"
                  + (f"; {n_potential}/{len(rows)} ceilings published" if a.detail else "")
                  + ("  ** more pages exist — this is a floor **" if capped else ""))
            for r in rows[:5]:
                print(f"    ${(r['obligated'] or 0):>14,.0f}  {r['recipient']}  "
                      f"({r['start']} to {r['end']}, {r['state']})")
            results.append({"keyword": kw, "award_group": group, "capped": capped,
                            "page_total_obligated": total, "awards": rows})

    if a.out:
        out = a.out if a.out.is_absolute() else ROOT / a.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"_meta": {
            "source": "USAspending.gov /api/v2/search/spending_by_award/",
            "queried": dt.date.today().isoformat(),
            "time_period": [start, end],
            "caveat": "'obligated' is money on contract to date, not the ceiling if all option "
                      "years are exercised, which is reported as 'potential' and is null unless "
                      "--detail was passed AND the API publishes it at this level. Any result "
                      "marked capped:true is a floor. On "
                      "multi-phase cooperative agreements the obligation can instead be the full "
                      "federal ceiling — check the awarding agency's own announcement for a "
                      "phase release before quoting it.",
        }, "queries": results}, indent=2, ensure_ascii=False) + "\n")
        print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
