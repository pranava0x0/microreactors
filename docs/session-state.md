# Session state — 2026-08-23 (site eval + deployment-sites research)

Resume file: a fresh session reads THIS file plus `git log -5` and continues from
"Next actions". Prior session (citation+IA overhaul) is COMPLETE — PR #2 merged,
Pages live at https://pranava0x0.github.io/microreactors/. See git history of this
file for that log. Branch: `jam/site-eval-deployment-research-b100c6` (worktree).

## The task (user's words, decomposed)

1. Comprehensive evaluation of site + data: every claim cited; tests/scrapers
   enforce it (extend gates where holes found).
2. Deployment-categories research (Applications tab = 8 sectors / ~50 load bands):
   for each category, a list of candidate SITES (US + abroad) reached by clicking
   through from that page's citations + new search, and relevant UTILITY FILINGS
   (the known-empty field; needs FERC eLibrary / state PUC / NRC ADAMS, not web
   search).
3. Depth-first: 1–2 sites per 1–3 sub-categories FIRST, with reusable scripts;
   THEN fan out broad. Parallel + web-search before agents.
4. Every grabbed source document gets indexed: original URL + access date; cache
   pages (data/cache/, gitignored raw; committed index in
   data/research/source_index.json).
5. A 16-min timer (cron ce715fb0, fires 13:02 local) resumes this task if the
   usage window dies.

## Evaluation findings so far

- 30/30 tests green; tools/check_citations.py green; working tree was clean.
- Known gaps (README + gaps.json): land_acres, shell, utility_filing near-empty
  across opportunities.json; named absences: CPS Energy (JBSA), Xcel CO
  (Buckley), NorthWestern MT (Malmstrom) interconnection filings "not located".

## Plan of record

- Deep-dive picks (3 subcategories, sites with real filing trails):
  A. Defense — remote installation: Eielson AFB pilot (Fairbanks AK; utility
     context Golden Valley Electric Association; hunt DAF/DLA award docs + NRC
     pre-application docket).
  B. Civic — universities: Penn State eVinci LOI (NRC ADAMS pre-application
     trail for eVinci; Westinghouse docket).
  C. Utilities — remote/regional grids: Copper Valley Electric (AK, RCA dockets)
     + abroad comparator with richest foreign filing trail (CNSC: SRC eVinci
     pilot; check status of Chalk River MMR before citing — USNC bankruptcy).
- Scripts to write in tools/: fetch_source.py (fetch→cache→index, idempotent),
  adams_search.py (NRC ADAMS public API), ferc_elibrary.py (eLibrary API).
  Validate each against a real query before relying on it.
- New dataset: data/deployment_sites.json (category/subcategory keyed site rows
  with filings[] and sources[]); wire into check_citations.py + new test; NOT
  into build_data FILES yet (no UI this pass — site integration is a later PR).
- Then broad pass: per-sector site lists US+abroad (agents in parallel OK here).

## Next actions (strike as completed)

- [ ] Probe ADAMS + FERC eLibrary endpoints (curl) — validate before scripting
- [ ] tools/fetch_source.py + data/research/source_index.json + .gitignore cache
- [ ] Deep dive A (Eielson), B (Penn State), C (Copper Valley + CNSC comparator)
- [ ] data/deployment_sites.json schema + first rows + citation-gate wiring
- [ ] Try to close CPS/Xcel/NorthWestern filing absences via dockets
- [ ] Broad pass per 8 sectors (US + abroad lists)
- [ ] Evaluation write-up (what the gate covers, holes closed this pass)
- [ ] Commit early and often; update this file as things land
