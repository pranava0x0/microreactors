/* Microreactor Opportunity Map — render window.MR into the page.
   No framework, no build step. Data is inlined by tools/build_data.py.

   Rendering posture: all markup is built from committed data in this repo
   (no user input, no remote fetches). Every interpolated value still passes
   esc() — defence in depth — and all HTML lands through the single render()
   sink below so the injection surface stays auditable in one place. */
(function () {
  "use strict";
  var D = window.MR;
  if (!D) { console.error("data.js did not load"); return; }
  // Tab switches manage their own scroll; the browser's automatic restoration
  // otherwise re-applies a stale offset after boot and strands the view.
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";

  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  function render(el, html) {
    el.replaceChildren();
    el.insertAdjacentHTML("afterbegin", html);
  }
  var NONE = '<span class="v none">not found</span>';
  var val = function (v) { return v ? '<span class="v">' + esc(v) + "</span>" : NONE; };

  /* Inline citation chips: numbered superscript links, one per source.
     An empty list renders an explicit "no source yet" marker, never a blank —
     an honest absence has to be visible to be fixed. */
  function cite(sources) {
    if (!sources || !sources.length) return '<span class="nosrc">no source yet</span>';
    return sources.map(function (s, i) {
      return '<a class="cite" href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer" ' +
        'title="' + esc(s.label) + '">[' + (i + 1) + "]</a>";
    }).join("");
  }
  function srcList(sources, cls) {
    return '<div class="' + (cls || "srcs") + '">' + (sources || []).map(function (x) {
      return '<a href="' + esc(x.url) + '" target="_blank" rel="noopener noreferrer">' +
        esc(x.label) + "</a>";
    }).join("") + "</div>";
  }
  function srcsOf(x) { return x.sources || (x.source ? [x.source] : []); }

  /* ---------- tabs ---------- */
  var PANELS = ["pipeline", "economics", "vendors", "demand", "market", "policy", "evidence"];
  var tablist = $("tabs");
  var tabEls = Array.prototype.slice.call(tablist.querySelectorAll(".tab"));

  function activate(id, opts) {
    opts = opts || {};
    if (PANELS.indexOf(id) === -1) id = PANELS[0];
    PANELS.forEach(function (p) {
      var panel = $(p);
      if (panel) panel.hidden = p !== id;
    });
    // The hero and its stat strip belong to the landing tab only; every other
    // tab opens straight on its own content.
    document.querySelector(".hero").hidden = id !== PANELS[0];
    tabEls.forEach(function (t) {
      var on = t.dataset.panel === id;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
      if (on && opts.focus) t.focus();
    });
    if (location.hash.slice(1) !== id) {
      if (opts.push) location.hash = id;
      else history.replaceState(null, "", "#" + id);
    }
    if (opts.scroll) window.scrollTo(0, 0);
  }

  tablist.addEventListener("click", function (e) {
    var t = e.target.closest(".tab");
    if (t) activate(t.dataset.panel, { push: true, scroll: true });
  });
  tablist.addEventListener("keydown", function (e) {
    var i = tabEls.indexOf(document.activeElement);
    if (i === -1) return;
    var next = null;
    if (e.key === "ArrowRight") next = (i + 1) % tabEls.length;
    else if (e.key === "ArrowLeft") next = (i - 1 + tabEls.length) % tabEls.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = tabEls.length - 1;
    if (next != null) {
      e.preventDefault();
      activate(tabEls[next].dataset.panel, { push: true, focus: true });
    }
  });
  window.addEventListener("hashchange", function () {
    activate(location.hash.slice(1) || PANELS[0], {});
  });

  /* ---------- hero stats ---------- */
  var s = D.summary;
  $("built").textContent = s.built;
  /* Deployment stats, not site stats: each number answers "how far along is
     this market", so all six move when the market moves. */
  var stats = [
    { n: s.opportunities, k: "opportunities mapped" },
    { n: s.binding_rows + "/" + s.opportunities, k: "hold a binding instrument", accent: true },
    { n: s.reactors_critical_2026, k: "test reactors critical in 2026", accent: true },
    { n: s.units_largest_preorder, k: "units in the largest preorder" },
    { n: s.first_delivery_year, k: "first delivery target" },
    { n: s.filing_pct + "%", k: "have a utility filing", accent: true }
  ];
  render($("stats"), stats.map(function (x) {
    return '<div class="stat"><span class="n' + (x.accent ? " accent" : "") + '">' +
      esc(x.n) + '</span><span class="k">' + esc(x.k) + "</span></div>";
  }).join(""));

  /* ---------- pipeline ---------- */
  var tracks = D.opportunities.tracks;
  var opps = D.opportunities.opportunities;
  var active = "all";

  var chips = [{ id: "all", label: "All", n: opps.length }].concat(
    tracks.map(function (t) { return { id: t.id, label: t.label, n: s.tracks[t.id] }; })
  );
  render($("filters"), chips.map(function (c) {
    return '<button class="chip" type="button" data-t="' + esc(c.id) + '" aria-pressed="' +
      (c.id === "all") + '">' + esc(c.label) + '<span class="c">' + c.n + "</span></button>";
  }).join(""));

  function trackLabel(id) {
    for (var i = 0; i < tracks.length; i++) if (tracks[i].id === id) return tracks[i].label;
    return id;
  }

  function rowHTML(o) {
    var fields = [
      ["Sector", o.sector], ["Owner", o.owner], ["Location", o.location],
      ["Vendor", o.vendor], ["Power", o.power_mw], ["Timeline", o.timeline],
      ["Instrument", o.instrument], ["Status", o.status],
      ["Land area", o.land_acres ? o.land_acres + " acres" : null],
      ["Shell / enclosure", o.shell], ["Utility filing", o.utility_filing]
    ];
    var gaps = (o.gaps || []).length
      ? '<div class="gapnote"><strong>Known gaps</strong><ul>' +
        o.gaps.map(function (g) { return "<li>" + esc(g) + "</li>"; }).join("") + "</ul></div>"
      : "";
    return '<article class="row" data-t="' + esc(o.track) + '">' +
      '<div class="rowtop" role="button" tabindex="0" aria-expanded="false">' +
        '<div><div class="rowname">' + esc(o.name) + "</div>" +
          '<div class="rowmeta"><span class="owner">' + esc(o.owner) + "</span>" +
          "<span>" + esc(o.sector) + "</span><span>" + esc(o.power_mw || "—") + "</span></div></div>" +
        '<span class="pill' + (o.track === "us-gov" ? " gov" : "") + '">' +
          esc(trackLabel(o.track)) + "</span>" +
      "</div>" +
      '<div class="detail"><div class="grid2">' +
        fields.map(function (f) {
          return '<div class="field"><span class="k">' + esc(f[0]) + "</span>" + val(f[1]) + "</div>";
        }).join("") +
      "</div>" + gaps + srcList(o.sources) + "</div></article>";
  }

  function renderRows() {
    var list = active === "all" ? opps : opps.filter(function (o) { return o.track === active; });
    render($("rows"), list.map(rowHTML).join(""));
  }

  $("filters").addEventListener("click", function (e) {
    var b = e.target.closest(".chip");
    if (!b) return;
    active = b.dataset.t;
    Array.prototype.forEach.call(this.querySelectorAll(".chip"), function (c) {
      c.setAttribute("aria-pressed", String(c === b));
    });
    renderRows();
  });

  function toggle(top) {
    var row = top.parentNode, open = row.classList.toggle("open");
    top.setAttribute("aria-expanded", String(open));
  }
  $("rows").addEventListener("click", function (e) {
    var t = e.target.closest(".rowtop");
    if (t && !e.target.closest("a")) toggle(t);
  });
  $("rows").addEventListener("keydown", function (e) {
    var t = e.target.closest(".rowtop");
    if (t && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); toggle(t); }
  });
  renderRows();

  /* ---------- economics ---------- */
  var bands = [];
  D.costs.microreactor_lcoe.forEach(function (c) {
    bands.push({ lab: c.scenario, lo: c.low_mwh, hi: c.high_mwh, cls: "micro",
                 srcs: srcsOf(c), caveat: c.caveat });
  });
  D.costs.displaced_alternatives.forEach(function (a) {
    if (a.low_mwh != null) bands.push({ lab: a.alternative, lo: a.low_mwh, hi: a.high_mwh, cls: "alt",
                                        srcs: srcsOf(a) });
  });
  var MAX = 850;
  // Round for display: the underlying study reports cents, but a chart label
  // implying two-decimal precision on a forward-looking cost estimate is false
  // precision. Full values stay in data/costs.json.
  var money = function (n) { return "$" + Math.round(n); };
  render($("chart"), bands.map(function (b) {
    var lo = Math.max(0, b.lo), hi = Math.max(lo + 4, b.hi);
    var left = (lo / MAX) * 100, width = ((hi - lo) / MAX) * 100;
    var txt = Math.round(b.lo) === Math.round(b.hi)
      ? money(b.lo) : money(b.lo) + "–" + Math.round(b.hi);
    // A band narrower than its own label pushes the text outside the bar rather
    // than letting it spill across the edge.
    var narrow = width < 11;
    return '<div class="bar"><div class="lab">' + esc(b.lab) + cite(b.srcs) + "</div>" +
      '<div class="track"><div class="span ' + b.cls + (narrow ? " narrow" : "") +
      '" style="left:' + left.toFixed(1) + "%;width:" + Math.max(width, 2.5).toFixed(1) +
      '%"><span class="t">' + esc(txt) + "</span></div></div>" +
      (b.caveat ? '<div class="caveat">' + esc(b.caveat) + "</div>" : "") + "</div>";
  }).join("") +
    '<div class="axis"><span>$0</span><span>$' + MAX / 2 + "</span><span>$" + MAX + "/MWh</span></div>");

  render($("altnotes"), D.costs.displaced_alternatives.filter(function (a) {
    return a.low_mwh == null;
  }).map(function (a) {
    return '<div class="altnote"><span class="k">' + esc(a.alternative) + " · </span>" +
      esc(a.note) + cite(srcsOf(a)) + "</div>";
  }).join(""));

  render($("reading"), esc(D.costs.reading).replace(/\*\*(.+?)\*\*/g, "<strong style=\"color:var(--text-primary)\">$1</strong>"));

  var inc = D.costs.incentives;
  if (inc) {
    $("ptc-q").textContent = inc.question;
    render($("incentives"), '<div class="inc"><div class="lead">' + esc(inc.answer) + "</div><ul>" +
      inc.points.map(function (p) {
        return "<li>" + esc(p.fact) + cite(srcsOf(p)) + "</li>";
      }).join("") +
      "</ul>" + (inc.caveat ? '<div class="cv">' + esc(inc.caveat) + "</div>" : "") + "</div>");
  }

  /* ---------- vendors ---------- */
  render($("vendorcards"), D.vendors.vendors.map(function (v) {
    var specs = [
      ["Output", v.mwe_label], ["Coolant", v.coolant], ["Fuel", v.fuel],
      ["Refuelling", v.refuel_years ? "every " + v.refuel_years + " yr" : null],
      ["ANPI site", v.anpi_site], ["Footprint", v.land_acres ? v.land_acres + " acres" : null],
      ["Mass", v.mass_tonnes ? v.mass_tonnes + " t" : null],
      ["Target", v.first_delivery_target]
    ].filter(function (x) { return x[1]; });
    var gaps = (v.gaps || []).length
      ? '<div class="gapnote"><strong>Known gaps</strong><ul>' +
        v.gaps.map(function (g) { return "<li>" + esc(g) + "</li>"; }).join("") + "</ul></div>"
      : "";
    var tl = (v.milestones || []).length
      ? '<div class="vtlhead">Roadmap to power</div><div class="vtl">' +
        v.milestones.map(function (m) {
          return '<div class="ms ' + (m.status === "done" ? "done" : "tgt") + '">' +
            '<span class="d">' + esc(m.date) + '</span><span class="dot" aria-hidden="true"></span>' +
            '<span class="l">' + esc(m.label) + cite(m.source ? [m.source] : []) + "</span></div>";
        }).join("") + "</div>"
      : "";
    return '<div class="vcard"><h3>' + esc(v.name) + '</h3><span class="r">' + esc(v.reactor) + "</span>" +
      specs.map(function (x) {
        return '<div class="vspec"><span class="k">' + esc(x[0]) + '</span><span class="v">' +
          esc(x[1]) + "</span></div>";
      }).join("") + tl + gaps + srcList(v.sources, "vsrcs") + "</div>";
  }).join(""));

  /* ---------- demand accordions ---------- */
  render($("sectors"), D.sectors.sectors.map(function (sec, i) {
    var cited = sec.loads.filter(function (l) { return (l.sources || []).length; }).length;
    return '<details class="sector"' + (i === 0 ? " open" : "") + "><summary>" +
      "<h3>" + esc(sec.sector) + "</h3>" +
      '<span class="meta">' + sec.loads.length + " loads · " + cited + " cited</span>" +
      "</summary>" +
      (sec.context
        ? '<div class="sectorctx">' + esc(sec.context.today) + cite(sec.context.sources) + "</div>"
        : "") +
      '<div class="loads">' +
      sec.loads.map(function (l) {
        return '<div class="load"><span>' + esc(l.label) +
          (l.note ? '<span class="note">' + esc(l.note) + "</span>" : "") +
          (l.delta_note ? '<span class="delta">' + esc(l.delta_note) + "</span>" : "") +
          '</span><span class="b">' + esc(l.band) + cite(l.sources) + "</span></div>";
      }).join("") + "</div></details>";
  }).join(""));

  /* ---------- market design ---------- */
  var M = D.mechanisms;
  if (M && M.proposal) {
    render($("market-intro"), esc(M.intro) +
      ' <span class="proposaltag">proposal — precedents cited below</span>');
    render($("mechanism"), '<div class="mech">' + M.proposal.cards.map(function (c) {
      return '<div class="mechcard"><h4>' + esc(c.title) + "</h4>" +
        (c.paras || []).map(function (p) { return "<p>" + esc(p) + "</p>"; }).join("") +
        (c.steps && c.steps.length
          ? '<ol class="steps">' + c.steps.map(function (st) { return "<li>" + esc(st) + "</li>"; }).join("") + "</ol>"
          : "") +
        "</div>";
    }).join("") + "</div>");
    render($("precedents"), (M.precedent_groups || []).map(function (g) {
      return '<div class="pgroup"><h4>' + esc(g.name) + "</h4>" +
        g.items.map(function (p) {
          return '<details class="prec"><summary><span class="nm">' + esc(p.name) + "</span>" +
            '<span class="cat">' + esc(p.category) + "</span></summary>" +
            '<div class="body">' +
            '<p><span class="k">Mechanism · </span>' + esc(p.mechanism) + "</p>" +
            '<p><span class="k">Outcome · </span>' + esc(p.outcome) + "</p>" +
            (p.early_vs_late ? '<p><span class="k">Early vs late orders · </span>' + esc(p.early_vs_late) + "</p>" : "") +
            (p.relevance ? '<p><span class="k">Read-across · </span>' + esc(p.relevance) + "</p>" : "") +
            srcList(p.sources) + "</div></details>";
        }).join("") + "</div>";
    }).join(""));
  }

  /* ---------- policy pathways ---------- */
  var P = D.policy;
  if (P) {
    render($("pathways"), P.groups.map(function (g) {
      return '<div class="pgroup"><h4>' + esc(g.name) + "</h4>" +
        g.pathways.map(function (pw) {
          var tag = pw.kind === "idea" ? ' <span class="ideatag">idea</span>' : "";
          var srcs = (pw.sources || []).length ? cite(pw.sources)
            : (pw.kind === "idea" ? "" : '<span class="nosrc">no source yet</span>');
          return '<div class="pw"><div class="top"><span class="nm">' + esc(pw.name) + "</span>" +
            '<span class="st">' + esc(pw.status) + "</span>" + tag + "</div>" +
            "<p>" + esc(pw.mechanism) + " " + srcs + "</p></div>";
        }).join("") + "</div>";
    }).join(""));
  }

  /* ---------- evidence: source register ---------- */
  var reg = D.sources_index || [];
  render($("evsummary"),
    esc(s.source_count) + " distinct sources back " + esc(s.cited_rows) + "/" + esc(s.opportunities) +
    " pipeline rows and " + esc(s.cited_loads) + "/" + esc(s.load_types) +
    " demand bands; the uncited bands are named on the Demand tab.");
  render($("register"), '<div class="reg">' + reg.map(function (r) {
    var uses = r.uses.slice(0, 3).join(" · ") + (r.uses.length > 3 ? " · +" + (r.uses.length - 3) + " more" : "");
    return '<div class="rrow"><span><a href="' + esc(r.url) + '" target="_blank" rel="noopener noreferrer">' +
      esc(r.label) + '</a><span class="uses">cited by: ' + esc(uses) + '</span></span>' +
      '<span class="host">' + esc(r.host) + "</span></div>";
  }).join("") + "</div>");

  /* ---------- coverage ---------- */
  render($("coverage"), D.gaps.field_coverage.map(function (c) {
    var red = c.pct < 50;
    return '<div class="cov"><span class="lab">' + esc(c.field.replace(/_/g, " ")) + "</span>" +
      '<div class="covbar"><div class="covfill" style="width:' + c.pct + "%;background:" +
      (red ? "var(--antares-red)" : "var(--stone-500)") + '"></div></div>' +
      '<span class="p">' + c.have + "/" + c.total + "</span></div>";
  }).join(""));

  render($("next"), D.gaps.next_pass.map(function (n) {
    return '<div class="nextcard"><h4>' + esc(n.target) + "</h4>" +
      '<p class="prose" style="margin-bottom:var(--space-3)">' + esc(n.why) + " " + esc(n.why_search_failed) + "</p>" +
      '<p class="prose"><span class="k" style="color:var(--text-tertiary)">Where to look: </span>' +
      esc(n.where) + "</p></div>";
  }).join(""));

  /* boot: land on the panel the hash names, or the first. scroll:true beats
     the browser's native jump-to-anchor, which otherwise strands a deep link
     mid-page because the section ids double as hash routes. */
  activate(location.hash.slice(1) || PANELS[0], { scroll: true });
})();
