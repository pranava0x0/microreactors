#!/usr/bin/env python3
"""Apply verification pass C (verify-c-A.json, verify-c-B.json) to this pass's research files.

Pass C looked for every number in the records this pass added that no cached copy of a cited
page contained. Each fix below is one of: a figure the cited pages do not support, removed or
replaced with what a page does say; a figure that is right but was cited to a page that does not
carry it, which gains the page that does; a misattribution, corrected. Pages that block scripted
clients (AVEC, Power and Water, Horizon Power, Mining Technology) were read in a browser on
2026-09-26 and are marked fetched with the verbatim span read there.

Every edit asserts its old text is present exactly once, and skips when the new text is already
in place, so re-running is safe. Run from the repo root, then the integrate scripts:
  python3 data/research/2026-09-26-refresh/apply_verify_c.py
"""
import json
import pathlib

P = pathlib.Path(__file__).resolve().parent


def src(label: str, url: str, quote: str) -> dict:
    return {"label": label, "url": url, "quote": quote, "status": "fetched"}


# (file, list key, record id, field, old, new); field "loads.<i>.<key>" edits one load entry
EDITS = [
    # --- Alaska rural PCE: AVEC's 58/46 counts are on no reachable AVEC page; a 2026 listing says 59 locations
    ("north.json", "regions", "alaska-rural-pce-communities", "power_system",
     "Alaska Village Electric Cooperative (AVEC) alone serves 58 communities off 46 separate diesel power plants, each an isolated microgrid with no interconnection between villages;",
     "Alaska Village Electric Cooperative (AVEC) alone serves 59 locations across rural Alaska, each village an isolated microgrid with no interconnection to the next;"),
    ("north.json", "regions", "alaska-rural-pce-communities", "loads.0.mw",
     "46 diesel power plants across 58 communities", "59 locations"),
    ("north.json", "regions", "alaska-rural-pce-communities", "price",
     "the statewide FY2026 PCE base rate (the subsidized floor the state pays down to) is reported at 20.38 cents/kWh",
     "the RCA proposed raising the PCE base amount (the floor the state subsidy pays down to) from 19.92 to 20.38 cents/kWh"),
    # --- Alaska mines: Donlin's 220 MW is in no fetched source; Alaska DNR gives the pipeline as 315 miles
    ("north.json", "regions", "alaska-mines-power", "power_system",
     "Donlin Gold (not yet built) would need a 220 MW dual-fuel plant and a 316-mile gas pipeline.",
     "Donlin Gold (not yet built) would need its own dual-fuel power plant, fed by a 315-mile gas pipeline."),
    ("north.json", "regions", "alaska-mines-power", "loads.2.mw",
     "220 MW planned dual-fuel plant, 316-mile gas pipeline", "planned dual-fuel plant (MW not published), 315-mile gas pipeline"),
    # --- NWT: Ekati's 30.8 MW / seven 4.4 MW units are in no fetched source
    ("north.json", "regions", "northwest-territories", "loads.0.mw",
     "30.8 MW installed (seven 4.4 MW diesel generators)", "installed capacity not found in a fetched source"),
    ("north.json", "regions", "northwest-territories", "microreactor_read",
     "NWT's diamond mines (Ekati at 30.8 MW, Diavik at 55.4 MW) are exactly the scale a relocatable reactor targets,",
     "NWT's diamond mines are the scale a relocatable reactor targets (Diavik's wind-diesel plant is 55.4 MW; Ekati's capacity was not found),"),
    # --- Greenland: the 70% was Critical Metals' purchase of 60 North ApS; it owns 92.5% of Tanbreez
    ("north.json", "regions", "greenland", "loads.1.name",
     "Tanbreez rare earth project (Critical Metals Corp, 70% acquired)", "Tanbreez rare earth project (Critical Metals Corp, 92.5% owned)"),
    # --- Polar stations: the $2.42/gal was a live price-tracker figure, not a dated national average
    ("north.json", "regions", "polar-research-stations", "price",
     "No $/gallon or $/MWh fuel-logistics figure was found for Summit Station specifically; Greenland's general retail diesel price was $2.42/gallon as of 16 April 2026 (national average, not station-specific)",
     "No $/gallon or $/MWh fuel-logistics figure was found for Summit Station or McMurdo"),
    # --- CNMI: the 42.5 MW page is gone (404) and the 62.1 MW has no reachable source
    ("islands.json", "regions", "cnmi-cuc", "power_system",
     "Saipan's plants (Power Plant 1 designed for 86 MW across eight units, Plant 2 at 10 MW, Plant 4 at 16 MW) were reported at 62.1 MW combined availability in March 2025; a 2026 typhoon cut that further, with a recovery update citing 42.5 MW restored on Saipan and Rota timelines still being set.",
     "Saipan's plants are Power Plant 1 (designed for 86 MW across eight units), Plant 2 (10 MW) and Plant 4 (16 MW); how much of that is available now was not found in a page that could be fetched."),
    ("islands.json", "regions", "cnmi-cuc", "loads.0.mw",
     "42.5 MW available (2026 post-typhoon recovery update), versus 62.1 MW combined availability in March 2025",
     "86 MW (Plant 1), 10 MW (Plant 2) and 16 MW (Plant 4) design capacity"),
    ("islands.json", "regions", "cnmi-cuc", "loads.0.note",
     "diesel; typhoon-damaged and under repair as of this pass", "diesel; current availability not found in a fetchable page"),
    # --- Australia: no source gives WA mine diesel at $0.50 or hybrids at $0.25-0.35/kWh; Horizon's
    #     page gives 34 microgrids but not the resident count; SETuP is 26 communities, per ARENA
    ("islands.json", "regions", "australia-remote-power-market", "price",
     "WA off-grid mine diesel generation has historically cost upwards of $0.50/kWh, with recent hybrid-displaced costs reported around $0.25-0.35/kWh;",
     "Horizon Power's standard A2 residential rate is 33.2621 cents/kWh plus a $1.1924 daily supply charge (1 July 2026, GST included); no WA-specific $/kWh for off-grid mine diesel was found in a fetched source;"),
    ("islands.json", "regions", "australia-remote-power-market", "power_system",
     "runs 34 microgrids supplying about 100,000 residents and 10,000 businesses, and is rolling out",
     "runs 34 microgrids across regional WA and is rolling out"),
    ("islands.json", "regions", "australia-remote-power-market", "power_system",
     "its ARENA-funded Solar Energy Transformation Program (SETuP) added 10 MW of solar microgrids across 25 communities, saving an estimated 94 million litres of diesel over the program's 25-year life.",
     "its ARENA-funded Solar Energy Transformation Program (SETuP) brought solar to 26 remote off-grid communities, cutting diesel use by an estimated 94 million litres over the life of the panels."),
    ("islands.json", "regions", "australia-remote-power-market", "microreactor_read",
     "WA and the NT have exactly the diesel-cost profile (historically $0.50+/kWh, still $0.25-0.35/kWh even after hybridisation) and the off-grid scale",
     "WA and the NT have the diesel dependence and the off-grid scale"),
    ("islands.json", "regions", "australia-remote-power-market", "loads.0.note",
     "72 remote communities plus 66 outstations; diesel, partially solar-offset by the 10 MW SETuP program",
     "72 remote communities plus 66 outstations; diesel, partially solar-offset by the SETuP program"),
    # --- Pooling precedents
    ("pooling.json", "precedents", "nhs-antimicrobial-subscription-netflix-model", "how_it_works",
     "since the manufacturer is paid the same fee whether the drug treats 50 patients or 5,000 that year.",
     "since the manufacturer is paid the same fee however many patients the drug treats that year (NHS England estimated about 1,700 a year would be eligible for the first two drugs)."),
    ("pooling.json", "precedents", "global-fund-pooled-procurement-mechanism", "size",
     "; a further $128 million in non-Global-Fund money has been routed through the platform since 2018", ""),
    ("pooling.json", "precedents", "global-fund-pooled-procurement-mechanism", "outcome",
     ", and since 2018 countries have separately routed a further $128 million in non-Global-Fund money through the same platform to capture its negotiated prices.",
     "."),
]

ADD_SOURCES = [
    ("north.json", "regions", "alaska-rural-pce-communities", [
        src("NAOGUA - Alaska Village Electric Cooperative, Inc. (2026)", "https://www.naogua.org/alaska-village-electric-cooperative-inc",
            "is a non-profit electric utility serving residents in 59 locations throughout rural Alaska"),
        src("Regulatory Commission of Alaska - notice of proposed PCE base amount (2026)", "https://aws.state.ak.us/OnlinePublicNotices/notices/View.aspx?id=219490",
            "The Commission proposes to adjust the base amount to 20.38")]),
    ("north.json", "regions", "alaska-mines-power", [
        src("Alaska DNR - Donlin Gold project (2026)", "https://dnr.alaska.gov/mlw/mining/large-mines/donlin/",
            "a buried 14-inch diameter, 315-mile-long natural gas pipeline"),
        src("Anchorage Daily News - One of Alaska's flagship mines soon could draw energy from the sun (2026)",
            "https://www.adn.com/business-economy/energy/2026/03/22/one-of-alaskas-flagship-mines-soon-could-draw-energy-from-the-sun/",
            "roughly 40,000 gallons each day")]),
    ("north.json", "regions", "alaska-legal-framework", [
        src("World Nuclear News - Alaska simplifies microreactor regulations (2022)", "https://www.world-nuclear-news.org/Articles/Alaska-simplifies-microreactor-regulations",
            "an advanced nuclear reactor capable of producing no more than 50 MW")]),
    ("north.json", "regions", "greenland", [
        src("Critical Metals Corp - Greenland government approves transfer of final 50.5% of Tanbreez (2026)",
            "https://www.criticalmetalscorp.com/greenland-government-approves-transfer-of-final-50-5-of-tanbreez-taking-critical-metals-corp-to-92-5-ownership/",
            "bringing total CRML ownership to 92.5%"),
        src("Wikipedia - Nukissiorfiit", "https://en.wikipedia.org/wiki/Nukissiorfiit",
            "approximately 56,000 residents across 17 towns and 54 settlements")]),
    ("north.json", "regions", "northwest-territories", [
        src("Wikipedia - List of generating stations in the Northwest Territories",
            "https://en.wikipedia.org/wiki/List_of_generating_stations_in_the_Northwest_Territories", "27.66"),
        src("SustainableBiz - Rio Tinto plans largest solar farm in Canada's North at Diavik (2023)",
            "https://sustainablebiz.ca/rio-tinto-plans-largest-solar-farm-canada-north-diavik-mine",
            "Diavik already features a wind-diesel hybrid power facility with a capacity of 55.4 megawatts")]),
    ("north.json", "regions", "polar-research-stations", [
        src("Engineering.com - 60 years ago there was a small modular reactor", "https://www.engineering.com/60-years-ago-there-was-a-small-modular-reactor/",
            "Design output was 1,800 kW electrical operating at an 80 percent power factor"),
        src("NSF - NSF invites professional news media to report from Summit Station, Greenland", "https://www.nsf.gov/news/news_summ.jsp?cntn_id=307191&org=OPP",
            "Summit Station is located 10,530 feet (3200 meters) above sea level")]),
    ("islands.json", "regions", "australia-remote-power-market", [
        src("Horizon Power - A2 Residential Tariff (1 July 2026)", "https://www.horizonpower.com.au/for-home/home-electricity-solutions/a2-residential-tariff/",
            "Electricity unit charge (cents/kWh) 33.2621"),
        src("Horizon Power - Who we serve (2026)", "https://www.horizonpower.com.au/about-us/who-we-serve/",
            "34 microgrids across regional WA, all outside of the South West Interconnected System (SWIS)"),
        src("ARENA - NT Top End solar rollout enters next phase (2018)", "https://arena.gov.au/blog/solar-setup-next-phase/",
            "will cut diesel use by 15 per cent, equivalent to 94 million litres over the life of the panels")]),
    ("islands.json", "cases", "agnew-gold-mine-edl-hybrid-microgrid", [
        src("Mining Technology - Agnew gold mine: a vision for green power at mines? (2020)",
            "https://www.mining-technology.com/features/agnew-gold-mine-a-vision-for-green-power-at-mines/",
            "The agreement constituted an A$112m (approximately $80.2m) investment")]),
    ("pooling.json", "precedents", "maschinenring-farm-machinery-ring-buyers-club", [
        src("Maschinenring Österreich - Die Maschinenringe", "https://www.maschinenring.at/die-maschinenringe",
            "Mehr als 80 regionale Maschinenring-Standorte")]),
    ("pooling.json", "precedents", "rolls-royce-totalcare-trent1000-overrun-cover", [
        src("IMechE - Rolls-Royce Trent 1000 turbine blade issues contribute to £1.26bn pre-tax loss (2018)",
            "https://www.imeche.org/news/news-article/rolls-royce-trent-1000-turbine-blade-issues-contribute-to-1.26bn-pre-tax-lo",
            "an exceptional charge of £554m")]),
    ("pooling.json", "precedents", "ny-proton-center-hospital-consortium", [
        src("BioSpace - New York State's first proton therapy center opens in East Harlem (2019)",
            "https://www.biospace.com/article/releases/new-york-state-s-first-proton-therapy-center-opens-in-east-harlem/",
            "140,000-square-foot facility will be a beacon of top-quality cancer care nationwide")]),
    ("pooling.json", "precedents", "nhs-antimicrobial-subscription-netflix-model", [
        src("The Pharmaceutical Journal - First two antimicrobial drugs funded by NHS subscription payment scheme (2022)",
            "https://pharmaceutical-journal.com/article/news/first-two-antimicrobial-drugs-funded-by-nhs-subscription-payment-scheme-to-be-given-to-patients",
            "around 1,700 patients per year with severe bacterial infections would be eligible")]),
    ("filings.json", "dockets", "tennessee-nuclear-energy-fund-2025", [
        src("Spectrum News - Tennessee nuclear development (2026)", "https://spectrumlocalnews.com/us/snplus/news/2026/08/31/tennessee-nuclear-development",
            "Since 2023, the state has invested $95 million into a fund to support new nuclear projects")]),
]

# Pages that read as fetched but hold the figure only in a stitched quote, or no longer exist
FIX_SOURCES = [
    ("islands.json", "regions", "australia-remote-power-market", "https://www.powerwater.com.au/about/what-we-do/remote-operations/remote-power-sources",
     {"quote": "We own and operate 51 diesel-fired power stations with an installed capacity of about 80 megawatts (MW)", "status": "fetched"}),
]
DROP_SOURCES = [
    ("islands.json", "regions", "cnmi-cuc", "https://www.nminewsservice.com/bavi-recovery-rundown-day-10/"),
]


def load(name: str):
    """Return [data, raw, fmt]; fmt is (indent, ensure_ascii) or None for a hand-formatted file,
    which is edited as text so its layout survives (pooling.json and filings.json are)."""
    raw = (P / name).read_text()
    data = json.loads(raw)
    for indent in (1, 2):
        for ascii_ in (False, True):
            if json.dumps(data, indent=indent, ensure_ascii=ascii_) + "\n" == raw:
                return [data, raw, (indent, ascii_)]
    return [data, raw, None]


def record(data, key: str, rid: str) -> dict:
    hits = [r for r in data[key] if r.get("id") == rid]
    assert len(hits) == 1, (key, rid, len(hits))
    return hits[0]


def enc(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)[1:-1]


def closing_bracket(raw: str, open_at: int) -> int:
    """Index of the ] matching the [ at open_at, skipping brackets inside strings."""
    depth, i, in_str = 0, open_at, False
    while i < len(raw):
        c = raw[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced")


def text_add_source(raw: str, rid: str, s: dict) -> str:
    """Append a one-line source object to a record's sources array, at the indent of the last one."""
    marker = f'"id": "{rid}"'
    assert raw.count(marker) == 1, rid
    at = raw.index(marker)
    open_at = raw.index('"sources": [', at) + len('"sources": ')
    nxt = raw.find('"id": "', at + len(marker))
    assert nxt == -1 or open_at < nxt, f"{rid}: sources not inside the record"
    body_end = len(raw[:closing_bracket(raw, open_at)].rstrip())  # just after the last source
    line = raw[raw.rfind("\n", 0, body_end) + 1:body_end]
    indent = line[:len(line) - len(line.lstrip())]
    return raw[:body_end] + ",\n" + indent + json.dumps(s, ensure_ascii=False) + raw[body_end:]


def main() -> None:
    files = {}

    def get(name):
        if name not in files:
            files[name] = load(name)
        return files[name]
    changed = 0
    for name, key, rid, field, old, new in EDITS:
        f = get(name)
        rec = record(f[0], key, rid)
        parts = field.split(".")
        holder, leaf = rec, parts[-1]
        for p in parts[:-1]:
            holder = holder[int(p)] if p.isdigit() else holder[p]
        text = holder[leaf]
        if old in text:
            assert text.count(old) == 1, (rid, field, old[:40])
            holder[leaf] = text.replace(old, new)
            if f[2] is None:
                assert f[1].count(enc(old)) == 1, (name, rid, old[:40])
                f[1] = f[1].replace(enc(old), enc(new))
            changed += 1
        else:
            assert new == "" or new in text, f"{rid}.{field}: neither old nor new text found"
    for name, key, rid, sources in ADD_SOURCES:
        f = get(name)
        rec = record(f[0], key, rid)
        have = {s["url"] for s in rec.get("sources", [])}
        for s in sources:
            if s["url"] not in have:
                rec.setdefault("sources", []).append(s)
                if f[2] is None:
                    f[1] = text_add_source(f[1], rid, s)
                changed += 1
    for name, key, rid, url, fields in FIX_SOURCES:
        f = get(name)
        assert f[2] is not None, "text-mode source fixes are not implemented"
        rec = record(f[0], key, rid)
        hit = [s for s in rec["sources"] if s["url"] == url]
        assert len(hit) == 1, (rid, url)
        if any(hit[0].get(k) != v for k, v in fields.items()):
            hit[0].update(fields)
            changed += 1
    for name, key, rid, url in DROP_SOURCES:
        f = get(name)
        assert f[2] is not None, "text-mode source drops are not implemented"
        rec = record(f[0], key, rid)
        before = len(rec["sources"])
        rec["sources"] = [s for s in rec["sources"] if s["url"] != url]
        changed += before - len(rec["sources"])
    for name, (data, raw, fmt) in files.items():
        if fmt is None:
            assert json.loads(raw) == data, f"{name}: text edits diverged from the data edits"
            (P / name).write_text(raw)
        else:
            (P / name).write_text(json.dumps(data, indent=fmt[0], ensure_ascii=fmt[1]) + "\n")
    print(f"apply_verify_c: {changed} change(s) across {len(files)} file(s)")


if __name__ == "__main__":
    main()
