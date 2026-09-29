# Run log

## 2026-09-29 - Alaska dossier page: EIA power mix and AS 42.05 utility law

- Why: build a dedicated Applications › Alaska page and needed three things not yet in the
  dataset: EIA's Alaska generation mix by region, Alaska's public-utility/CPCN threshold for
  behind-the-meter generation, and cooperative governance rules for adding generation.
- Tools: one general-purpose subagent (web search/fetch only, no repo access), 143K tokens,
  35 tool uses, ~4 min; then the main session re-fetched and cached the two statute pages the
  agent could reach via WebFetch but that `tools/fetch_source.py` could not (403 to a non-browser
  client) using the built-in browser, and read the full AS 42.05.711 exemption list itself.
- Result: 3 findings in `data/research/alaska-dossier-2026-09-29/new-research.json`; folded into
  `data/alaska.json`'s `power_mix` and `regulatory_notes`, each re-cited to a locally cached page.
- Worth it: yes, and the deeper read paid for itself: the agent's own inference ("a single-customer
  reactor likely escapes RCA jurisdiction") is narrower than it first appears — AS 42.05.990(5)(B)
  counts even one customer as "the public" if it sits inside a utility's presently-or-formerly
  certificated territory and pays over $50,000/year. That distinction only turned up from reading
  the statute's own "public" definition, not from the agent's summary of it.

## 2026-09-28 - Alaska and Greenland pricing/contracts research

- Why: deepen 1-20 MW price comparators, utility filings, and mine-power contracts after the broad refresh.
- Tools: targeted web search/open, direct primary-page fetches, PDF extraction, `jq`, research-pass validator.
- Cost: subagent token count not reported.
- Result: 6 cases + 1 region in `data/research/2026-09-28-alaska-greenland-pricing/north.json`; 0 validator errors.
- Worth it: yes. Found exact $/MWh, escalation, term, MW/MWh, tariff, and modeled-LCOE evidence; explicitly preserved approval and contract-term absences.

## 2026-09-28 - Utility filings and contract approvals

- Why: find current regulator records that expose nuclear PPA approval and risk allocation.
- Tools: targeted regulator-domain search, docket/PDF reading, research-pass validator.
- Cost: subagent token count not reported.
- Result: 2 dockets in `data/research/2026-09-28-alaska-greenland-pricing/filings-contracts.json`; 0 validator errors.
- Worth it: yes. Added one approved nuclear PPA framework and one microreactor-specific regulator process while preserving redactions and non-procurement status.

## 2026-09-28 - PR #23 expert review

- Why: review the finished PR through nuclear-project, regulated-utility and energy-contract lenses.
- Tools: branch diff, data contracts and tests; no web or subagents.
- Cost: subagent token count not reported.
- Result: 8 findings: 2 P1 and 6 P2; all accepted for repair.
- Worth it: yes. It caught commercially material category errors that schema, citation and browser tests cannot detect.
