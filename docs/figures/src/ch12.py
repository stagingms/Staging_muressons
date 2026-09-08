import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import bu_profiles as BP, config as C

BUS = ["pharma", "electronics", "consumer_goods", "software"]
REV = sum(BP.BU_PROFILES[b]["revenue_base"] for b in BUS) / 1e6
OPX = sum(BP.BU_PROFILES[b]["opex_base"] for b in BUS) / 1e6
GOV = {b: BP.BU_PROFILES[b]["governance_risk_score"] for b in BUS}
OPXb = {b: BP.BU_PROFILES[b]["opex_base"] for b in BUS}
CONT = sum(OPXb[b] * sum(GOV[o] for o in BUS if o != b) * C.SUPPLY_CHAIN_OVERLAP_COEFF
           for b in BUS) / 1e6

# ══ Figure 12.1 — the treasury waterfall, annotated ══════════════════════
STEPS = [
 ("Opening treasury", 50.0, "total", "SIM_INITIAL_BUDGET"),
 ("Gross profit (CSF)\nrevenue − OPEX", REV - OPX, "up",
  F.esc(f"${REV:.1f}m − ${OPX:.1f}m")),
 ("Supply-chain\ncontagion surcharge", -CONT, "down",
  "every unit's OPEX carries\nthe others' governance risk"),
 ("Brain-drain premium\n(Software)", -0.83, "down", "reputation below 65"),
 ("CapEx paid in cash", -10.0, "down", "the 20% investment allowance"),
 ("Carbon and climate\ncharges", 0.0, "flat", "nil at the opening tier"),
 ("Regulatory\nratchet fine", 0.0, "flat", "nil until Round 9"),
 ("Closing treasury", None, "total", "opening + every entry"),
]
vals, running = [], 50.0
for name, v, kind, note in STEPS:
    if kind == "total" and v is not None:
        vals.append((name, running, running, kind, note))
    elif kind == "total":
        vals.append((name, running, running, kind, note))
    else:
        vals.append((name, running, running + v, kind, note))
        running += v
fig, ax = F.newfig(h=3.9)
xs = np.arange(len(vals))
for i, (name, y0, y1, kind, note) in enumerate(vals):
    if kind == "total":
        ax.bar(i, y1, width=0.62, color=F.NAVY, edgecolor="white", lw=0.8)
        ax.text(i, y1 + 0.9, F.esc(f"${y1:.2f}m"), ha="center", va="bottom",
                fontsize=7.6, fontweight="bold", color=F.NAVY)
    elif kind == "flat":
        ax.plot([i - 0.31, i + 0.31], [y0, y0], color=F.GREY, lw=2.2)
        ax.text(i, y0 + 0.9, "nil", ha="center", va="bottom", fontsize=7,
                color=F.GREY, fontweight="bold")
    else:
        col = F.TEAL if y1 > y0 else F.RUST
        ax.bar(i, y1 - y0, bottom=y0, width=0.62, color=col,
               hatch="///" if y1 < y0 else "", edgecolor="white", lw=0.8)
        ax.text(i, max(y0, y1) + 0.9, F.esc(f"{y1-y0:+.2f}m"), ha="center", va="bottom",
                fontsize=7, fontweight="bold", color=col)
    if i < len(vals) - 1:
        ax.plot([i + 0.31, i + 1 - 0.31], [y1, y1], color=F.GREY, lw=0.8, ls=(0, (2, 2)))
    ax.text(i, -6.2, note, ha="center", va="top", fontsize=5.7, color=F.GREY)
ax.set_xticks(xs); ax.set_xticklabels([v[0] for v in vals], fontsize=6.6)
ax.set_ylabel(F.esc("treasury, $m")); ax.set_ylim(0, 68)
ax.grid(axis="x", visible=False); F.despine(ax)
ax.set_title("The Round 1 treasury bridge, at the opening state and a full allowance of capex",
             loc="left", color=F.NAVY, fontsize=8.8)
F.source(fig, "The named ledger described in §12.2.3, executed on the opening state at commit 0ad1246. "
              "Gross profit is group revenue less group OPEX. The contagion surcharge is "
              "engine.calc_supply_chain_contagion summed across the four units. CapEx assumes the team "
              "spends its whole Round 1 Corporate Strategic Fund. Carbon, climate and ratchet lines are nil "
              "at Round 1 and are drawn as flat markers rather than omitted, because a bridge that omits its "
              "zero rows cannot be reconciled — which is the point of §12.2.3's closing paragraph.")
F.save(fig, "fig12_01_waterfall")

# ══ Figure 12.2 — the three statements and their articulation points ═════
fig, ax = F.newfig(h=4.7)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
COLW = 0.300
X = [0.005, 0.350, 0.695]
TITLES = ["INCOME STATEMENT", "CASH FLOW", "BALANCE SHEET"]
for j, t in enumerate(TITLES):
    ax.text(X[j] + COLW / 2, 0.985, t, ha="center", va="top", fontsize=7.6,
            fontweight="bold", color=F.NAVY)
IS = [("Revenue", F.esc(f"${REV:.1f}m")), ("Operating expense", F.esc(f"({OPX:.1f}m)")),
      ("EBITDA", F.esc(f"${REV-OPX:.1f}m")), ("Depreciation", "(non-cash)"),
      ("Interest", "base + NCD × 0.0001"), ("Net income", "the plug into equity")]
CF = [("Operating", "EBITDA, working capital"), ("+ depreciation", "added back"),
      ("Investing", "capex, offsets purchased"), ("Financing", "loans, emergency credit"),
      ("Net movement", "the treasury bridge")]
BSA = [("Cash", F.esc("$30.0m")), ("PPE", F.esc("$25.3m")), ("Intangibles", F.esc("$58.0m")),
       ("Working capital", F.esc("$13.4m"))]
BSL = [("Revolver", F.esc("$50.0m")), ("Provisions", F.esc("$8.0m")),
       ("Leases", F.esc("$18.7m")), ("Equity", F.esc("$35.0m")),
       ("Retained earnings", "derived")]
def col(j, items, y0, label=None):
    rh = 0.088
    if label:
        ax.text(X[j] + 0.006, y0 + 0.012, label, fontsize=6.4, fontweight="bold",
                color=F.GREY)
        y0 -= 0.045
    ys = []
    for i, (nm, sub) in enumerate(items):
        y = y0 - i * rh
        F.box(ax, X[j], y - rh * 0.42, COLW, rh * 0.82, f"{nm}   {sub}",
              fc=F.PALE, ec=F.GREY, tc=F.INK, size=6.4)
        ys.append(y)
    return ys
ys_is = col(0, IS, 0.905)
ys_cf = col(1, CF, 0.905)
ys_a = col(2, BSA, 0.905, "ASSETS")
ys_l = col(2, BSL, 0.905 - 0.045 - len(BSA) * 0.088 - 0.030, "LIABILITIES AND EQUITY")
ART = [((0, 2), (1, 0), "EBITDA opens the\ncash statement", F.TEAL),
       ((0, 3), (1, 1), "depreciation is\nadded back", F.RUST),
       ((1, 4), (2, 0), "net movement lands\nin cash", F.NAVY),
       ((0, 5), (2, 8), "net income is the only\nroute into equity", F.RUST)]
for (c0, i0), (c1, i1), note, colr in ART:
    y_from = [ys_is, ys_cf][c0][i0] if c0 < 2 else 0
    y_to = ([ys_cf, ys_a + ys_l][c1 - 1][i1] if c1 >= 1 else 0)
    if c1 == 2:
        y_to = (ys_a + ys_l)[i1]
    F.arrow(ax, (X[c0] + COLW, y_from), (X[c1], y_to), color=colr, rad=0.16, lw=1.3)
ax.text(0.005, 0.245, "The three arrows are the articulation\npoints. Break any one and the three\n"
                      "statements stop being one document.\n\n"
                      "§12.3.4's retained-earnings plug is the\nfourth, and the chapter is candid that\n"
                      "the model derives it rather than\naccumulating it round by round.",
        fontsize=6.7, color=F.RUST, style="italic", va="top",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=F.RUST, lw=0.7))
F.source(fig, "Line items and opening balances as tabulated in Chapter 12 §12.3.1, computed on the opening "
              "state at commit 0ad1246. The articulation points are the standard four; §12.3.4 records that "
              "the retained-earnings line is derived as a plug rather than accumulated round by round, which "
              "is the one place the model departs from a real set of statements.")
F.save(fig, "fig12_02_three_statements")

# ══ Figure 12.3 — where each non-financial metric lands ══════════════════
METRICS = [
 ("Carbon intensity", ["Operating expense", "Terminal EBITDA", "Cost of capital"]),
 ("Natural capital debt", ["Interest expense", "Provisions", "Operating expense"]),
 ("Water dependency", ["Cost of capital"]),
 ("Burnout", ["Operating expense", "Terminal multiplier"]),
 ("Workforce readiness", ["Terminal multiplier", "Operating expense"]),
 ("Social licence", ["Revenue", "Operating expense", "Terminal multiplier"]),
 ("Reputation", ["Intangible assets", "Operating expense"]),
 ("Governance risk", ["Operating expense", "Revenue", "Cost of capital"]),
 ("Synergy multiplier", ["Operating expense", "Terminal multiplier"]),
 ("Supply-chain transparency", ["Cost of capital"]),
]
LINES = ["Revenue", "Operating expense", "Interest expense", "Intangible assets",
         "Provisions", "Cost of capital", "Terminal EBITDA", "Terminal multiplier"]
LCOL = {"Revenue": F.TEAL, "Operating expense": F.RUST, "Interest expense": F.RUST,
        "Intangible assets": F.NAVY, "Provisions": F.NAVY, "Cost of capital": F.SERIES[3],
        "Terminal EBITDA": F.SERIES[4], "Terminal multiplier": F.SERIES[4]}
fig, ax = F.newfig(h=4.6)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
LX, CELL = 0.255, 0.0905
for j, ln in enumerate(LINES):
    ax.text(LX + (j + 0.5) * CELL, 1.005, ln.replace(" ", "\n"), ha="center", va="top",
            fontsize=6.1, fontweight="bold", color=LCOL[ln])
rh = 0.0755
for i, (m, lands) in enumerate(METRICS):
    y = 0.865 - (i + 1) * rh
    ax.text(0.005, y + rh / 2, m, fontsize=6.9, color=F.INK, va="center")
    ax.add_patch(plt.Rectangle((0.0, y + 0.004), 1.0, rh - 0.010,
                               fc=F.PALE if i % 2 == 0 else "white", ec="none", zorder=0))
    ax.text(0.005, y + rh / 2, m, fontsize=6.9, color=F.INK, va="center", zorder=2)
    for j, ln in enumerate(LINES):
        cx = LX + (j + 0.5) * CELL
        if ln in lands:
            ax.plot([cx], [y + rh / 2], marker="o", ms=6.0, color=LCOL[ln], zorder=3)
        else:
            ax.plot([cx], [y + rh / 2], marker="_", ms=3.6, color="#D2DAE1", zorder=3)
counts = {ln: sum(1 for _m, l in METRICS if ln in l) for ln in LINES}
for j, ln in enumerate(LINES):
    ax.text(LX + (j + 0.5) * CELL, 0.055, str(counts[ln]), ha="center", fontsize=8,
            fontweight="bold", color=LCOL[ln])
ax.text(0.005, 0.055, "metrics reaching this line:", fontsize=6.6, color=F.GREY, va="center")
ax.text(0.005, 0.012, "Operating expense carries seven of the ten. The second ledger reaches the first "
                      "mostly through cost, not through revenue.",
        fontsize=6.8, color=F.RUST, style="italic")
F.source(fig, "The routing tabulated in Chapter 12 §12.6, which names the mechanism for each metric; the "
              "counts are of that table. Every mechanism behind a mark is a function in the build at commit "
              "0ad1246 — the burnout penalty, the NCD interest coefficient, the nature premium, the "
              "supply-chain contagion surcharge, the brand-value formula and the synergy engine.")
F.save(fig, "fig12_03_metric_to_line")
print("ch12 done")
