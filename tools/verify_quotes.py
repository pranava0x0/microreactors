#!/usr/bin/env python3
"""Upgrade snippet-only sources by fetching each page and confirming its quote.

A source recorded with status "snippet-only" was corroborated by search results
without a direct page read. This tool fetches each such URL, normalises both
sides (whitespace, curly quotes, case, HTML entities; PDFs via pypdf when
available), and if the recorded verbatim quote appears in the page, flips the
status to "fetched" and stamps verified. Sources that stay unreachable keep
snippet-only status, which the site renders with an explicit marker.

  python3 tools/verify_quotes.py          # verify and rewrite data files
  python3 tools/verify_quotes.py --dry    # report only
  python3 tools/verify_quotes.py --cache  # offline: verify EVERY quoted source
                                          # against data/cache via the source
                                          # index; exit 1 on any mismatch

--cache needs no network, so it can gate a local run: a quote that drifts from
the cached bytes of its source fails loudly. Sources whose URL is not in the
index (or whose cache file is missing) are reported but do not fail — the
cache is gitignored, so a fresh checkout legitimately lacks it.
"""
import argparse
import datetime
import html
import io
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Any, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FILES = ["opportunities", "vendors", "costs", "sectors", "mechanisms", "policy",
         "deployment_sites"]
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def norm(s: str) -> str:
    s = html.unescape(s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("‑", "-")
    return re.sub(r"\s+", " ", s).casefold().strip()


def page_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    if raw[:4] == b"%PDF":
        try:
            from pypdf import PdfReader
            return " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(raw)).pages)
        except Exception:
            return ""
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", text)


def walk(node: Any, out: List[dict], any_status: bool = False) -> None:
    if isinstance(node, dict):
        ok = any_status or node.get("status") == "snippet-only"
        if ok and node.get("url") and node.get("quote"):
            out.append(node)
        for v in node.values():
            walk(v, out, any_status)
    elif isinstance(node, list):
        for v in node:
            walk(v, out, any_status)


def cached_text(cache_file: pathlib.Path) -> str:
    raw = cache_file.read_bytes()
    if raw[:5] == b"%PDF-":
        try:
            import fitz  # PyMuPDF
            return " ".join(p.get_text() for p in fitz.open(cache_file))
        except ImportError:
            try:
                from pypdf import PdfReader
                return " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(raw)).pages)
            except ImportError:
                return ""
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", text)


def check_against_cache(verbose: bool = False) -> int:
    """Verify every quoted source (any status) against data/cache.
    Exit 1 only on a real mismatch; a missing cache entry is a report line
    (listed only when verbose — the cache legitimately holds a subset)."""
    index_p = DATA / "research" / "source_index.json"
    by_url = {}
    if index_p.exists():
        for r in json.loads(index_p.read_text())["sources"]:
            by_url[r["url"]] = DATA / "cache" / r["cache"]
    ok, missing, mismatched = [], [], []
    for name in FILES:
        targets: List[dict] = []
        walk(json.loads((DATA / f"{name}.json").read_text()), targets, any_status=True)
        for src in targets:
            cache_file = by_url.get(src["url"])
            if not cache_file or not cache_file.exists():
                missing.append((name, src["url"]))
                continue
            if norm(src["quote"]) in norm(cached_text(cache_file)):
                ok.append((name, src["url"]))
            else:
                mismatched.append((name, src["url"], src["quote"][:60]))
    print(f"cache-verified {len(ok)} · not-in-cache {len(missing)} · MISMATCH {len(mismatched)}")
    for name, url, q in mismatched:
        print(f"QUOTE MISMATCH  {name}: {url}\n    quote: {q}…")
    if verbose:
        for name, url in missing:
            print(f"not in cache     {name}: {url}")
    return 1 if mismatched else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--cache", action="store_true",
                    help="offline: verify all quoted sources against data/cache")
    ap.add_argument("--stamp", default=datetime.date.today().isoformat(),
                    help="verification date to record (defaults to today; "
                         "pass explicitly for a reproducible backfill)")
    args = ap.parse_args()
    if args.cache:
        return check_against_cache(verbose=True)
    stamp = args.stamp

    verified: List[Tuple[str, str]] = []
    unreachable: List[Tuple[str, str]] = []
    mismatched: List[Tuple[str, str]] = []
    cache: dict = {}

    for name in FILES:
        p = DATA / f"{name}.json"
        d = json.loads(p.read_text())
        targets: List[dict] = []
        walk(d, targets)
        changed = False
        for src in targets:
            url = src["url"]
            if url not in cache:
                try:
                    cache[url] = norm(page_text(url))
                except Exception as e:
                    cache[url] = e
            body = cache[url]
            if isinstance(body, Exception):
                unreachable.append((name, url))
                continue
            if norm(src["quote"]) in body:
                src["status"] = "fetched"
                src["verified"] = f"{stamp} quote confirmed in page"
                verified.append((name, url))
                changed = True
            else:
                mismatched.append((name, url))
        if changed and not args.dry:
            p.write_text(json.dumps(d, indent=1 if name in ("costs", "sectors", "mechanisms", "policy") else 2,
                                    ensure_ascii=False) + "\n")

    print(f"verified {len(verified)} · unreachable {len(unreachable)} · quote-not-found {len(mismatched)}")
    for name, url in mismatched:
        print(f"QUOTE NOT FOUND  {name}: {url}")
    for name, url in unreachable:
        print(f"unreachable      {name}: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
