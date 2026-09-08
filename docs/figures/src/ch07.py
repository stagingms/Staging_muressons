import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import round_configs as RC, config as CFG, bu_profiles as BP

# ══ Figure 7.1 — the linear flow, and the two cycles ═══════════════════════
fig, (a1, a2) = plt.subplots(2, 1, figsize=(F.TEXT_WIDTH_IN, 4.5),
                             gridspec_kw=dict(height_ratios=[1.0, 1.32], hspace=0.20))
for a in (a1, a2):
    F.nogrid(a); a.set_xlim(0, 1); a.set_ylim(0, 1)

# linear
a1.text(0.005, 0.98, "LINEAR — take, make, waste", fontsize=8, fontweight="bold",
        color=F.RUST, va="top")
STAGES = ["TAKE\nvirgin material", "MAKE\nthe product", "USE\nthree years", "WASTE\nlost to the firm"]
bw, bh, y0 = 0.195, 0.34, 0.40
for i, s in enumerate(STAGES):
    x = 0.02 + i * (bw + 0.055)
    last = i == len(STAGES) - 1
    F.box(a1, x, y0, bw, bh, s, fc="white" if not last else "#F4EBE6",
          ec=F.RUST if last else F.GREY, tc=F.INK, size=7.2,
          weight="bold" if last else "normal", lw=1.4 if last else 1.0)
    if i < 3:
        F.arrow(a1, (x + bw, y0 + bh / 2), (x + bw + 0.055, y0 + bh / 2), color=F.GREY)
LEAKS = [("Residual value", "copper, cobalt,\na working screen", 0.30),
         ("Embodied energy", "the energy of extraction,\ndiscarded with the metal", 0.53),
         ("Disposal liability", "someone sends the\nproducer the bill", 0.76)]
for name, sub, x in LEAKS:
    F.arrow(a1, (x, y0), (x, y0 - 0.20), color=F.RUST, lw=1.2)
    a1.text(x, y0 - 0.235, name, ha="center", va="top", fontsize=7,
            fontweight="bold", color=F.RUST)
    a1.text(x, y0 - 0.335, sub, ha="center", va="top", fontsize=6.2, color=F.GREY)
a1.text(0.005, 0.055, "three leaks — §7.1.2", fontsize=6.6, color=F.RUST, style="italic")

# circular
a2.text(0.005, 0.985, "CIRCULAR — two cycles, and the rungs that close them",
        fontsize=8, fontweight="bold", color=F.TEAL, va="top")
F.box(a2, 0.055, 0.700, 0.180, 0.150, "MAKE", fc="white", ec=F.NAVY, tc=F.NAVY,
      size=8, weight="bold", lw=1.5)
F.box(a2, 0.055, 0.140, 0.180, 0.150, "USE", fc="white", ec=F.NAVY, tc=F.NAVY,
      size=8, weight="bold", lw=1.5)
F.arrow(a2, (0.145, 0.700), (0.145, 0.290), color=F.NAVY, lw=1.4)
SPINE = 0.300
a2.plot([SPINE, SPINE], [0.215, 0.775], color=F.TEAL, lw=1.6)
a2.plot([0.235, SPINE], [0.215, 0.215], color=F.TEAL, lw=1.6)
F.arrow(a2, (SPINE, 0.775), (0.238, 0.775), color=F.TEAL, lw=1.6)
LOOPS = [("Reuse / Repair / Refurbish", "keeps the whole product", 0.665, 0.010),
         ("Remanufacture / Repurpose", "keeps the component", 0.515, 0.075),
         ("Recycle", "keeps only the material", 0.365, 0.140),
         ("Recover", "keeps only the energy", 0.215, 0.205)]
for i, (label, sub, y, ind) in enumerate(LOOPS):
    x0 = SPINE + 0.045 + ind
    F.box(a2, x0, y - 0.058, 0.300, 0.116, label, fc=F.PALE, ec=F.TEAL, tc=F.INK,
          size=7.0, weight="bold")
    F.arrow(a2, (x0, y), (SPINE + 0.004, y), color=F.TEAL, lw=1.3,
            ls=F.DASH[i] if i else "-")
    a2.text(x0 + 0.315, y, sub, fontsize=6.5, color=F.GREY, va="center")
a2.annotate("", xy=(0.318, 0.700), xytext=(0.318, 0.215),
            arrowprops=dict(arrowstyle="-|>", color=F.GREY, lw=1.2))
a2.text(0.720, 0.790, "tightest loop — most of the original value survives it",
        fontsize=6.4, color=F.GREY, style="italic", ha="center")
a2.text(0.760, 0.118, "loosest loop — the material is gone, only the energy is recovered",
        fontsize=6.4, color=F.GREY, style="italic", ha="center")
a2.text(0.345, 0.905, "TECHNICAL CYCLE — the loops the Round 7 options buy",
        fontsize=7, fontweight="bold", color=F.TEAL, va="top")
F.box(a2, 0.020, 0.005, 0.630, 0.090,
      "BIOLOGICAL CYCLE — regenerate natural systems: nature-based offsets\n"
      "and NCD forgiveness. The third principle, and Chapter 6's engine, not this one.",
      fc="#EAF1EC", ec=F.SERIES[1], tc=F.INK, size=6.2)
F.arrow(a2, (0.145, 0.095), (0.145, 0.140), color=F.SERIES[1], lw=1.2)
a2.set_xlim(0, 1.16)
F.source(fig, "Leak points: §7.1.2. Three principles and two cycles: §7.2.1 — the statement is marked "
              "contested in the chapter and is used here as the organising frame, not as an authority. Rungs "
              "are the R-hierarchy of §7.2.2, ordered by value retained. The biological cycle is handled by "
              "Chapter 6's natural-capital engine, not by the Round 7 mechanic.")
F.save(fig, "fig07_01_linear_circular")

# ══ Figure 7.2 — the R-hierarchy, with a Muressons option on each rung ═════
RUNGS = [
 ("Refuse / Rethink", "Do not make the product;\nmake the service instead",
  "product-as-a-service — discussed in §7.3.1,\nnot offered as a round option", True),
 ("Reduce", "Use less material and energy\nper unit of output",
  "Round 2 · Energy Efficiency Upgrades  −$2.5m", False),
 ("Reuse / Repair / Refurbish", "Keep the product in use",
  "Round 7 · Material Passports (Full Circular Redesign)  −$10.0m", False),
 ("Remanufacture / Repurpose", "Recover the component\nor the function",
  "Round 3 · Closed-Loop Manufacturing", False),
 ("Recycle", "Recover the material",
  "Round 7 · Extended Producer Responsibility  −$5.0m", False),
 ("Recover", "Recover the energy",
  "Round 7 · Waste-to-Energy Partnership  −$7.0m", False),
]
fig, ax = F.newfig(h=4.0)
F.nogrid(ax)
n = len(RUNGS)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
rh = 0.132
for i, (rung, meaning, option, absent) in enumerate(RUNGS):
    y = 0.90 - (i + 1) * rh
    col = F.SERIES[i % len(F.SERIES)]
    indent = i * 0.026
    F.box(ax, 0.030 + indent, y + 0.008, 0.215, rh - 0.020, rung, fc="white", ec=col,
          tc=col, size=7.2, weight="bold", lw=1.3)
    ax.text(0.262 + indent, y + rh / 2, meaning, fontsize=6.8, color=F.INK, va="center")
    ax.text(0.520, y + rh / 2, option, fontsize=6.8, va="center",
            color=F.GREY if absent else F.INK,
            style="italic" if absent else "normal")
ax.annotate("", xy=(0.012, 0.905 - rh * n), xytext=(0.012, 0.905),
            arrowprops=dict(arrowstyle="-|>", color=F.GREY, lw=1.4))
ax.text(0.004, 0.905, "most value\nretained", fontsize=6.6, color=F.GREY, ha="left",
        va="bottom", fontweight="bold")
ax.text(0.004, 0.895 - rh * n, "least", fontsize=6.6, color=F.GREY, ha="left", va="top",
        fontweight="bold")
ax.text(0.030, 0.955, "RUNG", fontsize=7, fontweight="bold", color=F.GREY)
ax.text(0.262, 0.955, "WHAT IT MEANS", fontsize=7, fontweight="bold", color=F.GREY)
ax.text(0.520, 0.955, "WHERE IT APPEARS IN THE GAME", fontsize=7, fontweight="bold", color=F.GREY)
ax.text(0.030, 0.055, "The top rung is the one the game cannot be played on: there is no round option that "
                      "declines to make the product.", fontsize=7, color=F.RUST, style="italic")
F.source(fig, "Rungs, meanings and game options: the table in Chapter 7 §7.2.2, with the round costs read from "
              "pillar_configs and round_configs at commit 0ad1246. The ordering is the value-retention ordering "
              "the hierarchy asserts: the tighter the loop, the more of the original value survives it.")
F.save(fig, "fig07_02_r_hierarchy")

# ══ Figure 7.3 — Round 7's three options on six dimensions ═════════════════
r7 = RC.ROUND_CONFIGS[7]["options"]
OPTS = [("A · Full Circular\nRedesign", "option_a", F.NAVY, 0),
        ("B · Extended Producer\nResponsibility", "option_b", F.TEAL, 1),
        ("C · Waste-to-Energy\nPartnership", "option_c", F.RUST, 2)]
BONUS = CFG.ECONOMIC_CIRCULAR_ECONOMY_BONUS
def opex_saving(key):
    if key in ("option_a", "option_b"):
        return sum(BP.BU_PROFILES[b]["opex_base"] for b in
                   ("pharma", "electronics", "consumer_goods", "software")) * BONUS / 1e6
    return 0.0
DIMS = [
 ("Cash cost\n$m",            lambda k: abs(r7[k]["impacts"]["treasury"]) / 1e6, False),
 ("Carbon intensity\npoints removed", lambda k: -r7[k]["impacts"].get("carbon_intensity_delta", 0), True),
 ("Natural capital debt\npoints removed", lambda k: -r7[k]["impacts"].get("natural_capital_debt_delta", 0), True),
 ("Reputation and licence\npoints gained", lambda k: r7[k]["impacts"].get("reputation", 0)
                                            + r7[k]["impacts"].get("social_license_delta", 0), True),
 ("OPEX cut this round\n$m (15% of every base)", lambda k: opex_saving(k), True),
 ("Synergy multiplier\nadded", lambda k: r7[k]["impacts"].get("synergy_multiplier_boost", 0), True),
]
fig, axes = plt.subplots(1, 6, figsize=(F.TEXT_WIDTH_IN, 2.9))
for j, (title, fn, good_high) in enumerate(DIMS):
    a = axes[j]
    vals = [fn(k) for _l, k, _c, _i in OPTS]
    for i, (_l, k, c, _i) in enumerate(OPTS):
        a.bar(i, vals[i], width=0.68, color=c, hatch=F.HATCH[i], edgecolor="white", lw=0.7)
        lab = f"{vals[i]:.2f}" if max(vals) < 1.5 else f"{vals[i]:,.1f}"
        a.text(i, vals[i] + max(max(vals), 0.01) * 0.05, lab.rstrip("0").rstrip(".") if "." in lab else lab,
               ha="center", va="bottom", fontsize=6.6, fontweight="bold", color=c)
    a.set_title(title, fontsize=6.6, color=F.NAVY, pad=4)
    a.set_xticks(range(3)); a.set_xticklabels(["A", "B", "C"], fontsize=7)
    a.set_ylim(0, max(max(vals) * 1.30, 0.01))
    a.set_yticks([]); a.grid(False)
    F.despine(a, keep=("bottom",))
    a.text(0.5, -0.30, "higher is better" if good_high else "lower is better",
           transform=a.transAxes, ha="center", fontsize=5.8, color=F.GREY, style="italic")
handles = [plt.Rectangle((0, 0), 1, 1, fc=c, hatch=F.HATCH[i], ec="white")
           for i, (_l, _k, c, _ii) in enumerate(OPTS)]
fig.legend(handles, [l.replace("\n", " ") for l, _k, _c, _i in OPTS],
           loc="lower center", ncol=3, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.13))
F.source(fig, "\nImpacts read from round_configs.ROUND_CONFIGS[7] at commit 0ad1246. The OPEX cut is "
              f"ECONOMIC_CIRCULAR_ECONOMY_BONUS ({BONUS:.0%}) applied to every unit's opening opex base, which "
              "_post_r7_circularity grants to options A and B only. C's synergy boost of 0.30 is then scaled by "
              "workforce readiness — 0.70 below 40, 1.00 from 40 to 60, 1.10 at 60 or above — and it is the only "
              "route to the Round 10 Resist & Integrate option.")
F.save(fig, "fig07_03_r7_options")
print("ch07 done")
