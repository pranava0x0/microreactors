# Agent run log

One row per subagent/workflow run: why, cost, verdict, and the cheaper route in hindsight.

| Date | Run | Worked | Quality | ~Tokens | Cheaper route in hindsight |
|---|---|---|---|---|---|
| 2026-08-21 | Demand-band citations (55 loads, verdicts + quotes) | y | high — 23 supports / 18 partial / 2 contradicts / 12 not_found, honest verdicts, wrote to disk incrementally | 327K | None realistic — genuinely open web research across 8 sectors; the DOE Better Buildings CHP fact-sheet family it surfaced covered 7 rows and was not known beforehand |
| 2026-08-21 | Orderbook/insurance precedents (24 rows + design notes) | y | high — found the DOE Liftoff two-layer answer and EFI term sheet, which reshaped the proposal | 556K | Could have been ~30% cheaper with a tighter fetch cap; content justified it |
| 2026-08-21 | Regulatory pathways (34 rows) | y | high — corrected two citation errors in the brief itself (10 U.S.C. 2920 vs 2911(b); SB 177 date) | 209K | None — statute/docket verification needs fetches |
| 2026-08-21 | Site-flow reference scan (9 sites) | y | good — grounded the Tracker/Applications renames and the roadmap pattern | 126K | Borderline: ~half the value was 3 fetches (WNA, Antares, eVinci); a 5-fetch inline pass might have sufficed |
| 2026-08-21 | Sector power-context + band closures | y | high — 8/8 sector incumbent-power summaries with fetched sources (used verbatim on Applications); 12/12 bands resolved: 3 found, 1 derived, 8 honest not_founds; one white paper (Burns & McDonnell) closed two bands and corrected one | 283K | None — the not_founds were budgeted at 2 angles each by design, and the dead ends are now recorded in the load rows |
| 2026-08-24 | Creative demand applications deep-dive | y | high — 5 evaluated off-grid/hybrid spaces (Spaceports, Arctic defense radar outposts, Direct Air Capture, Subsea modules, Biorefineries) with power/steam metrics and primary citations written to data/research/creative-demand-applications.json | ~25K | Targeted search + fetch workflow was optimal |
| 2026-08-24 | Candidate deployment sites & docket follow-ups | y | high — resolved UIUC Construction Permit docketing (NRC Docket 50-618, docketed 2026-05-18), Aalo TAMUS RELLIS selection (Docket 99902128), and Last Energy Katowice/Legnica SEZ status; written to data/research/deployment-sites-followups.json | ~20K | Targeted federal register & ADAMS query |
| 2026-08-24 | UAT & UI/UX Expert Review & Design Refinements | y | high — clean URLs (default subtab hash pruning), full-width card prose, 2-col CSS grid for policy/precedents, interactive row chevrons, and mobile spacing tested across 375/768/1280/1440px | ~15K | In-process Playwright browser run + targeted CSS/JS updates |

Retro discipline: after each run, verify the file landed, spot-check 2–3 quotes against
their URLs, then fold the verified state into a deterministic gate (see
tools/check_citations.py) so the verification never has to be re-bought.
