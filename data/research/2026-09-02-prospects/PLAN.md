# Research pass — 2026-09-02 — prospects

## Question
For each open question on Deals > Prospects (issues #9-#17): what does the primary record say, and what is still absent?

## Seed (inline, before any agent)
Done 2026-09-02 with scripts, no agent tokens: `plan.json` (9 topics, 36 queries) run through `tools/web_search.py` into `seeds/digest.md`; SEC EDGAR full-text for TRISO, HALEU, Doyon Utilities, Global First Power, Last Energy and Micro Modular Reactor via `tools/news_watch.py --query` into `seeds/edgar.json`; the Doyon Utilities contract record via `tools/usaspending.py` into `seeds/usaspending-doyon.json`.
- [ ] Has someone already enumerated this? Find the existing dataset/report first.
- [ ] 4–6 broad web searches across .gov, national labs, regulator dockets, trade press.
- [ ] Cache anything primary with `tools/fetch_source.py` (main session only — agents must not).

## Partition (one agent per line; each entity belongs to exactly one agent)
| agent | output file | scope | skip-list |
|---|---|---|---|
| north | `north.json` | #9 Doyon/Fort Wainwright, #10 CVEA, #13 Red Dog, #14 Nunavut and Kivalliq | SRC, Chalk River, fuel, vendor prices, off-grid IPPs |
| vendors-fuel | `vendors-fuel.json` | #11 SRC, #12 Chalk River/GFP, #15 TRISO and HALEU, #16 published unit prices | anything in Alaska or Nunavut, off-grid IPPs |
| (wave 2, if budget) ipps | `ipps.json` | #17 off-grid power contractors' portfolio sites | everything above |

## Gate
```bash
python3 tools/research_pass.py validate data/research/2026-09-02-prospects
python3 tools/research_pass.py report data/research/2026-09-02-prospects
```

## Integration
- [ ] Single writer: only the main session edits `data/*.json`.
- [ ] Cache every shipping source, then `python3 tools/verify_quotes.py --cache`.
- [ ] `python3 tools/build_gaps.py && python3 tools/build_data.py`
- [ ] `python3 -m unittest discover -s tests`
