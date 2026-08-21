# Session state — 2026-08-21 (citation + IA overhaul, round 2)

Resume file: if this session dies, a fresh session reads THIS file plus `git log -5`
and continues from "Next actions". Keep updates terse; strike items when done.

## Where things stand

- Commit `18aad96` (branch `jam/microreactor-research-citations-a1b352`) holds round 1:
  7-tab IA, citations (144 sources), corrected economics (FOAK/NOAK/Alaska/PTC-OBBBA),
  mechanisms + policy tabs, stdlib test suite + optional Playwright e2e, CI workflow.
- Round 2 (user feedback) in progress, this list is the contract:
  1. Hero stats: replace site-meta stats with deployment/BD stats (binding instruments,
     test reactors critical, largest preorder, first delivery target, utility-filing %).
     Stats appear ONLY on the landing tab; other tabs get no hero at all.
  2. Vendors tab: per-vendor deployment timeline (done/target milestones with dates+sources).
  3. Demand tab: per-sector "how this sector powers today / what a microreactor displaces"
     intro with citations; close as many of the 12 uncited bands as possible.
     Agent writing to data/research/demand-context.json.
  4. Reference-site scan (nukebarbarian, DOE, NRC, vendor sites, FERC, WoodMac, Heatmap)
     for flow/naming ideas. Agent writing to data/research/site-flow-notes.json.
  5. Tab renames pending agent input; default decision if agent unhelpful:
     Pipeline->Deals (landing), Economics->Costs, Demand->Loads, others unchanged.
  6. Citation tooling: tools/check_citations.py (claim-number scan: any record whose
     prose carries hard numbers must have sources or an explicit uncited/idea marker)
     + tools/check_links.py (dead/blocked/live sweep). Wire scanner into tests; link
     checker manual (network in CI is flaky).
  7. /learnings pass into CLAUDE.md/companions.
  8. Ship: push branch, PR, wait for Codex bot, address comments (budget 2 rounds), merge.
  9. GitHub Pages deploy: repo may be private -> check `gh repo view --json visibility`;
     make public if needed (user pre-authorised all decisions), add
     .github/workflows/pages.yml (actions/upload-pages-artifact from site/ +
     deploy-pages), enable Pages via gh api; verify the live URL returns the real
     document (not a login page) before claiming success.

## Decisions already taken (do not relitigate)

- Stats derive in build_data.py from new data fields: `binding` bool per opportunity,
  `units_committed` (equinix 20), `reactors_critical_2026` (doe-pilot row = 3),
  `first_delivery_year` per vendor (2028/2028/2029).
- Binding=true rows: anpi-jbsa, anpi-buckley, anpi-malmstrom, dome, doe-pilot, eielson,
  equinix-radiant, uk-lastenergy, canada-src, romania-nuscale (10). False: janus, ianc,
  nano-supermicro, texas-backup, jp-kr-moc.
- Vendor milestones arrays added to vendors.json (Antares Mark-0 critical 2026-06-04;
  Radiant fuel-at-DOME 2026-07-01 + Equinix preorder 2025-08-14; eVinci DOME test +
  Penn State LOI 2026-02-28 + SRC 2029 + Malmstrom 2030), each with source.
- No co-author trailers in commits (repo config claude.coauthor=false).

## Next actions (strike as completed)

- [x] Launch agents (site-flow, demand-context)
- [x] Data: binding/units/critical fields + vendor milestones
- [x] build_data: new summary stats; app.js hero landing-only + timeline renderer
- [x] tools/check_citations.py + check_links.py + tests (scanner mutation-checked red)
- [x] Pages workflow written (.github/workflows/pages.yml, enablement:true, gates on suite)
- [x] Repo facts: github.com/pranava0x0/microreactors PRIVATE, default main, gh authed,
      no secrets/PII in tree (scanned). Plan unknown -> try Pages private, else flip public.
- [x] Integrate agent output (8 sector contexts, 4 band closures incl. 2 corrections,
      uncited 12 -> 8, tab renames Tracker/Costs/Applications)
- [x] Full suite green (29 tests incl. e2e); Applications/landing screenshots verified
- [x] /learnings written to both repos; issues.md, backlog.md, docs/agent-runs.md filled
- [x] Commits 18aad96, 2d0ad2e, baf4763; branch pushed; PR #2 open
      (https://github.com/pranava0x0/microreactors/pull/2)
- [ ] Codex review rounds on PR #2 (background poll running), then merge to main
- [ ] Pages: gh api repos/pranava0x0/microreactors/pages -X POST -f build_type=workflow
      (fallback: flip visibility public first); verify live URL serves the real document
