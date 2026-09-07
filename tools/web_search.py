#!/usr/bin/env python3
"""Run a plan of web searches from a script and write compact results.

The point is token economy: a research agent handed a digest of titles, URLs
and 140-character snippets starts from candidates instead of spending its own
context discovering them, and the same digest seeds a second agent for free.
Nothing here is a fact until a page is fetched and read; the digest says where
to look, not what is true (AGENTS.md: a specific figure seen only in a search
summary is synthesized until found in a fetched page).

  python3 tools/web_search.py "Doyon Utilities tariff Fort Wainwright"
  python3 tools/web_search.py --plan data/research/<pass>/plan.json --out data/research/<pass>/seeds

A plan is JSON: {"topics": [{"id": "...", "issue": 9, "context": "what the repo
already knows", "queries": ["...", "..."]}]}. Each topic writes <out>/<id>.json
and the whole plan writes <out>/digest.md, grouped by topic, deduped by URL,
with a per-topic hit count so an empty topic is visible rather than silent.

Backend: DuckDuckGo, the html endpoint first and the lite endpoint when that
one refuses. It needs no key and returns about ten results a page. It
rate-limits bursts (the first run of this tool got two topics in before every
later query came back blocked), so a pause sits between queries, a block waits
out a longer cooldown once, and a topic that still ends with zero hits is
printed as zero rather than recorded as "nothing exists". Bing's keyless RSS
endpoint was tried as a fallback and dropped: it answers a scripted query with
generic pages for the first word, which is worse than no result. `--only`
re-runs a subset of a plan's topics and rebuilds the digest from every topic
file on disk, so a rate-limited run is finished, not repeated. Stdlib only.
"""
import argparse
import html
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
ENDPOINT = "https://html.duckduckgo.com/html/?q="
LITE = "https://lite.duckduckgo.com/lite/?q="
COOLDOWN = 45  # seconds to wait once after a block before giving the query up
RESULT_RE = re.compile(
    r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>.*?'
    r'<a class="result__snippet"[^>]*>(.*?)</a>', re.S)
LITE_RE = re.compile(
    r'<a rel="nofollow" href="([^"]+)" class=[\'"]result-link[\'"]>(.*?)</a>.*?'
    r'<td class=[\'"]result-snippet[\'"]>(.*?)</td>', re.S)
# Hosts whose result is never a primary document for this project.
DENY_HOSTS = {"pinterest.com", "facebook.com", "instagram.com", "tiktok.com", "quora.com"}


def strip(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def search(query: str, timeout: int = 25, endpoint: str = ENDPOINT) -> Optional[List[Dict[str, str]]]:
    """One page of results, or None when the endpoint refused to search."""
    req = urllib.request.Request(endpoint + urllib.parse.quote(query),
                                 headers={"User-Agent": UA})
    try:
        body = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as e:  # noqa: PERF203
        print(f"  unreachable  {type(e).__name__}: {query[:60]}", file=sys.stderr)
        return None
    if "anomaly" in body and "result__a" not in body and "result-link" not in body:
        return None
    return parse(body, endpoint)


def parse(body: str, endpoint: str = ENDPOINT) -> List[Dict[str, str]]:
    """The result rows in one page of either endpoint. Split from search() so the
    parser is testable without the network: a regex that silently stops matching
    would otherwise report every query as empty and look like a quiet web."""
    out = []
    for m in (RESULT_RE.finditer(body) if endpoint == ENDPOINT else LITE_RE.finditer(body)):
        href = m.group(1)
        if "uddg=" in href:
            href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
        host = urllib.parse.urlparse(href).netloc.replace("www.", "")
        if host in DENY_HOSTS:
            continue
        out.append({"title": strip(m.group(2))[:120], "url": href, "host": host,
                    "snippet": strip(m.group(3))[:160]})
    return out


def run_query(query: str, pause: float) -> List[Dict[str, str]]:
    hits = search(query)
    if hits is None:
        hits = search(query, endpoint=LITE)
    if hits is None:
        print(f"  blocked, cooling down {COOLDOWN}s: {query[:60]}", file=sys.stderr)
        time.sleep(COOLDOWN)
        hits = search(query) or search(query, endpoint=LITE)
    time.sleep(pause)
    if hits is None:
        print(f"  blocked      {query[:70]}", file=sys.stderr)
        return []
    if not hits:
        print(f"  empty        {query[:70]}", file=sys.stderr)
    return hits


def run_plan(plan: dict, out_dir: pathlib.Path, per_query: int, pause: float,
             only: Optional[List[str]] = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = [f"# Search digest — {plan.get('title', out_dir.name)}", "",
              "Candidates only: a title, a URL and a snippet. Fetch before citing.", ""]
    for topic in plan["topics"]:
        tfile = out_dir / f"{topic['id']}.json"
        if only and topic["id"] not in only and tfile.exists():
            rows = json.loads(tfile.read_text())["results"]   # keep the earlier run's hits
        else:
            seen, rows = set(), []
            for q in topic["queries"]:
                for h in run_query(q, pause)[:per_query]:
                    if h["url"] in seen:
                        continue
                    seen.add(h["url"])
                    rows.append(dict(h, query=q))
            tfile.write_text(json.dumps(
                {"_meta": {"topic": topic["id"], "issue": topic.get("issue"),
                           "queries": topic["queries"], "hits": len(rows)},
                 "results": rows}, indent=1, ensure_ascii=False) + "\n")
        head = f"## {topic['id']}" + (f" (issue #{topic['issue']})" if topic.get("issue") else "")
        digest += [head, ""]
        if topic.get("context"):
            digest += [f"What the repo already holds: {topic['context']}", ""]
        digest.append(f"{len(rows)} candidates from {len(topic['queries'])} queries.")
        for r in rows:
            digest.append(f"- {r['title']} — {r['url']} — {r['snippet']}")
        digest.append("")
        print(f"{topic['id']}: {len(rows)} candidates")
    (out_dir / "digest.md").write_text("\n".join(digest))
    print(f"wrote {out_dir / 'digest.md'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="*", help="ad-hoc queries; prints results")
    ap.add_argument("--plan", type=pathlib.Path, help="plan JSON (see module docstring)")
    ap.add_argument("--out", type=pathlib.Path, help="output directory for a plan run")
    ap.add_argument("--per-query", type=int, default=8)
    ap.add_argument("--pause", type=float, default=6.0, help="seconds between queries")
    ap.add_argument("--only", nargs="+", metavar="TOPIC_ID",
                    help="re-run only these plan topics; other topics keep their file")
    a = ap.parse_args()
    if a.plan:
        if not a.out:
            ap.error("--plan needs --out")
        run_plan(json.loads(a.plan.read_text()), a.out, a.per_query, a.pause, a.only)
        return 0
    if not a.query:
        ap.error("give a query or --plan")
    for q in a.query:
        hits = run_query(q, a.pause)
        print(f"{q!r}: {len(hits)} results")
        for h in hits[:a.per_query]:
            print(f"  - {h['title'][:80]}\n    {h['url']}\n    {h['snippet'][:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
