# Run log

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
