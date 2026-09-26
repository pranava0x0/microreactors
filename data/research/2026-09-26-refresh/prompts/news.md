You are a research agent for a cited microreactor-market website (repo: /Users/pranava/Projects/microreactors). Job: find the dated events the site's News tab is missing, for 2026-01-01 to 2026-09-26, with priority on 2026-09-01 onward.

FIRST read /Users/pranava/Projects/microreactors/data/research/2026-09-26-refresh/CONTRACT.md in full (the universal source rule and "Type N — news items"). Then read the skip-list /Users/pranava/Projects/microreactors/data/research/2026-09-26-refresh/prompts/news-skiplist.txt: those 47 events are already on the site; do not repeat them. Output file: /Users/pranava/Projects/microreactors/data/research/2026-09-26-refresh/news.json with top-level keys `_meta` and `items`.

SCOPE: the 1-20 MW microreactor market and the adjacent events that bear on it: developer financing and listings, fuel (HALEU, TRISO), federal programs (DOE Reactor Pilot Program, Army Janus, Air Force ANPI, Navy, DOME), NRC and DOE regulatory steps (Part 57, Part 53, authorizations, safety design agreements), state law and regulations on microreactors, remote/island/Arctic deployment moves, and setbacks. Larger SMR news only when it changes something for microreactor buyers (fuel, a regulator's rule, a financing precedent).

QUOTA: up to 16 new items. Leads to check first (verify each against a fetched primary source; drop any you cannot):
- 2026-09-09 Department of War: Navy's first advanced microreactor at Naval Weapons Station Crane, Indiana (war.gov release 4593065).
- 2026-09-25 FERC rejects Oklo complaint seeking to reinstate a project to PJM's interconnection study cycle (Utility Dive; find the FERC order docket).
- 2026-09-25 X-energy TRISO-X fuel facility milestone (World Nuclear News).
- 2026-09-22 Bechtel steps away from TerraPower project; 2026-09-22 Samsung C&T invests in Kairos Power (WNN): include only if you can state why it matters for microreactor buyers.
- 2026-09-16 Holtec Palisades SMR-300 early site work approval; 2026-09-15 European Investment Bank's first SMR loan; 2026-09-24 US-Turkey SMR agreement: include at most one of these three, the one most relevant.
- 2026-06-25 and 2026-09-11/15: NuCube Energy business combination with Launch Two Acquisition Corp (BCA, then Form S-4 filed); SEC EDGAR is the primary source.
- 2026-01-12 NANO Nuclear and Ameresco MOU.
- 2026-08 DOE nuclear safety design agreement for Deep Fission's Gravity reactor.
- Radiant Kaleidos at INL's DOME: fuel receipt, startup or criticality, whichever the company or DOE has confirmed by 2026-09-26 (radiantnuclear.com blog; energy.gov).
- Alaska DEC microreactor siting regulations (adoption or effective date) and any 2026 Alaska legislative action.
- Project Pele: fuel delivered November 2025; any 2026 shipment of the reactor to INL.
- Canada/allies only if they are microreactor-specific (e.g. Yukon-Ontario SMR agreement 2026-04; Ottawa's August 2026 northern microreactor study).

METHOD: WebSearch to find, WebFetch to read and copy verbatim quotes. The event date is the date the thing happened, not the article date. Judge `binding` strictly per the contract: "down-selected for negotiation", MOUs and site announcements are false; a signed agreement, a filed S-4, a regulatory approval, an achieved criticality are true. Bail rule: 2 searches with no primary or trade-press page -> drop the lead and list it in `_meta.absences`. Do not spawn sub-agents. Do not run tools/ scripts except, at the end, `python3 tools/research_pass.py validate data/research/2026-09-26-refresh` from the repo root; fix FAIL lines naming news.json and ignore other files.

WRITE INCREMENTALLY: first Write = `_meta` + first 2 items; then one Edit per item. Before starting, Read the output path: if complete, stop; if partial, continue.

FINAL MESSAGE (parsed, not read): path, item count by category and binding, 2-3 surprises, the absences. Under 200 words.
