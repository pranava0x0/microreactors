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

  /* Inline citation chips carry the source's number in the Sources register,
     assigned once by tools/build_data.py and reused wherever that URL appears.
     The same source is the same number on every tab, so a chip is an address
     into the register rather than a per-row counter restarting at [1] on each
     bullet. An empty list renders an explicit "no source yet" marker, never a
     blank: an absence has to be visible to be fixed. A source whose page was
     never directly read (status snippet-only: search-corroborated, usually a
     bot-walled host) renders with a dagger so it never dresses as a full
     citation. */
  var NUM = D.source_numbers || {};
  function citeNum(url) { return NUM[url] || "?"; }
  // Citations written straight into index.html carry a "[?]" placeholder; the
  // number comes from the same register as every generated chip, so a static
  // and a data-driven citation of one URL can never print different numbers.
  Array.prototype.forEach.call(document.querySelectorAll("a.cite"), function (a) {
    a.textContent = "[" + citeNum(a.getAttribute("href")) + "]";
  });
  function cite(sources) {
    if (!sources || !sources.length) return '<span class="nosrc">no source yet</span>';
    return sources.map(function (s) {
      var snip = s.status === "snippet-only";
      return '<a class="cite" href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer" ' +
        'title="' + esc(s.label) + (snip ? " \u00b7 search-corroborated; page not directly fetched" : "") +
        '">[' + citeNum(s.url) + (snip ? "\u2020" : "") + "]</a>";
    }).join("");
  }
  /* Filing trails render on both the Sites cards and the Price-to-beat rows.
     One function, so a fix to either reaches both. */
  function filingList(filings, heading) {
    if (!filings || !filings.length) { return ""; }
    return '<div class="filingtrail"><h4>' + esc(heading || "Regulatory & utility filings") +
      "</h4>" + filings.map(function (f) {
        return '<div class="filingrow">' +
          '<span class="filingforum">' + esc(f.forum) + "</span>" +
          '<span class="filingdesc">' +
            (f.url ? '<a href="' + esc(f.url) + '" target="_blank" rel="noopener noreferrer">' +
              esc(f.type) + "</a>" : esc(f.type)) +
            (f.id ? " &middot; <code>" + esc(f.id) + "</code>" : "") +
            (f.note ? ' <span class="note">(' + esc(f.note) + ")</span>" : "") +
          "</span>" +
          '<span class="filingdate">' + esc(f.date || "") + "</span>" +
          "</div>";
      }).join("") + "</div>";
  }

  function srcList(sources, cls) {
    return '<div class="' + (cls || "srcs") + '">' + (sources || []).map(function (x) {
      var snip = x.status === "snippet-only";
      return '<a href="' + esc(x.url) + '" target="_blank" rel="noopener noreferrer"' +
        (snip ? ' title="search-corroborated; page not directly fetched"' : "") +
        '><span class="sn">' + citeNum(x.url) + "</span>" +
        esc(x.label) + (snip ? "\u2020" : "") + "</a>";
    }).join("") + "</div>";
  }
  function srcsOf(x) { return x.sources || (x.source ? [x.source] : []); }

  /* ---------- tabs ---------- */
  var PANELS = ["pipeline", "sites", "economics", "vendors", "demand", "market", "policy", "sources"];
  /* Sub-navigation, registered by makeSubnav() below. Four panels were long
     enough to bury their own sections at 1280px before this split: policy ran
     30,900px and the source register 67,500px, so field coverage and the gap
     register sat ~90 screens below the fold. Routes are "panel/sub", so a
     sub-section is still linkable. */
  var SUBS = {};
  /* Routes that used to exist. The Sources tab shipped as "Evidence" until
     2026-08-23, so #evidence is live in anything already linked or bookmarked;
     without this it falls through to the unknown-route branch and strands the
     reader on the Tracker. activate() rewrites the hash to the canonical id. */
  var ALIASES = { evidence: "sources" };
  var slug = function (t) {
    return String(t).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  };
  var tablist = $("tabs");
  var tabEls = Array.prototype.slice.call(tablist.querySelectorAll(".tab"));

  function activate(route, opts) {
    opts = opts || {};
    var parts = String(route || "").split("/");
    var id = parts[0], sub = parts[1] || "";
    if (ALIASES[id]) id = ALIASES[id];
    if (PANELS.indexOf(id) === -1) { id = PANELS[0]; sub = ""; }
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
    var subRes = SUBS[id] ? SUBS[id].show(sub) : "";
    var here = id + (subRes ? "/" + subRes : "");
    if (location.hash.slice(1) !== here) {
      if (opts.push) location.hash = here;
      else history.replaceState(null, "", "#" + here);
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
      activate(tabEls[next].dataset.panel, { push: true, focus: true, scroll: true });
    }
  });
  // Back/Forward land like any other tab switch: top of the newly shown panel.
  window.addEventListener("hashchange", function () {
    activate(location.hash.slice(1) || PANELS[0], { scroll: true });
  });

  /* One sub-tab strip per long panel. Items are [{id, label}]; each maps to a
     [data-sub] element already inside the panel. The strip wraps rather than
     scrolls, so no sub-section can sit off-screen unannounced. */
  function makeSubnav(panelId, items) {
    var panel = $(panelId), host = panel.querySelector(".subtabs");
    if (!host || !items.length) return;
    render(host, items.map(function (it) {
      return '<button class="subtab" type="button" role="tab" data-go="' + esc(it.id) +
        '" id="' + esc(panelId + "-tab-" + it.id) + '" aria-controls="' +
        esc(panelId + "-" + it.id) + '">' + esc(it.label) + "</button>";
    }).join(""));
    var btns = Array.prototype.slice.call(host.querySelectorAll(".subtab"));
    var ids = items.map(function (x) { return x.id; });
    Array.prototype.forEach.call(panel.querySelectorAll("[data-sub]"), function (el) {
      el.setAttribute("aria-labelledby", panelId + "-tab-" + el.getAttribute("data-sub"));
    });
    function show(id) {
      if (!id || ids.indexOf(id) === -1) id = ids[0];
      var isDefault = id === ids[0];
      Array.prototype.forEach.call(panel.querySelectorAll("[data-sub]"), function (el) {
        el.hidden = el.getAttribute("data-sub") !== id;
      });
      btns.forEach(function (b) {
        var on = b.dataset.go === id;
        b.setAttribute("aria-selected", String(on));
        b.tabIndex = on ? 0 : -1;
      });
      return isDefault ? "" : id;
    }
    host.addEventListener("click", function (e) {
      var b = e.target.closest(".subtab");
      if (b) {
        var targetSub = b.dataset.go === ids[0] ? "" : b.dataset.go;
        activate(panelId + (targetSub ? "/" + targetSub : ""), { push: true, scroll: true });
      }
    });
    host.addEventListener("keydown", function (e) {
      var i = btns.indexOf(document.activeElement), n = null;
      if (i === -1) return;
      if (e.key === "ArrowRight") n = (i + 1) % btns.length;
      else if (e.key === "ArrowLeft") n = (i - 1 + btns.length) % btns.length;
      else if (e.key === "Home") n = 0;
      else if (e.key === "End") n = btns.length - 1;
      if (n == null) return;
      e.preventDefault();
      var targetSub = btns[n].dataset.go === ids[0] ? "" : btns[n].dataset.go;
      activate(panelId + (targetSub ? "/" + targetSub : ""), { push: true, scroll: true });
      btns[n].focus();
    });
    SUBS[panelId] = { show: show };
    show(ids[0]);
  }

  /* ---------- hero stats ---------- */
  var s = D.summary;
  $("built").textContent = s.built;
  /* Deployment stats, not site stats: each number is a market event, not a
     count of what this site happens to curate. */
  var stats = [
    { n: s.milestones_2026, k: "vendor milestones hit in 2026" },
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

  var pipeItems = [{ id: "all", label: "All (" + opps.length + ")" }].concat(
    tracks.map(function (t) {
      return { id: t.id, label: t.label + " (" + (s.tracks[t.id] || 0) + ")" };
    })
  );

  render($("pipelinetracks"),
    '<div data-sub="all" id="pipeline-all" role="tabpanel" tabindex="0">' +
      '<div class="rows">' + opps.map(rowHTML).join("") + "</div></div>" +
    tracks.map(function (t) {
      var trackOpps = opps.filter(function (o) { return o.track === t.id; });
      return '<div data-sub="' + esc(t.id) + '" id="pipeline-' + esc(t.id) + '" role="tabpanel" tabindex="0">' +
        '<p class="prose trackblurb">' + esc(t.blurb) + "</p>" +
        '<div class="rows">' + trackOpps.map(rowHTML).join("") + "</div></div>";
    }).join("")
  );
  makeSubnav("pipeline", pipeItems);

  function toggle(top) {
    var row = top.parentNode, open = row.classList.toggle("open");
    top.setAttribute("aria-expanded", String(open));
  }
  $("pipelinetracks").addEventListener("click", function (e) {
    var t = e.target.closest(".rowtop");
    if (t && !e.target.closest("a")) toggle(t);
  });
  $("pipelinetracks").addEventListener("keydown", function (e) {
    var t = e.target.closest(".rowtop");
    if (t && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); toggle(t); }
  });

  /* ---------- candidate deployment sites ---------- */
  if (D.deployment_sites && D.deployment_sites.sites) {
    var sites = D.deployment_sites.sites;
    render($("sites-summary"), [
      { n: String(sites.length), k: "candidate sites tracked" },
      { n: "5", k: "load categories covered" },
      { n: String(sites.filter(function (s) { return s.filings && s.filings.length; }).length), k: "sites with active filings", accent: true },
      { n: "0", k: "FERC microreactor hits", accent: true }
    ].map(function (x) {
      return '<div class="dstat"><span class="n' + (x.accent ? " accent" : "") + '">' +
        esc(x.n) + '</span><span class="k">' + esc(x.k) + "</span></div>";
    }).join(""));

    var renderSiteCard = function (s) {
      var stCls = "status-" + slug(s.status);
      var filingsHTML = filingList(s.filings);
      var gapsHTML = "";
      if (s.gaps && s.gaps.length) {
        gapsHTML = '<div class="sitegaps"><strong>Evidence gaps:</strong> ' +
          s.gaps.map(function (g) { return esc(g); }).join(" &middot; ") + "</div>";
      }
      return '<div class="sitecard" id="site-' + esc(s.id) + '">' +
        '<div class="shdr">' +
          "<h3>" + esc(s.name) + "</h3>" +
          '<div class="smeta">' +
            '<span class="sitetag ' + stCls + '">' + esc(s.status) + "</span>" +
            '<span class="sitetag">' + esc(s.depth) + "</span>" +
            '<span class="sitetag">' + esc(s.country) + (s.region ? " &middot; " + esc(s.region) : "") + "</span>" +
          "</div>" +
        "</div>" +
        '<div class="sitedetails">' +
          '<div class="drow"><span class="dlbl">Category:</span><span>' + esc(s.category) + (s.band ? " &middot; " + esc(s.band) : "") + "</span></div>" +
          '<div class="drow"><span class="dlbl">Owner/Host:</span><span>' + esc(s.owner || "") + "</span></div>" +
          '<div class="drow"><span class="dlbl">Reactor:</span><span>' + esc(s.vendor || "") + (s.power ? " (" + esc(s.power) + ")" : "") + "</span></div>" +
          '<div class="drow"><span class="dlbl">Utility:</span><span>' + esc(s.utility_context || "Behind-the-meter") + "</span></div>" +
        "</div>" +
        '<div class="sitesummary">' + esc(s.summary) + " " + cite(s.sources) + "</div>" +
        filingsHTML +
        gapsHTML +
        "</div>";
    };

    var univSites = sites.filter(function (s) {
      return s.category === "Civic Infrastructure";
    });
    var defSites = sites.filter(function (s) {
      return s.category === "Defense installations" || (s.category === "Electric Utilities" && s.id === "cvea-valdez");
    });
    var commSites = sites.filter(function (s) {
      return s.category === "Compute" || s.category === "Oil & Gas" || (s.category === "Electric Utilities" && s.id !== "cvea-valdez");
    });

    var negs = D.deployment_sites._meta.negative_findings || [];
    var negHTML = '<div class="negfindings">' +
      negs.map(function (n) {
        return '<div class="negfinding">' +
          "<h4>Confirmed negative docket finding</h4>" +
          "<p>" + esc(n.finding) + " " + cite(n.sources) + "</p>" +
          "</div>";
      }).join("") +
      (D.deployment_sites._meta.category_absences
        ? '<div class="negfinding"><h4>Category absences</h4><p>' +
          esc(D.deployment_sites._meta.category_absences) + "</p></div>"
        : "") +
      "</div>";

    var siteItems = [
      { id: "all", label: "All (" + sites.length + ")" },
      { id: "universities-labs", label: "Universities & Labs (" + univSites.length + ")" },
      { id: "defense-remote", label: "Defense & Remote (" + defSites.length + ")" },
      { id: "commercial-grid", label: "Commercial & Grid (" + commSites.length + ")" },
      { id: "findings-absences", label: "Findings & Absences" }
    ];

    render($("sites-content"),
      '<div data-sub="all" id="sites-all" role="tabpanel" tabindex="0">' +
        '<div class="sitesgrid">' + sites.map(renderSiteCard).join("") + "</div></div>" +
      '<div data-sub="universities-labs" id="sites-universities-labs" role="tabpanel" tabindex="0">' +
        '<div class="sitesgrid">' + univSites.map(renderSiteCard).join("") + "</div></div>" +
      '<div data-sub="defense-remote" id="sites-defense-remote" role="tabpanel" tabindex="0">' +
        '<div class="sitesgrid">' + defSites.map(renderSiteCard).join("") + "</div></div>" +
      '<div data-sub="commercial-grid" id="sites-commercial-grid" role="tabpanel" tabindex="0">' +
        '<div class="sitesgrid">' + commSites.map(renderSiteCard).join("") + "</div></div>" +
      '<div data-sub="findings-absences" id="sites-findings-absences" role="tabpanel" tabindex="0">' +
        negHTML + "</div>"
    );
    makeSubnav("sites", siteItems);
  }

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

  makeSubnav("economics", [{ id: "bands", label: "Cost bands" },
                           { id: "tax-credit", label: "Tax credit" },
                           { id: "price-to-beat", label: "Price to beat" }]);

  /* ---------- price to beat: signed deals, with the number attached ---------- */
  var B = D.benchmarks;
  if (B && B.sectors) {
    render($("benchsummary"),
      esc(s.benchmarks) + " deals that were actually signed, across " +
      esc(B.sectors.length) + " sectors. " + esc(s.benchmarks_priced) +
      " carry a published price, capex or displaced cost; " + esc(s.benchmarks_filed) +
      " carry the filing, award notice or rate order that proves it. Every row is a " +
      "non-nuclear incumbent \u2014 this is the number a reactor has to beat, not a " +
      "forecast of what one would charge.");

    render($("benchmarks"), B.sectors.map(function (sec) {
      return '<div class="benchsector"><h4>' + esc(sec.sector) +
        ' <span class="cnt">' + sec.records.length + "</span></h4>" +
        '<div class="precgrid">' + sec.records.map(function (c) {
          var facts = [
            ["Signed", c.signed], ["Term", c.term_years ? c.term_years + " years" : ""],
            ["Instrument", c.instrument], ["Capacity", c.capacity],
            ["Price", c.price], ["Capex", c.capex], ["Displaces", c.displaced]
          ].filter(function (f) { return f[1]; });
          var head = [c.price, c.capex, c.displaced].filter(Boolean)[0] || c.capacity || "";
          return '<details class="prec"><summary><span class="nm">' + esc(c.name) +
            "</span>" + '<span class="cat">' + esc(head) + "</span></summary>" +
            '<div class="body">' +
            '<div class="sitedetails">' + facts.map(function (f) {
              return '<div class="drow"><span class="dlbl">' + esc(f[0]) +
                "</span><span>" + esc(f[1]) + "</span></div>";
            }).join("") + "</div>" +
            "<p>" + esc(c.summary) + "</p>" +
            (c.microreactor_read
              ? '<p><span class="k">Price to beat \u00b7 </span>' + esc(c.microreactor_read) + "</p>"
              : "") +
            filingList(c.filings) + srcList(c.sources) + "</div></details>";
        }).join("") + "</div></div>";
    }).join(""));
  }

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
  function vendorCardHTML(v) {
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
  }

  var vItems = [{ id: "all", label: "All vendors" }].concat(
    D.vendors.vendors.map(function (v) {
      return { id: slug(v.name), label: v.name };
    })
  );

  render($("vendorcards"),
    '<div class="vgrid" data-sub="all" id="vendors-all" role="tabpanel" tabindex="0">' +
    D.vendors.vendors.map(vendorCardHTML).join("") + "</div>" +
    D.vendors.vendors.map(function (v) {
      var vId = slug(v.name);
      return '<div class="vsolo" data-sub="' + esc(vId) + '" id="vendors-' + esc(vId) +
        '" role="tabpanel" tabindex="0">' + vendorCardHTML(v) + "</div>";
    }).join("")
  );
  makeSubnav("vendors", vItems);

  /* ---------- demand summary & top options ---------- */
  var totalLoads = [].concat.apply([], D.sectors.sectors.map(function (s) { return s.loads; }));
  var citedLoads = totalLoads.filter(function (l) { return l.sources && l.sources.length; });

  render($("dsummary"), [
    { n: String(D.sectors.sectors.length), k: "civilian sectors" },
    { n: String(totalLoads.length), k: "facility load profiles" },
    { n: String(citedLoads.length), k: "cited with primary sources" },
    { n: "$250–$850", k: "/MWh displaced diesel ceiling", accent: true }
  ].map(function (x) {
    return '<div class="dstat"><span class="n' + (x.accent ? " accent" : "") + '">' +
      esc(x.n) + '</span><span class="k">' + esc(x.k) + "</span></div>";
  }).join(""));

  var topOptions = [
    {
      title: "Remote Outposts & Arctic Microgrids",
      band: "1–5 MW",
      incumbent: "Islanded diesel generation ($300–$850/MWh) and seasonal ice-road fuel logistics",
      desc: "Isolated radar stations, military installations, and remote Arctic settlements require 24/7 firm power where fuel delivery is restricted to seasonal barges or ice roads. Microreactors provide multi-year continuous operation with black-start islanding capability.",
      edge: "Satisfies statutory 99.9% energy availability mandates (10 U.S.C. 2920) while cutting volatile fuel haulage risks.",
      sources: [
        { label: "ANS — DAF ANPI selections", url: "https://www.ans.org/news/2026-04-23/article-7972/air-force-selects-three-microreactor-developers-for-anpi/" },
        { label: "CVEA — Alaska MMR study", url: "https://www.cvea.org/assets/documents/pdfs/mmr/CVEA_Alaska_FS-RELEASEv01.pdf" }
      ]
    },
    {
      title: "Off-Grid Mining & Mineral Processing",
      band: "5–20 MW",
      incumbent: "Onsite diesel/HFO generator banks ($200–$450/MWh)",
      desc: "Remote copper, lithium, gold, and pozzolan operations operate continuous crushing, grinding, flotation mills, and employee camps. Building transmission lines across remote terrain often costs upwards of $100M with 5–10 year wait times.",
      edge: "Steady 24/7 flat baseload profile maximizes reactor capacity factor with zero transmission queue delay.",
      sources: [
        { label: "CVEA — Alaska project report", url: "https://www.cvea.org/about/project-reports/potential-micro-modular-nuclear-reactor-project.html" }
      ]
    },
    {
      title: "Behind-the-Meter Edge & Regional Data Centers",
      band: "5–20 MW",
      incumbent: "5–7 year utility interconnection queues and EPA/CARB emergency diesel runtime caps",
      desc: "Regional AI inference hubs and edge colocation facilities require 1–20 MW dedicated power blocks. Utility substation queues delay power delivery for years, while EPA RICE NESHAP rules cap non-emergency diesel dispatch at 100 hours per year.",
      edge: "Dedicated onsite baseload bypasses transmission queues entirely without triggering Tier 4 emergency diesel reclassification.",
      sources: [
        { label: "JLL — Smaller data centers", url: "https://www.jll.com/en-us/insights/why-smaller-data-centers-are-taking-off" },
        { label: "EPA — Emergency engine provisions", url: "https://www.epa.gov/stationary-engines/fact-sheet-specifics-about-provisions-related" },
        { label: "Kirkland & Ellis — EPA guidance", url: "https://www.kirkland.com/publications/kirkland-alert/2025/05/new-epa-guidance-clarifies-when-data-centers-and-other-operators-may-utilize-emergency-backup" }
      ]
    },
    {
      title: "Medical Campuses & Critical Civic Infrastructure",
      band: "2–10 MW",
      incumbent: "Aging campus Combined Heat & Power (CHP) plants and code-mandated diesel banks",
      desc: "Major hospitals and university campuses require simultaneous electricity and process steam for heating, sterilization, and climate control. CMS waiver QSO-23-11-LSC permits microgrids and non-generator sources to satisfy emergency power rules under 42 CFR 482.15.",
      edge: "Delivers continuous power plus 100°C–200°C steam while replacing aging combustion boilers facing tightening air-quality caps.",
      sources: [
        { label: "CMS — Alternate energy guidance", url: "https://essentialhospitals.org/cms-updates-guidance-alternative-energy-sources/" },
        { label: "DOE — Better Buildings CHP", url: "https://betterbuildingssolutioncenter.energy.gov/chp/colleges-universities" }
      ]
    },
    {
      title: "Marine Terminals & Port Cold Ironing",
      band: "5–20 MW",
      incumbent: "Auxiliary shipboard diesel engines running in port non-attainment air basins",
      desc: "Port authorities face strict mandates (such as CARB At-Berth rules) requiring berthed container and cruise vessels to shut down auxiliary diesel engines and plug into shore power (cold ironing). Simultaneous vessel berthing creates massive multi-megawatt load spikes.",
      edge: "Provides dedicated port microgrid power without overloading local municipal utility substations.",
      sources: [
        { label: "CARB — At-Berth regulation", url: "https://ww2.arb.ca.gov/our-work/programs/ocean-going-vessels-berth-regulation" }
      ]
    },
    {
      title: "Spaceport Propellant Liquefaction & Launch Pads",
      band: "5–30 MW",
      incumbent: "Bulk trucked cryogenic propellant haulage with high boil-off losses",
      desc: "High-cadence commercial launch sites require continuous liquefaction and zero-boil-off refrigeration for liquid oxygen, liquid methane, and liquid hydrogen. Launch pads are frequently situated in remote coastal areas fed by long, vulnerable radial transmission lines.",
      edge: "Onsite liquefaction eliminates thousands of hazardous propellant tanker truck runs and provides independent pad power.",
      sources: [
        { label: "Businesswire — Antares ANPI", url: "https://www.businesswire.com/news/home/20260422886007/en/Antares-Selected-for-Proposed-Deployment-of-Nuclear-Microreactor-at-Joint-Base-San-Antonio-Under-Department-of-the-Air-Force-ANPI-Initiative" }
      ]
    }
  ];

  var topGridHTML = '<div class="topgrid">' + topOptions.map(function (o) {
    return '<div class="topcard">' +
      '<div class="thdr"><h4>' + esc(o.title) + '</h4><span class="tband">' + esc(o.band) + "</span></div>" +
      '<div class="tinc"><strong>Displaces:</strong> ' + esc(o.incumbent) + "</div>" +
      '<div class="tdesc">' + esc(o.desc) + " " + cite(o.sources) + "</div>" +
      '<div class="tedge"><strong>Why microreactors win:</strong> ' + esc(o.edge) + "</div>" +
      "</div>";
  }).join("") + "</div>";

  var secItems = [
    { id: "top", label: "Top options" },
    { id: "all", label: "All sectors" }
  ].concat(
    D.sectors.sectors.map(function (sec) {
      return { id: slug(sec.sector), label: sec.sector };
    })
  );

  render($("sectors"),
    '<div data-sub="top" id="demand-top" role="tabpanel" tabindex="0">' +
      topGridHTML + "</div>" +
    '<div class="sall" data-sub="all" id="demand-all" role="tabpanel" tabindex="0">' +
    D.sectors.sectors.map(function (sec) {
      return '<details class="sector"><summary>' +
        "<h3>" + esc(sec.sector) + "</h3>" +
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
    }).join("") + "</div>" +
    D.sectors.sectors.map(function (sec) {
      var sId = slug(sec.sector);
      return '<div class="ssector" data-sub="' + esc(sId) + '" id="demand-' + esc(sId) +
        '" role="tabpanel" tabindex="0">' +
        '<div class="sector solo">' +
        '<div class="sectorhead"><h3>' + esc(sec.sector) + "</h3></div>" +
        (sec.context
          ? '<div class="sectorctx">' + esc(sec.context.today) + cite(sec.context.sources) + "</div>"
          : "") +
        '<div class="loads">' +
        sec.loads.map(function (l) {
          return '<div class="load"><span>' + esc(l.label) +
            (l.note ? '<span class="note">' + esc(l.note) + "</span>" : "") +
            (l.delta_note ? '<span class="delta">' + esc(l.delta_note) + "</span>" : "") +
            '</span><span class="b">' + esc(l.band) + cite(l.sources) + "</span></div>";
        }).join("") + "</div></div></div>";
    }).join("")
  );
  makeSubnav("demand", secItems);

  /* ---------- market design ---------- */
  var M = D.mechanisms;
  if (M && M.proposal) {
    render($("market-intro"), esc(M.intro) +
      ' <span class="proposaltag">this site\'s proposal</span>');
    render($("mechanism"), '<div class="mech">' + M.proposal.cards.map(function (c) {
      return '<div class="mechcard"><h4>' + esc(c.title) + "</h4>" +
        (c.paras || []).map(function (p) { return "<p>" + esc(p) + "</p>"; }).join("") +
        (c.steps && c.steps.length
          ? '<ol class="steps">' + c.steps.map(function (st) { return "<li>" + esc(st) + "</li>"; }).join("") + "</ol>"
          : "") +
        "</div>";
    }).join("") + "</div>");
    var mgroups = M.precedent_groups || [];
    render($("precedents"), mgroups.map(function (g) {
      return '<div class="precgroup" data-sub="' + esc(slug(g.name)) + '" id="market-' +
        esc(slug(g.name)) + '" role="tabpanel" tabindex="0"><p class="prose">Every mechanism ' +
        "here ran in the real world. Each row records how it worked, what happened, and " +
        "whether early or late buyers got the better deal.</p>" +
        '<div class="precgrid">' +
        g.items.map(function (p) {
          return '<details class="prec"><summary><span class="nm">' + esc(p.name) + "</span>" +
            '<span class="cat">' + esc(p.category) + "</span></summary>" +
            '<div class="body">' +
            '<p><span class="k">Mechanism · </span>' + esc(p.mechanism) + "</p>" +
            '<p><span class="k">Outcome · </span>' + esc(p.outcome) + "</p>" +
            (p.early_vs_late ? '<p><span class="k">Early vs late orders · </span>' + esc(p.early_vs_late) + "</p>" : "") +
            (p.relevance ? '<p><span class="k">Read-across · </span>' + esc(p.relevance) + "</p>" : "") +
            srcList(p.sources) + "</div></details>";
        }).join("") + "</div></div>";
    }).join(""));
    makeSubnav("market", [{ id: "proposal", label: "The proposal" }].concat(
      mgroups.map(function (g) { return { id: slug(g.name), label: g.name }; })));
  }

  /* ---------- policy pathways ---------- */
  var P = D.policy;
  if (P) {
    /* Instruments, keyed by the policy group they belong to. The Policy tab answers
       two questions per group: what the rule says (the pathway cards above) and how a
       deal actually gets signed under it (these). */
    var INST = {};
    ((D.instruments && D.instruments.groups) || []).forEach(function (g) {
      INST[g.group] = g.records;
    });

    var instrumentBand = function (groupId) {
      var recs = INST[groupId];
      if (!recs || !recs.length) { return ""; }
      return '<div class="instband"><div class="subhead"><h3>How the deal gets signed</h3></div>' +
        '<p class="prose">' + recs.length + " instruments behind this group. Each names who " +
        "signs what, who has signed one outside nuclear, and what changes when the asset is " +
        "a reactor.</p>" +
        '<div class="precgrid">' + recs.map(function (m) {
          var facts = [
            ["Who signs", m.who_signs], ["Asset owner", m.asset_owner],
            ["Term", m.term], ["How it is priced", m.price_form]
          ].filter(function (f) { return f[1]; });
          return '<details class="prec"><summary><span class="nm">' + esc(m.name) + "</span>" +
            '<span class="cat">' + esc((m.family || "").replace(/-/g, " ")) + "</span></summary>" +
            '<div class="body">' +
            '<div class="sitedetails">' + facts.map(function (f) {
              return '<div class="drow"><span class="dlbl">' + esc(f[0]) + "</span><span>" +
                esc(f[1]) + "</span></div>";
            }).join("") + "</div>" +
            "<p>" + esc(m.what_it_is) + "</p>" +
            ((m.precedents || []).length
              ? '<div class="beat"><span class="k">Happening today, outside nuclear</span>' +
                m.precedents.map(function (pr) {
                  return "<p>" + '<strong>' + esc(pr.name) +
                    (pr.year ? " (" + esc(pr.year) + ")" : "") + "</strong>" +
                    (pr.parties ? " \u2014 " + esc(pr.parties) : "") +
                    (pr.size ? " \u00b7 " + esc(pr.size) : "") +
                    (pr.price ? " \u00b7 " + esc(pr.price) : "") +
                    (pr.note ? " " + esc(pr.note) : "") + "</p>";
                }).join("") + "</div>"
              : "") +
            '<div class="beat"><span class="k">For a reactor, any size</span><p>' +
              esc(m.nuclear_fit) + "</p></div>" +
            (m.microreactor_edge
              ? '<div class="beat edge"><span class="k">What a 1\u201320 MW unit changes</span>' +
                "<p>" + esc(m.microreactor_edge) + "</p></div>"
              : "") +
            ((m.blockers || []).length
              ? '<div class="beat"><span class="k">Blockers</span><ul class="blockers">' +
                m.blockers.map(function (b) { return "<li>" + esc(b) + "</li>"; }).join("") +
                "</ul></div>"
              : "") +
            srcList(m.sources) + "</div></details>";
        }).join("") + "</div></div>";
    };

    render($("pathways"), P.groups.map(function (g) {
      return '<div class="policygroup" data-sub="' + esc(slug(g.name)) + '" id="policy-' +
        esc(slug(g.name)) + '" role="tabpanel" tabindex="0">' +
        '<div class="policygrid">' +
        g.pathways.map(function (pw) {
          var tag = pw.kind === "idea" ? ' <span class="ideatag">idea</span>' : "";
          var srcs = (pw.sources || []).length ? cite(pw.sources)
            : (pw.kind === "idea" ? "" : '<span class="nosrc">no source yet</span>');
          return '<div class="pw"><div class="top"><span class="nm">' + esc(pw.name) + "</span>" +
            '<span class="st">' + esc(pw.status) + "</span>" + tag + "</div>" +
            "<p>" + esc(pw.mechanism) + " " + srcs + "</p></div>";
        }).join("") + "</div>" + instrumentBand(g.id) + "</div>";
    }).join(""));
    makeSubnav("policy", P.groups.map(function (g) {
      return { id: slug(g.name), label: g.name };
    }));
  }

  /* ---------- evidence: source register ---------- */
  var reg = D.sources_index || [];
  render($("evsummary"),
    esc(s.source_count) + " sources, numbered once each. A chip like [12] anywhere on the site " +
    "points at number 12 below. Sources back " + esc(s.cited_rows) + "/" + esc(s.opportunities) +
    " tracker rows and " + esc(s.cited_loads) + "/" + esc(s.load_types) + " facility load profiles. " +
    "A † means the host refused a direct fetch and the page is corroborated through search " +
    "results instead.");
  render($("register"), '<div class="reg">' + reg.map(function (r) {
    var uses = r.uses.slice(0, 3).join(" · ") + (r.uses.length > 3 ? " · +" + (r.uses.length - 3) + " more" : "");
    return '<div class="rrow" id="src-' + r.n + '"><span class="rn">' + r.n + "</span>" +
      '<span><a href="' + esc(r.url) + '" target="_blank" rel="noopener noreferrer"' +
      (r.snippet ? ' title="search-corroborated; page not directly fetched"' : "") + ">" +
      esc(r.label) + (r.snippet ? "†" : "") + '</a><span class="uses">cited by: ' + esc(uses) + '</span></span>' +
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

  makeSubnav("sources", [{ id: "register", label: "Source register" },
                         { id: "coverage", label: "Field coverage" },
                         { id: "gaps", label: "What is missing" }]);

  /* boot: land on the panel the hash names, or the first. scroll:true beats
     the browser's native jump-to-anchor, which otherwise strands a deep link
     mid-page because the section ids double as hash routes. */
  activate(location.hash.slice(1) || PANELS[0], { scroll: true });
})();
