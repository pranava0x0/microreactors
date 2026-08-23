# Site + data evaluation, and the deployment-sites research basis — 2026-08-23

One-session audit of "does every claim have a citation, and do the tests enforce it,"
followed by the depth-first deployment-sites research pass the citations were missing.
Everything below is committed on `jam/site-eval-deployment-research-b100c6`.

## 1. What the evaluation checked, and what it found

**Baseline was green:** 30/30 tests, `check_citations.py` clean, tree clean, Pages live.
Presence-level citation coverage was already enforced. The audit therefore went one level
deeper — *does the cited document say what the row says?* — and found three defects,
all fixed this session:

| Finding | Class | Fix |
|---|---|---|
| `canada-src` still "Funded / binding, pilot by 2029" — Westinghouse cancelled the SRC contract in fall 2025 and left commercial markets (SRC's own FAQ) | Stale counterparty status | Status/binding/timeline corrected; quote-locked to SRC's page; hero stat 10→9 binding rows |
| Penn State LOI milestone dated 2026-02-28, cited to a 2023 article that cannot contain it; the primary LOI (ML25059A029, now cached) is 2025-02-17, 15 MWt research-reactor CP | Claim-vs-source mismatch (the class issues.md logged on 2026-08-21) | Date fixed; re-cited to the LOI itself; Westinghouse `first_delivery_year` 2029→2030 (SRC basis gone; Malmstrom ANPI is the new basis) |
| A sectors.json quote span crossed PDF extraction glyph damage (`100%of` in the INL text layer) — network verification had passed under a different extractor | Quote-lock fragility | Span shortened per the documented rule; caught by the new offline gate below |

**Eielson upgrade:** the tracker's registered gap "primary DoD award document not
located" is closed — the DAF's own NOITA announcement (2025-06-11) and Oklo's release
are now the row's lead sources (both browser-captured and cached; those hosts 403
non-browser clients), and the row's status is honest about NOITA ≠ award.

**Tracker addition:** the December 2024 Oklo–Switch 12 GW non-binding master power
agreement was missing entirely; added (binding=false).

## 2. What now enforces this (tests: 30 → 40, all green)

- `tools/check_citations.py` — extended to scan `data/deployment_sites.json` rows and
  its `_meta.negative_findings`; mutation-checked in the test (a numbered, source-less
  row must fail).
- `tools/verify_quotes.py --cache` — new offline mode: every quoted source whose URL is
  in the source index must have its quote present in the cached bytes. 19 verified, 0
  mismatch at close; runs in the suite when `data/cache/` exists (gitignored, so CI
  skips it gracefully). It caught a real pre-existing defect on its first run.
- `tests/test_deployment_sites.py` — schema gate: statuses/depths must come from the
  file's own `_meta` enums, band labels must be exact `sectors.json` load labels
  (derived, not copied), source URLs full (bare homepages rejected), filings carry
  forum/type/url, `tracker_id`s must resolve into `opportunities.json`, deep rows need
  ≥2 evidence entries.

## 3. The reusable research kit (tools/)

| Tool | What it does | Validated against |
|---|---|---|
| `fetch_source.py` | Fetch → cache raw bytes (`data/cache/`, gitignored) → index in `data/research/source_index.json` with URL, access date, SHA-256, content type. `--from-file` indexes browser-captured bytes for hosts that 403 non-browser clients (recorded `capture: out-of-band`). `--list` reports. | 27 sources indexed this session |
| `adams_search.py` | NRC ADAMS full-text/docket search via the API behind adams-search.nrc.gov (`POST /api/search`, contract sniffed from the Angular app — the old adams.nrc.gov WBA endpoint no longer resolves). Direct nrc.gov/docs URLs in every hit. | eVinci docket 99902079 (244 docs), ACU 05000610, UIUC 99902094, RELLIS 99902136 |
| `ferc_elibrary.py` | FERC eLibrary search via `eLibraryWebAPI/api/Search/AdvancedSearch`; docket sweeps and description/full-text search; emits stable `filelist?accession_number=` permalinks. | "microreactor" description search: **0 hits ever** (a citable negative); Malmstrom's single 1994 tariff |
| `verify_quotes.py --cache` | Offline quote-lock verification against the cache (above). | 19/19 |

Capture rules learned (also in issues.md): nrc.gov/docs, *.af.mil, oklo.com, ktoo.org
403 non-browser TLS fingerprints — capture via the browser pane (text for HTML;
chunked base64 via same-origin `fetch` for PDFs) and index with `--from-file`.
ans.org returns a JS shell to urllib — always grep a cached page for the fact you
came for before citing it.

## 4. The deployment-sites dataset (`data/deployment_sites.json`)

Depth-first, then broad, per plan. **Deep rows** (primary documents read and cached):

- **Penn State FRONTIER** (Civic/universities): 2025-02-17 NRC LOI for a 15 MWt
  eVinci-based research-reactor construction permit; vendor pre-app docket 99902079
  carries 244 documents into mid-2026. Gap flagged: the promised REP has not appeared,
  and Westinghouse's exit from commercial markets makes the schedule a live question.
- **CVEA Valdez/Glennallen** (Utilities/remote grids): the full 59-page pre-feasibility
  study read — named Mountain Site at Mile 3 Dayville Road (bedrock bench below the
  Trans-Alaska Pipeline), 2×15 MWt replacing the Valdez cogen, CVEA-ownership beats
  vendor-ownership, up to 50% ITC; study positive, yet **tabled indefinitely
  2023-08-09** — the best-documented "looked and stopped" case in the class. Alaska
  SB 177 (siting statute) attached as the state-policy artifact.
- **Eielson AFB** (Defense/remote): NOITA 2025-06-11, 30-year firm-fixed-price after
  NRC licensing, electricity + heat; base context (72-year-old coal CHP, GVEA as sole
  backup) cited to Alaska Public Media.
- **Chalk River MMR** (abroad; the richest foreign filing trail): first SMR licence
  application in Canada (2019-04-02), CNSC-led CEAA 2012 EA — **paused**; USNC Chapter
  11. CNSC's "Current Status: Paused" quote-locked.
- **SRC eVinci** (abroad): cancelled by the vendor fall 2025 — the correction that also
  fixed the tracker.

**Scan rows** (broad pass): Texas A&M RELLIS (ESP project 99902136 + Aalo's own ESP
LOI ML26190A374), UIUC Kronos MMR (CP application received 2026-04-15), ACU MSRR
(construction permit **issued** 2024-09-16 — the furthest-advanced university row),
Last Energy Haskell County TX (30×PWR-20 for data centers; NRC REP + reported ERCOT
filing — the only US microreactor grid-side filing found), Last Energy Llynfi Wales
(coal-site repowering; ONR PDR done; SIP July 2026), Oklo–Diamondback Permian (50 MW
LOI — the named oil-and-gas counterparty).

**Negative findings** are first-class rows in `_meta`: FERC's zero-ever microreactor
description hits; Malmstrom's 1994-only filing history; and a `category_absences` note
for Mining / Agriculture / US-Transportation / hospital-prison-water bands, where no
named site exists to cite.

## 5. Where the next session picks up

backlog.md is current: state-PUC forums (CO, MT, San Antonio, RCA, ERCOT queue) are
the remaining docket systems; the site UI for the new dataset is the shipping gap;
five dated watch-items (FRONTIER REP, UIUC docketing, Aalo ESP, Eielson environmental
analysis, Chalk River disposition) have expiry semantics.
