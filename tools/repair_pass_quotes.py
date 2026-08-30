#!/usr/bin/env python3
"""Repair source quotes in a research pass so every one either verifies or is honest.

  python3 tools/repair_pass_quotes.py data/research/<pass-dir>

Run after tools/verify_pass_quotes.py reports SLOPPY spans or after
tools/check_voices_pass.py reports over-length source quotes. Idempotent: a
second run over repaired output reports everything as kept.

For each source marked `fetched` carrying a quote:
  * verifies as-is and is <=25 words -> leave alone
  * verifies but is too long         -> trim to the longest leading span <=25 words
                                        that still verifies
  * does not verify                  -> demote to snippet-only and drop the quote

The third case is the important one. A record whose span cannot be found in the
page it cites must not keep a "fetched" claim; demoting it preserves the finding
while telling the truth about where it came from.
"""
import json, pathlib, re, html, io, sys, urllib.request, urllib.error
UA=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
def norm(s):
    s=html.unescape(s).replace("’","'").replace("‘","'").replace("“",'"').replace("”",'"')
    s=s.replace("–","-").replace("—","-").replace("‑","-")
    return re.sub(r"\s+"," ",s).casefold().strip()
CACHE={}
SEC_UA = "microreactors-research pranava.raparla@gmail.com"
def page(u):
    if u in CACHE: return CACHE[u]
    ua = SEC_UA if "sec.gov" in u else UA
    try:
        raw=urllib.request.urlopen(urllib.request.Request(
            u, headers={"User-Agent": ua, "Accept-Encoding": "gzip, deflate"}), timeout=30).read()
        if raw[:2] == b"\x1f\x8b":
            import gzip; raw = gzip.decompress(raw)
    except Exception:
        CACHE[u]=(None,"unreachable"); return CACHE[u]
    if raw[:4]==b"%PDF":
        try:
            from pypdf import PdfReader
            t=" ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(raw)).pages)
        except Exception: CACHE[u]=(None,"pdf"); return CACHE[u]
    else:
        t=raw.decode("utf-8","replace")
        t=re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>"," ",t,flags=re.S|re.I)
        t=re.sub(r"<[^>]+>"," ",t)
    CACHE[u]=(norm(t),""); return CACHE[u]

d_dir=pathlib.Path(sys.argv[1])
kept=trimmed=demoted=skipped=0
for f in sorted(d_dir.glob("*.json")):
    d=json.loads(f.read_text()); changed=False
    for rec in d.get("leaders",[])+d.get("quotes",[]):
        for s in rec.get("sources",[]):
            if s.get("status")!="fetched" or not s.get("quote"): continue
            txt,err=page(s["url"])
            if txt is None: skipped+=1; continue
            q=s["quote"]
            if norm(q) in txt:
                if len(q.split())<=25: kept+=1; continue
                words=q.split()
                for n in range(25,4,-1):
                    cand=" ".join(words[:n])
                    if norm(cand) in txt:
                        s["quote"]=cand; trimmed+=1; changed=True; break
                else:
                    s["status"]="snippet-only"; s.pop("quote",None); demoted+=1; changed=True
            else:
                s["status"]="snippet-only"; s.pop("quote",None); demoted+=1; changed=True
    if changed:
        f.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
print(f"kept {kept} · trimmed {trimmed} · demoted {demoted} · unreachable {skipped}")
