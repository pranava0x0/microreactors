#!/usr/bin/env python3
"""Bundle data/*.json into site/data.js as window.MR.

Inlined rather than fetched so the site works from file://, GitHub Pages, or
any static host with no server and no CORS story.

Deterministic: the "built" stamp derives from the data files' own _meta.captured
dates (max), never from the wall clock, so rebuilding unchanged data yields
byte-identical output and CI can enforce that site/data.js is in sync.
"""
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, SITE = ROOT / "data", ROOT / "site"

FILES = ["opportunities", "vendors", "costs", "benchmarks", "sectors", "mechanisms", "policy",
         "instruments", "deployment_sites", "voices", "arguments", "news", "gaps", "strategy",
         "regions", "dockets"]

# Datasets pulled out of the main bundle and fetched when their sub-tab opens.
# The test is that no panel needs one to draw its first screen. `benchmarks` used
# to stay eager because Costs and Applications both read it; Applications only
# ever wanted a per-load count, which `load_cases` above now precomputes, so the
# whole 302 KB payload is Costs' "Price to beat" sub-tab alone. `sources_index`
# is derived rather than a file in FILES, which the split handles fine - it pops
# any top-level key. Everything here still ships in site/data-<name>.js and is
# still counted in the citation register, which is built before the split.
# strategy is read by two sub-tabs on two panels (Costs "What wins", Deals
# "Prospects"); neither needs it for a first screen, and loadLazy hands both the
# same promise, so it ships once and arrives when either opens.
# regions (2026-09-26) is read only by Applications > Regions; mechanisms only by
# Rules > Deal design and deployment_sites only by Deals > Sites (their counts
# ride in `summary`).
LAZY = ["instruments", "voices", "news", "benchmarks", "sources_index", "strategy", "regions",
        "mechanisms", "deployment_sites", "dockets"]

# How many of the newest news items ship in the eager bundle for the front page.
HEADLINES = 8

# Citation numbering walks the data in the order the tabs render it, so [1] is
# the first source a reader meets. One number per URL, reused everywhere that
# URL is cited: a chip's number is a stable address into the Sources register,
# never a per-row counter that restarts.
# benchmarks render on the Costs tab and instruments on the Policy tab, so each sits
# beside the dataset it shares a tab with.
CITE_ORDER = ["opportunities", "costs", "benchmarks", "vendors", "sectors", "mechanisms",
              "policy", "instruments", "deployment_sites", "voices", "arguments", "news", "gaps",
              # last on purpose: strategy restates rows the files above already cite, so
              # walking it last keeps every existing chip number where it was.
              "strategy",
              # files added later append here, for the same reason.
              "regions", "dockets"]

# Dict identity fields, in priority order, used as the "cited by" context label
# for any source found beneath that dict.
IDENT_KEYS = ("name", "scenario", "alternative", "target", "question", "label", "sector")


def collect_sources(node: Any, ctx: str, out: List[Tuple[str, str, str, str]]) -> None:
    """Walk the bundle; record every {label, url} source dict with its context
    and fetch status ('' when unrecorded, which older rows treat as fetched)."""
    if isinstance(node, dict):
        url = node.get("url")
        if isinstance(url, str) and url.startswith("http") and isinstance(node.get("label"), str):
            out.append((node["label"], url, ctx, node.get("status", "")))
            return  # a source dict is a leaf; its own label is not a context
        ident: str = ctx
        for k in IDENT_KEYS:
            v = node.get(k)
            if isinstance(v, str) and v:
                ident = v
                break
        for v in node.values():
            collect_sources(v, ident, out)
    elif isinstance(node, list):
        for v in node:
            collect_sources(v, ctx, out)


def sources_index(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    assert sorted(CITE_ORDER) == sorted(FILES), "CITE_ORDER and FILES cover different data files"
    found: List[Tuple[str, str, str, str]] = []
    for name in CITE_ORDER:
        collect_sources(bundle[name], name, found)
    by_url: Dict[str, Dict[str, Any]] = {}
    for label, url, ctx, status in found:
        row = by_url.setdefault(url, {"n": len(by_url) + 1, "url": url, "label": label,
                                      "host": urlparse(url).netloc.replace("www.", ""),
                                      "uses": [], "statuses": []})
        if ctx not in row["uses"]:
            row["uses"].append(ctx)
        row["statuses"].append(status)
    rows = sorted(by_url.values(), key=lambda r: r["n"])
    for r in rows:
        # A URL is snippet-only for the register only if NO use ever read it.
        r["snippet"] = all(s == "snippet-only" for s in r.pop("statuses"))
    return rows


def captured_date(bundle: Dict[str, Any]) -> str:
    dates = []
    for name in FILES:
        meta = bundle[name].get("_meta", {})
        c = meta.get("captured")
        if isinstance(c, str) and c:
            dates.append(c)
    if not dates:
        print("no _meta.captured date in any data file", file=sys.stderr)
        sys.exit(1)
    return max(dates)


def priced(record: Dict[str, Any]) -> bool:
    """A benchmark case counts as priced when it carries a number you could
    compare a reactor against. A capacity figure or a filing is real evidence,
    but calling a row "priced" without a price, capex or displaced-cost number
    overclaims. One definition, read by the headline stat and by the load index
    below, because two copies of this test drifted apart once already."""
    return bool(record.get("price") or record.get("capex") or record.get("displaced"))


def main() -> int:
    bundle: Dict[str, Any] = {}
    for name in FILES:
        p = DATA / f"{name}.json"
        if not p.exists():
            print(f"missing {p}", file=sys.stderr)
            return 1
        bundle[name] = json.loads(p.read_text())

    # Derived headline figures — computed, never hand-typed, so they cannot
    # drift away from the data they summarise.
    opps = bundle["opportunities"]["opportunities"]
    vendors = bundle["vendors"]["vendors"]
    cov = {c["field"]: c for c in bundle["gaps"]["field_coverage"]}
    reg = sources_index(bundle)
    loads = [l for s in bundle["sectors"]["sectors"] for l in s["loads"]]
    # How many priced cases back each load label. The Applications tab only ever
    # rendered this count and a link to the Costs tab, so shipping it here lets the
    # 302 KB benchmarks payload leave the eager bundle entirely.
    load_cases: Dict[str, int] = {}
    for bsec in bundle["benchmarks"]["sectors"]:
        for r in bsec["records"]:
            if not priced(r):
                continue
            for label in r.get("load", []):
                load_cases[label] = load_cases.get(label, 0) + 1
    bundle["load_cases"] = load_cases

    # News reads newest-first everywhere. The file is not kept in order by hand
    # (a 2026-08-17 item sat above 2026-09-04 and the front page promoted it over
    # three newer stories), so the order is imposed here, once.
    bundle["news"]["items"] = sorted(bundle["news"]["items"],
                                     key=lambda it: (it.get("date", ""), it.get("id", "")),
                                     reverse=True)
    # The front page draws from these, so the landing tab never waits on the lazy
    # news payload.
    bundle["headlines"] = [{k: it[k] for k in ("id", "date", "headline", "category", "binding",
                                                "what_happened", "sources") if k in it}
                           for it in bundle["news"]["items"][:HEADLINES]]
    # Applications > Overview: the buyer segments from strategy.json, ranked by the
    # cost rung at which a reactor wins them. The strategy payload stays lazy; this
    # is the slice the overview needs.
    strat = bundle["strategy"]
    rung_ids = [r["id"] for r in strat["ladder"]["rungs"]]
    prospects_by_sector: Dict[str, int] = {}
    for pr in strat["prospects"]:
        prospects_by_sector[pr["sector"]] = prospects_by_sector.get(pr["sector"], 0) + 1
    bundle["applications"] = {
        "rungs": [{k: r.get(k) for k in ("id", "name", "lcoe_low_mwh", "lcoe_high_mwh",
                                           "capex_low_kwe", "capex_high_kwe", "opens_note")}
                  for r in strat["ladder"]["rungs"]],
        "segments": [{**{k: sg.get(k) for k in ("id", "name", "sector", "incumbent",
                                                 "incumbent_low_mwh", "incumbent_high_mwh",
                                                 "clears", "verdict", "blocker", "first_deal",
                                                 "sources")},
                      "benchmarks": len(sg.get("benchmark_ids", [])),
                      "prospects": prospects_by_sector.get(sg["sector"], 0)}
                     for sg in sorted(strat["segments"], key=lambda x: rung_ids.index(x["clears"]))],
    }
    bundle["sources_index"] = reg
    bundle["source_numbers"] = {r["url"]: r["n"] for r in reg}
    regions_by_id = {r["id"]: r for r in bundle["regions"]["regions"]}
    def featured_price(region_id: str) -> Dict[str, Any]:
        region = regions_by_id[region_id]
        by_url = {s["url"]: s for s in region["sources"]}
        urls = region["home_price_source_urls"]
        assert urls and all(url in by_url for url in urls), f"uncited home price: {region_id}"
        return {"text": region["home_price"], "sources": [by_url[url] for url in urls]}

    bundle["summary"] = {
        "opportunities": len(opps),
        "vendors": len(vendors),
        "tracks": {t["id"]: sum(1 for o in opps if o["track"] == t["id"])
                   for t in bundle["opportunities"]["tracks"]},
        "sector_count": len(bundle["sectors"]["sectors"]),
        "load_types": len(loads),
        "cited_loads": sum(1 for l in loads if l.get("sources")),
        "cited_rows": sum(1 for o in opps if o.get("sources")),
        "source_count": len(reg),
        "instruments": sum(len(g["records"]) for g in bundle["instruments"]["groups"]),
        "benchmarks": sum(len(s_["records"]) for s_ in bundle["benchmarks"]["sectors"]),
        "benchmarks_priced": sum(1 for s_ in bundle["benchmarks"]["sectors"]
                                 for r in s_["records"] if priced(r)),
        "benchmarks_priced_proposed": sum(1 for s_ in bundle["benchmarks"]["sectors"]
                                          for r in s_["records"]
                                          if priced(r) and r.get("price_status") == "proposed"),
        "benchmarks_filed": sum(1 for s_ in bundle["benchmarks"]["sectors"]
                                for r in s_["records"] if r.get("filings")),
        # Most benchmark rows are the non-nuclear incumbent a reactor would displace,
        # but a handful are nuclear projects carried for their published cost. The
        # page must not claim the set is uniformly non-nuclear, so count both.
        "benchmarks_nuclear": sum(1 for s_ in bundle["benchmarks"]["sectors"]
                                  for r in s_["records"] if r.get("nuclear")),
        # A count, not a percentage: on n=16 a "12%" reads as a rate and hides that
        # the numerator is 2. land_pct was emitted here for months and never read.
        "filing_rows": cov["utility_filing"]["have"],
        # Deployment-facing stats: how far the market has actually moved.
        "milestones_2026": sum(1 for v in vendors for m in v.get("milestones", [])
                               if m.get("status") == "done" and str(m.get("date", "")).startswith("2026")),
        "binding_rows": sum(1 for o in opps if o.get("binding")),
        "reactors_critical_2026": sum(o.get("reactors_critical_2026", 0) for o in opps),
        "units_largest_preorder": max((o.get("units_committed", 0) for o in opps), default=0),
        "first_delivery_year": min(v["first_delivery_year"] for v in vendors
                                   if v.get("first_delivery_year")),
        # Deals "Prospects (N)" and the Costs segment count draw these from the
        # eager bundle, since the strategy payload itself arrives lazily.
        "prospects": len(bundle["strategy"]["prospects"]),
        "segments": len(bundle["strategy"]["segments"]),
        # Front-page directory: one derived figure per tab.
        "news_items": len(bundle["news"]["items"]),
        "news_binding": sum(1 for it in bundle["news"]["items"] if it.get("binding")),
        "news_first": min(it["date"] for it in bundle["news"]["items"]),
        "arguments": len(bundle["arguments"]["arguments"]),
        "counters": len(bundle["arguments"]["counters"]),
        "pathways": sum(len(g["pathways"]) for g in bundle["policy"]["groups"]),
        "precedents": sum(len(g["items"]) for g in bundle["mechanisms"]["precedent_groups"]),
        "sites": len(bundle["deployment_sites"]["sites"]),
        "regions": len(bundle["regions"]["regions"]),
        "dockets": len(bundle["dockets"]["dockets"]),
        "dockets_micro": sum(1 for d in bundle["dockets"]["dockets"] if d.get("size_class") == "micro"),
        # Home answers the two most likely remote-market price questions without
        # making the reader open a region accordion. Text stays source-owned in
        # data/regions.json; the generator only takes its first decision sentence.
        "featured_prices": {
            "alaska": featured_price("alaska-rural-pce-communities"),
            "greenland": featured_price("greenland"),
        },
        "built": captured_date(bundle),
    }

    SITE.mkdir(exist_ok=True)
    # Split AFTER the register and summary are computed, so the citation numbering
    # and every derived figure still see the whole corpus. A lazy payload that
    # changed the source numbers would renumber every chip on the site.
    head = "/* generated by tools/build_data.py — do not edit */\n"
    lazy_bytes = 0
    for name in LAZY:
        payload = bundle.pop(name)
        chunk = (head + "window.MR." + name + "=" +
                 json.dumps(payload, separators=(",", ":"), ensure_ascii=False) +
                 ";window.dispatchEvent(new CustomEvent('mr:" + name + "'));\n")
        (SITE / f"data-{name}.js").write_text(chunk)
        lazy_bytes += len(chunk)
        print(f"site/data-{name}.js  {len(chunk):,} bytes  (fetched when its tab opens)")
    bundle["lazy"] = LAZY
    js = head + "window.MR=" + \
         json.dumps(bundle, separators=(",", ":"), ensure_ascii=False) + ";\n"
    (SITE / "data.js").write_text(js)
    s = bundle["summary"]
    print(f"site/data.js  {len(js):,} bytes  (+{lazy_bytes:,} lazy = "
          f"{len(js) + lazy_bytes:,} total)")
    print(f"  {s['opportunities']} opportunities ({s['cited_rows']} cited)  "
          f"{s['vendors']} vendors  {s['sector_count']} sectors / {s['load_types']} load types "
          f"({s['cited_loads']} cited)")
    print(f"  {s['source_count']} distinct sources  tracks: {s['tracks']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
