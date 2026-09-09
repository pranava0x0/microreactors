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
| 2026-09-09 | Utility filings for order book/insurance pool (5 findings, 10 absences) | y | high — corrected the ARC Act's "three or more projects" claim against the actual bill text (not in it — press paraphrase), found NRC's proposed Part 57 risk-tailored Price-Anderson coverage; wrote data/research/2026-09-09-orderbook-filings/utility-filings.json | 246K | None realistic — primary-filing verification (govinfo.gov, Federal Register, VA SCC) needs fetches, not search |
| 2026-09-09 | More order-book/insurance-pool evidence (3 nuclear_aggregation, 2 precedents, 1 risk_pooling, 5 design_notes) | y | high — found the Army's Janus Program was entirely absent from the base file (a demand-diversification strategy across 5 competing designs, not pooling), and pulled NEIL's real risk-scaling mechanics from its own audited financials; wrote data/research/2026-09-09-orderbook-filings/more-mechanisms.json | 277K | Borderline — the recency-check angles (UAMPS successor, EFI adoption, second Marsh placement) all came back empty; a tighter time-box on those could have saved ~20% |
| 2026-09-09 | Write up in-scope news candidates (4 investigated, 0 new records) | y | high — correctly judged all 4 candidates: 2 added as corroborating sources to existing records, 2 skipped as out-of-scope/no-new-fact, with reasons for each; no padding | 152K | Could have been a direct inline pass (~20K) — the judgment calls were straightforward once the 4 URLs were fetched |
| 2026-09-09 | PTC/45Y/48E status after OBBBA and 2026 (7 findings) | y | high — verified the site's nuclear-PTC claim against the enacted statute text (not just a law-firm summary), and found IRS Notice 2026-15's FEOC "material assistance" test, not yet reflected anywhere on the site, bearing directly on the site's own tracked TRISO deals; wrote data/research/2026-09-09-orderbook-filings/ptc-45y-48e-update.json | 139K | None — resolving conflicting secondary-source claims about the enacted deadline needed the primary statute |
| 2026-09-09 | AI in nuclear operations/policy survey (12 findings) | y | high — separated real named systems (Aalo+Microsoft permitting AI, DOE/INL/Argonne "Gordian" pilot, Project Prometheus) from unverifiable vendor marketing claims (Westinghouse eVinci "autonomous operation" is hardware I&C, not AI; Radiant's "ML fleet" traces to one 2023 blog post); wrote data/research/2026-09-09-orderbook-filings/ai-in-nuclear.json | 165K | None — this was genuinely open scouting with no existing site content to build from |

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

## 2026-08-28 — Applications financial-case pass (Compute, Manufacturing, Agriculture & Food)

Three agents, one wave, against `data/research/2026-08-28-apps/CONTRACT.md` — a narrower variant
of the deep-2026-08-24 contract adding an optional `load` field so a case can name the exact
Applications sub-application it prices, not just its sector.

| # | Agent | Worked | Quality | ~tokens | Best alternative in hindsight |
|---|---|---|---|---|---|
| 1 | Compute | y | high — 12 records (6 nuclear PPAs re-verified against primary sources, 6 non-nuclear incumbent prices); found xAI ran ~421 MW of unpermitted gas turbines at its Memphis site — the real incumbent in fast-growth AI campuses is unpermitted on-site gas, not a utility rate | 175K | none |
| 2 | Manufacturing | y | high — 7 records covering 8 of 12 loads; found Dow/X-energy's Seadrift, TX project (4×80MWe Xe-100, NRC construction permit docketed) — a real signed reactor-for-industry deal, the clearest "what a microreactor sale looks like" precedent in the whole corpus | 320K | none |
| 3 | Agriculture & Food | y | high — 8 records covering 5 of 7 loads; found USDA REAP is structurally incapable of reaching reactor scale (caps at $1M) and that a $1B-funded indoor-growing operator (Plenty) ran on ordinary grid tariff with no PPA at all before closing | 198K | none |

**What worked.** All three validated clean against the contract (0 errors, 27 records) on first
pass. Honest, specific absences throughout — e.g. "7 of 7 mining PPAs withhold $/kWh" pattern held
again; Manufacturing dropped two promising leads (Nucor Kingman, Intel/AEP Ohio) after the load's
own definition excluded them on inspection rather than writing weak matches.

**What the merge caught.** `tools/verify_quotes.py --cache` found 6 quote mismatches after merging
— all real, all fixable, none fabricated: two were verbatim spans crossing a glyph boundary a plain
tag-strip mangles (a curly-quoted defined term in a PDF, a `&nbsp;`-separated ® symbol, an HTML dollar
sign split across markup — the numeral+symbol-joint pattern this file already warns about), two were
paraphrase drift from the true verbatim sentence, and one was a genuinely wrong citation: a Corner
Brook Pulp and Paper PPA record cited a 2024-11 gov.nl.ca release for a "July 2026–June 2027" term
that release doesn't cover — the correct 2026-07-07 release existed and was found by a targeted
WebSearch. Fixed all six by re-checking the cached bytes (or fetching live via the Browser pane where
`fetch_source.py`'s urllib client hit a 403 — SEC EDGAR, Dominion's newsroom and CBRE all blocked the
plain UA but rendered fine in a real browser) before touching any quote text.

**Also fixed, orthogonal to this pass:** `tools/check_citations.py` never walked `benchmarks.json` or
`instruments.json` — the claim-coverage scanner's docstring claimed full coverage while two whole
data files, the ones carrying the dollar figures, were unchecked. Closed before adding any new
records so they'd actually be gated. `tools/merge_research.py` also gained multi-pass-dir support
(`nargs="+"`) — it previously rebuilt the derived files from exactly one pass dir, which would have
silently dropped the deep-2026-08-24 five sectors the moment this pass merged.

**Backfill, no new agents.** The `load` field only existed in this new pass's contract, so the
original five benchmark sectors (62 records, deep-2026-08-24) carried none — the priced-example
cross-link on the Applications tab worked for 3 of 8 sectors only. Tagged 55 of 62 existing records
by hand against the Applications loads they actually describe (7 left untagged — a courthouse
generator, a police-dispatch battery, nursing-home microgrids and similar don't map to any defined
sub-application). Zero web research, one script, one re-merge: sub-applications with a live example
went from 20 to 29, spanning all 8 sectors instead of 3.

**Gap-fill wave, deliberately small.** 9 sub-applications across Manufacturing and Agriculture & Food
still had zero priced case after the main pass, each already searched 1-5+ angles and documented as
absent. Rather than two more full-budget agents, ran one agent with an explicit low-expectation,
capped-budget brief: try only angles not already listed as tried, bail after two dead ends per load,
and treat 0-4 new records as a fine outcome. Result: 2 of 9 closed (Intel Ohio One's AEP substation
rate agreement, PUCO Case 24-734-EL-AEC; Eastman Kingsport's self-owned 200 MW CHP system) for 169K
tokens — versus ~320K per agent in the main pass. The other 7 (steel rolling, cement, lime, fertilizer,
sawmills, grain/oilseed mills, integrated ag campuses) stay honestly absent; the fresh angles tried
and why they failed are recorded in `data/research/2026-08-28-apps/apps-gapfill.json` `_meta.absences`
so a future pass doesn't retread them either. Sizing the follow-up agent to the marginal value of the
gap — not to the shape of the original fan-out — is what kept this cheap.

**Retrospective, after two Codex review rounds.** The 29-record pass (3 agents) plus the 2-record
gap-fill (1 agent) validated 0 errors against the contract and 0 citation-coverage/quote-cache
violations on first merge — but a *second* review round, after fixing round 1's findings, still
found two real data-quality bugs the gates couldn't catch: the gap-fill agent's Intel/AEP record
duplicated one the original Manufacturing agent had already written (days apart, no cross-pass
visibility), and that original record's own `capacity` field misattributed a 500 MW full-site
figure to a 50 MW substation — both real numbers from the same cited article, matched clean by the
quote gate, wrong in combination. Neither would have been caught without a reviewer that fetches
sources and reads past the first matching number; a broader post-merge duplicate sweep (by shared
source URL, then name/region/date) then found the same class of bug had shipped once already, in
the original deep-2026-08-24 pass (two agents, one wave, both writing the same Kokhanok, AK DOE
grant). Net for the wave: 31 candidate records in, 29 shipped, 2 real bugs required a human-grade
second read to find. Cheaper route in hindsight: none — this is exactly what the second review
round is for, and the fixes cost three replies and two small edits, not a re-research.

## 2026-09-02 — prospects pass: two Sonnet agents on the open questions, seeded by scripts

**Why it ran.** The commercial-strategy layer (Costs › What wins, Deals › Prospects) ended each
of 25 prospect rows with a first diligence question; ten of them were filed as GitHub issues
#9–#18. Nine are genuinely open web research (a regulator's rate case, a co-op's board release,
a bankruptcy sale, a prospectus), so a fan-out was the right tool. Two agents, not more, per
AGENTS.md; issue #17 (off-grid power contractors' portfolio sites) was left for a second wave.

**Seed before spawn, by script.** `tools/web_search.py` (new: a plan of 36 queries across 9
topics through DuckDuckGo's keyless endpoints into per-topic JSON and one digest),
`tools/news_watch.py --query` (new flag: SEC EDGAR full-text for TRISO, HALEU, Doyon Utilities,
Global First Power, Last Energy, Micro Modular Reactor → 376 filings, 119 after an issuer
filter) and `tools/usaspending.py` (Doyon's three Alaska contracts, $905M/$543M/$213M
obligated, 2007–2058). The web search got two topics in (Doyon 16 candidates, CVEA 7) before
DuckDuckGo rate-limited every later query for over twenty minutes; the seven empty topics were
handed to the agents as their own pre-planned query lists instead. Bing's keyless RSS was tried
as a fallback and dropped: it answers a scripted query with generic pages for its first word.
The gate came first: `research_pass.py` gained a Type C `answer` record (status answered /
partial / absent; a fetched source unless absent; a `for` that must be a strategy.json id) with
a negative test per rule, so agent output could fail before it reached the dataset.

**Cost and result.** north (#9, #10, #13, #14): 292K tokens, 72 tool uses, 14 min, 5 answers
(2 answered, 3 partial). vendors-fuel (#11, #12, #15, #16): 263K tokens, 82 tool uses, 15 min,
6 answers (2 answered, 4 partial). 0 absent, 0 cases, 0 validator errors, all 22 sources
fetched. Worth it: four of the eleven findings change a row's status or a segment's price
line (CVEA tabled on economics with the door open and four vendors already vetted; Global
First Power now owned by NANO Nuclear with the CNSC page still "paused"; the first public
TRISO price, $50–80M per metric ton of uranium, in Standard Nuclear's prospectus; 19 of
Nunavut's 25 plants over 1 MW), and three are documented absences that stop the next pass
re-searching them (no delivered fuel price at Fort Wainwright, Red Dog or Meliadine anywhere
public; no per-recipient HALEU quantities; the DOE clean-firm band is not in Oklo's filed deck).

**Integration.** A new generator, `tools/merge_answers.py`, copies the answers onto the rows
as `findings` (drift-tested), so a finding on the site always traces to a validated pass
record; the hand-written rows were then updated by hand. Caching the 22 sources with
`fetch_source.py`: three SEC documents 403 to the script's default user agent and had to be
fetched with curl and the SEC contact UA then indexed with `--from-file`; army.mil and
nsenergybusiness stay uncacheable (declared unverifiable, not failed). The quote gate then
found 5 near-misses in 22 quotes — a paraphrased lead-in, a hyphenated line break in a PDF, a
typo on the page ("owned" for "owed"), an encoding artefact in a Hansard transcript — each
re-copied to the verbatim span; the facts were unchanged. Five of twenty-two is the same rate
the 2026-08-29 voices pass saw, and it is why the gate runs on cached bytes and not on trust.

**One improvement.** Fetch and cache the primary documents the agents are going to need
(SEC filings, regulator PDFs) in the main session *before* spawning, since agents cannot write
the shared cache; and run the seed search at `--pause 8` in two halves rather than one burst.
