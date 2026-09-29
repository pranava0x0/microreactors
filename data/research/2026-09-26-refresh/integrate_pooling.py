#!/usr/bin/env python3
"""Fold the 2026-09-26 pooling pass into data/mechanisms.json (one-off, re-runnable).

What it does, all idempotent:
  1. tags every existing precedent with a `type` from the pass's mechanism enum;
  2. adds (or replaces) the group "Pooled buying and shared risk in other markets"
     built from pooling.json, with display prose edited to house style (no em
     dashes) and one short `relevance` line per row written for the page;
  3. adds (or replaces) the proposal card "What other markets add to the design".

Facts, numbers and sources come from pooling.json unchanged; only the wording of
the display fields is edited here, so a reviewer can diff the two.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
PASS = ROOT / "data" / "research" / "2026-09-26-refresh" / "pooling.json"
MECH = ROOT / "data" / "mechanisms.json"
GROUP = "Pooled buying and shared risk in other markets"
CARD = "What other markets add to the design"

# Existing precedents, by name, to the pass's mechanism enum.
EXISTING_TYPES = {
    "DOE Pathways to Commercial Liftoff — committed orderbook framework": "buyers-club",
    "EFI Foundation Cost Stabilization Facility": "overrun-or-performance-cover",
    "Nuclear Innovation Alliance — Catalyzing Commitments (June 2024)": "buyers-club",
    "UAMPS Carbon Free Power Project (NuScale)": "capacity-subscription",
    "DOE $900M Gen III+ SMR solicitation": "government-backstop",
    "Google–Kairos Power master agreement": "prepayment",
    "Equinix–Radiant 20-unit preorder": "prepayment",
    "DOE Advanced Reactor Demonstration Program": "government-backstop",
    "GAVI pneumococcal Advance Market Commitment": "advance-market-commitment",
    "Frontier climate advance market commitment": "advance-market-commitment",
    "First Movers Coalition": "buyers-club",
    "Boeing 787 launch-customer economics": "prepayment",
    "Operation Warp Speed advance purchases": "advance-market-commitment",
    "DOE SunShot Initiative": "government-backstop",
    "NYSERDA offshore wind solicitations": "joint-procurement",
    "Sematech": "consortium-ownership",
    "NEIL — Nuclear Electric Insurance Limited": "mutual-insurance-pool",
    "Price-Anderson Act": "government-backstop",
    "UK Regulated Asset Base model (Sizewell C)": "government-backstop",
    "Vogtle 3 & 4 and the Westinghouse fixed-price collapse": "overrun-or-performance-cover",
    "Coastal Virginia Offshore Wind tiered overrun schedule": "overrun-or-performance-cover",
    "ARC Act (introduced 2026)": "government-backstop",
    "Marsh insurance placement for TerraPower Kemmerer": "overrun-or-performance-cover",
    "Price-Anderson sub-100 MWe tier structure and retrospective pool exemption": "mutual-insurance-pool",
}

# House style: no em dashes in displayed prose (DESIGN.md 11.1). Each pair is an
# exact span in pooling.json and its replacement.
DASH_FIX = [
    ("over $10 million — proof the threshold", "over $10 million, proof that the threshold"),
    ("selling off the furnaces — Apple recovered", "selling off the furnaces. Apple recovered"),
    ("intended purpose down with it — a single-supplier", "intended purpose down with it; a single-supplier"),
    ("four hours' notice — letting thousands", "four hours' notice, letting thousands"),
    ("1,500 hospitals — about a third of all U.S. hospital beds — and has",
     "1,500 hospitals (about a third of all U.S. hospital beds) and has"),
    ("shares of that LLC — up to eight per home — to buyers", "shares of that LLC (up to eight per home) to buyers"),
    ("resell wholesale — including to non-owners", "resell wholesale, including to non-owners"),
    ("in the world — 45,000 km", "in the world: 45,000 km"),
    ("of design capacity — with stakes", "of design capacity, with stakes"),
    ("access to the drug — completely decoupling", "access to the drug, decoupling"),
    ("than priced in — there is no separate", "than priced in; there is no separate"),
    ("Rolls-Royce — not its airline customers — absorbed", "Rolls-Royce, not its airline customers, absorbed"),
    ("no reinsurance layer behind it — when the fault", "no reinsurance layer behind it. When the fault"),
    ("the producer or the buyer — so neither", "the producer or the buyer, so neither"),
    ("is ever touched — so the sequence", "is ever touched, so the sequence"),
    ("open-ended damage assessments — but a member", "open-ended damage assessments, but a member"),
    ("premium Haiti had paid — but that payout", "premium Haiti had paid, but that payout"),
    ("what the model said it should, fast — but the model's", "what the model said it should, fast, but the model's"),
    ("Hydra — a Bermuda-domiciled captive reinsurer", "Hydra (a Bermuda-domiciled captive reinsurer"),
    ("cell for each club — retains", "cell for each club) retains"),
]

# One line per row for the page: the design element an orderbook or overrun pool
# could copy, or the trap it should avoid. Written here, not by the agent, so the
# page reads in one voice.
RELEVANCE = {
    "kickstarter-pebble-assurance-contract": "Make every order void unless a stated number of units clears a public bar by a deadline, and cap the book at what the factory can deliver, since Pebble's orders outran its supply chain.",
    "tesla-model3-refundable-reservations-prepayment": "A refundable deposit turns interest into a public, dollar-denominated count a vendor can show its lenders before it builds capacity.",
    "bordeaux-en-primeur-wine-futures-prepayment": "Early tranches have to be priced below what a buyer could get by waiting, or the buyers who prepay first simply stop coming back.",
    "apple-gtat-sapphire-prepayment-bankruptcy": "Spread prepayments across more than one vendor or site: a single first-of-a-kind supplier that misses its yield takes the whole prepayment down with it.",
    "netjets-fractional-jet-ownership": "Sell guaranteed output from a pooled fleet rather than a named unit, so a fractional owner draws on whichever reactor is running.",
    "strategic-airlift-capability-c17-fractional-ownership": "Twelve nations share three aircraft by pre-agreed hours: small buyers can hold a percentage of a fleet they could never own a whole unit of.",
    "nato-mmf-tanker-pool-consortium-ownership": "Grow the fleet by rule: each block of newly committed offtake triggers the next unit order, the way every 1,100 committed flight-hours orders another tanker.",
    "civica-rx-hospital-owned-generic-manufacturer": "Tie each member's ownership stake to a multi-year purchase commitment sized to its own demand; that pairing is what finances the shared supplier.",
    "ny-proton-center-hospital-consortium": "Competitors can co-own one expensive machine when each would otherwise buy an underused one of its own.",
    "pacaso-fractional-home-co-ownership": "Settle the legal form of fractional ownership with the regulator first; counting co-owners was enough for towns to reclassify Pacaso homes and cap its growth.",
    "2africa-submarine-cable-consortium-ownership": "Turn an ownership share into a resellable capacity right, so a member with more contracted MW than it needs can sell the surplus.",
    "nhs-antimicrobial-subscription-netflix-model": "Pay a fixed annual availability fee instead of a per-MWh price where the buyer is paying for firmness it hopes never to use.",
    "paho-revolving-fund-vaccines-joint-procurement": "A revolving fund pays the vendor on schedule while members repay on their own budget cycles, so no single small buyer carries the timing.",
    "global-fund-pooled-procurement-mechanism": "Let buyers outside the founding group pay to use the pool's negotiated price and terms without joining its governance.",
    "louisiana-hepatitis-c-subscription-2019": "A fixed multi-year payment for unlimited access suits a buyer whose goal is maximum deployment rather than rationing.",
    "rolls-royce-totalcare-trent1000-overrun-cover": "A vendor-backed performance guarantee needs reinsurance or a reserve behind it; a fleet-wide defect put more than £2 billion on one balance sheet.",
    "h2global-hintco-double-auction-hydrogen": "Split the intermediary into a long-term fixed-price buy side and a short-term market sell side, with a public fund paying only the gap.",
    "sustainable-aviation-buyers-alliance-saf-rfp": "Buyers too small to matter alone can issue one joint request for proposals that a vendor will answer.",
    "zemba-shipping-tender-buyers-club": "A collective tender commits a volume before any member's own order exists, giving the vendor one bankable multi-year contract.",
    "maschinenring-farm-machinery-ring-buyers-club": "A broker layer that matches idle capacity to occasional users can run without owning any machines; a host network could do the same with spare heat or power.",
    "pool-re-uk-terrorism-reinsurance-backstop": "Put the public guarantee last: member retention, then the pool's own reinsurance, then the state, and only for losses the first two cannot cover.",
    "tria-federal-terrorism-backstop": "Two triggers, a per-event floor and an annual aggregate floor, keep a federal backstop out of routine losses and in reach of a real tail event.",
    "ccrif-parametric-pool-haiti-basis-risk": "An index-triggered payout arrives in a day but only covers the loss the index tracks; test the index against real overruns before relying on it.",
    "international-group-pandi-clubs-mutual-pool": "Layer the pool: each member keeps the first slice, a shared layer with a hard ceiling pays the middle, and a jointly owned reinsurer and the market take the top.",
}

CARD_STEPS = [
    "A public threshold: orders bind only if a stated number of units clears by a deadline, and the book is capped at what the factory can build (Kickstarter's rule, and Pebble's lesson).",
    "Growth by rule: each block of newly committed offtake orders the next unit, as NATO's tanker pool orders an aircraft for every 1,100 committed flight-hours.",
    "Shares, not whole reactors: a 2 MW buyer holds a slice of a fleet's output, the way twelve nations share three C-17s and NetJets owners draw guaranteed hours from a pool.",
    "An availability fee where firmness is the product, as the NHS pays a fixed yearly sum per antibiotic regardless of doses used.",
    "Prepayments spread across vendors and sites: Apple's single-supplier sapphire prepayment still had $439 million outstanding when the supplier failed.",
    "A layered overrun pool: each project keeps the first slice, the pool pays a capped middle layer, reinsurance takes the top, and a public backstop sits last (P&I clubs, Pool Re, TRIA).",
    "Early tranches priced below the later market, or the first buyers wait, as they did when Bordeaux 2011 futures cost more than bottled older vintages.",
]
CARD_PARA = ("Each step below is borrowed from a market that has run it, and each named case is a row in the "
             "list further down, with its numbers and sources.")


def fix_dashes(text: str) -> str:
    for old, new in DASH_FIX:
        text = text.replace(old, new)
    return text


def dedupe(sources):
    seen, out = set(), []
    for s in sources:
        if s["url"] not in seen:
            seen.add(s["url"])
            out.append(s)
    return out


def main() -> None:
    raw = MECH.read_text()
    mech = json.loads(raw)
    rows = json.loads(PASS.read_text())["precedents"]

    for g in mech["precedent_groups"]:
        for it in g["items"]:
            if it["name"] in EXISTING_TYPES:
                it["type"] = EXISTING_TYPES[it["name"]]
    missing = [it["name"] for g in mech["precedent_groups"] if g["name"] != GROUP
               for it in g["items"] if "type" not in it]
    assert not missing, f"untyped precedents: {missing}"

    items = []
    for r in rows:
        outcome = fix_dashes(r["outcome"])
        if r.get("failure_mode"):
            outcome += " Where it broke: " + fix_dashes(r["failure_mode"])
        item = {"name": r["name"], "type": r["mechanism"], "category": r["sector"],
                "year": r["year"], "mechanism": fix_dashes(r["how_it_works"]),
                "outcome": outcome, "relevance": RELEVANCE[r["id"]],
                "sources": dedupe(r["sources"])}
        if r.get("size"):
            item["size"] = fix_dashes(r["size"])
        for f in ("mechanism", "outcome", "size"):
            assert "—" not in item.get(f, ""), (r["id"], f)
        items.append(item)
    mech["precedent_groups"] = [g for g in mech["precedent_groups"] if g["name"] != GROUP]
    mech["precedent_groups"].insert(2, {"name": GROUP, "items": items})

    cards = [c for c in mech["proposal"]["cards"] if c["title"] != CARD]
    cards.append({"title": CARD, "paras": [CARD_PARA], "steps": CARD_STEPS})
    mech["proposal"]["cards"] = cards
    mech["_meta"]["captured"] = "2026-09-26"
    note = (" 2026-09-26: added the group '" + GROUP + "' (24 non-nuclear precedents from "
            "data/research/2026-09-26-refresh/pooling.json, integrated by that folder's "
            "integrate_pooling.py), a mechanism `type` on every precedent, and the proposal card '"
            + CARD + "'.")
    if "2026-09-26" not in mech["_meta"]["note"]:
        mech["_meta"]["note"] += note
    indent = 1 if raw.startswith('{\n "') else 2
    MECH.write_text(json.dumps(mech, indent=indent, ensure_ascii=False) + "\n")
    print(f"{len(items)} precedents in '{GROUP}'; proposal cards: {len(cards)}")


if __name__ == "__main__":
    main()
