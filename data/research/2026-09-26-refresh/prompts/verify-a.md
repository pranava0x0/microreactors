You are a verification agent for a cited microreactor-market website (repo: /Users/pranava/Projects/microreactors). Today is 2026-09-26. Your job is to check whether claims already shipped on the site are still TRUE TODAY and are ATTRIBUTED correctly, and to write a Type G `checks` record for each.

FIRST read /Users/pranava/Projects/microreactors/data/research/2026-09-26-refresh/CONTRACT.md in full (Type G `checks` and the universal source rule). Then read your claim list: /Users/pranava/Projects/microreactors/data/research/2026-09-26-refresh/prompts/verify-a-claims.json. Output file: /Users/pranava/Projects/microreactors/data/research/2026-09-26-refresh/verify-a.json with top-level keys `_meta` and `checks`.

WHAT TO CHECK, per claim, in this order of importance:
1. Status currency. In this market projects die, slip or advance quietly. For each status, timeline or milestone, find the counterparty's own newest statement (company release, agency page, docket) and say whether the claim still holds on 2026-09-26. A milestone marked done must have happened; a target date that has passed must be reported as met or missed.
2. Attribution. A number must belong to the thing the claim attaches it to (a substation's 50 MW is not the site's 500 MW). A binding/executed label must match the instrument: a "down-selection for negotiation", an MOU or a site announcement is not executed.
3. Internal consistency: flag where two claims in your list contradict each other.

VERDICTS: confirmed | outdated (was true, no longer) | wrong (never true or misattributed) | unsupported (the cited source does not say it and you found nothing that does) | unverifiable (no reachable source either way). `outdated` and `wrong` need a `correction`: replacement text no longer than the original. Every verdict but `unverifiable` needs a fetched source.

SPECIFIC QUESTIONS:
- Army Janus (tracker row `janus` and the six 2026-08-26 news items): has any of the five Other Transactions agreements been EXECUTED (signed) by 2026-09-26, or are they still "down-selected ... for negotiation" as the Army's 2026-08-26 release (army.mil article 294891) says? Check each vendor's own release (Antares, Radiant, BWXT, General Atomics EMS, Westinghouse) and DIU. Give the right label for the tracker row (its own rule: "binding=true marks rows holding a signed, funded or awarded instrument (selection with a named site ...)") and for each news item (news "binding" means executed: a signed contract, filed application, achieved milestone, formal regulatory step).
- Radiant Kaleidos at INL's DOME: fuel arrived 2026-07-01; has it reached criticality or finished the 150-hour run by 2026-09-26 (the vendor row targets "2026 Q3")? Is the `dome` row's status "Operating" right?
- DOE Reactor Pilot Program: still five reactors critical (Antares, Valar, Deployable, Aalo, Oklo Groves) at 2026-09-26, or more?
- Eielson (Oklo): has the notice of intent to award become a contract? Any 2026 NRC or DAF milestone?
- Every other tracker row's status (Equinix-Radiant, Switch-Oklo, IANC, NANO-Supermicro, Texas backup program, DP World-Last Energy, SRC, Doicesti NuScale, US-Japan-Korea MOC, ANPI sites): still current at 2026-09-26?
- Vendor rows: is each "done" milestone real and correctly dated, and has any "target" date already passed (met or missed)?

METHOD: Start from the claim's own source_urls (WebFetch), then search for anything newer. Quote verbatim, max 2 sources per check, two sources means two documents. Prefer primary pages (army.mil, energy.gov, inl.gov, nrc.gov, sec.gov, company newsrooms). Bail rule: 2 searches without a dated primary statement -> `unverifiable`. Do not spawn sub-agents. Do not run tools/ scripts except, at the end, `python3 tools/research_pass.py validate data/research/2026-09-26-refresh` from the repo root; fix FAIL lines naming your file and ignore other files.

QUOTA AND ORDER: one check per claim that carries a date, a status, a number or a binding label; skip pure descriptions. Work in list order; if you run long, finish the current section and record what you did not reach in `_meta.absences`.

WRITE INCREMENTALLY: first Write = `_meta` + first 2 checks; then one Edit per check (or per 3 checks). Before starting, Read the output path: if complete, stop; if partial, continue.

FINAL MESSAGE (parsed, not read): path, count per verdict, the 3 most important corrections in one line each, and what you did not reach. Under 220 words.
