#!/usr/bin/env python3
"""Generate the agent- and crawler-facing surface from the data.

Writes site/llms.txt, site/sitemap.xml, site/robots.txt, and the JSON-LD block
inside site/index.html's generated:meta markers. Everything with a number or a
date in it is derived from data/*.json, so a stale artifact is a test failure
rather than something a reader discovers.

The site is a GitHub Pages *project* site, so robots.txt at the subpath is not
read by crawlers that only fetch the domain root. It ships for direct-fetch
tools and to document intent; discovery leans on the meta tags, the JSON-LD and
the sitemap.
"""
import json
import pathlib
import re
import sys
from typing import Any, Dict, List

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, SITE = ROOT / "data", ROOT / "site"
BASE = "https://pranava0x0.github.io/microreactors/"

MARK_OPEN, MARK_CLOSE = "<!-- generated:meta -->", "<!-- /generated:meta -->"


# Panels whose standfirst is rendered by app.js into an empty <p>, so the markup
# has nothing to read. Each names the data file and _meta key app.js draws from,
# which is the same string a reader sees.
JS_LEDE = {
    "why": ("arguments", "what_this_is"),
    "news": ("news", "what_this_is"),
    "market": ("mechanisms", "intro"),
}


def text(html_fragment: str) -> str:
    """Markup to prose. Strips the [?] citation placeholders app.js fills in at
    runtime, which otherwise ship into llms.txt as literal question marks."""
    t = re.sub(r"<a class=\"cite\".*?</a>", "", html_fragment, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).replace("[?]", "").strip()


def panels(html: str) -> List[Dict[str, str]]:
    """Tab id, label and the panel's own heading and standfirst, read from the
    markup rather than re-typed here: a tab renamed or reordered in index.html
    must not need a second edit in this file to stay described correctly."""
    order = re.findall(r'<button class="tab"[^>]*data-panel="([\w-]+)"[^>]*>(.*?)</button>', html)
    out = []
    for pid, label in order:
        m = re.search(r'<section id="%s".*?<h2>(.*?)</h2>(.*?)</div>' % pid, html, re.S)
        head = text(m.group(1)) if m else ""
        lede = ""
        if pid in JS_LEDE:
            fname, key = JS_LEDE[pid]
            d = json.loads((DATA / f"{fname}.json").read_text())
            lede = d.get("_meta", {}).get(key) or d.get(key) or ""
            assert isinstance(lede, str) and lede, f"{fname}.json has no usable {key}"
        elif m:
            pm = re.search(r'<p class="prose"[^>]*>(.*?)</p>', m.group(2), re.S)
            if pm:
                lede = text(pm.group(1))
        out.append({"id": pid, "label": label.strip(), "head": head, "lede": lede})
    return out


def main() -> int:
    bundle = json.loads((SITE / "data.js").read_text().split("window.MR=", 1)[1].rsplit(";", 1)[0])
    s: Dict[str, Any] = bundle["summary"]
    html = (SITE / "index.html").read_text()
    ps = panels(html)
    desc = re.search(r'<meta name="description" content="([^"]+)"', html).group(1)

    # --- llms.txt ------------------------------------------------------------
    lines = ["# Microreactor Opportunity Map", "",
             f"> {desc}", "",
             f"Captured {s['built']}. Every figure below is derived from the JSON in "
             f"`data/`, and every claim carrying a number cites a source; "
             f"{s['source_count']} distinct sources are registered, each with one "
             f"stable number reused everywhere it is cited.", "",
             "## How far the market has moved", ""]
    facts = [
        f"{s['binding_rows']} of {s['opportunities']} tracked buyers hold a binding instrument "
        f"(a signed contract, a filed application or an executed award); the rest are "
        f"selections, letters of intent and memoranda.",
        f"{s['filing_rows']} of {s['opportunities']} have a utility filing on record.",
        f"{s['milestones_2026']} vendor milestones were hit in 2026 and "
        f"{s['reactors_critical_2026']} test reactors reached criticality.",
        f"The largest single preorder is {s['units_largest_preorder']} units; the earliest "
        f"stated delivery target is {s['first_delivery_year']}.",
        f"No microreactor has sold power, so every cost figure on the site is an estimate "
        f"with its basis stated. {s['benchmarks']} real-world benchmark rows carry what "
        f"power actually costs today, {s['benchmarks_priced']} of them with a price, capex "
        f"or displaced-cost number.",
        f"{s['instruments']} policy and market instruments are written up, "
        f"{s['sector_count']} demand sectors with {s['load_types']} load profiles "
        f"({s['cited_loads']} cited).",
    ]
    lines += [f"- {f}" for f in facts] + ["", "## Sections", ""]
    for p in ps:
        lines.append(f"- [{p['label']}]({BASE}#{p['id']}): {p['head']}."
                     + (f" {p['lede']}" if p["lede"] else ""))
    lines += ["", "## Data", "",
              "The site is static and its data is committed as JSON. Each file carries a "
              "`_meta` block naming what it is and when it was captured.", ""]
    src = "https://github.com/pranava0x0/microreactors/blob/main/data/"
    for f in sorted(p.stem for p in DATA.glob("*.json")):
        lines.append(f"- [{f}.json]({src}{f}.json)")
    lines += ["", "## What is missing", "",
              "The site publishes its own gaps rather than implying coverage it does not have.", ""]
    for g in bundle["gaps"]["next_pass"]:
        lines.append(f"- **{g['target']}** — {g['why']} {g['why_search_failed']}")
    lines.append("")
    (SITE / "llms.txt").write_text("\n".join(lines))

    # --- sitemap.xml ---------------------------------------------------------
    urls = "".join(
        f"  <url>\n    <loc>{BASE}#{p['id']}</loc>\n"
        f"    <lastmod>{s['built']}</lastmod>\n  </url>\n" for p in ps)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url>\n    <loc>{BASE}</loc>\n    <lastmod>{s['built']}</lastmod>\n  </url>\n"
        f"{urls}</urlset>\n")

    # --- robots.txt ----------------------------------------------------------
    (SITE / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {BASE}sitemap.xml\n")

    # --- JSON-LD, injected between markers in index.html ---------------------
    ld = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Microreactor Opportunity Map",
        "description": desc,
        "url": BASE,
        "dateModified": s["built"],
        "isAccessibleForFree": True,
        "creator": {"@type": "Person", "name": "Pranava Raparla"},
        "keywords": [p["label"] for p in ps],
        "variableMeasured": [
            {"@type": "PropertyValue", "name": "tracked buyers", "value": s["opportunities"]},
            {"@type": "PropertyValue", "name": "buyers holding a binding instrument",
             "value": s["binding_rows"]},
            {"@type": "PropertyValue", "name": "registered sources", "value": s["source_count"]},
            {"@type": "PropertyValue", "name": "priced real-world benchmarks",
             "value": s["benchmarks_priced"]},
        ],
        "distribution": [{
            "@type": "DataDownload", "encodingFormat": "application/json",
            "contentUrl": f"{src}{f}.json"} for f in sorted(p.stem for p in DATA.glob("*.json"))],
    }
    block = (MARK_OPEN + '\n<script type="application/ld+json">\n'
             + json.dumps(ld, indent=1, ensure_ascii=False) + "\n</script>\n" + MARK_CLOSE)
    if MARK_OPEN not in html:
        print("index.html has no generated:meta markers", file=sys.stderr)
        return 1
    html = re.sub(re.escape(MARK_OPEN) + r".*?" + re.escape(MARK_CLOSE), lambda _: block,
                  html, flags=re.S)
    (SITE / "index.html").write_text(html)

    print(f"site/llms.txt        {(SITE / 'llms.txt').stat().st_size:,} bytes")
    print(f"site/sitemap.xml     {(SITE / 'sitemap.xml').stat().st_size:,} bytes  "
          f"({len(ps) + 1} urls)")
    print(f"site/robots.txt      {(SITE / 'robots.txt').stat().st_size:,} bytes")
    print(f"index.html JSON-LD   {len(block):,} bytes  (dateModified {s['built']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
