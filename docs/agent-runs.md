# Agent run log

One row per subagent/workflow run: why, cost, verdict, and the cheaper route in hindsight.

| Date | Run | Worked | Quality | ~Tokens | Cheaper route in hindsight |
|---|---|---|---|---|---|
| 2026-08-21 | Demand-band citations (55 loads, verdicts + quotes) | y | high — 23 supports / 18 partial / 2 contradicts / 12 not_found, honest verdicts, wrote to disk incrementally | 327K | None realistic — genuinely open web research across 8 sectors; the DOE Better Buildings CHP fact-sheet family it surfaced covered 7 rows and was not known beforehand |
| 2026-08-21 | Orderbook/insurance precedents (24 rows + design notes) | y | high — found the DOE Liftoff two-layer answer and EFI term sheet, which reshaped the proposal | 556K | Could have been ~30% cheaper with a tighter fetch cap; content justified it |
| 2026-08-21 | Regulatory pathways (34 rows) | y | high — corrected two citation errors in the brief itself (10 U.S.C. 2920 vs 2911(b); SB 177 date) | 209K | None — statute/docket verification needs fetches |
| 2026-08-21 | Site-flow reference scan (9 sites) | y | good — grounded the Tracker/Applications renames and the roadmap pattern | 126K | Borderline: ~half the value was 3 fetches (WNA, Antares, eVinci); a 5-fetch inline pass might have sufficed |
| 2026-08-21 | Sector power-context + band closures | pending | — (fill in when the run completes; never log a result before the notification arrives) | — | — |

Retro discipline: after each run, verify the file landed, spot-check 2–3 quotes against
their URLs, then fold the verified state into a deterministic gate (see
tools/check_citations.py) so the verification never has to be re-bought.
