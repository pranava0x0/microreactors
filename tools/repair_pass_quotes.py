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

It also repairs the DISPLAYED quote, which is the text the site renders inside
quotation marks and therefore the string that actually has to be verbatim. Where
a record's quote is not present whole in any source it cites, it is trimmed to
its longest verbatim prefix; where that prefix is too short to carry meaning, the
record is reported for a human rather than silently shortened.

The displayed quote and the source's evidence span are different strings, and an
earlier version of the gate checked only the second. Of 107 records, 16 displayed
exactly what had been verified and 10 were disjoint from it entirely.

  python3 tools/repair_pass_quotes.py data/research/<pass-dir>

Idempotent: a second run over repaired output reports everything as kept.
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

MIN_WORDS = 6   # below this a "quote" is a fragment, not a quotation
d_dir=pathlib.Path(sys.argv[1])
kept=trimmed=demoted=skipped=0
q_kept=q_trimmed=q_flagged=0
flagged=[]
for f in sorted(d_dir.glob("*.json")):
    d=json.loads(f.read_text()); changed=False
    for rec in d.get("quotes",[]):
        rq = rec.get("quote","")
        srcs=[s for s in rec.get("sources",[]) if s.get("status")=="fetched" and s.get("url")]
        texts=[page(s["url"])[0] for s in srcs]
        texts=[x for x in texts if x]
        if not rq or not texts:
            continue
        if any(norm(rq) in x for x in texts):
            q_kept+=1; continue
        w=rq.split(); best=0
        for n in range(len(w)-1, MIN_WORDS-1, -1):
            if any(norm(" ".join(w[:n])) in x for x in texts):
                best=n; break
        if best:
            rec["quote"]=" ".join(w[:best]).rstrip(" ,;:-")
            q_trimmed+=1; changed=True
        else:
            q_flagged+=1
            flagged.append(f"{f.name}:{rec.get('id')}  only <{MIN_WORDS}w verbatim: {rq[:70]}")
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
print(f"source spans: kept {kept} · trimmed {trimmed} · demoted {demoted} · unreachable {skipped}")
print(f"displayed quotes: kept {q_kept} · trimmed to verbatim extent {q_trimmed} · "
      f"flagged for a human {q_flagged}")
for m in flagged:
    print(f"  FLAG  {m}")
