#!/usr/bin/env python3
"""Search NRC ADAMS (Agencywide Documents Access and Management System).

Queries the ADAMS Public Search API that backs https://adams-search.nrc.gov —
the only reliable way to find NRC dockets, licensing correspondence and
pre-application material; ordinary web search does not index ADAMS.

Endpoint contract (verified 2026-08-23 by sniffing the APS Angular app):
  POST https://adams-search.nrc.gov/api/search
  body: {"q": str, "filters": [...], "anyFilters": [...],
         "pageSize": int, "page": int}   (filters may be [])
  response: {"count": N, "results": [{"score": .., "document": {
             AccessionNumber, DocumentTitle, DocumentDate, DateAdded,
             DocketNumber: [..], DocumentType: [..], AuthorAffiliation: [..],
             Url (direct https://www.nrc.gov/docs/... link), IsPackage, ...}}]}
  There is also GET /api/search/{AccessionNumber} for a single-document lookup.

Usage:
  python3 tools/adams_search.py "eVinci Penn State" [--limit 20] [--docket 99902079]
  python3 tools/adams_search.py --accession ML25059A029
  python3 tools/adams_search.py "Eielson" --json          # raw JSON to stdout

Stdlib only. Exit 1 on HTTP failure, 0 otherwise (0 hits is a valid answer).
"""
import argparse
import json
import sys
import urllib.request

API = "https://adams-search.nrc.gov/api/search"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def post(url: str, body: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def get(url: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def search(q: str, limit: int = 20, page: int = 1) -> dict:
    return post(API, {"q": q, "filters": [], "anyFilters": [],
                      "pageSize": limit, "page": page})


def rows(payload: dict) -> list:
    out = []
    for r in payload.get("results", []):
        d = r["document"]
        out.append({
            "accession": d.get("AccessionNumber"),
            "date": d.get("DocumentDate") or d.get("DateAdded"),
            "title": d.get("DocumentTitle") or d.get("Name"),
            "dockets": d.get("DocketNumber") or [],
            "types": d.get("DocumentType") or [],
            "affiliation": d.get("AuthorAffiliation") or [],
            "url": d.get("Url"),
            "package": d.get("IsPackage") == "Yes",
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Search NRC ADAMS")
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--docket", help="restrict to rows whose DocketNumber list contains this")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--accession", help="single-document lookup instead of a search")
    ap.add_argument("--json", action="store_true", help="print raw JSON")
    args = ap.parse_args()

    try:
        if args.accession:
            payload = get(f"{API}/{args.accession}")
            if args.json:
                json.dump(payload, sys.stdout, indent=2)  # complete, cacheable
            else:
                print(json.dumps(payload, indent=2)[:4000])  # human preview
            return 0
        if not args.query and not args.docket:
            ap.error("need a query, --docket, or --accession")
        q = args.query or args.docket
        payload = search(q, args.limit, args.page)
    except OSError as e:
        print(f"ADAMS request failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        json.dump(payload, sys.stdout, indent=2)
        return 0
    out = rows(payload)
    if args.docket:
        out = [r for r in out if args.docket in r["dockets"]]
    print(f"count={payload.get('count')} shown={len(out)}  q={q!r}")
    for r in out:
        dockets = ",".join(r["dockets"]) or "-"
        pkg = " [package]" if r["package"] else ""
        print(f"{r['accession']}  {r['date'] or '?':<10}  docket:{dockets:<12} {r['title'][:88]}{pkg}")
        print(f"    {r['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
