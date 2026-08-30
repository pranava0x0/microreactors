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

  python3 tools/repair_quotes.py --data                                    # dry run
  python3 tools/repair_quotes.py --data --apply

Operates on the RESEARCH files, which are the source of truth; re-run
tools/merge_research.py afterwards. --data instead walks the hand-authored
datasets in data/ (sectors, mechanisms, policy and the rest), which have no pass
behind them. Twelve of their quotes failed the moment a cache sweep made their
sources reachable for the first time - the gate had been passing over them, not
on them. Stdlib plus PyMuPDF for PDFs, as elsewhere.
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

# One normaliser for BOTH sides of every comparison, imported from the gate.
# This was a local lambda that collapsed whitespace and nothing else, while the
# gate casefolds and folds smart quotes and dashes. Normalising only one side
# made 81 sound quotes look broken and would have "repaired" them into shorter
# spans for no reason.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import verify_quotes as _vq  # noqa: E402
norm = _vq.norm


def cached_text(row: dict) -> str:
    """Extract exactly the way tools/verify_quotes.py does.

    This used PyMuPDF while the gate used pypdf. The two disagree on real PDFs -
    ligatures, soft hyphens and spacing around numerals - so a repair driven by
    one could produce a span the other cannot find, and could "fix" a quote that
    was already passing. There is now one extractor, imported from the gate, so a
    repair is true by construction rather than by luck.
    """
    p = CACHE / row["cache"]
    if not p.exists():
        return ""
    raw = p.read_bytes()
    if raw[:4] == b"%PDF":
        try:
            from pypdf import PdfReader
            import io as _io
            return _vq.norm(" ".join(pg.extract_text() or ""
                                     for pg in PdfReader(_io.BytesIO(raw)).pages))
        except Exception:
            return ""
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    return _vq.norm(re.sub(r"<[^>]+>", " ", text))


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
    ap.add_argument("pass_dir", type=pathlib.Path, nargs="?")
    ap.add_argument("--data", action="store_true",
                    help="walk data/*.json instead of a research pass")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="file names to leave alone — use for research files a background "
                         "agent is still appending to, since two writers corrupt each other")
    a = ap.parse_args()
    if not a.data and a.pass_dir is None:
        ap.error("give a pass_dir or --data")
    pass_dir = None if a.data else (a.pass_dir if a.pass_dir.is_absolute() else ROOT / a.pass_dir)

    index = {r["url"]: r for r in json.loads(INDEX.read_text())["sources"]}
    texts: dict = {}
    repaired = manual = ok = uncached = 0

    if a.data:
        import build_data as _bd
        # derived files are excluded: repairing them here would be undone by the
        # next merge, which is the single-source-of-truth rule this repo already
        # learned once on instruments.json.
        DERIVED = {"instruments", "benchmarks", "voices", "news", "gaps"}
        paths = [ROOT / "data" / f"{n}.json" for n in _bd.FILES if n not in DERIVED]
    else:
        paths = sorted(pass_dir.glob("*.json"))
    for path in paths:
        if path.name in a.exclude:
            print(f"skip   {path.name} (in flight)")
            continue
        doc = json.loads(path.read_text())
        if a.data:
            recs = []

            def _collect(n):
                if isinstance(n, dict):
                    if n.get("sources") or n.get("source"):
                        recs.append(n)
                    for v in n.values():
                        _collect(v)
                elif isinstance(n, list):
                    for v in n:
                        _collect(v)
            _collect(doc)
            for r in recs:
                if r.get("source") and not r.get("sources"):
                    r["sources"] = [r["source"]]
        else:
            recs = doc.get("mechanisms") or doc.get("cases") or []
        changed = False
        for rec in recs:
            for s in rec.get("sources") or []:
                if not isinstance(s, dict):
                    continue
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
                # A source with no quote is not a failure: plenty of citations here
                # are a link and a label, and only a quoted span makes a lock.
                if not q:
                    continue
                if q in text:
                    ok += 1
                    continue
                run = longest_present_run(q, text)
                n, total = len(run.split()), len(q.split())
                if n >= MIN_WORDS and total and n / total >= MIN_RATIO:
                    rid = rec.get("id") or rec.get("name") or rec.get("scenario") or "?"
                    print(f"REPAIR {path.name} [{str(rid)[:40]}] {n}/{total} words")
                    print(f"   was: {q[:100]}")
                    print(f"   now: {run[:100]}")
                    if a.apply:
                        s["quote"] = run
                        changed = True
                    repaired += 1
                else:
                    rid = rec.get("id") or rec.get("name") or rec.get("scenario") or "?"
                    print(f"MANUAL {path.name} [{str(rid)[:40]}] best run {n}/{total} words "
                          f"— {s['url'][:70]}")
                    print(f"   quote: {q[:100]}")
                    manual += 1
        if changed and a.apply:
            # Match the file's OWN indentation, read from the file rather than
            # guessed from its path. A first version keyed off the directory and
            # would have reformatted every research file, turning a two-line quote
            # fix into a whole-file diff.
            second = path.read_text().split("\n")[1] if "\n" in path.read_text() else " "
            width = len(second) - len(second.lstrip()) or 1
            path.write_text(json.dumps(doc, indent=width, ensure_ascii=False) + "\n")

    print(f"\n{ok} already verbatim · {repaired} repairable · {manual} need a human · "
          f"{uncached} not cached")
    if a.apply:
        print("applied — now re-run tools/merge_research.py and tools/verify_quotes.py --cache")
    return 0


if __name__ == "__main__":
    sys.exit(main())
