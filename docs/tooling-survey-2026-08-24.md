# Tooling survey — `pranava0x0` public repos, 2026-08-24

What already exists across the owner's other repos that this project should adopt or
shell out to, rather than rebuild.

**Scope.** 37 repos returned by `gh repo list pranava0x0 --limit 200`; 10 are private
(`DryDock`, `website`, `PersonalCRM`, `pitches`, `teaching-ideas`, and five pre-2018
personal repos) and were not opened. That leaves **26 public repos other than this
one**, of which **10 hold machinery worth taking** (three more appear in the
table with a `skip` verdict, so nobody re-opens them). None is archived.

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
| **FERCforms** | The FERC document-audit tool. Downloads FERC audit-report PDFs out of eLibrary through the F5 WAF, extracts per-page text, structures findings→recommendations; plus a 50-state PUC crawler | `adapt` (the eLibrary PDF fetch) + `call-out-of-process` (the rest) | Closes the gap in `tools/ferc_elibrary.py`, which today returns filing *metadata* only. Lets a research pass read the text of a FERC filing, not just find it. **Caveat: I retested the combined-PDF endpoint on 2026-08-25 — the auth half still works from stdlib, but it now 524s at ~125 s. See §1.** |
| **FERC-Orders-June-2026** | RM26-4 / large-load docket site: browser-side eLibrary docket-sheet sweeper and bulk comment downloader, PDF/DOCX→text with page markers, corpus validator | `adapt` (`elibrary-sweep.js`, `validate-comments.py`) | **Market design** and **Policy** tabs: a repeatable way to pull a whole FERC docket sheet and its comment bodies when the JSON search API is not enough |
| **nucleardeployment** | The sibling nuclear tracker (Node/Next). Source cache, **claim-term validator against cached text**, newsroom freshness canary, AI-prose linter, source-tier validator | `adapt` (port `validate-claims` and `check-news` to Python) | `validate-claims` catches the exact defect the 2026-08-21 audit found by hand (cited paper does not contain the number). `check-news` addresses the 2026-08-23 finding that 3 of 5 deep-dive rows were stale |
| **datacentercommunitybenefits** | Data-centre community-benefit tracker. **Stdlib-only** HTML→publication-date/quote extractor, link checker with Wayback fallback, scout/recheck research accelerators | `copy-as-is` (`connectors/extract.py`) + `adapt` (`check_links.py`) | Auto-extracting a source's publication date makes the "claim dated after its source" lint from 2026-08-23 mechanical. Wayback fallback turns a dead citation into a recoverable one |
| **vibe-coding-security** | Advisory tracker | `copy-as-is` (`tools/check-external-links.py`) | Stdlib link-rot gate with Wayback lookup and gate-shaped exit codes; a tighter, better-classified sibling of this repo's `tools/check_links.py` |
| **virginia-budget-explorer** | Source-verified static budget dashboard | `adapt` (`scripts/freshness.py`) | A drift canary: HEAD every cited source, compare `Content-Length` against the byte count recorded at capture, report re-issued documents. Feeds the **Sources** tab's staleness story |
| **datacenterwaterusage** | Water-use document pipeline; 20+ state/local scrapers (VA DEQ, Ohio EPA), EPA ECHO DMR, PDF text+table extraction | `call-out-of-process` | Cooling-water and siting-constraint evidence for the **Sites** tab, if that question is ever taken up. Too heavy (asyncio, structlog, pdfplumber) to import |
| **us-tpd-tracker** | Tech-prosperity-deals tracker | `adapt` (`pipeline/scrapers/federal_register.py`) | Federal Register JSON API, no key, full-text + date filters — a real source for the **Policy** tab that this repo currently has no connector for |
| **FirstPassRx** | Formulary/prior-auth reference site. Node-builtins-only source archiver with sha256 drift detection and **secret redaction before write**; offline provenance gate | `adapt` (the redaction step for `tools/fetch_source.py`) | Closes a live path from a third-party page's embedded API key to a commit — a documented 2026-07-07 incident there. Also a cleaner `last_verified`-vs-`sha256` drift model than this repo's single `fetched` date |
| **roboticsleadership** | Robotics-leadership tracker | `skip` | Same archive/check pattern as FirstPassRx, less well documented |
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

### 3. `datacentercommunitybenefits` — the data-centre community-benefits tool

`https://github.com/pranava0x0/datacentercommunitybenefits` · Python · last push
**2026-08-24** · licence **none** · not archived · public.

**Purpose.** Track what hyperscalers promise a community when they site a data centre,
what the community says back, and what the tariff/rate case actually does — companies,
claims, projects, community responses, moratoriums, ratepayer-protection provisions.

**Entry points.**

- `python refresh.py` — the pipeline driver.
- `python check_links.py` · `--fix` (write `wayback_url` back into the seed JSON and
  append to `ISSUES.md`) · `--dry-run`. Writes `dead_links_report.json`.
- `python scripts/validate_moratoriums.py`, `scripts/build_rate_cases.py`,
  `scripts/build_signatories.py`, `scripts/update_ratepayer_v119.py`,
  `tools/build_preview.py`.
- `connectors/` is a library, not a CLI: `scout.py` (find candidate records),
  `research.py`, `recheck.py` (re-verify what was found), `dedupe.py`, `extract.py`,
  `http.py`. `scout`/`harvest` take `--html-file` so a page fetched through a real
  browser can be fed back in.

**Data sources hit.** Named news outlets and company first-party data-centre pages,
fetched as **HTML and parsed with regex — no API**. Plus the **Wayback Machine CDX API**
(public, keyless) for dead-link recovery. `connectors/extract.py` maintains an explicit
first-party domain map (`datacenters.atmeta.com` → meta, `local.microsoft.com` →
microsoft, …) and, usefully, a `JS_RENDERED_DOMAINS` set plus a `needs_browser(url, page)`
heuristic that flags a 200 with under 600 characters of body text as an SPA shell —
the exact failure this project hit on 2026-08-23 when a fetched page turned out to be a
JS stub.

**Dependencies.** The repo as a whole needs `pydantic` and `requests`. **But the two
files worth taking are stdlib-only and say so in their own docstrings:**

- `connectors/extract.py` — "Stdlib only (no bs4 dependency)": `html`, `json`, `re`,
  `datetime`, `urllib.parse`.
- `check_links.py` — `urllib.request`, `urllib.error`, `json`, `time`, `collections`.

**Verdict: `copy-as-is` for `connectors/extract.py`; `adapt` for `check_links.py`; `skip`
the rest.** The scout/research/recheck loop is bound to that project's Pydantic schema
and its editorial rules about stance and constituency, none of which transfer.

**What it unlocks here.**

- `extract_pub_date(page)` walks JSON-LD (`datePublished`/`dateCreated`/`uploadDate`,
  nested, via a recursive `_walk_ld`), then a meta-tag alternation covering
  `article:published_time`, `og:published_time`, `datePublished`, `sailthru.date`,
  `parsely-pub-date`, then `<time datetime=…>` — and validates the result is a real
  calendar date before returning it, returning `None` rather than guessing. That turns
  the **2026-08-23 candidate lint into something mechanical**: this repo recorded
  "flag any milestone whose source predates its date" as a lesson after a 2026-02-28
  claim cited a 2025-02-17 document, but has no way to *get* a source's publication
  date. This is that missing half, and it drops straight into `tools/fetch_source.py`
  as an extra index field.
- `extract_quotes` surfaces `<blockquote>` and commitment-cue sentences from a page as
  candidate verbatim spans — a feeder for `tools/verify_quotes.py`, which today needs a
  quote span chosen by hand.
- `check_links.py`'s **Wayback CDX fallback** is the piece `tools/check_links.py` lacks:
  today a dead citation is classified dead and stays dead. With a CDX lookup a dead URL
  becomes a recoverable one, and `--fix` writes the archived URL back into the data.

---

## Other reusable machinery

### `nucleardeployment` — `scripts/validate-claims.mjs` and `scripts/check-news.mjs`

TypeScript/Next, last push 2026-08-23, licence none. `npm run data:claims`
(`-- --web`, `-- --company X`, `-- --json`) checks **every record against its own cited
source**: does the cached page actually contain the figures, dates and names the record
claims? Cache first, web second, so a normal run is free, offline and deterministic.
Its docstring is blunt that this catches "a real, reachable, plausible URL that does not
say what the site says it says", and that the defect shipped there and survived three
review rounds. That is precisely the 2026-08-21 finding in this repo — three cost rows
citing a real paper for capex/LCOE figures it does not contain, all of which survived an
expert-review pass because that pass checked reasoning, not provenance.
`npm run data:news` derives a newsroom watch list by truncating already-cited URLs down
to their `/news//press//newsroom/` index and reports which have changed — a canary for
the 2026-08-23 finding that 3 of 5 deep-dive subjects had status-changing corrections.

`scripts/lib/source-cache.mjs` is the reusable core: `urlHash`, `readCachedText`,
`htmlToText`, `claimTerms(label)`, `missingTerms(text, terms)`, `looksLikeWall(text)`,
plus `apiUrlFor` / `textFromFederalRegisterApi` for the Federal Register.

**Dependencies.** The scripts themselves import only `node:crypto` and `node:fs/promises`
— no npm packages. But `scripts/lib/records.mjs` does `import("../../app/data.ts")`,
so running them out-of-process needs that repo's TypeScript data modules and a
type-stripping Node. **Verdict: `adapt` — port the algorithm, not the script.** The
`claimTerms`/`missingTerms`/`looksLikeWall` trio is maybe 80 lines of stdlib Python
against `data/cache/` and `data/research/source_index.json`, which this repo already
maintains. It would slot in beside `tools/check_citations.py` as the check that closes
the loop between a citation existing and a citation being true.

### `FERC-Orders-June-2026` — docket sweep and comment corpus

JavaScript, last push 2026-08-23, licence none. Three pieces:

- **`tools/elibrary-sweep.js`** — a *browser snippet*, explicitly not a Node script,
  pasted into an eLibrary docket-sheet page via the Chrome bridge and read back from
  `window.__sweep`. It encodes two facts that cost a sweep to learn: eLibrary sorts
  ascending so the newest rows are **not** all on the last page (AD26-7 had 32 of 67
  recent filings sitting on page 1), and the Chrome bridge discards an async IIFE's
  return value. Rows accumulate into a `Map` keyed by accession.
- **`tools/grind-comment-downloads.js`** — bulk comment-body download via hidden
  iframes, with the one-time `chrome://settings/content/automaticDownloads` prerequisite
  documented (without it every download past the first silently fails).
- **`tools/validate-comments.py`** — corpus gate: every inventoried comment has a body
  on disk, every PDF opens with pages, every body has >200 chars of real text.
  Distinguishes missing / corrupt / **scanned** (image-only, empty text layer) and exits
  non-zero only on an unexpected problem, with a `KNOWN_MISSING` allowlist. Needs
  PyMuPDF. `tools/organize-comment-files.py` does the `~/Downloads` → per-accession
  directory move with `--- PAGE n ---` markers in the extracted text.

**Verdict: `adapt`.** The scanned-vs-corrupt-vs-missing classification and the
`--- PAGE n ---` marker convention are worth copying into whatever this repo builds on
top of a FERC download path. The browser snippets are the documented fallback for
exactly the case my 524 test above hit.

### `vibe-coding-security` — `tools/check-external-links.py`

Python, last push 2026-08-24, licence none. **Stdlib only** (`urllib.request`, `re`,
`ipaddress`, `glob`). A sharper sibling of this repo's `tools/check_links.py`:

- Treats **401/403/405/429 as ALIVE** ("security sites routinely bot-block HEAD/GET"),
  failing only on 404/410/451 and DNS/connection failure. This repo's `check_links.py`
  reaches the same conclusion by a different route (`blocked` vs `dead` sentinels), so
  the two are worth reconciling into one classifier.
- **Skips non-citation URLs** — localhost, RFC1918/link-local via `ipaddress`,
  `*.test`/`*.local`/`*.invalid`, `example.*`, and placeholder hosts containing
  `attacker`/`evil`/`victim`/`malicious`. This repo has no such skip list.
- **Gate-shaped exit codes**: `0` clean, `1` a dead citation with no Wayback snapshot,
  `2` bad invocation — and transient DNS/timeout errors are reported but do **not** fail
  the gate, which is the right call given the 2026-08-19 lesson about giving a network
  failure one retry before it becomes a finding.

**Verdict: `copy-as-is`, then merge.** Take the ignorable-host filter and the exit-code
contract into `tools/check_links.py`; do not keep two link checkers.

### `virginia-budget-explorer` — `scripts/freshness.py`

Python, last push 2026-07-06, licence none. Only third-party dependency in the whole
repo is `PyMuPDF==1.26.5`, and `freshness.py` itself is **stdlib** (`urllib.request`,
`json`, `socket`, `os`) apart from two local imports.

`python3 scripts/freshness.py` (add `--check` to exit non-zero on drift) HEADs every
URL in `sources/manifest.json` and compares the live `Content-Length` against the byte
count recorded at capture; a size change or a newly-erroring URL means the document was
re-issued. It exists because the site once silently presented a superseded budget stage
as current. It **never auto-ingests** — detection only. Under GitHub Actions it writes
`drift=true|false` to `$GITHUB_OUTPUT` and a Markdown report.

**Verdict: `adapt`.** `data/research/source_index.json` in this repo already records
`sha256`, `bytes` and `content_type` per source — every input this needs. It is close to
a drop-in, and it is the cheapest available answer to "which of our cited documents has
been re-issued since we read it".

### `us-tpd-tracker` — `pipeline/scrapers/federal_register.py`

Python, last push 2026-02-24 (the least active relevant repo), licence none.
Repo needs `httpx`, `bs4`, `lxml`, `pydantic`, `anthropic`, `feedparser` — but the
Federal Register scraper is thin, and the thing worth taking is the **URL contract**:
`https://www.federalregister.gov/api/v1/documents.json` with PHP-style bracket params
(`conditions[term]`, `conditions[publication_date][gte]`, `per_page`, `order=newest`,
`fields[]=…`), free, keyless, structured JSON, full-text search plus date filtering.
The file also records a live gotcha: the `agencies` filter 400s in certain combinations,
so term-only search is what actually works.

**Verdict: `adapt` — write a ~60-line stdlib `tools/federal_register.py`.** This repo
has connectors for NRC ADAMS, FERC eLibrary and USAspending but **none for the Federal
Register**, which is where DOE/NRC rulemakings, NOITAs and program notices are published
— the primary-source layer under the **Policy** tab.

### `datacenterwaterusage` — 20+ state and local scrapers

Python, last push 2026-08-25, licence none. VA DEQ (ArcGIS, Tableau, VPDES Excel, VWP,
public notices), Ohio EPA (eDocument, general permit, NPDES ArcGIS), ODNR water
withdrawal, Columbus Legistar, Loudoun BoardDocs/Highbond/ACFR, PWC eServices, EPA ECHO
DMR and NAICS, plus `extractors/pdf_extractor.py` (text **and tables**) and
`extractors/excel_extractor.py`.

**Dependencies: the heaviest in the survey** — `playwright`, `httpx`, `bs4`, `lxml`,
`pdfplumber`, `PyMuPDF`, `openpyxl`, `pandas`, `tenacity`, `aiosqlite`, `structlog`,
`click`, `streamlit`, `plotly`, `markdown`. Nothing here can be pasted into a
stdlib-only repo.

**Verdict: `call-out-of-process`, and only if the water question is ever taken up.**
The genuinely transferable asset is the *knowledge* of which state portals expose what:
the Legistar and BoardDocs scrapers are the pattern for reading county-board minutes,
which is where a microreactor siting approval would first appear.

### `FirstPassRx` — `scripts/archive-sources.mjs`

JavaScript, last push 2026-08-25, licence none. Node builtins only (`node:fs`,
`node:crypto`, `node:url`, `node:path`) — runnable with plain `node`, no install.
Archives every cited source with url, final url, HTTP status, content-type, byte size,
sha256, fetch method, first-archived and last-verified timestamps; a re-run only bumps
`last_verified` when the bytes are unchanged and **flags a new sha256 as drift**.

It carries one thing `tools/fetch_source.py` does not, and the reason is documented as
a real incident: these are **third-party pages, and an embedded map/analytics/chat widget
can carry a live API key in the raw HTML** — on 2026-07-07 a Mapbox token embedded in an
Illinois state page reached a commit before GitHub push protection caught it. So every
fetched body is scanned for secret patterns and **redacted before it is written to disk**.

`tools/fetch_source.py` here writes `body` to `data/cache/` verbatim. `data/cache/` is
gitignored, which is most of the protection — but the gitignore is the only thing
standing between a third-party page's embedded credential and a commit.

**Verdict: `adapt` — take the redaction step, not the script.** Roughly 20 lines in
`fetch_source.py`'s `add()`, before `p.write_bytes(body)`. Its `last_verified`-vs-`sha256`
drift distinction is also a cleaner model than this repo's single `fetched` date.

### `roboticsleadership` — `scripts/archive-sources.js`, `check-sources.js`

JavaScript, last push 2026-08-24, licence none. The same archive/check pattern as
FirstPassRx plus `enrich.js` and two scrapers (`scraper-news.js`, `scraper-policy.js`),
each with a colocated `.test.js`. **Verdict: `skip` — superseded.** FirstPassRx's version
of the same idea is better documented and carries the secret-redaction incident.

---

## Not relevant

One line each, so nobody re-opens them.

| Repo | Language | Why not |
|---|---|---|
| `usgs-mineral-commodity-summaries` | Python | USGS MCS viewer over public-domain PDFs. The only transferable idea is the page-screenshot provenance pattern; the data has no bearing on microreactor siting. |
| `uscbp-trade-tracker` | JavaScript | CBP trade-action tracker. Its cache/classify/crawl layer is a weaker version of what `us-tpd-tracker` and this repo already have. |
| `iran-infrastructure-tracker` | TypeScript | Next app, no `scripts/` or `tools/` directory at all — the data-handling lives in app code. Nothing extractable. |
| `PPAhelper` | JavaScript | Interactive PPA course. No pipeline, no scripts directory. Domain-adjacent, machinery-empty. |
| `dcelectionstracker` | TypeScript | One script, `merge-positions.mjs`, specific to candidate/position records. |
| `FERC-Orders-June-2026` UI half | JavaScript | The site, tests and summary tooling are docket-specific; only the three tools named above transfer. |
| `nucleardeployment` app half | TypeScript | Cloudflare/vinext/drizzle app. Only `scripts/` transfers. |
| `VisionZeroDC`, `TBDC50K`, `dayssincelastblunder`, `gyn-journal-club` | JavaScript | Single-purpose civic/hobby sites. No connectors, no gates. |
| `ratemypupusa`, `settle`, `keeper`, `bubblebook` | TypeScript | Consumer apps with backends. Nothing static-site or research-pipeline shaped. |
| `shirtpost`, `FantasyGM` | Python | Unrelated domains; no source-verification or fetch machinery worth porting. |
| `datacenterwaterusage` dashboard half | Python | Streamlit/plotly. Only the scrapers and extractors were considered above. |
| `DryDock`, `website`, `PersonalCRM`, `pitches`, `teaching-ideas`, and 5 pre-2018 repos | — | **Private — not opened.** Named here only so the count reconciles. |

---

## Recommended next steps

Ranked. Each is sized as one task.

1. **Port the eLibrary document download into `tools/ferc_elibrary.py` as
   `--download ACCESSION`.** ~40 lines of stdlib (`http.cookiejar` + `urllib.request`),
   lifted from `FERCforms/pipeline/fetch.py`: warm the filelist URL, POST
   `DownloadPDF?accesssionNumber=…` with `{"serverLocation": ""}`, accept only
   `%PDF-`, write through a `.part` file. **Start by finding the per-file route** — open
   an eLibrary filelist page in the browser, watch the network tab, and record the real
   route and param spelling for a `transmittals[].fileId` download; the combined-PDF
   route 524s at ~125 s today (verified above) and guessing the route name is futile
   because the API answers `200 ""` to anything it does not recognise. Highest value in
   the survey: it is the only item that changes what this project can *know*, rather
   than how well it checks what it already knows.

2. **Import the 15-or-so genuinely-new commitment rows and 9 vendor rows from
   `brownfield-opportunities/docs/data/microreactor-fleet.json`, and de-aggregate
   `janus` and `doe-pilot`.** Re-verify each against its own `sources[]` first — that
   file is a downstream consumer of this project, not an independent source. Bring the
   `lat`/`lon` fields across: nothing in `data/` currently has a coordinate, so this is
   also the enabling step for anything map-shaped.

3. **Add publication-date extraction to `tools/fetch_source.py`.** Copy
   `extract_pub_date` from `datacentercommunitybenefits/connectors/extract.py`
   (stdlib, JSON-LD → meta → `<time>`, validates the calendar date, returns `None`
   rather than guessing) and record it as `published` in `source_index.json`. Then the
   2026-08-23 lint becomes one line: **fail any claim whose date is after its source's
   publication date.** That check exists today only as a paragraph in `CLAUDE.md`.

4. **Merge `vibe-coding-security/tools/check-external-links.py` into
   `tools/check_links.py`, and add the Wayback CDX fallback from
   `datacentercommunitybenefits/check_links.py`.** Take the ignorable-host filter, the
   401/403/405-is-alive rule, and the three-way exit-code contract; add archived-URL
   recovery so a dead citation becomes a recoverable one instead of a permanent failure.
   One checker, not three.

5. **Port `nucleardeployment`'s `claimTerms` / `missingTerms` / `looksLikeWall` into a
   `tools/check_claims.py`.** ~80 lines of stdlib against `data/cache/` and
   `data/research/source_index.json`, both of which already exist. This is the gate that
   would have caught the 2026-08-21 defect — three cost rows citing a real paper for
   figures it does not contain — without a 300K-token agent pass.

6. **Write `tools/federal_register.py`** against
   `https://www.federalregister.gov/api/v1/documents.json` (keyless, bracket params,
   term-only search — the `agencies` filter 400s). Fills the one obvious hole in this
   repo's connector set for the **Policy** tab.

7. **Add secret redaction to `tools/fetch_source.py` before `write_bytes`**, per the
   documented FirstPassRx incident. Small, and it removes a live path from a third-party
   page's embedded credential to a commit.

8. **Run `brownfield-opportunities`' `refresh.py --source infra-proximity` and
   `--source eia-retired-plants` out-of-process, commit the output here, and copy
   `connectors/spatial.py` + `connectors/geom.py` in as-is** (both already stdlib-only)
   so this repo can compute proximity locally for any site added later. Do this after
   step 2, since it needs coordinates to be useful.

9. **Adopt `virginia-budget-explorer/scripts/freshness.py` as a source-drift canary.**
   `source_index.json` already records `sha256`, `bytes` and `content_type` per source,
   so it is close to a drop-in. Lowest urgency of the list, but it is the standing answer
   to "which of our cited documents changed since we read it".

