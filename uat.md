# UAT - Alaska, Greenland, contracts and discovery

Date: 2026-09-28  
Status: PASS  
Environment: local static server, Playwright Chromium

## Scope

- Alaska and Greenland pricing evidence
- Utility filing and contract-approval paths
- Home-page answer density and navigation cost
- Search metadata, `llms.txt`, `robots.txt`, sitemap and JSON-LD
- Initial-load performance at phone, tablet and desktop widths

## Likely questions and path cost

| User question | Answer path | Clicks | Position / scroll |
| --- | --- | ---: | --- |
| What must power beat in rural Alaska? | Home, Applications card | 0 | Card starts 1.09 screens from top at 375 px |
| What is Greenland mine power worth? | Home, Applications card | 0 | Same card; EUR 199/MWh hybrid and EUR 297/MWh diesel are visible |
| What supports those regional figures? | Applications card -> Regions -> open record | 2 | Rural Alaska begins 2.32 screens into the phone view; Greenland 3.34 |
| Which regulators or utilities name advanced nuclear? | Home card -> Utility filings | 1 | Direct sub-tab route; 16 records render |
| Is the Natrium PPA approved, and is its price public? | Utility filings -> open Rocky Mountain Power record | 2 | Record starts 1.28 screens into the phone view; price is explicitly redacted |
| What published contracts, filings and cost figures can a reactor be compared against? | Home card -> Price to beat -> open first sector/record | 3 | Direct Costs sub-tab; sector groups keep 96 cases collapsed and visibly mark 2 proposed prices |

Finding: the two highest-value remote-market price questions now have zero-click answers. Full source context remains one route click plus one disclosure click. Greenland is the deepest likely record; its phone position is 3.34 screens into Regions.

## Performance

Cold local load. Transfer is the sum of initial resource `transferSize`; lazy region and docket chunks are excluded until opened.

| Viewport | Initial resources | Transfer | FCP | Home height |
| --- | ---: | ---: | ---: | ---: |
| 375 x 812 | 4 | 489,367 B | 44 ms | 4.17 screens |
| 768 x 1024 | 4 | 489,367 B | 124 ms | 2.67 screens |
| 1280 x 800 | 4 | 489,367 B | 48 ms | 2.58 screens |

Baseline was 488,005 B with four resources. Change: +1,362 B (+0.28%). FCP remained below 125 ms in all three local runs. Mobile Home shortened from 4.2 to 4.17 screens despite adding the two price answers.

## Scenarios

- PASS: tablet checked first; no overflow or clipped card text.
- PASS: phone 375 x 812; eight directory cards, exact Alaska/Greenland price text, readable headlines.
- PASS: desktop 1280 x 800; two balanced four-card rows and two-column headline layout.
- PASS: direct `#demand/regions`, `#economics/price-to-beat`, and `#policy/utility-filings` routes survive lazy loading.
- PASS: 24 region records, 16 docket records and 96 benchmark records render.
- PASS: sitemap contains only the canonical crawlable URL; fragments stay in `llms.txt` as navigation hints.
- PASS: JSON-LD download URLs point to raw JSON, not GitHub HTML views.
- PASS: generic `User-agent: *` allow rule covers people-facing and agent crawlers; sitemap is declared.
- PASS: every cost-band value and all three axis ticks state a per-MWh unit; values distinguish `US$` from `source $` when currency is unstated. The chart explains LCOE, FOAK and NOAK and warns that dollar years were not normalized.
- PASS: cost chart at 375 px and 1280 px has no horizontal overflow after adding unit suffixes.
- PASS: screenshots reviewed; no visible overlap, truncation, blank panel or horizontal overflow.

## Evidence

- `screenshots/2026-09-28-alaska-greenland-375.png`
- `screenshots/2026-09-28-alaska-greenland-768.png`
- `screenshots/2026-09-28-alaska-greenland-1280.png`
- `screenshots/2026-09-28-cost-units-375.png`
- `screenshots/2026-09-28-cost-units-1280.png`

The pricing-focused pass found no new product defect and added no `issues.md` entry.

## Full navigation and reading-length pass — 2026-09-28

- Chromium at 375×812, 768×1024, and 1280×900: 135 panel/sub-tab visits across all 9 primary tabs. Every route showed the expected active tab and content; no page-level horizontal overflow, empty panel, dead placeholder link, or JavaScript exception.
- Checked first-screen screenshots for every primary tab at each width. Type family, section headings, colors, and card treatment remained consistent. Narrow navigation shows the active tab and scroll cues. Filter chips and the cost table scroll inside their own bounded containers.
- Phone reading length: `Sources > In their words` was 11.4 screens because the first quote group opened by default. Fixed to a 4.9-screen index; the quotes still open on demand. `Deals > Sites` and `Costs > What wins` remain the longest data views at 8.3 screens; both have sectioning or filters.
- JBSA: Antares and JBSA describe **one proposed prototype microreactor**. No committed JBSA unit order was disclosed. The tracker now says this explicitly and cites both primary pages. Fort Bragg's three-unit Janus deployment is separate.
- Browser regression: the Voices index starts collapsed and expands on click. Full suite: 122 tests.
