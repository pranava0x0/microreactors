#!/usr/bin/env python3
"""Replace quotes that do not appear in the cached source with ones that do.

Research agents return quotes that are *nearly* verbatim: the right sentence with
an em-dash normalised, a thousands separator dropped, or two fields joined by an
ellipsis. The claim is sound but the quote-lock gate cannot confirm it, and a
citation that cannot be confirmed is worth little.

For each failing source this finds the longest contiguous run of the quote's own
words that IS present in the cached text, and — only when that run is long enough
to be unmistakably the same passage — narrows the quote to it. The result is
always a verbatim span of the cached bytes, never an invented one.

Anything below the threshold is reported for a human, never rewritten: a quote
with little overlap is a different problem (wrong page, JS shell, or a figure
that simply is not there) and silently trimming it would hide that.

  python3 tools/repair_quotes.py data/research/deep-2026-08-24            # dry run
  python3 tools/repair_quotes.py data/research/deep-2026-08-24 --apply

Operates on the RESEARCH files, which are the source of truth; re-run
tools/merge_research.py afterwards. Stdlib plus PyMuPDF for PDFs, as elsewhere.
"""
import argparse
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
INDEX = ROOT / "data" / "research" / "source_index.json"
MIN_WORDS = 6      # shorter than this is not a citation, it is a coincidence
MIN_RATIO = 0.55   # of the original quote's words

norm = lambda t: re.sub(r"\s+", " ", t).strip()


def cached_text(row: dict) -> str:
    p = CACHE / row["cache"]
    if not p.exists():
        return ""
    if row.get("content_type", "").startswith("application/pdf"):
        import fitz
        with fitz.open(p) as d:
            return norm("\n".join(pg.get_text() for pg in d))
    raw = p.read_bytes().decode("utf-8", "replace")
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return norm(html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def longest_present_run(quote: str, text: str) -> str:
    """Longest contiguous run of quote words that appears verbatim in text."""
    words = quote.split()
    best = ""
    for i in range(len(words)):
        for j in range(len(words), i, -1):
            if j - i <= len(best.split()):
                break
            cand = " ".join(words[i:j])
            if cand in text:
                best = cand
                break
    return best


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pass_dir", type=pathlib.Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="file names to leave alone — use for research files a background "
                         "agent is still appending to, since two writers corrupt each other")
    a = ap.parse_args()
    pass_dir = a.pass_dir if a.pass_dir.is_absolute() else ROOT / a.pass_dir

    index = {r["url"]: r for r in json.loads(INDEX.read_text())["sources"]}
    texts: dict = {}
    repaired = manual = ok = uncached = 0

    for path in sorted(pass_dir.glob("*.json")):
        if path.name in a.exclude:
            print(f"skip   {path.name} (in flight)")
            continue
        doc = json.loads(path.read_text())
        recs = doc.get("mechanisms") or doc.get("cases") or []
        changed = False
        for rec in recs:
            for s in rec.get("sources") or []:
                row = index.get(s.get("url", ""))
                if not row:
                    uncached += 1
                    continue
                if s["url"] not in texts:
                    texts[s["url"]] = cached_text(row)
                text = texts[s["url"]]
                if not text:
                    uncached += 1
                    continue
                q = norm(s.get("quote", ""))
                if q and q in text:
                    ok += 1
                    continue
                run = longest_present_run(q, text)
                n, total = len(run.split()), len(q.split())
                if n >= MIN_WORDS and total and n / total >= MIN_RATIO:
                    print(f"REPAIR {path.name} [{rec['id']}] {n}/{total} words")
                    print(f"   was: {q[:100]}")
                    print(f"   now: {run[:100]}")
                    if a.apply:
                        s["quote"] = run
                        changed = True
                    repaired += 1
                else:
                    print(f"MANUAL {path.name} [{rec['id']}] best run {n}/{total} words "
                          f"— {s['url'][:70]}")
                    print(f"   quote: {q[:100]}")
                    manual += 1
        if changed and a.apply:
            path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")

    print(f"\n{ok} already verbatim · {repaired} repairable · {manual} need a human · "
          f"{uncached} not cached")
    if a.apply:
        print("applied — now re-run tools/merge_research.py and tools/verify_quotes.py --cache")
    return 0


if __name__ == "__main__":
    sys.exit(main())
