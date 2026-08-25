# Tooling survey — `pranava0x0` public repos, 2026-08-24

What already exists across the owner's other repos that this project should adopt or
shell out to, rather than rebuild.

**Scope.** 37 repos returned by `gh repo list pranava0x0 --limit 200`; 10 are private
(`DryDock`, `website`, `PersonalCRM`, `pitches`, `teaching-ideas`, and five pre-2018
personal repos) and were not opened. That leaves **26 public repos other than this
one**, of which **9 hold machinery worth taking** (two more are listed in the table
and rejected, so nobody re-opens them). None is archived.

**Licence, for all of them: `null` — no `LICENSE` file in any repo surveyed.** Same
owner, so reuse is not a legal problem here, but nothing is licensed for third-party
redistribution, and copying a file in should carry a provenance comment naming the
source repo and commit.

**The constraint that shapes every verdict below.** This repo is strictly stdlib-only
Python (`tools/*.py` import nothing outside the standard library). Several of the best
tools elsewhere are built on `requests` + `pydantic` + `pdfplumber`/`PyMuPDF`, or on
Node. Those cannot be pasted in; they are either ported (the logic is usually small),
or run out-of-process in their own repo and their output committed here.

---

## Summary

| Repo | What it does | Verdict | What it unlocks here |
|---|---|---|---|
| **brownfield-opportunities** | 21-connector siting pipeline over ~46.8k contaminated/federal sites; pure-Python spatial index; **already carries a 12-vendor / 32-commitment microreactor fleet file and a microreactor siting score** | `adapt` (data) + `copy-as-is` (`spatial.py`, `geom.py`) + `call-out-of-process` (connectors) | **Sites** and **Vendors** tabs: 21 commitment rows this repo does not have (9 Janus installations geocoded, 6 INL pilot-program reactors, Penn State, UIUC, 2 RELLIS, Valar, Deep Fission), each with source URLs; grid/rail/road/substation proximity for any site we add |
| **FERCforms** | The FERC document-audit tool. Downloads FERC audit-report PDFs out of eLibrary through the F5 WAF, extracts per-page text, structures findings→recommendations; plus a 50-state PUC crawler | `adapt` (the eLibrary PDF fetch) + `call-out-of-process` (the rest) | Closes the gap in `tools/ferc_elibrary.py`, which today returns filing *metadata* only. Lets a research pass read the text of a FERC filing, not just find it |
| **FERC-Orders-June-2026** | RM26-4 / large-load docket site: browser-side eLibrary docket-sheet sweeper and bulk comment downloader, PDF/DOCX→text with page markers, corpus validator | `adapt` (`elibrary-sweep.js`, `validate-comments.py`) | **Market design** and **Policy** tabs: a repeatable way to pull a whole FERC docket sheet and its comment bodies when the JSON search API is not enough |
| **nucleardeployment** | The sibling nuclear tracker (Node/Next). Source cache, **claim-term validator against cached text**, newsroom freshness canary, AI-prose linter, source-tier validator | `adapt` (port `validate-claims` and `check-news` to Python) | `validate-claims` catches the exact defect the 2026-08-21 audit found by hand (cited paper does not contain the number). `check-news` addresses the 2026-08-23 finding that 3 of 5 deep-dive rows were stale |
| **datacentercommunitybenefits** | Data-centre community-benefit tracker. **Stdlib-only** HTML→publication-date/quote extractor, link checker with Wayback fallback, scout/recheck research accelerators | `copy-as-is` (`connectors/extract.py`) + `adapt` (`check_links.py`) | Auto-extracting a source's publication date makes the "claim dated after its source" lint from 2026-08-23 mechanical. Wayback fallback turns a dead citation into a recoverable one |
| **vibe-coding-security** | Advisory tracker | `copy-as-is` (`tools/check-external-links.py`) | Stdlib link-rot gate with Wayback lookup and gate-shaped exit codes; a tighter, better-classified sibling of this repo's `tools/check_links.py` |
| **virginia-budget-explorer** | Source-verified static budget dashboard | `adapt` (`scripts/freshness.py`) | A drift canary: HEAD every cited source, compare `Content-Length` against the byte count recorded at capture, report re-issued documents. Feeds the **Sources** tab's staleness story |
| **datacenterwaterusage** | Water-use document pipeline; 20+ state/local scrapers (VA DEQ, Ohio EPA), EPA ECHO DMR, PDF text+table extraction | `call-out-of-process` | Cooling-water and siting-constraint evidence for the **Sites** tab, if that question is ever taken up. Too heavy (asyncio, structlog, pdfplumber) to import |
| **us-tpd-tracker** | Tech-prosperity-deals tracker | `adapt` (`pipeline/scrapers/federal_register.py`) | Federal Register JSON API, no key, full-text + date filters — a real source for the **Policy** tab that this repo currently has no connector for |
| **usgs-mineral-commodity-summaries** | USGS MCS viewer | `skip` (see Not relevant, with one exception noted) | PDF page-screenshot provenance pattern only |
| **uscbp-trade-tracker** | CBP trade-action tracker | `skip` | Generic cache/classify/crawl layer, nothing this repo lacks |

---

## The three named tools

### 1. `FERCforms` — the FERC document-audit tool

`https://github.com/pranava0x0/FERCforms` · Python · last push **2026-08-10** · licence
**none** · not archived · public.

**Purpose.** Download FERC audit reports (Form 1 / 2 / 6, financial and non-financial)
out of eLibrary, extract per-page text, and structure each into verbatim
findings → recommendations. 120-report corpus, 2014–present, plus prudence reviews and
state PUC audits ingested metadata-only.

**Entry points** (each stage is `python -m pipeline.<stage>`, run in this order):

| Stage | What it does | Flags |
|---|---|---|
| `pipeline.listing` | parse `data/listing.json` from a saved `/audits` HTML snapshot | `--snapshot PATH` `--out PATH` |
| `pipeline.backfill` | add FY2014–18 from a Wayback snapshot | |
| `pipeline.sources` | ingest non-FERC seeds from `data/seeds/*.json` | |
| `pipeline.fetch` | **the eLibrary download** → `data/raw/<accession>.pdf` | `--listing` `--limit N` `--force` |
| `pipeline.classify` | tag each PDF by FERC form | |
| `pipeline.extract` | PDF → per-page text JSON | `--limit N` |
| `pipeline.structure` | text → findings + recommendations | `--listing` `--limit N` |
| `pipeline.patterns` / `pipeline.build` | cross-report themes; bake site JSON | |

Also standalone: `python -m pipeline.state_puc_crawler [--dry-run] [--state CA,TX,NY] [--years 2014-2026]`,
a 50-state PUC directory with dedicated parsers for the major states and a generic
fallback, writing `SourceSeed` records.

**Data source hit.** `elibrary.ferc.gov`, via its **undocumented internal Web API** —
not an official published API, but a real JSON endpoint rather than HTML scraping.
No key. The sequence in `pipeline/fetch.py`:

1. `GET https://elibrary.ferc.gov/eLibrary/filelist?accession_number=<acc>&optimized=false`
   to seed the WAF session cookie;
2. `POST https://elibrary.ferc.gov/eLibraryWebAPI/api/File/DownloadPDF?accesssionNumber=<acc>`
   (yes, three s's) with body `{"serverLocation": ""}` and headers `Origin`, `Referer`,
   `X-Requested-With: XMLHttpRequest`;
3. accept only `200 + application/pdf + %PDF-` magic; 429 → linear backoff; 4 retries;
   2 s between requests; 180 s timeout because the server assembles the combined PDF
   on demand.

`pipeline/config.py` additionally records two hard-won facts worth copying verbatim
into any FERC or state-PUC fetcher here: **`www.ferc.gov` HTML is Cloudflare-gated to
scripts but born-digital PDFs under `/sites/default/files/` are not**, and several
official `.gov` hosts 404 or 403 any User-Agent containing the substring
`python-requests` while serving the identical public PDF to a browser UA. It keeps an
honest project UA as the default and falls back to a browser UA **only** on 401/403,
only for already-public documents.

**Dependencies.** **Not stdlib.** `requests`, `pydantic`, `pdfplumber`, `PyMuPDF`,
`beautifulsoup4`, `lxml`, `pandas`, all `==`-pinned (`playwright` dev-only). The
`fetch.py` logic itself, though, touches only `requests.Session` + cookies + headers —
a ~40-line stdlib port using `http.cookiejar` + `urllib.request`.

**I tested the download path from this repo's stdlib client, and it half-works today.**
Using `http.cookiejar.CookieJar` + `urllib.request` with the headers above:

- The cookie warm-up **succeeds**: `GET /eLibrary/filelist?...` returns `200 text/html`
  and sets `TS015bc54f`, `__cf_bm`, `46455243`.
- The `POST .../DownloadPDF` **reaches the application**, not a WAF wall — a 485 MB
  accession returned a structured `400` with
  `{"FileName":["TOTAL_FILE_SIZE_EXCEEDED_MAX. Total file sizes: 485,499,850 bytes"],"Code":"2"}`.
- But three accessions of very different sizes (34 KB smallest file; 20231220-5304;
  20251014-5017) all returned **Cloudflare `524` at ~125 s**. The origin builds the
  combined PDF synchronously and Cloudflare cuts the connection first, so FERCforms'
  180 s client timeout cannot help. **Verified 2026-08-25 from this machine.**

That is a real correction to two of the owner's own repos at once: FERCforms' comment
says the cookie dance works (verified 2026-05-22, and the *auth* half still does), while
`FERC-Orders-June-2026` says eLibrary is "Cloudflare-gated to automated fetch" (verified
2026-08-23). Both are half right. The API accepts a stdlib client and rejects it only on
a *timeout*, not on a challenge.

**The lead this leaves.** The search API this repo already calls returns, per hit, a
`transmittals[]` array carrying `fileId`, `fileName`, `fileType` and `fileSize` — so the
per-file download route exists and would sidestep combined-PDF assembly entirely. I
probed four plausible route/param spellings for it (`File/GetFile`, `File/Download`,
`File/DownloadFile`, `eLibrary/filedownload`) and the API answered `200 ""` to all of
them: it is a catch-all that returns an empty JSON string for an unknown route or
param name rather than a 404, so guessing cannot find it. The correct spelling has to be
read off the live Angular SPA's network tab once.

**Verdict: `adapt`.** Port `pipeline/fetch.py`'s cookie-warm + POST + PDF-magic
validation into `tools/ferc_elibrary.py` as a `--download ACCESSION` subcommand
(stdlib, ~40 lines), and copy `config.py`'s UA and Cloudflare notes into a comment.
Do **not** port `extract.py`/`structure.py` — those are pdfplumber/PyMuPDF-bound and
the findings→recommendations parser is shaped for audit reports, which is not what this
project reads. Treat the 50-state PUC crawler as `call-out-of-process`.

**What it unlocks here.** `tools/ferc_elibrary.py` searches filings and returns
metadata; nothing in `tools/` can read a filing's *text*. That is the binding constraint
on the interconnection-and-tariff evidence behind the **Market design** and
**Sites** tabs — every claim there currently rests on a docket number plus a filing
description. With the download path it rests on the document.

### 2. `brownfield-opportunities` — the brownfields tool

`https://github.com/pranava0x0/brownfield-opportunities` · Python · last push
**2026-08-25** (the most active repo surveyed) · licence **none** · not archived ·
public.

**Purpose.** A siting screen over ~46.8k contaminated and federal sites — EPA Superfund
NPL, EPA ACRES brownfields, DoD FUDS, BRAC, retired industrial — enriched with the
infrastructure facts that decide whether a site can host large load.

**Entry points.**

- `python refresh.py --list-sources` — print the 21 registered connectors.
- `python refresh.py --source <name>` — run one; `--all` runs everything.
- Flags: `--no-cache` (force fresh fetch), `--dry-run` (cached responses only),
  `--fetch-only`, `--output PATH`, `--pretty`, `--combined`, `--allow-ipv6`,
  `--missing-only`, plus per-connector flags such as `--infra-skip-flood-zone`
  and `--infra-skip-rail`.
- Curated one-shot builders under `scripts/`, each `python3 scripts/<name>.py` with no
  arguments: `build_microreactor_fleet.py`, `build_retired_industrial.py`,
  `build_planned_retirements.py`, `build_coal_conversions.py`,
  `build_doe_sites_e2e.py`, `build_ap1000_sites.py`, `check_upstream_freshness.py`.

**Data sources hit.** All public, all keyless, all official or documented endpoints —
no HTML scraping in the ones that matter here. EPA Superfund + ACRES + ECHO; DoD FUDS
and BRAC (ArcGIS REST); **EIA-860M "Preliminary Monthly Electric Generator Inventory"**
(public `.xlsx`, the "Retired" sheet — the canonical source for retired generator
locations post-2002); HIFLD `Electric_Power_Transmission_Lines` (~52k), HIFLD gas
pipelines (~33k), HIFLD `Power_Plants_in_the_US` (~13k); Census TIGERweb Railroads
(~112k) and Primary Roads (~17k); OpenStreetMap `power=substation` via Overpass;
FEMA NFHL flood zones (one ArcGIS query per site); Census workforce; IRA energy
communities; opportunity zones; tribal areas.

**Dependencies.** **Not stdlib**, but barely: `requests==2.32.3`, `pydantic==2.9.2`,
`openpyxl==3.1.5`. Two files are already pure stdlib and import nothing from the
package: `connectors/spatial.py` (`math`, `collections`, `typing`) and
`connectors/geom.py` (`math`, `typing`).

**Verdict: three different verdicts for three different pieces.**

- **`copy-as-is` — `connectors/spatial.py` + `connectors/geom.py`.** A uniform lat/lon
  grid index bucketing polyline segments by bounding-box cell, expanding ring by ring
  until the candidate minimum is a provable lower bound, with local-projection distance
  math (better than 1% in CONUS). It answers "nearest transmission line / rail / road"
  across 47k records with no shapely and no rtree — exactly the constraint this repo
  operates under. `geom.py` is the polygon half: `polygon_acreage()` corrects the
  degrees²-vs-metres error that a naive Shoelace on WGS84 coordinates produces.
- **`adapt` — the microreactor fleet data, `docs/data/microreactor-fleet.json`.**
  Built by `scripts/build_microreactor_fleet.py` (stdlib-only: `json` + `pathlib`), it
  carries 12 vendors, 32 commitments and 8 sectors on a 6-rung evidence ladder, each row
  with per-row source URLs and an explicit `gaps[]` list.
- **`call-out-of-process` — the 21 connectors.** They are `requests`/`pydantic`/`openpyxl`
  and hit heavy upstreams. Run `refresh.py --source infra-proximity` in that repo and
  commit the resulting lookup file here.

**What it unlocks here, measured rather than asserted.** I diffed the fleet file's 32
commitment ids against this repo's `data/opportunities.json` (16 rows):

- **21 commitment ids exist there and not here.** Two of those (`dome-inl`,
  `eielson-ak`) are renames of rows we already carry, so **19 are genuinely new**, and
  after netting out the four that `data/deployment_sites.json` covers under different
  ids (`psu-frontier`, `uiuc-kronos`, and the two RELLIS projects folded into
  `tamus-rellis`), about **15 rows appear in no dataset in this repo at all**.
- The largest single gain is **de-aggregation**. This repo carries `janus` as one row
  reading "nine candidate installations" and `doe-pilot` as one row reading "11
  projects". The fleet file carries those as 9 and 6 individually-sourced rows —
  Fort Benning, Fort Bragg, Fort Campbell, Fort Drum, Fort Hood, Fort Wainwright,
  Holston AAP, JBLM, Redstone Arsenal; then Pele, Antares Mark-0, Valar Ward 250,
  Deployable Energy Unity, Aalo CTR, Deep Fission Parsons.
- **Every geocodable row there has `lat`/`lon`; nothing in this repo does.** Neither
  `opportunities.json` nor `deployment_sites.json` carries a single coordinate. The
  Janus coordinates are joined from `ap1000-sites.json` rather than re-typed, so the
  two surfaces cannot disagree about where Fort Wainwright is.
- Vendors: 12 there against 3 here (`Antares`, `Radiant`, `Westinghouse`) — Oklo, BWXT,
  Aalo, Deep Fission, Last Energy, NANO, Valar, Deployable Energy, Terrestrial are all
  absent from `data/vendors.json`.

**One caveat that has to be stated plainly.** `build_microreactor_fleet.py`'s own
docstring says every row is "carried forward from" *this* project and
`nucleardeployment`. It is a downstream consumer, not an independent source. So the
19 new rows are net-new **relative to `data/opportunities.json`**, but they were curated
in that repo on 2026-08-21 from primary sources it cites per row — they are not
independent corroboration of anything already here, and importing them means importing
its citations too. Re-verify each against its own `sources[]` before it ships.

**The other half — the thing the brownfields angle was actually named for.** The 2026-08
finding that surplus grid interconnection lives at retiring industrial sites has a
ready-made connector: `connectors/eia_retired_plants.py` marks every site with the
distance to the nearest retired ≥100 MW dispatchable plant, and its docstring names the
exact thesis ("stranded high-voltage interconnection → fastest path to energising a
campus; the interconnect agreement is already grandfathered in many RTO tariffs").
`connectors/planned_retirements.py` and `scripts/build_retired_industrial.py` are its
forward-looking siblings. That is the **Sites** tab's missing screen, already built.

