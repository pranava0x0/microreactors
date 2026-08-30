# Applications financial-case pass — 2026-08-28 — output contract

Extends the `deep-2026-08-24` contract to three Applications-tab sectors that
`data/benchmarks.json` has never covered: **Compute, Manufacturing, Agriculture
& Food** (`data/sectors.json` names these sectors verbatim — use them exactly).
This pass writes **Type B `case` records only**. Skip Type A `mechanism`
records entirely; the deal-mechanism catalog (diesel/batteries/interconnection/
licensing) is already researched and out of scope here.

Plain UTF-8. No HTML entities. Omit optional keys rather than emit empty strings.
Your final chat message is parsed, not read: return only `path + counts + 2-3 surprises`.

## Universal source rule
```json
{"label": "Publisher — document title", "url": "https://full/url/to/document",
 "quote": "verbatim span of <=25 words copied from the page you fetched",
 "status": "fetched" | "snippet-only"}
```
- `status: "fetched"` ONLY if you actually retrieved the page/PDF and read the quote in it.
- `status: "snippet-only"` if the figure came from a search-result summary. A specific fact
  (a date, a dollar figure) seen only in a search summary is SYNTHESIZED until found in a
  fetched page — mark it snippet-only or drop it.
- Bare homepages are rejected. Deep-link to the document.
- Max 2 sources per claim.
- If the claim's date is AFTER the source's publication date, the citation is impossible. Drop it.

## Type B — `case` (a real application-side deal, with real numbers)
```json
{"_meta": {"captured": "2026-08-28", "agent": "<your slug>", "scope": "<one line>",
           "angles_run": ["..."], "absences": ["what you looked for and could NOT verify"]},
 "cases": [{
   "id": "kebab-slug",
   "sector": "Compute" | "Manufacturing" | "Agriculture & Food",
   "load": ["exact load label(s) from data/sectors.json this case bears on, e.g. Semiconductor fabs — see your agent's row in PLAN.md. Omit only if genuinely sector-wide."],
   "name": "Site or deal name",
   "country": "US" | "CA" | "AU" | ...,
   "region": "City, State/Province",
   "parties": {"host": "...", "provider": "...", "utility": "... or omit"},
   "instrument": "PPA | ESA (energy services agreement) | EaaS | BOO | design-build |
                  utility tariff | ESPC/UESC | grant-funded | lease | colocation power
                  agreement | omit if unknown",
   "signed": "YYYY-MM or YYYY",
   "term_years": 20,
   "capacity": "e.g. 5 MW solar + 12 MWh BESS + 3 MW diesel",
   "price": "verbatim contracted price if published, else omit",
   "capex": "if published, else omit",
   "displaced": "what it displaced and at what cost, if published",
   "nuclear": true,
   "filings": [{"forum": "State PUC | FERC eLibrary | NRC ADAMS | SEC | port authority board",
                "type": "...", "id": "docket/accession no.", "date": "YYYY-MM-DD", "url": "..."}],
   "summary": "3-5 sentences of what was actually signed and what it cost.",
   "microreactor_read": "What this deal implies for selling a 1-20 MW reactor into this sector. One or two sentences. Be concrete about the price the reactor has to beat.",
   "sources": [ ...universal source objects... ]
 }]}
```
- `load` is new in this pass (not in the deep-2026-08-24 contract): it is what lets the site
  link a specific sub-application (e.g. "Semiconductor fabs") to the real-world deal that prices
  it, instead of only the sector as a whole. Tag every load the case genuinely bears on; most
  cases will carry one.
- `nuclear: true` marks a case as a signed *nuclear* PPA/deal kept for its published cost (e.g.
  a hyperscaler nuclear PPA) rather than the non-nuclear incumbent a reactor has to beat. Omit
  the key entirely for non-nuclear cases — do not write `"nuclear": false`.
- A large-reactor or SMR-scale nuclear PPA is a valid, high-value case here even though this
  site is about 1-20 MW microreactors: it is real evidence of what a buyer in this sector will
  actually pay for nuclear power, and `microreactor_read` is where you say what changes at 1-20 MW.

## Hard rules for every agent
1. **Write incrementally.** First `Write` = `_meta` + the first 2 records. Then one `Edit`
   per subsequent record appended. Never hold the whole file for one terminal write.
   Before writing, Read the target path: if it already looks complete, stop; if partial, append.
2. **Bail rule.** If 2 searches on an angle surface nothing with a real number or a real
   document, move to the next angle. Stop after your record quota is met, or after 2
   consecutive angles surface nothing new.
3. **Numbers or nothing.** A record with no dollar figure, no capacity, no date and no
   filing is not a record. Drop it and say so in `_meta.absences`.
4. **State absences.** `_meta.absences` must list what you searched for and could not verify —
   including which loads in your partition you could not find a priced case for.
5. Prefer, in order: government sites (.gov), DOE national-lab publications (NREL/INL/PNNL/
   ANL/LBNL/Sandia docs.nrel.gov, inl.gov, osti.gov), regulator dockets (state PUC, FERC
   eLibrary, NRC ADAMS, SEC EDGAR), company press releases and investor materials, energy/
   sector trade press (Utility Dive, Data Center Frontier, Latitude Media, Canary Media,
   Recharge, S&P Global, Fastmarkets, Feed & Grain, Greenhouse Grower), then general web.
6. **A published $/kWh or $/MWh figure is rare and valuable — say so when you can't find one.**
   Prior passes on this project found real signed deals routinely withhold the price (e.g. 7 of
   7 mining PPAs found in the deep-2026-08-24 pass withheld $/kWh). Capacity, capex, term and
   what was displaced are still real numbers worth a record even when price is missing.
