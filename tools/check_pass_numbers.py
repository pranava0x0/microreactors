#!/usr/bin/env python3
"""Check that every number in a research pass's prose appears on a page it cites.

  python3 tools/check_pass_numbers.py data/research/2026-10-18-refresh

The quote gate (verify_pass_quotes.py) proves the quoted span is on the page; it
says nothing about the sentence around it. On 2026-09-26 a by-hand number check
found 22 records whose prose carried figures no cited page contained, all of
which had passed the quote gate. This automates that check for `items`,
`checks` (the correction), `dockets` and `applications`.

For each record: fetch every cited url (the same fetcher as the quote gate),
extract numbers from the prose fields, and report any number found on none of
the pages. Years and small ordinals (<= 31) are skipped: they are dates, and a
date's month/day form rarely matches the page's. A record whose pages were all
unreachable is reported as such, never as clean.

Exit 1 if any record has an unsupported number. Stdlib (+ pypdf/PyMuPDF if present).
"""
import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from verify_pass_quotes import norm, page_text  # noqa: E402  (one fetcher for both gates)

PROSE = {"items": ("headline", "what_happened", "why_it_matters"),
         "checks": ("correction",),
         "dockets": ("what_it_says",),
         "applications": ("what_it_says", "power_class", "timeline")}
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers(text: str) -> set:
    out = set()
    for m in NUM.findall(text or ""):
        n = m.replace(",", "").rstrip(".")
        if not n:
            continue
        v = float(n)
        if v <= 31 and "." not in n:
            continue
        if 1900 <= v <= 2100 and "." not in n:
            continue
        out.add(n)
    return out


def on_page(n: str, text: str) -> bool:
    flat = text.replace(",", "")
    return re.search(rf"(?<![\d.]){re.escape(n)}(?![\d])", flat) is not None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pass_dir", type=pathlib.Path)
    args = ap.parse_args()
    cache, bad, unreachable, ok = {}, 0, 0, 0
    for f in sorted(args.pass_dir.glob("*.json")):
        doc = json.loads(f.read_text())
        for key, fields in PROSE.items():
            for rec in doc.get(key, []):
                if key == "checks" and rec.get("verdict") not in ("outdated", "wrong"):
                    continue
                nums = set().union(*(numbers(str(rec.get(k, ""))) for k in fields))
                if not nums:
                    continue
                pages = []
                for s in rec.get("sources", []):
                    url = s.get("url", "")
                    if url not in cache:
                        text, _err = page_text(url)
                        cache[url] = norm(text) if text else ""
                    if cache[url]:
                        pages.append(cache[url])
                tag = f"{f.name}[{rec.get('id')}]"
                if not pages:
                    unreachable += 1
                    print(f"UNREACHABLE  {tag}: no cited page could be read; check by hand")
                    continue
                missing = sorted(n for n in nums if not any(on_page(n, p) for p in pages))
                if missing:
                    bad += 1
                    print(f"UNSUPPORTED  {tag}: {', '.join(missing)}")
                else:
                    ok += 1
    print(f"\n{ok} supported · {bad} unsupported · {unreachable} unreachable")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
