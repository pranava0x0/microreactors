# Research pass — 2026-09-28 — Alaska, Greenland, filings and pricing

## Objective

Extend the 2026-09-26 full refresh with primary-source evidence that helps a buyer
price or contract for a 1–20 MW reactor. Focus on Alaska and Greenland, then on
utility filings and executed contracts elsewhere that expose risk allocation.

## Web discovery completed before agents

- Alaska RCA tariff filing TA401-13: GVEA/Aurora Energy amended PPA proposes
  $115.23/MWh in 2026, 2.8% annual escalation, and 150,000 MWh by year-end.
- Greenland Mineral Resources Authority: July 2026 Ramboll mine-energy study says
  100% renewable supply is presently more expensive than fossil alternatives, while
  hybrid supply can save money.
- Utah PSC Docket 25-035-55: commission approved the settlement for PacifiCorp's
  40-year Natrium PPA on 2026-06-01; public pricing remains redacted.
- Louisiana PSC February 2026 minutes: directive created the LANE program so
  investor-owned utilities and rural electric cooperatives can engage advanced
  nuclear vendors, including microreactors.
- Greenland mine comparators: Tanbreez/Nukissiorfiit agreement for up to 7.5 MW and
  30 GWh at the standard tariff; Malmbjerg plans a third-party 33–43 MW power tender,
  with about $150 million identified for renewable supply.

## Rules

- Primary source or regulator docket first. Two sources maximum per claim.
- Exact quote, 25 words maximum. Mark search-only evidence `snippet-only`.
- No inferred prices. Redacted prices stay redacted.
- Contracts must separate binding, approved, proposed and non-binding instruments.
- Save raw research here before editing generated or canonical datasets.

## Planned integration

1. Add qualifying dockets to `data/dockets.json` through a pass-local integration script.
2. Add priced non-nuclear power contracts to the applicable source research file,
   then regenerate `data/benchmarks.json` with `tools/merge_research.py`.
3. Update Greenland and Alaska region records only where new evidence changes the
   decision read or replaces a weaker source.
4. Add compact paths from likely user questions to the exact filing or price record.
5. Rebuild metadata, test, UAT, performance-test, review, push and open one PR.

