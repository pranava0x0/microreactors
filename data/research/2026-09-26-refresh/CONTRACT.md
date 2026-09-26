# Research pass — 2026-09-26 — output contract

Every agent writes ONE JSON file at the path it is given. Plain UTF-8, no HTML entities.
Omit optional keys rather than emit empty strings. A file may carry more than one top-level
record list (e.g. `regions` and `cases`). Your final chat message is parsed, not read:
return only `path + record counts + 2-3 surprises + the absences`.

Gate: `python3 tools/research_pass.py validate data/research/2026-09-26-refresh`
(you may run it on your own file's folder; do not run any other tool in `tools/`).

## Universal source rule
```json
{"label": "Publisher — document title (with its year)", "url": "https://full/deep/link",
 "quote": "verbatim span of <=25 words copied from the page you fetched",
 "status": "fetched" | "snippet-only"}
```
- `fetched` ONLY if you retrieved the page/PDF (WebFetch) and read the quote in it.
- `snippet-only` if the fact came from a search-result summary. A specific fact (a date, a
  dollar figure) seen only in a search summary is SYNTHESIZED until found in a fetched page.
- Quotes must be copied character-for-character from the page: no ellipses joining two
  passages, no normalised dashes, no paraphrased lead-ins. Keep spans clear of footnote
  digits glued to numbers and of PDF line-break hyphens.
- Bare homepages are rejected; deep-link to the document. Max 2 sources per claim.
- A source published before the event it documents cannot document it. Drop it.
- Prefer, in order: government (.gov, .gc.ca, .gov.au, .gov.uk, .gl), regulators' dockets,
  national labs, company filings and releases, trade press, general web.

## Record types A-C
Unchanged from `data/research/2026-09-02-prospects/CONTRACT.md` (read it for field lists):
`mechanisms` (A), `cases` (B, a priced real deal at a named site; `sector` must be one of
the validator's CASE_SECTORS), `answers` (C, a finding on a `data/strategy.json` prospect's
`next_question`; `for` must be an existing prospect or segment id).

## Type D — `precedents` (pooled buying, shared ownership or shared risk, OUTSIDE nuclear)
```json
{"id": "kebab-slug",
 "mechanism": "advance-market-commitment | buyers-club | assurance-contract | joint-procurement | consortium-ownership | fractional-ownership | capacity-subscription | prepayment | mutual-insurance-pool | parametric-pool | overrun-or-performance-cover | government-backstop",
 "sector": "carbon removal | vaccines | aviation | buses | luxury goods | shipping | space launch | healthcare equipment | ...",
 "name": "Frontier advance market commitment",
 "year": "2022",
 "parties": "who pooled, who supplied, who administered",
 "size": "verbatim numbers: dollars committed, units, members, cover limits",
 "how_it_works": "2-4 sentences: who commits what; the trigger or threshold; who holds price, volume and delivery risk; how money flows.",
 "outcome": "what happened, with numbers: unit price before and after, volumes delivered, time to first delivery, or how it failed.",
 "failure_mode": "optional: where it broke, or what it could not do",
 "microreactor_read": "1-2 sentences: the specific design element a pooled microreactor orderbook or overrun pool should copy, or avoid.",
 "sources": [ ... ]}
```
`sector` may not be nuclear. `size` or `outcome` must carry a number.

## Type E — `regions` (a remote or cold jurisdiction, civilian power only)
```json
{"id": "kebab-slug", "region": "Greenland", "country": "GL",
 "jurisdiction": "US state | US territory | Canadian territory | Canadian province (north) | Danish autonomous territory | Norwegian territory | Australian state | UK overseas territory | ...",
 "power_system": "who generates and distributes; fuel mix; number of isolated grids or communities; installed MW; with numbers",
 "price": "verbatim retail tariff or generation cost, unit and year (e.g. 'US$0.37/kWh residential, 2025')",
 "loads": [{"name": "town, mine or facility", "mw": "verbatim with unit", "note": "diesel / off-grid / seasonal"}],
 "nuclear_position": "legal and policy position on civil nuclear power with dates: ban, enabling law, study, statement",
 "microreactor_activity": "named MOUs, studies, vendor visits, feasibility work, with dates; or 'none found' plus what you searched",
 "blockers": ["concrete, named blockers"],
 "microreactor_read": "1-2 sentences: is there a 1-20 MW buyer here, and what would have to change",
 "sources": [ ... ]}
```
Military bases are context only, never the subject. `price`, `power_system` or `loads` must
carry a number.

## Type F — `dockets` (a utility or regulator filing that names microreactors or SMRs)
```json
{"id": "kebab-slug", "forum": "Georgia PSC", "docket": "56002", "url": "deep link to the filing or docket page",
 "utility": "Georgia Power", "state": "GA",
 "type": "IRP | rider | CPCN | RFP | tariff | study | rate-case | legislation | contract-approval | other",
 "date": "YYYY-MM-DD (filing or order date)",
 "size_class": "micro | small | large | unspecified",
 "status": "filed | approved | rejected | pending | withdrawn | enacted",
 "what_it_says": "2-3 sentences: what the filing says about microreactors or SMRs: MW, in-service year, cost, cost recovery, who pays",
 "microreactor_read": "1 sentence",
 "sources": [ ... ]}
```

## Type G — `checks` (a verdict on a claim already shipped in data/*.json)
```json
{"id": "check-<target>-<n>", "target": "record id in the data file", "file": "opportunities | vendors | news | strategy | deployment_sites | costs | policy | sectors | arguments",
 "claim": "the exact shipped text you checked",
 "verdict": "confirmed | outdated | wrong | unsupported | unverifiable",
 "evidence": "what the fetched primary source says, with its date",
 "correction": "required when outdated or wrong: the replacement text, same length or shorter",
 "sources": [ ... ]}
```
`unverifiable` may omit sources; every other verdict needs a fetched one.

## Hard rules for every agent
1. **Write incrementally.** First `Write` = `_meta` + the first 2 records. Then one `Edit`
   per record appended. Never hold the file for one terminal write. Before writing, Read the
   target path: if it already looks complete, stop; if partial, append the rest.
2. **Bail rule.** 2 searches on an angle with nothing citable -> next angle. Stop at your
   quota, or after 2 consecutive angles surface nothing new.
3. **Numbers or nothing.** A record with no number, date or filing is not a record.
4. **State absences** in `_meta.absences`: what you searched for and could not verify.
5. **Do not spawn sub-agents.** Do the searches yourself.
6. **Do not run** `tools/fetch_source.py` or any tool that writes shared files. The main
   session caches sources after you return.
7. `_meta` = `{"captured": "2026-09-26", "agent": "<slug>", "scope": "...", "angles_run": [...], "absences": [...]}`.
