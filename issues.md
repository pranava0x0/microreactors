# Issues

Living audit trail. Each bug: date, area, description, root cause (code bug vs data bug
vs test bug), status.

- **2026-09-09 · data · DOE Reactor Pilot Program criticality count stale, 3 vs actual 5 — Fixed.**
  `opportunities.json`'s `reactors_critical_2026` field (feeding the homepage hero stat)
  was hand-set to 3 and never updated after Aalo (2026-07-04) and Oklo's Groves Isotope
  Test Reactor (2026-08-05) also reached criticality — both confirmed against DOE's own
  primary source ("Groves is the fifth DOE-authorized advanced reactor to achieve
  criticality this summer"). Root cause: **data bug**, a hand-typed number with no
  refresh trigger, the same class as the 2026-08-23 canada-src entry below. Oklo's
  criticality was also entirely missing from its vendor milestones. Fix: count corrected
  to 5, timeline/status text updated, Oklo milestone added, both cited to DOE's article.
  Caught by the user asking "didn't we have more companies go critical???" — the site's
  own data disagreed with itself once checked against a primary source.
- **2026-09-09 · data · "2/16 have a utility filing" counted two explicit N/A rows as having one — Fixed.**
  `tools/build_gaps.py`'s field-coverage counter treated any non-null `utility_filing`
  value as "have," so the two rows reading `"N/A; DOE-authorized test reactors"` /
  `"N/A; authorized by DOE, not licensed by NRC"` (i.e. explicitly stating no filing
  applies) counted toward the "have" total. The true count is 0/16 — no tracked
  opportunity carries an actual citable utility/PUC filing. Root cause: **test/tooling
  bug**, the "checker doesn't model the real object" class — "field is present" was
  conflated with "field states a fact was found." Fix: `build_gaps.py` now buckets
  N/A-prefixed values into their own `not_applicable` count, separate from `have` and
  from the missing/gap list.
- **2026-09-09 · design · homepage "17 vendor milestones hit in 2026" stat was
  incoherent — Removed.** The figure summed unrelated event types (a criticality event,
  a hire, a funding close, a base selection) into one number with no shared unit of
  meaning. Root cause: **design bug**, not a data error — the underlying count was
  computed correctly, it just measured nothing coherent. Fix: tile removed; the
  criticality and binding-deal tiles already surface the two milestone types worth a
  headline number. All 5 remaining hero stats now link to the tab where the number is
  broken out (Deals, Deals→US Government, Vendors, Sources→Gaps), and every pipeline row
  now shows a visible executed/announced badge so "9/16 hold an executed agreement" is
  no longer citing an invisible field.
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

> **Resolved 2026-09-26** (see the 2026-09-26 section below).

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

## 2026-09-02 — commercial-strategy pass

- **2026-09-02 · Costs / learning curve · data bug · Fixed.** `costs.json` `learning_curve.floor` read "INL models 6 to 10 full-time staff at $162,000 to $188,000 each." A grep of both cached INL reports finds no such figures: INL uses a single $178,500 per FTE rate (security 5 FTEs shared one guard per two reactors, remote monitoring one person per 20 reactors). The 3-10 staff and $120,000-225,000 ranges are the University of Michigan paper's uniform input distributions (Table 2, nominal 5 staff at $150,000), and its optimized solution is ten FTEs at $162,424. The $188,000 figure appears in no cached source. Root cause: a paraphrase from the 2026-08-29 cost pass that merged two papers' assumptions under one attribution; the block's sources were the right documents, so the citation-coverage gate could not see it. Fix: sentence re-attributed and two quote-locks added (`Using $178,500/FTE`; `ten FTEs at $162,424.20/year`), verified against the cache. The same wrong sentence is in the (uncommitted) pitch documents; flagged in the pitch improvement plan.

## 2026-09-26 — full refresh (UAT, claim validation, research pass)

- **2026-09-26 · home · The front page promoted an older story over three newer ones — Fixed.**
  `renderHome()` sliced `D.news.items` assuming newest-first ("already sorted by build_data.py"),
  but nothing sorted it and `data/news.json` had a 2026-08-17 item above 2026-09-04. Root cause:
  **code bug plus a false comment**. `tools/build_data.py` now sorts news and ships the newest
  eight as `headlines`; `test_home_is_a_directory_of_the_site_with_the_newest_headlines` asserts
  date order.
- **2026-09-26 · data · news.json had drifted from its research pass — Fixed.** PR #21 hand-edited
  five items in and three items' fields, while the seed pass stayed marked `incomplete`, so no
  tool could rebuild the file. Root cause: **process gap** (no drift test for news, unlike voices).
  The curated items are now `data/research/news/curated-2026-09-21.json`; `test_news_matches_its_pass`.
- **2026-09-26 · tooling · The quote gate reported 147 PDF quotes as mismatches — Fixed.** With no
  PDF library installed `cached_text()` returned "", which reads as "the page lacks the quote".
  Root cause: **tool bug** (an unreadable input reported as a failure). It now returns None and the
  gate prints `UNCHECKED n PDF-backed quotes` instead. With PyMuPDF: 734 verified, 0 mismatches.
- **2026-09-26 · site · Duplicate citation chips — Fixed.** A record citing one page twice printed
  "[10][10]" on the front page. `cite()` now emits one chip per URL.
- **2026-09-26 · site · Sourced facts typed into app.js — Retired.** Why > The loads rendered six
  hand-typed cards whose citations did not support them (a 5-30 MW spaceport band cited to an
  Antares base-selection release; mining transmission costs cited to a Valdez utility page).
  Root cause: **data in the renderer**, outside every gate. Replaced by the derived Applications
  overview; `test_app_js_carries_no_sourced_facts` keeps inline sources out of app.js.
- **2026-09-26 · site · Hand-typed stats — Fixed.** Applications' "$250-$850/MWh displaced diesel
  ceiling" and Sites' "5 load categories" / "0 FERC hits" were literals; all are counted now.
- **2026-09-26 · data · Degenerate band "0.24-0.24 MW" — Fixed.** Now "0.24 MW"; the band test
  accepts single values and rejects equal-ended ranges.
- **2026-09-26 · data · eVinci's criticality was invisible on Vendors — Fixed.** The 2026-08-24
  NCERC milestone lacked the `unit` field `criticalityMilestone()` requires, so the new vendor
  table said "no criticality yet" beside a News item recording it. Antares also listed its Mark-0
  criticality twice (deduped). Root cause: **data bug**.
- **2026-09-26 · layout · Two-row nav and an off-screen active tab — Fixed.** Nine tabs wrapped to
  two rows at 768 and 1280px (129-143px of sticky chrome); on phones #sources left its tab ~500px
  off-screen. The strip now scrolls below 1280px with an edge fade and reveals the active tab.
- **2026-09-26 · tooling · The language lint read six object keys of app.js — Fixed.** Copy built
  around variables (every new Home and Applications string) was never scanned. It now tokenizes
  every string literal, skipping regex literals and comments.
- **2026-09-26 · gate · Banned-word sweep covered 7 of 15 data files (#18) — Fixed.** Derived from
  `build_data.FILES`; three hits fixed or exempted (a blog headline in a venue field).
- **2026-09-26 · data · Janus binding status disagrees between tracker and News — Open.** The tracker
  row says not binding; the six 2026-08-26 News items say executed; the Army's release says the five
  vendors were "down-selected ... for negotiation of Other Transactions Authority-based agreements".
  Under verification in the 2026-09-26 pass.
- **2026-09-26 · sources · Five dead citations — Fixed.** `tools/check_links.py`: 639 URLs, 535
  live, 99 bot-blocked (page exists), 5 dead. The AEP Ohio tariff book moved to the September 2026
  edition (both Schedule DCT quotes re-verified in it); the CNSC MMR review page and the reflector.com
  Radiant release now cite Wayback snapshots whose cached copies contain the quotes; the CNSC GFP
  admin-protocol filing row was dropped (removed after the project paused, never archived).
- **2026-09-26 · data · Two Transportation loads were cited to a quote that is not on the page —
  Fixed.** "Large Amazon, Walmart and similar fulfillment and distribution centers" and "Large rail,
  truck and fleet-charging hubs" cited data.nrel.gov/submissions/162 for a sentence ("A 20-bus transit
  depot ... could draw 3 MW") that the archived dataset page does not contain: a search-engine
  synthesis, already marked snippet-only. Root cause: **data bug** (DATA.md: never cite a fact that
  exists only in a search summary). Both loads are in `_meta.uncited` until a facility-level source
  is found; the filings agent is looking.
- **2026-09-26 · site · Clearing a register search left all ~700 rows open — Fixed.** Typing lifted
  the 30-row page limit and hid Show all, and nothing restored either when the box was emptied.
  Found by the interaction sweep (every filter chip, disclosure, deal row, search and deep link at
  375 and 1280px). Root cause: **code bug** (one-way state). The limit now returns when the box is
  cleared unless the reader chose Show all or arrived on a #src-N link;
  `test_register_search_restores_the_first_page`.
- **2026-09-26 · data · Five Janus news items said "signed" — Fixed.** Their binding notes claimed
  signed OTA agreements; the Army's release says the five vendors were "down-selected ... for
  negotiation", and the BWXT, General Atomics and Westinghouse releases use selection language
  (Antares says "awarded", Radiant says binding). The five are now announced, not executed (News:
  42 of 60 executed). The Janus tracker row moves the other way, to binding, because the tracker's
  own rule counts a selection with a named site, as it already did for the ANPI rows. Root cause:
  **data bug** (an agent's reading of "award" as "signed"). Found by the verification pass.
- **2026-09-26 · data · UK Last Energy row carried the Welsh project's design review — Fixed.** The
  2025 ONR review covers the Llynfi site, not the DP World Thames Freeport project.
- **2026-09-26 · data · Antares Series C dated to a recap article — Fixed.** Announced 2026-07-27
  (TechCrunch, BusinessWire); the row said 2026-08-03, the date of a later recap.
- **2026-09-26 · data · Site and prospect claims corrected by the verification pass — Fixed.** 44 checks
  (all 16 sites, all 25 prospects): 37 confirmed. Penn State's letter of intent was *submitted*
  2025-02-28 (the letter is dated 2025-02-17, which a 2026-08-23 fix had used for "told the NRC on");
  UIUC's application notice of receipt was published 2026-04-21 and it was docketed 2026-05-18, not
  "announced 2026-04-15"; Chalk River's vendor is NANO Nuclear since its 2025-10-22 purchase of
  Global First Power; Wales' consenting route is a Significant (not Strategic) Infrastructure
  Project; Doyon's obligations are $906M, not $895M. One verdict was itself wrong: the agent called
  CVEA's vendor list unsupported after reading only the press release, but CVEA's September 2023
  Ruralite article names Westinghouse, Oklo, NuScale and Radiant; the site now attributes the list
  to that article and cites it. Root cause of the originals: **data bugs** (dates read off the wrong
  document, a corporate change applied to one record and not its sibling).
- **2026-09-26 · data · The one unverifiable site claim is confirmed in ADAMS — Fixed.** The
  verification agent could not find Aalo's letter of intent for an early site permit at Texas A&M
  RELLIS because web search does not index ADAMS. `tools/adams_search.py --accession ML26190A374`
  returns it (Aalo Holdings, 2026-07-09, docket 99902128). The same search found NRC's 2026-09-02
  e-mail to Aalo on a RELLIS ESP project number (ML26245A061, docket 99902180), now in the site's
  filing trail. Root cause: **tool choice** (a web-only verifier checking a docket-only fact).
- **2026-09-26 · data · Five news items had no fetched source — Fixed.** The news validator added in
  this pass requires one fetched source per item. Four items cited investor-relations pages that
  stall scripted clients (Q4 and GlobeNewswire hosts), so they carried search snippets only; each now
  also cites a fetched copy of the same release (PR Newswire for the two Centrus contracts, X-energy's
  and NANO's own sites). One snippet quote was not verbatim ("signed a definitive" where the release
  reads "the signing of a definitive") and was re-copied. The PJM ER26-1479-002 row had no quote: its
  eLibrary page is a script shell, so it is now cached as rendered (capture "out-of-band") and quotes
  FERC's filing description. Root cause: **data bug** (snippet-only sources shipped as the only
  evidence for four executed events).
- **2026-09-26 · data · The older news archive fails two structural news rules — Open.**
  `python3 tools/research_pass.py validate data/research/news` reports 94 errors, none in this pass's
  files: 42 ids in `seed-2026-08-30.json` repeat in `curated-2026-09-21.json`, which superseded it
  (merge_news keeps the later file, so the site is unaffected), and 52 older items list one URL twice,
  usually two quotes from one page (`cite()` already renders one chip per URL). Root cause: **rules
  added after the data** (the news type and its no-repeated-URL rule arrived in this pass). Fix
  when next touched: fold each item's same-page quotes into one source and mark the seed file
  superseded, so the validator skips it.
