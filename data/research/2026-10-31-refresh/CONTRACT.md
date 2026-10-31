# Refresh pass — 2026-10-31 — output contract

Canonical template: data/research/refresh-contract.md (tools/refresh_init.py copies it here).
Newest item already on the News tab: 2026-10-27.

Every agent writes ONE JSON file at the path it is given. Plain UTF-8, no HTML entities.
Omit optional keys rather than emit empty strings. A file may carry several top-level
record lists (`items`, `checks`, `applications`, `regions`, `dockets`). Your final chat
message is parsed, not read: return only `path + record counts + 2-3 surprises + absences`.

Validator: `python3 tools/research_pass.py validate data/research/2026-10-31-refresh`
(the only tool in `tools/` you may run).

## Skip lists
`skip/<file>.json` holds what the site already ships (ids, text, source urls). Never add a
record whose event or subject is already there. When you are asked to validate shipped
data, the claim text you check is in the skip list.

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
7. `_meta` = `{"captured": "2026-10-31", "agent": "<slug>", "scope": "...", "angles_run": [...], "absences": [...]}`.

## Added after wave 1
- **Two sources means two documents.** Never list the same URL twice on one record; the pooling
  agent did on 11 of 24 rows.

## Type N — news `items` (the shape of data/news.json)
```json
{"id": "kebab-slug-YYYY-MM-DD", "date": "YYYY-MM-DD (the event's date, not the article's)",
 "headline": "under 90 characters, plain, no colon-setup",
 "companies": ["Antares", "Centrus"],
 "category": "fuel | award | regulatory | criticality | financing | contract | construction | policy | setback | personnel",
 "what_happened": "2-3 sentences: who did what, with the number and the instrument",
 "why_it_matters": "1-2 sentences for a buyer of a 1-20 MW reactor; no hype",
 "binding": true,
 "binding_note": "optional: why this is or is not executed",
 "sources": [ ...universal source objects, at least one fetched... ]}
```
`binding: true` ONLY for something executed: a signed contract, a filed application, an achieved
milestone, a formal regulatory order or approval, or a closed financing. Selections, down-selections
"for negotiation", MOUs, letters of intent and announcements are `false`.
- **No "..." inside a fetched quote.** The validator rejects it (2026-10-08): 11 of ~55 region quotes
  were two passages stitched together. Copy one unbroken span.
- **A load is demand, not on-site generation.** A facility's rooftop solar or cogeneration capacity
  does not tell you its load.

## Type S — `applications` (a buyer segment or named project the Applications tab does not yet carry)
```json
{"id": "kebab-slug", "segment": "short segment label, e.g. 'lunar surface power' | 'launch sites' | 'district heat' | 'desalination' | 'telecom towers' | 'cold chain' | 'ports' | 'steel and cement' | ...",
 "name": "named project, program or buyer",
 "status": "operating | contracted | funded | studied | proposed | cancelled",
 "power_class": "verbatim electric or thermal size with unit (e.g. '40 kWe', '5 MWth', '1-10 MW')",
 "timeline": "optional, dated",
 "sponsor": "optional: who pays", "vendor": "optional",
 "what_it_says": "2-3 sentences with the numbers: load, today's power source and its price if published, what the project is.",
 "microreactor_read": "1-2 sentences: does a 1-20 MW block fit this load, at what price, and what blocks it",
 "sources": [ ...universal source objects... ]}
```
Type G `checks` also accept `file`: `opportunities`, `vendors`, `deployment_sites`, `costs`.
Output files may hold `items` (Type N), `checks` (G), `applications` (S), `regions` (E), `dockets` (F),
`precedents` (D), `cases` (B) together. `_meta.absences` is mandatory and must be non-empty.

## Lessons from earlier haiku passes
- **WebFetch returns a model's summary, not the page.** A quote is `fetched` only if you saw those exact
  words in the fetch output. If the fetch result paraphrases or you are unsure the words are verbatim,
  mark the source `snippet-only`. The main session re-verifies every quote against the raw bytes and
  drops what does not match, so a wrong `fetched` costs you the record.
- Search for the *primary* page (company release, agency page, docket), not an aggregator.
- Dates: the event's date. A date seen only in a search summary is unverified until found in a fetched page.
- **Do not emit `unverifiable` checks.** On 2026-10-08 a tracker agent returned 16 of 16 checks as
  `unverifiable` with no sources: 109K tokens for nothing. Only write a check when a fetched page
  confirms, corrects or contradicts the shipped text. A `confirmed` check needs a page dated within
  ~60 days or a primary page stating the same status.
- **Prefer corrections over confirmations.** The value of a validation pass is the `outdated` and
  `wrong` verdicts. Spend searches on records most likely to have changed (dated timelines,
  "expected", "targeted", "pending", counts that grow).
- **Two agents, one window:** your prompt lists the other agents' scopes. Stay in yours; if you
  stumble on news outside it, skip it rather than duplicate the other agent's ids.
