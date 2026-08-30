# Leadership and voices pass — 2026-08-29 — output contract

One JSON file per agent. Plain UTF-8. Omit optional keys rather than emit empty strings.
Your final chat message is parsed, not read: return only `path + counts + 2-3 surprises`.

## Universal source rule
```json
{"label": "Publisher — document or episode title", "url": "https://full/url",
 "quote": "verbatim span of <=25 words copied from the page/transcript you fetched",
 "status": "fetched" | "snippet-only"}
```
- `status: "fetched"` ONLY if you actually retrieved the page, PDF or transcript and read the
  quote in it. `snippet-only` if it came from a search-result summary.
- **A specific fact seen only in a search summary is SYNTHESIZED until found in a fetched page.**
  Mark it snippet-only or drop it. This has bitten this project twice.
- **If the quote's date is AFTER the source's publication date, the citation is impossible.** Drop it.
- Bare homepages are rejected. Deep-link to the document.
- Never paraphrase inside `quote`. If you cannot copy it verbatim, drop the record.

## File shape
```json
{"_meta": {"captured": "2026-08-29", "agent": "<your slug>",
           "companies": ["..."], "window": "2024-08 to 2026-08",
           "angles_run": ["..."],
           "absences": ["what you looked for and could NOT find — be specific"],
           "incomplete": false},
 "leaders": [{
   "id": "kebab-company-lastname",
   "company": "Company name",
   "name": "Full name",
   "title": "Exact current title",
   "since": "YYYY-MM or omit",
   "background": "2-3 sentences. Prior roles, employers, degrees. Facts only.",
   "why_they_matter": "1 sentence: what this hire or person signals commercially.",
   "sources": [ ...universal source objects... ]
 }],
 "quotes": [{
   "id": "kebab-slug",
   "company": "Company name",
   "speaker": "Full name",
   "role": "Their title at the time of speaking",
   "date": "YYYY-MM-DD or YYYY-MM",
   "venue": "Podcast/outlet/filing/conference name",
   "topic": "customers" | "costs" | "supply-chain" | "units-manufacturing" | "orders" | "regulatory" | "international",
   "quote": "VERBATIM. <=60 words. Copy exactly, including any awkward phrasing.",
   "what_it_means": "1-2 sentences of plain analysis. No hype.",
   "sources": [ ...universal source objects... ]
 }]}
```

## What to hunt for, in priority order
1. **Numbers said out loud.** Cost per unit, $/kW, $/MWh, PPA price, order counts, factory
   throughput, headcount, capex, revenue, backlog. A number in a CEO's own mouth is worth more
   than any analyst estimate.
2. **Customers and orders.** Named counterparties, LOIs vs binding, megawatts, delivery dates.
3. **Supply chain.** HALEU/TRISO sourcing, enrichment, fuel fabrication contracts, long-lead
   components, who they depend on.
4. **Manufacturing.** Units per year, factory location, what "serial production" means to them.
5. **Where they say they will NOT compete.** Negative statements are unusually informative.

## Good sources
Company newsroom and investor pages; SEC filings (S-1, S-4, 10-K, 8-K — several of these
companies went public in 2025-26 and their filings are fetchable and quotable); earnings-call
transcripts; podcast episodes **that publish a transcript**; YouTube auto-transcripts if you
can retrieve the text; conference proceedings; trade press interviews (ANS Nuclear Newswire,
World Nuclear News, POWER, Utility Dive, Axios, TechCrunch).

## Write incrementally — this is not optional
Write the file with `_meta` plus your first 2-3 records FIRST. Then add each further record
with a single Edit. A session limit killed four agents mid-run on 2026-08-25; because they
wrote incrementally, 111 of ~130 records survived on disk. An agent that writes once at the
end and dies returns nothing.

If you run out of budget, set `_meta.incomplete: true` and list what you never reached in
`_meta.absences`.

## Do not
- Do not run anything in `tools/`. `fetch_source.py` writes a shared index that concurrent
  agents corrupt.
- Do not edit any file outside your own output path.
- Do not invent a title, a date or a number. An honest `absences` entry is worth more than a
  plausible guess.
