# Research pass — 2026-08-28 — apps

## Question
Real-world PPA/contract precedents for Compute, Manufacturing and Agriculture & Food sub-applications

## Seed (inline, before any agent)
- [ ] Has someone already enumerated this? Find the existing dataset/report first.
- [ ] 4–6 broad web searches across .gov, national labs, regulator dockets, trade press.
- [ ] Cache anything primary with `tools/fetch_source.py` (main session only — agents must not).

## Partition (one agent per line; each entity belongs to exactly one agent)
| agent | output file | scope | loads (data/sectors.json) |
|---|---|---|---|
| compute | apps-compute.json | Compute sector — data-center/AI power deals | Regional data centers; Company-owned data centers; Shared data centers; Supercomputing centers; AI and very large cloud data centers; Dedicated baseload and outage-protection blocks within larger data-center campuses |
| manufacturing | apps-manufacturing.json | Manufacturing sector — heavy-industry power/steam deals | Steel rolling and finishing plants; Cement plants; Lime plants; Chemical plants; Fertilizer plants; Hydrogen and low-carbon fuel plants; Pulp and paper mills; Large integrated sawmills and wood-products plants; Semiconductor fabs; Battery-cell plants; Battery-material plants; Battery-recycling plants |
| agri-food | apps-agri-food.json | Agriculture & Food sector — controlled-environment ag and food-processing power deals | Large lighted greenhouse campuses; Large indoor-growing facilities; Large land-based aquaculture operations; Remote seafood-processing plants connected to a year-round community grid; Very large meat, dairy and frozen-food plants; Large grain and oilseed mills; Integrated agricultural campuses combining growing, processing, refrigeration and water pumping |

Known starting material for `compute`: `docs/microreactor-demand-research.md` already
documents Microsoft/Constellation (TMI restart), Meta/Constellation (Clinton), Google/Kairos,
Amazon/X-energy + Energy Northwest + Dominion — these are real, dated, sourced nuclear PPAs.
Structure them as `nuclear: true` case records (re-verify each source is still live and the
quote still matches) rather than re-researching from scratch, then spend the research budget
on the non-nuclear incumbent price at data-center scale (utility large-load tariffs, on-site
gas/diesel backup costs, colocation power agreements) — that is the number a reactor has to beat.

## Gate
```bash
python3 tools/research_pass.py validate data/research/2026-08-28-apps
python3 tools/research_pass.py report data/research/2026-08-28-apps
```

## Integration
- [ ] Single writer: only the main session edits `data/*.json`.
- [ ] Cache every shipping source, then `python3 tools/verify_quotes.py --cache`.
- [ ] `python3 tools/build_gaps.py && python3 tools/build_data.py`
- [ ] `python3 -m unittest discover -s tests`
