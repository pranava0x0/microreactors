#!/usr/bin/env python3
"""Parse docs/rian-research-chatgpt.md into data/sectors.json.

Two bugs the first (inline, ad-hoc) version of this had, both silent:

  1. Splitting items on every ';' also split *inside* a parenthetical, so
     "fulfillment centers (1-3 MW normally; 2-10 MW with heavy automation)"
     became two fragments and the row was lost. Split only at top level.
  2. `.lstrip("and ")` strips the *character set* {a,n,d,space}, not the prefix
     "and " -- so "dedicated baseload..." lost its leading 'd' and became
     "edicated baseload...". Use an explicit prefix strip.

The item count is asserted against the source so a future edit that drops a row
fails loudly instead of quietly shipping a shorter list.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "rian-research-chatgpt.md"
OUT = ROOT / "data" / "sectors.json"


def split_top_level(text, sep=";"):
    """Split on `sep`, ignoring separators inside parentheses."""
    parts, depth, buf = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def strip_prefix(s, *prefixes):
    for p in prefixes:
        if s.lower().startswith(p):
            return s[len(p):].lstrip()
    return s


# "12-25 MW for a representative site, with larger mines..." ->
#   ("12-25 MW", "for a representative site, with larger mines...")
RANGE = re.compile(r"^([\d.,]+(?:\s*[–-]\s*[\d.,]+)?\+?\s*MW)\b[,]?\s*(.*)$", re.S)


def main():
    src = SRC.read_text()
    blocks = re.findall(r"### \d+\. (.+?)\n\n(.+?)(?=\n\n###|\n\nThese are)", src, re.S)
    if not blocks:
        print("no sector blocks matched", file=sys.stderr)
        return 1

    sectors, total = [], 0
    for name, body in blocks:
        loads = []
        for part in split_top_level(body.strip()):
            part = strip_prefix(part.strip().rstrip("."), "and ")
            m = re.search(r"\(([^()]*MW[^()]*)\)\s*$", part)
            if not m:
                continue
            label = part[: m.start()].strip().rstrip(",")
            band_raw = m.group(1).strip()
            rm = RANGE.match(band_raw)
            band, note = (rm.group(1), rm.group(2).strip()) if rm else (band_raw, "")
            loads.append({
                "label": label[0].upper() + label[1:] if label else label,
                "band": band,
                "note": note,
                "band_full": band_raw,
            })
        sectors.append({"sector": name.strip(), "loads": loads})
        total += len(loads)

    # Guard: every top-level "(... MW ...)" in the source must survive parsing.
    expected = sum(
        len([p for p in split_top_level(b.strip())
             if re.search(r"\([^()]*MW[^()]*\)\s*$", p.strip().rstrip("."))])
        for _, b in blocks
    )
    if total != expected:
        print(f"FAIL: parsed {total} loads but source has {expected}", file=sys.stderr)
        return 1

    OUT.write_text(json.dumps({
        "_meta": {
            "source": "docs/rian-research-chatgpt.md — annual-average electrical demand planning bands",
            "generated_by": "tools/parse_sectors.py",
            "caveat": "Planning bands, not guaranteed averages; final sizing requires at least one year of hourly site-load data.",
        },
        "sectors": sectors,
    }, indent=1))

    print(f"{len(sectors)} sectors, {total} load types (source: {expected}) -> {OUT}")
    for s in sectors:
        print(f"  {len(s['loads']):2}  {s['sector']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
