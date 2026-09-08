import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import org_politics as OP

# ══ Figure 16.1 — the decision-rights matrix ════════════════════════════
ROWS = ["Energy", "Operations", "Supply Chain", "Offsetting", "Human Resources",
        "The crisis decision", "The Round 9 closure"]
SEATS = ["CEO", "CFO", "CSO"]
VERBS = ["Propose", "Decide", "Consult", "Inform"]
VCOL = {"Propose": F.TEAL, "Decide": F.NAVY, "Consult": F.SERIES[3], "Inform": F.GREY}
VMK = {"Propose": "^", "Decide": "o", "Consult": "s", "Inform": "_"}
fig, ax = F.newfig(h=4.2)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
LX, CW = 0.300, 0.150
for j, s in enumerate(SEATS):
    ax.text(LX + (j + 0.5) * CW, 0.985, s, ha="center", va="top", fontsize=8.4,
            fontweight="bold", color=F.NAVY)
ax.text(LX + 1.5 * CW, 0.928, "who may propose, decide, be consulted, be informed",
        ha="center", va="top", fontsize=6.4, color=F.GREY)
ax.text(0.005, 0.985, "DECISION", fontsize=6.8, fontweight="bold", color=F.GREY, va="top")
ax.text(LX + 3 * CW + 0.020, 0.985, "TO BE FILLED IN BY THE TEAM", fontsize=6.6,
        fontweight="bold", color=F.RUST, va="top")
rh = 0.108
for i, r in enumerate(ROWS):
    y = 0.880 - (i + 1) * rh
    crisis = i >= 5
    ax.add_patch(plt.Rectangle((0.0, y + 0.004), 1.0, rh - 0.010,
                               fc=F.PALE if i % 2 == 0 else "white", ec="none"))
    ax.text(0.005, y + rh / 2, r, fontsize=7.0, color=F.INK, va="center",
            fontweight="bold" if crisis else "normal")
    for j in range(3):
        ax.add_patch(plt.Rectangle((LX + j * CW + 0.008, y + 0.016), CW - 0.016,
                                   rh - 0.034, fc="white", ec=F.GREY, lw=0.8,
                                   linestyle=(0, (2, 2))))
    ax.add_patch(plt.Rectangle((LX + 3 * CW + 0.020, y + 0.016), 0.200, rh - 0.034,
                               fc="white", ec=F.RUST, lw=0.8, linestyle=(0, (2, 2))))
    ax.text(LX + 3 * CW + 0.120, y + rh / 2, "tie-break holder", ha="center",
            va="center", fontsize=5.8, color=F.RUST, style="italic")
kx = 0.005
for v in VERBS:
    ax.plot([kx], [0.055], marker=VMK[v], ms=6, color=VCOL[v])
    ax.text(kx + 0.018, 0.055, v, fontsize=6.8, color=VCOL[v], va="center",
            fontweight="bold")
    kx += 0.115
ax.text(0.505, 0.055, "One verb per cell. A cell with two Decides is a charter that has not been written.",
        fontsize=6.8, color=F.RUST, style="italic", va="center")
ax.text(0.005, 0.008, "The three seats are §16.2's; the build does not implement them — the "
                      "role-asymmetry specification's private information and hot-seat modes are unbuilt, "
                      "and the decision log's team_consensus column is written by nothing.",
        fontsize=6.3, color=F.GREY, va="bottom")
F.source(fig, "The four verbs are §16.1.1; the three seats and their characteristic failures are §16.2. The "
              "rows are the five pillar areas of the multi_toggles paradigm plus the two decisions the "
              "chapter singles out. The matrix is deliberately blank: it is the charter the team writes "
              "before Round 1, and §16.2's Inside the Engine records that nothing in the build fills it in "
              "for them at commit 0ad1246.")
F.save(fig, "fig16_01_decision_rights")

# ══ Figure 16.2 — the twenty-five-minute meeting ═══════════════════════
SEG = [("Brief", 0, 3, "One person reads the crisis, the foreshadowing and the state.",
        "The discussion starts before everyone has the same facts."),
       ("Analyse", 3, 8, "The five-minute scan: intelligence feeds, state, what changed.",
        "The loudest reading of the situation becomes the team's."),
       ("Argue", 8, 16, "Positions read out. Silent writing before the vote.",
        "The argument becomes a negotiation before it has produced information."),
       ("Decide", 16, 20, "The tie-break holder calls it. Dissents are recorded.",
        "The clock runs out and the default option wins."),
       ("Allocate", 20, 23, "The sliders, against the thesis. Check the 15% floor.",
        "Allocation absorbs the argument time."),
       ("Record", 23, 25, "The journal: options, uncertainty, trade-off, falsification trigger.",
        "Nothing is recorded, and the debrief has nothing to read.")]
fig, ax = F.newfig(h=3.9)
F.nogrid(ax); ax.set_xlim(-0.5, 25.5); ax.set_ylim(0, 1)
for i, (nm, a, b, what, wrong) in enumerate(SEG):
    col = F.SERIES[i % len(F.SERIES)]
    ax.add_patch(plt.Rectangle((a, 0.740), b - a, 0.150, fc=F.PALE, ec=col, lw=1.4))
    ax.text((a + b) / 2, 0.815, nm, ha="center", va="center", fontsize=7.6,
            fontweight="bold", color=col)
    ax.text((a + b) / 2, 0.918, f"{b-a} min", ha="center", va="bottom", fontsize=6.6,
            color=col)
    y = 0.520 - i * 0.082
    ax.text(0.4, y, nm, fontsize=6.8, color=col, va="center", fontweight="bold")
    ax.text(3.2, y, what, fontsize=6.3, color=F.INK, va="center")
    ax.text(14.2, y, wrong, fontsize=6.1, color=F.RUST, va="center")
for t in range(0, 26, 5):
    ax.plot([t, t], [0.715, 0.740], color=F.GREY, lw=0.9)
    ax.text(t, 0.700, str(t), ha="center", va="top", fontsize=6.8, color=F.GREY)
ax.text(12.5, 0.662, "minutes", ha="center", va="top", fontsize=6.6, color=F.GREY)
ax.text(0.4, 0.575, "SEGMENT", fontsize=6.6, fontweight="bold", color=F.GREY)
ax.text(3.2, 0.575, "WHAT HAPPENS", fontsize=6.6, fontweight="bold", color=F.GREY)
ax.text(14.2, 0.575, "WHAT GOES WRONG WITHOUT THE CLOCK", fontsize=6.6,
        fontweight="bold", color=F.RUST)
ax.text(0.4, 0.020, "The Argue segment is the longest, and it is the one every team shortens first.",
        fontsize=7, color=F.RUST, style="italic")
F.source(fig, "The six segments and their failure modes are the table in Chapter 16 §16.6. The decision "
              "timer the build ships is off by default and set to 300 seconds when enabled — five minutes, "
              "which is the Analyse segment alone; a team running the full protocol is running it on its own "
              "clock, not the platform's.")
F.save(fig, "fig16_02_meeting")

# ══ Figure 16.3 — the pathologies, and where each shows up ═════════════
PATH = [
 ("Groupthink", "concurrence-seeking that suppresses dissent", [6],
  "the four-second silence of §16.3's composite"),
 ("Escalation of commitment", "defending a sunk choice, hardest for whoever made it", [4, 5, 7],
  "defending the Round 3 choice into Rounds 4 and 5"),
 ("Anchoring and ordering", "the first number sets the range; the first option is over-chosen", [1],
  "the platform shuffles option order for this reason"),
 ("Overconfidence after a good round", "raising the bet without raising the analysis", [4],
  "the most reliably observed pattern in ten-round play"),
 ("Loss aversion after a bad one", "taking the cheap option, which here is the expensive one", [5, 9],
  "Round 9 immediate closure is the extreme case"),
 ("Diffusion of responsibility", "the five-pillar allocation nobody owns", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "every round, and hardest to see in any one of them"),
]
fig, ax = F.newfig(h=3.9)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
LX, CELL = 0.520, 0.0345
for r in range(1, 11):
    ax.text(LX + (r - 0.5) * CELL, 0.985, str(r), ha="center", va="top", fontsize=6.6,
            fontweight="bold", color=F.GREY)
ax.text(LX + 5 * CELL, 0.930, "the round where it most often appears", ha="center",
        va="top", fontsize=6.4, color=F.GREY)
ax.text(0.005, 0.985, "PATHOLOGY", fontsize=6.8, fontweight="bold", color=F.GREY, va="top")
ax.text(0.870, 0.985, "ITS SIGNATURE HERE", fontsize=6.8, fontweight="bold",
        color=F.GREY, va="top")
rh = 0.128
for i, (nm, defn, rounds, sig) in enumerate(PATH):
    y = 0.905 - (i + 1) * rh
    col = F.SERIES[i % len(F.SERIES)]
    ax.add_patch(plt.Rectangle((0.0, y + 0.004), 1.0, rh - 0.012,
                               fc=F.PALE if i % 2 == 0 else "white", ec="none"))
    ax.text(0.005, y + rh * 0.66, nm, fontsize=7.0, fontweight="bold", color=col)
    ax.text(0.005, y + rh * 0.30, defn, fontsize=6.0, color=F.GREY, style="italic")
    for r in range(1, 11):
        cx = LX + (r - 0.5) * CELL
        if r in rounds:
            ax.plot([cx], [y + rh / 2], marker=F.MARK[i % len(F.MARK)], ms=5.0, color=col)
        else:
            ax.plot([cx], [y + rh / 2], marker="_", ms=3.0, color="#D2DAE1")
    ax.text(0.870, y + rh / 2, sig, fontsize=5.9, color=F.INK, va="center")
ax.text(0.005, 0.048, "Six, not eight. The outline for this chapter promised eight pathologies; the chapter "
                      "names six, and six is what the text supports.",
        fontsize=6.8, color=F.RUST, style="italic")
F.source(fig, "The six pathologies and their simulation signatures are Chapter 16 §16.3. The rounds are the "
              "rounds the chapter itself names against each; diffusion of responsibility is marked across "
              "all ten because it is a property of the allocation mechanic rather than of any one round. "
              "The chapter is careful that the empirical support for several of these is contested and "
              "marks them accordingly.")
F.save(fig, "fig16_03_pathologies")
print("ch16 done")
