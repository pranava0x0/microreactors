#!/usr/bin/env python3
"""Fetch every source in a research pass and confirm its quote is really there.

  python3 tools/verify_pass_quotes.py data/research/2026-08-29-voices
  python3 tools/verify_pass_quotes.py <dir> --only antares-radiant.json

It verifies the DISPLAYED quote - the text a reader sees in quotation marks on
the site - not merely the short evidence span beside it. Those are different
strings, and an earlier version checked only the second: of 107 records, just 16
displayed exactly what had been verified, 75 wrapped it in unchecked text, and 10
were disjoint from it entirely. The gate reported "0 fabricated" over 15% of what
the page renders. A source span that verifies proves the source is real; it does
not make the sentence built around it verbatim.

check_voices_pass.py validates SHAPE: required keys, id collisions, word caps.
It cannot tell whether a quote marked `status: "fetched"` was ever on the page,
and on 2026-08-29 an agent attributed a quote to a POWER article that contains
neither the sentence nor the speaker's surname, on the live page or in cache.
Structure was perfect. The citation was invented.

So this checks the thing that actually matters:

  VERIFIED    the quote appears in the fetched bytes
  SLOPPY      the SUBJECT is on the page but the span was not copied verbatim -
              usually a reconstructed line like "Name - Title" the page never
              wrote that way. The underlying fact is probably sound; the quote
              is not a quote. Re-copy it.
  FABRICATED  the subject's surname does not appear on the page at all. The
              attribution is invented.
  UNREACHABLE the host blocked us or the URL is dead (not the record's fault)
  SNIPPET     declared snippet-only; not checked, by design

The SLOPPY/FABRICATED split is the whole value of this tool. On the run that
prompted it, a first pass reported "7 missing" and read like a 22% fabrication
rate; separating them showed six were bad transcription of real facts and
exactly one was an invented attribution. Those need different responses, and
collapsing them would have libelled five sound records or excused one bad one.

Both FABRICATED and SLOPPY fail the build. The split is a diagnostic, not a
severity: a reconstructed span is still not a quote, and a gate that accepts one
because the page happens to name the speaker is not a quote gate. An earlier
version exited 0 on SLOPPY, which meant "Name - Title" invented punctuation could
pass review as verbatim. UNREACHABLE and SNIPPET do not fail: the first is the
host's fault and the second was declared honestly.

tools/repair_pass_quotes.py fixes SLOPPY automatically by trimming to a subspan
that verifies, or demoting to snippet-only when none does, so failing on it costs
one command rather than an argument.

Exit 1 if any MISSING. Stdlib only.
"""
import argparse
import html
import io
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Dict, List, Tuple

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def norm(s: str) -> str:
    s = html.unescape(s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("‑", "-")
    return re.sub(r"\s+", " ", s).casefold().strip()


def page_text(url: str) -> Tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        return "", f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return "", type(e).__name__
    if raw[:4] == b"%PDF":
        try:
            from pypdf import PdfReader
            return " ".join(p.extract_text() or "" for p in
                            PdfReader(io.BytesIO(raw)).pages), ""
        except Exception as e:  # noqa: BLE001
            return "", f"pdf:{type(e).__name__}"
    t = raw.decode("utf-8", errors="replace")
    t = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", t), ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pass_dir", type=pathlib.Path)
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    files = sorted(a.pass_dir.glob("*.json"))
    if a.only:
        want = {x.strip() for x in a.only.split(",")}
        files = [f for f in files if f.name in want]

    cache: Dict[str, Tuple[str, str]] = {}
    tally = {"VERIFIED": 0, "SLOPPY": 0, "FABRICATED": 0, "DISPLAYED": 0,
             "UNREACHABLE": 0, "SNIPPET": 0, "NOQUOTE": 0}
    sloppy: List[str] = []
    fabricated: List[str] = []
    displayed: List[str] = []
    noquote: List[str] = []

    for f in files:
        d = json.loads(f.read_text())
        recs = [("leader", r) for r in d.get("leaders", [])] + \
               [("quote", r) for r in d.get("quotes", [])]
        for kind, rec in recs:
            where = f"{f.name}:{kind}:{rec.get('id', '?')}"
            # The record's OWN quote is what the site renders, so it is the string
            # that has to be verbatim. Checked against every fetched source: one
            # of them must contain it whole.
            if kind == "quote" and rec.get("quote"):
                fetched = [s for s in rec.get("sources", [])
                           if s.get("status") == "fetched" and s.get("url")]
                hit = reachable = False
                for s in fetched:
                    if s["url"] not in cache:
                        cache[s["url"]] = page_text(s["url"])
                    text, err = cache[s["url"]]
                    if err:
                        continue
                    reachable = True
                    if norm(rec["quote"]) in norm(text):
                        hit = True
                        break
                if fetched and reachable and not hit:
                    tally["DISPLAYED"] += 1
                    displayed.append(
                        f"{where}\n      displayed: {rec['quote'][:110]}\n"
                        f"      not found whole in any fetched source it cites")
            for s in rec.get("sources", []):
                url, q = s.get("url", ""), s.get("quote", "")
                if s.get("status") == "snippet-only":
                    tally["SNIPPET"] += 1
                    continue
                if not q:
                    # A "fetched" claim with no span is an unfalsifiable citation:
                    # it asserts the page was read and leaves nothing to check.
                    tally["NOQUOTE"] += 1
                    noquote.append(f"{where}  ({url[:80]})")
                    continue
                if url not in cache:
                    cache[url] = page_text(url)
                text, err = cache[url]
                if err:
                    tally["UNREACHABLE"] += 1
                    continue
                if norm(q) in norm(text):
                    tally["VERIFIED"] += 1
                    continue
                # The span is absent. Is the SUBJECT there? A leader record's
                # subject is the person; a quote record's is the speaker. If the
                # surname is on the page, this is bad transcription of a real
                # fact. If it is not, the attribution was invented.
                subject = rec.get("name") or rec.get("speaker") or ""
                surname = subject.split()[-1] if subject.split() else ""
                on_page = bool(surname) and norm(surname) in norm(text)
                line = (f"{where}\n      subject: {subject or '(none)'}\n"
                        f"      quote:   {q[:96]}\n      url:     {url}")
                if on_page:
                    tally["SLOPPY"] += 1
                    sloppy.append(line)
                else:
                    tally["FABRICATED"] += 1
                    fabricated.append(line)

    print(f"checked {len(files)} file(s), {len(cache)} distinct URL(s) fetched\n")
    for m in fabricated:
        print(f"  FABRICATED  {m}")
    for m in displayed:
        print(f"  DISPLAYED   {m}")
    for m in sloppy:
        print(f"  SLOPPY      {m}")
    for m in noquote:
        print(f"  NOQUOTE     {m}  (fetched, but nothing to check)")
    if fabricated or sloppy:
        print()
    print("  ".join(f"{k.lower()} {v}" for k, v in tally.items()))
    print(f"\n{len(fabricated)} invented attribution(s), "
          f"{len(displayed)} displayed quote(s) not verbatim in their source, "
          f"{len(sloppy)} span(s) not copied verbatim, "
          f"{len(noquote)} fetched source(s) with nothing to check")
    if (sloppy or noquote) and not (fabricated or displayed):
        print("run: python3 tools/repair_pass_quotes.py <pass-dir>")
    return 1 if (fabricated or sloppy or displayed or noquote) else 0


if __name__ == "__main__":
    sys.exit(main())
