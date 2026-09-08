import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import bu_profiles as BP, pillar_configs as PC

BUS = ["pharma", "electronics", "consumer_goods", "software"]
NAME = {"pharma": "Pharma", "electronics": "Electronics",
        "consumer_goods": "Consumer Goods", "software": "Software"}
REV = {b: BP.BU_PROFILES[b]["revenue_base"] / 1e6 for b in BUS}
CI = {b: BP.BU_PROFILES[b]["carbon_intensity"] for b in BUS}
TOT_REV = sum(REV.values())
TONNES = {b: CI[b] * REV[b] for b in BUS}
TOT_T = sum(TONNES.values())
# the engine's own scope split, admin_router.py
SCOPE = {"pharma": (35, 25, 40), "electronics": (10, 15, 75),
         "consumer_goods": (15, 10, 75), "software": (5, 60, 35)}

# ══ Figure 5.1 — scope boundaries on the Muressons value chain ═════════════
fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.25),
                             gridspec_kw=dict(width_ratios=[1.0, 1.05], wspace=0.30))
y = np.arange(len(BUS))[::-1]
SC_COL = [F.NAVY, F.TEAL, F.RUST]
SC_H = ["", "///", "..."]
for i, b in enumerate(BUS):
    left = 0
    for k, s in enumerate(SCOPE[b]):
        a1.barh(y[i], s, left=left, height=0.62, color=SC_COL[k], hatch=SC_H[k],
                edgecolor="white", lw=0.8)
        if s >= 12:
            a1.text(left + s / 2, y[i], f"{s}%", ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold")
        left += s
a1.set_yticks(y); a1.set_yticklabels([NAME[b] for b in BUS], fontsize=7.6)
a1.set_xlim(0, 100); a1.set_xlabel("Share of the unit's tonnes, %")
a1.grid(axis="y", visible=False); F.despine(a1)
for k, lab in enumerate(["Scope 1 — what you burn", "Scope 2 — what was burned for your power",
                         "Scope 3 — everything else in the chain"]):
    a1.plot([], [], color=SC_COL[k], lw=6, label=lab)
a1.legend(loc="lower center", bbox_to_anchor=(0.5, -0.52), fontsize=6.6, ncol=1,
          handlelength=1.4, borderpad=0.2)
a1.set_title("The split each unit carries", loc="left", color=F.NAVY, fontsize=8.8)

order = sorted(BUS, key=lambda b: -TONNES[b])
for i, b in enumerate(order):
    yy = len(order) - 1 - i
    left = 0
    for k, s in enumerate(SCOPE[b]):
        t = TONNES[b] * s / 100
        a2.barh(yy, t, left=left, height=0.62, color=SC_COL[k], hatch=SC_H[k],
                edgecolor="white", lw=0.8)
        left += t
    a2.text(TONNES[b] + 22, yy, f"{TONNES[b]:,.0f} t", va="center", fontsize=7.2,
            color=F.INK, fontweight="bold")
a2.set_yticks(range(len(order)))
a2.set_yticklabels([NAME[b] for b in order][::-1], fontsize=7.6)
a2.set_xlabel("tCO$_2$e at the opening state")
a2.set_xlim(0, 1420)
a2.grid(axis="y", visible=False); F.despine(a2)
a2.set_title(f"The same split in tonnes — group total {TOT_T:,.0f} t", loc="left",
             color=F.NAVY, fontsize=8.8)
F.source(fig, "Scope ratios: the engine's own per-unit split (admin_router.py) at commit 0ad1246. Tonnes are "
              "carbon_intensity × revenue in $m, the formula database.py uses for baseline_tco2e — Pharma 35 × 18, "
              "Electronics 72 × 16.5, Consumer Goods 48 × 10.5, Software 12 × 8.5, giving the 2,424 t of §5.3.2. "
              "Electronics is a quarter of group revenue and half the group's carbon.")
F.save(fig, "fig05_01_scopes")

# ══ Figure 5.2 — a MACC built from the Energy pillar ═══════════════════════
# One intensity point routes as d x num_bus x revenue_share to each unit, so the
# group tonnage move is NOT 53.5 t/point (uniform) but the revenue-weighted form.
n_bu = len(BUS)
T_PER_POINT = sum(n_bu * (REV[b] / TOT_REV) * REV[b] for b in BUS)
opts = []
for r in range(1, 11):
    area = PC.PILLAR_OPTIONS[r]["areas"].get("energy")
    if not area:
        continue
    for ok, o in area["options"].items():
        d = o.get("impacts", {}).get("carbon_intensity_delta")
        if d and d < 0:
            tonnes = abs(d) * T_PER_POINT
            opts.append((r, o["title"], abs(o["cost"]), abs(d), tonnes,
                         abs(o["cost"]) / tonnes))
opts.sort(key=lambda x: x[5])
fig, ax = F.newfig(h=3.9)
x = 0.0
for i, (r, title, cost, d, tonnes, per_t) in enumerate(opts):
    col = F.SERIES[i % len(F.SERIES)]
    ax.bar(x + tonnes / 2, per_t, width=tonnes * 0.94, color=col,
           hatch=F.HATCH[i % len(F.HATCH)], edgecolor="white", lw=0.7)
    ax.text(x + tonnes / 2, per_t + 120, f"R{r}", ha="center", va="bottom",
            fontsize=6.6, color=col, fontweight="bold")
    x += tonnes
ax.axhline(250, color=F.RUST, lw=1.4)
ax.text(x * 0.015, 620, F.esc("the price the terminal actually charges: $250 a tonne"),
        ha="left", va="bottom", fontsize=7.4, color=F.RUST, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=F.RUST, lw=0.7))
ax.set_xlabel("Cumulative tonnes abated at the opening state, tCO$_2$e")
ax.set_ylabel("Cost of abatement, $ per tonne")
ax.set_xlim(0, x * 1.02); ax.set_ylim(0, max(o[5] for o in opts) * 1.22)
F.despine(ax)
ax.set_title("Every abatement option in the game costs more than the tonne is worth to it",
             loc="left", color=F.NAVY)
lines = [f"R{r:<2} {t[:30]:32s} {c/1e6:>4.1f}m  {d:>3.0f} pts  {tn:>6,.0f} t  {pt:>7,.0f}/t"
         for r, t, c, d, tn, pt in opts]
hdr = f"{'':3s} {'option':32s} {'cost':>5s}  {'pts':>7s}  {'tonnes':>8s}  {'$/tonne':>9s}"
ax.text(0.015, 0.97, F.esc(hdr + "\n" + "\n".join(lines)), transform=ax.transAxes, va="top", ha="left",
        fontsize=5.6, family="monospace", color=F.INK,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=F.GREY, lw=0.6, alpha=0.94))
F.source(fig, "Options: the Energy area of pillar_configs.PILLAR_OPTIONS at commit 0ad1246 — thirteen "
              "carbon-reducing options across seven of the ten rounds (§5.4.2 says eight; Rounds 5, 8 and 9 carry "
              "an Energy area whose options all have no carbon_intensity_delta). Tonnes per intensity point are "
              f"computed from the engine's actual routing, delta x 4 x revenue share per unit, giving "
              f"{T_PER_POINT:.1f} t a point on the opening portfolio — not the 53.5 t a uniform application "
              "would give. The $250 line is FINANCIAL_SHADOW_CARBON_PRICE.")
F.save(fig, "fig05_04_macc")

# ══ Figure 5.3 — the terminal line, at three prices ════════════════════════
GROSS = sum((BP.BU_PROFILES[b]["revenue_base"] - BP.BU_PROFILES[b]["opex_base"]) for b in BUS)
PRICES = [("Standard\nshadow price", 250, F.NAVY),
          ("Regulatory Shutdown\nending", 350, F.RUST),
          ("Climate Black Swan\nending", 750, "#7A2E12")]
PROFILES = [("Opening state\nintensity 45.3, 2,424 t", 2424, "-", ""),
            ("Decarbonised to Chapter 14's\n'good' profile: intensity 31, 1,659 t", 1659, "--", "///")]
fig, ax = F.newfig(h=3.4)
w = 0.36
xs = np.arange(len(PRICES))
for k, (plab, tonnes, ls, hatch) in enumerate(PROFILES):
    vals = [tonnes * p / 1000 for _l, p, _c in PRICES]
    ax.bar(xs + (k - 0.5) * w, vals, width=w * 0.92,
           color=[c for _l, _p, c in PRICES], alpha=1.0 if k == 0 else 0.55,
           hatch=hatch, edgecolor="white", lw=0.8, label=plab)
    for i, v in enumerate(vals):
        ax.text(xs[i] + (k - 0.5) * w, v + 22,
                f"${v:,.0f}k\n{v*1000/GROSS*100:.1f}% of gross profit",
                ha="center", va="bottom", fontsize=6.6, color=F.INK)
ax.set_xticks(xs); ax.set_xticklabels([l for l, _p, _c in PRICES], fontsize=7.6)
ax.set_ylabel("Terminal carbon cost, $ thousand")
ax.set_ylim(0, 2250)
ax.grid(axis="x", visible=False); F.despine(ax)
ax.legend(fontsize=6.8, loc="upper left", handlelength=1.3)
ax.set_title("The terminal carbon line, at the three prices the engine can charge",
             loc="left", color=F.NAVY)
F.source(fig, "terminal carbon cost = tonnes × price. The price is a flat $250 a tonne "
              "(FINANCIAL_SHADOW_CARBON_PRICE), overridden to $350 on the Regulatory Shutdown ending and $750 on "
              f"the Climate Black Swan ending. Opening tonnage 2,424 t; opening gross profit ${GROSS/1e6:.1f}m. "
              "The outline and the Player Briefing's first draft described this as '$50 escalating 5% a year'; "
              "it is not, and never was — §5.3.2.")
F.save(fig, "fig05_03_terminal_carbon")

# ══ Figure 5.4 — the fifteen Scope 3 categories ════════════════════════════
CATS = [
 (1, "Purchased goods and services", "up", "Electronics",
  "75% of its tonnes are Scope 3 and its carbon is in bought components (CI 72, the group's highest)"),
 (2, "Capital goods", "up", "Pharma",
  "the most capital-intensive unit — process chemistry plant; opex base $12.0m, the group's largest"),
 (3, "Fuel- and energy-related activities", "up", "Software",
  "60% Scope 2, the group's highest — its upstream fuel chain scales with that draw"),
 (4, "Upstream transport and distribution", "up", "Consumer Goods",
  "75% Scope 3 on a physical, distributed product line"),
 (5, "Waste generated in operations", "up", "Electronics",
  "e_waste_impact is a Q1 issue in the Round 2 dictionary and is electronics_sensitive"),
 (6, "Business travel", "up", "— group —",
  "modelled only as the exec_travel distractor in CSRD_ISSUES: <0.01% of group emissions"),
 (7, "Employee commuting", "up", "— none —", "no mechanic in the build"),
 (8, "Upstream leased assets", "up", "— none —", "no mechanic in the build"),
 (9, "Downstream transport and distribution", "down", "Consumer Goods",
  "the plastic_packaging / EPR levy route runs through its distribution"),
 (10, "Processing of sold products", "down", "Pharma",
  "an intermediate-goods producer; API leakage is a Q1 issue on its output"),
 (11, "Use of sold products", "down", "Software",
  "data-centre draw at use is the unit's dominant carbon story (Green Data Centers, R6)"),
 (12, "End-of-life treatment of sold products", "down", "Consumer Goods",
  "plastic_waste_impact, Q1; the R7 circularity options act here"),
 (13, "Downstream leased assets", "down", "— none —", "no mechanic in the build"),
 (14, "Franchises", "down", "— none —", "no mechanic in the build"),
 (15, "Investments", "down", "— none —",
  "financed emissions appear only if the Banking vertical takes the Software slot"),
]
fig, ax = F.newfig(h=5.3)
F.nogrid(ax)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
n = len(CATS)
rh = 0.058
top = 0.945
BU_COL = {"Pharma": F.NAVY, "Electronics": F.TEAL, "Consumer Goods": F.RUST,
          "Software": F.SERIES[3], "— group —": F.GREY, "— none —": F.GREY}
ax.text(0.005, 0.985, "GHG PROTOCOL SCOPE 3 CATEGORY", fontsize=7, fontweight="bold",
        color=F.GREY, va="top")
ax.text(0.415, 0.985, "MOST-EXPOSED UNIT", fontsize=7, fontweight="bold", color=F.GREY, va="top")
ax.text(0.585, 0.985, "WHY — the attribute or mechanic that puts it there", fontsize=7,
        fontweight="bold", color=F.GREY, va="top")
prev = None
for i, (num, title, ud, bu, why) in enumerate(CATS):
    y = top - (i + 1) * rh
    if ud != prev:
        ax.text(0.005, y + rh * 0.95, "UPSTREAM" if ud == "up" else "DOWNSTREAM",
                fontsize=6.6, fontweight="bold", color=F.SERIES[0 if ud == "up" else 2],
                va="bottom")
        prev = ud
        y -= 0.016
        top -= 0.016
    col = BU_COL[bu]
    none = bu.startswith("—")
    ax.text(0.010, y + rh / 2, f"{num:>2}", fontsize=7, color=F.GREY, va="center",
            family="monospace")
    ax.text(0.042, y + rh / 2, title, fontsize=7.1, color=F.INK, va="center")
    ax.add_patch(plt.Rectangle((0.412, y + 0.008), 0.160, rh - 0.016,
                               fc="white" if none else F.PALE, ec=col,
                               lw=0.9, ls=(0, (2, 2)) if none else "-"))
    ax.text(0.492, y + rh / 2, bu, fontsize=6.9, color=col, va="center", ha="center",
            fontweight="bold" if not none else "normal",
            style="italic" if none else "normal")
    ax.text(0.585, y + rh / 2, why, fontsize=6.3, color=F.GREY, va="center")
F.source(fig, "Categories 1–15 and the upstream/downstream split: the GHG Protocol Corporate Value Chain "
              "(Scope 3) Standard. The unit against each is a judgement [J], but each is justified from a stated "
              "attribute of that unit at commit 0ad1246 — its scope split, its carbon intensity, or a named issue "
              "or round option. Five categories have no mechanic in the build at all; the figure says so rather "
              "than assigning them a unit.")
F.save(fig, "fig05_02_scope3_categories")
print("ch05 done")
