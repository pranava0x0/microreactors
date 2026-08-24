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
  exit affect it?); UIUC CP docketing decision after 2026-04-15 receipt; Aalo RELLIS
  ESP progress on docket 99902128; DAF/NRC environmental analysis for Eielson (next
  paper trail); Chalk River MMR post-bankruptcy disposition (Standard Nuclear).
- **med** · Browser-capture the DAF Microreactor FAQs PDF (eielson.af.mil 403s curl;
  use the JS chunk flow documented in AGENTS.md) — carries the NOITA issuance date and
  site-selection detail the row currently lacks.
- **low** · Last Energy Poland (Legnica SEZ letter of intent, DB Energy) — one search
  found nothing current; verify and add an abroad row or record the absence.
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
