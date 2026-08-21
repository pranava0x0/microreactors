# Microreactor Opportunity Map

A lightweight, cited map of the microreactor business-development opportunity space —
built for evaluating where a 1–20 MW power block actually gets sold.

**[site/index.html](site/index.html)** — no build step, no framework, no dependencies.
Open it directly or serve the `site/` directory.

## What's here

| Path | What it is |
|---|---|
| `site/` | The visualisation. Static HTML/CSS/JS; data is inlined into `site/data.js`. |
| `data/*.json` | The dataset. Hand-curated except `gaps.json`, which is derived. |
| `tools/build_data.py` | Bundles `data/*.json` → `site/data.js` and computes the headline figures. |
| `tools/build_gaps.py` | Derives `data/gaps.json` (field coverage + next-pass plan) from the data. |
| `docs/segmentation.md` | Why international gov + industry are one track, and why international industry is not merged into U.S. commercial. |
| `docs/microreactor-demand-research.md` | Prior demand-side evidence base (Antares R1 pitch). |
| `docs/rian-research-chatgpt.md` | Sector load bands, annual-average electrical demand. |

## Rebuild

```bash
python3 tools/build_gaps.py && python3 tools/build_data.py
```

Both are idempotent. `build_data.py` computes every headline number on the page from the
rows beneath it, so the summary counts cannot drift away from the data — a hand-typed
"14 opportunities" in the markup would rot the first time a row was added.

## What this research knows and does not know

Sector, owner, timeline and power are well covered. **Land area, shell/enclosure and
utility filings are near-empty (1/14, 1/14 and 4/14 respectively)** and all three fail
for the same reason: web search does not index docket systems. More searching will not
fix them. The next pass needs direct queries against FERC eLibrary, state PUC dockets,
and NRC ADAMS — see the Evidence section of the site, generated from `data/gaps.json`.

Rows that show **not found** are honest absences. Nothing in this dataset is inferred to
fill a blank.

## Method

Web search only; no agent fan-out. Every one of the 14 opportunity rows carries at least
one source URL — rows without a source were not written. Figures carried over from the
two prior research documents are labelled as carried-forward rather than re-verified.
