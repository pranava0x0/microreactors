# Backlog

## High Priority

- **high** · Docket pass, remaining state & regional forums (2026-08-23: NRC ADAMS + FERC eLibrary DONE —
  tools/adams_search.py + tools/ferc_elibrary.py, findings in data/deployment_sites.json;
  FERC has zero microreactor description hits ever, Malmstrom's only filing is a 1994
  tariff). Still open: CO PUC (Buckley/Xcel), MT PSC (Malmstrom/NorthWestern), San
  Antonio city agendas (JBSA/CPS), Alaska RCA (CVEA), ERCOT queue number for Last
  Energy Haskell.
- **high** · Integrate the 5 creative off-grid/hybrid demand applications into `data/sectors.json`
  (from `data/research/creative-demand-applications.json`): add dedicated facility load profiles
  with primary citations for Orbital Spaceports, Arctic Defense Radar Outposts, Megaton-scale Direct
  Air Capture Hubs, Subsea Power & Compute Pods, and Biorefinery Cogeneration.
- **high** · Browser-capture the DAF Microreactor FAQs PDF (eielson.af.mil 403s curl;
  use the JS chunk flow documented in AGENTS.md) — carries the NOITA issuance date and
  site-selection detail the Eielson row currently lacks.

## Medium Priority

- **med** · Deep-dive follow-ups with regulatory expiry: Penn State FRONTIER REP (promised late
  2025, absent from ADAMS as of 2026-08-23 — does the Westinghouse commercial-market
  exit affect it?); UIUC CP docketed under NRC Docket 50-618 on 2026-05-18 (DONE — findings in data/research/deployment-sites-followups.json); Aalo RELLIS
  selection & NRC pre-application docket 99902128 (DONE — findings in data/research/deployment-sites-followups.json); DAF/NRC environmental analysis for Eielson (next
  paper trail); Chalk River MMR post-bankruptcy disposition (Standard Nuclear).
- **med** · Interactive Diesel Displacement / LCOE Break-Even Calculator on Costs (`#economics`) tab:
  slider for diesel fuel price ($/gal), capacity factor, and remote logistics adder to dynamically
  compute the microreactor grid-parity ceiling ($/MWh) against incumbent generators.
- **med** · Close the remaining uncited Applications loads (registered in
  `data/sectors.json` `_meta.uncited`); each needs a facility-level MW source or stays marked.
- **med** · Watch items with regulatory expiry: NRC Part 57 finalisation (proposed May 2026 — the
  6–12 month licensing claim must stay labelled proposed until final), FERC EL25-49 PJM
  co-location compliance tariff, Radiant DOME campaign completion (targeted Q3 2026),
  ARC Act floor action. Re-verify each on the next data refresh.

## Low Priority

- **low** · Add one skeptic quote to the Tracker or Sources framing (Heatmap
  pattern: credibility from acknowledged doubt) — candidates already in the data: the
  MINING.COM <10%-of-miners counter-signal, or Parsons' "my crystal ball is broken".
- **low** · Thermal Cogeneration / Process Steam Filter on Applications tab: toggle for
  loads requiring 100°C–550°C thermal energy (e.g. DAC, chemical, pulp & paper) vs pure electrical power.
- **low** · Last Energy Poland (Katowice & Legnica SEZ agreements, DB Energy, PAA pre-application) (DONE — findings in data/research/deployment-sites-followups.json).
- **low** · Integrate data/deployment_sites.json into the site as a Sites layer/tab (DONE — 2026-08-24 dedicated Sites tab with sub-tabs for Universities & Labs, Defense & Remote, Commercial & Grid, and Findings & Absences).
- **low** · Sources tab: split the durable source register from dated developments (DOE
  reports-rail vs news-rail pattern) if a news stream ever gets added.
- **low** · Cite the Alaska band to the AEA Power Cost Equalization statistical report
  (primary) in addition to the current secondary reporting.
- **low** · Sub-tabs for the Tracker's three buyer tracks if the row count grows: the
  track chips currently filter one list, which still reads fine at 16 rows. Costs,
  Market design, Policy and Sources got sub-tabs on 2026-08-23.

