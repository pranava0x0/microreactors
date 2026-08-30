#!/usr/bin/env python3
"""Watch structured sources for microreactor news and report what is new.

  python3 tools/news_watch.py                    # candidates since the newest item in data/news.json
  python3 tools/news_watch.py --since 2026-06-01
  python3 tools/news_watch.py --json out.json    # machine-readable, for a research agent to write up
  python3 tools/news_watch.py --check-feeds      # which sources are reachable today

This does NOT write data/news.json. It produces CANDIDATES. Turning a headline
into a record means reading the article, judging whether the instrument is
binding, and quoting a verbatim span — none of which a feed parser can do. What
it removes is the expensive half: finding out that something happened.

Two sources, chosen because both are machine-readable and neither needs a key:

  RSS/Atom feeds from six trade and government publishers. Four more were tried
  and dropped: ANS returns 404 on its advertised feed path, and NRC, Radiant and
  Oklo return 403 to non-browser clients. They are listed in BLOCKED so the next
  person does not re-discover them.

  SEC EDGAR full-text search. Higher signal than any feed, because a company
  saying something in a filing is bound by securities law and a company saying it
  in a press release is not. 151 filings mentioned "microreactor" at the time of
  writing.

Every candidate carries the URL it came from, so the write-up step starts from a
document rather than a summary. Stdlib only.
"""
import argparse
import html
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, List

ROOT = pathlib.Path(__file__).resolve().parent.parent
NEWS = ROOT / "data" / "news.json"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
SEC_UA = "microreactors-research pranava.raparla@gmail.com"

FEEDS: Dict[str, str] = {
    "World Nuclear News": "https://www.world-nuclear-news.org/rss",
    "DOE Nuclear Energy": "https://www.energy.gov/ne/rss.xml",
    "POWER Magazine": "https://www.powermag.com/feed/",
    "Neutron Bytes": "https://neutronbytes.com/feed/",
    "Utility Dive": "https://www.utilitydive.com/feeds/news/",
    "Data Center Dynamics": "https://www.datacenterdynamics.com/en/rss/",
}
# Probed 2026-08-30 and unusable from a script. Recorded so the next run does not
# spend the same minutes rediscovering it.
BLOCKED = {
    "ANS Nuclear Newswire": "404 on https://www.ans.org/news/rss/ — no feed at the advertised path",
    "NRC press releases": "403 to non-browser clients",
    "Radiant newsroom": "403 to non-browser clients",
    "Oklo investor relations": "403 to non-browser clients",
}

# A headline has to carry one of these to be a candidate. Deliberately narrow:
# the point is to miss the general-nuclear firehose, not to catch it.
TERMS = re.compile(
    r"\bmicroreactor|micro-reactor|\bSMR\b|small modular|"
    r"Antares|Radiant|Oklo|X-energy|Kairos|BWXT|eVinci|Westinghouse|"
    r"Aalo|Valar|Deep Fission|Last Energy|NANO Nuclear|TerraPower|Zeno Power|"
    r"Standard Nuclear|General Atomics|"
    r"\bJanus\b|ANPI|HALEU|TRISO|Part 53|Part 57|reactor pilot", re.I)


def get(url: str, ua: str = UA, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def text(el, *names: str) -> str:
    for n in names:
        found = el.find(n)
        if found is not None and found.text:
            return html.unescape(found.text).strip()
    return ""


def parse_feed(name: str, url: str) -> List[dict]:
    try:
        raw = get(url)
    except Exception as e:  # noqa: BLE001 — report, never swallow
        print(f"  unreachable  {name}: {type(e).__name__}", file=sys.stderr)
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print(f"  unparseable  {name}: {e}", file=sys.stderr)
        return []
    out = []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        title = text(it, "title", "a:title")
        link = text(it, "link", "a:link")
        if not link:
            le = it.find("a:link", ns)
            link = le.get("href", "") if le is not None else ""
        date = text(it, "pubDate", "published", "updated", "a:published", "a:updated")
        if title:
            out.append({"source": name, "title": title, "url": link, "date_raw": date})
    return out


def parse_edgar(since: str) -> List[dict]:
    url = ('https://efts.sec.gov/LATEST/search-index?q=%22microreactor%22'
           f'&dateRange=custom&startdt={since}&enddt=2099-12-31')
    try:
        d = json.loads(get(url, ua=SEC_UA))
    except Exception as e:  # noqa: BLE001
        print(f"  unreachable  SEC EDGAR: {type(e).__name__}", file=sys.stderr)
        return []
    out = []
    for h in d.get("hits", {}).get("hits", []):
        s = h.get("_source", {})
        names = s.get("display_names") or ["?"]
        adsh = (h.get("_id", "") or "").split(":")[0].replace("-", "")
        cik = (s.get("ciks") or [""])[0]
        out.append({
            "source": "SEC EDGAR full-text",
            "title": f"{names[0]} — {s.get('root_form', s.get('form_type', 'filing'))}",
            "url": (f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{adsh}/"
                    if cik and adsh else "https://efts.sec.gov/LATEST/search-index?q=microreactor"),
            "date_raw": s.get("file_date", ""),
        })
    return out


ISO = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")
MONTHS = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def norm_date(s: str) -> str:
    m = ISO.search(s)
    if m:
        return m.group(0)
    m = re.search(r"(\d{1,2})\s+([A-Z][a-z]{2})\w*\s+(20\d{2})", s)
    if m:
        return f"{m.group(3)}-{MONTHS.get(m.group(2), 1):02d}-{int(m.group(1)):02d}"
    return ""


def known_urls() -> set:
    if not NEWS.exists():
        return set()
    d = json.loads(NEWS.read_text())
    urls = set()
    for it in d.get("items", []):
        for s in it.get("sources", []):
            if s.get("url"):
                urls.add(s["url"])
    return urls


def newest_known() -> str:
    if not NEWS.exists():
        return "2026-01-01"
    d = json.loads(NEWS.read_text())
    dates = [i["date"] for i in d.get("items", []) if i.get("date")]
    return max(dates) if dates else "2026-01-01"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--check-feeds", action="store_true")
    a = ap.parse_args()

    if a.check_feeds:
        print(f"{len(FEEDS)} feed(s) in the registry:")
        for n, u in FEEDS.items():
            items = parse_feed(n, u)
            print(f"  {'ok  ' if items else 'DEAD'} {n:<24} {len(items):>3} items  {u}")
        print(f"\n{len(BLOCKED)} source(s) known unusable from a script:")
        for n, why in BLOCKED.items():
            print(f"  --   {n:<24} {why}")
        return 0

    since = a.since or newest_known()
    seen = known_urls()
    rows: List[dict] = []
    for n, u in FEEDS.items():
        rows.extend(parse_feed(n, u))
    rows.extend(parse_edgar(since))

    cands = []
    for r in rows:
        d = norm_date(r["date_raw"])
        if d and d < since:
            continue
        if r["url"] in seen:
            continue
        if r["source"] != "SEC EDGAR full-text" and not TERMS.search(r["title"]):
            continue
        cands.append({"date": d, "source": r["source"], "title": r["title"], "url": r["url"]})
    cands.sort(key=lambda c: (c["date"] or "0000", c["source"]), reverse=True)

    print(f"scanned {len(FEEDS)} feed(s) + SEC EDGAR · {len(rows)} raw item(s) · "
          f"since {since} · {len(seen)} url(s) already in data/news.json")
    print(f"{len(cands)} candidate(s) not yet written up\n")
    for c in cands[:60]:
        print(f"  {c['date'] or '(undated)':<12} {c['source']:<22} {c['title'][:70]}")
        print(f"               {c['url'][:110]}")
    if len(cands) > 60:
        print(f"\n  ... and {len(cands) - 60} more (use --json for the full list)")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(
            {"_meta": {"since": since, "feeds": len(FEEDS), "raw_items": len(rows),
                       "blocked": BLOCKED}, "candidates": cands}, indent=2, ensure_ascii=False) + "\n")
        print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
