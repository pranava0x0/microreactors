# Deep research pass — 2026-08-24 — output contract

Two record types. Every agent writes ONE JSON file matching one of these shapes.
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

## Type A — `mechanism` (how a deal actually gets signed)
```json
{"_meta": {"captured": "2026-08-24", "agent": "<your slug>", "scope": "<one line>",
           "angles_run": ["..."], "absences": ["what you looked for and could NOT verify"]},
 "mechanisms": [{
   "id": "kebab-slug",
   "group": "diesel" | "batteries" | "interconnection",
   "family": "commercial-contract" | "regulatory-rule" | "utility-tariff" | "public-procurement",
   "name": "Short name of the mechanism",
   "what_it_is": "2-4 sentences. Who signs what with whom; who OWNS the asset; who bears fuel/availability/performance risk; how the host pays.",
   "who_signs": "Party A <-> Party B",
   "asset_owner": "host | third-party developer | utility | public agency",
   "term": "e.g. 15-20 years",
   "price_form": "$/kWh | $/kW-month capacity fee | fixed monthly service fee | rate-based | grant-funded",
   "precedents": [{"name": "...", "year": "2024", "parties": "...", "size": "...",
                   "price": "... or omit", "note": "...", "source_idx": 0}],
   "nuclear_fit": "What changes when the asset is a nuclear reactor of ANY size. Name the specific blocker or enabler.",
   "microreactor_edge": "What a 1-20 MW factory-built, modular, relocatable unit changes SPECIFICALLY vs a large reactor. Omit if nothing real.",
   "blockers": ["concrete, named blockers"],
   "sources": [ ...universal source objects... ]
 }]}
```
`precedents` MUST be non-nuclear, real, and dated — that is the point of the record.
`source_idx` indexes into this mechanism's own `sources` array.

## Type B — `case` (a real application-side deal, with real numbers)
```json
{"_meta": {"captured": "2026-08-24", "agent": "<your slug>", "scope": "<one line>",
           "angles_run": ["..."], "absences": ["..."]},
 "cases": [{
   "id": "kebab-slug",
   "sector": "Remote outposts & microgrids" | "Marine terminals" | "Medical campuses"
             | "Critical civic infrastructure" | "Off-grid mining & mineral processing",
   "name": "Site or deal name",
   "country": "US" | "CA" | "AU" | ...,
   "region": "City, State/Province",
   "parties": {"host": "...", "provider": "...", "utility": "... or omit"},
   "instrument": "PPA | ESA (energy services agreement) | EaaS | BOO | design-build |
                  utility tariff | ESPC/UESC | grant-funded | lease | omit if unknown",
   "signed": "YYYY-MM or YYYY",
   "term_years": 20,
   "capacity": "e.g. 5 MW solar + 12 MWh BESS + 3 MW diesel",
   "price": "verbatim contracted price if published, else omit",
   "capex": "if published, else omit",
   "displaced": "what it displaced and at what cost, if published",
   "filings": [{"forum": "State PUC | FERC eLibrary | NRC ADAMS | SEC | port authority board",
                "type": "...", "id": "docket/accession no.", "date": "YYYY-MM-DD", "url": "..."}],
   "summary": "3-5 sentences of what was actually signed and what it cost.",
   "microreactor_read": "What this deal implies for selling a 1-20 MW reactor into this sector. One or two sentences. Be concrete about the price the reactor has to beat.",
   "sources": [ ...universal source objects... ]
 }]}
```

## Hard rules for every agent
1. **Write incrementally.** First `Write` = `_meta` + the first 2 records. Then one `Edit`
   per subsequent record appended. Never hold the whole file for one terminal write.
   Before writing, Read the target path: if it already looks complete, stop; if partial, append.
2. **Bail rule.** If 2 searches on an angle surface nothing with a real number or a real
   document, move to the next angle. Stop after your record quota is met, or after 2
   consecutive angles surface nothing new.
3. **Numbers or nothing.** A record with no dollar figure, no capacity, no date and no
   filing is not a record. Drop it and say so in `_meta.absences`.
4. **State absences.** `_meta.absences` must list what you searched for and could not verify.
   A report of only successes hides its coverage gaps.
5. Prefer, in order: government sites (.gov), DOE national-lab publications (NREL/INL/PNNL/
   ANL/LBNL/Sandia docs.nrel.gov, inl.gov, osti.gov), regulator dockets (state PUC, FERC
   eLibrary, NRC ADAMS), company SEC filings and press releases, energy trade press
   (Utility Dive, Microgrid Knowledge, Latitude Media, Power Engineering, Canary Media,
   Data Center Frontier, Mining.com), then general web.
