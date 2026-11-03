# Refresh 2026-11-03: integration report

## News: 0 added

- none

## Validation of shipped data: 7 confirmed, 1 corrected, 1 need a human

- corrected policy/licensing: wrong: 'Alaska SB 177 (2022) and its 2025 regulations' -> 'Alaska SB 177 (2022) and its 2023 regulations'
- needs a human: news/last-energy-texas-dsa-approval-2026-10-08: wrong: claim found 0 times, apply by hand -> '2026-10-07'

## Utility filings: 0 added

- none

## Applications: 0 added

- none

## Prospects: 0 added

- none

## Main-session edits (2026-11-03)

- news/last-energy-texas-dsa-approval-2026-10-08: date 2026-10-08 -> 2026-10-07 (ANS 2026-11-02: "On October 7, Last Energy announced the DOE's approval of its DSA"; WNN covered it 2026-10-08). ANS added as a source; edited in `data/research/news/refresh-2026-10-08.json`, since `merge_news.py` regenerates `data/news.json`.
- policy/Texas HB 14: dropped "expandable toward $2B" (politics check `unsupported`; the cited governor's statement gives only $350 million, and ANS 2026-04-09 neither).
- vendors/evinci `test_reactor`: the row implied eVinci still held the 2027 DOME slot. NEI (2026-10-05, read in the browser pane, cached from file) says Westinghouse told NRIC about two months after the July 2025 selection that it would not take the slot; Deployable Energy now holds it. NEI added as a source.
- Dropped the integrator's duplicate WNN source on the Alaska row (same article, different URL casing).
