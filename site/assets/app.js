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
  var PANELS = ["pipeline", "sites", "economics", "vendors", "why", "demand", "market", "policy", "news", "sources"];
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

  /* Lazy datasets. instruments (421 KB) and voices (232 KB) are 46% of the
     bundle and each is read by exactly one panel, so they ship as separate
     files and load when that panel first opens.

     The cache holds the in-flight PROMISE, not a boolean set after the fetch
     resolves. A boolean is not idempotent under concurrency: two callers in the
     same tick both read it as false before either settles, and the payload
     downloads twice. Every caller here gets the same promise. */
  var LAZY = {};
  function loadLazy(name) {
    if (!(D.lazy || []).length || (D.lazy || []).indexOf(name) === -1) {
      return Promise.resolve(D[name]);          // not split; already present
    }
    if (D[name]) { return Promise.resolve(D[name]); }
    if (!LAZY[name]) {
      LAZY[name] = new Promise(function (resolve, reject) {
        var s = document.createElement("script");
        s.src = "data-" + name + ".js";
        s.onload = function () { resolve(D[name]); };
        // Fail loud: a swallowed error here leaves a panel permanently empty
        // with no explanation, which reads as a rendering bug for weeks.
        s.onerror = function () { reject(new Error("could not load data-" + name + ".js")); };
        document.head.appendChild(s);
      });
    }
    return LAZY[name];
  }
  function lazyPanel(name, el, render) {
    var host = $(el);
    if (host && !host.innerHTML) { host.innerHTML = '<p class="prose note">Loading\u2026</p>'; }
    return loadLazy(name).then(render).catch(function (err) {
      if (host) {
        host.innerHTML = '<p class="prose">This section could not load its data. ' +
          esc(String(err.message || err)) + "</p>";
      }
      throw err;
    });
  }

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
    // Panels whose data ships separately render on first open. loadLazy caches the
    // in-flight promise, so a fast double-activate fetches once.
    if (id === "policy" && !policyRendered) {
      lazyPanel("instruments", "pathways", renderPolicy);
    }
    if (id === "sources" && !voicesRendered) {
      lazyPanel("voices", "voices", renderVoices);
    }
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
  // Axis ceiling derived from the bands themselves, rounded up to a clean step.
  // A hard-coded ceiling silently renders any band above it wider than the
  // chart: raising rural Alaska to $1,950/MWh against a literal 850 produced a
  // 1,945px bar inside a 1,280px page.
  var MAX = (function () {
    var top = bands.reduce(function (m, b) { return Math.max(m, b.hi || 0); }, 0);
    return Math.max(850, Math.ceil(top / 250) * 250);
  }());
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
    '<div class="axis"><span>$0</span><span>$' + Math.round(MAX / 2) + "</span><span>$" +
    MAX + "/MWh</span></div>");

  render($("altnotes"), D.costs.displaced_alternatives.filter(function (a) {
    return a.low_mwh == null;
  }).map(function (a) {
    return '<div class="altnote"><span class="k">' + esc(a.alternative) + " · </span>" +
      esc(a.note) + cite(srcsOf(a)) + "</div>";
  }).join(""));

  render($("reading"), esc(D.costs.reading).replace(/\*\*(.+?)\*\*/g, "<strong style=\"color:var(--text-primary)\">$1</strong>"));

  /* Unit economics: what one unit costs to build, what the twentieth costs,
     and whether reactor type changes the answer. Capital cost per kW was
     missing from this site entirely until 2026-08-29 — it carried levelised
     energy cost only, which is the number a buyer argues about but not the
     number they sign for. */
  (function () {
    var C = D.costs;
    if (!C.capex) { return; }
    var money = function (n) { return "$" + Number(n).toLocaleString("en-US"); };
    var band = function (lo, hi, unit) {
      return lo === hi ? money(lo) + unit : money(lo) + "\u2013" + money(hi) + unit;
    };
    render($("capex-q"), esc(C.capex.question));
    render($("capex-note"), esc(C.capex.note));
    render($("capex"), '<div class="unitrows">' + C.capex.rows.map(function (r) {
      return '<div class="unitrow"><span class="unitname">' + esc(r.scenario) + "</span>" +
        '<span class="unitval">' + esc(band(r.low_kwe, r.high_kwe, "/kWe")) + "</span>" +
        '<span class="unitbasis">' + esc(r.basis) + " " + cite(r.sources) + "</span></div>";
    }).join("") + "</div>");
    render($("capex-reading"), esc(C.capex.reading));

    var L = C.learning_curve;
    render($("lc-q"), esc(L.question));
    render($("lc-worked"), "<code>" + esc(L.formula) + "</code><br>" + esc(L.worked));
    render($("lc-classes"), '<div class="unitrows">' + L.classes.map(function (c) {
      return '<div class="unitrow"><span class="unitname">' + esc(c.klass) + "</span>" +
        '<span class="unitval">&times;' + esc(c.multiplier.toFixed(2)) + "</span>" +
        '<span class="unitbasis">' + esc(c.detail) + "</span></div>";
    }).join("") + "</div>");
    render($("lc-floor"), esc(L.floor) + " " + esc(L.rates) + " " +
      esc(L.definitions_warning) + " " + cite(L.sources));

    var A = C.archetypes;
    render($("arch-q"), esc(A.question));
    render($("arch-note"), esc(A.note));
    render($("archetypes"), '<div class="unitrows">' + A.rows.map(function (r) {
      return '<div class="unitrow"><span class="unitname">' + esc(r.archetype) + "</span>" +
        '<span class="unitval">' + esc(money(r.foak_mwh) + "/MWh \u2192 " + money(r.noak_mwh) + "/MWh") +
        "</span>" + '<span class="unitbasis">' + esc(r.analogue) + " " + cite(A.sources) +
        "</span></div>";
    }).join("") + "</div>");
    render($("arch-finding"), esc(A.finding) + " " + esc(A.convergence) + " " + cite(A.sources));
  })();

  makeSubnav("economics", [{ id: "bands", label: "Cost bands" },
                           { id: "unit-economics", label: "Unit economics" },
                           { id: "tax-credit", label: "Tax credit" },
                           { id: "price-to-beat", label: "Price to beat" }]);

  /* ---------- price to beat: signed deals, with the number attached ---------- */
  var B = D.benchmarks;
  if (B && B.sectors) {
    render($("benchsummary"),
      esc(s.benchmarks) + " rows across " + esc(B.sectors.length) + " sectors: what power " +
      "actually costs at places like these, from signed contracts, government awards and rate " +
      "orders. " + esc(s.benchmarks - s.benchmarks_nuclear) + " are the non-nuclear incumbent a " +
      "reactor would have to beat; " + esc(s.benchmarks_nuclear) + " are nuclear projects kept " +
      "for their published cost. " + esc(s.benchmarks_priced) + " give a price or a cost, and " +
      esc(s.benchmarks_filed) + " include the paperwork.");

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
            (c.nuclear ? ' <span class="nuctag">nuclear</span>' : "") + "</span>" +
            '<span class="cat">' + esc(head) + "</span></summary>" +
            '<div class="body">' +
            '<div class="sitedetails">' + facts.map(function (f) {
              return '<div class="drow"><span class="dlbl">' + esc(f[0]) +
                "</span><span>" + esc(f[1]) + "</span></div>";
            }).join("") + "</div>" +
            "<p>" + esc(c.summary) + "</p>" +
            (c.microreactor_read
              ? '<p><span class="k">What a reactor would have to beat \u00b7 </span>' + esc(c.microreactor_read) + "</p>"
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
        { label: "CMS — QSO-23-11-LSC categorical waiver", url: "https://www.cms.gov/files/document/qso-23-11-lsc.pdf" },
        { label: "DOE Better Buildings — CHP technology fact sheet", url: "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/Overview_of_CHP_Technologies.pdf" }
      ]
    },
    {
      title: "Marine Terminals & Port Cold Ironing",
      band: "5–20 MW",
      incumbent: "Auxiliary shipboard diesel engines running in port non-attainment air basins",
      desc: "Port authorities face strict mandates (such as CARB At-Berth rules) requiring berthed container and cruise vessels to shut down auxiliary diesel engines and plug into shore power (cold ironing). Simultaneous vessel berthing creates massive multi-megawatt load spikes.",
      edge: "Provides dedicated port microgrid power without overloading local municipal utility substations.",
      sources: [
        { label: "CARB / CA Dept of Finance — At-Berth regulation impact assessment", url: "https://dof.ca.gov/media/docs/forecasting/economics/major-regulations/major-regulations-table/SRIA_with_Appendices-Proposed_Control_Measure_for_Ocean-Going_Vessels_At_Berth-080119.pdf" }
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

  /* Why microreactors. The 74 instrument notes each answer one question about one
     rule; clustered, they are twelve arguments and seven places the argument
     fails. The counters are not a disclaimer section - six of them come out of
     the notes themselves, and a case that only collects its wins is a brochure. */
  if (D.arguments) {
    var A = D.arguments;
    render($("why-intro"), esc(A._meta.what_this_is));
    render($("why-method"), esc(A._meta.method));
    render($("why-honest"), esc(A._meta.honest_note));
    render($("why-coverage"), esc(A._meta.coverage));
    var noteList = function (rows) {
      return '<div class="body">' + rows.map(function (r) {
        return '<div class="edgerow"><span class="en">' + esc(r.name) + "</span>" +
          '<span class="cat">' + esc(r.group) + "</span></div>";
      }).join("") + "</div>";
    };
    render($("arguments"), A.arguments.map(function (a, i) {
      return '<div class="argrow"><div class="argnum">' + (i + 1) + "</div>" +
        '<div class="argbody"><h3>' + esc(a.name) + "</h3>" +
        '<p class="argclaim">' + esc(a.claim) +
        ' <span class="argbasis">' + esc(a.basis) + "</span></p>" +
        '<p class="prose">' + esc(a.detail) + "</p>" +
        '<details class="prec"><summary><span class="nm">The notes behind it</span>' +
        '<span class="cat">' + a.note_count + "</span></summary>" +
        noteList(a.notes) + "</details></div></div>";
    }).join(""));
    render($("counters"), A.counters.map(function (c) {
      return '<div class="argrow counter"><div class="argnum">\u00d7</div>' +
        '<div class="argbody"><h3>' + esc(c.name) + "</h3>" +
        '<p class="prose">' + esc(c.detail) + "</p>" +
        '<details class="prec"><summary><span class="nm">The notes behind it</span>' +
        '<span class="cat">' + c.notes.length + "</span></summary>" +
        noteList(c.notes) + "</details></div></div>";
    }).join(""));
    render($("whyloads"), topGridHTML);
    makeSubnav("why", [{ id: "arguments", label: "The arguments" },
                       { id: "against", label: "Where it fails" },
                       { id: "loads", label: "The loads" }]);
  }

  var secItems = [
    { id: "top", label: "Top options" },
    { id: "all", label: "All sectors" }
  ].concat(
    D.sectors.sectors.map(function (sec) {
      return { id: slug(sec.sector), label: sec.sector };
    })
  );

  /* Load -> priced real-world case(s), built once from D.benchmarks.sectors[].
     records[].load (case records opt into a load label; most sectors and most
     older-pass cases carry no `load` tag at all, so this is additive — it
     never hides a load that already had nothing). Read by loadRow() below,
     which renders both the "All sectors" and per-sector views: one function so
     a future edit to a load row cannot fix one copy and silently leave the
     other stale (see 2026-08-24 CLAUDE.md note on duplicated render paths). */
  var loadCaseIndex = {};
  ((D.benchmarks && D.benchmarks.sectors) || []).forEach(function (bsec) {
    bsec.records.forEach(function (c) {
      // Same "priced" test as tools/build_data.py's benchmarks_priced stat — a
      // case with only a capacity figure or a filing is real evidence, but
      // calling it "priced" without a price, capex or displaced-cost number
      // overclaims. Six of the ten Compute/"AI and very large cloud data
      // centers" cases are MOUs and fleet agreements with none of the three.
      if (!(c.price || c.capex || c.displaced)) { return; }
      (c.load || []).forEach(function (label) {
        (loadCaseIndex[label] = loadCaseIndex[label] || []).push(c);
      });
    });
  });
  function loadRow(l) {
    var cases = loadCaseIndex[l.label] || [];
    var priced = !cases.length ? "" :
      '<span class="priced"><a href="#economics/price-to-beat">' + cases.length +
      (cases.length === 1 ? " priced example" : " priced examples") + " →</a></span>";
    return '<div class="load"><span>' + esc(l.label) +
      (l.note ? '<span class="note">' + esc(l.note) + "</span>" : "") +
      (l.delta_note ? '<span class="delta">' + esc(l.delta_note) + "</span>" : "") +
      priced +
      '</span><span class="b">' + esc(l.band) + cite(l.sources) + "</span></div>";
  }

  render($("sectors"),
    '<div data-sub="top" id="demand-top" role="tabpanel" tabindex="0">' +
      '<div class="topcross"><p class="prose">The six load shapes these sectors resolve to, and the case for the size, moved to <a href="#why">Why microreactors</a> - they are one argument and were being told in two places. This tab answers what a unit would power; that one answers why it is this size.</p></div>' + "</div>" +
    '<div class="sall" data-sub="all" id="demand-all" role="tabpanel" tabindex="0">' +
    D.sectors.sectors.map(function (sec) {
      return '<details class="sector"><summary>' +
        "<h3>" + esc(sec.sector) + "</h3>" +
        "</summary>" +
        (sec.context
          ? '<div class="sectorctx">' + esc(sec.context.today) + cite(sec.context.sources) + "</div>"
          : "") +
        '<div class="loads">' +
        sec.loads.map(loadRow).join("") + "</div></details>";
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
        sec.loads.map(loadRow).join("") + "</div></div></div>";
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
        esc(slug(g.name)) + '" role="tabpanel" tabindex="0"><p class="prose">Every one of these ' +
        "really happened. Each row covers how it worked and who came out ahead, the buyers " +
        "who moved early or the ones who waited.</p>" +
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
  /* Deferred: the instrument bands on this tab read the 421 KB instruments
     payload, which now ships separately. Rendering the pathway cards first and
     filling the bands in later would show a half-built tab, so the whole panel
     waits on one promise instead. */
  var P = D.policy;
  var policyRendered = false;
  function renderPolicy() {
    if (policyRendered || !P) { return; }
    policyRendered = true;
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
        '<p class="prose">' + recs.length + " ways a deal like this gets done. Each one shows " +
        "who signs, who has already done it without a reactor, and what changes once a " +
        "reactor is involved.</p>" +
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
              ? '<div class="beat"><span class="k">Who is already doing this</span>' +
                m.precedents.map(function (pr) {
                  return "<p>" + '<strong>' + esc(pr.name) +
                    (pr.year ? " (" + esc(pr.year) + ")" : "") + "</strong>" +
                    (pr.parties ? " \u2014 " + esc(pr.parties) : "") +
                    (pr.size ? " \u00b7 " + esc(pr.size) : "") +
                    (pr.price ? " \u00b7 " + esc(pr.price) : "") +
                    (pr.note ? " " + esc(pr.note) : "") + "</p>";
                }).join("") + "</div>"
              : "") +
            '<div class="beat"><span class="k">What changes with a reactor</span><p>' +
              esc(m.nuclear_fit) + "</p></div>" +
            (m.microreactor_edge
              ? '<div class="beat edge"><span class="k">What is different about a small one</span>' +
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

  /* ---------- news ---------- */
  /* Newest first, grouped by month, with the binding/announced split on every
     row. A selection and a signed contract look identical in a headline, which
     is the whole reason this site exists. */
  if (D.news && (D.news.items || []).length) {
    var N = D.news;
    render($("news-intro"), esc(N._meta.what_this_is));
    render($("news-binding"), esc(N._meta.binding_note));
    render($("news-refresh"), esc(N._meta.refresh));
    var months = [], byMonth = {};
    N.items.forEach(function (it) {
      var m = (it.date || "").slice(0, 7);
      if (!byMonth[m]) { byMonth[m] = []; months.push(m); }
      byMonth[m].push(it);
    });
    var MON = ["January","February","March","April","May","June","July","August",
               "September","October","November","December"];
    var pretty = function (m) {
      var p = m.split("-");
      return p.length === 2 ? MON[parseInt(p[1], 10) - 1] + " " + p[0] : m;
    };
    render($("news-filter"),
      '<button class="newschip on" data-cat="">All ' + N.items.length + "</button>" +
      N.categories.map(function (c) {
        return '<button class="newschip" data-cat="' + esc(c.id) + '">' +
          esc(c.id) + " " + c.count + "</button>";
      }).join(""));
    render($("news"), months.map(function (m) {
      return '<div class="newsmonth"><h3>' + esc(pretty(m)) + "</h3>" +
        byMonth[m].map(function (it) {
          return '<div class="newsitem" data-cat="' + esc(it.category || "") + '">' +
            '<div class="nhdr"><span class="ndate">' + esc(it.date) + "</span>" +
            '<span class="ncat">' + esc(it.category || "") + "</span>" +
            '<span class="nbind ' + (it.binding ? "yes" : "no") + '">' +
            (it.binding ? "executed" : "announced") + "</span></div>" +
            "<h4>" + esc(it.headline) + "</h4>" +
            '<p class="prose">' + esc(it.what_happened) + " " + cite(it.sources) + "</p>" +
            '<p class="nwhy">' + esc(it.why_it_matters) + "</p>" +
            (it.binding_note ? '<p class="nbindnote">' + esc(it.binding_note) + "</p>" : "") +
            "</div>";
        }).join("") + "</div>";
    }).join(""));
    $("news-filter").addEventListener("click", function (e) {
      var b = e.target.closest(".newschip");
      if (!b) { return; }
      var cat = b.dataset.cat;
      Array.prototype.forEach.call($("news-filter").querySelectorAll(".newschip"), function (x) {
        x.classList.toggle("on", x === b);
      });
      Array.prototype.forEach.call($("news").querySelectorAll(".newsitem"), function (it) {
        it.hidden = !!cat && it.dataset.cat !== cat;
      });
      Array.prototype.forEach.call($("news").querySelectorAll(".newsmonth"), function (mo) {
        mo.hidden = !mo.querySelector(".newsitem:not([hidden])");
      });
    });
  }

  /* ---------- evidence: source register ---------- */
  var reg = D.sources_index || [];
  render($("evsummary"),
    esc(s.source_count) + " sources. Each gets one number, used everywhere on the site, so [12] " +
    "always means the same thing. They back " + esc(s.cited_rows) + " of " + esc(s.opportunities) +
    " tracker rows and " + esc(s.cited_loads) + " of " + esc(s.load_types) + " load profiles. " +
    "A † means we could not open the page directly and checked it through search instead.");
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

  /* In their words. Grouped by whose interest the speaker has: the companies
     selling, the government buying, and the analysts arguing it does not add
     up. A quote whose page could not be fetched keeps the dagger every other
     snippet-only citation on this site carries. */
  /* Rendered when the Sources panel first opens, because voices ships as a
     separate 232 KB payload. renderVoices is idempotent; loadLazy hands every
     caller the same promise, so opening the tab twice fetches once. */
  var voicesRendered = false;
  function renderVoices() {
    if (voicesRendered || !(D.voices && D.voices.groups)) { return; }
    voicesRendered = true;

    render($("voices-head"), esc("In their words"));
    render($("voices-intro"), esc(D.voices._meta.what_this_is));
    var voiceRow = function (q) {
      return '<figure class="voice">' +
        "<blockquote>" + esc(q.quote) + "</blockquote>" +
        '<figcaption><span class="voicewho">' + esc(q.speaker) + "</span>" +
          '<span class="voicerole">' + esc(q.role) +
          (q.org && q.org !== "-" ? ", " + esc(q.org) : "") + "</span>" +
          (q.date ? '<span class="voicedate">' + esc(q.date) + "</span>" : "") +
          cite(q.sources) + "</figcaption>" +
        '<p class="voicemeans">' + esc(q.what_it_means) + "</p>" +
        "</figure>";
    };
    /* Collapsed by default: at 120 quotes an open list is a wall. The summary
       carries the count and the note, so a reader never opens a group just to
       find out what is in it. */
    render($("voices"), D.voices.groups.map(function (g, i) {
      return "<details class=\"voicegroup\"" + (i === 0 ? " open" : "") + ">" +
        "<summary><span class=\"vgname\">" + esc(g.name) + "</span>" +
        '<span class="vgcount">' + g.voices.length + "</span></summary>" +
        '<p class="prose note">' + esc(g.note) + "</p>" +
        g.voices.map(voiceRow).join("") + "</details>";
    }).join(""));

    /* The roster. Who these people are, so a quote has a person behind it. */
    if (D.voices.leaders && D.voices.leaders.length) {
      var byCo = {};
      D.voices.leaders.forEach(function (l) {
        (byCo[l.company] = byCo[l.company] || []).push(l);
      });
      render($("roster-head"), esc("Who runs these companies"));
      render($("roster-intro"), esc(D.voices._meta.roster_note));
      render($("roster"), Object.keys(byCo).sort().map(function (co) {
        return "<details class=\"voicegroup\"><summary><span class=\"vgname\">" + esc(co) +
          '</span><span class="vgcount">' + byCo[co].length + "</span></summary>" +
          '<div class="unitrows">' + byCo[co].map(function (l) {
            return '<div class="unitrow"><span class="unitname">' + esc(l.name) + "</span>" +
              '<span class="unitval2">' + esc(l.title) + "</span>" +
              '<span class="unitbasis">' + esc(l.background) +
              (l.why_they_matter ? " " + esc(l.why_they_matter) : "") + " " +
              cite(l.sources) + "</span></div>";
          }).join("") + "</div></details>";
      }).join(""));
    }
    }

  makeSubnav("sources", [{ id: "register", label: "Source register" },
                         { id: "coverage", label: "Field coverage" },
                         { id: "gaps", label: "What is missing" },
                         { id: "voices", label: "In their words" },
                         { id: "about", label: "About" }]);

  /* boot: land on the panel the hash names, or the first. scroll:true beats
     the browser's native jump-to-anchor, which otherwise strands a deep link
     mid-page because the section ids double as hash routes. */
  activate(location.hash.slice(1) || PANELS[0], { scroll: true });
})();
