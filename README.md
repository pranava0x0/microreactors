# Microreactor Opportunity Map

A lightweight, cited map of the microreactor business-development opportunity space —
built for evaluating where a 1–20 MW power block actually gets sold.

**[site/index.html](site/index.html)** — no build step, no framework, no dependencies.
Open it directly or serve the `site/` directory.

## The seven tabs, and what each is for

| Tab | Question it answers |
|---|---|
| Pipeline | Who is buying now — signed instruments, by buyer track |
| Economics | What it costs against what it displaces, and whether the PTC survives the OBBBA (it does, for nuclear) |
| Vendors | Who builds the machines — the exact Air Force ANPI slate |
| Demand | Which loads fit a 1–20 MW block, each band cited |
| Market design | How early orders get cheaper — a shared orderbook + overrun pool proposal, argued from cited precedents |
| Policy | Rules that unlock the sale: diesel replacement, battery pairing, faster interconnection, licensing speed |
| Evidence | Every source cited anywhere on the site, plus field coverage and the honest gaps |

## What's here

| Path | What it is |
|---|---|
| `site/` | The visualisation. Static HTML/CSS/JS; data is inlined into `site/data.js`. |
| `data/*.json` | The dataset. Hand-curated except `gaps.json`, which is derived. |
| `data/research/` | Committed research trails from the citation passes (agent outputs, verbatim). |
| `tools/build_data.py` | Bundles `data/*.json` → `site/data.js`, computes the headline figures and the source register. |
| `tools/build_gaps.py` | Derives `data/gaps.json` (field coverage + next-pass plan) from the data. |
| `tests/` | The CI gate: citation coverage, generator sync/idempotency, HTML/CSS/JS contract, prose register. |
| `docs/` | Segmentation rationale and the two prior research documents. |

## Rebuild and test

```bash
python3 tools/build_gaps.py && python3 tools/build_data.py
```

```bash
python3 -m unittest discover -s tests
```

Both builders are idempotent and deterministic: the site's "captured" stamp derives from
the data files' own `_meta.captured` dates, never the wall clock, so CI
(`.github/workflows/ci.yml`) can regenerate everything and fail on any drift between the
data and the committed `site/data.js`. Every headline number on the page is computed from
the rows beneath it — a hand-typed "14 opportunities" in the markup would rot the first
time a row was added.

## Citation rules the tests enforce

- Every opportunity, vendor, cost band, incentive point and precedent carries at least
  one source with a full URL (bare homepages are rejected).
- Every demand load either carries a source or its label sits in an explicit
  `_meta.uncited` register — silence is the one state a band cannot be in.
- Policy rows marked `idea` are this site's own proposals and must NOT carry a source;
  everything else must.
- Authored prose is linted against the AI-register word list (verbatim quotes and
  source titles exempt).

## What this research knows and does not know

Sector, owner, timeline and power are well covered. **Land area, shell/enclosure and
utility filings are near-empty** and all three fail for the same reason: web search does
not index docket systems. More searching will not fix them. The next pass needs direct
queries against FERC eLibrary, state PUC dockets, and NRC ADAMS — see the Evidence tab,
generated from `data/gaps.json`.

Rows that show **not found** are honest absences. Nothing in this dataset is inferred to
fill a blank.
