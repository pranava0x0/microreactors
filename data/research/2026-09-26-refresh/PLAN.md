# Research pass — 2026-09-26 — full refresh

Branch: `research/2026-09-26-refresh`. Resume from this file plus `git log -5`.

## The ask (user, 2026-09-26), as a checklist

- [ ] 1. Web searches for new information for **each tab**; plan them, find new keywords and new things to search (this file, "Per-tab angles").
- [ ] 2. Update **News**; make the **Home** page a real summary of the whole site with top headlines.
- [ ] 3. More research on **applications** and **utility filings**.
- [ ] 4. More examples of **pooled buying / insurance / shared orders** from *other sectors* (novel tech, luxury, expensive goods, anything), and fold the ideas into Rules & deal design.
- [ ] 5. Improve the **summarization of the application space** (Applications tab).
- [ ] 6. Dedicated deep dive: **Alaska, Greenland, US islands and territories, AUKUS, and remote cold regions in allied countries** (non-military).
- [ ] 7. **Validate every claim** on the site and in the datasets.
- [ ] 8. **UAT** on mobile, tablet, desktop: every interaction, minimal scrolling, clear flow, clear affordances, good perf.
- [ ] 9. Address open **GitHub issues** (#9, #11, #13, #14, #15, #16, #17, #18) and bugs in `issues.md`.
- [ ] 10. Open a PR; one round of code review with **inline comments on GitHub**.
- [ ] 11. Address all review comments, including **one Codex bot round**; then merge.

Constraints: Sonnet agents only, **max 2 at a time**; every agent writes to disk incrementally
(see CONTRACT.md) so a usage-limit kill loses nothing.

## State on disk (update as work lands)

- `data/cache/` rebuilt 2026-09-26 from `source_index.json` (gitignored; scratch script
  `rebuild_cache.py`): 445 of 469 re-fetched, 24 failed (16x403, 3x308, 2x404, 1 timeout,
  1 SSL, 1 DNS). USAspending API URLs must be fetched with `Accept: application/json`
  or DRF serves its HTML browsable page and every JSON quote "mismatches".
- 43 cited-but-never-indexed URLs fetched and indexed with `fetch_source.py`.
- Quote gate (`verify_quotes.py --cache`, **needs PyMuPDF**; without it every PDF quote
  reads as a mismatch): **699 verified, 0 mismatches**, 128 not-in-cache, 39 snippet-only.
- `seeds/news_watch.json`: feed + EDGAR candidates since 2026-09-01.

## Per-tab angles and new keywords (from the 2026-09-26 discovery searches)

| Tab | Data | New keywords / angles |
|---|---|---|
| Home | news.json + every tab's headline | one-screen summary: headline numbers per tab, top 3 headlines, "what changed this month" |
| Deals | opportunities, deployment_sites, strategy.prospects | "Department of War" (DoD renamed; search both), NWS Crane Navy shore-based microreactor (2026-09-09, vendor TBD from Janus pool, Sept 2028), Janus contract definitization, Eielson status, Oklo PJM complaint rejected by FERC (2026-09-25), NANO-Ameresco MOU (2026-01-12), Urenco-Antares enrichment deal |
| Why | arguments.json | NIA / INL territory studies (Puerto Rico, USVI, Guam, CNMI, American Samoa), survey data on Alaska public support (25% -> 40% awareness) |
| Applications | sectors.json, benchmarks | off-grid mine contracts (Zenith, Aggreko, EDL, TUGLIQ), island utilities' fuel cost, desalination, district heat (Steady Energy), cold-chain, spaceports |
| Costs | costs, benchmarks, strategy ladder | published vendor unit prices (#16), TRISO $/MTU (#15), island/territory $/kWh tariffs, PCE rates |
| Vendors | vendors.json | eVinci heated-core record (1,011 C), X-energy microreactor (DOE cooperative agreement), Project Pele TRISO delivery, Deployable Energy "Unity" |
| Rules & deal design | policy, mechanisms, instruments | Part 57 final rule due Nov 2026, "fleet approvals", "manufacturing licenses", Alaska DEC siting regs, NSW uranium ban repeal, Denmark SMR review (Jan 2026), Yukon-Ontario SMR pact (Apr 2026), Kvanefjeld licence refused (Jun 2026); **pooled buying**: AMC (Frontier $915M, Gavi pneumococcal), First Movers Coalition, Symbiosis, H2Global double auction, JIVE fuel-cell bus joint procurement, NATO MMF tanker pool / SAC C-17 pool, P&I clubs, CCRIF parametric pool, NHS antibiotic subscription, Civica Rx, SEMATECH, rideshare launch, en primeur wine, fractional jets, proton-therapy consortia, undersea-cable consortia |
| News | news.json | items since 2026-09-17: FERC rejects Oklo PJM complaint (09-25), NWS Crane (09-09), US-Turkey SMR (09-24), EIB first SMR loan (09-15), Holtec Palisades site work (09-16), Samsung C&T in Kairos (09-22), Bechtel exits TerraPower (09-22), Project Pele TRISO |
| Sources | register, voices | re-verify, cache, dead-link replacements (AEP Ohio tariff book, NREL data, CNSC Chalk River) |

## Partition (max 2 concurrent; each entity belongs to exactly one agent)

| wave | agent | file | scope | skip |
|---|---|---|---|---|
| 1 | pooling | `pooling.json` | Type D precedents: pooled buying, buyers' clubs, AMCs, assurance contracts, shared ownership, mutual/parametric insurance, overrun cover, subscription payment — **outside nuclear** | nuclear-sector examples already in `data/mechanisms.json` |
| 1 | north | `north.json` | Type E regions + B cases + C answers: Alaska, Greenland, Canada's north (Yukon, NWT, Nunavut, Nunavik, Labrador), Nordics (Svalbard, Iceland, Faroe, N. Norway/Sweden/Finland), polar research stations | military bases (Eielson, Wainwright only as context), islands below |
| 2 | islands | `islands.json` | Type E + B: Puerto Rico, USVI, Guam, CNMI, American Samoa, Hawaii, Pacific allies; AUKUS civil: Australia (remote mines, NT/WA communities, legal ban), UK (Scottish islands, Falklands, St Helena), NZ (Chatham) | the north |
| 2 | filings | `filings.json` | Type F utility/PUC filings naming microreactors or SMRs (IRPs, riders, CPCNs, RFPs, state study mandates) + Type B application cases | regions above |
| 3 | verify | `verify-*.json` | Type G claim checks on every tracker row, vendor milestone, prospect and news item older than 6 months | — |
| 3 | issues | `issues.json` | #17 off-grid IPP portfolio + still-open parts of #9, #11, #13, #14, #15, #16 | — |

Main session (single writer): news update, integration into `data/*.json`, caching every
shipping source with `fetch_source.py`, quote gate, UI, UAT, PR.

## Gate

```bash
python3 tools/research_pass.py validate data/research/2026-09-26-refresh
V=<scratch venv>/bin/python; $V tools/verify_quotes.py --cache
$V -m unittest discover -s tests
```

## UAT findings (before), 2026-09-26 — `uat_audit.py` in the scratch dir

- Perf: FCP ~80 ms local; first load 571 KB raw (data.js 342 KB + data-news.js 90 KB + app.js 80 KB + CSS 54 KB); no console errors; no horizontal overflow at 375/768/1280.
- Nav wraps to 2 rows at 768 and 1280 (129-143 px tall); on mobile the tab strip scrolls with no hint of more tabs.
- Mobile home: hero is 922 px on an 812 px screen; nothing but the masthead above the fold.
- Longest views (mobile screens): Source register 74, Customer cost 25, Vendors/all 14, Why/arguments 12, Policy/diesel 12, Policy/interconnection 10, News 9, Deals/all 8.
- Applications "All sectors" = 8 bare collapsed headers: no summary of loads, today's power, or price.
- Duplicate chips ("[10][10]") in Home "Also recent"; chips stack vertically there.
- Citation chips are ~12x14 px on touch.
- Hand-typed data in app.js: Why > "The loads" `topOptions` (six cards with $ ranges and citations that do not support them, e.g. spaceport "5-30 MW" cited to an Antares ANPI release, mining transmission "$100M, 5-10 years" cited to a CVEA page); Applications stat "$250-$850/MWh" hard-coded; Sites summary "5" load categories and "0" FERC hits hard-coded.
- "0.24-0.24 MW" renders a degenerate range.
- Tracker Janus row says NOT BINDING while the 2026-08-26 Janus award news items are binding: reconcile.

## UI plan

1. Nav: one row at >=1024 (tighter tab padding/tracking); mobile strip gets an edge fade and scrolls the active tab into view.
2. Home = site overview: compact masthead + stat strip; "Top headlines" (precomputed in build_data, so the 90 KB news payload leaves the first load); "The site at a glance": one card per tab, question -> derived answer -> link.
3. Applications: new default "Overview" = buyer segments on one price ladder (incumbent $/MWh band vs first-unit / mass-produced / optimized rungs), with who wins when, blocker, first deal, evidence counts (precomputed from strategy.json); sectors keep their sub-tabs; new "Regions" sub-tab from the regions research.
4. Why > The loads: drop the hand-typed `topOptions`; point to the Applications overview.
5. Rules & deal design: pooled-buying precedents by mechanism (new research) inside Deal design; new "Utility filings" sub-tab from the dockets research.
6. Shorter long lists: source register paged (first 30 + filter + show all); Customer cost grouped per sector in collapsed sections with the price range in the summary; deal rows get a visible "Details" affordance.
7. Chips: dedupe per cite(); 24 px minimum hit area on coarse pointers.
8. Derive the hard-coded Sites and Applications stats.

## State at the usage-limit stop (2026-09-26, resume here)

Done and committed on branch `research/2026-09-26-refresh` (not yet pushed, no PR yet):
- Checklist items 2 (Home = site directory + sorted headlines), 4 (24 pooled-buying precedents,
  7 design elements in the orderbook proposal), 5 (Applications overview), 6 (24 regions in
  Applications > Regions), most of 8 (nav, long lists, disclosures; phone scroll lengths cut
  3-15x), #18 closed, 5 dead links fixed, quote gate 798 verified / 0 mismatches.
- Regions pass: north.json (12 regions, 3 cases, 5 answers), islands.json (12 regions, 3 cases),
  integrated by integrate_regions.py. north's 3 cases and 5 answers are NOT yet merged anywhere.

Still to do, in order:
1. filings agent (running at the stop; writes filings.json incrementally): integrate dockets into
   a Rules > "Utility filings" sub-tab and cases/loads into sectors.json/benchmarks.
2. Launch news agent (prompts/news.md), then merge its items via data/research/news/ + merge_news.py.
3. Launch verify agents (prompts/verify.md with CLAIMS_FILE verify-a-claims.json / verify-b-claims.json,
   OUT_FILE verify-a.json / verify-b.json; SPECIFIC_QUESTIONS: Janus binding status vs the Army's
   "down-selected ... for negotiation" release; Radiant DOME criticality by Q3 2026; eVinci status).
4. Issues agent: #17 off-grid IPPs, #11 SRC, #15 per-vendor HALEU, #16 vendor prices, plus the 8
   "tariff not fetched" regions (Railbelt, Yukon, NWT, Nunavik, Labrador, Svalbard, Scotland, Greenland).
5. Merge north answers (#9, #13, #14) into strategy.json via merge_answers.py; update Home glance with regions.
6. Final UAT (uat_audit.py), docs (README tabs, agent-runs), push, PR, inline review, Codex round, merge.
