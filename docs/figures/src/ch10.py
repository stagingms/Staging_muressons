import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import config as C, bu_profiles as BP, round_configs as RC, npc_stakeholders as NPC

BUS = ["pharma", "electronics", "consumer_goods", "software"]
GOV = {b: BP.BU_PROFILES[b]["governance_risk_score"] for b in BUS}
OPEX = {b: BP.BU_PROFILES[b]["opex_base"] for b in BUS}
NAME = {"pharma": "Pharma", "electronics": "Electronics",
        "consumer_goods": "Consumer Goods", "software": "Software"}

# ══ Figure 10.1 — the governance-risk propagation map ═════════════════════
fig = plt.figure(figsize=(F.TEXT_WIDTH_IN, 4.9))
ax = fig.add_axes([0.0, 0.360, 1.0, 0.630]); F.nogrid(ax)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
F.box(ax, 0.375, 0.860, 0.250, 0.125, "governance_risk_score\nper unit", fc="white",
      ec=F.NAVY, tc=F.NAVY, size=7.6, weight="bold", lw=1.6)
CHAN = [
 (0.005, "Every OTHER unit's OPEX",
  f"surcharge = opex × Σ(other units' gov × {C.SUPPLY_CHAIN_OVERLAP_COEFF})", F.RUST),
 (0.253, "Strike probability, R9",
  f"P = gov ÷ 100 + (1 − SLO ÷ 100) × {C.STRIKE_SOCIAL_LICENSE_WEIGHT}", F.RUST),
 (0.501, "Cost of capital",
  "premium = max(0, (mean gov − 25) × 0.0006)", F.TEAL),
 (0.749, "The regulator NPC",
  "trigger at gov > 60 → formal investigation", F.NAVY),
]
for x, title, formula, col in CHAN:
    F.box(ax, x, 0.545, 0.246, 0.150, title, fc=F.PALE, ec=col, tc=col, size=7.2,
          weight="bold")
    ax.text(x + 0.123, 0.520, formula, ha="center", va="top", fontsize=5.9, color=F.GREY)
    F.arrow(ax, (0.500, 0.860), (x + 0.123, 0.700), color=col, rad=0.0)
F.box(ax, 0.005, 0.230, 0.990, 0.105,
      "The propagation is the point: one unit's governance failure is charged to the other three, "
      "every round, whether or not they did anything.",
      fc="#F4EBE6", ec=F.RUST, tc=F.INK, size=7.4, weight="bold")
F.box(ax, 0.320, 0.030, 0.360, 0.115, "staff_burnout_index above 70\nadds governance risk",
      fc="white", ec=F.GREY, tc=F.INK, size=6.9)
F.arrow(ax, (0.500, 0.145), (0.500, 0.230), color=F.GREY, ls=(0, (3, 2)))
ax.plot([0.680, 0.982, 0.982], [0.0875, 0.0875, 0.922], color=F.GREY, lw=1.0, ls=(0, (3, 2)))
F.arrow(ax, (0.982, 0.922), (0.628, 0.922), color=F.GREY, ls=(0, (3, 2)))

bx = fig.add_axes([0.075, 0.080, 0.860, 0.215])
y = np.arange(len(BUS))[::-1]
for i, b in enumerate(BUS):
    others = sum(GOV[o] for o in BUS if o != b)
    sur = OPEX[b] * others * C.SUPPLY_CHAIN_OVERLAP_COEFF / 1e6
    bx.barh(y[i], sur, height=0.60, color=F.SERIES[i], hatch=F.HATCH[i],
            edgecolor="white", lw=0.7)
    bx.text(sur + 0.012, y[i], F.esc(f"${sur:.2f}m a round   "
            f"(own gov {GOV[b]}, others' {others})"), va="center", fontsize=6.8, color=F.INK)
bx.set_yticks(y); bx.set_yticklabels([NAME[b] for b in BUS], fontsize=7.2)
bx.set_xlabel("supply-chain contagion surcharge at the opening state, $m a round", fontsize=7)
bx.set_xlim(0, 1.15); bx.grid(axis="y", visible=False); F.despine(bx)
bx.tick_params(labelsize=6.8)
F.source(fig, "engine.calc_supply_chain_contagion, calc_strike_probability, the WACC governance premium of "
              "§6.2.3 and npc_stakeholders.NPC_PROFILES['regulator'].triggers, at commit 0ad1246. Opening "
              "governance-risk scores: Software 25, Electronics 20, Pharma 15, Consumer Goods 10. "
              "Software carries the highest governance risk of the four and the lowest OPEX base, so it pays "
              "the least contagion and causes the most.")
F.save(fig, "fig10_01_governance_propagation")

# ══ Figure 10.2 — five ethical lenses on the Round 6 decision ═════════════
r6 = RC.ROUND_CONFIGS[6]["options"]
LENSES = [
 ("Consequences", "Which option produces the best\noutcome overall, counting everyone?",
  "A buys $10m of Software revenue against −20 reputation, −15 licence and a contagion spike. "
  "B costs $8m and buys +15 licence, +5 reputation, −5 governance and +$0.8m revenue on every unit. "
  "On totals, B."),
 ("Duty", "What do we owe the people the\nalgorithm ranked, regardless of outcome?",
  "The candidates were wronged. A monetises the wrong; C conceals it. Only B remedies it. "
  "A duty account does not weigh the $10m at all."),
 ("Rights", "Whose rights are engaged, and are\nthey the kind that can be traded?",
  "Non-discrimination is not a preference to be priced. On a rights account A and C are "
  "not cheaper options; they are not options."),
 ("Virtue", "What would a person of good\ncharacter do — and become?",
  "C is the character question in miniature: the Quiet Patch costs only $1m and asks the team "
  "to become the kind of company that fixes quietly and says nothing."),
 ("Justice", "Who bears the burden, and did\nthey agree to bear it?",
  "The burden falls on rejected candidates who never consented and cannot appeal. "
  "The benefit falls to the Software unit's revenue line."),
]
fig, ax = F.newfig(h=4.6)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.text(0.005, 0.995, "THE ROUND 6 DECISION — an AI recruitment tool found to discriminate",
        fontsize=8, fontweight="bold", color=F.NAVY, va="top")
OPT = [("A · Monetise the Algorithm", "+$10.0m Software revenue · −20 rep · −15 licence · +8 gov", F.RUST),
       ("B · Ethical AI Overhaul", "−$8.0m · +15 licence · +5 rep · −5 gov · +$0.8m revenue/unit", F.TEAL),
       ("C · Quiet Patch", "−$1.0m · −5 rep · +10 gov · −3 licence · −$0.2m revenue/unit", F.GREY)]
for i, (t, sub, col) in enumerate(OPT):
    F.box(ax, 0.005 + i * 0.332, 0.845, 0.325, 0.105, f"{t}\n{sub}", fc="white", ec=col,
          tc=col, size=6.3, weight="bold")
rh = 0.150
for i, (name, question, reading) in enumerate(LENSES):
    y = 0.815 - (i + 1) * rh
    col = F.SERIES[i % len(F.SERIES)]
    F.box(ax, 0.005, y + 0.008, 0.150, rh - 0.020, name, fc=F.PALE, ec=col, tc=col,
          size=7.6, weight="bold")
    ax.text(0.168, y + rh / 2, question, fontsize=6.6, color=F.GREY, va="center")
    ax.text(0.395, y + rh / 2, reading, fontsize=6.5, color=F.INK, va="center", wrap=True)
ax.text(0.005, 0.020, "Four of the five lenses land on B. The one that does not — consequences — is the "
                      "only one the cockpit shows you a number for.",
        fontsize=7, color=F.RUST, style="italic")
ax.set_xlim(0, 1.02)
F.source(fig, "Option impacts read from round_configs.ROUND_CONFIGS[6] at commit 0ad1246. The five lenses "
              "are the standard normative frames; the readings are the chapter's argument applied to the "
              "engine's own numbers [J], not an output of the model — the model scores only the first column.")
F.save(fig, "fig10_02_five_lenses")

# ══ Figure 10.3 — the nine NGRBC principles against the rounds ════════════
PRIN = [
 ("P1", "conduct and govern with integrity —\nethical, transparent, accountable", [1]),
 ("P2", "provide goods and services in a manner\nthat is sustainable and safe", [3]),
 ("P3", "respect and promote the well-being of\nall employees, including value chains", [2]),
 ("P4", "respect the interests of and be\nresponsive to all stakeholders", [9]),
 ("P5", "respect and promote human rights", [2, 6]),
 ("P6", "protect and restore the environment", [3]),
 ("P7", "influence public and regulatory policy\nresponsibly and transparently", [1, 7]),
 ("P8", "promote inclusive growth and\nequitable development", [8]),
 ("P9", "engage with and provide value to\nconsumers responsibly", [9]),
]
BRSR_TITLES = {1: "Governance & Transparency", 2: "Workforce & Human Rights",
               3: "Environment & Circularity", 4: "Value Chain & BRSR Core",
               5: "Integrated Disclosure & ESG Alpha", 6: "Human Rights Realities",
               7: "Policy Advocacy & Ethical Frameworks", 8: "Inclusive Micro-Growth",
               9: "Value Chain Assurance", 10: "Global Integration"}
fig = plt.figure(figsize=(F.TEXT_WIDTH_IN, 4.7))
ax = fig.add_axes([0.0, 0.235, 1.0, 0.700]); F.nogrid(ax)
ax.set_xlim(0, 1); ax.set_ylim(0, 1.06)
LEFT, CELL = 0.475, 0.0505
for r in range(1, 11):
    ax.text(LEFT + (r - 0.5) * CELL, 1.045, str(r), ha="center", va="bottom",
            fontsize=7, fontweight="bold", color=F.GREY)
ax.text(LEFT + 5 * CELL, 1.015, "BRSR / NGRBC side-track round", ha="center", va="bottom",
        fontsize=6.6, color=F.GREY)
rh = 0.108
for i, (code, text, rounds) in enumerate(PRIN):
    y = 0.98 - (i + 1) * rh
    col = F.SERIES[i % len(F.SERIES)]
    ax.text(0.005, y + rh / 2, code, fontsize=8, fontweight="bold", color=col, va="center")
    ax.text(0.042, y + rh / 2, text, fontsize=6.4, color=F.INK, va="center")
    for r in range(1, 11):
        cx = LEFT + (r - 0.5) * CELL
        if r in rounds:
            ax.add_patch(plt.Rectangle((LEFT + (r - 1) * CELL + 0.004, y + 0.012),
                                       CELL - 0.008, rh - 0.024, fc=F.PALE, ec=col, lw=1.0))
            ax.plot([cx], [y + rh / 2], marker=F.MARK[i % len(F.MARK)], ms=4.2, color=col)
        else:
            ax.plot([cx], [y + rh / 2], marker="_", ms=3.4, color="#D2DAE1")
kx = fig.add_axes([0.0, 0.0, 1.0, 0.205]); F.nogrid(kx)
kx.set_xlim(0, 1); kx.set_ylim(0, 1)
kx.text(0.0, 1.0, "The side track's own round titles", fontsize=7.2, fontweight="bold",
        color=F.GREY, va="top")
for j in range(2):
    for k in range(5):
        r = j * 5 + k + 1
        kx.text(0.005 + k * 0.200, 0.78 - j * 0.30, f"R{r}  {BRSR_TITLES[r]}",
                fontsize=6.3, color=F.INK, va="top")
kx.text(0.0, 0.14, "Rounds 4, 5 and 10 carry no single principle: they are the integrative rounds "
                   "(Value Chain and BRSR Core, Integrated Disclosure, Global Integration).",
        fontsize=6.6, color=F.RUST, va="top", style="italic")
F.source(fig, "Principle wording: the National Guidelines on Responsible Business Conduct (MCA, 2019), "
              "as published. Round mapping: the principle codes the BRSR / NGRBC side track itself carries "
              "in side_tracks.brsr_ngrbc.configs.BRSR_ROUND_CONFIGS at commit 0ad1246 — the titles name the "
              "principles, so the mapping is the build's own, not an interpretation.")
F.save(fig, "fig10_03_ngrbc_map")

# ══ Figure 10.4 — the greenwashing detector ═══════════════════════════════
POOL = 10_000_000
share = np.linspace(0, 0.30, 400)
full = np.where(share < C.GREENWASH_INVESTMENT_THRESHOLD, C.GREENWASH_SLO_PENALTY, 0.0)
mod_t = C.GREENWASH_INVESTMENT_THRESHOLD * C.GREENWASH_MODERATE_THRESHOLD_SCALE
mod = np.where(share < mod_t, C.GREENWASH_SLO_PENALTY * C.GREENWASH_MODERATE_PENALTY_SCALE, 0.0)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.3),
                             gridspec_kw=dict(width_ratios=[1.0, 1.25], wspace=0.30))
a1.step(share * 100, full, where="post", color=F.RUST, lw=2.0, label="full green claim")
a1.step(share * 100, mod, where="post", color=F.TEAL, lw=2.0, ls="--",
        label="moderate green claim")
a1.axvline(C.GREENWASH_INVESTMENT_THRESHOLD * 100, color=F.RUST, lw=0.9, ls=(0, (2, 2)))
a1.axvline(mod_t * 100, color=F.TEAL, lw=0.9, ls=(0, (2, 2)))
a1.text(C.GREENWASH_INVESTMENT_THRESHOLD * 100 + 0.4, 13.6, "15%", fontsize=7,
        color=F.RUST, fontweight="bold")
a1.text(mod_t * 100 + 0.4, 6.2, "10.05%", fontsize=7, color=F.TEAL, fontweight="bold")
a1.set_xlabel("team's share of the CSF pool, %")
a1.set_ylabel("social licence penalty, points")
a1.set_ylim(-0.8, 17); a1.set_xlim(0, 30)
a1.legend(fontsize=6.8, loc="upper right")
F.despine(a1)
a1.set_title("Two claims, two thresholds", loc="left", color=F.NAVY, fontsize=8.6)

TAX = [("Selective disclosure", "report the good number, omit the bad",
        "The Round 2 dictionary has no Q4 issue,\nso a team can only ever over-claim"),
       ("Empty claim", "a promise with no capital behind it",
        F.esc("exactly what the detector catches: a green\nclaim on under 15% of the pool")),
       ("Symbolic action", "a real but immaterial act,\npresented as strategy",
        "CSRD_ISSUES exec_travel: <0.01% of group\nemissions, offered as a material choice"),
       ("Misleading baseline", "true against a chosen year,\nfalse against any other",
        "intensity versus absolute — Chapter 5 §5.2,\nand the growth trap of §5.2.2"),
       ("Concealed remediation", "fix it, say nothing,\nkeep the credit",
        "the Round 6 Quiet Patch: $1m, −5 reputation,\n+10 governance risk, no disclosure")]
a2.axis("off")
a2.set_xlim(0, 1); a2.set_ylim(0, 1)
rh2 = 0.183
for i, (name, defn, ex) in enumerate(TAX):
    y = 0.965 - (i + 1) * rh2
    col = F.SERIES[i % len(F.SERIES)]
    a2.text(0.005, y + rh2 * 0.72, name, fontsize=7.2, fontweight="bold", color=col)
    a2.text(0.005, y + rh2 * 0.45, defn, fontsize=6.2, color=F.GREY, style="italic")
    a2.text(0.400, y + rh2 * 0.55, ex, fontsize=6.2, color=F.INK, va="center")
a2.text(0.005, 0.985, "FIVE FORMS, AND WHERE EACH LIVES IN THE SIMULATION", fontsize=7,
        fontweight="bold", color=F.GREY, va="top")
F.source(fig, "engine.calc_greenwashing_risk at commit 0ad1246: a green claim is checked against the team's "
              f"share of the CSF pool, at {C.GREENWASH_INVESTMENT_THRESHOLD:.0%} for a full claim and "
              f"{mod_t:.2%} for a moderate one, and the penalty is {C.GREENWASH_SLO_PENALTY:.0f} social "
              f"licence points, halved for a moderate claim. Either claim is backed outright by total capex "
              f"of ${C.GREENWASH_ABS_CAPEX_FLOOR/1e6:.0f}m or more, whatever the share. The taxonomy is the "
              "chapter's [J]; each example is a mechanic or dictionary entry that exists in the build.")
F.save(fig, "fig10_04_greenwashing")
print("ch10 done")
