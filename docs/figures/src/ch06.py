import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import config as C, bu_profiles as BP

BUS = ["pharma", "electronics", "consumer_goods", "software"]
NAME = {"pharma": "Pharma", "electronics": "Electronics",
        "consumer_goods": "Consumer Goods", "software": "Software"}
WD = {b: BP.BU_PROFILES[b]["water_dependency"] for b in BUS}
CIv = {b: BP.BU_PROFILES[b]["carbon_intensity"] for b in BUS}
REV = {b: BP.BU_PROFILES[b]["revenue_base"] / 1e6 for b in BUS}

# ══ Figure 6.1 — two chains: what NCD reaches, and what reaches the WACC ═══
fig = plt.figure(figsize=(F.TEXT_WIDTH_IN, 4.95))
ax = fig.add_axes([0.0, 0.20, 1.0, 0.78]); F.nogrid(ax)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.text(0.005, 0.995, "THE CHAIN NATURAL CAPITAL DEBT ACTUALLY RUNS", fontsize=7.6,
        fontweight="bold", color=F.NAVY, va="top")
F.box(ax, 0.005, 0.735, 0.175, 0.135, "natural_capital_debt\nper unit", fc="white",
      ec=F.NAVY, tc=F.NAVY, size=7.2, weight="bold", lw=1.5)
F.box(ax, 0.245, 0.845, 0.235, 0.115,
      "its own interest rate\nWACC + NCD × 0.0001", fc=F.PALE, ec=F.NAVY, size=6.9)
F.box(ax, 0.245, 0.700, 0.235, 0.115,
      "OPEX, every round\nNCD × $1,000 × hostility", fc=F.PALE, ec=F.NAVY, size=6.9)
F.box(ax, 0.545, 0.845, 0.225, 0.115, "it compounds\n300 → 593 over R3–R10", fc="white",
      ec=F.NAVY, size=6.9)
F.box(ax, 0.545, 0.700, 0.225, 0.115, "at hostility 5:\n$1.5m a round on 300 pts",
      fc="white", ec=F.NAVY, size=6.9)
F.box(ax, 0.820, 0.700, 0.175, 0.260, "TERMINAL\nVALUATION", fc=F.NAVY, ec=F.NAVY,
      tc="white", size=7.6, weight="bold")
F.arrow(ax, (0.180, 0.822), (0.245, 0.902), color=F.NAVY)
F.arrow(ax, (0.180, 0.788), (0.245, 0.757), color=F.NAVY)
F.arrow(ax, (0.480, 0.902), (0.545, 0.902), color=F.NAVY)
F.arrow(ax, (0.480, 0.757), (0.545, 0.757), color=F.NAVY)
F.arrow(ax, (0.770, 0.902), (0.820, 0.860), color=F.NAVY)
F.arrow(ax, (0.770, 0.757), (0.820, 0.800), color=F.NAVY)
F.arrow(ax, (0.655, 0.838), (0.290, 0.838), color=F.NAVY, rad=-0.55, ls=(0, (3, 2)))
ax.text(0.472, 0.660, "the compounding loop:\nlast round's debt sets this round's rate",
        fontsize=6.5, color=F.NAVY, style="italic", ha="center", va="center")
F.box(ax, 0.005, 0.520, 0.175, 0.085, "green capex\nthis round", fc="white", ec=F.TEAL,
      tc=F.TEAL, size=7, weight="bold")
F.box(ax, 0.245, 0.520, 0.235, 0.085, "forgiveness\n2.0 × ln(1 + capex in $m)", fc=F.PALE,
      ec=F.TEAL, size=6.9)
F.arrow(ax, (0.180, 0.562), (0.245, 0.562), color=F.TEAL)
F.arrow(ax, (0.290, 0.605), (0.075, 0.735), color=F.TEAL, rad=-0.25, ls="--")

ax.plot([0.0, 1.0], [0.455, 0.455], color=F.GREY, lw=0.9, ls=(0, (4, 3)))
ax.text(0.005, 0.425, "AND THE CHAIN THAT REACHES THE COST OF CAPITAL — WHICH DOES NOT CONTAIN IT",
        fontsize=7.6, fontweight="bold", color=F.RUST, va="top")
TERMS = [("weighted carbon\nintensity", "max(0, (CI − 40) × 0.0008)", "+0.42%", F.RUST),
         ("mean governance\nrisk", "max(0, (gov − 25) × 0.0006)", "0", F.GREY),
         ("mean social\nlicence", "− max(0, (licence − 50) × 0.0003)", "0", F.GREY),
         ("mean water dependency\n× transparency", "(water/100) × (1 − T/100) × 0.02", "+0.76%", F.RUST)]
bw = 0.225
for i, (src, formula, val, col) in enumerate(TERMS):
    x = 0.005 + i * (bw + 0.023)
    F.box(ax, x, 0.235, bw, 0.100, src, fc="white", ec=col, tc=col, size=6.9, weight="bold")
    ax.text(x + bw / 2, 0.212, formula, ha="center", va="top", fontsize=6.0, color=F.GREY)
    ax.text(x + bw / 2, 0.163, val, ha="center", va="center", fontsize=8.6,
            fontweight="bold", color=col)
    F.arrow(ax, (x + bw / 2, 0.150), (0.50, 0.098), color=col, rad=0.0)
F.box(ax, 0.245, 0.010, 0.510, 0.085,
      "base 5.00%  +  ESG adjustment 1.18  =  WACC 6.18%   →   exit multiple 18× (capped)",
      fc=F.PALE, ec=F.RUST, tc=F.INK, size=7.4, weight="bold", lw=1.3)
kx = fig.add_axes([0.0, 0.0, 1.0, 0.185]); F.nogrid(kx)
kx.set_xlim(0, 1); kx.set_ylim(0, 1)
kx.text(0.5, 0.80, "Natural capital debt appears nowhere in the cost-of-capital formula.",
        ha="center", va="center", fontsize=8.6, fontweight="bold", color=F.RUST)
kx.text(0.5, 0.34, "It reaches the valuation by compounding against itself and by loading operating cost — "
                   "never by repricing the firm's capital.\nThe chain that does reprice capital reads nature "
                   "through water dependency and transparency instead.",
        ha="center", va="center", fontsize=7.4, color=F.INK, linespacing=1.5)
F.source(fig, "Chains executed at commit 0ad1246: NCD interest is engine.calc_natural_capital_interest "
              f"(coefficient {C.NCD_INTEREST_COEFFICIENT}), the OPEX load is NCD × "
              f"${C.NCD_OPEX_PENALTY_PER_UNIT:,.0f} × market_hostility_index (default 5), capped at 50% of "
              f"revenue, and forgiveness is {C.NCD_FORGIVENESS_LOG_COEFF} × ln(1 + green capex in $m). "
              "The WACC terms and the opening values are §6.2.3, executed on the opening state.")
F.save(fig, "fig06_01_ncd_chain")

# ══ Figure 6.2 — the water risk profile of the four units ══════════════════
fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.2),
                             gridspec_kw=dict(width_ratios=[1.0, 1.0], wspace=0.32))
order = sorted(BUS, key=lambda b: -WD[b])
y = np.arange(len(order))[::-1]
for i, b in enumerate(order):
    a1.barh(y[i], WD[b], height=0.60, color=F.SERIES[i], hatch=F.HATCH[i],
            edgecolor="white", lw=0.8)
    a1.text(WD[b] + 1.5, y[i], f"{WD[b]}", va="center", fontsize=7.6,
            fontweight="bold", color=F.SERIES[i])
MEAN = sum(WD.values()) / len(WD)
a1.axvline(MEAN, color=F.RUST, lw=1.3, ls=(0, (4, 2)))
a1.text(MEAN + 1.5, -0.62, f"group mean {MEAN:.2f}\n→ the nature premium", color=F.RUST,
        fontsize=7, fontweight="bold", va="center")
a1.set_yticks(y); a1.set_yticklabels([NAME[b] for b in order], fontsize=7.6)
a1.set_xlabel("water_dependency (0–100)"); a1.set_xlim(0, 100)
a1.grid(axis="y", visible=False); F.despine(a1)
a1.set_title("What would stop if the water did", loc="left", color=F.NAVY, fontsize=8.8)

T = np.linspace(0, 100, 200)
for i, (label, w) in enumerate([("Pharma alone, 82", 82), (f"group mean, {MEAN:.2f}", MEAN),
                                ("Software alone, 12", 12)]):
    prem = (w / 100) * (1 - T / 100) * 0.02 * 100
    a2.plot(T, prem, color=F.SERIES[i], linestyle=F.DASH[i], lw=1.8)
    a2.text(1.5, prem[0] + 0.022, label, color=F.SERIES[i], fontsize=7,
            fontweight="bold", va="bottom")
a2.plot([30], [(MEAN / 100) * 0.70 * 0.02 * 100], marker="o", ms=6, color=F.RUST, zorder=5)
a2.annotate("opening state: transparency 30,\nnature premium +0.76%",
            xy=(30, 0.76), xytext=(46, 1.30), fontsize=7, color=F.RUST,
            arrowprops=dict(arrowstyle="->", color=F.RUST, lw=0.9))
a2.set_xlabel("transparency (0–100)"); a2.set_ylabel("nature premium on the WACC, %")
a2.set_xlim(0, 100); a2.set_ylim(0, 1.85)
F.despine(a2)
a2.set_title("Disclosure is the only lever on it", loc="left", color=F.NAVY, fontsize=8.8)
F.source(fig, "water_dependency from bu_profiles.BU_PROFILES at commit 0ad1246: Pharma 82, Consumer Goods 65, "
              "Electronics 58, Software 12, mean 54.25. Nature premium = (mean water dependency ÷ 100) × "
              "(1 − transparency ÷ 100) × 0.02, §6.2.3. At the opening transparency of 30 that is 0.76 points of "
              "the 1.18-point ESG adjustment — the largest single term in it. A unit cannot lower its water "
              "dependency by wanting to; it lowers the premium by disclosing.")
F.save(fig, "fig06_02_water_profile")

# ══ Figure 6.3 — grey, green and hybrid ═══════════════════════════════════
ROWS = [
 ("Cost",          "Highest — $8m",  "Middle — $5m", "Between"),
 ("Lead time",     "Two rounds;\ncertain", "Two rounds; 75%\nestablished, else partial",
  "Two rounds; the\ngrey part certain"),
 ("Protection",    "0.85",           "0.60\n(0.35 on a failed roll)", "Additive in principle"),
 ("Co-benefits",   "None —\nNCD +10, CI +3,\nrevenue −$600K", "NCD −8, CI −6,\nrevenue +$500K per unit",
  "Some"),
 ("Residual risk", "15% of damage;\nthe wall fails once,\ncatastrophically",
  "40% of damage;\nthe mangrove\ndegrades gradually", "Lowest"),
]
COLS = [("Grey\nhard engineering", F.GREY), ("Green\nnature-based", F.TEAL), ("Hybrid", F.NAVY)]
fig, ax = F.newfig(h=3.9)
F.nogrid(ax)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
LX, CW = 0.155, 0.268
for j, (cl, col) in enumerate(COLS):
    ax.text(LX + j * CW + CW / 2, 0.985, cl, ha="center", va="top", fontsize=8,
            fontweight="bold", color=col, linespacing=1.4)
rh = 0.163
for i, row in enumerate(ROWS):
    y = 0.885 - (i + 1) * rh
    ax.text(0.148, y + rh / 2, row[0], ha="right", va="center", fontsize=7.6,
            fontweight="bold", color=F.INK)
    for j in range(3):
        col = COLS[j][1]
        F.box(ax, LX + j * CW + 0.006, y + 0.010, CW - 0.012, rh - 0.020, row[j + 1],
              fc=F.PALE if j < 2 else "white", ec=col, tc=F.INK, size=6.8)
ax.text(0.5, 0.045, "The wall fails once, catastrophically. The mangrove degrades gradually. "
                    "That is the choice, not the price.",
        ha="center", va="center", fontsize=7.6, style="italic", color=F.RUST)
F.source(fig, "Values as tabulated in Chapter 6 §6.5.3 from the Round 5 resilience options at commit 0ad1246. "
              "The Hybrid column is thin because the model offers it only in principle: the round presents the "
              "grey and green routes as the live choice.")
F.save(fig, "fig06_03_grey_green")
print("ch06 done")
