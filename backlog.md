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
  (primary) in addition to the current secondary reporting. (DONE — 2026-08-25, cited to the
  Regulatory Commission of Alaska's own FY2024 order L2300184 rather than the AEA statistical
  report, whose PDFs exceed the fetch size limit; the order carries the per-utility appendix.)
- **low** · Sub-tabs for the Tracker's three buyer tracks if the row count grows: the
  track chips currently filter one list, which still reads fine at 16 rows. Costs,
  Market design, Policy and Sources got sub-tabs on 2026-08-23.

## From the 2026-08-24/25 deep research pass

- **high** · Cache and quote-verify every source that now ships. The pass added 111 records to
  `data/instruments.json` and `data/benchmarks.json`, but only the handful promoted into
  `costs.json` and `policy.json` have been through `tools/fetch_source.py` +
  `tools/verify_quotes.py --cache`. 124 registered URLs are still not-in-cache. Until they are,
  the site's own quote-lock gate cannot speak for the new rows. Run `fetch_source.py` from the
  main session only — it writes a shared index and concurrent agents corrupt it.
- **high** · ~~Finish the four agents the session limit killed on 2026-08-25.~~ Re-fired 2026-08-25;
  federal awards completed at 26 records. Original scope below for the remainder:
  **Finish the four agents the session limit killed on 2026-08-25.** Targets are recorded
  verbatim in each partial file's `_meta.absences` (`_meta.incomplete: true`) and summarised in
  `docs/RESUME-2026-08-25.md`: `mech-dockets.json` (2 of ~8 records — CT PURA 20-03-17, CT DEEP
  per-site award chart, NJ BPU TCDER + the DCO Energy intersection ruling, CPUC 2025 SGIP
  eligibility text, a 2025–26 large-load tariff); `mech-nuclear-structures.json` (6 of ~12 —
  utility rate-basing, ARDP/Dow cost-share, heat-not-electricity contracts, and decommissioning
  assurance / Price-Anderson / HALEU as contract terms); `apps-federal-awards.json` (FEMA
  BRIC/HMGP and DOE ERA still open — use `tools/usaspending.py`, not web search).
- **high** · The tooling survey of `pranava0x0`'s public repos never started —
  `docs/tooling-survey-2026-08-24.md` does not exist. Scope the FERC document-audit tool, the
  brownfields tool and the data-centre community-benefits tool. `ferc_elibrary.py` reads only
  filing metadata, so anything that retrieves FERC *document text* is the highest-value adoption;
  a brownfields dataset pairs directly with surplus interconnection, since both point at the same
  retiring-industrial sites.
- **med** · `site/data.js` is now 813 KB uncompressed, up from roughly 490 KB, because the two new
  datasets carry long prose. The repo's own rule is to minimise page weight. Either split the
  instruments and benchmarks payloads into lazily-fetched files loaded when their tab opens, or
  trim `what_it_is`/`summary` at build time and keep the full text in `data/`. If lazy-loading,
  cache the in-flight *promise*, not a boolean — a boolean set after the fetch resolves double-fetches
  under concurrent callers.
- **med** · The diesel group now carries 25 instruments against 2 for licensing. Twenty-five
  disclosures is past scanning length even collapsed. Either sub-group them by `family`
  (commercial contract / regulatory rule / utility tariff / public procurement) with a filter chip
  row, or promote the strongest eight and move the rest behind a "more instruments" disclosure.
- **med** · Fill the licensing group: it has 2 instruments because no agent was pointed at it.
  The obvious instruments are the NRC pre-application docket, the DOE authorisation route under the
  2025 executive orders, Part 53 vs Part 57 election, and the §104(c) non-profit research-reactor
  pathway Penn State used.
- **med** · Reconcile `data/benchmarks.json` sectors with the Applications tab's eight sectors.
  Benchmarks use the five sectors this pass researched; Applications uses Compute, Mining, Electric
  Utilities, Manufacturing, Oil & Gas, Transportation, Civic Infrastructure, Agriculture & Food.
  Marine terminals sit inside Transportation and medical campuses inside Civic Infrastructure, so a
  reader cannot currently get from a load band to the price that sector actually pays. Add a
  sector-to-sector map and cross-link both ways.
- **med** · Verify the surplus-interconnection census against megawatts, not filings. 35 executed
  agreements is a count of documents; no filing description states the capacity inherited, so the
  size distribution — the thing that decides whether a 1–20 MW reactor fits in the leftover
  headroom — is unknown. Opening a sample of the agreements themselves would settle it.
- **med** · Test that the two new datasets stay in sync with their research pass. `tools/merge_research.py
  --check` already exits 1 on drift but nothing runs it; wire it into `tests/` so an edit to a
  research file that never reaches `data/` fails CI, the same way the builders' sync gate works.
- **low** · Re-run `tools/ferc_census.py` on further instrument phrases — "black start service
  agreement", "provisional interconnection service", "replacement generation" — to see which other
  instruments are actually in use. The script already flags single-docket years and capped lists.
- **low** · No AHJ document accepting a non-diesel emergency power supply survived two passes, for
  a hospital or a data centre. This is the single most valuable missing artefact for the diesel
  group: it would convert the CMS argument from a reading of the waiver text into a precedent.
  Worth a targeted pass at state hospital-licensing agencies (California HCAI is the likeliest,
  given it certified Kaiser Ontario's battery as primary backup in April 2025).
- **low** · Record the confirmed negative on the Batteries tab: no reactor vendor has signed
  anything with any battery major as of 2026-08-24. The site currently states this as a `finding`
  row; the research pass re-confirmed it across a second independent search, which is worth noting
  so a third pass does not re-spend on it.

- **high** · Surface FEMA's benefit-cost data as its own figure. The federal-awards pass found that
  FEMA publishes a benefit-cost ratio and a net-value-of-benefits per project, and the numbers are
  one to two orders of magnitude above what is actually spent on the generator: WaterOne (Johnson
  County, KS) carries a 38.09 BCR and $261,096,991 of net benefits against a $6.54M project; Erie
  County Medical Center $67.6M against $15.1M; Cayuga Medical Center $81.1M against $11.6M. That is
  a published, federally-modelled willingness-to-pay ceiling for firm power at named critical sites
  — a far stronger anchor for a microreactor pitch than any $/kW, and nothing on the site uses it.
- **med** · Correct the "utility privatization" framing wherever it appears. The NAVFAC Beaufort
  contract carried at $251.4M is really $254,977,740.80 **for water and wastewater, containing no
  electricity at all**. Any argument that reads the 50-year utility-privatization vehicle as an
  electricity precedent needs re-checking against what each contract actually covers.
- **med** · Clean Ports has committed roughly $1.45B at two ports (PANYNJ $451.6M federal + $350.2M
  cost share, plus Los Angeles) to create electrical load and not one dollar to supply. Where no
  shore power exists MARAD's answer is to *rent* a mobile diesel generator — $9.86M obligated over
  five years for one laid-up vessel, leaving no asset behind. That pairing is the clearest
  load-without-supply story in the dataset and deserves a callout on the Applications tab.

## Copy and register (2026-08-25)

- **med** · Extend `tools/check_register.py` with the §11.2 moves that are regexable on authored
  display copy: register drift (`realis*`, `utilis*`, `whilst`, `in order to`), and UI narration
  (`carries a cited`, `links to its source`, `carry no citation`, `proven by`). Both were swept by
  hand on 2026-08-25 and nothing stops them coming back. Calibrate before landing it — a scan found
  ~9 register-drift hits that are false positives, because CPUC and CARB regulatory language quoted
  inside `instruments.json` legitimately uses "utilisation". Scope the pattern to authored fields
  and allowlist the quoted-regulation ones, or the gate is red on arrival and gets ignored.
- **low** · `which is why` appears 18 times across `microreactor_read` and absence prose, all
  agent-written. Used causally it is fine; at that density it is a tic. Worth one editing pass, and
  worth a line in the research-agent prompt template so the next pass does not reintroduce it.
- **low** · Move the `topOptions` cards out of `site/assets/app.js` and into a data file. They are
  the only display content whose prose and sources live in JavaScript, which is why three of their
  citations dangled unnoticed until 2026-08-25 — `index.html` was gated, `app.js` was not. There is
  a gate now (`test_app_js_hardcoded_citations_resolve`), but the content still bypasses the AI-
  register lint and the citation coverage scanner, both of which only walk `data/`.

