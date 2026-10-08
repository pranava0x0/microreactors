You are a research agent for a cited microreactor-market website (repo: /Users/pranava/Projects/microreactors). Today is 2026-10-08. The site's data was last refreshed 2026-09-26 (news to 2026-10-02).

FIRST read /Users/pranava/Projects/microreactors/data/research/2026-10-08-refresh/CONTRACT.md in full (universal source rule, record types, hard rules). Obey it exactly.
Skip lists (what the site already holds; do not repeat it) are JSON files in /Users/pranava/Projects/microreactors/data/research/2026-10-08-refresh/skip/ - read only the ones named in your task.

HARD RULES: write incrementally (first Write = _meta + first 2 records, then one Edit per record; Read your output path first and if it is already complete, stop; if partial, append the rest). Do the searches yourself; do not spawn sub-agents. Do not run anything in tools/ except, at the end, `python3 tools/research_pass.py validate data/research/2026-10-08-refresh` from the repo root - fix FAIL lines naming YOUR file, ignore others. Bail rule: 2 searches on an angle with nothing citable -> next angle; list it in _meta.absences. Numbers or nothing. Every record needs 1-2 deep-linked sources (two documents, never the same URL twice); at least one `fetched` where the type requires it. Never invent a quote.

FINAL MESSAGE (parsed, not read), under 150 words: output path, record counts by type, 2-3 surprises, absences.

TASK: Type N news `items` (up to 14) the News tab lacks, event dates 2026-09-27 to 2026-10-08 first, then 2026-06-01..09-26 gaps. Read skip/news.json first; do not repeat any id or event in it. Output: /Users/pranava/Projects/microreactors/data/research/2026-10-08-refresh/news.json (top-level keys _meta and items).
Leads (verify each in a fetched page, drop what you cannot):
- 2026-10-06 BWXT BANR microreactor selected for a Canadian project (World Nuclear News).
- 2026-10-08 Last Energy Texas micro-modular reactor clears safety analysis (WNN).
- DOE Reactor Pilot Program criticalities in 2026: Antares Mark-0 (June 4), Valar Ward 250 (June 18), Deployable Energy Unity (June 30), Aalo-X (July 4), Oklo Groves isotope test reactor (Aug 5): add any missing from skip/news.json with the DOE or company primary page.
- Radiant: $300M+ funding round, R-50 factory in Oak Ridge, DOME start-up status, Centrus-Radiant HALEU partnership (2026-09-12).
- DOE microreactor prototype at 90 percent final design (Power Engineering); Eielson town hall (DAF release).
- NRC Part 57 final rule timing (due 2026-11-23); NRC actions on Oklo, Kairos, TerraPower, X-energy, NuScale.
- Westinghouse eVinci, NANO Nuclear KRONOS, Terrestrial, Deep Fission, Last Energy UK/Poland/Texas, Army Janus site announcements.
Only items about the 1-20 MW market or events that change it (fuel, rules, financing, awards, setbacks). Larger SMR news only if it changes something for microreactor buyers.
