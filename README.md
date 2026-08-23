# Microreactor Opportunity Map

A lightweight, cited map of the microreactor business-development opportunity space —
built for evaluating where a 1–20 MW power block actually gets sold.

**[site/index.html](site/index.html)** — no build step, no framework, no dependencies.
Open it directly or serve the `site/` directory.

## The seven tabs, and what each is for

| Tab | Question it answers |
|---|---|
| Tracker | Who is buying now — signed instruments, by buyer track (named "Tracker" after WNA's SMR project tracker; WoodMac defines "pipeline" as the whole announced market, which this is not) |
| Costs | What it costs against what it displaces, and whether the PTC survives the OBBBA (it does, for nuclear) |
| Vendors | Who builds the machines — the ANPI slate, each with a cited deployment roadmap |
| Applications | Which loads fit a 1–20 MW block (Westinghouse's own term for this content), each band cited, plus how each sector powers itself today |
| Market design | How early orders get cheaper — a shared orderbook + overrun pool proposal, argued from cited precedents |
| Policy | Rules that unlock the sale: diesel replacement, battery pairing, faster interconnection, licensing speed |
| Evidence | Every source cited anywhere on the site, plus field coverage and the honest gaps |

## What's here

| Path | What it is |
|---|---|
| `site/` | The visualisation. Static HTML/CSS/JS; data is inlined into `site/data.js`. |
| `data/*.json` | The dataset. Hand-curated except `gaps.json`, which is derived. |
| `data/deployment_sites.json` | Candidate deployment sites per Applications category (US + abroad) with their regulatory filing trails. Gated by `tests/test_deployment_sites.py`; not yet rendered by the site (backlog). |
| `data/research/` | Committed research trails from the citation passes (agent outputs, verbatim), plus `source_index.json` — every fetched source document: URL, access date, SHA-256 of the cached bytes. |
| `data/cache/` | Raw bytes of every indexed source (gitignored; rebuild with `tools/fetch_source.py`). |
| `tools/build_data.py` | Bundles `data/*.json` → `site/data.js`, computes the headline figures and the source register. |
| `tools/build_gaps.py` | Derives `data/gaps.json` (field coverage + next-pass plan) from the data. |
| `tools/check_citations.py` | Claim-coverage scanner: any record whose prose carries a hard number must have a source, be registered uncited, or sit on a reasoned allowlist. Wired into the test suite. |
| `tools/check_links.py` | Liveness sweep over every cited URL (dead/blocked/live). Network-dependent, so run locally on demand, never in CI. |
| `tools/fetch_source.py` | Fetch → cache → index a source document (URL + access date + SHA-256). `--from-file` for hosts that 403 non-browser clients. |
| `tools/adams_search.py` | NRC ADAMS docket/full-text search (the only way to find NRC filings — web search does not index ADAMS). |
| `tools/ferc_elibrary.py` | FERC eLibrary docket/full-text search, same rationale. |
| `tools/verify_quotes.py` | Quote-lock verification: network mode upgrades snippet-only sources; `--cache` verifies every quoted source offline against `data/cache/`. |
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
utility filings are near-empty on the tracker** because web search does not index docket
systems. The 2026-08-23 pass built the direct-query tools (`tools/adams_search.py`,
`tools/ferc_elibrary.py`) and ran them: NRC ADAMS and FERC eLibrary are now covered —
including the negative results (FERC has zero microreactor filings; see
`data/deployment_sites.json` `_meta.negative_findings`) — while state PUC forums
(CO, MT, San Antonio, Alaska RCA, the ERCOT queue) remain open in `backlog.md`.
Site-level filing trails live in `data/deployment_sites.json`; see also
`docs/evaluation-2026-08-23.md`.

Rows that show **not found** are honest absences. Nothing in this dataset is inferred to
fill a blank.
