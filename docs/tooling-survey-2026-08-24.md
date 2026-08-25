# Tooling survey — `pranava0x0` public repos, 2026-08-24

What already exists across the owner's other repos that this project should adopt or
shell out to, rather than rebuild.

**Scope.** 37 repos returned by `gh repo list pranava0x0 --limit 200`; 10 are private
(`DryDock`, `website`, `PersonalCRM`, `pitches`, `teaching-ideas`, and five pre-2018
personal repos) and were not opened. That leaves **26 public repos other than this
one**, of which **11 hold machinery worth taking**. None is archived.

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
