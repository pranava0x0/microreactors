# Adjudication log, 2026-10-27

ideas.json skipped (still being written; main session to check).

## news.json: 3 records, 2 corrected, 1 corrected + 1 added
- antares-bwxt-triso-framework-2026-10-27: corrected. BWXT release (bwxt.com) calls it a framework with an initial 1 MTU allocation and future task orders. binding stays false.
- antares-mark1-doe-nsda-2026-10-23: corrected (INL wording, date note). binding true (formal DOE approval).
- aidea-nucube-share-purchase-2026-10-19: corrected (14.5% discount, minimum cash condition). binding false (merger not closed).
- nano-hyundai-engineering-kronos-mou-2026-10-27: ADDED, binding false. Release returned 403; terms rest on a StockTitan summary (non-exclusive MOU, no work package, no funding commitment).

## politics.json: 3 records, 3 corrected, 0 dropped
- check-licensing-1 (Alaska SB 177): shipped "August 2025" regulations is wrong; WNN (2023-07-28) says regulations took effect August 2023. Correction rewritten.
- nj-s4849: corrected from "less than 20 MW" and "request proposals" to "not more than 20 megawatts" and "competitive solicitation program for awarding micro-reactor incentive contracts".
- nrc-doe-dow-prior-authorization-final-rule-2026-10-22: confirmed (finalized 2026-10-22, 10 CFR 50.43(f) and 53.440(a)(1)); prose tightened, quotes fixed. FR publication date not verified.

## deals.json: 2 checks kept (evidence corrected), 0 dropped; `opportunities` array removed
- check-janus-1: confirmed; "four of nine unassigned" is unchecked (page says more sites announced later).
- check-doe-pilot-1: confirmed (five, named); "others in safety review" unchecked.

## applications.json: 5 corrected, 0 dropped
- Breed (960 MW; "Amazon would fund development" not found, removed), Prosperity One, NuAlaska, Idaho Strategic (1 MWe / 1.9 MWt), Natura/NGL (3M bbl/day; no water-system power figure). All out-of-band except NuSun-1 and Kaleidos.

## vendors.json: 1 check corrected, 1 item dropped
- check-valar-ward250-1: Beehive/BLM facts confirmed; the Nvidia 30 MW half is neither confirmed nor contradicted (not in the article); correction now says so.
- antares-mark1-nsda-2026-10-24: dropped, duplicate of the news record.

## prospects.json: 6 records written
Douglas County CO, Wise County VA, Canada DND northern microreactor, Meadow Lake Tribal Council, AIDEA/Alaska Fund/NuCube, Idaho Strategic Resources. Meralco dropped (300-500 MW SMR study; micro proposal shelved). Denver airport dropped (RFP paused 2025-08-08, nothing in 2026). Natura/NGL out of band (100 MW).

## Open questions
a. Eielson (data/opportunities.json): binding should be FALSE. Oklo's release (2025-06-11) says it "has been issued a Notice of Intent to Award" designating it the apparent successful offeror, and refers to "the anticipated agreement"; no contract signed. https://oklo.com/newsroom/news-details/2025/Oklo-Selected-as-Intended-Awardee-to-Provide-Clean-Reliable-Power-to-Eielson-Air-Force-Base-in-Alaska/default.aspx (DAF page 403; no 2026 status found).
b. Westinghouse eVinci cancellation: UNCONFIRMED. Only Neutron Bytes (2026-10-24) states it, with no citation; searches found no Westinghouse or second-outlet page. Westinghouse's zero-power criticality (Aug 2026) is documented. Not shipped. https://neutronbytes.com/2026/10/24/nuclear-reactor-developers-target-indiana-kentucky-for-sites-and-customers/
c. BWXT-Antares: CONFIRMED and shipped as news (bwxt.com release, fetched). NANO-Hyundai Engineering MOU: CONFIRMED via StockTitan summary only; shipped binding false. https://www.bwxt.com/bwxt-announces-contract-with-antares-for-triso-nuclear-fuel-production/ ; https://www.stocktitan.net/news/NNE/
d. NRC prior-authorization rule: FINALIZED 2026-10-22 (Power Magazine; Orrick 2026-10-23). In politics.json as an item. https://www.powermag.com/nrc-finalizes-rule-allowing-reactor-applicants-to-use-doe-dow-demonstration-data/
