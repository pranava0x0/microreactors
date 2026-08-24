# Backlog

- **high** · Docket pass, remaining forums (2026-08-23: NRC ADAMS + FERC eLibrary DONE —
  tools/adams_search.py + tools/ferc_elibrary.py, findings in data/deployment_sites.json;
  FERC has zero microreactor description hits ever, Malmstrom's only filing is a 1994
  tariff). Still open: CO PUC (Buckley/Xcel), MT PSC (Malmstrom/NorthWestern), San
  Antonio city agendas (JBSA/CPS), Alaska RCA (CVEA), ERCOT queue number for Last
  Energy Haskell.
- **high** · Integrate data/deployment_sites.json into the site as a Sites layer/tab
  (per-category candidate sites + filings). The dataset is gated and cited; only the
  UI is missing. Decide render: per-sector site lists on Applications vs its own tab.
- **med** · Deep-dive follow-ups with expiry: Penn State FRONTIER REP (promised late
  2025, absent from ADAMS as of 2026-08-23 — does the Westinghouse commercial-market
  exit affect it?); UIUC CP docketed under NRC Docket 50-618 on 2026-05-18 (DONE — findings in data/research/deployment-sites-followups.json); Aalo RELLIS
  selection & NRC pre-application docket 99902128 (DONE — findings in data/research/deployment-sites-followups.json); DAF/NRC environmental analysis for Eielson (next
  paper trail); Chalk River MMR post-bankruptcy disposition (Standard Nuclear).
- **med** · Browser-capture the DAF Microreactor FAQs PDF (eielson.af.mil 403s curl;
  use the JS chunk flow documented in AGENTS.md) — carries the NOITA issuance date and
  site-selection detail the row currently lacks.
- **low** · Last Energy Poland (Katowice & Legnica SEZ agreements, DB Energy, PAA pre-application) (DONE — findings in data/research/deployment-sites-followups.json).
- **med** · Close the remaining uncited Applications bands (registered in
  sectors.json `_meta.uncited`); each needs a facility-level MW source or stays marked.
- **med** · Watch items with expiry: NRC Part 57 finalisation (proposed May 2026 — the
  6–12 month licensing claim must stay labelled proposed until final), FERC EL25-49 PJM
  co-location compliance tariff, Radiant DOME campaign completion (targeted Q3 2026),
  ARC Act floor action. Re-verify each on the next data refresh.
- **low** · Add one skeptic quote to the Tracker or Sources framing (Heatmap
  pattern: credibility from acknowledged doubt) — candidates already in the data: the
  MINING.COM <10%-of-miners counter-signal, or Parsons' "my crystal ball is broken".
- **low** · Sources tab: split the durable source register from dated developments (DOE
  reports-rail vs news-rail pattern) if a news stream ever gets added. The tab now has
  sub-tabs (register / coverage / gaps), so a fourth rail is a one-line addition.
- **low** · Cite the Alaska band to the AEA Power Cost Equalization statistical report
  (primary) in addition to the current secondary reporting.
- **low** · Sub-tabs for the Tracker's three buyer tracks if the row count grows: the
  track chips currently filter one list, which still reads fine at 16 rows. Costs,
  Market design, Policy and Sources got sub-tabs on 2026-08-23.
- **med** · Research & evaluate creative off-grid/hybrid application spaces (DONE — 2026-08-24 deep dive in data/research/creative-demand-applications.json):
  1. Spaceports and orbital launch complexes (5–30 MWe + thermal for on-site cryogenic propellant liquefaction: LOX, liquid methane, and LH2).
  2. Arctic defense radar and surveillance outposts (NORAD/North Warning System modernization: 47+ remote sites replacing pure diesel logistics).
  3. Direct Air Capture (DAC) / Megaton-scale carbon removal hubs (1–20 MWe + 10–50 MWth 100°C–300°C low-carbon thermal desorption in remote mineralized basins).
  4. Subsea power and offshore seabed processing (displacing deepwater gas turbines and long umbilicals for subsea pumping, compression, and subsea compute pods).
  5. Biorefinery and grain processing cogeneration (5–20 MWe + process steam displacing gas boilers constrained by regional pipeline capacity).

