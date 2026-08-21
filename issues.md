# Issues

Living audit trail. Each bug: date, area, description, root cause (code bug vs data bug
vs test bug), status.

- **2026-08-21 · data · Fabricated capex scenarios in costs.json — Fixed** (commit 18aad96).
  Two LCOE rows ("CAPEX $5,000/kW (FOAK-ish)" → $80–90/MWh and "CAPEX $2,500/kW (at scale)"
  → $35/MWh) cited Abdussami et al. (arXiv 2506.13361 / Nucl. Eng. & Design), which contains
  none of those numbers — its capital-cost distribution is $2,500–4,000/kW, nth-of-a-kind.
  Root cause: **data bug** — figures carried into the dataset without checking the cited PDF
  (LLM-aggregation class; see DATA.md "AI-synthesized values are provisional"). The earlier
  expert review missed it because it reviewed the reasoning, not the provenance. Fix: rows
  replaced with NEI 2019 FOAK ($140–410/MWh) and NOAK ($90–330/MWh) bands, provenance stated
  on-page. Regression guard: tools/check_citations.py + the source-shape tests (bare-homepage
  rejection); content-level provenance still needs a human/agent read per DATA.md.
- **2026-08-21 · data · Alaska band mis-cited — Fixed** (commit 18aad96). "Small rural
  Alaskan communities $350–600/MWh (avg $520)" cited the same paper, which never mentions
  Alaska. Root cause: **data bug**, same class. Re-sourced to NEI 2019 ($300–600/MWh remote
  arctic diesel) + Alaska PCE reporting ($550–800+/MWh rural rates), band now $300–800+,
  labelled diesel-fired.
- **2026-08-21 · data · Offshore-platforms band contradicted by sources — Fixed.** Claimed
  10–50 MW total; published figures run 80–300+ MW (single platforms exceed 100 MW, FPSOs
  80–150 MW). Root cause: **data bug** (unchecked planning estimate). Band corrected in
  place; delta note records the correction. Same for land-based aquaculture (1–5 MW claimed;
  published points 0.5 and 16 MW; now 0.5–16 MW).
- **2026-08-21 · site · Hash deep links stranded mid-page — Fixed.** Panel ids double as
  hash routes, so the browser's native jump-to-anchor scrolled past the tab layout on load.
  Root cause: **code bug**. Fix: scroll-to-top on boot activation + history.scrollRestoration
  = "manual". (Note: the dev browser pane separately restores its own scroll offset across
  navigations — that half is tool artifact, not site behaviour; see AGENTS.md.)
- **2026-08-21 · site · Mobile overflow ×2 — Fixed.** Precedent category labels
  (white-space:nowrap) overflowed 375px on Market design; the 40-char
  betterbuildingssolutioncenter.energy.gov hostname overflowed the Evidence register. Root
  cause: **code bug** (nowrap on unbounded strings). Both stack/wrap on ≤640px now; the e2e
  layout gate (tests/test_layout_e2e.py) caught both and guards the class.
