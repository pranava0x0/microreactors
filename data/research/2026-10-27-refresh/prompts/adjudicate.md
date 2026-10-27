You are the ADJUDICATOR for a research pass on a cited microreactor-market website (repo /Users/pranava/Projects/microreactors). Today is 2026-10-27. Haiku agents wrote the JSON files in /Users/pranava/Projects/microreactors/data/research/2026-10-27-refresh/ (news.json, deals.json, applications.json, politics.json, vendors.json, prospects.json, and any other *.json there except skip/). Haiku finds leads well and paraphrases badly. Your job is to decide what ships and make it correct.

Read CONTRACT.md in that directory first. Then, for EVERY record in every pass file:
1. Fetch each cited source (WebFetch; if a host 403s, try one alternate copy of the same document, e.g. globenewswire / businesswire / stocktitan / sec.gov / the company newsroom). 
2. Check every number, date, name, MW figure, dollar figure and binding claim in the prose fields (headline, what_happened, why_it_matters, documented, load, fit, status, binding_note, etc.) against the fetched text. Correct the prose to match the source exactly. If a claim cannot be found on any fetched page, delete the claim; if the record's core fact cannot be confirmed, move the record to a top-level `dropped` array in the same file with a one-line `reason`.
3. `binding` is true only for an executed instrument (signed contract, award, issued approval). An MOU, LOI, selection, notice of intent, or framework that defers volumes to future task orders is false.
4. Quotes: each `quote` must be words you saw verbatim in your own fetch output; otherwise fix the quote to a verbatim span you saw, or set status `snippet-only`. Keep quotes clear of footnote digits and symbol joints.
5. Dates: an event dated after its source's publication date is impossible - fix it.
6. Plain language, no hype, no em-dash chains.

Also adjudicate these open questions and record the answers:
 a. data/opportunities.json row for Eielson AFB (Air Force ANPI / Oklo): is it shipped as binding=true on a notice of intent to award? Fetch the best available source and say whether binding should be true or false and why. Do NOT edit data/*.json; just report.
 b. web lead: Westinghouse eVinci commercial work cancelled / factory on hold (Neutron Bytes 2026-10-24). Confirm or refute from a primary page.
 c. web leads: BWXT-Antares TRISO contract and NANO-Hyundai Engineering MOU (2026-10-27). Try alternate copies of the releases. If you can confirm either, ADD it as a Type N item to news.json in the contract shape, binding false unless executed with defined volumes.
 d. NRC rule letting applicants use prior DOE/DoD authorization (proposed 2026-04-02): was it finalized? If yes with a date, ensure politics.json carries it as an item.

Edit the pass files in place (Read first, then Edit/Write). Do not touch data/*.json, site/, or tools/. At the end run `python3 tools/research_pass.py validate data/research/2026-10-27-refresh` from the repo root and fix FAIL lines.

Write a short log to data/research/2026-10-27-refresh/ADJUDICATION.md: per file, records kept / corrected / dropped with one line each, plus answers to a-d with source URLs.

FINAL MESSAGE under 200 words: counts kept/corrected/dropped per file, answers a-d, anything the main session must do by hand.

PROSPECTS (opportunity space, priority): prospects.json came back empty because the Haiku agent required a published load figure. Relax that: `load` may say "Not published" when no figure exists, as long as the counterparty, its reason to buy and its status are documented on fetched pages. Build up to 8 prospect records into prospects.json `prospects` (schema at the top of prompts/prospects.md; skip ids already in skip/prospects.json) from: the 3 `opportunities` in deals.json (Douglas County CO, Wise County VA, Meralco), the candidates named in prospects.json `_meta.absences` that have a named counterparty (e.g. Canada's northern military microreactor plan, Meadow Lake Tribal Council, Denver International Airport only if still live), the AIDEA/NuCube Alaska equity (advantage sovereignty or nuclear-interest), and any applications.json record that names a buyer without a signed reactor deal. Every fact verified on a fetched page as above. Then remove the `opportunities` array from deals.json (it is superseded by prospects).
