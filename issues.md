# Issues

Living audit trail. Each bug: date, area, description, root cause (code bug vs data bug
vs test bug), status.

- **2026-08-23 · data · canada-src row a year stale — Fixed.** The tracker carried SRC as
  "Funded / binding, pilot by 2029" while SRC's own FAQ states Westinghouse cancelled the
  contract in fall 2025, pivoting eVinci to space/defence/government. Root cause: **data
  bug** (no refresh trigger on counterparty status). Fix: status "Cancelled — vendor
  withdrew", binding false (hero stat 10→9 binding), quote-locked to SRC's page, cached.
  Regression guard: the quote-lock now verifies offline via `verify_quotes --cache`.
- **2026-08-23 · data · Penn State milestone mis-dated AND mis-cited — Fixed.** Vendor
  milestone said Penn State filed its NRC letter of intent on 2026-02-28, citing a 2023
  POWER article that predates the claim and cannot contain it. The primary document
  (ADAMS ML25059A029, fetched and cached) is dated 2025-02-17 and is for a 15 MWt
  eVinci-based research-reactor construction permit. Root cause: **data bug**, the
  claim-vs-source mismatch class (see 2026-08-21 capex entry) — presence-checking cannot
  catch it; only reading the cited document does. Fix: date corrected, milestone re-cited
  to the LOI itself with a verified quote span.
- **2026-08-23 · data · Quote span crossed PDF glyph damage — Fixed.** A sectors.json
  quote ("…with 100% of electric production…") failed offline verification against the
  cached INL-EXT-21-63214 bytes because the PDF text layer reads "100%of" (no space).
  The prior network verification passed under a different extractor. Root cause: **data
  bug** per the documented glyph-damage rule — span must end before the damaged region.
  Fix: span shortened, re-verified. Found BY the new `verify_quotes --cache` gate.
- **2026-08-23 · tooling · ans.org caches as a JS shell — noted.** urllib fetches of
  ans.org return a nav-only stub (5.6KB) that looks like a successful capture. The stub
  row was removed from the source index. Rule: after caching a page, grep the cache for
  the fact you want before citing it (the "May 30 NOITA date" claimed by a search summary
  was never on the page). nrc.gov/docs, *.af.mil, oklo.com and ktoo.org 403 non-browser
  clients outright — use browser capture + `fetch_source --from-file`.

- **2026-08-23 · tooling · Structural register lint skipped the markup it claimed to
  cover — Fixed.** `check_register.py` pulled only `h1`–`h3` and eyebrows out of
  index.html, while its own docstring said comma-tail ran on "every short display string".
  Measured: 10 headline-length static strings were invisible to it — the wordmark, all
  seven tab labels, the chart legend and the footer credit. Root cause: **test bug**, the
  "a checker that does not model the real object measures nothing" class, in its reassuring
  form: the gate reported 0 hits over 1,101 strings and looked thorough. Fix: an
  `html.parser` pass emits every run of authored text, one per element holding text plus
  the joined text of its ancestors, so a sentence split by an inline `<span>` is still seen
  whole; headings stay tagged so the colon check keeps its narrower scope. 1,101 → 1,138
  strings, still 0 hits. Guards: floors on total strings, heading count and markup runs, so
  a parser returning nothing fails loudly instead of shrinking the total by too little to
  notice. Negative-tested against a comma-tail planted in a tab label, in the footer and in
  a nested legend span, and a colon-setup planted in an `h2`. Known limit, now stated in the
  docstring rather than overclaimed: both patterns anchor at end-of-string and only run
  below 80 characters, so a tell buried mid-paragraph is out of scope by design.
- **2026-08-23 · site · Sub-tabs shipped boxed against a written rule — Fixed.** The new
  sub-tab strips used the site's `.chip` treatment (1px border, radius, raised background)
  on all four panels. DESIGN.md §8.7 specifies the opposite in as many words: "a second,
  lighter tablist inside the panel (underline style, not the boxed primary tabs)". Root
  cause: **design bug**, and the same class as the AGENTS.md case from 2026-08-12 — the rule
  was written in this repo and read during the same session, then not applied, because
  reusing an existing component felt like the conservative choice. Fix: underline treatment,
  subordinated by colour rather than size (`--size-caption` and `--size-label` are both 12px,
  so the hierarchy is a neutral underline against the primary nav's accent red plus tertiary
  idle text). Regression guard: the e2e layout gate now fails any sub-tab carrying a radius
  or a side/top border, and asserts the 44px touch floor on `pointer:coarse`.
- **2026-08-23 · site · Register host stuffed into the number column ≤640px — Fixed.**
  Widening `.reg .rrow` from two grid columns to three (number, details, host) left the
  ≤640px override at two columns, so auto-placement dropped the third child into row 2
  **column 1**: the host sized the number column to 114–247px, squeezed the details column
  to 197px, and `word-break:break-all` broke long domains over two lines. Root cause:
  **code bug** — a grid child count changed without its narrow-viewport rule changing with
  it. Fix: explicit `grid-column:2` on `.reg .host` in the media rule, which also aligns it
  under the details it belongs to. Found by the PR bot on #4, not by the e2e gate, which
  checked page overflow but never where a child landed. Regression guard:
  `SourceRegisterMobile` in tests/test_layout_e2e.py asserts every host starts right of the
  number and shares the details column's left edge.
- **2026-08-23 · site · Renaming the Evidence panel broke `#evidence` links — Fixed.**
  Renaming the panel id to `sources` made the old route unknown, and `activate()` silently
  falls back to the first panel, so every shared `#evidence` link landed on the Tracker with
  the hash rewritten. Root cause: **code bug** — an id rename treated as internal when it is
  also a public URL. Fix: an `ALIASES` map in app.js normalises `evidence` to `sources`
  before the unknown-route check. Regression guard: `Routing` in tests/test_layout_e2e.py.
- **2026-08-23 · site · Citation numbers restarted at [1] on every row — Fixed.** `cite()`
  numbered chips by their index within one row's own source list, so `[1]` appeared dozens
  of times across the site pointing at a different source each time, and no chip could be
  matched to the register. Root cause: **code bug** (a local counter used as a global
  address). Fix: `tools/build_data.py` assigns one number per URL in tab-render order and
  emits `source_numbers`; every chip, source list and register row reads from it, and a
  URL missing from the register renders `[?]`. Regression guards:
  `test_citation_numbers_are_global_and_total` and `test_static_html_citations_resolve`
  in tests/test_build.py, both negative-tested against a doctored bundle.
- **2026-08-23 · site · Four panels had grown past reading length — Fixed.** Measured at
  1280px: Policy 30,906px, Sources 67,475px, Market design 13,951px, Costs 13,216px. Field
  coverage and the gap register sat roughly 90 screens below the fold on Sources, so in
  practice they were unreachable. Root cause: **design bug** (one flat scroll per tab, with
  no second level of navigation). Fix: a shared sub-tab strip (`makeSubnav`) on those four
  panels, routed as `#panel/sub`; Policy's first sub-panel is now 11,265px. The strip wraps
  instead of scrolling, so no sub-section can sit off-screen.
- **2026-08-23 · site · Sector summaries reported a meaningless ratio — Fixed.** Each
  Applications accordion printed "6 loads · 4 cited", a count of this site's own curation
  presented as if it were a finding, and the first sector auto-expanded on load. Root
  cause: **design bug**. Both removed.
- **2026-08-23 · copy · Structural AI-register tells across display copy — Fixed.** A scan
  over all 649 user-visible strings found the tells no word list catches: 3 headings with a
  comma-stapled adverb tail ("Published cost bands, sourced"), 5 comma-stapled twin
  headings, 10 of 32 policy names on a colon setup/payoff template, 14 of 23 precedent
  read-across notes opening "The <noun> for <X>:", and 92 strings carrying em-dashes.
  Root cause: **copy bug** (DESIGN.md §11.1 documents every one of these; the register
  test only greps single words, in data/*.json only, so index.html's "unlock" also went
  unchecked). Fix: swept to 0 / 0 / 0 / 3 / 9 respectively, the remainder being proper
  names and verbatim quotes. Per-tab eyebrow taglines and the footer's build-tooling
  narration were cut in the same pass.

- **2026-08-21 · data · Fabricated capex scenarios in costs.json — Fixed** (commit 18aad96).
  Two LCOE rows ("CAPEX $5,000/kW (FOAK-ish)" → $80–90/MWh and "CAPEX $2,500/kW (at scale)"
  → $35/MWh) cited Abdussami et al. (arXiv 2506.13361 / Nucl. Eng. & Design), which contains
  none of those numbers — its capital-cost distribution is $2,500–4,000/kW, nth-of-a-kind.
  Root cause: **data bug** — figures carried into the dataset without checking the cited PDF
  (LLM-aggregation class; see DATA.md "AI-synthesized values are provisional"). The earlier
  expert review missed it because it reviewed the reasoning, not the provenance. Fix: rows
  replaced with NEI 2019 FOAK ($140–410/MWh) and NOAK ($90–330/MWh) bands, provenance stated
  on-page. Regression guard: tools/check_citations.py + the source-shape tests (bare-homepage
  rejection); content-level provenance still needs a human/agent read per DATA.md.
- **2026-08-21 · data · Alaska band mis-cited — Fixed** (commit 18aad96). "Small rural
  Alaskan communities $350–600/MWh (avg $520)" cited the same paper, which never mentions
  Alaska. Root cause: **data bug**, same class. Re-sourced to NEI 2019 ($300–600/MWh remote
  arctic diesel) + Alaska PCE reporting ($550–800+/MWh rural rates), band now $300–800+,
  labelled diesel-fired.
- **2026-08-21 · data · Offshore-platforms band contradicted by sources — Fixed.** Claimed
  10–50 MW total; published figures run 80–300+ MW (single platforms exceed 100 MW, FPSOs
  80–150 MW). Root cause: **data bug** (unchecked planning estimate). Band corrected in
  place; delta note records the correction. Same for land-based aquaculture (1–5 MW claimed;
  published points 0.5 and 16 MW; now 0.5–16 MW).
- **2026-08-21 · site · Hash deep links stranded mid-page — Fixed.** Panel ids double as
  hash routes, so the browser's native jump-to-anchor scrolled past the tab layout on load.
  Root cause: **code bug**. Fix: scroll-to-top on boot activation + history.scrollRestoration
  = "manual". (Note: the dev browser pane separately restores its own scroll offset across
  navigations — that half is tool artifact, not site behaviour; see AGENTS.md.)
- **2026-08-21 · site · Mobile overflow ×2 — Fixed.** Precedent category labels
  (white-space:nowrap) overflowed 375px on Market design; the 40-char
  betterbuildingssolutioncenter.energy.gov hostname overflowed the Evidence register. Root
  cause: **code bug** (nowrap on unbounded strings). Both stack/wrap on ≤640px now; the e2e
  layout gate (tests/test_layout_e2e.py) caught both and guards the class.

## 2026-08-25 — deep research pass, quote gate and copy sweep

- **2026-08-25 · site · Every styled `<details>` kept its full height when closed — Fixed.**
  No closed-state rule existed anywhere in `site.css`; the UA rule alone does not survive an
  author-styled disclosure. Invisible until the Policy tab gained 25 instrument rows and
  reserved a screen-height of blank space. Root cause: **code bug**. Measured 917px closed
  before, 0px after. `details.sector` had the same latent bug and is fixed in the same rule.
- **2026-08-25 · site · Cost chart overflowed the page at every width — Fixed.**
  The axis ceiling was a literal `var MAX = 850`, so correcting rural Alaska to $1,950/MWh
  rendered a 1,945px bar inside a 1,280px page. Root cause: **code bug** (hand-typed constant
  mirroring the data). `MAX` now derives from the bands. Caught by `tests/test_layout_e2e.py`,
  not by the manual browser pass, which had only checked the sub-tab it just added.
- **2026-08-25 · tooling · Four stale hand-typed mirrors of `build_data.FILES` — Fixed.**
  `test_build.py`, `verify_quotes.py` and `check_register.py` each re-typed the data-file list,
  and all three were stale: the quote gate and the AI-register lint had never once examined
  `benchmarks.json` or `instruments.json`. Root cause: **test/tool bug**. All three now derive
  from the builder's registry. Deriving `check_register`'s list immediately caught two headings
  written the same session in the colon-setup shape the site swept on 2026-08-23.
- **2026-08-25 · data · 18 shipped quotes did not appear in their cited source — Fixed.**
  Exposed only after caching 145 sources, which took the quote gate from 33 checks to 272.
  Root cause: **data bug** (agents return near-verbatim quotes: an em-dash normalised, a
  separator dropped, two JSON fields joined by an ellipsis). 26 narrowed to a genuinely verbatim
  span by the new `tools/repair_quotes.py`; 4 hosts serve a JS shell and are now `snippet-only`
  with a note; one quote was simply not on its page and was replaced.
- **2026-08-25 · tooling · Quote gate reported honest disclosures as failures — Fixed.**
  `verify_quotes.py --cache` flagged `snippet-only` sources as `QUOTE MISMATCH`, though such a
  row declares the page was never fetched and cannot match cached bytes. Root cause: **tool bug**
  (missing third verdict). Now reports `snippet-only` separately and fails only on real
  mismatches.
- **2026-08-25 · site · Three inline citations in `app.js` were not in the source register — Fixed.**
  They rendered `[?]` to the reader. One was orphaned the same session by re-sourcing the CMS
  policy row to the primary memo, removing the only row citing the old URL; the other two had
  never been registered. Root cause: **code bug plus a gate gap** — `index.html` citations were
  tested, `app.js` citations were not. New `test_app_js_hardcoded_citations_resolve` closes it.
- **2026-08-25 · tooling · Impossible-citation lint first false-positived, then went silent — Fixed.**
  `(19|20)\d{2}` matched inside contract number `N69450-16-C-1901`; requiring non-digit boundaries
  then stopped it matching ISO dates like `2025-06`, so it caught nothing and passed everything.
  Root cause: **tool bug**. Structured date fields and prose labels now use separate patterns, and
  both directions are fixture-tested.
- **2026-08-25 · docs · An earlier claim in-session that the Vendors `[?]` was a bug — Not a bug.**
  It is the placeholder `app.js` fills from the register, which is why the browser check reported
  zero unresolved chips. Recorded so the next reader does not "fix" it.
- **2026-08-29 · tooling · `check_citations.py` never checked `benchmarks.json` or `instruments.json` — Fixed.**
  The claim-coverage scanner's docstring claimed full coverage of every data file, but its `check()`
  hand-lists which files to walk and these two — the ones actually carrying dollar figures — were
  never added when they shipped. Root cause: **gate gap**, the third occurrence of this exact class
  in this project (see the 2026-08-25 quote-gate and register-lint entries above). Closed in
  `tools/check_citations.py` before adding more benchmark/instrument records.
- **2026-08-29 · data · Two independent research agents wrote the same real-world deal as two records with conflicting numbers — Fixed.**
  (1) An Intel Ohio/AEP Ohio substation deal was researched twice, days apart: the first record's
  `capacity` field conflated the $95.1M substation's actual 50 MW capacity with Intel's eventual
  500 MW full-site draw (both real numbers, from the same source, attributed to the wrong thing);
  the second, independently-researched record had the correct 50 MW figure. (2) A Kokhanok, AK DOE
  microgrid grant was independently researched by two agents in the *same* wave, each capturing
  real evidence the other lacked. Root cause: **partitioning failure** — agents partition by named
  entity within one wave, but a later, independent pass (the Intel case) has no visibility into an
  earlier pass's records unless explicitly pointed at them, and both duplicates sat invisible in the
  data until an unrelated feature (the Applications-tab priced-example cross-link) aggregated
  records by a new dimension (`load`) that made the double-count visible. Caught by a second Codex
  review round, not by the citation/quote gates — a citation gate only proves a quoted span exists
  on the page, not that a paraphrased field (like `capacity`) attributes the right number to the
  right thing. Both merged into one canonical record carrying the union of evidence; a broader
  post-merge duplicate sweep (by shared source URL, then by name/region/date) found no others.

## 2026-08-29 — link rot found by check_links (pre-existing, not introduced)

Three registered URLs are dead as of 2026-08-29. All three predate this session's changes
(confirmed present in `origin/main`'s `site/data.js`). `tools/check_links.py` exits 1 on them;
the test suite only imports its `collect_urls()`, so CI stays green.

| Status | URL | Area |
|---|---|---|
| -1 (no response) | `https://data.nrel.gov/submissions/162` | costs / benchmarks |
| 404 | `https://www.aepohio.com/lib/docs/ratesandtariffs/Ohio/July_24_2026_AEP_Ohio_Tariff_Book.pdf` | instruments (utility tariff) |
| 404 | `https://www.cnsc-ccsn.gc.ca/.../global-first-micro-modular-reactor-project/gfp-admin/` | deployment sites (Chalk River MMR) |

Root cause: **link rot at the publisher**, not a code or data bug. The AEP Ohio tariff book is
re-issued under a new dated filename each cycle, and the CNSC page moved after the Chalk River MMR
project was paused. Status: Open. Each needs a replacement URL or an archived copy; the Chalk River
one may simply have no live equivalent now that the project is off.
