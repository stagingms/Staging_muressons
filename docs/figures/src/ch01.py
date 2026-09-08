import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

# ══ Figure 1.1 — the capital-to-money chain ════════════════════════════════
# Rows are the chapter's own table (§1.2.2); the middle column carries the
# variable names as they are spelt in the build.
ROWS = [
    ("Financial",  "corporate_treasury\ncost_of_capital",                    "Directly"),
    ("Manufactured", "revenue_base / opex_base\n(no dedicated stock)",       "Revenue and\ndepreciation"),
    ("Human",      "workforce_readiness\nstaff_burnout_index",               "Operating expense;\nstrike risk; Year-5\nvaluation bonus"),
    ("Social and\nrelationship", "social_license_score\ngroup_reputation",   "Revenue risk; crisis\nseverity; valuation\npenalty to −0.40"),
    ("Intellectual", "vrio_advantage\nsynergy_multiplier",                   "Margin durability;\ndecays each round"),
    ("Natural",    "carbon_intensity  water_dependency\nnatural_capital_debt", "Carbon tax at exit;\ncost of debt;\nregulatory exposure"),
]

fig, ax = F.newfig(h=4.6)
F.nogrid(ax)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
n = len(ROWS)
h = 0.128
gap = (1.0 - n * h) / (n + 1)
xs = [0.005, 0.235, 0.665]
ws = [0.205, 0.400, 0.330]
ax.text(xs[0] + ws[0] / 2, 0.985, "CAPITAL", ha="center", va="top", fontsize=8,
        fontweight="bold", color=F.GREY)
ax.text(xs[1] + ws[1] / 2, 0.985, "MURESSONS STATE VARIABLE", ha="center", va="top",
        fontsize=8, fontweight="bold", color=F.GREY)
ax.text(xs[2] + ws[2] / 2, 0.985, "HOW IT BECOMES MONEY", ha="center", va="top",
        fontsize=8, fontweight="bold", color=F.GREY)
for i, (cap, var, money) in enumerate(ROWS):
    y = 1.0 - (i + 1) * (h + gap) - 0.035
    col = F.SERIES[i % len(F.SERIES)]
    dashed = "--" if cap == "Manufactured" else "-"
    F.box(ax, xs[0], y, ws[0], h, cap, fc="white", ec=col, tc=col, size=8.2, weight="bold", lw=1.4)
    F.box(ax, xs[1], y, ws[1], h, var, fc=F.PALE, ec=col, tc=F.INK, size=7.4, ls=dashed)
    F.box(ax, xs[2], y, ws[2], h, money, fc="white", ec=F.GREY, tc=F.INK, size=7.4)
    F.arrow(ax, (xs[0] + ws[0], y + h / 2), (xs[1], y + h / 2), color=col)
    F.arrow(ax, (xs[1] + ws[1], y + h / 2), (xs[2], y + h / 2), color=col)
F.source(fig, "Rows: the chapter's own table, §1.2.2. Variable names as spelt in engine commit 0ad1246 "
              "(GlobalStateOut, BUStateOut, ENGINE_STATE_KEYS). Manufactured is the one capital with no "
              "dedicated stock variable: it is carried by the revenue and opex bases (dashed).")
F.save(fig, "fig01_01_capitals_chain")

# ══ Figure 1.2 — salience, with the roster placed ══════════════════════════
import npc_stakeholders as NPC
ROSTER = [(v["name"], v["salience"]) for v in NPC.NPC_PROFILES.values()]
HAS = 0.40   # the engine's own cut: _leverage_label calls anything below 0.40 "low"

NAMES = {
    (1,0,0): ("1", "Dormant",        "power only"),
    (0,1,0): ("2", "Discretionary",  "legitimacy only"),
    (0,0,1): ("3", "Demanding",      "urgency only"),
    (1,1,0): ("4", "Dominant",       "power + legitimacy"),
    (1,0,1): ("5", "Dangerous",      "power + urgency, no legitimacy"),
    (0,1,1): ("6", "Dependent",      "legitimacy + urgency, no power"),
    (1,1,1): ("7", "Definitive",     "all three"),
}
r, d = 1.0, 0.60
C = [(0.0, d), (-d*0.866, -d*0.5), (d*0.866, -d*0.5)]     # Power, Legitimacy, Urgency
STY = [(F.NAVY, "-"), (F.TEAL, "--"), (F.RUST, "-.")]

def cls(s):
    return (s["power"] >= HAS, s["legitimacy"] >= HAS, s["urgency"] >= HAS)

occupants = {k: [] for k in NAMES}
for name, sal in ROSTER:
    k = tuple(int(b) for b in cls(sal))
    if k in occupants:
        occupants[k].append(f"{name} ({sal['power']:.2f} / {sal['legitimacy']:.2f} / {sal['urgency']:.2f})")

fig = plt.figure(figsize=(F.TEXT_WIDTH_IN, 5.5))
ax = fig.add_axes([0.185, 0.455, 0.63, 0.525])
F.nogrid(ax)
ax.set_xlim(-2.05, 2.05); ax.set_ylim(-1.95, 2.00); ax.set_aspect("equal")
for (cx, cy), (col, ls) in zip(C, STY):
    ax.add_patch(Circle((cx, cy), r, fill=False, ec=col, lw=1.9, ls=ls))
ax.text(0, d + r + 0.13, "POWER", ha="center", va="bottom", fontsize=9.5,
        fontweight="bold", color=F.NAVY)
ax.text(-d*0.866 - r*0.80, -d*0.5 - r*0.80, "LEGITIMACY", ha="right", va="top",
        fontsize=9.5, fontweight="bold", color=F.TEAL)
ax.text(d*0.866 + r*0.80, -d*0.5 - r*0.80, "URGENCY", ha="left", va="top",
        fontsize=9.5, fontweight="bold", color=F.RUST)

pts = F.venn_label_points(C, r)
for key, (num, cname, _) in NAMES.items():
    kk = tuple(bool(x) for x in key)
    if kk not in pts:
        continue
    x, y = pts[kk]
    filled = bool(occupants[key])
    ax.scatter([x], [y], s=210, marker="o",
               facecolor=(F.PALE if filled else "white"),
               edgecolor=(F.NAVY if filled else F.GREY),
               linewidth=(1.6 if filled else 0.9), zorder=4)
    ax.text(x, y, num, ha="center", va="center", fontsize=8.5, zorder=5,
            fontweight="bold", color=(F.NAVY if filled else F.GREY))
    if not filled:
        ax.text(x, y - 0.24, "empty", ha="center", va="top", fontsize=6.6,
                color=F.GREY, style="italic", zorder=5)
ax.set_title("The eight salience classes, and where the Muressons roster actually sits",
             loc="center", color=F.NAVY, pad=2)

# key beneath the diagram
kx = fig.add_axes([0.005, 0.015, 0.99, 0.415]); F.nogrid(kx)
kx.set_xlim(0, 1); kx.set_ylim(0, 1)
rows = [(NAMES[k][0], NAMES[k][1], NAMES[k][2], occupants[k]) for k in
        [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(1,1,1)]]
yy = 0.97
for num, cname, defn, occ in rows:
    hot = cname == "Dangerous"
    filled = bool(occ)
    col = F.RUST if (hot and not filled) else (F.NAVY if filled else F.GREY)
    kx.text(0.012, yy, num, fontsize=7.6, fontweight="bold", color=col, va="top")
    kx.text(0.045, yy, cname, fontsize=7.6, fontweight="bold", color=col, va="top")
    kx.text(0.175, yy, defn, fontsize=7.2, color=F.GREY, va="top")
    if filled:
        kx.text(0.435, yy, ";  ".join(occ), fontsize=7.2, color=F.INK, va="top")
    else:
        kx.text(0.435, yy, "— nobody in the Muressons roster —"
                + ("   the cell §1.6.2 calls systematically under-managed" if hot else ""),
                fontsize=7.2, color=col, va="top", style="italic")
    yy -= 0.123
kx.text(0.012, yy - 0.035,
        "Triples are (power / legitimacy / urgency). A stakeholder counts as holding an attribute at 0.40 or above — "
        "the engine's own cut, since\n_leverage_label calls anything below 0.40 'low'. Mehta sits exactly on it at 0.40 "
        "urgency; Patil's power of 0.30 is the roster's only 'low'.",
        fontsize=6.9, color=F.GREY, va="top", style="italic")
F.source(fig, "Three attributes and eight classes: Mitchell, Agle & Wood (1997). Triples read verbatim from "
              "npc_stakeholders.NPC_PROFILES at engine commit 0ad1246 — the build stores exactly these three "
              "attributes per stakeholder, so the taxonomy is the data model, not a gloss on it.")
F.save(fig, "fig01_02_salience")

# ══ Figure 1.3 — what one Round 1 pillar decision costs ════════════════════
import pillar_configs as PC
import config as CFG
areas = PC.PILLAR_OPTIONS[1]["areas"]
order = ["energy", "operations", "supply_chain", "offsetting", "human_resources"]
labels, costs, notes, groups = [], [], [], []
for gi, ak in enumerate(order):
    a = areas[ak]
    for ok, o in sorted(a["options"].items(), key=lambda kv: kv[1]["cost"]):
        labels.append(o["title"])
        costs.append(abs(o["cost"]) / 1e6)
        imp = o.get("impacts", {})
        bits = []
        for k, short in (("carbon_intensity_delta", "CI"), ("reputation", "rep"),
                         ("social_license_delta", "SLO"), ("governance_risk_delta", "gov"),
                         ("natural_capital_debt_delta", "NCD"), ("burnout_delta", "burnout")):
            if k in imp:
                bits.append(f"{short} {imp[k]:+g}")
        notes.append("  ".join(bits) if bits else "no impacts")
        groups.append(gi)

fig, ax = F.newfig(h=5.4)
ypos, cur, g_prev = [], 0.0, None
for g in groups:
    if g_prev is not None and g != g_prev:
        cur += 1.15                      # breathing room between pillars
    ypos.append(cur); cur += 1.0; g_prev = g
y = np.array([max(ypos) - v for v in ypos])
for i, (c, g) in enumerate(zip(costs, groups)):
    ax.barh(y[i], c, height=0.66, color=F.SERIES[g % len(F.SERIES)],
            hatch=F.HATCH[g % len(F.HATCH)], edgecolor="white", linewidth=0.6)
    ax.text(c + 0.06, y[i], f"${c:.1f}m   {notes[i]}", va="center", fontsize=6.9, color=F.INK)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=7.2)
ax.set_xlabel("Cash cost of the option, $m")
ax.set_xlim(0, 6.4)
ax.grid(axis="y", visible=False)
F.despine(ax)
prev = None
for i, g in enumerate(groups):
    if g != prev:
        ax.text(-0.06, y[i] + 0.90, areas[order[g]]["label"].upper(), fontsize=7.4,
                fontweight="bold", color=F.SERIES[g % len(F.SERIES)], ha="right", va="center")
        prev = g
ax.set_title("Round 1: fifteen options, five pillars, one budget", loc="left", color=F.NAVY)
tot_max = sum(max(abs(o["cost"]) for o in areas[a]["options"].values()) for a in order) / 1e6
csf = max(CFG.SIM_INITIAL_BUDGET * CFG.CSF_POOL_TREASURY_FRACTION, CFG.CSF_POOL_FLOOR) / 1e6
ax.text(0.99, 0.02, f"Round 1 Corporate Strategic Fund: ${csf:.1f}m\n"
                    f"Most expensive option in every pillar: ${tot_max:.1f}m",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=7.6, color=F.RUST,
        fontweight="bold", bbox=dict(boxstyle="round,pad=0.35", fc=F.PALE, ec=F.RUST, lw=0.8))
F.source(fig, "Options, costs and impacts: pillar_configs.PILLAR_OPTIONS[1] at engine commit 0ad1246. "
              f"CSF pool = max(treasury × {CFG.CSF_POOL_TREASURY_FRACTION:.0%}, "
              f"${CFG.CSF_POOL_FLOOR/1e6:.0f}m) on an opening treasury of ${CFG.SIM_INITIAL_BUDGET/1e6:.0f}m. "
              "The gap between the two figures is the opportunity cost of §1.7.1, in dollars.")
F.save(fig, "fig01_03_pillar_cost")
print("ch01 done")
