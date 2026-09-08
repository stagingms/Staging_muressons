import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import meadows_leverage as ML, bu_profiles as BP, ending_pathways as EP

# ══ Figure 15.1 — the strategic loop over the round cycle ════════════════
fig, ax = F.newfig(h=4.3)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
STAGES = [("Look outward",  "PESTEL, five forces,\nthe intelligence feeds", "R1, R5, R8", F.NAVY),
          ("Look inward",   "value chain, capability\naudit, technical debt", "R1, R3, R7", F.TEAL),
          ("Synthesise",    "the strategic thesis\nin one sentence", "R2, R5", F.RUST),
          ("Choose",        "pillar allocation and\nthe round's decision", "every round", F.SERIES[3]),
          ("Commit",        "flags that cannot be\nunset later", "R3, R6, R7, R9", F.SERIES[4]),
          ("Read the result", "the reveal, the debrief,\nthe mental-model tracker", "R5, R10", F.GREY)]
n = len(STAGES)
cx, cy, r = 0.30, 0.50, 0.325
ASPECT = 6.5 / 4.3
for i, (nm, sub, when, col) in enumerate(STAGES):
    th = np.pi / 2 - i * 2 * np.pi / n
    x = cx + r * np.cos(th) / ASPECT
    y = cy + r * np.sin(th)
    F.box(ax, x - 0.105, y - 0.062, 0.210, 0.124, nm, fc="white", ec=col, tc=col,
          size=7.6, weight="bold", lw=1.5)
    ax.text(x, y - 0.075, sub, ha="center", va="top", fontsize=6.2, color=F.GREY)
    ax.text(x, y + 0.072, when, ha="center", va="bottom", fontsize=6.2, color=col,
            fontweight="bold")
    th2 = np.pi / 2 - (i + 1) * 2 * np.pi / n
    x2 = cx + r * np.cos(th2) / ASPECT
    y2 = cy + r * np.sin(th2)
    F.arrow(ax, (x + (x2 - x) * 0.30, y + (y2 - y) * 0.30),
            (x + (x2 - x) * 0.70, y + (y2 - y) * 0.70), color=F.GREY, lw=1.2)
ax.text(cx, cy + 0.03, "ONE ROUND", ha="center", fontsize=8, fontweight="bold", color=F.NAVY)
ax.text(cx, cy - 0.02, "six months", ha="center", fontsize=6.8, color=F.GREY)
ax.text(0.665, 0.955, "AND WHAT CARRIES OVER", fontsize=7.4, fontweight="bold",
        color=F.GREY, va="top")
CARRY = [("Flags", "cannot be unset — R3's decarboniser,\nR6's truth premium, R7's synergy unlock", F.RUST),
         ("Stocks", "licence, burnout, readiness, NCD,\nsynergy: all path-dependent", F.NAVY),
         ("The thesis", "the only thing the loop cannot\nrewrite for you", F.TEAL)]
for i, (nm, sub, col) in enumerate(CARRY):
    y = 0.845 - i * 0.230
    F.box(ax, 0.665, y - 0.075, 0.330, 0.150, f"{nm}\n{sub}", fc=F.PALE, ec=col,
          tc=F.INK, size=6.5)
    if i < 2:
        F.arrow(ax, (0.830, y - 0.075), (0.830, y - 0.155), color=col)
ax.text(0.665, 0.115, "The loop runs ten times. Nothing in it is annual, and nothing in it\n"
                      "waits for the strategy to be finished before the round is committed.",
        fontsize=6.8, color=F.RUST, style="italic", va="top")
F.source(fig, "The process stages are Chapter 15 §15.1–§15.4; the rounds against each are the rounds in "
              "which the build actually asks for that work — the R1 and R5 intelligence feeds, the R2 "
              "materiality gate, the R5 formative checkpoint and the R10 reveal. The carry-over column is "
              "the state that survives a round: the flags of round_logic and the stocks of the engine at "
              "commit 0ad1246.")
F.save(fig, "fig15_01_strategic_loop")

# ══ Figure 15.2 — the value chain, redrawn, for Electronics ══════════════
PRIMARY = ["Inbound\nlogistics", "Operations", "Outbound\nlogistics", "Marketing\nand sales", "Service"]
SUPPORT = ["Firm infrastructure", "Human resource management", "Technology development", "Procurement"]
ROWS = [("Emissions at each stage", F.RUST,
         ["cobalt, copper,\nrare earths — 75%\nof its tonnes",
          "CI 72, the group's\nhighest", "freight", "—", "e-waste return\nlogistics"]),
        ("Water at each stage", F.TEAL,
         ["upstream mining", "water_dependency 58", "—", "—", "—"]),
        ("Labour conditions at each stage", F.NAVY,
         ["Tier-3: 14-hour shifts,\nwithheld wages", "own workforce", "—", "—", "repair network"])]
fig, ax = F.newfig(h=4.4)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
LX, CW = 0.245, 0.150
for j, p in enumerate(PRIMARY):
    F.box(ax, LX + j * CW + 0.004, 0.845, CW - 0.008, 0.105, p, fc=F.PALE, ec=F.NAVY,
          tc=F.NAVY, size=6.8, weight="bold")
ax.text(LX, 0.985, "PRIMARY ACTIVITIES", fontsize=7, fontweight="bold", color=F.GREY, va="top")
rh = 0.175
for i, (nm, col, cells) in enumerate(ROWS):
    y = 0.815 - (i + 1) * rh
    ax.text(0.005, y + rh / 2, nm, fontsize=7.0, fontweight="bold", color=col, va="center")
    for j, c in enumerate(cells):
        F.box(ax, LX + j * CW + 0.004, y + 0.012, CW - 0.008, rh - 0.030, c,
              fc="white" if c == "—" else F.PALE, ec=col if c != "—" else "#D2DAE1",
              tc=F.INK if c != "—" else F.GREY, size=5.8)
ax.text(0.005, 0.245, "SUPPORT ACTIVITIES", fontsize=7, fontweight="bold", color=F.GREY, va="top")
for j, s in enumerate(SUPPORT):
    F.box(ax, 0.005 + j * 0.248, 0.130, 0.240, 0.085, s, fc="white", ec=F.GREY,
          tc=F.INK, size=6.6)
ax.text(0.005, 0.075, "The three added rows are the point: they run the whole width, and the two that "
                      "matter most for Electronics sit upstream of anything it controls directly.",
        fontsize=6.8, color=F.RUST, style="italic", va="top")
F.source(fig, "The classical chain and the three added rows are §15.3.1. The cells are Electronics' own "
              "state at commit 0ad1246 — carbon intensity 72 and water dependency 58 from BU_PROFILES, the "
              "75 per cent Scope 3 share from the engine's scope split, and the Tier-3 labour and e-waste "
              "entries from the Round 2 dictionary, where both are electronics_sensitive.")
F.save(fig, "fig15_02_value_chain")

# ══ Figure 15.3 — the twelve leverage points, ranked ═════════════════════
LP = ML.LEVERAGE_POINTS
fig, ax = F.newfig(h=5.3)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
rh = 0.0755
ax.text(0.005, 0.995, "LEVEL", fontsize=6.6, fontweight="bold", color=F.GREY, va="top")
ax.text(0.060, 0.995, "MEADOWS' NAME", fontsize=6.6, fontweight="bold", color=F.GREY, va="top")
ax.text(0.395, 0.995, "THE SIMULATION DECISION THAT SITS THERE", fontsize=6.6,
        fontweight="bold", color=F.GREY, va="top")
ax.text(0.905, 0.995, "POWER", fontsize=6.6, fontweight="bold", color=F.GREY, va="top")
EFF_COL = {"low": F.GREY, "medium": F.SERIES[3], "high": F.TEAL, "very high": F.RUST,
           "extreme": F.RUST, "highest": F.RUST}
for i, lvl in enumerate(sorted(LP, reverse=True)):
    v = LP[lvl]
    y = 0.955 - (i + 1) * rh
    eff = str(v.get("effectiveness", "")).lower()
    col = EFF_COL.get(eff, F.NAVY)
    ax.add_patch(plt.Rectangle((0.0, y + 0.004), 1.0, rh - 0.010,
                               fc=F.PALE if i % 2 == 0 else "white", ec="none"))
    ax.text(0.020, y + rh / 2, str(lvl), fontsize=8.4, fontweight="bold", color=col,
            ha="center", va="center")
    ax.text(0.060, y + rh / 2, v["name"], fontsize=6.6, color=F.INK, va="center")
    ex = (v.get("simulation_examples") or ["—"])[0]
    ax.text(0.395, y + rh / 2, ex, fontsize=6.1, color=F.GREY, va="center")
    nbar = {"low": 1, "medium": 2, "high": 3, "very high": 4, "extreme": 5,
            "highest": 5}.get(eff, 3)
    for k in range(nbar):
        ax.add_patch(plt.Rectangle((0.905 + k * 0.017, y + 0.020), 0.013, rh - 0.042,
                                   fc=col, ec="none"))
ax.annotate("", xy=(0.010, 0.955 - 12 * rh), xytext=(0.010, 0.950),
            arrowprops=dict(arrowstyle="-|>", color=F.RUST, lw=1.6))
ax.text(0.005, 0.030, "The list runs weakest at twelve to strongest at one, and the discomfort rises with "
                      "the power: the simulation lets you move the sliders freely and asks about the goal "
                      "exactly twice.",
        fontsize=6.8, color=F.RUST, style="italic")
F.source(fig, "meadows_leverage.LEVERAGE_POINTS at commit 0ad1246 — the twelve levels, the build's own "
              "name for each, and the first simulation example it lists against each. The chapter is candid "
              "at §15.6 that the list's provenance is messy; it is used here as the build catalogues it. "
              "The power column is the registry's own effectiveness field, shown as a count of blocks as "
              "well as a colour.")
F.save(fig, "fig15_03_leverage_points")

# ══ Figure 15.4 — the five endings as five strategic tests ══════════════
ENDINGS = [
 ("Activist Ultimatum", "Portfolio logic —\ncan you justify owning these four?", [1,2,3,4,5,6,7],
  "a spread allocation and a\ndefensible parent thesis"),
 ("Climate Black Swan", "Decarbonisation conviction —\ndid you cut intensity, or buy offsets?", [3,5,7],
  "the most expensive path\nin the book"),
 ("Stakeholder Revolt", "Social investment —\nis your licence a stock or a slogan?", [1,4,8,9],
  "steady modest spend; the\ncheapest capability to build"),
 ("Hostile Takeover", "Financial strength and governance —\nare you worth taking?", [1,2,3,4,5,6,7,8,9],
  "treasury above $30m and\nsynergy above 1.3"),
 ("Regulatory Shutdown", "Compliance integrity —\nis your record clean and legible?", [2,4,6],
  "cheap in money, expensive\nin foregone options"),
]
fig = plt.figure(figsize=(F.TEXT_WIDTH_IN, 4.0))
ax = fig.add_axes([0.0, 0.06, 1.0, 0.90]); F.nogrid(ax)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
LX, CELL = 0.470, 0.0345
for r in range(1, 11):
    ax.text(LX + (r - 0.5) * CELL, 0.985, str(r), ha="center", va="top", fontsize=6.6,
            fontweight="bold", color=F.GREY)
ax.text(LX + 5 * CELL, 1.030, "ROUNDS WHERE THE CAPABILITY IS BUILT", ha="center",
        va="top", fontsize=6.6, fontweight="bold", color=F.GREY)
ax.text(0.005, 0.985, "ENDING", fontsize=6.6, fontweight="bold", color=F.GREY, va="top")
ax.text(0.155, 0.985, "THE CAPABILITY IT AUDITS", fontsize=6.6, fontweight="bold",
        color=F.GREY, va="top")
ax.text(0.825, 0.985, "WHAT IT COSTS TO BE READY", fontsize=6.6, fontweight="bold",
        color=F.GREY, va="top")
rh = 0.170
for i, (nm, cap, rounds, cost) in enumerate(ENDINGS):
    y = 0.930 - (i + 1) * rh
    col = F.SERIES[i % len(F.SERIES)]
    F.box(ax, 0.005, y + 0.014, 0.140, rh - 0.034, nm, fc="white", ec=col, tc=col,
          size=6.6, weight="bold")
    ax.text(0.155, y + rh / 2, cap, fontsize=6.2, color=F.INK, va="center")
    for r in range(1, 11):
        cx = LX + (r - 0.5) * CELL
        if r in rounds:
            ax.add_patch(plt.Rectangle((LX + (r - 1) * CELL + 0.003, y + 0.030),
                                       CELL - 0.006, rh - 0.070, fc=F.PALE, ec=col, lw=0.9))
            ax.plot([cx], [y + rh / 2], marker=F.MARK[i % len(F.MARK)], ms=3.8, color=col)
        else:
            ax.plot([cx], [y + rh / 2], marker="_", ms=3.0, color="#D2DAE1")
    ax.text(0.825, y + rh / 2, cost, fontsize=6.2, color=F.GREY, va="center")
ax.text(0.005, 0.035, "Round 10 is empty in every row: by the time the ending is revealed, the capability "
                      "it audits has already been built or it has not.",
        fontsize=6.8, color=F.RUST, style="italic")
F.source(fig, "The five pathways are ending_pathways.IMPLEMENTED_PATHWAYS at commit 0ad1246, all five "
              "implemented. The capability, the rounds and the cost are the table in Chapter 15 §15.8, which "
              "reads them off the rounds where each pathway's determining flags and stocks are actually set.")
F.save(fig, "fig15_04_five_endings")
print("ch15 done")
