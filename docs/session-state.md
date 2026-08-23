# Session state — 2026-08-23 (site eval + deployment-sites research) — COMPLETE

Resume file: a fresh session reads THIS file plus `git log -5`. This session's work is
committed on `jam/site-eval-deployment-research-b100c6` (worktree); not yet pushed/PR'd —
that is the user's call. Full write-up: docs/evaluation-2026-08-23.md.

## What landed (all committed, 40/40 tests green)

1. **Evaluation**: baseline 30 tests green; the deeper claim-vs-source audit found and
   fixed three data defects (canada-src a year stale — Westinghouse cancelled SRC fall
   2025; Penn State LOI milestone mis-dated 2026-02-28 → 2025-02-17 and mis-cited to an
   article predating it; a quote span crossing PDF glyph damage). Eielson row upgraded
   to primary DAF/Oklo sources, closing its registered gap. Oklo–Switch 12 GW MPA added
   to the tracker (was missing).
2. **Tools** (each validated live before use): fetch_source.py (fetch→cache→index,
   --from-file for 403 hosts), adams_search.py (new adams-search.nrc.gov API — old
   adams.nrc.gov is gone), ferc_elibrary.py, verify_quotes --cache (offline quote gate;
   caught a real pre-existing defect on first run). 26 sources indexed with URL +
   access date + SHA-256; raw bytes in gitignored data/cache/.
3. **data/deployment_sites.json**: 5 deep rows (Penn State FRONTIER, CVEA Valdez —
   tabled after a positive study, Eielson, Chalk River — paused, SRC — cancelled) +
   6 scan rows (RELLIS, UIUC Kronos, ACU MSRR permitted, Last Energy Haskell + Llynfi,
   Oklo–Diamondback) + negative findings (FERC zero microreactor filings ever;
   Malmstrom's only filing is a 1994 tariff) + category absences. Gated by
   tests/test_deployment_sites.py (enums from _meta, bands locked to sectors.json,
   tracker_ids resolve, mutation-checked scanner coverage).

## Open threads (see backlog.md for the full list)

- State-PUC docket forums not yet queried: CO PUC, MT PSC, San Antonio agendas,
  Alaska RCA, ERCOT queue number.
- Site UI for deployment_sites.json (a Sites layer/tab) — dataset is ready, render isn't.
- Watch items with dates: Penn State FRONTIER REP (overdue vs. 'later in 2025' promise),
  UIUC CP docketing decision, Aalo RELLIS ESP (docket 99902128), Eielson environmental
  analysis, Chalk River post-bankruptcy disposition.
- DAF Microreactor FAQs PDF still uncaptured (af.mil 403s curl; browser chunk flow).

## Session mechanics notes

- The 16-min resume timer (cron ce715fb0, 13:02) was set first as asked; the usage
  window never cut the session, so it was deleted at close.
- Capture rules for blocked hosts and the ans.org JS-shell trap are in issues.md.
