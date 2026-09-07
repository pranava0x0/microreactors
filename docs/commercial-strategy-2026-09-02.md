# Commercial strategy read, 2026-09-02

What the site's own data says about where a 1–20 MW reactor gets sold, what a unit has to
cost to get there, and which counterparties have a structural reason to buy. This is the
reasoning behind `data/strategy.json` (rendered on Costs › What wins and Deals › Prospects).
Every number here is a row on the site; nothing was fetched for this pass. Derived figures
say so and print their formula.

## 1. Where things are

- **The only signed, sited reactors are federal.** Janus (five bases, 20+ units, up to
  $2.2B, Army-licensed) and ANPI (three bases) pair a named reactor to a named site. The
  Army says the purpose is to manufacture a commercial industry, and that it expects the
  majority of the money to be private. Its contracts convert to a power purchase agreement
  after year one.
- **The commercial track has one signed microreactor purchase** (Equinix, 20 units with
  deposits, no sites, no price) and a set of frameworks at SMR scale (Switch 12 GW, Meta's
  prepayment, Google's fleet agreement, Amazon's phased Xe-100 deal).
- **Three funded buyers have no vendor.** Copper Valley Electric Association finished a
  favourable pre-feasibility study and tabled the project; its vendor, USNC, then went
  bankrupt. Saskatchewan Research Council had CA$80M and lost Westinghouse in fall 2025.
  Global First Power's Chalk River application is paused for the same bankruptcy.
- **Cost is a five-times disagreement**, $2,515 to $22,000 per kWe, and the spread is
  first-unit versus factory-unit, not measurement error.

## 2. The cost ladder: what a unit has to cost to win

Four rungs, each a published scenario, each opening a set of buyers whose incumbent price
is on the Customer cost sub-tab.

| Rung | $/kWe | $/MWh | Opens |
|---|---|---|---|
| First unit (INL bottom-up) | 14,500–22,000 | 325 (NEI FOAK 140–410) | Rural Alaska and Nunavut at $410–1,950/MWh; island bases where the gas alternative is $18,440/kW plus shipped fuel; the top half of the remote-mine band |
| Mass-produced (INL, 10 units a year) | 6,000 | 120–150 (NEI NOAK 90–330) | The whole $250–600/MWh remote-diesel band; healthcare behind the meter at $150/MWh; firm on-site generation at bases priced at $5,433/kW |
| Optimized design (U-Michigan inputs) | 2,515–3,970 | 48–78 with PTC, 63–103 without | Grid-adjacent buyers, given a schedule or resilience reason to pay above the grid |
| Below every estimate | 1,420–2,800 (gas CHP) | n/a | Nothing. Greenhouses, university concessions, a battery plant at $24.56/MWh plus demand charge |

Per unit (derived: $/kWe × MWe × 1,000):

| | 1 MWe | 2.5 MWe | 6 MWe | 20 MWe |
|---|---|---|---|---|
| First unit | $14.5–22M | $36–55M | $87–132M | $290–440M |
| Mass-produced | $6M | $15M | $36M | $120M |
| Optimized | $2.5–4M | $6.3–9.9M | $15–24M | $50–79M |

Rule of thumb (derived, 5% real over 20 years, 95% capacity factor): every $1,000/kWe adds
about $10/MWh; over 40 years about $7. So the gap between the first unit and the
mass-produced unit, about $8,500/kWe, is about $80/MWh of price, which is the difference
between winning the top half of the remote-diesel band and winning all of it.

## 3. The floor that never falls, and why the 1 MWe class is a fleet product

INL charges staff, security and monitoring per reactor and holds the line fixed as the
reactor grows. Spread over output at 95% capacity factor (derived):

| Fixed cost per reactor | $/yr | 1 MWe | 2.5 MWe | 6 MWe | 20 MWe |
|---|---|---|---|---|---|
| Guard (1 per 2 reactors) + remote monitor (1 per 20) | 490,000 | $59 | $24 | $10 | $3 |
| INL O&M staff line, first unit | 3,915,898 | $471 | $188 | $78 | $24 |
| Same line, mass-produced (−62%) | 1,488,041 | $179 | $72 | $30 | $9 |

At 1 MWe the first-unit staff line alone exceeds the entire remote-diesel band. Even the
leanest case (a shared guard and a remote monitor, operators arriving only for a shutdown)
is $59/MWh, a fifth of the band's floor. This is the reverse economy of scale in its
sharpest form, and it is why every 1 MWe deal on the tracker is a fleet: 15 units at Fort
Benning, 3 at Fort Bragg, 20 for Equinix. The 1 MWe product is sold by the site, not by
the unit, and the price depends on how many units share the guards, the monitors and the
refuelling crew. A lone 1 MWe unit at a remote mine only clears rural-Alaska prices. The
20 MWe unit (BWXT) carries the floor at $3–24/MWh and is the one that can be sold singly.

## 4. Segment verdicts

| Segment | Incumbent | Clears at | Blocker |
|---|---|---|---|
| Rural Alaska and Nunavut | $410–1,950/MWh certified; Nunavut $555–1,130 | First unit | Load: villages draw tens of kW; only hubs (Kotzebue, 19.7 GWh/yr) or an aggregated tribal utility can take a unit |
| Isolated federal installations | Guantanamo $18,440/kW gas plant; Doyon's $3.08B 50-year franchise on coal and oil | First unit | Eielson award follows NRC licensing; price unpublished |
| Off-grid mines | $250–600/MWh; NRCan C$200–350M per 20 MWe | Mass-produced (first unit only wins the top half) | Mine life vs payback (Diavik, Red Dog 2032); electrification adds 10–15 MW; distrust of microgrid collapse at −40 |
| Hospitals, water, civic anchors | $150/MWh flat 30-yr (Loma Linda); $220–250 sub-acute; FEMA outage value $67.6M–$261M per site | Mass-produced | No AHJ accepts a non-diesel sole emergency source; campus loads are single-digit MW so the floor bites |
| Firm generation at grid-connected bases | $5,433/kW (Fort Stewart); $3,480/kW firm block (Camp Buehring) | Mass-produced, on the fuel and O&M line | Army says reactors will not supply all of a base; the comparison is a microgrid block |
| Ports | $7.0M/berth, $14.7M/cruise berth; $1.4B of Clean Ports load with zero supply | Capital avoidance, no $/MWh | Duty cycle; no US port has signed |
| Data centers | Colocation $269/MWh all-in; PJM capacity $121,700/MW-yr; 15-yr minimum bills | Optimized vs grid; mass-produced vs a colocation-priced resilience block | Speed: xAI chose unpermitted turbines over waiting |
| Factories and process heat | $24.56/MWh + demand charge; $187/MWh firm in a remote grid; self-owned CHP | Optimized, or heat as the product | One small host cannot carry a licensee; no priced vendor-owned heat precedent |

The honest summary: **two segments buy on cost today (Arctic communities and isolated
bases), one buys on cost at the mass-produced rung (remote mines), and everything else
buys schedule, resilience or capital avoidance and has to be priced that way.**

## 5. Who has a structural reason to buy

Grouped by the reason, with the first question to ask. Full rows in `data/strategy.json`.

**Off-grid and burning fuel.** Teck/NANA Red Dog (25 MW, one 20 MWe unit replaces the
station, closure ~2032 so only a relocatable unit fits); Glencore Raglan (60M L/yr, third
party ownership precedent); the off-grid power contractors themselves (Zenith, Aggreko,
EDL, TUGLIQ), who hold the sites and the 15–16 year contracts and would own the reactor
behind the fence. The channel is the contractor, not the miner.

**A wire that has not arrived.** Agnico Eagle and Nukik in Kivalliq (a C$3.2B line due
2032; the mine is three-quarters of its justification, but Inuit ownership is what
mobilises the public money); the Ports of Los Angeles and New York/New Jersey ($1.4B of
electrified load, no supply funded).

**Sovereignty.** Doyon Utilities (Alaska Native corporation JV, 50-year franchise on coal
and oil at Fort Wainwright, an unmatched Janus site); Qulliq and the Government of Nunavut;
Tanana Chiefs Conference's eight-village tribal utility (the aggregated buyer the federal
award just created).

**Funded, and vendorless.** CVEA (study done, site chosen, state law changed, board tabled
it); SRC (CA$80M, evaluating vendors); Global First Power at Chalk River (paused CNSC
application, OPG co-venturer). These are the cheapest first conversations in the file.

**Already signed or declared.** Equinix (the fleet-shaped purchase); the hyperscalers
(their legal teams own a nuclear PPA playbook; the microreactor sale is a 1–20 MW
resilience block priced against colocation and diesel); Diamondback (LOI, unconverted);
IANC members (a consortium with no RFP); DP World (a port will sign, under a UK regulator);
the four universities with real filings; the privatised base utilities that own Janus
bases' wires (Sandhills, City Light & Power).

**Speed or land.** xAI-class builders (permitting exposure is the pitch); Texas large loads
under SB6 (curtailment makes firm on-site generation worth more; 9.9 MW fits the fast
process by rule); Last Energy's 30-unit Haskell site; Aalo at RELLIS (2,400 acres offered).

**Policy-gated.** Texas's $1.8B backup program and $350M nuclear fund, both sized for the
band and both closed to it by a technology list.

**Supply chain.** BWXT (fuel to its own competitors), Standard Nuclear (Radiant's and
Antares' fabricator, downsized IPO), Centrus ($900M HALEU contract). Fuel is the one line
volume does not learn down and the one with no published price.

## 6. What this changes about the pitch

1. Sell the site, not the unit, below 5 MWe. Quote a fleet price with the staffing floor
   shown, or quote a 20 MWe unit.
2. Price against the incumbent's instrument, not its tariff: the ESPC, the privatised
   utility's rate base, the FEMA worksheet, the colocation rate, the feeder upgrade.
3. Start where the vendor is missing: CVEA, SRC, Chalk River. Feasibility is paid for.
4. Treat the off-grid IPPs as the channel for mines, and the privatised utilities as the
   channel for bases.
5. Publish a cost curve before someone else does; Radiant's 15-unit run is the only place
   serial cost will be observed.

## 7. What is not known (the next research pass)

Each prospect row ends with its first question. The ones that would move a decision:
Doyon's delivered fuel cost at Fort Wainwright and whether the 2688 contract admits new
generation; CVEA's stated reason for tabling; SRC's current vendor list and whether the
CA$80M survives; Red Dog's delivered $/MWh; Nukik's openness to generation in place of
the line; which Nunavut communities draw over 1 MW; what a ton of fabricated TRISO costs.
These are filed as GitHub issues.
