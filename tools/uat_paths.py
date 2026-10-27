"""Interaction-cost UAT: how many taps, swipes and screens of scrolling it takes
a phone reader to reach the answer to each key question, starting from a fresh
load of Home.

    ~/.venvs/microreactors/bin/python tools/uat_paths.py            # 375x812
    ~/.venvs/microreactors/bin/python tools/uat_paths.py --width 768 --height 1024
    ~/.venvs/microreactors/bin/python tools/uat_paths.py --json out.json

A journey is a list of steps. Before every tap the script scrolls the way a
reader would (vertically to bring the control into view, horizontally inside a
scrolling strip) and charges for it:

    tap    one click on a control
    swipe  one horizontal flick inside a scrolling strip (a flick moves ~80% of
           the strip's width)
    scroll screens of vertical travel, summed over the journey

The answer step charges scroll only. A journey whose element never renders
fails loudly instead of reporting zero.
"""
from __future__ import annotations

import argparse
import contextlib
import http.server
import json
import math
import pathlib
import socket
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Key questions a buyer, investor or analyst brings to the site. Each ends on
# the element that answers it. Selectors use ids the app renders; ":first"
# means the first visible match.
JOURNEYS: list[tuple[str, list[tuple[str, str]]]] = [
    ("What is the latest headline?",
     [("see", "#hero-latest a")]),
    ("What happened this week? (lead story)",
     [("see", "#home-lead")]),
    ("What does a microreactor's power cost? (headline)",
     [("see", "#home-glance .glancebox:nth-child(4) .glancecard")]),
    ("What must power beat in rural Alaska? (headline)",
     [("see", "#home-glance .glancebox:nth-child(3) .glancecard")]),
    ("Which buyers have signed something binding?",
     [("tap", "#tab-pipeline"), ("see", "#pipeline-all article.row")]),
    ("Who could buy next? (prospects)",
     [("tap", "#tab-pipeline"), ("tap", "#pipeline-tab-prospects"),
      ("see", "#prospects :is(details,article)")]),
    ("Where are units proposed? (sites)",
     [("tap", "#tab-pipeline"), ("tap", "#pipeline-tab-sites"),
      ("see", "#sites-grid :is(details,article)")]),
    ("Cost per MWh, first unit to nth (chart)",
     [("tap", "#tab-economics"), ("see", "#chart")]),
    ("What price must a reactor beat? (Price to beat)",
     [("tap", "#tab-economics"), ("tap", "#economics-tab-price-to-beat"),
      ("see", "#economics-price-to-beat :is(details,article,table)")]),
    ("Which vendor delivers first?",
     [("tap", "#tab-vendors"), ("see", "#vendors-all table")]),
    ("What is Radiant's status?",
     [("tap", "#tab-vendors"), ("tap", "#vendors-tab-radiant-nuclear"),
      ("see", "#vendors-radiant-nuclear :is(h3,table,details,article)")]),
    ("Could a mine use one?",
     [("tap", "#tab-demand"), ("tap", "#demand-tab-mining"),
      ("see", "#demand-mining :is(details,article,table,h3)")]),
    ("Which utility filings name advanced reactors?",
     [("tap", "#tab-policy"), ("tap", "#policy-tab-utility-filings"),
      ("see", "#policy-utility-filings :is(details,article,table)")]),
    ("Latest news item and its source",
     [("tap", "#tab-news"), ("tap", "#newslist details.newsitem > summary"),
      ("see", "#newslist details.newsitem[open] a[href^='http']")]),
]

MEASURE_JS = """
([sel, headroom]) => {
  const all = [...document.querySelectorAll(sel)];
  const el = all.find(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden');
  if (!el) return null;
  // Horizontal: the nearest ancestor that scrolls sideways.
  let strip = el.parentElement, swipes = 0;
  while (strip && strip !== document.body) {
    const cs = getComputedStyle(strip);
    if ((cs.overflowX === 'auto' || cs.overflowX === 'scroll') && strip.scrollWidth > strip.clientWidth + 2) break;
    strip = strip.parentElement;
  }
  if (strip && strip !== document.body) {
    const s = strip.getBoundingClientRect(), r = el.getBoundingClientRect();
    const over = Math.max(0, r.right - s.right, s.left - r.left);
    if (over > 0) {
      swipes = Math.ceil(over / (0.8 * strip.clientWidth));
      strip.scrollLeft += (r.left - s.left) - (s.width - r.width) / 2;
    }
  }
  // Vertical: travel needed to bring the element's top into the readable band
  // (below the sticky nav, above the bottom edge).
  const nav = document.querySelector('.nav');
  const navH = nav && getComputedStyle(nav).position === 'sticky' ? nav.getBoundingClientRect().height : 0;
  const vh = innerHeight, top = el.getBoundingClientRect().top;
  let travel = 0;
  if (top > vh - headroom) travel = top - (vh - headroom);
  else if (top < navH) travel = navH - top;
  if (travel) scrollBy(0, top > navH ? travel : -travel);
  return {swipes, screens: travel / vh};
}
"""


@contextlib.contextmanager
def serve_site():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):  # noqa: D102
            pass
    handler = lambda *a, **kw: Quiet(*a, directory=str(SITE), **kw)  # noqa: E731
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{port}/index.html"
    finally:
        srv.shutdown()


def run_journey(page, base: str, steps: list[tuple[str, str]]) -> dict:
    page.goto(base + "#home", wait_until="networkidle")
    page.evaluate("scrollTo(0,0)")
    taps = swipes = 0
    screens = 0.0
    for kind, sel in steps:
        # A tapped control only needs to be visible; an answer needs its top
        # well inside the screen so a line or two of it can be read.
        headroom = 60 if kind == "tap" else 200
        page.wait_for_function(
            "s => [...document.querySelectorAll(s)].some(e => e.getClientRects().length)",
            arg=sel, timeout=8000)
        m = page.evaluate(MEASURE_JS, [sel, headroom])
        if m is None:
            raise RuntimeError(f"no visible element for {sel!r}")
        swipes += m["swipes"]
        screens += m["screens"]
        if kind == "tap":
            page.evaluate(
                "s => [...document.querySelectorAll(s)].find(e => e.getClientRects().length).click()", sel)
            taps += 1
            page.wait_for_timeout(250)
    return {"taps": taps, "swipes": swipes, "screens": round(screens, 2),
            "cost": round(taps + swipes + screens, 2)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--width", type=int, default=375)
    ap.add_argument("--height", type=int, default=812)
    ap.add_argument("--json", type=pathlib.Path)
    args = ap.parse_args(argv)
    from playwright.sync_api import sync_playwright

    rows, failed = [], 0
    with serve_site() as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": args.height},
                                has_touch=args.width < 768, is_mobile=args.width < 768)
        page.goto(base, wait_until="networkidle")
        assert page.evaluate("innerWidth") == args.width, "viewport did not apply"
        for q, steps in JOURNEYS:
            try:
                r = run_journey(page, base, steps)
            except Exception as e:  # report and keep going; exit non-zero below
                failed += 1
                r = {"error": str(e).splitlines()[0][:120]}
            rows.append({"question": q, **r})
        browser.close()

    print(f"Interaction cost at {args.width}x{args.height}, from a fresh Home load\n")
    print(f"{'question':52} {'taps':>4} {'swipe':>5} {'scroll':>6} {'cost':>5}")
    for r in rows:
        if "error" in r:
            print(f"{r['question'][:52]:52} FAILED: {r['error']}")
        else:
            print(f"{r['question'][:52]:52} {r['taps']:>4} {r['swipes']:>5} {r['screens']:>6} {r['cost']:>5}")
    ok = [r for r in rows if "error" not in r]
    if ok:
        print(f"\n{len(ok)} journeys · mean cost {sum(r['cost'] for r in ok)/len(ok):.2f}"
              f" · total swipes {sum(r['swipes'] for r in ok)}"
              f" · total screens {sum(r['screens'] for r in ok):.2f}")
    if args.json:
        args.json.write_text(json.dumps({"width": args.width, "height": args.height, "rows": rows}, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
