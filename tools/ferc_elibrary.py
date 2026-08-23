#!/usr/bin/env python3
"""Search FERC eLibrary (dockets and filings).

Queries the JSON API that backs https://elibrary.ferc.gov — the only reliable
way to find FERC filings; ordinary web search does not index eLibrary.

Endpoint contract (verified 2026-08-23 against the live service):
  POST https://elibrary.ferc.gov/eLibraryWebAPI/api/Search/AdvancedSearch
  body: {"searchText": str, "searchFullText": bool, "searchDescription": bool,
         "allDates": bool, "dateSearches": [...], "resultsPerPage": int,
         "curPage": int, "availability": "public", "categories": [],
         "libraries": [], "affiliations": [], "docketSearches":
         [{"docketNumber": "ER24-1234", "subDocketNumbers": []}], ...}
  response: {"searchHits": [{"description", "acesssionNumber" (sic),
             "filedDate", "docketNumbers": [..], "classTypes": [..],
             "libraries": [..], "transmittals": [files..]}], "totalHits": N}

The human-facing permalink for a hit is
  https://elibrary.ferc.gov/eLibrary/filelist?accession_number={accession}

Usage:
  python3 tools/ferc_elibrary.py "microreactor"            # full-text
  python3 tools/ferc_elibrary.py --docket ER24-2444        # docket sweep
  python3 tools/ferc_elibrary.py "Malmstrom" --desc-only   # description search
  python3 tools/ferc_elibrary.py "..." --json              # raw JSON

Stdlib only. Exit 1 on HTTP failure, 0 otherwise (0 hits is a valid answer).
"""
import argparse
import json
import sys
import urllib.request

API = "https://elibrary.ferc.gov/eLibraryWebAPI/api/Search/AdvancedSearch"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def search(text: str = "", docket: str = "", full_text: bool = True,
           per_page: int = 20, page: int = 1) -> dict:
    body = {
        "searchText": text,
        "searchFullText": bool(text) and full_text,
        "searchDescription": True,
        "allDates": True,
        "dateSearches": [],
        "resultsPerPage": per_page,
        "curPage": page,
        "availability": "public",
        "categories": [],
        "libraries": [],
        "affiliations": [],
        "eFiling": False,
        "allAccessions": True,
        "accessionNumber": None,
        "docketSearches": ([{"docketNumber": docket, "subDocketNumbers": []}]
                           if docket else []),
        "sortBy": "",
        "groupBy": "",
    }
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def rows(payload: dict) -> list:
    out = []
    for h in payload.get("searchHits", []):
        acc = h.get("acesssionNumber") or h.get("accessionNumber")
        out.append({
            "accession": acc,
            "filed": h.get("filedDate"),
            "description": h.get("description"),
            "dockets": h.get("docketNumbers") or [],
            "class_types": [f"{c.get('documentClass')}/{c.get('documentType')}"
                            for c in (h.get("classTypes") or [])],
            "libraries": h.get("libraries") or [],
            "files": len(h.get("transmittals") or []),
            "url": f"https://elibrary.ferc.gov/eLibrary/filelist?accession_number={acc}",
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Search FERC eLibrary")
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--docket", default="")
    ap.add_argument("--desc-only", action="store_true",
                    help="search descriptions only, not full text")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not args.query and not args.docket:
        ap.error("need a query and/or --docket")

    try:
        payload = search(args.query, args.docket, not args.desc_only,
                         args.limit, args.page)
    except OSError as e:
        print(f"eLibrary request failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        json.dump(payload, sys.stdout, indent=2)
        return 0
    out = rows(payload)
    total = payload.get("totalHits", "?")
    print(f"totalHits={total} shown={len(out)}  q={args.query!r} docket={args.docket!r}")
    for r in out:
        dockets = ",".join(r["dockets"][:3]) or "-"
        print(f"{r['accession']}  filed:{r['filed'] or '?':<10}  {dockets:<16} {(r['description'] or '')[:90]}")
        print(f"    {r['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
