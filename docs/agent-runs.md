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

## 2026-08-24/25 — deep research pass: deal mechanisms + sector price benchmarks

Ten agents in three waves against one `CONTRACT.md`. Wave 1 (6) returned complete; wave 2 (3)
and the repo survey (1) were killed by a session limit mid-run.

| # | Agent | Worked | Quality | ~tokens | Best alternative in hindsight |
|---|---|---|---|---|---|
| 1 | Diesel mechanisms | y | high — 13 records, 11 absences, found the Uptime-vs-EPA conflict and that **no host anywhere has removed its diesel** | 172K | none; this is the pass's best single result |
| 2 | Battery mechanisms | y | high — 13 records; found CMS QSO-23-11-LSC already waives the generator-or-battery limit, and INL's optimiser wanting a 100 MWe battery on a 9.6 MWe reactor | 214K | none |
| 3 | Interconnection | y | high — 12 records; **corrected a premise in its own prompt** (SGIP Fast Track caps synchronous machines at 2 MW, so 2–20 MW reactors get the full study) | 202K | none |
| 4 | Remote + marine | y | high — 11 records; found the RCA per-utility order, a better price sheet than the AEA report the prompt named | 182K | none |
| 5 | Medical + civic | y | high — 12 records; found civic critical facilities are 220–800 kW, an order of magnitude under a reactor | 158K | none |
| 6 | Mining | y | high — 13 records; **falsified the prompt's premise** that this sector publishes contract prices (it publishes fuel volumes and capex; 7 of 7 PPAs withhold $/kWh) | 198K | none |
| 7 | Docket recovery | partial | 2 of ~8 records before the kill | — | fire earlier in the window |
| 8 | Federal awards | partial | 14 records; mining angle reported dry | — | should have used `tools/usaspending.py` from the start rather than web search |
| 9 | Nuclear structures | partial | 6 of ~12 records | — | fire earlier in the window |
| 10 | Repo survey | n | never started | — | non-research task; did not need to share the window with nine research agents |

**What worked.** One shared contract file + a validator written before launch: zero parse failures,
zero contract violations across 111 records from ten independent agents. Partitioning by entity with
explicit skip-lists produced no cross-agent duplicates. Requiring `_meta.absences` turned four
"failures" into a usable work list — the absences are what aimed wave 2 and what the resume doc runs on.
Three agents contradicted premises stated in their own prompts, which is the behaviour worth paying for.

**What to change.** (1) Launch order should put non-research and recovery agents *first*; they were
cheapest and died last. (2) Nine concurrent research agents against one shared 5-hour pool is what
caused the wall — serialise into two waves of four or five. (3) Tell agents which repo tools exist
even when forbidding them from running the ones that write shared state: three independently gave up
on FERC filings the repo can already fetch. (4) An agent's declared dead seam is a task for the
orchestrator, not a closed question.

### Wave 3 — the four killed agents, re-run after the limit reset (2026-08-25)

| # | Agent | Worked | Quality | ~tokens | Best alternative in hindsight |
|---|---|---|---|---|---|
| 7 | Docket recovery (resume) | y | high — 2 → 8 records; **corrected the AEP Ohio terms on two of three numbers** and found the cited tariff superseded in April 2026; confirmed CT PURA 20-03-17 a dead host with exact failure modes | 230K | none |
| 8 | Federal awards (resume) | y | high — 14 → 26 records; found FEMA publishes a benefit-cost ratio per project ($261M net benefits against a $6.54M generator) | 195K | should have been pointed at `tools/usaspending.py` in wave 2, not left to web search |
| 9 | Nuclear structures (resume) | y | high — 6 → 13 records; **Price-Anderson is a ~100× step function at exactly 100 MWe**, in 10 CFR with dollar figures | 211K | none |
| 10 | Repo survey | y | high — 37 repos, 10 relevant; **tested the FERC download route live** rather than trusting the README, and corrected two of the owner's own repos that disagree about whether eLibrary accepts automated fetch | 174K | should have been launched FIRST in wave 2: it was the cheapest and the only non-research task, and it died last having produced nothing |

**Resume economics.** Re-running four killed agents cost ~810K tokens and produced 45 new records
plus a 539-line survey. The alternative — treating the partial files as final — would have shipped
`mech-dockets.json` at 2 records and no survey at all. The incremental-write rule is what made the
resume cheap: each agent read its own partial file, kept what was there, and appended, so nothing
was re-researched.

**Two rules earned this wave.**
1. **Launch order should put the cheapest and most independent agent first, not last.** The repo
   survey needed no prior result, was the smallest job, and was the only one that returned nothing
   when the wall hit. Ordering by dependency instead of by cost lost it entirely on the first try.
2. **An agent's declared dead seam is a task for the orchestrator, not a closed question.** Three
   agents independently gave up on FERC filings that `tools/ferc_elibrary.py` fetches without
   trouble. They were correctly barred from running `tools/` (shared-index race), which means the
   main session has to read the absences as a work list — closing that one seam produced the
   surplus-interconnection census, the strongest single finding in the pass.
