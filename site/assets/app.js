/* Microreactor Opportunity Map — render window.MR into the page.
   No framework, no build step. Data is inlined by tools/build_data.py. */
(function () {
  "use strict";
  var D = window.MR;
  if (!D) { console.error("data.js did not load"); return; }

  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  var NONE = '<span class="v none">not found</span>';
  var val = function (v) { return v ? '<span class="v">' + esc(v) + "</span>" : NONE; };

  /* ---------- hero stats ---------- */
  var s = D.summary;
  $("built").textContent = s.built;
  var stats = [
    { n: s.opportunities, k: "opportunities mapped" },
    { n: s.cited_rows + "/" + s.opportunities, k: "rows with a source", accent: s.cited_rows === s.opportunities },
    { n: s.vendors, k: "reactor vendors" },
    { n: s.load_types, k: "load types sized" },
    { n: s.filing_pct + "%", k: "have a utility filing", accent: true }
  ];
  $("stats").innerHTML = stats.map(function (x) {
    return '<div class="stat"><span class="n' + (x.accent ? " accent" : "") + '">' +
      esc(x.n) + '</span><span class="k">' + esc(x.k) + "</span></div>";
  }).join("");

  /* ---------- pipeline ---------- */
  var tracks = D.opportunities.tracks;
  var opps = D.opportunities.opportunities;
  var active = "all";

  var chips = [{ id: "all", label: "All", n: opps.length }].concat(
    tracks.map(function (t) { return { id: t.id, label: t.label, n: s.tracks[t.id] }; })
  );
  $("filters").innerHTML = chips.map(function (c) {
    return '<button class="chip" type="button" data-t="' + esc(c.id) + '" aria-pressed="' +
      (c.id === "all") + '">' + esc(c.label) + '<span class="c">' + c.n + "</span></button>";
  }).join("");

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
    var src = (o.sources || []).map(function (x) {
      return '<a href="' + esc(x.url) + '" target="_blank" rel="noopener noreferrer">' +
        esc(x.label) + "</a>";
    }).join("");
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
      "</div>" + gaps +
      '<div class="srcs">' + src + "</div></div></article>";
  }

  function render() {
    var list = active === "all" ? opps : opps.filter(function (o) { return o.track === active; });
    $("rows").innerHTML = list.map(rowHTML).join("");
  }

  $("filters").addEventListener("click", function (e) {
    var b = e.target.closest(".chip");
    if (!b) return;
    active = b.dataset.t;
    Array.prototype.forEach.call(this.querySelectorAll(".chip"), function (c) {
      c.setAttribute("aria-pressed", String(c === b));
    });
    render();
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
  render();

  /* ---------- economics ---------- */
  var bands = [];
  D.costs.microreactor_lcoe.forEach(function (c) {
    bands.push({ lab: c.scenario, lo: c.low_mwh, hi: c.high_mwh, cls: "micro", src: c.source });
  });
  D.costs.displaced_alternatives.forEach(function (a) {
    if (a.low_mwh != null) bands.push({ lab: a.alternative, lo: a.low_mwh, hi: a.high_mwh, cls: "alt", src: a.source });
  });
  var MAX = 650;
  // Round for display: the underlying study reports cents, but a chart label
  // implying two-decimal precision on a forward-looking cost estimate is false
  // precision. Full values stay in data/costs.json.
  var money = function (n) { return "$" + Math.round(n); };
  $("chart").innerHTML = bands.map(function (b) {
    var lo = Math.max(0, b.lo), hi = Math.max(lo + 4, b.hi);
    var left = (lo / MAX) * 100, width = ((hi - lo) / MAX) * 100;
    var txt = Math.round(b.lo) === Math.round(b.hi)
      ? money(b.lo) : money(b.lo) + "–" + Math.round(b.hi);
    // A band narrower than its own label pushes the text outside the bar rather
    // than letting it spill across the edge.
    var narrow = width < 11;
    return '<div class="bar"><div class="lab">' + esc(b.lab) + "</div>" +
      '<div class="track"><div class="span ' + b.cls + (narrow ? " narrow" : "") +
      '" style="left:' + left.toFixed(1) + "%;width:" + Math.max(width, 2.5).toFixed(1) +
      '%"><span class="t">' + esc(txt) + "</span></div></div></div>";
  }).join("") +
    '<div class="axis"><span>$0</span><span>$' + MAX / 2 + "</span><span>$" + MAX + "/MWh</span></div>";
  $("reading").textContent = D.costs.reading;

  /* ---------- vendors ---------- */
  $("vendors").innerHTML = D.vendors.vendors.map(function (v) {
    var specs = [
      ["Output", v.mwe_label], ["Coolant", v.coolant], ["Fuel", v.fuel],
      ["Refuelling", v.refuel_years ? "every " + v.refuel_years + " yr" : null],
      ["ANPI site", v.anpi_site], ["Footprint", v.land_acres ? v.land_acres + " acres" : null],
      ["Mass", v.mass_tonnes ? v.mass_tonnes + " t" : null],
      ["Target", v.first_delivery_target]
    ].filter(function (x) { return x[1]; });
    return '<div class="vcard"><h3>' + esc(v.name) + '</h3><span class="r">' + esc(v.reactor) + "</span>" +
      specs.map(function (x) {
        return '<div class="vspec"><span class="k">' + esc(x[0]) + '</span><span class="v">' +
          esc(x[1]) + "</span></div>";
      }).join("") + "</div>";
  }).join("");

  /* ---------- sectors ---------- */
  $("sectors").innerHTML = D.sectors.sectors.map(function (sec) {
    return '<div class="sector"><h3>' + esc(sec.sector) + "</h3>" +
      sec.loads.map(function (l) {
        return '<div class="load"><span>' + esc(l.label) + '</span><span class="b">' +
          esc(l.band) + "</span></div>";
      }).join("") + "</div>";
  }).join("");

  /* ---------- coverage ---------- */
  $("coverage").innerHTML = D.gaps.field_coverage.map(function (c) {
    var red = c.pct < 50;
    return '<div class="cov"><span class="lab">' + esc(c.field.replace(/_/g, " ")) + "</span>" +
      '<div class="covbar"><div class="covfill" style="width:' + c.pct + "%;background:" +
      (red ? "var(--antares-red)" : "var(--stone-500)") + '"></div></div>' +
      '<span class="p">' + c.have + "/" + c.total + "</span></div>";
  }).join("");

  $("next").innerHTML = D.gaps.next_pass.map(function (n) {
    return '<div class="nextcard"><h4>' + esc(n.target) + "</h4>" +
      '<p class="prose" style="margin-bottom:var(--space-3)">' + esc(n.why) + " " + esc(n.why_search_failed) + "</p>" +
      '<p class="prose"><span class="k" style="color:var(--text-tertiary)">Where to look: </span>' +
      esc(n.where) + "</p></div>";
  }).join("");
})();
