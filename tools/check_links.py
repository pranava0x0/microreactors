#!/usr/bin/env python3
"""Source-URL liveness sweep over every citation in the dataset.

Classification (per AGENTS.md): dead (404/410/DNS/refused) is actionable and
fails the run; blocked (403/429/timeout with a bot-wall) means the page exists
and is kept; live is a 200-family response. Network-dependent, so this runs
locally and on demand, never in CI.

  python3 tools/check_links.py            # sweep everything
  python3 tools/check_links.py --limit 20 # first N (smoke)
"""
import argparse
import concurrent.futures
import json
import pathlib
import socket
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_data import FILES, collect_sources  # noqa: E402  (single source of truth)

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


# Sentinels below the HTTP range: a host that no longer resolves or refuses
# connections is DEAD (the citation target is gone); a timeout or TLS failure
# means the host exists but will not talk to a script, which is BLOCKED.
DNS_DEAD = -1
REFUSED = -2


def status_of(url: str, timeout: float) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, socket.gaierror):
            return DNS_DEAD
        if isinstance(reason, ConnectionRefusedError):
            return REFUSED
        return 0  # timeout / TLS / reset: host exists, treat as blocked
    except socket.gaierror:
        return DNS_DEAD
    except ConnectionRefusedError:
        return REFUSED
    except Exception:
        return 0


def collect_urls() -> list:
    """Every distinct cited URL across the data files. collect_sources yields
    (label, url, context, status) for labeled source dicts; deployment_sites
    (not in build_data.FILES — the site does not render it yet) is swept with
    a plain URL walker so its filings[] entries, which carry a url but no
    label, are covered too."""
    found: list = []
    for name in FILES:
        p = ROOT / "data" / f"{name}.json"
        if p.exists():
            collect_sources(json.loads(p.read_text()), name, found)
    urls = {u for _, u, _, _ in found}

    def walk(node) -> None:
        if isinstance(node, dict):
            u = node.get("url")
            if isinstance(u, str) and u.startswith("http"):
                urls.add(u)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    sites_p = ROOT / "data" / "deployment_sites.json"
    if sites_p.exists():
        walk(json.loads(sites_p.read_text()))
    return sorted(urls)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--timeout", type=float, default=15.0)
    args = ap.parse_args()
    if args.limit is not None and args.limit <= 0:
        print("--limit must be a positive integer", file=sys.stderr)
        return 2

    urls = collect_urls()
    if not urls:
        print("no URLs found — that is a failure, not a clean sweep", file=sys.stderr)
        return 1
    if args.limit:
        urls = urls[:args.limit]

    dead, blocked, live = [], [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for url, code in zip(urls, ex.map(lambda u: status_of(u, args.timeout), urls)):
            if code in (404, 410, DNS_DEAD, REFUSED):
                dead.append((code, url))
            elif code == 0 or code in (403, 429) or code >= 500:
                blocked.append((code, url))
            else:
                live.append((code, url))

    print(f"live {len(live)} · blocked {len(blocked)} · dead {len(dead)}  (of {len(urls)} checked)")
    for code, url in dead:
        print(f"DEAD {code} {url}")
    for code, url in blocked:
        print(f"blocked {code} {url}")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
