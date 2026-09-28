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

## 2026-09-28 - PR #23 expert review

- Why: review the finished PR through nuclear-project, regulated-utility and energy-contract lenses.
- Tools: branch diff, data contracts and tests; no web or subagents.
- Cost: subagent token count not reported.
- Result: 8 findings: 2 P1 and 6 P2; all accepted for repair.
- Worth it: yes. It caught commercially material category errors that schema, citation and browser tests cannot detect.
