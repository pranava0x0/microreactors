#!/usr/bin/env python3
"""Fetch and cache a source document, recording it in the source index.

Every source document grabbed during research gets:
  1. a cached copy under data/cache/ (gitignored; raw bytes exactly as fetched),
  2. an index row in data/research/source_index.json with the original URL, the
     access date, SHA-256 of the cached bytes, content type and size,
so any claim sourced to the document can later be re-verified against the exact
bytes that were read, even if the URL dies.

Usage:
  python3 tools/fetch_source.py URL [URL ...] [--title "..."] [--note "..."] [--force]
  python3 tools/fetch_source.py URL --from-file capture.html   # pre-captured body
  python3 tools/fetch_source.py --list

--from-file indexes URL with bytes captured out-of-band (e.g. via a real
browser when the host 403s non-browser TLS fingerprints — nrc.gov/docs,
*.af.mil and oklo.com all do). The row records capture="out-of-band" so the
provenance is honest.

Idempotent: a URL already in the index is skipped (reported) unless --force,
which re-fetches and updates the row in place. Exit 1 if any fetch failed.
Stdlib only, like every tool in this repo.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
INDEX = ROOT / "data" / "research" / "source_index.json"

# Some hosts 403 the default Python UA; identify as a normal browser.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

EXT_BY_TYPE = {
    "application/pdf": ".pdf", "text/html": ".html", "application/json": ".json",
    "text/plain": ".txt", "application/xml": ".xml", "text/xml": ".xml",
}


def load_index() -> dict:
    if INDEX.exists():
        return json.loads(INDEX.read_text())
    return {"_meta": {"purpose": "Every source document fetched during research: "
                                 "original URL, access date, SHA-256 of the cached bytes. "
                                 "Cache lives in data/cache/ (gitignored)."},
            "sources": []}


def save_index(idx: dict) -> None:
    idx["sources"].sort(key=lambda r: r["url"])
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False) + "\n")


def fetch(url: str, timeout: int = 60) -> tuple:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        return body, ctype, resp.geturl()


def cache_path(url: str, ctype: str) -> pathlib.Path:
    stem = hashlib.sha256(url.encode()).hexdigest()[:16]
    ext = EXT_BY_TYPE.get(ctype, "")
    if not ext:
        tail = url.split("?")[0].rsplit(".", 1)
        ext = "." + tail[1].lower() if len(tail) == 2 and len(tail[1]) <= 5 else ".bin"
    return CACHE / f"{stem}{ext}"


def sniff_type(body: bytes, path: pathlib.Path) -> str:
    if body[:5] == b"%PDF-":
        return "application/pdf"
    for t, ext in EXT_BY_TYPE.items():
        if path.suffix == ext:
            return t
    return "application/octet-stream"


def add(url: str, title: str, note: str, force: bool, idx: dict,
        body_path: str = "") -> bool:
    """Fetch url into the cache and upsert its index row. True on success.

    body_path: index url with pre-captured bytes from this file instead of
    fetching (for hosts that 403 non-browser clients); recorded as
    capture="out-of-band"."""
    row = next((r for r in idx["sources"] if r["url"] == url), None)
    if row and not force and (CACHE / row["cache"]).exists():
        print(f"already indexed ({row['fetched']}): {url}")
        return True
    if body_path:
        p_in = pathlib.Path(body_path)
        body, final_url = p_in.read_bytes(), url
        ctype = sniff_type(body, p_in)
    else:
        try:
            body, ctype, final_url = fetch(url)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            print(f"FETCH FAILED  {url}: {e}", file=sys.stderr)
            return False
    CACHE.mkdir(parents=True, exist_ok=True)
    p = cache_path(url, ctype)
    p.write_bytes(body)
    new = {
        "url": url,
        "fetched": dt.date.today().isoformat(),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "content_type": ctype or "unknown",
        "cache": p.name,
    }
    if body_path:
        new["capture"] = "out-of-band"
    if final_url != url:
        new["final_url"] = final_url
    if title:
        new["title"] = title
    elif row and row.get("title"):
        new["title"] = row["title"]
    if note:
        new["note"] = note
    elif row and row.get("note"):
        new["note"] = row["note"]
    if row:
        idx["sources"][idx["sources"].index(row)] = new
    else:
        idx["sources"].append(new)
    print(f"cached {len(body):,}B {ctype or '?'} -> data/cache/{p.name}  {url}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--title", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--from-file", default="",
                    help="index the (single) URL with pre-captured bytes from this file")
    args = ap.parse_args()
    if args.from_file and len(args.urls) != 1:
        ap.error("--from-file requires exactly one URL")

    idx = load_index()
    if args.list:
        for r in idx["sources"]:
            print(f"{r['fetched']}  {r['bytes']:>9,}B  {r.get('title', '')[:48]:<48} {r['url']}")
        print(f"{len(idx['sources'])} sources indexed")
        return 0
    if not args.urls:
        ap.error("no URLs given (or use --list)")

    ok = all([add(u, args.title, args.note, args.force, idx, args.from_file)
              for u in args.urls])
    save_index(idx)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
