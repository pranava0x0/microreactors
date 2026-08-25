# DESIGN.md: Universal Visual & UX Principles

> Base file for every project in this folder with a UI. Project-specific `design.md` files extend this with palette, motif, and content rules. When project conflicts with base, project wins.
>
> Companion files: [CLAUDE.md](CLAUDE.md) is the engineering principles; [AGENTS.md](AGENTS.md) is the agent workflow.

---

## 1. Posture

Three principles set every call below:

1. **Refuse the default look (top priority).** Shipping the generic AI aesthetic (violet-to-indigo gradient, centered hero with a gradient headline and two buttons, the same sans everywhere, emoji feature cards on slate-gray) reads instantly as "a model made this" and makes the product interchangeable with a thousand others. A real product looks *decided*: each one earns a specific, defensible identity anchored in its subject. See §1.1; this overrides convenience every time.
2. **The content is the product. Chrome earns its pixels.** Anything that isn't the primary surface (map, feed, list, form, canvas) justifies itself by helping the user understand or narrow it. Backgrounds, textures, and decoration sit low (≤~10% opacity/contrast) so anything assertive is real data. Every color encodes meaning; decorative color competes with the data for attention.
3. **Performance is a design constraint, not a follow-up.** Every "nice touch" (web font, blur, full-page animation) competes with first paint and the 60fps budget. Choose perf when they conflict.

Aesthetic follows the product: an editorial dashboard reads like the FT; a consumer app like its category; a government tool like a public record. Don't paste one voice onto another. Project `design.md` carries the *specific* identity; this file carries the *universal* rules it must respect.

### 1.1 The default-AI tells, and what to do instead

The giveaways of an unconsidered, model-generated UI. Each right-hand cell is the *minimum* move away. This isn't optional polish. It's what separates a product from a demo.

| Default-AI tell | Do instead |
| --------------- | ---------- |
| Violet→indigo (or teal→blue) gradient backdrop; gradient-filled headline text | Commit to a flat palette **derived from the subject** (a water tracker → deep-water blues; a crash atlas → newsprint black/white with one alarm red; a finance tool → ledger greens on cream). One accent, used sparingly. Gradients only when they encode data (a scale, a ramp). |
| The same neutral sans (Inter / Geist / Roboto) on everything | Pick a pairing **with a point of view**: a real display face (serif, slab, or a distinctive grotesque) against a quiet workhorse. System stacks are still the default for perf (§2), but *choose* the stack deliberately; don't accept the first one. |
| Centered hero: big headline + subtitle + two buttons, nothing below the fold but feature cards | **Lead with the tool or the content.** The first screen should *do* something: show the map, the table, the feed, real numbers. Asymmetric and editorial layouts beat the symmetric marketing-page template. |
| Three-up grid of cards, each with an emoji icon and a sentence | Break the grid. Use scale, density, and rule lines to build hierarchy. Real iconography or none. Emoji is not an icon system (§11). |
| Glassmorphism, `backdrop-blur`, and a soft drop shadow on every surface | Choose **one** structural device (hairline rule lines, a hard border, a visible grid) and commit to it. Flat surfaces read as more serious and cost less per frame (§10). |
| Everything rounded to the same `1rem`/`2xl` radius | Vary radius with meaning (§5). Sharper corners read as editorial/authoritative; soft corners as friendly/consumer. Pick per project, don't default. |
| Dark mode = slate `#0f172a` with indigo accents | Derive the dark surface from the project's own palette, not the framework default. |
| "✨ New", "Beta" pill ceremony; vague benefit-copy ("Powerful insights at your fingertips") | Concrete labels, real counts, source trails. Say what the thing *is*, with a number. |

**Get creative on purpose:** before writing CSS, name the identity in one line in the project `design.md`: a reference point (a publication, era, or object), a subject-anchored palette, a type pairing, and **one memorable move** that's yours (a masthead rule, textured paper ground, monospace data spine, hand-tuned chart style). One deliberate move escapes the default; the rest of this document keeps it disciplined.

---

## 2. Typography: system stacks only by default

No web fonts unless justified: a Google Fonts link costs a render-blocking RTT and ~50KB, and the system stack approximates Charter / Inter / SF Mono everywhere.

```css
--font-sans:  -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui,
              "Helvetica Neue", Arial, sans-serif;
--font-serif: "Charter", "Source Serif 4", "Source Serif Pro",
              "Iowan Old Style", "Apple Garamond", "Palatino", "Georgia",
              "Times New Roman", serif;
--font-mono:  ui-monospace, "SF Mono", "JetBrains Mono", Menlo,
              Consolas, monospace;
```

- **Serif for editorial display** (H1, hero H2, KPI numerals, verbatim quotes). Signals "this is content, not chrome."
- **Sans for body and UI** (everything else).
- **Mono for code, IDs, paths, share codes.** Anything that has to round-trip a copy/paste.
- **Tabular numerals.** `font-feature-settings: "tnum"` on `:root`. Any column of numbers (KPIs, table cells, dates, counts) lines up.

If the project genuinely needs a custom font (rare, most don't), audit the alternative system stack on target browsers before introducing a fetch.

---

## 3. Color tokens

**All colors live as CSS custom properties on `:root`, with `[data-theme="dark"]` overrides.** JS reads via `getComputedStyle()`. Never hardcode a hex outside `:root`.

```css
:root {
  --bg: …;          /* page background */
  --surface: …;     /* cards, panels */
  --surface-2: …;   /* inputs, secondary surfaces */
  --border: …;
  --text: …;
  --text-muted: …;
  --accent: …;      /* primary CTA, focus ring */
}

[data-theme="dark"] {
  --bg: …;
  /* ... */
}
```

**Every filled surface needs an explicit `--on-<role>` foreground token, per theme.** "White text on the accent" is not a theme-independent fact: a dark theme's accent is usually a *light* tint of the same hue, so the identical rule that measures 5.4:1 in light mode measures **2.7:1** in dark. Ship `--on-accent` / `--on-status` (white on light, near-black on dark) rather than a literal `#fff` beside `background: var(--accent)`. This is the main reason the "no hardcoded hex outside `:root`" rule exists — a literal hex is precisely the thing that can't flip with the theme.

**Automate the contrast check; a colour annotated "AA" in a doc is a claim, not a measurement — including a doc you wrote.** A spec for one redesign specified an accent as `#A8862C` on a `#F2EEE3` ground and annotated it "AA at display sizes; test"; it measures **2.96:1**, below the 4.5:1 small-text floor *and* the 3:1 large-text floor, so it was unusable at any size and would have shipped as the page's primary accent. Adopting a palette from a reference site imports its contrast bugs along with its look. Compute every token against its real background **before** writing it into a spec, not after. A ~60-line test that parses the token block, computes WCAG ratios for every text/bg pair the UI actually renders, and asserts ≥4.5:1 in **both** themes will find things review never does. On its first run against a hand-written palette it caught three at once: the white-on-accent case above (2.73:1, already live); a reference amber annotated "AA on paper" that actually measured 4.48:1; and an accent-on-accent-weak pair at 4.40:1 that forced the selected tab's *label* onto the darker `--accent-hover` (the icon beside it may keep the lighter accent — non-text is WCAG 1.4.11, 3:1). Fold in the "no hardcoded hex outside the token blocks" assertion while you're there; it's the same parse.

### 3.1 Semantic separation

When a project uses color to encode meaning (status, stance, category), keep *meaning* and *brand* in separate token families:

- **Brand / surface tokens**: neutral chrome (`--bg`, `--surface`, `--text`).
- **Semantic tokens**: meaning (`--status-{success,warning,error}`, `--stance-{positive,mixed,negative}`).
- **Category tokens**: distinguish without ranking (`--category-{a,b,c}`).

Never conflate them. Coloring "category" with the same palette as "status" tells the user "category A is bad," which is rarely what you mean.

### 3.2 Brand-adjacent colors are not brand colors

When showing third-party brands (companies, products, services), use **brand-adjacent but neutral** tones: desaturated versions that distinguish without implying endorsement. Using a company's actual brand color implies affiliation and invites legal questions.

### 3.3 Theme swap is JS, not filter

Toggle light/dark via the CSS variable swap plus a JS pass over any canvas/SVG layers reading the variables. Never `filter: brightness/contrast` a tile pane or content layer. It recomposites every frame and tanks mobile perf.

---

## 4. Spacing scale

A 4 / 8 px ladder covers ~99% of cases:

`4, 6, 8, 10, 12, 14, 16, 18, 22, 24, 28, 32`

Round `7px`/`13px` to the nearest step unless you have a reason. Skip an explicit `--space-2` variable until a refactor would save more LOC than it churns.

---

## 5. Radii, shadows, motion

- **Radii:** `4` (chips), `6` (small inputs), `8` (buttons, cards), `12` (modals), `14` (mobile bottom sheets), `999` (pills).
- **Shadows:** one soft (`0 1px 2px rgba(0,0,0,0.06)`) for at-rest cards; one elevated (`0 4px 18px rgba(0,0,0,0.08)`) for panels and toasts. Dark theme uses heavier alpha (`0.4–0.5`) because contrast against a dark `--bg` needs more.
- **Motion:**
  - `90ms`: table row hover, color swaps
  - `120ms`: button / input hover
  - `200ms`: panel slide-in/out, modal open
  - `300ms max`: toast, fade
  - **No motion above 300ms.** No CSS animations on hot paths (pan / zoom / scroll).
- **Respect `prefers-reduced-motion`.** When set, kill panel transforms and any non-essential transition.

---

## 6. Layout: mobile-first, three breakpoints

Default to three viewport bands, matched 1:1 with Tailwind defaults:

| Width band     | Name    | Tailwind prefix | Layout shape                                     |
| -------------- | ------- | --------------- | ------------------------------------------------ |
| `< 640px`      | Mobile  | (none)          | Single column, sticky toolbar, FAB, bottom sheets |
| `640–1023px`   | Tablet  | `sm:`, `md:`    | 2-up grids, full CTA labels, hamburger nav        |
| `≥ 1024px`     | Desktop | `lg:`           | 3-up / 4-up grids, inline nav, side panels        |

A fourth tier is rarely justified. Desktop scales fine above 1280 if you cap content width (`max-width: 1280px; margin: 0 auto`).

**Don't use container queries unless an independent embedded component needs them.** Viewport media queries are simpler, work everywhere, and match how the rest of the layout reasons.

**Don't duplicate DOM trees for mobile / desktop.** A `<section class="hero-copy">` that's `display: none` on mobile is fine; rendering a separate mobile-only block is not.

---

## 7. Mobile patterns

- **Bottom sheets, not full-page overlays**, for detail panels and filters. A full overlay covers the primary surface and breaks the "tap a result → read → keep browsing" loop.
- **Carousels (scroll-snap), not stacked grids**, for KPI strips. Stacking pushes the primary surface below the fold.
- **Hide hero copy on mobile**, keep KPI / summary chips. The user already knows what they opened.
- **Bump input font-size to 16px on iOS** to suppress auto-zoom on focus.
- **Title attributes don't work on touch; use hover explainer cards instead.** The `title` attribute is a browser affordance on desktop (tooltip on hover) but invisible on touch. For any term that needs a definition or acronym that needs expansion, use a dedicated popover/card that appears on hover or focus, with keyboard access (Escape to close) and optional touch flow (card + link to glossary). Why: accessibility (title attributes don't reach screen readers well) + mobile coverage. How to apply: create a `.term-card` component with the term, definition, and category; auto-tag the first bare occurrence per block from a glossary.
- **Respect safe-area-inset.** Bottom-edge FABs, sheets, and bars use `bottom: max(1rem, env(safe-area-inset-bottom))` so they don't sit under the home indicator.
- **Sticky toolbars** so users can switch views from any scroll position; keep them slim (~52px).
- **Touch targets ≥ 44 × 44px.** Non-negotiable. Even for "small" admin actions. For a compact visual control (a theme swatch, a small toggle) that shouldn't grow visually, expand the *hit area* with an invisible `::before`/`::after` overlay sized to 44×44 rather than resizing the element itself.
- **The `<details>` primitive is preferred over JS accordions.** Native, keyboard-accessible, screen-reader-friendly; `open` toggle doesn't re-render the inner content.

---

## 8. Components

### 8.1 Buttons

| Variant   | Use                                  | Spec                                                 |
| --------- | ------------------------------------ | ---------------------------------------------------- |
| Primary   | The one CTA per view                 | Filled `--accent`, white text, rounded 8/12          |
| Secondary | Adjacent actions                     | Bordered, transparent bg, accent text                |
| Ghost     | Tertiary / inline                    | No border, no bg, accent text, hover bg `--surface-2` |
| Icon      | Toolbar (filters, theme, share)      | 32×32 (44×44 touch target), rounded 8, hover bg     |

Focus state is a 2px `--accent` outline with 2px offset via `:focus-visible` (not `:focus`) so mouse users don't see it on click.

### 8.2 Pills

A single base `.pill { padding: 1px 8px; border-radius: 999px; font-size: 10.5px; font-weight: 600 }` with semantic variants. Outline pills (`.pill.outline`) for "candidate" / "eligible" / "ready" signals; solid pills for status. Stack left-to-right as a readability ladder (program → status → readiness).

### 8.3 Cards

`background: var(--surface); border: 1px solid var(--border); border-radius: 12; padding: 16` is the safe default. Use shadow `0 1px 3px rgba(0,0,0,0.05)` at rest, `0 4px 12px rgba(accent, 0.15)` on hover.

### 8.4 KV grids (detail panels)

```html
<dl class="kv">
  <dt>Label</dt>
  <dd>Value <span class="dd-note">optional sub-line</span></dd>
</dl>
```

`grid-template-columns: 130px 1fr` on desktop, `110px 1fr` on mobile. Null values render as italic muted (`<dd class="muted-cell">Not available</dd>`), never blank.

### 8.5 Toasts

One at a time. Don't grow into a queue. If you need stacked toasts, swap in a real library. Lazy-mount a single `#toast` div, fade in via `.visible`, auto-fade after 4s.

### 8.6 Comparison matrix

A matrix answers a binary question: "does this entity touch this dimension at all?" Render a single `✓` per populated cell, not a count. Volume belongs in the subsidiary list, not the at-a-glance grid; digits make the matrix harder to scan and over-state precision.

### 8.7 Sub-tabs (a panel that's grown too long)

When one tab's content runs past ~2–3 screens, split it into **sub-tabs** instead of a longer scroll: a second, lighter tablist *inside* the panel (underline style, not the boxed primary tabs), each sub-panel `role="tabpanel"`. Keep the same ARIA contract as the primary tabs (`role="tab"` / `aria-selected` / roving `tabindex` / arrow-key navigation) and a ≥44px touch target on `pointer:coarse`. Example: a long comment list split into Overview / Respondent types / Comment summaries — each one screen instead of one ten-screen scroll.

Three design rules for sub-tabs and sub-panels (2026-08):
- **Omit the default sub-tab slug from the URL hash.** Landing on a panel with sub-tabs should yield a clean `#market` or `#pipeline` URL, not `#market/proposal` or `#pipeline/all`. Only secondary/non-default sub-tabs append a path suffix (e.g. `#market/other-industries`).
- **Use structured CSS grids rather than CSS multi-column (`column-count`) for card lists and accordions.** CSS column-balancing splits items across columns and reflows jarringly when an accordion expands or collapses. Use `display: grid; grid-template-columns: repeat(2, 1fr)` for multi-column cards, keeping introductory prose in a full-width header block above the grid.
- **Let prose spread across full container card widths.** Avoid hardcoding `max-width: var(--measure-prose)` inside bounded UI cards (such as sector descriptions, precedent detail cards, and deployment site cards), which leaves awkward blank gutters inside otherwise wide surfaces.

### 8.8 Metadata chips (multi-lens tags)

When a row carries several orthogonal tag sets (e.g. three classification lenses), render each lens as a small tint chip in its own color, lenses separated by a hairline. Abbreviate the chip label and carry the full meaning in `title` plus an `sr-only` group label so the grouping survives for screen readers. Keep it to ~3 lenses or the row stops scanning; push the rest to the deep-dive. Color is a *cue*, never the only signal — the text is the label.

### 8.9 Stat row — one number per real thing

A stat strip must have exactly as many cells as it has real numbers; if a metric is dropped, drop the grid column too (a `repeat(N)` that outruns the items leaves a dead cell). Never keep a stat whose label has gone stale — "9 read in full" becomes misleading once all are read. The honest number is the one a careful editor would write on deadline.

### 8.10 Model-output numbers show a fixed decimal precision

A projection or model output should always render with a fixed number of decimals (e.g. always 1), even when the value would round to a whole number. A whole-number-looking projection reads as a measured fact; one decimal signals "this is an estimate."

### 8.11 Map interactions: calm selection, and a non-map path to the same data

Selecting a result on a map should highlight and pan to it, never re-zoom, unless the item is off-screen — repeated re-zooming on every click reads as janky. Provide an explicit "fit all" reset instead of relying on zoom-out. For a large ranked dataset shown on a map, also expose it as a plain sortable table — it gives mobile users, and anyone doing a close read, a non-map path to the same ranked data.

### 8.12 Persisted UI state should default to session-only

A "last active tab" or similar convenience state should reset on a fresh page load unless there's a specific reason it shouldn't survive a visit. Use in-memory module state, not `localStorage`, for this class of affordance — persisting it to storage means a returning user lands on an arbitrary pane instead of the intended default view.

### 8.13 Sparklines & meters

A trend line at a glance is a hand-rolled inline `<svg>` `polyline`, not a charting library: a sparkline is ~20 lines of coordinate math, and a dependency for it is dead weight (§ 10, and CLAUDE.md "boring tech"). Scale the series to the box with min-max, but handle the zero-range case explicitly: when every point is equal, `span = max - min || 1` doesn't center the result, it maps every value to `1 - 0 = 1`, the far edge (a flat sparkline pinned to the bottom, not the middle). Special-case `max === min` to place the flat line at the mid-line, not wherever the degenerate division falls out. It's a lossy visual, so it carries the exact latest value in `aria-label` ("Hype over 24 observations, latest 158,000"); a screen reader and a test both need the number the glyph stands for. Fewer than 2 points: render nothing (a one-point line is noise).

A proportion bar (e.g. a within-group normalized score) is `role="meter"` with `aria-valuemin/max/now`, not a bare `<div>`. Fill width is the only thing that changes; keep the track visible so 0% still reads as "measured, low," not "missing." Never let the bar imply a comparison the data doesn't support: a bar is only honest within one comparable group (§ 12.28 below).

Build bar/column charts as **pure DOM + CSS**, not a library or a canvas: a stacked timeline is flex columns of `<div>` segments with `height`/`width` in px or %, and semantic color from `var(--status-x)` set inline. The payoff is theming — DOM/inline-SVG that references CSS vars **re-themes on the dark swap for free**, with no JS at all. The `getComputedStyle`-and-repaint pass from § 3.3 is only for *canvas/WebGL* layers that can't read a var; don't reach for it when the chart is DOM. Tabular-nums on every value, and a `title`/`aria-label` on each segment since color alone isn't a label.

---

## 9. Accessibility (baseline)

| Concern                | Implementation                                                                |
| ---------------------- | ----------------------------------------------------------------------------- |
| Skip to content        | `<a class="skip-link">` is the first focusable element; visually hidden until focused |
| Landmarks              | `<header role="banner">` · `<nav>` · `<main role="main">` · `<aside>` · `<footer role="contentinfo">` |
| Focus indicators       | `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }` on every interactive element |
| Clickable non-buttons  | A table row / card / `div` used as a control gets `role="button"` + `tabindex="0"` + an Enter/Space key handler + a focus-visible ring. A bare `onclick` is mouse-only: invisible to keyboard and screen readers |
| Live region for counts | `<span aria-live="polite">` so result counts and dynamic state changes announce |
| Filters as fieldsets   | `<fieldset><legend>` for grouped controls                                     |
| Tabs                   | `role="tablist"` / `role="tab"` / `role="tabpanel"` / `aria-controls` / `aria-selected` |
| Color contrast         | All text/bg pairs ≥ 4.5:1 in both light and dark themes (verify with audit tools) |
| Reduced motion         | `@media (prefers-reduced-motion: reduce)` kills non-essential transforms      |
| Touch                  | `touch-action: manipulation` on interactive elements                          |

---

## 10. Performance constraints on design

Design decisions that look like aesthetic calls but are actually performance calls:

| Choice                                      | Reason                                                      |
| ------------------------------------------- | ----------------------------------------------------------- |
| System fonts only (default)                 | Save a render-blocking RTT + ~50KB                          |
| No `backdrop-filter: blur` on map / overlay | Recomposites on every pan/zoom frame                        |
| No `filter:` on hot panes                   | Same                                                        |
| CSS-var theme + JS re-paint                 | Theme swap doesn't trigger a full re-style cascade          |
| Canvas markers, not SVG                     | SVG nodes melt mobile at 10k+                               |
| Pagination + IntersectionObserver           | DOM stays small; sentinel auto-appends only when needed     |
| Lazy-load non-default data layers           | First paint stays small                                     |
| Lazy-load a blocking third-party `<script>` (cdnjs html2pdf, etc.) from the handler that needs it, not `<head>` | A render-blocking `<script>` in `<head>` delays first paint *and* stalls every Playwright `page.goto`: one e2e suite went from ~11 min with 5–13 flaky load timeouts to ~52s / 0 failures once it was deferred. Keep SRI on the lazy import |
| `<link rel="preload">` for critical JSON    | Races the JSON behind defer-loaded JS                       |
| `priority: "low"` on enrichment fetches     | Browser deprioritizes behind first-paint resources          |
| `contain: layout paint` on heavy panels     | Bounds invalidation cost when content re-renders            |
| Pre-render to static HTML, not a client runtime | A client-side WASM runtime cold-starts in tens of seconds; the same site pre-rendered to static HTML paints near-instantly |

If a proposal trades any of these for visual polish, it either (a) proves it works on a mid-range Android over throttled connection, or (b) gets explicit sign-off that the perf cost is acceptable.

---

## 11. Editorial / content rules

These apply to any project that surfaces data, claims, or content from external sources.

- **Cite primary sources.** Every numeric claim links to a primary/authoritative source, or it doesn't ship.
- **Source lines are bylines, not hidden metadata.** Every chart, KPI, and table carries its agency + capture date + link, compact but visible, a footnote, not a tooltip the reader has to hunt for.
- **A citation chip names the destination it links to, not a loose association.** If a source chip links to POWER Magazine, label it "POWER Magazine", not the author's primary affiliation ("Duke"). The link target and the visible credit must agree, or the chip misattributes. Keep the person + affiliation on the card; keep the publisher on the chip that opens it.
- **Separate fact from estimate from judgment.** Render observed facts, modeled estimates, and policy/editorial judgments as visibly distinct tiers; never let a confident-sounding estimate read as a measured fact. A composite score (safety index, risk rank) always shows its components, no black-box number.
- **Mechanism-first policy language.** "Shorten the crossing distance," not "make it safer." Name the lever, not the vibe.
- **Frame vocabulary forward, not deficit.** Load-bearing product terms set the user's mental model. *Top need* and *upgrade opportunity* point forward where *weakness* points back. Choose the framing in the project `design.md`, mirror it in field names and labels, and enforce it with a test that greps the build for banned words.
- **Surface "why".** Boolean badges ("Eligible", "Verified") carry their qualifying criteria inline (italic sub-line or tooltip). The badge alone is opaque.
- **One surface, two audiences: lead lay, demote expert, keep the load-bearing number in the open.** When a page serves both a layperson and a specialist (patient + clinician, citizen + analyst), open with the plain-language answer and tuck the expert detail behind `<details>`, but never bury the one fact both audiences need (the drug strength, the dollar figure, the deadline). Progressive disclosure hides depth, not the answer.
- **Title-case CAPS source data at ingest.** Government/scraped feeds ship ALL CAPS or sentinels (`-- Not Defined --`, `_NULL_`). Run `prettyName()` at ingest, preserve raw on `*_raw`, and keep an acronym whitelist (NASA, NPS, USA, …).
- **"Not available", not blank.** Optional fields render as italic muted placeholders.
- **"Adjacent", not "0.0 mi".** Render `n < threshold` as a meaningful word, not a misleading number.
- **No emojis by default.** Outline pills do the badge work. If the project's voice needs emoji (consumer/social), use sparingly and document in `design.md`.
- **Lowercase prose, uppercase labels.** Eyebrows, KPI labels, table heads, outline-pill text are uppercase with `0.04–0.14em` tracking; everything else sentence case.
- **AI-generated content is visibly distinguished**: a 3px accent left-border plus a model-credit meta line. The reader should never confuse primary data with generated narrative.
- **Borrow design *values*, never imitate a brand.** Take the useful values from a reference publication (high-contrast type, disciplined grids, rule lines, source trails, calm authority), not its masthead, logo, proprietary fonts, or furniture that implies you *are* them. The first screen is the tool, not a marketing page.

### 11.1 Voice: write like a person, not a model

Every word that ships (headings, labels, microcopy, empty states, tooltips, generated narrative, user-facing READMEs) gets a plain, specific voice. The model register is as recognizable in copy as the violet gradient is in layout (§ 1.1). This is the prose half of "refuse the default look."

**Tells to cut:**

| Tell | Example |
| ---- | ------- |
| LLM register words | *delve, leverage, robust, seamless, elevate, unlock, empower, harness, tapestry, testament, underscore, reflect, pivotal, crucial, comprehensive, cutting-edge, game-changer, ever-evolving, realm, navigate the complexities of* |
| Stacked noun phrases (2026-07-30) | Nouns piled as unbroken modifiers instead of a phrase with real syntax: "user engagement optimization framework", "management performance improvement incentives". Unpack with a preposition or a verb: "a framework for optimizing engagement", "incentives to improve management performance" |
| Nominalization (2026-07-30) | A verb converted to a noun, forcing a second, weaker verb to carry the sentence: "make a decision" for *decide*, "conduct an investigation" for *investigate*, "provide an explanation" for *explain*. The `-tion` / `-ment` / `-ance` ending is the tell to grep for |
| Filler & throat-clearing | "it's worth noting that", "it's important to note", "in today's fast-paced world", "when it comes to", "at the end of the day" |
| Rhetorical crutches (2026-07-30) | A filler device reached for instead of just stating the point: a rhetorical question doing a transition's job ("But what does this mean for you?"), a forced pivot ("That said,", "With that in mind,"), a stage direction to the reader ("Consider this:", "Picture this:"). Cut the device, keep the sentence after it |
| Marketing vapor | "powerful insights at your fingertips", "take your X to the next level", "the ultimate solution for", "designed to help you" |
| Contrast & negation family (2026-07-30) | Named forms, all banned whether or not the underlying contrast is real. The shape reads as generated regardless of the claim's truth. **Antithesis**: "operational, not narrative"; "a configuration, not an invention"; "published, not promised"; "sell the factory, not the GPU". **Corrective negation**, antithesis's two-clause cousin: "it's not X, it's Y". **Negative parallelism** (Wikipedia's own name for this family): "not only… but also", "not X. Rather, Y", "X rather than Y". **Negative anaphora**: the same negation repeated at the start of each clause ("Not because it's fast. Not because it's cheap. Because it works."). **Contrasting-pair coupling**, no negation required: "simple yet powerful", "fast but reliable". **Rule of three / tricolon**: "fast, simple, and powerful". Rewrite to a plain declarative; where the negated half carried a number or a status, keep that by restructuring ("in 6 months, against an industry norm of 18"; "a target that has not yet shipped"). Attributed verbatim quotes are exempt |
| Hollow summaries (summary beats) | "In conclusion", "Overall", "To summarize", or any recap sentence, mid-piece or closing, that restates a point already made |
| Hedging qualifiers | "generally", "typically", "in most cases", "somewhat", "arguably", "to some extent", "it could be argued". Fine when the uncertainty is real; cut when it's a reflex on a claim you could just state |
| Ceremony | emoji in body copy (per § 11), em-dash padding, exclamation marks selling a feature, performed enthusiasm ("Great question!", "Happy to help with that!") standing in for substance |
| Caption-register phrasing | "[Person] underscores that…", "[Report] highlights the importance of…", "[Source] makes clear that…" — the caption voice narrates instead of quoting. Use a verbatim short quote or a plain attribution ("X said…", "X found…") |
| Style/boilerplate in LLM-generated text | AI-register words, em-dashes, and caption phrases in generated summaries or descriptions. Run a grep linter over the built output — it catches these for free, before any human audit |
| Motif-word overuse (2026-07-17) | one vivid word repeated as a tic across a corpus. "receipts" ran 80+ times over a ten-deck set ("energy receipts", "community receipts", "delivery receipts", "receipts attached") until it read as a verbal tic, not voice. Vary it (the numbers, the record, the data, delivered-versus-promised) or cut it; keep only literal uses ("tax receipts"). Guard the exact tell-phrases in the register linter |
| Twee meta-framing (2026-07-17) | "the honest version", "an honest read", "the honest gap/answer/trade" — announcing candor instead of just being plain. Also "here's the thing", "the real question is". State the thing; don't narrate that you're being honest |
| Comparative superlatives (2026-07-17) | "the industry's best/first/most-copied", "the rare X that", "the first X where Y" — claims-by-comparison that lean on the field instead of the fact, and in a multi-recipient set they quietly reference the *other* recipients. Say what is true of the subject on its own |
| Empty intensifiers & value-claims (2026-07-17) | "quietly" (withdrew, lapsing), "genuinely", "really", "truly", "actually", "precisely", "worth more than any press release" — padding that adds no information. Cut the adverb; keep the fact |
| Comma-staple twin fragments (2026-07-19) | "short phrase, short phrase" — two ideas stapled with a comma where one sentence belongs: "electrons to tokens, power made on site"; "the three US sites, in detail"; "the alternative, industrialized"; "margin and truth, engineered"; "Federal ground, federal speed." Reads as copywriter cadence, not something a person says. **One idea per display string:** cut the weaker fragment, or join the two into one real clause with a verb ("compute that makes its own power"; "the three US sites"; "Federal ground at federal speed."). Worst in the highest-visibility strings — heroes, hooks, section intros, nav/section labels — where it clusters. **Not** the tell: name/role bylines ("Pranava Raparla, for Crusoe", "Technical Program Manager, Data Center Operations") and conjunction-led second clauses ("…the ratepayer benefits, if the numbers are public"). Track with the `twin` column in `tools/register_report.py` (a report, not a hard gate — the editor judges each one) |

**Do instead:**

- **Lead with the specific.** A number, a name, a date beats an adjective: "Tracks 49 cases since 2014," not "comprehensive tracking of enforcement actions."
- **Vary sentence length on purpose, unpredictably.** A run of same-length sentences is its own tell (parataxis, § 11.1.2 below); say a thing and stop, then let the next one run long if the thought needs it.
- **Concrete verbs, plain nouns.** "Download the report," not "seamlessly access your documents."
- **Cut the warm-up.** If the first sentence only clears its throat, delete it and open on the point.
- **Write for the spoken voice; read it aloud.** If you wouldn't say a sentence to a colleague standing next to you, rewrite it.
- **No em-dashes in displayed prose** (house style across these projects). The em-dash reads as a model tic at scale; replace it with a comma, colon, period, or parentheses as the sentence needs. Verbatim quotes, reporter cites, and source titles are exempt. Range dashes become "to" when the identifiers already contain hyphens ("EL26-67-000 to EL26-72-000", a dash there is ambiguous). Enforce with a grep test over the rendered build.

The test mirrors the code rule ([CLAUDE.md](CLAUDE.md) → "AI has no taste"): *would a careful human writer have written this line?* If it reads like it was generated to fill space, cut it or rewrite it.

### 11.1.1 Section intros carry the point; a thesis is singular (2026-07-17)

Two structural tells, distinct from word-level ones, caught reviewing a set of pitch decks:

- **A section intro states the section's point, never its shape.** "Three ways to read the company. One conclusion.", "Two moves.", "Five internal products, whichever team owns them" describe the layout the reader can already see. Replace with the actual takeaway ("The moat is energy origination; its durable form is a repeatable machine and a public ledger"). Drop count-prefixes ("Two moves.", "Three moves.") — the reader can count the cards.
- **A thesis (or any singular-claim section: a position, a takeaway, a recommendation) states one clear claim.** Do not fill it with N parallel "reads"/"lenses" and leave the conclusion implicit — that reads as N mini-arguments, not a thesis. State the one claim, then let the angles argue *for* it. If the angles don't converge on a single claim, it isn't a thesis yet, it's background, and it belongs in the situation section, not the thesis. Applied to the decks: the "engineer's / policy / operator's read" trio now sits under a stated thesis as its argument, not in place of one.

### 11.1.2 Rhythm: the sentence- and paragraph-level tells (2026-07-30)

Word-level tells are things you can grep for. These aren't. Catching them takes a read for cadence, since no fixed word list flags a rhythm problem. Collected from a mix of AI-writing criticism (Wikipedia's "Signs of AI writing" essay names several of the word-level tells above under its own terms) and journalism craft vocabulary repurposed for the same diagnosis.

- **Parataxis (the staccato stack).** A run of short declarative sentences with no subordination or connective tissue: "This works. This scales. This lasts." Coordinate them when they're actually related: "It works because it scales, and it's lasted through three rewrites." A single short sentence after a long one is a legitimate beat; the tell is the run.
- **Uniform sentence structure within a paragraph.** Three or more consecutive sentences built on the same syntactic template (same subject position, same clause order, similar length) read as generated even when no individual sentence is wrong. Break the template: change which clause leads, or let one sentence run noticeably longer than its neighbors.
- **Setup/payoff sentence constructions.** A tease clause followed by a colon-delivered reveal ("Here's what nobody talks about: consistency.") or a rhetorical question answered in the next sentence ("So what changed? Everything."). State the point directly.
- **Landing sentences (kickers), used as a reflex.** A short aphoristic line closing a paragraph for punch ("That's the difference." "The result speaks for itself.") is a real journalism device, a kicker, when a paragraph earns one. On every paragraph it becomes a metronome. The reader learns to expect the beat and stops hearing it. Save it for the one paragraph that actually needs it.
- **Paragraph pinning.** Best working definition, not a sourced term; it reached this list secondhand with no definition attached. Reading applied here: a paragraph that opens by naming its own point or function before making it ("What this shows is…", "The key thing to understand here is…"). Let the content carry the point instead of announcing it first.
- **Vary sentence length on purpose, unpredictably.** The fix underneath all five tells above. A human writer's sentence lengths cluster unevenly, a 6-word sentence next to a 31-word one, no pattern a reader could predict two sentences ahead. Text with suspiciously even sentence lengths (the detection term is low *burstiness*) reads as generated even when every individual sentence is fine on its own.

### 11.2 SEO & social metadata

For any public page, get the share card and the dates right. They're how Google, LLMs, and social scrapers read the page:

- **Social-card OG images: ship JPG, not WebP.** LinkedIn (and some other scrapers) won't render WebP link previews. Use a JPG hero for `og:image` / `twitter:image` (`summary_large_image`); fall back to a default image for pages without a hero.
- **`datePublished` ≠ "last updated."** Derive each page's `datePublished` from its first commit (clamp to ≤ `dateModified`) and omit it when unknown; use the content's refresh date only for `dateModified`. Feeding the "last updated" value into `datePublished` republishes old pages on every data refresh, misleading to Google and LLM consumers.
- **Sitemap `<lastmod>` is the real per-page change date, never today's stamp.** And a no-op QA/UAT or "zero regressions" commit is not a content update. Date-bump logic that feeds ordering, `lastmod`, or a displayed "updated" date must skip routine non-content commits and keep the last *meaningful* change date.
- **Ship structured data + a sitemap + `llms.txt`.** A JSON-LD block (`@type` Article / Report / Dataset) with `headline`, `description`, `datePublished`/`dateModified`, `author`, `about`; a `sitemap.xml`; a `robots` meta; and an `llms.txt` for agent consumers (generated from the data, kept in sync by a test). On a GitHub Pages *project* site (`user.github.io/repo/`), `robots.txt` at the subpath is not read by crawlers that only fetch the domain root — ship it anyway for direct-fetch tools and intent documentation, but don't rely on it; submit the sitemap manually and lean on meta + JSON-LD + canonical.

---

## 12. Common pitfalls (the "scar tissue" list)

These are encoded across this folder's projects. If you're tempted to undo them, read the rationale.

### 12.1 The `[hidden]` trap

`display: inline-flex | block | flex` on an element that uses the `hidden` HTML attribute silently overrides the implicit `display: none`. The element renders despite `hidden` being set.

**Always** ship a `[hidden] { display: none }` rule alongside any `display: ...` override. If the element animates out (e.g. slide), use `visibility: hidden` + `transform` on `[hidden]` instead.

### 12.2 `text-overflow: ellipsis` no-ops on `display: inline`

A `<span>` defaults to `display: inline`; `overflow: hidden` + `text-overflow: ellipsis` silently does nothing. Always set `display: block | inline-block | flex | grid` on the element you're ellipsizing. Pair with `min-width: 0` on the parent grid item.

### 12.3 IntersectionObserver callbacks need a scroll-position guard

`isIntersecting === true` is necessary but not sufficient for "user scrolled near the bottom." During tab swaps and in headless contexts, layout can settle in multiple paint passes, firing the observer several times. Each firing prefetches another page. Add an explicit `scrollHeight - scrollTop - clientHeight > 400` check to bail when the user hasn't actually scrolled.

### 12.4 Anything that enumerates a fixed list MUST iterate the source-of-truth array

Reset buttons, dropdown populators, persona buttons, anything that touches "all programs / themes / tiers / categories" must iterate from the canonical constant array, never a hardcoded subset. When the list grows, the iterating code picks up the change for free; the hardcoded subset silently drops the new entries.

### 12.5 No web fonts without sign-off (see § 2)

### 12.6 No CSS `filter` on hot paths (see § 10)

### 12.7 Pills do NOT fall back across columns

When a row has a "Program" column and a "Status" column, the Status cell must render Status-specific content (or `—`), never the Program pill as a fallback. Two identical pills doubles visual noise without adding signal.

### 12.8 The default-AI aesthetic (see § 1.1)

Violet/indigo gradient + centered hero + two buttons + same sans + emoji cards = the model default, and it reads as disposable. Anchor a real identity in the subject first (§ 1.1). Highest-priority visual rule here, not a nice-to-have.

### 12.9 Fetch from absolute paths, and check `response.ok`

Fetch data from absolute paths (`/data/x.json`), never relative (`../data/x.json`). Relative paths break silently when the page's directory depth changes. And `fetch(...).then(r => r.json())` swallows a 404/500 into a confusing parse failure: throw on `!response.ok` with the status, and render the actual `error.message` (not a generic "failed to load") so debugging isn't blind.

### 12.10 Cache-bust user-facing assets, and rule out stale cache first when debugging

A browser serving an old `app.js` is the most common silent frontend failure. The error you see is from code that no longer exists. Version JS/CSS (`?v=YYYYMMDD`) so deploys bust the cache, and when debugging a frontend bug, hard-refresh as step one before touching code.

### 12.11 Mobile collapse must be deterministic

Don't drive a responsive show/hide off the `hidden` attribute or a native `<details open>` default alone. Once restyled, their behavior is inconsistent across breakpoints. Drive open/closed from a `matchMedia` listener with an explicit `display: none` per breakpoint (collapsed on mobile, forced visible on desktop), so the state never rides on attribute quirks. (`<details>` is still the right primitive for *user-toggled* disclosure per § 7. This is about *breakpoint-driven* collapse.)

### 12.12 A `var()` alias resolved in `:root` doesn't inherit the dark-theme override

Aliasing a semantic token to a base token in `:root` only (`--tariff-accent: var(--stance-positive)`) does **not** pick up the `[data-theme="dark"]` override. The alias resolves once against `:root`, so descendants in dark mode keep the light value and badges/chips/icons render wrong. Define the token with **literal values in both** `:root` and `[data-theme="dark"]` (mirror the working `--stance-*` / `--status-*` families); don't alias across token families and expect the theme cascade to follow.

### 12.13 `#page=N` only jumps on a same-origin, inline-rendered PDF

A deep link to a PDF page (`href=".../order.pdf#page=60"`) lands on the page *only* when the browser renders the PDF inline from the same origin. A cross-origin PDF, or one behind Cloudflare or an attachment `Content-Disposition`, ignores the fragment (or downloads instead). To deep-link a page, commit/serve the PDF same-origin; keep the official external URL as a separate visible link. Regression-test that each link's target page actually contains its quoted text.

### 12.14 The 44 px touch target is for *touch* — don't bloat desktop

A `min-height: 44px` on a small inline control (a "show more" toggle, a tag chip) makes it tower next to lightweight elements on desktop and read as a primary CTA. The 44 px guideline is about coarse pointers. Style the control at its natural chip scale and restore the touch target only where it applies:

```css
@media (pointer: coarse) {
  .show-more-toggle { min-height: 44px; padding: 10px 12px; }
}
```

Same number, applied where it matters — desktop stays visually quiet, touch stays comfortable.

### 12.15 SVG rotation via the `transform` attribute conflicts with CSS `transform-origin`

Combining an SVG `transform="rotate(-90 cx cy)"` attribute with a CSS `transform-origin` (which defaults to `50% 50%` of the element's own bounding box, not the SVG attribute's pivot) composes both, rotating the element far off its intended center — a donut-chart's colored arcs can render fully off-canvas while an unrotated background ring masks the bug. Rotate via CSS only: `transform: rotate(-90deg); transform-box: fill-box`, and drop the attribute transform.

### 12.16 CSS-only hover/disclosure popouts need `:focus-visible`, not `focus-within`

`group-hover` + `focus-within` (or the plain-CSS equivalent) keeps a popout open after a mouse click, because a click leaves the trigger focused and `focus-within` doesn't distinguish that from a real keyboard-focus visit. Use `group-has-[:focus-visible]` (or `:focus-visible` scoped to the trigger) so a mouse click doesn't leave the panel stuck open with no way to close it short of JS.

### 12.17 A truncation/disambiguation helper must be collision-aware, not fixed for the one case you saw

Shortening a name or label to fit a column (e.g. dropping a suffix) can produce two different entities rendering identically once shortened (two people both truncating to the same surname). Fixing the first collision you notice isn't enough — the helper needs a collision list, or a second, distinguishing token, not just a per-record patch. And when the fix already exists on one render path (e.g. mobile), reuse it on every other path instead of re-implementing the same display logic twice.

### 12.18 `grid-template-columns: repeat(auto-fit, minmax(...))` produces a lopsided orphan row

When the last row has fewer items than columns, `auto-fit` collapses the empty tracks and stretches the partial row to fill the width (3-then-2 items rendering as ~50%/50% instead of ~33%/33%/33%). Force `repeat(N, 1fr)` instead when the item count is known ahead of render.

### 12.19 A percentage/delta formatter must collapse near-zero before applying a sign

Rounding a small negative value (e.g. `-0.004`) *after* formatting the sign renders `-0.0%`, a value nobody wrote and nobody wants to see. Collapse `|v| < threshold` to `0` before formatting the sign.

### 12.20 `content:` glyphs need unicode escapes, not raw UTF-8 characters

A static host serving CSS without an explicit `charset=utf-8` header can mojibake a raw arrow/caret character in `content: "▾"`. Use the unicode escape (`content: "\25BE"`) instead — ASCII, encoding-proof.

### 12.21 An iframe-embedded component reads its own viewport, not the host's

`window.innerWidth` inside an embedded iframe reports the iframe's own width, not the page that embeds it. For host-viewport-based breakpoints, read `window.parent.innerWidth` with a try/catch fallback for cross-origin embeds.

### 12.22 A cached/keyed component won't re-render on a changed expression unless its key also changes

A component mounted with a stable `key` (e.g. an iframe or a memoized panel) can keep its old instance even after the JS expression driving it changes, because the framework only remounts on a key change. Bump the key alongside any logic change that must actually take effect.

### 12.23 An undefined CSS custom property silently resolves to nothing, not an error

`var(--undefined-thing)` fails silent: no console error, no failed test, just a themed component rendering invisibly (e.g. white-on-white) on whichever theme happens not to define that token. Audit `var(--x)` references against actual definitions across every theme file; don't rely on visual QA under a single theme.

### 12.24 A map library needs real container dimensions before it can size itself

Calling `setView()`/`fitBounds()` before a flex/dynamic layout has settled computes against a zero-width or stale container, causing a world-zoom or a visible jump on load; hiding the map container via `visibility`/`opacity` compounds this, since the library needs real box-model dimensions to size itself. Create the map view-less, then call `invalidateSize()` and `fitBounds({ animate: false })` inside `requestAnimationFrame` once layout has actually painted.

### 12.25 In-page anchor links inside an SPA view-router collide with hash-based routing

A numbered "on this page" jump link or a cross-tab cross-reference can't use a real `href="#section"` if the app also treats hash changes as a view-router signal — the anchor click fires the router instead of scrolling. Wire jump targets through the existing click-delegated scroll wiring (a `data-scroll-to` attribute) instead of a hash href. Where an anchor handler *does* legitimately intercept clicks for cross-tab jumps, it still has to fall through on modifier/middle-click (so cmd/ctrl/middle-click still opens a new tab) and push the fragment to `history` so the deep link is shareable and the Back button returns to the origin — prefix-agnostic matching (any in-page anchor with a resolvable target, not a hardcoded list of known ids) means new card families get cross-tab linking for free.

### 12.26 Don't trust a layout measurement taken mid-reflow

A heading or element read via `getBoundingClientRect()`/`offsetHeight` immediately after a DOM mutation can report a transient in-flight value (e.g. 800px) before layout settles to its real size (29px) a paint or two later. Re-measure after layout has actually painted (next frame / a `ResizeObserver` callback), the same class of bug as §12.24's map-sizing trap but for text/heading measurement rather than a map container.

### 12.27 Color an aggregate stance/sentiment grid by net signed value, not by plurality or presence

A cell aggregating many individual support/oppose/mixed judgments should color by net sentiment (support − oppose over engaged count), not by whichever category has the most instances (plurality) and not by whether any signal exists at all (an all-neutral cell is "no position," not "contested"). Compute the band once and share it between the cell color and the legend so they can't drift, and only render a legend swatch for a band that actually occurs in the data — a legend key for a state with zero instances (e.g. "net oppose" when 0 of 60 cells qualify) misrepresents what's on the page.

### 12.28 One sorted list of incomparable rows lies by layout

A single list sorted by a number that means different things across rows (a search-traffic estimate vs. a "present in feed" flag) tells the eye they're on one scale; the low-scale source always sinks to the bottom and reads as least important. Group into labeled per-source lanes and rank within each; label the lane ("ranked within source"). A within-lane meter (§ 8.13) then compares only comparable things. The data-layer rule behind this lives in CLAUDE.md ("don't rank incomparable series on one scale").

### 12.29 Never display a number that contradicts one you also quote

When a source's own headline figure conflicts with the detail it aggregates (an infographic whose bar labels sum to a different total than its headline number), show the source's stated figure, or its stated share, cited, not a recomputed sum. A page must never contradict a value it puts on screen elsewhere. Log the source-side discrepancy so a later editor doesn't "correct" a faithful transcription; keep a document's own subtotal over a sum of its rows when the two disagree.

### 12.30 An `overflow-x: auto` chart silently eats its newest data

A time-series whose axis outgrows its container scrolls — and a scroll container starts at `scrollLeft: 0`, i.e. parked on the **oldest** end. The recent data (usually the whole point) is off-screen with no affordance, and it reads to the user as *"the data is missing"* — not as "scroll me." Three-part fix, and you want all three: (1) size so the axis **fits** at your real breakpoints (measure, don't assume); (2) keep the **scrollbar visible** (`scrollbar-width: thin` + a styled `::-webkit-scrollbar`) — a hidden scrollbar is *how* data disappears quietly; (3) after render, **park `scrollLeft` on the most recent** column, so whatever does clip is the empty past, never the live present. Widening the bars (a grouped/parallel variant) is the usual trigger — it doubles axis width in one edit.

### 12.31 `offsetLeft` lies about clipping — measure against the scroll container's rect

`offsetLeft` is relative to the nearest **positioned** ancestor, which your scroll container usually isn't. Compare it against `scrollLeft`/`clientWidth` and you get confident nonsense — a chart that fits fine reports its last column as "clipped." For "is this child visible inside that scroller," use `getBoundingClientRect()` on both and compare the rects. (Distinct from §12.26, which is about measuring *too early*; this one is measuring against the *wrong origin*.)

### 12.32 A chart rendered inside a `display:none` tab has zero `scrollWidth`

Anything that measures or sets scroll at render time is a **silent no-op** when the view is still hidden — so the fix from §12.30 quietly doesn't apply, and the bug reappears exactly where you thought you'd killed it. Do the work again after layout exists: a `requestAnimationFrame` pass, a `ResizeObserver`, or on tab activation. Idempotent, so call it both times.

### 12.33 A filtered chart keeps a shared scale — and prefer a filter to a second visual encoding

Rescaling a chart to its **filtered** subset is a lie: a level with one record renders a full-height bar, exactly as tall as the 58-record quarter next to it. Derive the axis range **and** the y-scale from the **unfiltered** dataset, so filtering reads as filtering *in place* — categories stay comparable and a sliver stays a sliver. Pin it with a test ("the near-empty category must not render full height"); it's the kind of thing that regresses silently. Relatedly: when a small chart needs a second dimension, reach for a **filter/toggle before a second visual encoding** — texture-as-category and grouped bars both make one chart carry two scales (and grouped bars trip §12.30). Colour = one thing. If you truly must encode a second dimension inside the marks, use texture — **never** a second colour ramp.

### 12.34 A bare `1fr` grid track won't shrink below its content — pair it with `minmax(0, 1fr)`

A single-column `grid-template-columns: 1fr` has an implicit `auto` minimum: the track refuses to shrink below whatever unbreakable content lives inside it, so one long nowrap string anywhere in the subtree (a full-sentence label rendered as a badge, an un-truncated identifier) silently pushes the whole layout past the viewport. A sibling desktop breakpoint using `minmax(0, 1fr)` for the same reason is easy to miss when a narrower breakpoint is added later and copies the pattern without the `minmax`. Default to `minmax(0, 1fr)` for any grid/flex track whose content isn't provably short and fixed-width; a bare `1fr`/`flex: 1` is the exception that needs a comment justifying it, not the default.

### 12.35 `table-layout: fixed` sizes columns from the header row, and truncation on a bare `<td>` can still leak into the table's `scrollWidth`

Two related traps when a dense table needs to fit a container: (1) **`table-layout: auto` (the default) sizes every column from its widest cell across ALL rows**, so a tuned width is only a hint — one long value anywhere overrides it, and the table can render far wider than its container regardless of what CSS says. Use `table-layout: fixed` with explicit per-column widths when the container width is load-bearing. (2) Under fixed layout, **column width is set by the header `<th>` row** — if a header cell doesn't carry the same class as its column's body `<td>` (e.g. a header-building loop that only special-cases numeric columns and passes `null` for the rest), a width rule targeting that class silently matches only the body and does nothing, because the header — the thing actually sizing the column — never received it. (3) `overflow: hidden; text-overflow: ellipsis` set directly on a `<td>` clips visually, but the cell's *intrinsic* content width can still count toward the table's own `scrollWidth` under fixed layout — move the truncation onto a nested `display: inline-block` span inside the cell instead (§12.2's inline-ellipsis fix, generalized to table cells). All three compound: a table can look "fixed" by width and still overflow because the header lost its class, or overflow invisibly because its truncated cells report a false width.

---

## 13. What's intentionally NOT in design

Decisions made by *omission*:

- **No icon libraries by default.** System glyphs + outline pills cover most needs. Add Lucide/Heroicons only at ~30+ distinct glyphs.
- **No animation libraries.** CSS transitions + `animate-pulse` suffice.
- **No marker clustering** when canvas markers + decimation handle the load (`leaflet.markercluster` only when grouping is a real interaction).
- **No multi-toast queue** until a project needs it.
- **No infinite zoom / unconstrained pan.** Set `maxBounds`. Most projects have a meaningful viewport.
- **No backend until profit/scale demands one.** Static-first: JSON in `docs/`, GitHub Pages. (levels.io: "you don't need a backend.")

---

## 14. When to revisit this document

- A new component pattern emerges across 2+ projects (promote from project `design.md` to here).
- A bullet in § 12 (pitfalls) repeats in a third project. That means it needs more emphasis or a different remedy.
- A new accessibility standard lands (WCAG update, platform-level mandate).
- A perf budget regresses across the portfolio (e.g. mid-range Android performance audit).

---

## Influences

- **FT, Bloomberg Businessweek, ProPublica, Greater Greater Washington**: editorial gravitas through typography and restraint, not dependencies.
- **Linear**: typography discipline, dark UI without losing readability.
- **Apple Human Interface Guidelines**: touch targets, safe areas, mobile-first ergonomics.
- **Pieter Levels (levels.io)**: "you don't need a backend, you don't need a CSS framework, you don't need a font, you don't need npm." When in doubt, ship the simpler thing.
- **Andrej Karpathy**: performance budgets are real constraints, not afterthoughts; measure before optimizing; the smallest version that works is the right starting point.


---

## Frontend standards & performance (moved from CLAUDE.md, 2026-08-04)

_These were in CLAUDE.md's always-loaded context. They live here now; CLAUDE.md keeps the compressed non-negotiables and points at this file._


- Functional components + hooks only. TypeScript strict, no `any`.
- Colors, enums, constants in a dedicated file, never inline.
- Data transforms in hooks/utils, not components.
- Loading, error, and empty states on every view. Visible focus indicators on every interactive element.
- **Mobile-first**; test at 375px before declaring done. **Touch targets ≥ 44px on touch** — apply the 44px floor under `@media (pointer: coarse)` so inline controls (tags, chips, "show more" toggles) keep their natural chip scale on desktop instead of bloating into CTAs next to lightweight elements.
- **Deduplicate image assets;** `<picture>` + `srcset` for AVIF/WebP/PNG. Never serve uncompressed PNGs for content. **Descriptive `alt`** on every content image.
- **`object-fit: cover` only crops when the source and target aspect ratios actually differ.** A square 1771x1771 source rendered into square 120/96/72px avatar boxes had zero cropping happening in CSS — matching aspect ratios mean `cover` just scales. "Too much empty space above the subject's head" in a square photo lives in the *source file*, invisible from reading the CSS, not in an `object-position` rule that was never there. Fix it by re-cropping the master (and regenerating every derived size), and recover the true master from version control before iterating — a destructively-cropped working file can't be zoomed into further without a second, better source.
- **Only load libraries used on the page.** No backend-only deps in read-only frontends.
- **Responsive CSS, not duplicate DOM trees.**
- **Never strip comments from bundled JS with a regex.** A `//`-matching regex (even with a lookbehind) can't reliably distinguish a real comment from `//` inside a string literal, and will silently corrupt a string constant, breaking the entire bundle with one syntax error. Use a parser that tracks string/backtick context, and add a bundle-integrity test that fetches the built output and asserts a known string literal survived.
- **Two UI sections that share state only through `localStorage` need the writer to explicitly trigger the reader's re-render.** Reading state lazily on the next paint isn't sufficient since nothing schedules that paint; the data is correct in storage but the dependent view doesn't know to refresh, producing UI that looks broken despite valid state.
- **Budget the DOM.** Synchronously rendering thousands of nodes freezes the main thread (38k rows → ~265k nodes). Keep working sets in memory, render only a visible window (pagination + IntersectionObserver sentinel), hydrate in chunks across idle ticks, regression-test the node count. A sentinel can fire repeatedly before layout settles. Gate the append on a real scroll-distance check, not `isIntersecting` alone.
- **A browser tab you drive but can't keep foreground reports `visibilityState: "hidden"`, and the browser throttles hydration, rAF, and React streaming there** — so client-interactivity checks return *false failures* that mimic real bugs: clicks don't register, `__reactFiber`/`__reactProps` are absent (looks unhydrated), animations and page-turns freeze, and a streaming `loading.tsx` fallback never swaps out (two `<main>`s, real content collapsed behind a stuck spinner). Confirm the tab is actually visible before trusting a client-side read; otherwise verify server-side (DOM/DB/the API pipeline, which is visibility-independent) or from a browser instance you fully control (a headless preview you own hydrated the same build fine while the driven foreground tab did not). Same root cause as a backgrounded tab freezing rAF animation — one trap, many disguises.
- **Lossy visuals keep the value in `aria-label`.** A glyph standing in for a number (checkmark for a count) carries the exact figure in `aria-label` so screen readers and tests still get it. Guard with a test.
- **Icon + label buttons expose no accessible name — and a screenshot can't tell you.** `<button><span aria-hidden>◎</span><span>Today</span></button>` renders perfectly and lands in the a11y tree unnamed; name-from-contents doesn't reliably survive the `aria-hidden` sibling. Put an explicit `aria-label` on any button whose visible text sits beside an `aria-hidden` icon, and on any tile whose label can ellipsis (the truncated string becomes the name). Two nav bars shipped this way in one session and only reading the accessibility tree caught it: **screenshots verify layout, never a11y — read the tree.**
- **Chrome bound after an `await` is inert for the entire load.** If `main()` awaits a large fetch before wiring nav/buttons, every tap during that window silently does nothing — worst on the slow connections that need the feedback most. Bind chrome with one delegated listener at parse time; let the data fill the panels in later. (A 2.8 MB payload made a bottom tab bar dead for the whole load.)
- **Two numbers in one block must answer the same question over the same window**, or drop one. "Up 50.0" beside "52% odds" reads as a contradiction when the odds come from season-long variance and can't see the live score. A number that visibly contradicts the one above it is worse than no number. Likewise, when a card replaces a raw metric with a derived one ("+14.1 net" for "66.7 proj"), keep the input visible — a conclusion without its cause ("24.6/g · no lineup gain") reads as a bug.
- **Zero is a result; missing is not — don't let a truthiness check conflate them.** `el.textContent = n ? \`${n} items\` : ""` renders a genuinely-empty count and a never-loaded one identically. A directory filtered down to nothing then loses its "0 results" the moment its section is collapsed, which is precisely when that chip is the only thing still speaking. Guard with `Number.isFinite(n)`. **The same disease in a *metric* is worse:** an unjudged field scoring 0% reads as "always wrong" and sends someone rewriting what was never broken, so render it `—`; and a rate that counts "neither side had a value" as agreement measures sparsity rather than quality and trends to 100% (2026-07-29). Note this does *not* contradict honest-absence (don't render a zero stat tile): a tile's existence asserts a finding, so a zero one manufactures one, whereas a count chip answers "how much is in here" and `0` is a true answer.
- **The `[hidden]` trap.** A `display: ...` rule overrides the `hidden` attribute. Always ship a `[hidden] { display: none }` rule alongside it.
- **The intrinsic-width trap: a control sized by its *widest* content will not shrink in a flex row.** A `<select>` is as wide as its longest `<option>`, and as a flex item it defaults to `min-width: auto`, so it refuses to shrink below that: one 41-character option name put 404px of content in a 375px viewport and pushed the whole page into a sideways scroll. Same root as the ellipsis trap's `min-width: 0`, different symptom, and it only appears once the *content* gets long, so it ships fine and breaks later. Any flex-row control whose width follows its content (`select`, a long chip, a mono filename) needs `min-width: 0; max-width: 100%` — and test it with the longest string it will ever hold, not the current one.
- **An `aria-label` written for one variant of a page silently lies in the others.** A stats band labelled "The record in numbers" was correct on the personal view and false on the de-personalized one, where the same band held the *company's* public figures. It renders identically, contains no banned word, passes every content grep, and tells a screen-reader user the opposite of the truth. Any label describing *whose* or *what kind* of data a region holds is content, not chrome: put it in the data next to the values it names, so it varies when they do.
- **The ellipsis trap.** `overflow: hidden` + `text-overflow: ellipsis` silently no-op on a `display: inline` element (a bare `<span>`). Set `block`/`inline-block`/`flex`/`grid` on anything you expect to ellipsis, plus `min-width: 0` on a flex/grid parent so the column can shrink below intrinsic width.
- **The `<details>`-collapse trap.** An author `display:` rule on a `<details>` body (e.g. `.discourse { display: grid }`) outranks the UA rule that hides content when the element is closed, so a closed accordion keeps rendering its body. Ship `details.acc:not([open]) > :not(summary) { display: none }` alongside any styled `<details>`, and if the collapsed header is a styled `<span>` rather than a real heading, give it `role="heading" aria-level="N"` or it drops out of screen-reader heading navigation and the document outline.
- **A click anywhere inside `<summary>` toggles the panel — so a button in the header is a trap.** Export/action buttons placed in a collapsible section's `<summary>` fire their handler *and* collapse the section out from under the reader, every time. Put toolbars in the panel body. (Shipped this way for months: a directory table's CSV/PDF buttons closed the table on every export click, and it reads as "the export broke the page.")
- **Aliasing legacy class names onto a new shared rule only works if the shared rule wins the cascade.** Unifying five ad-hoc heading styles onto one rule left two components (`.hot-rail-title`, `.hot-rail-sub`) looking unchanged, because their own rules sat *later* in the stylesheet and silently re-won. The symptom reads as "my new rule didn't apply" and sends you hunting specificity that is fine. After introducing a shared rule, grep the sheet for every aliased selector and delete the now-redundant declarations — don't just add the alias. While you're there: a selector with **zero** remaining markup is dead code, not a safety net (four such rules were carried along, one of which set `color: var(--text-secondary)` where `--text-secondary` was never defined in any `:root`).
- **A styled `<span>` standing in for a heading is invisible in review and invisible in a screenshot.** Converting a section header into a collapsible summary is the moment this happens — the `<h3>` becomes a `<span>` to fit a flex layout, renders pixel-identically, and drops out of screen-reader heading navigation and the document outline. Keep the real heading element inside the `<summary>` (wrap in a `<div>`, not a `<span>` — phrasing content can't legally contain a heading), and guard it with a test that asserts every collapsible header contains an `h1`–`h6` or `[role="heading"]`.
- **Lazy-load heavy CDN libs; never block `<head>` on them.** A blocking `<script>` for a large lib (pdf renderer, charting engine) adds full-load latency and makes test suites flaky (`page.goto(..., "load")` waits on CDN). Load async on first user action (`await import(...)` or a thin wrapper). Store the SRI hash in a constant so it's auditable; don't skip SRI just because it's lazy-loaded.
- **Footer carries attribution + source.** Every shipped site footer credits the author and links the code: include `pranavaraparla.com` and the project's GitHub repo. One line, understated.
- **Don't ship the "AI-generated dashboard" look.** Generated UIs have tells that read as untrustworthy templated filler — strip them: (1) **eyebrow kickers** (tiny uppercase colored labels above every heading); (2) **cutesy section names** ("The receipts", "In their words", "Where it goes") — use plain, journalistic titles; (3) **stat cards with a colored left accent stripe + drop shadow** — prefer flat, hairline-bordered tiles; (4) **badge pills** for status (a green rounded chip with a circle checkmark) — use one understated line of text; (5) **gratuitous hover-lift** (`translateY` bounce) on every card; (6) **gradient/glass everything**. Lean flat and editorial: real type hierarchy, borders over shadows, restrained color (reserve hue for data, not chrome), self-hosted fonts. Litmus test: if it looks like every other LLM-built landing page, redesign it to look like a tool a newsroom or a product team shipped.

---


---

## Performance, reliability & bandwidth: measure, don't guess

Ship targets, then track them against real users; Google ranks on p75 *field* data, not lab averages.

- **Core Web Vitals at p75, segmented by page/device/percentile.** The `web-vitals` library reports LCP/INP/CLS for free; beacon batched on `visibilitychange`, sample at high traffic. Synthetic (Lighthouse CI) catches regressions pre-merge, RUM catches what real devices see. Run both.
- **Budget page weight + request count, fail CI on regression.** A `size-limit`/bundlesize check per route so a heavy dep fails loud, not silent. Benchmark against the lightest site in the portfolio.
- **Track bandwidth over time.** A 3× jump in transfer size / request count is a regression to investigate. (The reducing levers (AVIF/WebP, tree-shake, code-split) live in Frontend standards; this is about *watching the number*.)
- **Track error rate + uptime.** Beacon client errors (`window.onerror` or the analytics tool). A spike after a deploy is the roll-back signal. Backends also track request error rate + p95 latency.
- **Put before/after weight + CWV in any hot-path PR.** A number beats "feels fast."

### Website analytics: privacy-first, not GA4

For a content/static site, default to a **cookieless, privacy-first** tool (no consent banner, <2 ms script):

- **Skip GA4 by default:** ~2.5 MB + ~17 ms, cookies/fingerprinting, GDPR-non-compliant in parts of the EU, and consent fatigue drops 40–60% of EU traffic from the data. Use it only when you need its ad-attribution/funnels and accept the weight + banner.
- **Decision rule:** on Cloudflare → **Cloudflare Web Analytics** (free, barebones, samples). Want portability/self-host → **Plausible** (~1 KB, EU-hosted; Umami/Fathom equivalent). On Vercel and staying → **Vercel Web Analytics** (zero-config but lock-in, never the reason to stay). Need deep attribution → GA4. Never proxy a tracker through your own domain to dodge blockers (Security → privacy).

---

**2026-08-09**

- **Two `function foo()` declarations in one JS scope shadow silently, and the browser drops an invalid DOM child without raising — together they produce a bug with no error at all.** A new Places helper named `personRow` was declared after the `personRow` that builds a People-table `<tr>`. The later declaration won, so the table began appending `<div>`s into a `<tbody>`; the parser discards those, so **29 rows became 0 with an empty console, no exception, and a passing lint**. The only symptom was an end-to-end test timing out on `.table tbody tr`. Name a helper for its view (`placeRow`), not for its argument, and add a one-line guard: collect `^\s*function (\w+)` from the bundle and fail on any duplicate. Generic names (`personRow`, `render`, `item`) are exactly the ones that collide.
- **Collapsing a `<details>` you have styled does nothing unless you ship the closed-state rule.** An author `display:` on the body outranks the UA rule that hides a closed `details`' content. Prove it by measuring, not by looking: the group body read 970px open and 0px closed only once `details:not([open]) > :not(summary) { display: none }` was present. And default a disclosure to **open** — content behind one that starts closed is content a reader never finds, and every test that waits on it times out.

**2026-08-10**

- **A `var(--name)` with no definition anywhere makes the whole declaration invalid at computed-value time, so the property silently falls back to nothing.** `outline: 2px solid var(--focus)` appeared on three real controls — accordion summaries, person sub-tabs, a disclosure toggle — and `--focus` was defined in no `:root` at all. Those controls had **no visible focus ring**, and because the rules had higher specificity than the global `:focus-visible`, they beat the working rule and then evaluated to nothing. Nothing errors, nothing logs, and a screenshot looks fine. Two one-line tests close the whole class: every `var(--x)` referenced is defined, and every `--x` defined is referenced. The second half found `--mono` had been declared since the first commit and applied to *nothing*, so every email, phone and date in the app was rendering in the sans stack the design said it should not.
- **A CSS guard that reads only the shorthand is defeated by the longhand, and you will find that out by trying to do the banned thing.** An accent-stripe check matched `border-(top|left):` and flagged any `≥2px` or accent-coloured value. Writing `border-top: 2px solid transparent` on every nav item plus `border-top-color: var(--accent)` on the current one paints precisely the banned stripe in two statements and sails past. Match `border-top(-color|-width)?` — and when a guard blocks a pattern you wanted, that is the moment to check whether it can be walked around, not just to find another way.
- **A selector testing `[open]` without naming `details` is a claim about every element carrying that class.** `.group:not([open]) > :not(summary) { display: none }` was written for a Places accordion and also matched another view's `<section class="group">`; a section can never be `[open]`, so the rule hid **every row of that view** while the suite stayed green counting attached nodes. Scope details-only rules to `details.acc`, and add two static guards: no `[open]` selector may omit `details`, and no class may be used for both a `<details>` and something else in the renderer.
- **Column widths keyed on `nth-child` silently mis-assign the moment the column set becomes data-dependent.** A table gated its Tags and Origin columns on ≥20% population; the `nth-child(5) { width: 9% }` rules then applied to whichever column happened to land in slot five, so "Place" got 9% and "Last contact" got 22%. Key widths on what the column *is* (`[data-col="title"]`), which cannot drift.
- **A responsive table becomes rows without a second DOM tree.** Hide `thead`, make `tr` a flex row, and `display: none` the cells a phone has no room for — one tree, two shapes, nothing to keep in sync. The only element worth adding for the narrow shape is a secondary line carrying the values whose columns you hid, itself hidden at the wider width so nothing prints twice.
- **`flex: 1 1 auto` sizes a column from its own content, so a long line inside it can push a sibling onto its own row.** A list row's text column wrapped below its avatar plate whenever the reason line was long, orphaning the plate. `flex: 1 1 0` makes the width a pure function of the siblings and fixes it — the same zero-basis lesson as measuring a flex item mid-overflow, in pure CSS with no JS involved.
- **"Never contacted" is a fact, not missing data, and an em dash says the wrong one.** A list rendered `—` for anyone with no logged interaction. In a corpus where 27 of 29 people have never been logged, that is a column of placeholders implying broken data; the word "never" states the truth and reads as ordinary. Reserve the placeholder for values that genuinely are absent.

- **A stat strip must measure the subject, not the site.** (2026-08-21) "144 distinct sources cited" and "55 load types sized" describe the artifact; "10/15 hold a binding instrument" and "3 test reactors critical in 2026" describe the market the artifact maps. A reader asked for the second kind by name ("useless stats... I only need stats about the deployment/sales/BD"). Corollary: a summary strip repeated on every tab compounds the offence - it belongs on the landing view only, and every other tab opens straight on its own content.

### 11.2 The slop patterns a word list cannot catch (2026-08-25)

§11.1 lists banned *words*. These are banned *moves* — every one of them was shipped on this
site, read fine sentence by sentence, and made the page colder and harder to scan. The test for
all of them: **would you say this out loud to someone who just walked up to the screen?**

- **Explaining the machinery instead of using it.** "Each card carries a cited roadmap to first
  power." "Every figure links to its source." "They are not enacted policy and carry no citation."
  "What the incumbent charges, proven by a contract." The citation chips, the `idea` tag and the
  source register already say all of this, visibly, on every row. Prose that narrates the UI is
  pure overhead — delete it and let the interface speak. If the mechanism genuinely needs a
  legend, write one short legend once, not a reminder in every section.
- **Meta-commentary about the data instead of the data.** "…and that disagreement is the useful
  part." "That is worth knowing too." "Where the bands overlap is what matters." The reader
  decides what is useful; your job is to put the number in front of them. Cut the sentence that
  tells them how to feel about the previous sentence.
- **Balanced abstract headings.** "What it costs against what it displaces." The shape is a
  see-saw — two abstractions weighed against each other, naming nothing. Say the concrete thing:
  "What the power costs." A heading should survive being read alone in a table of contents.
- **Register drift into the formal.** "realised price," "whilst," "utilise," "in order to." This
  site is read by business-development people on a phone, not by a journal's copy desk. Plain
  American, short words, contractions where they fall naturally.
- **Throat-clearing before the point.** "Three buyer tracks, ranked by how far each has moved from
  interest to a signed instrument. Every figure links to its source, and the fields research could
  not reach are counted and named." Two sentences of methodology before a single fact. Front-load
  the answer, the way the federal plain-language guidance has said since 2011: lead with what is
  there, and let anyone who wants the method go find it.
- **Nominalisation.** "the fields research could not reach are counted and named" → "we say which
  fields we could not fill." Verbs beat abstract nouns, and an actor beats a passive.
- **Hedge stacking.** One qualifier is honest; three is a shrug. "Roughly, in most cases, it may
  be that…" — pick the single hedge that is actually true and commit to it.
- **The em-dash habit.** More than one per paragraph and the prose starts to sound like an
  aside about an aside. A full stop is usually the better mark.
- **Rule of three for its own sake.** Three parallel clauses when the truth has two parts, or
  four, is rhythm chosen over accuracy.

The house label rule follows from the same test: prefer **"Who is already doing this"** over
"Happening today, outside nuclear," and **"What is different about a small one"** over "What a
1–20 MW unit changes." Say it the way you would in the room.

**These apply to your own replies as well as to shipped copy** — the same list, both places.
