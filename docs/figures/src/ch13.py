import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import engine as E, bu_profiles as BP

MACRO = E._MACRO_RATE_CYCLES
def multiple(wacc, g=0.02, lo=6.0, hi=18.0):
    return max(lo, min(hi, (1 + g) / (wacc - g)))

# ══ Figure 13.1 — the WACC bridge ════════════════════════════════════════
STEPS = [("Base rate", 5.00, "total"),
         ("Carbon premium\n(CI 45.31 − 40) × 0.0008", 0.42, "up"),
         ("Governance premium\nmean 17.5, below the 25 floor", 0.00, "flat"),
         ("Licence discount\nmean 50, at the 50 floor", 0.00, "flat"),
         ("Nature premium\n(54.25÷100) × 0.70 × 0.02", 0.76, "up"),
         ("Cost of capital", None, "total")]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.4),
                             gridspec_kw=dict(width_ratios=[1.28, 1.0], wspace=0.32))
run = 0.0
for i, (nm, v, kind) in enumerate(STEPS):
    if kind == "total":
        val = 5.00 if v is not None else run
        if v is None:
            a1.bar(i, run, width=0.60, color=F.NAVY, edgecolor="white", lw=0.8)
            a1.text(i, run + 0.14, f"{run:.2f}%", ha="center", va="bottom",
                    fontsize=8.4, fontweight="bold", color=F.NAVY)
        else:
            run = v
            a1.bar(i, run, width=0.60, color=F.NAVY, edgecolor="white", lw=0.8)
            a1.text(i, run + 0.14, f"{run:.2f}%", ha="center", va="bottom",
                    fontsize=8.4, fontweight="bold", color=F.NAVY)
    elif kind == "flat":
        a1.plot([i - 0.30, i + 0.30], [run, run], color=F.GREY, lw=2.4)
        a1.text(i, run + 0.14, "0", ha="center", va="bottom", fontsize=7.4,
                color=F.GREY, fontweight="bold")
    else:
        a1.bar(i, v, bottom=run, width=0.60, color=F.RUST, hatch="///",
               edgecolor="white", lw=0.8)
        a1.text(i, run + v + 0.14, f"+{v:.2f}", ha="center", va="bottom",
                fontsize=7.6, fontweight="bold", color=F.RUST)
        run += v
    if i < len(STEPS) - 1:
        a1.plot([i + 0.30, i + 0.70], [run, run], color=F.GREY, lw=0.8, ls=(0, (2, 2)))
a1.set_xticks(range(len(STEPS)))
a1.set_xticklabels([s[0] for s in STEPS], fontsize=6.0)
a1.set_ylabel("cost of capital, %"); a1.set_ylim(0, 7.4)
a1.grid(axis="x", visible=False); F.despine(a1)
a1.set_title("The ESG adjustment is 1.18 points, and 0.76 of it is water",
             loc="left", color=F.NAVY, fontsize=8.6)

w = np.linspace(0.03, 0.20, 500)
a2.plot(w * 100, [multiple(x) for x in w], color=F.NAVY, lw=2.1)
a2.axhline(18, color=F.GREY, ls=(0, (2, 2)), lw=1.0)
a2.axhline(6, color=F.GREY, ls=(0, (2, 2)), lw=1.0)
a2.text(19.6, 18.4, "cap 18×", ha="right", fontsize=7, color=F.GREY)
a2.text(19.6, 6.4, "floor 6×", ha="right", fontsize=7, color=F.GREY)
for x, lab in [(6.18, "opening 6.18%"), (7.67, "the cap breaks\nat 7.67%"),
               (9.0, "9%"), (12.0, "12%"), (15.0, "15%")]:
    m = multiple(x / 100)
    a2.plot([x], [m], marker="o", ms=5, color=F.RUST, zorder=5)
    a2.annotate(f"{lab}\n{m:.2f}×", (x, m), textcoords="offset points",
                xytext=(6, 6), fontsize=6.4, color=F.RUST, fontweight="bold")
a2.set_xlabel("cost of capital, %"); a2.set_ylabel("exit multiple, ×")
a2.set_xlim(3, 20); a2.set_ylim(0, 21)
F.despine(a2)
a2.set_title("A cliff the team walks toward, not a live scoreboard",
             loc="left", color=F.NAVY, fontsize=8.6)
F.source(fig, "The WACC terms and their opening values are §6.2.3 and §13.1, executed on the opening state "
              "at commit 0ad1246. The multiple is the Gordon-growth expression (1 + g) ÷ (WACC − g) with "
              "g = 2%, floored at 6× and capped at 18×. The cap binds until 7.67%, which is why the "
              "opening ESG adjustment changes the multiple by nothing at all.")
F.save(fig, "fig13_01_wacc_bridge")

# ══ Figure 13.2 — the four macro regimes ═════════════════════════════════
rounds = np.arange(1, 11)
base = 5.00
esg = 1.18
wacc = [base + MACRO[r] * 100 + esg for r in rounds]
mult = [multiple(x / 100) for x in wacc]
REGIMES = [(1, 2, "easing", -1.0, F.TEAL), (3, 5, "neutral", 0.0, F.GREY),
           (6, 8, "tightening", 1.0, F.RUST), (9, 10, "crisis premium", None, "#7A2E12")]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(F.TEXT_WIDTH_IN, 3.9), sharex=True,
                             gridspec_kw=dict(hspace=0.16))
for lo, hi, lab, mod, col in REGIMES:
    a1.axvspan(lo - 0.5, hi + 0.5, color=col, alpha=0.10)
    a2.axvspan(lo - 0.5, hi + 0.5, color=col, alpha=0.10)
    a1.text((lo + hi) / 2, 8.55, lab, ha="center", fontsize=7, color=col, fontweight="bold")
    txt = f"{mod:+.0f}%" if mod is not None else "+1.5%, +2%"
    a1.text((lo + hi) / 2, 8.15, txt, ha="center", fontsize=6.6, color=col)
a1.plot(rounds, wacc, color=F.NAVY, lw=2.1, marker="o", ms=4.2)
for r, v in zip(rounds, wacc):
    a1.annotate(f"{v:.2f}", (r, v), textcoords="offset points", xytext=(0, -12),
                ha="center", fontsize=6.4, color=F.NAVY)
a1.axhline(7.67, color=F.RUST, ls=(0, (4, 2)), lw=1.1)
a1.text(1.0, 7.78, "7.67% — above this the 18× cap stops binding", fontsize=6.8,
        color=F.RUST, fontweight="bold")
a1.set_ylabel("cost of capital, %"); a1.set_ylim(4.6, 9.0)
F.despine(a1)
a1.set_title("Four macro regimes, on a clean ESG path (adjustment held at the opening 1.18)",
             loc="left", color=F.NAVY, fontsize=8.6)
a2.plot(rounds, mult, color=F.RUST, lw=2.1, marker="s", ms=4.2)
for r, v in zip(rounds, mult):
    a2.annotate(f"{v:.2f}×", (r, v), textcoords="offset points", xytext=(0, 6),
                ha="center", fontsize=6.4, color=F.RUST)
a2.set_ylabel("exit multiple, ×"); a2.set_xlabel("Round")
a2.set_xticks(rounds); a2.set_ylim(14.5, 19.4)
F.despine(a2)
F.source(fig, "engine._MACRO_RATE_CYCLES at commit 0ad1246: −1% in Rounds 1 and 2, zero in Rounds 3 to 5, "
              "+1% in Rounds 6 to 8, +1.5% at Round 9 and +2% at Round 10, applied to the 5% base. The ESG "
              "adjustment is held at the opening 1.18 points so that only the macro cycle moves. The "
              "multiple sits on its 18× ceiling through Round 8 and falls only at Rounds 9 and 10 — "
              "the pattern §13.1.3 records as 18.00× to Round 8, 17.96× at Round 9 and 16.50× at Round 10.")
F.save(fig, "fig13_02_macro_regimes")

# ══ Figure 13.3 — four allocation heuristics ═════════════════════════════
BUS = ["pharma", "electronics", "consumer_goods", "software"]
NAME = {"pharma": "Pharma", "electronics": "Electronics",
        "consumer_goods": "Consumer\nGoods", "software": "Software"}
REV = {b: BP.BU_PROFILES[b]["revenue_base"] for b in BUS}
TOTR = sum(REV.values())
POOL = 10.0
HEUR = [
 ("Proportional\nby revenue", [POOL * REV[b] / TOTR for b in BUS],
  "avoids every penalty, earns nothing;\nfunds the unit that needs nothing"),
 ("Worst-first", [POOL * 0.55, POOL * 0.25, POOL * 0.15, POOL * 0.05],
  "responsive, but chases the dashboard;\nthe lowest score is often the least material"),
 ("Flag-hunting", [POOL * 0.30, POOL * 0.30, POOL * 0.20, POOL * 0.20],
  "beats both, reliably: the flags are\nwhere the terminal value is"),
 ("Concentrated\n(one unit)", [POOL, 0.0, 0.0, 0.0],
  "trips the overrun tax and the\nneglect penalty at once"),
]
fig, ax = F.newfig(h=3.7)
x = np.arange(len(HEUR)); w = 0.19
for j, b in enumerate(BUS):
    vals = [h[1][j] for h in HEUR]
    ax.bar(x + (j - 1.5) * w, vals, width=w * 0.9, color=F.SERIES[j], hatch=F.HATCH[j],
           edgecolor="white", lw=0.7, label=NAME[b].replace("\n", " "))
ax.axhline(POOL * 0.15, color=F.RUST, ls=(0, (4, 2)), lw=1.2)
ax.text(3.44, POOL * 0.15 + 0.10, F.esc("the 15% floor: below it a unit\nis 'neglected' and penalised"),
        fontsize=6.6, color=F.RUST, fontweight="bold", ha="right", va="bottom")
ax.axhline(3.0, color=F.SERIES[3], ls=(0, (2, 2)), lw=1.1)
ax.text(3.44, 3.10, F.esc("above $3m in one unit: a 25% chance\nof a 15% overrun — a 3.75% expected tax"),
        fontsize=6.6, color=F.SERIES[3], ha="right", va="bottom")
ax.set_xticks(x); ax.set_xticklabels([h[0] for h in HEUR], fontsize=7.4)
ax.set_ylabel(F.esc("allocation of a $10m pool, $m")); ax.set_ylim(0, 11.6)
ax.grid(axis="x", visible=False); F.despine(ax)
ax.legend(fontsize=6.8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.14),
          frameon=False)
for i, h in enumerate(HEUR):
    ax.text(i, -1.05, h[2], ha="center", va="top", fontsize=6.0, color=F.GREY)
F.source(fig, "The pool is 20% of the opening treasury, floored at $5m — $10.0m at Round 1. The two "
              "constraint lines are the penalties §13.5 records: a 15% floor per unit below which neglect is "
              "penalised, and a 25% chance of a 15% overrun on any allocation above $3m, an expected cost of "
              "3.75% of the amount. Proportional and worst-first allocations are drawn to the heuristics "
              "§13.5.1 describes [J]; the constraint lines and the pool are the engine's.")
F.save(fig, "fig13_03_allocation")

# ══ Figure 13.4 — the five instruments compared ══════════════════════════
INSTR = [
 ("Use-of-proceeds\ngreen bond", "the input —\nwhere the money goes", "Low\nproceeds ring-fenced",
  "Is the project additional?", 3),
 ("European green\nbond label", "the input, against\na legal taxonomy", "Low\n85% aligned, 15% pocket",
  "Registered external review,\npre and post issuance", 1),
 ("Sustainability-\nlinked bond", "the outcome —\na performance target", "High\ngeneral purpose",
  "Was the target ambitious,\nand in the issuer's control?", 2),
 ("Transition\nfinance", "a pathway\nrather than a state", "High", "Plan, budget, pay, lobbying —\nall four", 3),
 ("Blended\nfinance", "the risk nobody\nelse will take", "Structured",
  "Would this have been funded\nwithout the concession?", 1),
]
GW = {3: ("HIGH", F.RUST), 2: ("MODERATE", F.SERIES[4]), 1: ("LOW", F.TEAL)}
fig, ax = F.newfig(h=4.0)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
COLS = [(0.005, 0.150, "INSTRUMENT"), (0.165, 0.185, "WHAT IT PRICES"),
        (0.360, 0.170, "FLEXIBILITY"), (0.540, 0.265, "CREDIBILITY TEST"),
        (0.815, 0.180, "GREENWASHING\nEXPOSURE")]
for x, wd, h in COLS:
    ax.text(x, 0.995, h, fontsize=6.5, fontweight="bold", color=F.GREY, va="top")
rh = 0.172
for i, row in enumerate(INSTR):
    y = 0.905 - (i + 1) * rh
    col = F.SERIES[i % len(F.SERIES)]
    ax.add_patch(plt.Rectangle((0.0, y + 0.004), 1.0, rh - 0.012,
                               fc=F.PALE if i % 2 == 0 else "white", ec="none"))
    F.box(ax, COLS[0][0], y + 0.014, COLS[0][1], rh - 0.032, row[0], fc="white", ec=col,
          tc=col, size=6.6, weight="bold")
    for j in (1, 2, 3):
        ax.text(COLS[j][0], y + rh / 2, row[j], fontsize=6.3, color=F.INK, va="center")
    lab, gcol = GW[row[4]]
    ax.add_patch(plt.Rectangle((COLS[4][0], y + 0.030), COLS[4][1], rh - 0.062,
                               fc="white", ec=gcol, lw=1.3))
    ax.text(COLS[4][0] + COLS[4][1] / 2, y + rh / 2, lab, ha="center", va="center",
            fontsize=7.2, fontweight="bold", color=gcol)
    for k in range(row[4]):
        ax.plot([COLS[4][0] + 0.030 + k * 0.026], [y + 0.052], marker="^", ms=4,
                color=gcol)
ax.text(0.005, 0.030, "The instrument with the lowest greenwashing exposure is the one whose control is "
                      "external and legal, not the one whose story is best.",
        fontsize=6.9, color=F.RUST, style="italic")
F.source(fig, "The five rows and their four attributes are the table in Chapter 13 §13.3.4. The exposure "
              "column is the chapter's own rating, shown here with a count of markers as well as a word so "
              "it does not depend on colour. Only the European green bond label and blended finance carry a "
              "control the issuer does not write itself.")
F.save(fig, "fig13_04_instruments")
print("ch13 done")
