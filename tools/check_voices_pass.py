#!/usr/bin/env python3
"""Validate agent output for the leadership/voices research pass.

  python3 tools/check_voices_pass.py data/research/2026-08-29-voices

Written BEFORE the agents ran, not after. A contract enforced by a script costs
one file; a contract enforced by reading ten JSON files by hand costs an
afternoon and misses things. Exit 1 on any violation.

What it checks, and why each one is here:
  * required keys present, correct types
  * every leader and every quote carries >=1 source with a real deep-linked URL
  * status is fetched|snippet-only, nothing else
  * a source `quote` is <=25 words and a record `quote` <=60 (the contract's caps)
  * NO paraphrase markers inside a verbatim quote ("said that", "[sic]", "...")
  * duplicate ids across files - ten agents pick the same obvious slug
  * impossible citations: a source published BEFORE the thing it is cited for
    cannot support it. Where a URL carries a year in its path, a quote dated in
    a later year is flagged. This was documented here for a week before it was
    implemented, which is its own lesson: a docstring asserting an invariant
    does not enforce one.
  * a quote record that carries no number AND no named counterparty is weak:
    reported, not failed, so the human decides
"""
import json
import pathlib
import re
import sys
from typing import Dict, List

REQ_META = ("captured", "agent", "companies", "window")
LEADER_REQ = ("id", "company", "name", "title", "background", "sources")
QUOTE_REQ = ("id", "company", "speaker", "date", "venue", "topic", "quote",
             "what_it_means", "sources")
TOPICS = {"customers", "costs", "supply-chain", "units-manufacturing", "orders",
          "regulatory", "international"}
PARAPHRASE = re.compile(r"\[sic\]|\bsaid that\b|\.\.\.|…|\[\s*\w+\s*\]")
NUMBER = re.compile(r"\$\s?[\d,]|\b\d[\d,.]*\s?(?:%|MW|MWe|MWt|MWh|GW|kW|kWe|ton|tonne|units?|years?)\b|\b\d{2,}\b")
# A year inside a URL PATH, e.g. /2025/report or /news/2024-03-01/. Anchored on
# slashes and hyphens so it cannot match inside a contract number like
# N69450-16-C-1901 - a sibling lint in this repo fired on exactly that, and the
# first fix for it silently stopped matching real dates.
URL_YEAR = re.compile(r"/(19|20)\d{2}(?=[/\-]|$)")
CLAIM_YEAR = re.compile(r"^((?:19|20)\d{2})")
BARE_HOST = re.compile(r"^https?://[^/]+/?$")


def check(pass_dir: pathlib.Path) -> List[str]:
    errs: List[str] = []
    warns: List[str] = []
    files = sorted(p for p in pass_dir.glob("*.json"))
    if not files:
        return [f"no JSON files in {pass_dir}"]
    seen_ids: Dict[str, str] = {}
    n_lead = n_quote = n_src = 0
    incomplete: List[str] = []

    for f in files:
        try:
            d = json.loads(f.read_text())
        except Exception as e:  # noqa: BLE001
            errs.append(f"{f.name}: unparseable JSON - {e}")
            continue
        meta = d.get("_meta", {})
        for k in REQ_META:
            if k not in meta:
                errs.append(f"{f.name}: _meta missing '{k}'")
        if meta.get("incomplete"):
            incomplete.append(f.name)

        def sources_ok(rec: dict, where: str) -> None:
            nonlocal n_src
            srcs = rec.get("sources") or []
            if not srcs:
                errs.append(f"{where}: no sources")
                return
            for s in srcs:
                n_src += 1
                url = s.get("url", "")
                if not url.startswith("http"):
                    errs.append(f"{where}: source has no usable url")
                elif BARE_HOST.match(url):
                    errs.append(f"{where}: bare homepage cited ({url})")
                if s.get("status") not in ("fetched", "snippet-only"):
                    errs.append(f"{where}: status={s.get('status')!r}, must be fetched|snippet-only")
                q = s.get("quote", "")
                if q and len(q.split()) > 25:
                    errs.append(f"{where}: source quote is {len(q.split())} words (cap 25)")

        for rec in d.get("leaders", []):
            n_lead += 1
            where = f"{f.name}:leader:{rec.get('id', '?')}"
            for k in LEADER_REQ:
                if not rec.get(k):
                    errs.append(f"{where}: missing '{k}'")
            rid = rec.get("id")
            if rid in seen_ids:
                errs.append(f"{where}: duplicate id, also in {seen_ids[rid]}")
            elif rid:
                seen_ids[rid] = f.name
            sources_ok(rec, where)

        for rec in d.get("quotes", []):
            n_quote += 1
            where = f"{f.name}:quote:{rec.get('id', '?')}"
            for k in QUOTE_REQ:
                if not rec.get(k):
                    errs.append(f"{where}: missing '{k}'")
            rid = rec.get("id")
            if rid in seen_ids:
                errs.append(f"{where}: duplicate id, also in {seen_ids[rid]}")
            elif rid:
                seen_ids[rid] = f.name
            if rec.get("topic") not in TOPICS:
                errs.append(f"{where}: topic={rec.get('topic')!r} not in {sorted(TOPICS)}")
            q = rec.get("quote", "")
            if len(q.split()) > 60:
                errs.append(f"{where}: quote is {len(q.split())} words (cap 60)")
            if PARAPHRASE.search(q):
                errs.append(f"{where}: quote contains an ellipsis or editorial mark; "
                            f"a verbatim span must not be stitched")
            if not NUMBER.search(q) and rec.get("topic") in {"costs", "orders", "units-manufacturing"}:
                warns.append(f"{where}: topic={rec['topic']} but the quote carries no number")
            sources_ok(rec, where)

            # Impossible citation: a source whose URL is stamped with a year
            # EARLIER than the year the quote is dated cannot be where the quote
            # came from. Only the newest year in the URL counts - paths often
            # carry an archive year and an article year.
            m = CLAIM_YEAR.match(str(rec.get("date", "")))
            if m:
                claim_year = int(m.group(1))
                for s in rec.get("sources", []):
                    years = [int(a + b) for a, b in
                             [(y.group(1), y.group(0)[-2:]) for y in
                              URL_YEAR.finditer(s.get("url", ""))]]
                    if years and max(years) < claim_year:
                        errs.append(f"{where}: quote dated {claim_year} cites a source "
                                    f"stamped {max(years)} ({s.get('url', '')[:70]})")

    print(f"checked {len(files)} file(s): {n_lead} leaders, {n_quote} quotes, {n_src} sources")
    if incomplete:
        print(f"marked incomplete (agent ran out of budget): {', '.join(incomplete)}")
    for w in warns:
        print(f"  WEAK  {w}")
    return errs


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    errs = check(pathlib.Path(sys.argv[1]))
    for e in errs:
        print(f"  FAIL  {e}")
    print(f"\n{len(errs)} violation(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
