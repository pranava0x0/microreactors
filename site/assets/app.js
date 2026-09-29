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
  // Defined before any renderer runs: several render at module scope during boot.
  var usd = function (n) { return "$" + Number(n).toLocaleString("en-US"); };
  // A data value used as a class name is cut to [a-z0-9-] first (SECURITY.md:
  // attribute position needs an allowlist, not only escaping).
  var cls = function (v) { return String(v == null ? "" : v).toLowerCase().replace(/[^a-z0-9-]/g, ""); };
  /* A sentence ends at . ! or ? after a lowercase letter, digit or closing
     bracket, before a capital: "U.S. data centers" is not two sentences. */
  var firstSentenceOf = function (t) {
    var m = String(t || "").match(/^.*?[a-z0-9)\]'"%][.!?](?=\s+[A-Z"'(]|\s*$)/);
    return (m ? m[0] : String(t || "")).trim();
  };
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
    // One chip per URL: a record citing the same page twice (two quotes from one
    // release) printed "[10][10]" on the front page.
    var seen = {};
    return sources.filter(function (s) {
      if (seen[s.url]) return false;
      seen[s.url] = true;
      return true;
    }).map(function (s) {
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
  /* Reading order, not build order: deals and sites -> why this machine -> for what
     load -> at what price -> from whom -> rules and deal design -> what just happened ->
     show the work. index.html's tab
     buttons and <section> order must match this list; a test asserts all three. */
  var PANELS = ["home", "pipeline", "why", "demand", "economics", "vendors", "policy", "news", "sources"];
  /* Sub-navigation, registered by makeSubnav() below. Four panels were long
     enough to bury their own sections at 1280px before this split: policy ran
     30,900px and the source register 67,500px, so field coverage and the gap
     register sat ~90 screens below the fold. Routes are "panel/sub", so a
     sub-section is still linkable. */
  var SUBS = {};
  var deferredRoute = "";
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
  /* Same deployment stamp build_meta.py puts on data.js and app.js, so a chunk
     can never pair with a page from another deployment. */
  var VER = D.summary && D.summary.built ? "?v=" + D.summary.built : "";
  function loadLazy(name) {
    if (!(D.lazy || []).length || (D.lazy || []).indexOf(name) === -1) {
      return Promise.resolve(D[name]);          // not split; already present
    }
    if (D[name]) { return Promise.resolve(D[name]); }
    if (!LAZY[name]) {
      LAZY[name] = new Promise(function (resolve, reject) {
        var s = document.createElement("script");
        s.src = "data-" + name + ".js" + VER;
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
    if (id === "sites") { id = "pipeline"; sub = "sites"; }
    if (id === "market") { id = "policy"; sub = "market-design"; }
    // Why > The loads (six hand-typed cards) was retired on 2026-09-26 in favour
    // of the derived Applications overview; keep old links landing somewhere true.
    if (id === "why" && sub === "loads") { id = "demand"; sub = ""; }
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
    if (id === "policy" && !policyRendered && sub) {
      deferredRoute = id + "/" + sub;
    }
    if (id === "policy" && !policyRendered) {
      lazyPanel("instruments", "pathways", renderPolicy);
    }
    /* "#news/<id>" opens that record: the front page's headlines link to the
       story itself rather than to the top of a 47-row list. */
    if (id === "news" && !newsRendered) {
      lazyPanel("news", "newslist", renderNews).then(function () { openNewsItem(sub); });
    } else if (id === "news" && sub) {
      setTimeout(function () { openNewsItem(sub); }, 0);
    }
    var subRes = SUBS[id] ? SUBS[id].show(sub) : "";
    // News has no sub-tabs, but #news/<id> names a record: keep it, so a link
    // followed from a headline can be copied and shared as that record.
    var here = id + (subRes ? "/" + subRes : (id === "news" && sub ? "/" + sub : ""));
    if (location.hash.slice(1) !== here) {
      if (opts.push) location.hash = here;
      else history.replaceState(null, "", "#" + here);
    }
    if (opts.scroll) window.scrollTo(0, 0);
    revealActiveTab();
  }

  /* On a phone the tab strip scrolls sideways. Say so with a fade on whichever
     edge hides tabs, and bring the active tab into view after every switch:
     landing on #sources used to leave its tab 500px off-screen to the right. */
  var navrow = tablist.parentNode;
  function markNavEdges() {
    var max = tablist.scrollWidth - tablist.clientWidth;
    navrow.classList.toggle("more-left", tablist.scrollLeft > 4);
    navrow.classList.toggle("more-right", max > 4 && tablist.scrollLeft < max - 4);
  }
  function revealActiveTab() {
    var on = tablist.querySelector('[aria-selected="true"]');
    if (!on || tablist.scrollWidth <= tablist.clientWidth) { markNavEdges(); return; }
    var box = tablist.getBoundingClientRect(), r = on.getBoundingClientRect();
    tablist.scrollLeft += (r.left + r.width / 2) - (box.left + box.width / 2);
    markNavEdges();
  }
  tablist.addEventListener("scroll", markNavEdges, { passive: true });
  window.addEventListener("resize", markNavEdges);

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
      /* An item may name a payload it cannot draw without. Fetch on first reveal,
         never at boot: makeSubnav ends by calling show(ids[0]) while every panel
         but the landing one is still hidden, and firing there would defeat the
         split. loadLazy caches the in-flight promise, so a double-click fetches
         once and two sub-tabs naming the same payload share one request. */
      var it = items[ids.indexOf(id)];
      if (it && it.lazy && !it.lazy.done && !panel.hidden) {
        it.lazy.done = true;
        lazyPanel(it.lazy.name, it.lazy.el, it.lazy.render);
      }
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
  /* Deployment stats, not site stats: each number is a market event, not a
     count of what this site happens to curate. Every tile links to the tab
     where that number is broken out row-by-row, so the number is never the
     end of the story. "Vendor milestones hit" was dropped: it summed
     unrelated event types (a criticality, a hire, a funding close) into one
     figure that meant nothing on its own - the criticality and binding-deal
     tiles below already surface the two kinds of milestone worth a headline. */
  var stats = [
    { n: s.binding_rows + "/" + s.opportunities, k: "are marked binding", accent: true, href: "#pipeline" },
    { n: s.reactors_critical_2026, k: "DOE pilot-program reactors critical in 2026", accent: true, href: "#pipeline/us-gov" },
    { n: s.units_largest_preorder, k: "units in the largest preorder", href: "#pipeline" },
    { n: s.first_delivery_year, k: "first delivery target", href: "#vendors" },
    { n: s.filing_rows + "/" + s.opportunities, k: "have a citable utility filing", accent: true, href: "#sources/gaps" }
  ];
  render($("stats"), stats.map(function (x) {
    return '<a class="stat" href="' + esc(x.href) + '"><span class="n' + (x.accent ? " accent" : "") + '">' +
      esc(x.n) + '</span><span class="k">' + esc(x.k) + "</span></a>";
  }).join(""));

  /* ---------- pipeline ---------- */
  // Counted, not typed: "Only one group has a named reactor at a named site with
  // a signed deal" was true when written and went stale once the Air Force and
  // Army named vendors for specific bases.
  render($("pipeline-intro"), esc(s.binding_rows) + " of " + esc(s.opportunities) +
    " tracked buyers hold a signed, funded or awarded instrument; the rest are programs, consortia " +
    "or memoranda without one. Open any row for the details.");
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
    /* One row here can be several rows elsewhere - Janus is one line in this
       table and five installations on the Sites tab - and nothing said so. */
    var seeAlso = o.see_also
      ? '<p class="seealso"><a href="' + esc(o.see_also.href) + '">' +
        esc(o.see_also.label) + " \u2192</a></p>"
      : "";
    return '<article class="row" data-t="' + esc(o.track) + '">' +
      '<div class="rowtop" role="button" tabindex="0" aria-expanded="false">' +
        '<div><div class="rowname">' + esc(o.name) + "</div>" +
          '<div class="rowmeta"><span class="owner">' + esc(o.owner) + "</span>" +
          "<span>" + esc(o.sector) + "</span><span>" + esc(o.power_mw || "—") + "</span>" +
          /* opportunities.binding is a broader test than news.binding - it
             counts a named-site selection or a notice of intent, not only a
             signed contract (see _meta.binding_note) - so it must not borrow
             the News tab's "executed/announced" words, which promise more
             than this field does. */
          '<span class="nbind ' + (o.binding ? "yes" : "no") + '">' +
          (o.binding ? "binding" : "not binding") + "</span>" +
          '<span class="rowmore" aria-hidden="true">Details</span></div></div>' +
        '<span class="pill' + (o.track === "us-gov" ? " gov" : "") + '">' +
          esc(trackLabel(o.track)) + "</span>" +
      "</div>" +
      '<div class="detail"><div class="grid2">' +
        fields.map(function (f) {
          return '<div class="field"><span class="k">' + esc(f[0]) + "</span>" + val(f[1]) + "</div>";
        }).join("") +
      "</div>" + seeAlso + gaps + srcList(o.sources) + "</div></article>";
  }

  var pipeItems = [{ id: "all", label: "All deals (" + opps.length + ")" }].concat(
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
  makeSubnav("pipeline", pipeItems.concat([
    { id: "sites", label: "Sites (" + s.sites + ")",
      lazy: { name: "deployment_sites", el: "pipeline-sites", render: renderSites } },
    { id: "prospects", label: "Prospects" + (s.prospects != null ? " (" + s.prospects + ")" : ""),
      lazy: { name: "strategy", el: "prospects", render: renderProspects } }]));

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

  /* ---------- candidate deployment sites ----------
     Lazy since 2026-09-26: only this sub-tab reads the 40 KB payload. */
  var sitesRendered = false;
  function renderSites() {
    if (sitesRendered || !(D.deployment_sites && D.deployment_sites.sites)) { return; }
    sitesRendered = true;
    var sites = D.deployment_sites.sites;
    render($("pipeline-sites"),
      '<div class="subhead"><h3>Sites</h3></div>' +
      '<p class="prose">Named deployments and screening prospects, ordered by remote grids, off-grid mines, then marine terminals. A concept row does not mean its owner plans a reactor.</p>' +
      '<div class="sites-summary" id="sites-summary"></div>' +
      '<div class="sitefilters" id="site-filters"></div>' +
      '<div id="sites-content"></div>');
    // Every tile counted from the rows. "5 load categories" and "0 FERC hits" were
    // typed here and would have gone stale the day a sixth category landed.
    var siteCats = {};
    sites.forEach(function (x) { siteCats[x.category] = true; });
    render($("sites-summary"), [
      { n: String(sites.length), k: "candidate sites tracked" },
      { n: String(Object.keys(siteCats).length), k: "load categories covered" },
      { n: String(sites.filter(function (s) { return s.filings && s.filings.length; }).length), k: "sites with listed filings", accent: true },
      { n: String((D.deployment_sites._meta.negative_findings || []).length), k: "confirmed negative docket searches", accent: true }
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
      /* Collapsed for the same reason the news rows are: sixteen cards rendered
         open ran to 24 screens on a phone, against 7 for the sixteen tracker rows
         next door. The summary keeps the name, the status, the research depth and
         the country, which is everything you triage on. */
      return '<details class="sitecard" id="site-' + esc(s.id) + '">' +
        "<summary>" +
        '<div class="shdr">' +
          "<h3>" + esc(s.name) + "</h3>" +
          '<div class="smeta">' +
            '<span class="sitetag ' + stCls + '">' + esc(s.status) + "</span>" +
            '<span class="sitetag">' + esc(s.depth) + "</span>" +
            '<span class="sitetag">' + esc(s.country) + (s.region ? " &middot; " + esc(s.region) : "") + "</span>" +
          "</div>" +
        "</div>" +
        "</summary>" +
        '<div class="sbody">' +
        '<div class="sitedetails">' +
          '<div class="drow"><span class="dlbl">Category:</span><span>' + esc(s.category) + (s.band ? " &middot; " + esc(s.band) : "") + "</span></div>" +
          '<div class="drow"><span class="dlbl">Owner/Host:</span><span>' + esc(s.owner || "") + "</span></div>" +
          '<div class="drow"><span class="dlbl">Reactor:</span><span>' + esc(s.vendor || "None announced") + (s.power ? " (" + esc(s.power) + ")" : "") + "</span></div>" +
          '<div class="drow"><span class="dlbl">Utility:</span><span>' + esc(s.utility_context || "Behind-the-meter") + "</span></div>" +
        "</div>" +
        '<div class="sitesummary">' + esc(s.summary) + " " + cite(s.sources) + "</div>" +
        filingsHTML +
        gapsHTML +
        "</div></details>";
    };

    var remoteIds = ["cvea-valdez", "eielson-pilot", "fort-wainwright-doyon",
      "guantanamo-bay-base", "iqaluit-qec"];
    var siteGroups = [
      { id: "remote", label: "Remote outposts & microgrids", sites: sites.filter(function (s) {
        return remoteIds.indexOf(s.id) !== -1;
      }) },
      { id: "mining", label: "Off-grid mining & minerals", sites: sites.filter(function (s) {
        return s.category === "Mining";
      }) },
      { id: "marine", label: "Marine terminals", sites: sites.filter(function (s) {
        return s.category === "Transportation" && s.band ===
          "Cargo-port electrical systems combining terminal operations and ship plug-in power";
      }) }
    ];
    var prioritized = siteGroups.reduce(function (all, group) {
      return all.concat(group.sites);
    }, []);
    siteGroups.push({ id: "other", label: "Other sites", sites: sites.filter(function (s) {
      return prioritized.indexOf(s) === -1;
    }) });

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

    var siteKinds = [{ id: "all", label: "All (" + sites.length + ")" }].concat(
      siteGroups.map(function (group) {
        return { id: group.id, label: group.label + " (" + group.sites.length + ")" };
      }), [{ id: "findings-absences", label: "Findings & Absences" }]);
    render($("site-filters"), siteKinds.map(function (k, i) {
      return '<button class="newschip' + (i === 0 ? " on" : "") + '" data-site-filter="' +
        esc(k.id) + '" aria-pressed="' + (i === 0 ? "true" : "false") + '">' + esc(k.label) + "</button>";
    }).join(""));
    render($("sites-content"), '<div id="sites-grid">' +
      siteGroups.map(function (group) {
        return '<section class="sitegroup" data-site-group="' + group.id + '">' +
          '<h4>' + esc(group.label) + '</h4><div class="sitesgrid">' +
          group.sites.map(renderSiteCard).join("") + '</div></section>';
      }).join("") + '</div><div id="site-negative-findings" hidden>' + negHTML + "</div>");
    $("site-filters").addEventListener("click", function (e) {
      var b = e.target.closest("[data-site-filter]");
      if (!b) return;
      var kind = b.dataset.siteFilter;
      Array.prototype.forEach.call($("site-filters").querySelectorAll("[data-site-filter]"), function (x) {
        x.classList.toggle("on", x === b);
        x.setAttribute("aria-pressed", String(x === b));
      });
      Array.prototype.forEach.call($("sites-grid").children, function (group) {
        group.hidden = kind === "findings-absences" || (kind !== "all" && group.dataset.siteGroup !== kind);
      });
      $("site-negative-findings").hidden = kind !== "findings-absences";
    });
  }

  /* ---------- economics ---------- */
  var bands = [];
  D.costs.microreactor_lcoe.forEach(function (c) {
    bands.push({ lab: c.scenario, lo: c.low_mwh, hi: c.high_mwh, cls: "micro",
                 currency: c.currency, dollarYear: c.dollar_year,
                 srcs: srcsOf(c), caveat: c.caveat });
  });
  D.costs.displaced_alternatives.forEach(function (a) {
    if (a.low_mwh != null) bands.push({ lab: a.alternative, lo: a.low_mwh, hi: a.high_mwh, cls: "alt",
                                        currency: a.currency, dollarYear: a.dollar_year,
                                        srcs: srcsOf(a) });
  });
  // A rural-Alaska rate at $1,950/MWh is a real but exceptional diesel case.
  // Plotting it on the same linear axis makes every other band unreadable, so
  // render exceptional cases as cited callouts rather than pretending the
  // shorter bars are meaningfully comparable by eye.
  var chartBands = bands.filter(function (b) { return b.hi <= 800; });
  var outlierBands = bands.filter(function (b) { return b.hi > 800; });
  var MAX = (function () {
    var top = chartBands.reduce(function (m, b) { return Math.max(m, b.hi || 0); }, 0);
    return Math.max(850, Math.ceil(top / 250) * 250);
  }());
  // Round for display: the underlying study reports cents, but a chart label
  // implying two-decimal precision on a forward-looking cost estimate is false
  // precision. Full values stay in data/costs.json.
  var money = function (n) { return "$" + Math.round(n); };
  var bandMoney = function (b, n) {
    return (b.currency === "USD" ? "US$" : "source $") + Math.round(n);
  };
  render($("chart"), chartBands.map(function (b) {
    var lo = Math.max(0, b.lo), hi = Math.max(lo + 4, b.hi);
    var left = (lo / MAX) * 100, width = ((hi - lo) / MAX) * 100;
    var txt = Math.round(b.lo) === Math.round(b.hi)
      ? bandMoney(b, b.lo) + "/MWh"
      : bandMoney(b, b.lo) + "–" + Math.round(b.hi) + "/MWh";
    // A band narrower than its own label pushes the text outside the bar rather
    // than letting it spill across the edge.
    var narrow = width < 11;
    return '<div class="bar"><div class="lab">' + esc(b.lab) + cite(b.srcs) + "</div>" +
      '<div class="track"><div class="span ' + b.cls + (narrow ? " narrow" : "") +
      '" style="left:' + left.toFixed(1) + "%;width:" + Math.max(width, 2.5).toFixed(1) +
      '%"><span class="t">' + esc(txt) + "</span></div></div>" +
      (b.caveat ? '<div class="caveat">' + esc(b.caveat) + "</div>" : "") + "</div>";
  }).join("") +
    '<div class="axis"><span>$0/MWh</span><span>$' + Math.round(MAX / 2) + "/MWh</span><span>$" +
    MAX + "/MWh</span></div>");

  render($("cost-outliers"), outlierBands.map(function (b) {
    return '<div class="costoutlier"><span class="k">Exceptional diesel case</span>' +
      '<span class="nm">' + esc(b.lab) + cite(b.srcs) + '</span>' +
      '<span class="val">' + esc(bandMoney(b, b.lo) + "–" + Math.round(b.hi) + "/MWh") + '</span>' +
      '<span class="note">Shown outside the chart so one extreme rate does not flatten the rest of the comparison.</span></div>';
  }).join(""));

  render($("altnotes"), D.costs.displaced_alternatives.filter(function (a) {
    return a.low_mwh == null;
  }).map(function (a) {
    return '<div class="altnote"><span class="k">' + esc(a.alternative) + " · </span>" +
      esc(a.note) + cite(srcsOf(a)) + "</div>";
  }).join(""));

  render($("reading"), esc(D.costs.reading).replace(/\*\*(.+?)\*\*/g, "<strong style=\"color:var(--text-primary)\">$1</strong>"));

  /* An LCOE is only comparable to another LCOE that assumed the same things, and
     these did not. Stated here rather than buried in each band's basis line,
     because the discrepancy is between the bands, not inside any one of them. */
  if (D.costs.assumptions) {
    var AS = D.costs.assumptions;
    $("assume-q").textContent = AS.question;
    render($("assume-note"), esc(AS.note));
    render($("assume"), AS.rows.map(function (r) {
      return '<div class="unitrow"><span class="unitname">' + esc(r.parameter) + "</span>" +
        '<span class="unitval2">' + esc(r.value) + "</span>" +
        '<span class="unitbasis">' + esc(r.note) + " " + cite(r.sources) + "</span></div>";
    }).join(""));
  }

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

  /* ---------- price to beat: signed deals, with the number attached ----------
     The 89 benchmark rows are the biggest payload on the site and only this
     sub-tab reads them, so they ship separately and arrive when it opens. */
  function renderBenchmarks() {
    var B = D.benchmarks;
    if (!(B && B.sectors)) { return; }
    render($("benchsummary"),
      "Published power costs and construction costs across " + esc(B.sectors.length) + " sectors.");

    /* One collapsed section per sector, its summary carrying the counts: 89 rows
       rendered flat ran to 25 screens on a phone even with each row collapsed. */
    render($("benchmarks"), B.sectors.map(function (sec) {
      var nPriced = sec.records.filter(function (c) { return c.price || c.capex || c.displaced; }).length;
      var nFiled = sec.records.filter(function (c) { return (c.filings || []).length; }).length;
      return '<details class="benchsector"><summary><h4>' + esc(sec.sector) + "</h4>" +
        '<span class="cnt">' + sec.records.length + " cases · " + nPriced + " priced" +
        (nFiled ? " · " + nFiled + " with filings" : "") + "</span></summary>" +
        '<div class="precgrid">' + sec.records.map(function (c) {
          var facts = [
            ["Date", c.signed], ["Approval status", c.approval_status],
            ["Term", c.term_years ? c.term_years + " years" : ""],
            ["Deal type", dealType(c.instrument)], ["Capacity", c.capacity], ["Annual energy", c.annual_energy],
            ["Price", c.price], ["Construction cost", c.capex], ["Displaces", c.displaced]
          ].filter(function (f) { return f[1]; });
          var head = [c.price, c.capex, c.displaced].filter(Boolean)[0] || c.capacity || c.annual_energy || "";
          if (c.price_status === "proposed") { head = "proposed · " + head; }
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
        }).join("") + "</div></details>";
    }).join(""));
  }

  /* ---------- what wins the deal, and who could buy next ----------
     Both read data-strategy.js, which ships separately because two panels draw
     on it and neither needs it for a first screen. loadLazy hands both sub-tabs
     the same promise, so opening Costs then Deals fetches it once. Every figure
     here restates a cited row; the derived tables print their formula. */
  var winRendered = false;
  function renderPriceToWin() {
    var T = D.strategy;
    if (winRendered || !(T && T.ladder)) { return; }
    winRendered = true;
    var usd = function (n) { return "$" + Number(n).toLocaleString("en-US"); };
    var kwe = function (lo, hi) {
      return lo === hi ? usd(lo) + "/kWe" : usd(lo) + "–" + usd(hi) + "/kWe";
    };
    var mwh = function (lo, hi) {
      if (lo == null) { return "no published estimate"; }
      return lo === hi ? usd(lo) + "/MWh" : usd(lo) + "–" + usd(hi) + "/MWh";
    };
    var rungOf = function (id) {
      return T.ladder.rungs.filter(function (x) { return x.id === id; })[0];
    };
    var drows = function (facts) {
      return '<div class="sitedetails">' + facts.filter(function (f) { return f[1]; }).map(function (f) {
        return '<div class="drow"><span class="dlbl">' + esc(f[0]) + "</span><span>" + esc(f[1]) + "</span></div>";
      }).join("") + "</div>";
    };
    var table = function (head, body) {
      return '<div class="tablewrap"><table class="wintable"><thead><tr>' +
        head.map(function (h) { return "<th>" + esc(h) + "</th>"; }).join("") + "</tr></thead><tbody>" +
        body.map(function (cells) {
          return "<tr>" + cells.map(function (c, i) {
            return (i ? "<td>" : '<td class="lbl">') + esc(c) + "</td>";
          }).join("") + "</tr>";
        }).join("") + "</tbody></table></div>";
    };
    var Lr = T.ladder;
    render($("win-q"), esc(Lr.question));
    render($("win-note"), esc(Lr.note) + " " + esc(T._meta.derived_note));
    render($("win-ladder"), '<div class="unitrows">' + Lr.rungs.map(function (r) {
      return '<div class="unitrow"><span class="unitname">' + esc(r.name) +
        '<br><span class="argbasis">' + esc(mwh(r.lcoe_low_mwh, r.lcoe_high_mwh)) + "</span></span>" +
        '<span class="unitval">' + esc(kwe(r.capex_low_kwe, r.capex_high_kwe)) +
        (r.all_in_min_kwe ? '<br><span class="argbasis">over ' + esc(usd(r.all_in_min_kwe)) + "/kWe all-in</span>" : "") + "</span>" +
        '<span class="unitbasis">' + esc(r.scenario) + ". " + (r.capex_basis ? esc(r.capex_basis) + " " : "") +
        (r.all_in_note ? esc(r.all_in_note) + " " : "") + esc(r.lcoe_note) +
        " <strong>Opens:</strong> " + esc(r.opens_note) + " " + cite(r.sources) + "</span></div>";
    }).join("") + "</div>");

    var U = Lr.units;
    render($("win-units-q"), esc(U.question));
    render($("win-units"), '<p class="prose">' + esc(U.note) + " <code>" + esc(U.formula) + "</code> " +
      cite(U.sources) + "</p>" +
      table(["Rung"].concat(U.sizes_mwe.map(function (m) { return m + " MWe"; })),
            U.rows.map(function (row) {
              var r = rungOf(row.rung);
              return [r ? r.name : row.rung].concat(U.sizes_mwe.map(function (m) {
                var v = row.usd_millions[String(m)];
                var cell = v[0] === v[1] ? "$" + v[0] + "M" : "$" + v[0] + "–" + v[1] + "M";
                if (row.all_in_min_usd_millions) { cell += "; over $" + row.all_in_min_usd_millions[String(m)] + "M all-in"; }
                return cell;
              }));
            })));

    var Cv = Lr.conversion;
    render($("win-conv-q"), esc(Cv.question));
    render($("win-conv"), '<p class="prose">' + esc(Cv.note) + " <code>" + esc(Cv.formula) + "</code> " +
      cite(Cv.sources) + "</p>" + '<div class="unitrows">' + Cv.rows.map(function (r) {
        return '<div class="unitrow"><span class="unitname">' + esc(r.life_years + "-year life") + "</span>" +
          '<span class="unitval">' + esc("$" + r.usd_per_mwh_per_1000_kwe + "/MWh per $1,000/kWe") + "</span>" +
          '<span class="unitbasis">' + esc("Capital recovery factor " + r.crf + " at " +
            Math.round(r.real_rate * 100) + "% real, " + Math.round(r.cf * 100) + "% capacity factor.") +
          "</span></div>";
      }).join("") + "</div>");

    var F = T.floor;
    render($("win-floor-q"), esc(F.question));
    render($("win-floor-note"), esc(F.note) + " <code>" + esc(F.formula) + "</code>");
    render($("win-floor"),
      table(["Fixed cost per reactor", "A year"].concat(F.sizes_mwe.map(function (m) { return m + " MWe"; })),
            F.rows.map(function (row) {
              var inp = F.inputs.filter(function (x) { return x.id === row.input; })[0];
              return [inp ? inp.name : row.input, usd(row.usd_per_year)].concat(
                F.sizes_mwe.map(function (m) { return "$" + row.per_mwh[String(m)] + "/MWh"; }));
            })) +
      '<div class="unitrows">' + F.inputs.map(function (inp) {
        return '<div class="unitrow"><span class="unitname">' + esc(inp.name) + "</span>" +
          '<span class="unitval">' + esc(usd(inp.usd_per_year) + "/yr") + "</span>" +
          '<span class="unitbasis">' + esc(inp.basis) + " " + cite(inp.sources) + "</span></div>";
      }).join("") + "</div>" +
      '<p class="prose">' + esc(F.reading) + " " + cite(F.sources) + "</p>");

    render($("win-seg-q"), "Buyer by buyer");
    render($("win-segments"), '<div class="precgrid">' + T.segments.map(function (sg) {
      var rung = rungOf(sg.clears);
      return '<details class="prec"><summary><span class="nm">' + esc(sg.name) + "</span>" +
        '<span class="cat">' + esc(rung ? "clears at " + rung.name : sg.clears) + "</span></summary>" +
        '<div class="body"><p><span class="k">Verdict · </span>' + esc(sg.verdict) + "</p>" +
        drows([["Incumbent", sg.incumbent], ["Price form", sg.price_form], ["Term", sg.term],
               ["Clears at", rung ? rung.name + ", " + kwe(rung.capex_low_kwe, rung.capex_high_kwe) : sg.clears],
               ["Blocker", sg.blocker], ["First deal", sg.first_deal]]) +
        findingsHTML(sg.findings) +
        '<p class="seealso"><a href="#economics/price-to-beat">' + esc(sg.benchmark_ids.length) +
        " priced cases on the Customer cost sub-tab →</a></p>" +
        srcList(sg.sources) + "</div></details>";
    }).join("") + "</div>");
  }

  /* A finding is a research-pass answer to the row's open question, copied in by
     tools/merge_answers.py. An absent one says what was searched, so a blank never
     reads as "nobody looked". Figures print verbatim beside the finding. */
  function findingsHTML(findings) {
    if (!findings || !findings.length) { return ""; }
    return findings.map(function (f) {
      var figs = f.figures ? Object.keys(f.figures).map(function (k) {
        return esc(k.replace(/_/g, " ")) + ": " + esc(f.figures[k]);
      }).join("; ") : "";
      if (f.status === "absent") {
        return '<p class="finding"><span class="k">Searched ' + esc(f.date) + ", not found · </span>" +
          esc(f.finding) + (f.searched ? ' <span class="note">(angles: ' +
          esc(f.searched.join("; ")) + ")</span>" : "") + "</p>";
      }
      // A finding may carry a station table (issue #17): drawn as a small table so
      // the flagged rows can be compared, not read out of a paragraph.
      var sites = (f.sites || []).length
        ? '<div class="tablewrap"><table class="sectortable findingsites"><thead><tr>' +
          "<th scope=\"col\">Station</th><th scope=\"col\">Contractor \u00b7 miner</th>" +
          "<th scope=\"col\">Start \u00b7 term</th><th scope=\"col\">MW (firm thermal)</th>" +
          "<th scope=\"col\">Mine life</th></tr></thead><tbody>" + f.sites.map(function (x) {
            return "<tr" + (x.flag ? ' class="flagged"' : "") + '><th scope="row">' + esc(x.station) +
              (x.flag ? ' <span class="vbadge critical">fits</span>' : "") +
              (x.sources && x.sources.length ? " " + cite(x.sources) : "") + "</th>" +
              "<td>" + esc(x.contractor) + " \u00b7 " + esc(x.miner) + "</td>" +
              "<td>" + esc(x.start) + " \u00b7 " + esc(x.term_years) + " yr</td>" +
              "<td>" + esc(x.capacity_mw) + " (" + esc(x.firm_thermal_mw) + ")</td>" +
              "<td>" + esc(x.mine_life) + "</td></tr>";
          }).join("") + "</tbody></table></div>"
        : "";
      return '<p class="finding"><span class="k">Finding ' + esc(f.date) + " · " + esc(f.status) +
        " · </span>" + esc(f.finding) + (figs && !sites ? ' <span class="note">' + figs + "</span>" : "") +
        " " + cite(f.sources) + "</p>" + sites;
    }).join("");
  }

  var prospectsRendered = false;
  function renderProspects() {
    var T = D.strategy;
    if (prospectsRendered || !(T && T.prospects)) { return; }
    prospectsRendered = true;
    var advs = T._meta.advantage_types, advLabel = {}, advGloss = {};
    advs.forEach(function (a) { advLabel[a.id] = a.label; advGloss[a.id] = a.gloss; });
    var HREF = { benchmark: "#economics/price-to-beat", site: "#pipeline/sites", opportunity: "#pipeline",
                 instrument: "#policy", news: "#news" };
    render($("prospects-intro"), esc(T._meta.what_this_is) + " " + esc(T._meta.method));
    render($("prospects-filter"),
      '<button class="newschip on" data-adv="">All ' + T.prospects.length + "</button>" +
      advs.map(function (a) {
        var n = T.prospects.filter(function (p) { return p.advantage === a.id; }).length;
        return '<button class="newschip" data-adv="' + esc(a.id) + '" title="' + esc(a.gloss) + '">' +
          esc(a.label) + " " + n + "</button>";
      }).join(""));
    render($("prospects"), '<div class="precgrid">' + T.prospects.map(function (p) {
      var facts = [["Load", p.load], ["Documented", p.documented], ["Why 1–20 MW fits", p.fit],
                   ["Sale shape", p.sale_shape], ["First question", p.next_question]];
      var refs = (p.refs || []).map(function (r) {
        var k = Object.keys(r)[0];
        return '<a href="' + esc(HREF[k] || "#") + '">' + esc(k) + " · " + esc(r[k]) + "</a>";
      });
      return '<details class="prec prospect" data-adv="' + esc(p.advantage) + '"><summary>' +
        '<span class="nm">' + esc(p.name) + '</span><span class="cat">' + esc(p.status) + " · " +
        esc(p.sector) + "</span></summary>" +
        '<div class="body"><p><span class="k">' + esc(advLabel[p.advantage] || p.advantage) + " · </span>" +
        esc(advGloss[p.advantage] || "") + " " + esc(p.region) + ".</p>" +
        '<div class="sitedetails">' + facts.map(function (f) {
          return '<div class="drow"><span class="dlbl">' + esc(f[0]) + "</span><span>" + esc(f[1]) + "</span></div>";
        }).join("") + "</div>" + findingsHTML(p.findings) +
        (refs.length ? '<p class="seealso">' + refs.join(" · ") + "</p>" : "") +
        srcList(p.sources) + "</div></details>";
    }).join("") + "</div>");
    $("prospects-filter").addEventListener("click", function (e) {
      var b = e.target.closest(".newschip");
      if (!b) { return; }
      Array.prototype.forEach.call($("prospects-filter").querySelectorAll(".newschip"), function (x) {
        x.classList.toggle("on", x === b);
      });
      var adv = b.dataset.adv;
      Array.prototype.forEach.call($("prospects").querySelectorAll("details.prospect"), function (d) {
        d.hidden = !!adv && d.dataset.adv !== adv;
      });
    });
  }

  makeSubnav("economics", [{ id: "bands", label: "Cost bands" },
                           { id: "unit-economics", label: "Unit economics" },
                           { id: "tax-credit", label: "Tax credit" },
                           { id: "price-to-beat", label: "Customer cost",
                             lazy: { name: "benchmarks", el: "benchmarks", render: renderBenchmarks } },
                           { id: "win", label: "What wins",
                             lazy: { name: "strategy", el: "win-ladder", render: renderPriceToWin } }]);

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
  // Criticality is derived from the milestone the vendor actually logged, never
  // hand-typed here - the 2026-09-09 homepage stat bug (a hand-set "3 critical"
  // that drifted to 5 once Aalo and Oklo went critical) is exactly what a second
  // hand-typed copy of the same fact would repeat.
  //
  // Requires a "unit" field, not just a "critical" substring: Oklo's card is
  // headlined "Aurora Powerhouse", but the vendor's only completed criticality
  // milestone is its unrelated Groves Isotope Test Reactor - a badge reading
  // "Reached criticality" on that card would misreport Aurora as critical, which
  // the vendor's own gaps note explicitly says has no criticality date. Naming
  // the actual unit (only set on real criticality milestones) keeps the badge
  // honest regardless of whether the critical unit is the card's flagship design.
  function criticalityMilestone(v) {
    var ms = v.milestones || [];
    for (var i = 0; i < ms.length; i++) {
      if (ms[i].status === "done" && ms[i].unit) return ms[i];
    }
    return null;
  }
  /* Roadmaps read in date order whatever order the file holds them in. A bare
     year ("2028") sorts to the end of that year; "2026 Q3" to the quarter's start. */
  function milestoneKey(d) {
    var m = String(d || "").match(/^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?(?:\s*Q([1-4]))?/);
    if (!m) { return 99999999; }
    var month = m[2] ? +m[2] : (m[4] ? (+m[4] - 1) * 3 + 1 : 12);
    var day = m[3] ? +m[3] : (m[2] || m[4] ? 1 : 31);
    return +m[1] * 10000 + month * 100 + day;
  }
  function byDate(ms) {
    return ms.slice().sort(function (a, b) { return milestoneKey(a.date) - milestoneKey(b.date); });
  }
  function vendorCardHTML(v) {
    var specs = [
      ["Output", v.mwe_label], ["Coolant", v.coolant], ["Fuel", v.fuel],
      ["Refuelling", v.refuel_years ? "every " + v.refuel_years + " yr" : null],
      ["ANPI site", v.anpi_site], ["Janus site", v.janus_site],
      ["Footprint", v.land_acres ? v.land_acres + " acres" : null],
      ["Mass", v.mass_tonnes ? v.mass_tonnes + " t" : null],
      ["Target", v.first_delivery_target]
    ].filter(function (x) { return x[1]; });
    var crit = criticalityMilestone(v);
    var badges = (v.janus_site ? '<span class="vbadge janus">Janus awardee</span>' : "") +
      (crit ? '<span class="vbadge critical">' + esc(crit.unit) + " critical — " + esc(crit.date) + "</span>" : "");
    var gaps = (v.gaps || []).length
      ? '<div class="gapnote"><strong>Known gaps</strong><ul>' +
        v.gaps.map(function (g) { return "<li>" + esc(g) + "</li>"; }).join("") + "</ul></div>"
      : "";
    var tl = (v.milestones || []).length
      ? '<div class="vtlhead">Roadmap to power</div><div class="vtl">' +
        byDate(v.milestones).map(function (m) {
          return '<div class="ms ' + (m.status === "done" ? "done" : "tgt") + '">' +
            '<span class="d">' + esc(m.date) + '</span><span class="dot" aria-hidden="true"></span>' +
            '<span class="l">' + esc(m.label) + cite(m.source ? [m.source] : []) + "</span></div>";
        }).join("") + "</div>"
      : "";
    return '<div class="vcard"><h3>' + esc(v.name) + '</h3><span class="r">' + esc(v.reactor) + "</span>" +
      (badges ? '<div class="vbadges">' + badges + "</div>" : "") +
      specs.map(function (x) {
        return '<div class="vspec"><span class="k">' + esc(x[0]) + '</span><span class="v">' +
          esc(x[1]) + "</span></div>";
      }).join("") + tl + gaps + srcList(v.sources, "vsrcs") + "</div>";
  }

  var vItems = [{ id: "all", label: "All companies (" + D.vendors.vendors.length + ")" }].concat(
    D.vendors.vendors.map(function (v) {
      return { id: slug(v.name), label: v.name };
    })
  );

  /* All companies: one comparison table, each name opening its full card. Eight
     full cards in a row ran to fourteen phone screens (UAT 2026-09-26); the
     cards themselves live on each company's own sub-tab. */
  var vendorRows = D.vendors.vendors.map(function (v) {
    var crit = criticalityMilestone(v);
    var next = byDate(v.milestones || []).filter(function (m) { return m.status !== "done"; })[0];
    var state = crit ? esc(crit.unit) + " critical " + esc(crit.date)
      : ((v.milestones || []).some(function (m) { return m.status === "done"; }) ? "no criticality yet" : "not yet built");
    return "<tr>" +
      '<th scope="row"><a href="#vendors/' + esc(slug(v.name)) + '">' + esc(v.name) + "</a>" +
        '<span class="vtreactor">' + esc(v.reactor) + "</span></th>" +
      "<td>" + esc(v.mwe_label || "\u2014") + "</td>" +
      "<td>" + esc(v.fuel || "\u2014") + "</td>" +
      "<td>" + (crit ? '<span class="vbadge critical">' + state + "</span>" : esc(state)) +
        (v.janus_site ? ' <span class="vbadge janus">Janus: ' + esc(v.janus_site.split(" (")[0]) + "</span>" : "") + "</td>" +
      "<td>" + (next ? esc(next.date) + " \u00b7 " + esc(next.label) : "\u2014") + "</td>" +
      "<td>" + esc(v.first_delivery_target || "\u2014") + "</td></tr>";
  }).join("");
  render($("vendorcards"),
    '<div data-sub="all" id="vendors-all" role="tabpanel" tabindex="0">' +
    '<div class="tablewrap"><table class="sectortable vendortable"><thead><tr>' +
    '<th scope="col">Company</th><th scope="col">Output</th><th scope="col">Fuel</th>' +
    '<th scope="col">Where it stands</th><th scope="col">Next milestone</th>' +
    '<th scope="col">Delivery target</th></tr></thead><tbody>' + vendorRows +
    "</tbody></table></div></div>" +
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

  var APPS = D.applications || { segments: [], rungs: [] };
  var firstWins = APPS.segments.filter(function (x) { return x.clears === "first-unit"; }).length;
  // All four tiles are counted. The fourth used to be a typed "$250–$850/MWh
  // displaced diesel ceiling" that no row on this tab produced.
  render($("dsummary"), [
    { n: String(D.sectors.sectors.length), k: "civilian sectors" },
    { n: String(totalLoads.length), k: "facility load profiles" },
    { n: String(citedLoads.length), k: "cited with primary sources" },
    { n: firstWins + " of " + APPS.segments.length, k: "buyer types already pay more than a first unit", accent: true }
  ].map(function (x) {
    return '<div class="dstat"><span class="n' + (x.accent ? " accent" : "") + '">' +
      esc(x.n) + '</span><span class="k">' + esc(x.k) + "</span></div>";
  }).join(""));

  /* Why microreactors. The 74 instrument notes each answer one question about one
     rule; clustered, they are the arguments and the counters. Every count on this
     tab is derived: the markup used to hard-code "six" counters against seven in
     the data, and read as correct for as long as nobody counted. */
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
        /* The claim is the answer and stays in view; the argued detail and its
           notes sit one tap away. Rendered open, twelve arguments ran to twelve
           phone screens (UAT 2026-09-26). */
        '<details class="prec"><summary><span class="nm">Why, and the notes behind it</span>' +
        '<span class="cat">' + a.note_count + " notes</span></summary>" +
        '<div class="body"><p class="prose">' + esc(a.detail) + "</p></div>" +
        noteList(a.notes) + "</details></div></div>";
    }).join(""));
    render($("counters"), A.counters.map(function (c) {
      return '<div class="argrow counter"><div class="argnum">\u00d7</div>' +
        '<div class="argbody"><h3>' + esc(c.name) + "</h3>" +
        '<p class="prose">' + esc(firstSentenceOf(c.detail)) + "</p>" +
        '<details class="prec"><summary><span class="nm">The full case, and the notes behind it</span>' +
        '<span class="cat">' + c.notes.length + " notes</span></summary>" +
        (c.detail.slice(firstSentenceOf(c.detail).length).trim()
          ? '<div class="body"><p class="prose">' + esc(c.detail.slice(firstSentenceOf(c.detail).length).trim()) + "</p></div>"
          : "") +
        noteList(c.notes) + "</details></div></div>";
    }).join(""));
    var fromNotes = A.counters.filter(function (c) { return (c.notes || []).length; }).length;
    render($("why-against-intro"),
      fromNotes + " of the " + A.counters.length + " below come out of the notes themselves, " +
      "not from a critic.");
    makeSubnav("why", [{ id: "arguments", label: "The arguments" },
                       { id: "against", label: "Where it fails" }]);
  }

  /* Applications > Regions: remote and cold jurisdictions from the 2026-09-26
     regional passes (data/regions.json, lazy). Each row says what the place pays,
     what it draws, and where its law stands on civil nuclear power. */
  var regionsRendered = false;
  function renderRegions() {
    var R = D.regions;
    if (regionsRendered || !(R && R.regions)) { return; }
    regionsRendered = true;
    var tagOf = {};
    (R._meta.position_tags || []).forEach(function (t) { tagOf[t.id] = t; });
    var tagCount = {};
    R.regions.forEach(function (r) { tagCount[r.position] = (tagCount[r.position] || 0) + 1; });
    /* The legend is on the page, not in a title tooltip: a phone never shows one,
       and "Restricted" (Hawaii's two-thirds vote) reads like "Banned" without it. */
    render($("regions-intro"), esc(R._meta.what_this_is) + '<dl class="taglegend">' +
      (R._meta.position_tags || []).filter(function (t) { return tagCount[t.id]; }).map(function (t) {
        return '<div><dt><span class="postag ' + cls(t.id) + '">' + esc(t.label) + "</span> " +
          tagCount[t.id] + "</dt><dd>" + esc(t.gloss) + "</dd></div>";
      }).join("") + "</dl>");
    render($("regions-filter"), '<button class="newschip on" data-group="" aria-pressed="true">All ' +
      R.regions.length + "</button>" + (R._meta.groups || []).map(function (g) {
        var n = R.regions.filter(function (r) { return r.group === g.id; }).length;
        return n ? '<button class="newschip" data-group="' + esc(g.id) + '" aria-pressed="false">' +
          esc(g.label) + " " + n + "</button>" : "";
      }).join(""));
    render($("regions"), '<div class="precgrid">' + R.regions.map(function (r) {
      var tag = tagOf[r.position] || { label: r.position, gloss: "" };
      var loads = (r.loads || []).filter(function (l) { return l.name; });
      return '<details class="prec region" data-group="' + esc(r.group) + '"><summary>' +
        '<span class="nm">' + esc(r.region) + ' <span class="postag ' + cls(r.position) + '" title="' +
        esc(tag.gloss) + '">' + esc(tag.label) + "</span></span>" +
        '<span class="cat">' + esc(r.price_short || "price not published") + "</span></summary>" +
        '<div class="body">' +
        '<p class="copyline"><span class="k">For a 1\u201320 MW unit \u00b7 </span>' + esc(r.microreactor_read) + "</p>" +
        '<p><span class="k">Power today \u00b7 </span>' + esc(r.power_system) + "</p>" +
        (r.price ? '<p><span class="k">Price \u00b7 </span>' + esc(r.price) + "</p>" : "") +
        (loads.length ? '<div class="sitedetails">' + loads.map(function (l) {
          return '<div class="drow"><span class="dlbl">' + esc(l.name) + "</span><span>" + esc(l.mw || "") +
            (l.note ? ' <span class="note">(' + esc(l.note) + ")</span>" : "") + "</span></div>";
        }).join("") + "</div>" : "") +
        '<p><span class="k">Law and policy \u00b7 </span>' + esc(r.nuclear_position) + "</p>" +
        (r.microreactor_activity ? '<p><span class="k">Reactor activity \u00b7 </span>' + esc(r.microreactor_activity) + "</p>" : "") +
        ((r.blockers || []).length ? '<div class="beat"><span class="k">Blockers</span><ul class="blockers">' +
          r.blockers.map(function (b) { return "<li>" + esc(b) + "</li>"; }).join("") + "</ul></div>" : "") +
        srcList(r.sources) + "</div></details>";
    }).join("") + "</div>");
    $("regions-filter").addEventListener("click", function (e) {
      var b = e.target.closest(".newschip");
      if (!b) { return; }
      Array.prototype.forEach.call($("regions-filter").querySelectorAll(".newschip"), function (x) {
        x.classList.toggle("on", x === b);
        x.setAttribute("aria-pressed", String(x === b));
      });
      var g = b.dataset.group;
      Array.prototype.forEach.call($("regions").querySelectorAll("details.region"), function (d) {
        d.hidden = !!g && d.dataset.group !== g;
      });
    });
  }

  var secItems = D.sectors.sectors.map(function (sec) {
    return { id: slug(sec.sector), label: sec.sector };
  });

  /* Load -> how many priced real-world cases back it. Counted in
     tools/build_data.py, which owns the one definition of "priced", so this tab
     needs no benchmarks payload: it renders the count and a link to the Costs
     tab, never the cases. Read by loadRow() below, which draws both the "All
     sectors" and per-sector views: one function so a future edit to a load row
     cannot fix one copy and silently leave the other stale (see 2026-08-24
     CLAUDE.md note on duplicated render paths). */
  var loadCases = D.load_cases || {};
  function loadRow(l) {
    var n = loadCases[l.label] || 0;
    var priced = !n ? "" :
      '<span class="priced"><a href="#economics/price-to-beat">' + n +
      (n === 1 ? " priced example" : " priced examples") + " →</a></span>";
    return '<div class="load"><span>' + esc(l.label) +
      (l.note ? '<span class="note">' + esc(l.note) + "</span>" : "") +
      (l.delta_note ? '<span class="delta">' + esc(l.delta_note) + "</span>" : "") +
      priced +
      '</span><span class="b">' + esc(l.band) + cite(l.sources) + "</span></div>";
  }

  /* Applications > Overview. The application space in one screen: the eight
     buyer types from strategy.json, grouped by the cost rung at which a 1-20 MW
     unit wins them (build_data.py ships the slice), then one line per sector.
     Replaces eight bare accordion headers that summarised nothing. */
  var bandEnds = function (b) {
    var m = String(b || "").match(/[\d.]+/g) || [];
    var lo = parseFloat(m[0]), hi = m.length > 1 ? parseFloat(m[1]) : lo;
    return isNaN(lo) ? null : [lo, hi];
  };
  var firstSentence = firstSentenceOf;
  var TIER = { "first-unit": "A first unit already wins",
               "mass-produced": "Wins once units are mass-produced",
               "optimized": "Wins only with the optimized design" };
  var paysToday = function (sg) {
    var lo = sg.incumbent_low_mwh, hi = sg.incumbent_high_mwh;
    if (lo != null && hi != null) { return usd(lo) + "\u2013" + usd(hi) + "/MWh"; }
    if (hi != null) { return "up to " + usd(hi) + "/MWh"; }
    return "no published $/MWh";
  };
  function segmentCard(sg) {
    var ev = [sg.benchmarks ? sg.benchmarks + " priced cases" : "",
              sg.prospects ? sg.prospects + " named prospects" : ""].filter(Boolean).join(" \u00b7 ");
    return '<details class="prec segcard"><summary><span class="nm">' + esc(sg.name) + "</span>" +
      '<span class="cat">pays ' + esc(paysToday(sg)) + "</span></summary>" +
      '<div class="body">' +
      '<p><span class="k">Today \u00b7 </span>' + esc(sg.incumbent) + "</p>" +
      '<p><span class="k">Verdict \u00b7 </span>' + esc(sg.verdict) + "</p>" +
      '<p><span class="k">Blocker \u00b7 </span>' + esc(sg.blocker) + "</p>" +
      '<p><span class="k">First deal to chase \u00b7 </span>' + esc(sg.first_deal) + "</p>" +
      '<p class="seealso">' + (ev ? esc(ev) + " \u00b7 " : "") +
      '<a href="#economics/price-to-beat">priced cases \u2192</a> \u00b7 ' +
      '<a href="#pipeline/prospects">prospects \u2192</a> \u00b7 ' +
      '<a href="#economics/win">cost ladder \u2192</a></p>' +
      srcList(sg.sources) + "</div></details>";
  }
  var ladderHTML = APPS.rungs.filter(function (r) {
    return APPS.segments.some(function (x) { return x.clears === r.id; });
  }).map(function (r) {
    var segs = APPS.segments.filter(function (x) { return x.clears === r.id; });
    var price = r.lcoe_low_mwh == null ? "" : (r.lcoe_low_mwh === r.lcoe_high_mwh ? usd(r.lcoe_low_mwh)
      : usd(r.lcoe_low_mwh) + "\u2013" + usd(r.lcoe_high_mwh)) + "/MWh";
    return '<div class="tier"><div class="tierhead"><span class="tiername">' + esc(TIER[r.id] || r.name) +
      "</span>" + '<span class="tierprice">' + esc(price) + "</span>" +
      '<span class="tiernote">' + esc(firstSentence(r.opens_note)) + "</span></div>" +
      '<div class="precgrid">' + segs.map(segmentCard).join("") + "</div></div>";
  }).join("");
  var sectorRows = D.sectors.sectors.map(function (sec) {
    var ends = sec.loads.map(function (l) { return bandEnds(l.band); }).filter(Boolean);
    var lo = Math.min.apply(null, ends.map(function (e) { return e[0]; }));
    var hi = Math.max.apply(null, ends.map(function (e) { return e[1]; }));
    var fits = ends.filter(function (e) { return e[0] <= 20 && e[1] >= 1; }).length;
    return '<tr><th scope="row"><a href="#demand/' + esc(slug(sec.sector)) + '">' + esc(sec.sector) + "</a></th>" +
      '<td class="num">' + sec.loads.length + "</td>" +
      '<td class="num">' + esc((lo === hi ? lo : lo + "\u2013" + hi) + " MW") + "</td>" +
      '<td class="num">' + fits + " of " + ends.length + "</td>" +
      '<td class="today">' + esc(firstSentence(sec.context && sec.context.today)) + "</td></tr>";
  }).join("");
  render($("sectors"),
    '<div class="sall" data-sub="overview" id="demand-overview" role="tabpanel" tabindex="0">' +
      '<p class="prose">' + esc(APPS.segments.length) + " kinds of buyer, grouped by the cost at which a " +
      "1\u201320 MW unit wins them. Open a card for what the buyer pays now, the blocker, and the first " +
      "deal worth chasing.</p>" +
      '<div class="ladder">' + ladderHTML + "</div>" +
      '<div class="subhead gap"><h3>Sector by sector</h3></div>' +
      '<div class="tablewrap"><table class="sectortable apps"><thead><tr><th scope="col">Sector</th>' +
      '<th scope="col" class="num">Loads</th><th scope="col" class="num">Range</th>' +
      '<th scope="col" class="num">Inside 1\u201320 MW</th><th scope="col">How it is powered today</th>' +
      "</tr></thead><tbody>" + sectorRows + "</tbody></table></div>" +
    "</div>" +
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
  makeSubnav("demand", [
    { id: "overview", label: "Overview" },
    { id: "regions", label: "Regions" + (s.regions != null ? " (" + s.regions + ")" : ""),
      lazy: { name: "regions", el: "regions", render: renderRegions } }
  ].concat(secItems));

  /* ---------- market design ----------
     Lazy since 2026-09-26: the 48 precedents made mechanisms the largest eager
     payload (83 KB) for one sub-tab. */
  var marketRendered = false;
  function renderMarketDesign() {
    var M = D.mechanisms;
    if (marketRendered || !(M && M.proposal)) { return; }
    marketRendered = true;
    render($("policy-market-intro"), esc(M.intro) +
      ' <span class="proposaltag">this site\'s proposal</span>');
    render($("policy-mechanism"), '<div class="mech">' + M.proposal.cards.map(function (c) {
      return '<div class="mechcard"><h4>' + esc(c.title) + "</h4>" +
        (c.paras || []).map(function (p) { return "<p>" + esc(p) + "</p>"; }).join("") +
        (c.steps && c.steps.length
          ? '<ol class="steps">' + c.steps.map(function (st) { return "<li>" + esc(st) + "</li>"; }).join("") + "</ol>"
          : "") +
        "</div>";
    }).join("") + "</div>");
    var mgroups = M.precedent_groups || [];
    /* One filter across all four groups, by the kind of arrangement: an advance
       market commitment in vaccines and one in carbon removal sit side by side
       under the same chip. Labels fall back to the enum text, so a new type in
       the data still renders. */
    var TYPE_LABEL = {
      "advance-market-commitment": "Advance commitments", "buyers-club": "Buyers' clubs",
      "assurance-contract": "Threshold contracts", "joint-procurement": "Joint procurement",
      "consortium-ownership": "Co-ownership", "fractional-ownership": "Fractional shares",
      "capacity-subscription": "Subscriptions", "prepayment": "Prepayments",
      "mutual-insurance-pool": "Mutual insurance", "parametric-pool": "Parametric pools",
      "overrun-or-performance-cover": "Overrun cover", "government-backstop": "Public backstops"
    };
    var typeLabel = function (t) { return TYPE_LABEL[t] || String(t || "other").replace(/-/g, " "); };
    var typeCount = {}, allPrec = 0;
    mgroups.forEach(function (g) {
      g.items.forEach(function (p) { typeCount[p.type] = (typeCount[p.type] || 0) + 1; allPrec++; });
    });
    var typeOrder = Object.keys(typeCount).sort(function (a, b) { return typeCount[b] - typeCount[a]; });
    render($("prec-intro"), allPrec + " precedents, in nuclear and far outside it. Most ran; a few, like " +
      "DOE's committed-orderbook framework and the ARC Act, are proposals still on paper. Filter by the " +
      "kind of deal; each row says how it worked, how it turned out, and what a reactor orderbook could copy.");
    render($("prec-filter"), '<button class="newschip on" data-type="" aria-pressed="true">All ' + allPrec +
      "</button>" + typeOrder.map(function (t) {
        return '<button class="newschip" data-type="' + esc(t) + '" aria-pressed="false">' +
          esc(typeLabel(t)) + " " + typeCount[t] + "</button>";
      }).join(""));
    render($("policy-precedents"),
      mgroups.map(function (g) {
        /* Each group is a disclosure, closed until opened or until a filter
           chip picks something inside it: 48 open rows were thirteen phone
           screens. */
        return '<details class="precgroup"><summary><h4 class="precgrouphead">' + esc(g.name) + "</h4>" +
          '<span class="cnt">' + g.items.length + "</span></summary>" +
          '<div class="precgrid">' +
          g.items.map(function (p) {
            return '<details class="prec" data-type="' + esc(p.type || "") + '"><summary><span class="nm">' +
              esc(p.name) + "</span>" +
              '<span class="cat">' + esc(typeLabel(p.type)) + (p.year ? " \u00b7 " + esc(p.year) : "") +
              "</span></summary>" +
              '<div class="body">' +
              (p.category ? '<p><span class="k">Market \u00b7 </span>' + esc(p.category) + "</p>" : "") +
              '<p><span class="k">How it worked \u00b7 </span>' + esc(p.mechanism) + "</p>" +
              (p.size ? '<p><span class="k">Size \u00b7 </span>' + esc(p.size) + "</p>" : "") +
              '<p><span class="k">Outcome \u00b7 </span>' + esc(p.outcome) + "</p>" +
              (p.early_vs_late ? '<p><span class="k">Early vs late orders \u00b7 </span>' + esc(p.early_vs_late) + "</p>" : "") +
              (p.relevance ? '<p class="copyline"><span class="k">What an orderbook could copy \u00b7 </span>' +
                esc(p.relevance) + "</p>" : "") +
              srcList(p.sources) + "</div></details>";
          }).join("") + "</div></details>";
      }).join(""));
    $("prec-filter").addEventListener("click", function (e) {
      var b = e.target.closest(".newschip");
      if (!b) { return; }
      Array.prototype.forEach.call($("prec-filter").querySelectorAll(".newschip"), function (x) {
        x.classList.toggle("on", x === b);
        x.setAttribute("aria-pressed", String(x === b));
      });
      var t = b.dataset.type;
      Array.prototype.forEach.call($("policy-precedents").querySelectorAll("details.prec"), function (d) {
        d.hidden = !!t && d.dataset.type !== t;
      });
      Array.prototype.forEach.call($("policy-precedents").querySelectorAll(".precgroup"), function (g) {
        g.hidden = !g.querySelector("details.prec:not([hidden])");
        // A chosen kind opens every group holding one; "All" closes them again.
        g.open = !!t && !g.hidden;
      });
    });
  }

  /* ---------- utility filings ----------
     Plans, dockets and statutes that name advanced reactors (data/dockets.json,
     lazy). How many name a 1-20 MW reactor is in the intro because it is the
     finding: so far, none. */
  var docketsRendered = false;
  function renderDockets() {
    var K = D.dockets;
    if (docketsRendered || !(K && K.dockets)) { return; }
    docketsRendered = true;
    var TYPE = { IRP: "Resource plans", legislation: "State laws", study: "Studies and inquiries",
                 RFP: "Requests for proposals", rider: "Cost-recovery riders", CPCN: "Certificates",
                 tariff: "Tariffs", "rate-case": "Rate cases", "contract-approval": "Contract approvals",
                 other: "Other" };
    var counts = {};
    K.dockets.forEach(function (d) { counts[d.type] = (counts[d.type] || 0) + 1; });
    render($("dockets-intro"), esc(K._meta.what_this_is));
    render($("dockets-filter"), '<button class="newschip on" data-type="" aria-pressed="true">All ' +
      K.dockets.length + "</button>" + Object.keys(counts).sort(function (a, b) {
        return counts[b] - counts[a];
      }).map(function (t) {
        return '<button class="newschip" data-type="' + esc(t) + '" aria-pressed="false">' +
          esc(TYPE[t] || t) + " " + counts[t] + "</button>";
      }).join(""));
    render($("dockets"), '<div class="precgrid">' + K.dockets.map(function (d) {
      var facts = [["Forum", d.forum], ["Docket", d.docket], ["Filed or decided", d.date],
                   ["Status", d.status], ["Reactor size named", d.size_class]];
      return '<details class="prec docket" data-type="' + esc(d.type) + '"><summary>' +
        '<span class="nm">' + esc(d.utility) + (d.state ? " \u00b7 " + esc(d.state) : "") + "</span>" +
        '<span class="cat">' + esc(TYPE[d.type] || d.type) + " \u00b7 " + esc(d.date) + "</span></summary>" +
        '<div class="body"><p>' + esc(d.what_it_says) + "</p>" +
        '<div class="sitedetails">' + facts.filter(function (f) { return f[1]; }).map(function (f) {
          var v = f[0] === "Docket" && d.url
            ? '<a href="' + esc(d.url) + '" target="_blank" rel="noopener noreferrer">' + esc(f[1]) + "</a>"
            : esc(f[1]);
          return '<div class="drow"><span class="dlbl">' + esc(f[0]) + "</span><span>" + v + "</span></div>";
        }).join("") + "</div>" +
        (d.microreactor_read ? '<p class="copyline"><span class="k">For a 1\u201320 MW unit \u00b7 </span>' +
          esc(d.microreactor_read) + "</p>" : "") +
        srcList(d.sources) + "</div></details>";
    }).join("") + "</div>");
    $("dockets-filter").addEventListener("click", function (e) {
      var b = e.target.closest(".newschip");
      if (!b) { return; }
      Array.prototype.forEach.call($("dockets-filter").querySelectorAll(".newschip"), function (x) {
        x.classList.toggle("on", x === b);
        x.setAttribute("aria-pressed", String(x === b));
      });
      var t = b.dataset.type;
      Array.prototype.forEach.call($("dockets").querySelectorAll("details.docket"), function (dd) {
        dd.hidden = !!t && dd.dataset.type !== t;
      });
    });
  }

  /* ---------- policy pathways ---------- */
  /* Deferred: the instrument bands on this tab read the 421 KB instruments
     payload, which now ships separately. Rendering the pathway cards first and
     filling the bands in later would show a half-built tab, so the whole panel
     waits on one promise instead. */
  var P = D.policy;
  var policyRendered = false;
  var dealType = function (value) {
    var labels = {
      "PPA": "Power purchase agreement",
      "ESPC/UESC": "Energy savings or utility service contract",
      "EaaS": "Energy as a service",
      "BOO": "Build-own-operate",
      "ESA (energy services agreement)": "Energy services agreement",
      "MOU (technical collaboration and commercial discussions)": "Memorandum of understanding",
      "PPA (terms under negotiation as of March 2026)": "Power purchase agreement under negotiation",
      "design-build": "One contractor designs and builds it",
      "design-build with utility supply upgrade and CleanBC support": "One contractor designs and builds it; utility upgrade and British Columbia clean-energy support",
      "owner-built (no PPA)": "Buyer builds and owns it",
      "owner-built, part grant-funded": "Buyer builds and owns it; partly grant-funded",
      "grant-funded": "Government grant",
      "grant-funded demonstration plus third-party-owned generation": "Government-funded demonstration with third-party generation",
      "utility tariff": "Standard utility rate",
      "public procurement / government program": "Public purchase or government program",
      "colocation power agreement": "Power agreement for a colocated facility",
      "lease": "Lease",
      "Early Works Agreement plus Task Order; state decision-in-principle obtained": "Early works agreement and task order",
      "commercial-contract": "Commercial contract",
      "public-procurement": "Public purchase",
      "regulatory-rule": "Rule or regulation",
      "utility-tariff": "Utility rate"
    };
    return labels[value] || value || "";
  };
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
      return '<details class="instband"><summary><h3>Deal structures</h3>' +
        '<span class="cnt">' + recs.length + " examples</span></summary>" +
        '<p class="prose">How each arrangement works without a reactor, and what changes with a reactor.</p>' +
        '<div class="precgrid">' + recs.map(function (m) {
          var facts = [
            ["Who signs", m.who_signs], ["Asset owner", m.asset_owner],
            ["Term", m.term], ["How it is priced", m.price_form]
          ].filter(function (f) { return f[1]; });
          return '<details class="prec"><summary><span class="nm">' + esc(m.name) + "</span>" +
            '<span class="cat">' + esc(dealType(m.family)) + "</span></summary>" +
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
        }).join("") + "</div></details>";
    };

    render($("pathways"), P.groups.map(function (g) {
      return '<div class="policygroup" data-sub="' + esc(slug(g.name)) + '" id="policy-' +
        esc(slug(g.name)) + '" role="tabpanel" tabindex="0">' +
        '<div class="policygrid">' +
        g.pathways.map(function (pw) {
          var tag = pw.kind === "idea" ? ' <span class="ideatag">idea</span>' : "";
          var srcs = (pw.sources || []).length ? cite(pw.sources)
            : (pw.kind === "idea" ? "" : '<span class="nosrc">no source yet</span>');
          /* Name, status and the first sentence stay visible; the rest of the
             mechanism and its sources open on tap. Rendered in full, the diesel
             group's ten rules ran to twelve phone screens (UAT 2026-09-26). */
          var lead = firstSentenceOf(pw.mechanism);
          var rest = String(pw.mechanism || "").slice(lead.length).trim();
          return '<details class="pw"><summary><div class="top"><span class="nm">' + esc(pw.name) + "</span>" +
            '<span class="st">' + esc(pw.status) + "</span>" + tag + "</div>" +
            '<p class="pwlead">' + esc(lead) + "</p></summary>" +
            "<p>" + (rest ? esc(rest) + " " : "") + srcs + "</p></details>";
        }).join("") + "</div>" + instrumentBand(g.id) + "</div>";
    }).join(""));
    makeSubnav("policy", P.groups.map(function (g) {
      return { id: slug(g.name), label: g.name };
    }).concat([{ id: "utility-filings", label: "Utility filings" + (s.dockets != null ? " (" + s.dockets + ")" : ""),
                 lazy: { name: "dockets", el: "dockets", render: renderDockets } },
               { id: "market-design", label: "Deal design",
                 lazy: { name: "mechanisms", el: "policy-precedents", render: renderMarketDesign } }]));
    if (deferredRoute) {
      var readyRoute = deferredRoute;
      deferredRoute = "";
      activate(readyRoute, { scroll: false });
    }
  }

  /* ---------- home and news ---------- */
  /* The front page is a directory of the site and the newest headlines. Every
     figure is derived: tools/build_data.py counts the rows and ships the newest
     headlines (sorted there, since the file is not kept in date order) in the
     eager bundle, so the landing tab draws with no lazy payload and no number
     typed into this file. */
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
                "September", "October", "November", "December"];
  var monthYear = function (iso) {
    var p = String(iso || "").split("-");
    return p.length >= 2 ? MONTHS[parseInt(p[1], 10) - 1] + " " + p[0] : String(iso || "");
  };
  function newsHdr(it) {
    return '<div class="nhdr"><span class="ndate">' + esc(it.date) + '</span>' +
      '<span class="ncat">' + esc(it.category || "") + '</span>' +
      '<span class="nbind ' + (it.binding ? "yes" : "no") + '">' +
      (it.binding ? "executed" : "announced") + "</span></div>";
  }
  function glanceCards() {
    var A = D.applications || { segments: [], rungs: [] };
    var rung = function (id) { return A.rungs.filter(function (r) { return r.id === id; })[0]; };
    var count = function (id) { return A.segments.filter(function (x) { return x.clears === id; }).length; };
    var lcoe = function (r) {
      return r.lcoe_low_mwh === r.lcoe_high_mwh ? usd(r.lcoe_low_mwh)
        : usd(r.lcoe_low_mwh) + "\u2013" + usd(r.lcoe_high_mwh);
    };
    var first = rung("first-unit"), mass = rung("mass-produced"), opt = rung("optimized");
    var apps = first && mass && opt
      ? "At a first unit's " + lcoe(first) + "/MWh, " + count("first-unit") + " of " + A.segments.length +
        " buyer types already pay more. " + count("mass-produced") + " open with mass production (" +
        lcoe(mass) + "), and " + count("optimized") + " need the modeled optimized design (" + lcoe(opt) + ")."
      : s.load_types + " facility load profiles across " + s.sector_count + " sectors.";
    if (s.featured_prices) {
      apps = s.featured_prices.alaska.text + " " + s.featured_prices.greenland.text +
        (s.regions ? " " + s.regions + " remote and cold regions profiled." : "");
    } else if (s.regions) {
      apps += " " + s.regions + " remote and cold regions profiled.";
    }
    var costs = first && opt
      ? "Estimates fall from " + lcoe(first) + "/MWh for a first unit to " + lcoe(opt) +
        " for a modeled optimized design. " + s.benchmarks_priced +
        " cases publish a contract, filing, award or cost figure; " + s.benchmarks_priced_proposed +
        " are proposed, not final."
      : s.benchmarks_priced + " cases publish a contract, filing, award or cost figure.";
    return [
      { href: "#pipeline", tab: "Deals", q: "Who is buying now",
        a: s.binding_rows + " of " + s.opportunities + " tracked buyers hold a binding instrument. " +
           s.sites + " named sites and " + s.prospects + " prospects to watch." },
      { href: "#why", tab: "Why microreactors", q: "What the case rests on",
        a: s.arguments + " arguments for a 1\u201320 MW unit, and " + s.counters + " places where they fail." },
      { href: "#demand/regions", tab: "Applications", q: "What Alaska and Greenland signal", a: apps,
        srcs: s.featured_prices ? [
          { label: "Alaska", sources: s.featured_prices.alaska.sources },
          { label: "Greenland", sources: s.featured_prices.greenland.sources }
        ] : [] },
      { href: "#economics/price-to-beat", tab: "Costs", q: "What the power costs", a: costs },
      { href: "#vendors", tab: "Vendors", q: "Who builds them",
        a: s.vendors + " companies tracked. " + s.reactors_critical_2026 + " reactors in DOE's pilot " +
           "program reached criticality in 2026, and the earliest delivery target is " + s.first_delivery_year + "." },
      { href: "#policy/utility-filings", tab: "Rules & deal design", q: "What unlocks a sale",
        a: s.pathways + " rule changes and " + s.instruments + " ways a deal gets signed, with a " +
           "shared-orderbook proposal checked against " + s.precedents + " precedents." +
           (s.dockets ? " " + s.dockets + " utility filings name advanced reactors; " +
             (s.dockets_micro ? s.dockets_micro + (s.dockets_micro === 1 ? " names" : " name")
               : "none names") + " a 1\u201320 MW reactor." : "") },
      { href: "#news", tab: "News", q: "What happened",
        a: s.news_items + " dated events since " + monthYear(s.news_first) + ". " + s.news_binding +
           " rest on something executed: a contract, a filing or a milestone." },
      { href: "#sources", tab: "Sources", q: "Where each number comes from",
        a: s.source_count + " sources, each numbered once and reused on every tab." }
    ];
  }
  function openNewsItem(id) {
    var el = id && $("n-" + id);
    if (!el) { return; }
    var all = $("news-filter").querySelector('.newschip[data-cat=""]');
    if (el.hidden && all) { all.click(); }
    var month = el.closest("details.newsmonth");
    if (month) { month.open = true; }
    el.open = true;
    el.scrollIntoView({ block: "start" });
  }
  function renderHome() {
    render($("home-glance"), glanceCards().map(function (c) {
      return '<div class="glancebox"><a class="glancecard" href="' + esc(c.href) + '"><span class="gtab">' + esc(c.tab) +
        '</span><span class="gq">' + esc(c.q) + '</span><span class="ga">' + esc(c.a) +
        '</span><span class="go" aria-hidden="true">\u2192</span></a>' +
        (c.srcs && c.srcs.length ? '<div class="glancecite">' + c.srcs.map(function (group) {
          return '<span>' + esc(group.label) + ' ' + cite(group.sources) + '</span>';
        }).join(' <span aria-hidden="true">\u00b7</span> ') + '</div>' : '') + '</div>';
    }).join(""));
    var H = D.headlines || [];
    if (!H.length) { return; }
    var lead = H[0];
    render($("home-lead"), '<article class="leadstory">' + newsHdr(lead) +
      "<h3>" + esc(lead.headline) + "</h3><p>" + esc(lead.what_happened) + " " + cite(lead.sources) +
      '</p><a class="more" href="#news/' + esc(lead.id) + '">Read the news record \u2192</a></article>');
    render($("home-headlist"), H.slice(1, 6).map(function (it) {
      return '<li><a href="#news/' + esc(it.id) + '">' + newsHdr(it) +
        '<span class="hl">' + esc(it.headline) + "</span></a></li>";
    }).join("") + '<li class="more"><a href="#news">All ' + s.news_items + " news records \u2192</a></li>");
  }
  /* Newest first, grouped by month, with the binding/announced split on every
     row. A selection and a signed contract look identical in a headline, which
     is the whole reason this site exists. Deferred: news is its own tab and
     nothing else reads it. */
  var newsRendered = false;
  function renderNews() {
    if (newsRendered || !(D.news && (D.news.items || []).length)) { return; }
    newsRendered = true;
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
    var pretty = monthYear;
    render($("news-filter"),
      '<button class="newschip on" data-cat="">All ' + N.items.length + "</button>" +
      N.categories.map(function (c) {
        return '<button class="newschip" data-cat="' + esc(c.id) + '">' +
          esc(c.id) + " " + c.count + "</button>";
      }).join(""));
    /* Collapsed, like the Policy rows. Rendered flat, 42 items ran to 33 screens on
       a phone while Policy fitted 74 into 12 by collapsing. The summary carries the
       date, the category, whether the instrument binds, and the headline, so nothing
       here has to be opened to be triaged. */
    /* Months are disclosures: the newest two open, older ones one tap away with
       their count in view. 47 rows ran to nine phone screens. */
    render($("newslist"), months.map(function (m, mi) {
      return '<details class="newsmonth"' + (mi < 2 ? " open" : "") + '><summary><h3>' + esc(pretty(m)) +
        '</h3><span class="cnt">' + byMonth[m].length + "</span></summary>" +
        byMonth[m].map(function (it) {
          return '<details class="newsitem" id="n-' + esc(it.id) + '" data-cat="' + esc(it.category || "") + '">' +
            "<summary>" +
            '<span class="nhdr"><span class="ndate">' + esc(it.date) + "</span>" +
            '<span class="ncat">' + esc(it.category || "") + "</span>" +
            '<span class="nbind ' + (it.binding ? "yes" : "no") + '">' +
            (it.binding ? "executed" : "announced") + "</span></span>" +
            "<h4>" + esc(it.headline) + "</h4>" +
            "</summary>" +
            '<div class="nbody">' +
            '<p class="prose">' + esc(it.what_happened) + " " + cite(it.sources) + "</p>" +
            '<p class="nwhy">' + esc(it.why_it_matters) + "</p>" +
            (it.binding_note ? '<p class="nbindnote">' + esc(it.binding_note) + "</p>" : "") +
            "</div></details>";
        }).join("") + "</details>";
    }).join(""));
    $("news-filter").addEventListener("click", function (e) {
      var b = e.target.closest(".newschip");
      if (!b) { return; }
      var cat = b.dataset.cat;
      Array.prototype.forEach.call($("news-filter").querySelectorAll(".newschip"), function (x) {
        x.classList.toggle("on", x === b);
      });
      Array.prototype.forEach.call($("newslist").querySelectorAll(".newsitem"), function (it) {
        it.hidden = !!cat && it.dataset.cat !== cat;
      });
      Array.prototype.forEach.call($("newslist").querySelectorAll(".newsmonth"), function (mo, mi) {
        mo.hidden = !mo.querySelector(".newsitem:not([hidden])");
        // A category filter opens every month that has a match; "All" restores the default.
        mo.open = cat ? !mo.hidden : mi < 2;
      });
    });
  }

  /* ---------- evidence: source register ---------- */
  render($("evsummary"),
    esc(s.source_count) + " sources. Each gets one number, used everywhere on the site, so [12] " +
    "always means the same thing. They back " + esc(s.cited_rows) + " of " + esc(s.opportunities) +
    " tracker rows and " + esc(s.cited_loads) + " of " + esc(s.load_types) + " load profiles. " +
    "A † means we could not open the page directly and checked it through search instead.");
  /* Every row stays in the DOM whether or not it matches: a citation chip links to
     #src-N, and a filter that removed rows would break the deep link the chips exist
     for. The match string is built once here rather than re-derived per keystroke. */
  function renderRegister() {
  var reg = D.sources_index || [];
  var PAGE = 30;
  render($("register"), '<div class="reg paged">' + reg.map(function (r) {
    var uses = r.uses.slice(0, 3).join(" · ") + (r.uses.length > 3 ? " · +" + (r.uses.length - 3) + " more" : "");
    var q = (r.n + " " + r.label + " " + r.host + " " + r.uses.join(" ")).toLowerCase();
    return '<div class="rrow" id="src-' + r.n + '" data-q="' + esc(q) + '"><span class="rn">' + r.n + "</span>" +
      '<span><a href="' + esc(r.url) + '" target="_blank" rel="noopener noreferrer"' +
      (r.snippet ? ' title="search-corroborated; page not directly fetched"' : "") + ">" +
      esc(r.label) + (r.snippet ? "†" : "") + '</a><span class="uses" title="' +
      esc(r.uses.join(" · ")) + '">cited by: ' + esc(uses) + '</span></span>' +
      '<span class="host">' + esc(r.host) + "</span></div>";
  }).join("") + "</div>");
  if (reg.length > PAGE) {
    $("regall").textContent = "Show all " + reg.length + " sources";
    $("regall").hidden = false;
  }

  /* 544 rows is 98 screens on a phone. The filter is the entry point; scrolling is
     the fallback. */
  (function () {
    var box = $("regq"), count = $("regcount");
    if (!box) { return; }
    var rows = null;
    var say = function (n) {
      count.textContent = n === reg.length ? reg.length + " sources"
        : n + " of " + reg.length + " sources";
    };
    /* 588 rows ran to 74 screens on a phone. The first page shows the first 30
       sources in reading order; typing searches every row, and "Show all" or a
       #src-N deep link lifts the page limit. */
    var list = $("register").querySelector(".reg"), more = $("regall");
    /* The page limit lifts while a search is typed and comes back when the box
       is cleared, unless the reader asked for everything ("Show all" or a
       #src-N link). Clearing a search used to leave all 700 rows open. */
    var showAll = false;
    var setPaged = function (paged) {
      list.classList.toggle("paged", paged);
      more.hidden = !paged;
    };
    var unpage = function () { showAll = true; setPaged(false); };
    more.addEventListener("click", unpage);
    if (/^#src-\d+$/.test(location.hash)) { unpage(); }
    say(reg.length);
    box.addEventListener("input", function () {
      if (!rows) { rows = $("register").querySelectorAll(".rrow"); }
      var q = box.value.trim().toLowerCase(), shown = 0;
      setPaged(!q && !showAll);
      Array.prototype.forEach.call(rows, function (row) {
        var on = !q || row.dataset.q.indexOf(q) !== -1;
        row.hidden = !on;
        if (on) { shown++; }
      });
      say(shown);
    });
    /* A chip lands on #src-N; if a filter is up, that row may be hidden. */
    window.addEventListener("hashchange", function () {
      if (/^#src-\d+$/.test(location.hash)) { unpage(); }
      if (/^#src-\d+$/.test(location.hash) && box.value) {
        box.value = ""; box.dispatchEvent(new Event("input"));
        var t = document.getElementById(location.hash.slice(1));
        if (t) { t.scrollIntoView(); }
      }
    });
  })();
  }

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
    render($("voices"), D.voices.groups.map(function (g) {
      return "<details class=\"voicegroup\">" +
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

  makeSubnav("sources", [{ id: "register", label: "Source register",
                           lazy: { name: "sources_index", el: "register", render: renderRegister } },
                         { id: "coverage", label: "Field coverage" },
                         { id: "gaps", label: "What is missing" },
                         { id: "voices", label: "In their words",
                           lazy: { name: "voices", el: "voices", render: renderVoices } },
                         { id: "about", label: "About" }]);

  /* boot: land on the panel the hash names, or the first. scroll:true beats
     the browser's native jump-to-anchor, which otherwise strands a deep link
     mid-page because the section ids double as hash routes. */
  renderHome();
  activate(location.hash.slice(1) || PANELS[0], { scroll: true });
})();
