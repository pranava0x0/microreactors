#!/usr/bin/env python3
"""Build data/regions.json from the 2026-09-26 regional passes (re-runnable).

north.json and islands.json hold Type E region records written by two agents.
This keeps their facts, numbers and sources unchanged and adds only what the
page needs to scan a list: a group, a law-and-policy tag, and a short price
label. Those three are curated here, per record, from the record's own text,
so a reviewer can check each call against the prose it summarises.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "data" / "regions.json"

GROUPS = [
    {"id": "alaska", "label": "Alaska"},
    {"id": "canada-north", "label": "Canada's north"},
    {"id": "arctic-europe", "label": "Greenland, the Nordics and polar stations"},
    {"id": "us-islands", "label": "US islands, territories and freely associated states"},
    {"id": "australia", "label": "Australia"},
    {"id": "uk-allies", "label": "UK, its territories and New Zealand"},
]
POSITION_TAGS = [
    {"id": "enabling", "label": "Enabling law",
     "gloss": "A statute or regulation already provides for siting a microreactor here."},
    {"id": "study", "label": "Studying",
     "gloss": "A government or utility is studying or planning nuclear power, with no enabling law yet."},
    {"id": "review", "label": "Ban under review",
     "gloss": "A standing ban or restriction on nuclear power is under formal review."},
    {"id": "silent", "label": "No stated position",
     "gloss": "No law, study or official statement on civil nuclear power was found."},
    {"id": "proposed-ban", "label": "Ban proposed",
     "gloss": "A bill to prohibit nuclear power has been introduced but not enacted."},
    {"id": "restricted", "label": "Restricted",
     "gloss": "A legal barrier short of an outright ban, such as a supermajority vote."},
    {"id": "banned", "label": "Banned",
     "gloss": "Civil nuclear power is prohibited by statute."},
]

# id -> (group, position tag, short price label). Filled from each record's text.
CURATION = {
    # north.json
    "alaska-railbelt-utilities": ("alaska", "enabling", "tariff not fetched"),
    "alaska-rural-pce-communities": ("alaska", "enabling", "$0.3647/kWh base rate (AVEC)"),
    "alaska-mines-power": ("alaska", "enabling", "Fort Knox buys $40M of power a year"),
    "alaska-legal-framework": ("alaska", "enabling", "statewide framework"),
    "greenland": ("arctic-europe", "review", "tariff not published"),
    "yukon": ("canada-north", "study", "tariff not fetched"),
    "northwest-territories": ("canada-north", "silent", "tariff not fetched"),
    "nunavut": ("canada-north", "silent", "$555-1,130/MWh (QEC, 2025)"),
    "nunavik-northern-quebec": ("canada-north", "silent", "tariff not fetched"),
    "labrador-northern-ontario": ("canada-north", "silent", "tariff not fetched"),
    "svalbard-and-northern-nordics": ("arctic-europe", "study", "tariff not fetched"),
    "polar-research-stations": ("arctic-europe", "silent", "no station fuel price published"),
    # islands.json
    "puerto-rico": ("us-islands", "study", "$0.26/kWh residential (2026)"),
    "us-virgin-islands": ("us-islands", "silent", "$0.42/kWh residential (2025)"),
    "guam": ("us-islands", "proposed-ban", "fuel charge $0.136/kWh (2025)"),
    "cnmi-cuc": ("us-islands", "study", "$0.27/kWh residential (2024)"),
    "american-samoa": ("us-islands", "silent", "$0.45/kWh residential (2022)"),
    "hawaii": ("us-islands", "restricted", "$0.396/kWh average (2025)"),
    "freely-associated-states-pacific": ("us-islands", "silent", "$0.28-0.48/kWh (Palau, FSM)"),
    "australia-nuclear-legal-position": ("australia", "banned", "federal and state law"),
    "australia-remote-power-market": ("australia", "banned", "A$0.333/kWh residential (WA, 2026)"),
    "uk-scottish-islands-and-nuclear-framework": ("uk-allies", "restricted", "tariff not fetched"),
    "uk-overseas-territories-south-atlantic": ("uk-allies", "silent", "up to £0.42/kWh (St Helena, 2014)"),
    "nz-chatham-islands-and-nuclear-law": ("uk-allies", "silent", "NZ$1.32/kWh (2026)"),
}

# Tariffs found later by the issues pass (issues.json `tariffs`) for the regions
# the regional agents could not price. The long price text and its source come
# from that file; the short label is written here for the list row.
TARIFF_SHORT = {
    "alaska-railbelt-utilities": "$0.244/kWh residential (Chugach, 2026)",
    "yukon": "C$0.121/kWh base plus riders (ATCO, 2026)",
    "northwest-territories": "C$0.365-0.890/kWh thermal zone (NTPC, 2026)",
    "nunavik-northern-quebec": "C$0.07-0.51/kWh by block (Hydro-Quebec, 2026)",
    "labrador-northern-ontario": "C$0.156/kWh first block (NL Hydro, 2026)",
    "svalbard-and-northern-nordics": "capped at NOK 1.30/kWh (Svalbard, 2026)",
    "uk-scottish-islands-and-nuclear-framework": "26.11p/kWh UK price cap (Jul-Sep 2026)",
    "greenland": "DKK 2.00/kWh in every town (2026)",
}

# The agents wrote " -- " as a dash; house style has no dashes in prose.
DASHES = [(" -- ", ", "), (" — ", ", ")]


def clean(text):
    if not isinstance(text, str):
        return text
    for old, new in DASHES:
        text = text.replace(old, new)
    return text


def dedupe(sources):
    seen, out = set(), []
    for s in sources or []:
        if s["url"] not in seen:
            seen.add(s["url"])
            out.append(s)
    return out


def main() -> None:
    order = [g["id"] for g in GROUPS]
    regions, missing = [], []
    for name in ("north.json", "islands.json"):
        path = HERE / name
        if not path.exists():
            continue
        for r in json.loads(path.read_text()).get("regions", []):
            if r["id"] not in CURATION:
                missing.append(r["id"])
                continue
            group, tag, price_short = CURATION[r["id"]]
            rec = {k: clean(r.get(k)) for k in ("id", "region", "country", "jurisdiction", "power_system",
                                                "price", "nuclear_position", "microreactor_activity",
                                                "microreactor_read") if r.get(k)}
            rec.update(group=group, position=tag, price_short=price_short,
                       loads=[{k: clean(v) for k, v in l.items()} for l in r.get("loads", [])],
                       blockers=[clean(b) for b in r.get("blockers", [])],
                       sources=dedupe(r.get("sources")))
            regions.append(rec)
    assert not missing, f"no curation for {missing}"
    tariffs_p = HERE / "issues.json"
    if tariffs_p.exists():
        by_id = {r["id"]: r for r in regions}
        for t in json.loads(tariffs_p.read_text()).get("tariffs", []):
            r = by_id[t["region_id"]]
            r["price"] = clean(t["price"])
            r["price_short"] = TARIFF_SHORT[t["region_id"]]
            for src in t.get("sources", []):
                if src["url"] not in {x["url"] for x in r["sources"]}:
                    r["sources"].append(src)

    # The 2026-09-28 follow-up adds two pricing views the regional sweep lacked:
    # proposed avoided-cost purchase rates for rural Alaska, and a government-
    # commissioned mine-microgrid cost model for Greenland. Merge them into the
    # existing jurisdiction records instead of rendering duplicate places.
    follow_p = HERE.parent / "2026-09-28-alaska-greenland-pricing" / "north.json"
    if follow_p.exists():
        follow = json.loads(follow_p.read_text())
        by_id = {r["id"]: r for r in regions}
        cases = {r["id"]: r for r in follow.get("cases", [])}
        alaska = by_id["alaska-rural-pce-communities"]
        alaska["price"] += (
            "; 2026 proposed non-nuclear qualifying-facility purchase rates range from $0.0225 to "
            "$0.5119/kWh across six Alaska Power Company groupings, while TDX Manley "
            "filed $1.1802/kWh. These are requested rates, not final orders.")
        alaska["microreactor_read"] = (
            "Rural Alaska cannot be modeled from one statewide diesel number. Filed 2026 "
            "non-nuclear qualifying-facility comparators span $22.50-$1,180.20/MWh before "
            "final RCA action. A reactor cannot claim those tariffs; it needs a negotiated "
            "PPA or special contract with a named utility and separate approval.")
        alaska["home_price"] = "Alaska QF comparators: $22.50-$1,180.20/MWh proposed."
        # The two figures in home_price come one each from these two cases, so
        # the Home page's featured-price citation (build_data.py:featured_price)
        # points at exactly the sources that back the $22.50 and $1,180.20 ends,
        # not the full merged alaska["sources"] list.
        alaska["home_price_source_urls"] = []
        for case_id in ("apc-rate-group5-2026-small-facility-rates",
                        "tdx-manley-2026-copa-small-facility-rates"):
            for src in cases[case_id].get("sources", []):
                if src["url"] not in {x["url"] for x in alaska["sources"]}:
                    alaska["sources"].append(src)
                if src["url"] not in alaska["home_price_source_urls"]:
                    alaska["home_price_source_urls"].append(src["url"])

        study = follow["regions"][0]
        greenland = by_id["greenland"]
        greenland["price"] += "; government mine study: " + study["price"]
        greenland["loads"].extend(study.get("loads", []))
        greenland["microreactor_activity"] += " " + study["microreactor_activity"]
        greenland["microreactor_read"] = study["microreactor_read"] + (
            " No Greenland reactor procurement, utility study or nuclear filing was found.")
        greenland["home_price"] = "Greenland modeled LCOE: EUR 199/MWh hybrid; EUR 297/MWh diesel."
        # Both LCOE figures come from the Ramboll mine-microgrid model specifically,
        # not the CIPF investment catalogue also merged into greenland["sources"].
        greenland["home_price_source_urls"] = [study["sources"][0]["url"]]
        greenland["blockers"].extend(study.get("blockers", [])[:2])
        for src in study.get("sources", []):
            if src["url"] not in {x["url"] for x in greenland["sources"]}:
                greenland["sources"].append(src)
    regions.sort(key=lambda x: (order.index(x["group"]), x["region"]))
    # Counted from the records, never asserted: an earlier version said every
    # source was fetched while 14 were snippet-only (Codex review, PR #22).
    statuses = [s.get("status") for r in regions for s in r["sources"]]
    fetched, snippet = statuses.count("fetched"), statuses.count("snippet-only")
    out = {
        "_meta": {
            "captured": "2026-09-28",
            "what_this_is": (f"{len(regions)} remote and cold places, most running on diesel, where a "
                             "1-20 MW reactor would compete: what each pays, what it draws, and where "
                             "its law stands on civil nuclear power."),
            "method": ("Two research passes (data/research/2026-09-26-refresh/north.json and "
                       "islands.json), one record per jurisdiction, with eight tariffs added from "
                       "that folder's issues.json, plus Alaska tariff and Greenland mine-model "
                       "evidence from data/research/2026-09-28-alaska-greenland-pricing/north.json. "
                       f"{fetched} of {len(statuses)} "
                       f"sources were fetched and read; {snippet} are search-corroborated only and "
                       "carry status snippet-only, which the page marks with a dagger. The group, "
                       "the law-and-policy tag and the short price label are curated in that "
                       "folder's integrate_regions.py from each record's own text. Military bases "
                       "appear only as context."),
            "groups": GROUPS,
            "position_tags": POSITION_TAGS,
        },
        "regions": regions,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(regions)} regions")


if __name__ == "__main__":
    main()
