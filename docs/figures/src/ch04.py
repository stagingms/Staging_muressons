import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import materiality_db as MDB, round2_csrd as R2

# ══ Figure 4.1 — the quadrant, with the default eight plotted ══════════════
issues = MDB.get_current_config()["issues"]
LEV = {"low": 0.5, "medium": 1.5, "high": 2.6}
SHORT = {
    "data_privacy_impact": "Data privacy",
    "api_leakage_impact": "API leakage",
    "drug_safety_financial_risk": "Drug safety",
    "e_waste_impact": "E-waste",
    "plastic_waste_impact": "Plastic waste",
    "supply_chain_labor_risk": "Supply-chain labour",
    "biodiversity_financial_risk": "Biodiversity",
    "energy_financial_risk": "Energy cost exposure",
}
fig, ax = F.newfig(h=4.3)
THR = 2.05                                    # the label cut: "high" or not
ax.add_patch(plt.Rectangle((THR, THR), 3.30 - THR, 3.30 - THR, fc="#E4EDE9", ec="none", zorder=0))
ax.add_patch(plt.Rectangle((0, THR), THR, 3.30 - THR, fc=F.PALE, ec="none", zorder=0))
ax.add_patch(plt.Rectangle((THR, 0), 3.30 - THR, THR, fc=F.PALE, ec="none", zorder=0))
ax.add_patch(plt.Rectangle((0, 0), THR, THR, fc="#F4F1EC", ec="none", zorder=0))
ax.axvline(THR, color=F.GREY, lw=1.1, ls=(0, (4, 2)))
ax.axhline(THR, color=F.GREY, lw=1.1, ls=(0, (4, 2)))
QLAB = [(THR + 0.06, 3.22, "Q1  double materiality", F.NAVY, "gets capital"),
        (0.06, 3.22, "Q2  impact only", F.TEAL, "gets a disclosure plan"),
        (THR + 0.06, 0.42, "Q3  financial only", F.RUST, "gets the risk register"),
        (0.06, 0.42, "Q4  neither", F.GREY, "gets excluded")]
for x, y, t, c, sub in QLAB:
    ax.text(x, y, t, ha="left", va="top", fontsize=8.2, fontweight="bold", color=c)
    ax.text(x, y - 0.15, sub, ha="left", va="top", fontsize=7.1, color=c, style="italic")

groups = {}
for it in issues:
    x = LEV[it["financial_impact"]]; y = LEV[it["societal_impact"]]
    groups.setdefault((x, y), []).append(it)
for (x, y), items in groups.items():
    n = len(items)
    for k, it in enumerate(items):
        q = R2.correct_quadrant_v2(it)
        col = {"q1": F.NAVY, "q2": F.TEAL, "q3": F.RUST, "q4": F.GREY}[q]
        mk = {"q1": "o", "q2": "s", "q3": "^", "q4": "X"}[q]
        dy = (k - (n - 1) / 2) * 0.195 - (0.13 if n > 2 else 0.0)
        ax.plot([x - 0.30], [y + dy], marker=mk, ms=7.5, color=col, zorder=4,
                markeredgecolor="white", markeredgewidth=0.9)
        ax.text(x - 0.21, y + dy, SHORT[it["id"]], fontsize=7.4, color=col,
                va="center", fontweight="bold")
ax.text(1.02, 1.55, "no issue in the default dictionary\nis a Q4 distractor",
        ha="center", va="center", fontsize=7.4, color=F.GREY, style="italic")
ax.set_xlim(0, 3.30); ax.set_ylim(0, 3.30)
ax.set_xticks([LEV["low"], LEV["medium"], LEV["high"]]); ax.set_xticklabels(["low", "medium", "high"])
ax.set_yticks([LEV["low"], LEV["medium"], LEV["high"]]); ax.set_yticklabels(["low", "medium", "high"])
ax.set_xlabel("Financial materiality  →  risk and opportunity to the company")
ax.set_ylabel("Impact materiality  →\nharm and benefit to the world")
ax.grid(False)
F.despine(ax)
ax.set_title("The default eight, placed by the engine's own classifier", loc="left", color=F.NAVY)
F.source(fig, "Issues and their two ratings: materiality_db.get_current_config() — the live default dictionary "
              "at commit 0ad1246. Placement is round2_csrd.correct_quadrant_v2, whose axis test is literally "
              "rating == 'high'; the dashed lines are that cut. Where an issue carries dual-axis scores instead, "
              f"the axis clears at magnitude × likelihood ≥ {R2.ESRS_MAT_THRESHOLD}. Quadrant corners follow the "
              "engine's own field names (quadrant_1_top_right … quadrant_4_bottom_left).")
F.save(fig, "fig04_01_quadrant")

# ══ Figure 4.2 — six steps, and the evidence each must leave ═══════════════
STEPS = [
 ("1", "Context and\nvalue chain",
  "Decide material to what:\nwhich entities, which\ngeographies, how far up and\ndown the value chain.",
  "A written scope statement\nnaming entities, geographies\nand value-chain reach, with\nthe exclusions justified."),
 ("2", "Identify impacts,\nrisks, opportunities",
  "Build the candidate universe\nbefore scoring any of it.\nSeparate the matter from the\nimpact. Include opportunities.",
  "A numbered issue library:\nmatter, mechanism, affected\nstakeholder, and the part of\nthe value chain it sits in."),
 ("3", "Score and\nthreshold",
  "Both axes, against a threshold\nset in advance. Two scorers\nindependently; differences\ndiscussed, never averaged.",
  "The scoring sheet, both initial\nscores, the resolved score, and\na note wherever resolution\nchanged a placement."),
 ("4", "Stakeholder\nengagement",
  "Evidence gathering about\nimpacts you cannot observe\nfrom inside. Not a vote. Engage\nthe affected, not the interested.",
  "Who was engaged, by what\nmethod, what they said —\nand what changed as a\nresult."),
 ("5", "Validation and\naudit trail",
  "To the accountable body for\nchallenge, not approval: what\nsits near the threshold, what\nwas excluded, what changed.",
  "Minutes recording the\nquestions asked, and any\nplacement that changed as\na result."),
 ("6", "Link to strategy,\ntargets and capital",
  "Every Q1 issue gets an owner,\na target with a date, a budget\nline and a place in the\ndisclosure. Q2, a disclosure plan.",
  "A line in the capital plan that\nexists because of the\nassessment — and a line that\nwas cut because of it."),
]
fig, ax = F.newfig(h=5.7)
F.nogrid(ax)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
n = len(STEPS)
h = 0.132
top = 0.945
gap = (top - n * h) / (n - 1) if n > 1 else 0
XN, XS, XD, XE, XO = 0.012, 0.038, 0.262, 0.578, 0.892
WS, WE, WO = 0.205, 0.296, 0.100
ax.text(XS, 0.985, "The step", fontsize=7.6, fontweight="bold", color=F.GREY, va="top")
ax.text(XD, 0.985, "What it decides", fontsize=7.6, fontweight="bold", color=F.GREY, va="top")
ax.text(XE, 0.985, "The evidence it must leave", fontsize=7.6, fontweight="bold", color=F.GREY, va="top")
ax.text(XO, 0.985, "owner", fontsize=7.6, fontweight="bold", color=F.RUST, va="top")
ax.text(XO, 0.958, "(name one)", fontsize=6.8, color=F.RUST, va="top")
for i, (num, name, decides, evidence) in enumerate(STEPS):
    y = top - h - i * (h + gap)
    col = F.SERIES[i % len(F.SERIES)]
    ax.add_patch(plt.Circle((XN, y + h / 2), 0.0135, fc=col, ec="none"))
    ax.text(XN, y + h / 2, num, ha="center", va="center", fontsize=7.4,
            color="white", fontweight="bold")
    F.box(ax, XS, y, WS, h, name, fc="white", ec=col, tc=col, size=7.8, weight="bold", lw=1.3)
    ax.text(XD, y + h / 2, decides, fontsize=6.9, color=F.INK, va="center", linespacing=1.35)
    F.box(ax, XE, y, WE, h, evidence, fc=F.PALE, ec=F.GREY, tc=F.INK, size=6.6)
    ax.add_patch(plt.Rectangle((XO, y + 0.016), WO, h - 0.032,
                               fc="white", ec=F.RUST, lw=0.8, ls=(0, (2, 2))))
    if i < n - 1:
        F.arrow(ax, (XN, y - 0.004), (XN, y - gap + 0.004), color=F.GREY, lw=0.9)
F.source(fig, "Steps, what each decides and the evidence each must leave: Chapter 4 §4.3.1–§4.3.6, which states "
              "the evidence requirement for all six. The chapter requires that each step have an owner but names "
              "one only at step five (the accountable body), so the owner column is left for the assessment team "
              "to complete — an unsigned step is §4.3's fourth failure mode.")
F.save(fig, "fig04_02_six_steps")

# ══ Figure 4.3 — ESRS topical standards against rounds and pillars ═════════
ROUNDS = ["1 Foundations", "2 Materiality", "3 Scope 3", "4 Contagion", "5 Climate",
          "6 AI Bias", "7 Circularity", "8 Blue Stress", "9 Just Transition", "10 Finale"]
# Each row: (code, title, rounds it bites, pillars that act on it, the evidence in the build)
ROWS = [
 ("E1", "Climate change", [3, 5, 10], "Energy · Offsetting",
  "carbon_intensity per BU; the R10 carbon tax at $250/tCO2e; energy pillar options carry carbon_intensity_delta"),
 ("E2", "Pollution", [7], "Operations · Supply Chain",
  "e_waste_impact in the default dictionary; CSRD_ISSUES e_waste cites ESRS E2 / WEEE Phase III"),
 ("E3", "Water and marine resources", [8], "Operations",
  "water_dependency per BU (Pharma 82, Semiconductor 92); R8 Blue Stress; water_stress_index drives the community NPC"),
 ("E4", "Biodiversity and ecosystems", [2, 8], "Offsetting",
  "biodiversity_financial_risk in the default dictionary; biodiversity_engine_enabled; nature-based offsets"),
 ("E5", "Resource use and circular economy", [7], "Operations · Supply Chain · Offsetting",
  "plastic_waste_impact; R7 options set circular_redesign / epr_program / waste_to_energy; 15% OPEX circular bonus"),
 ("S1", "Own workforce", [9], "Human Resources",
  "staff_burnout_index, workforce_readiness; the HR pillar's own flag set; JT scaling at terminal valuation"),
 ("S2", "Workers in the value chain", [2, 4], "Supply Chain",
  "supply_chain_labor_risk in the default dictionary; CSRD_ISSUES tier3_labor and living_wage cite ESRS S2 / CSDDD"),
 ("S3", "Affected communities", [4, 8], "Operations · Offsetting",
  "social_license_score per BU; the community-leader NPC (Deccan Plateau Council); CSRD_ISSUES philanthropy cites ESRS S3"),
 ("S4", "Consumers and end-users", [2, 6], "— none —",
  "data_privacy_impact and api_leakage_impact are in the dictionary, but no pillar acts on them and the NPC roster "
  "has no consumer: the thinnest coverage in the build"),
 ("G1", "Business conduct", [6, 10], "Operations · Supply Chain",
  "governance_risk_score per BU; the regulator NPC's csrd_compliance priority; CSRD_ISSUES open_source_ai cites ESRS G1 §37"),
]
fig = plt.figure(figsize=(F.TEXT_WIDTH_IN, 5.6))
ax = fig.add_axes([0.005, 0.455, 0.99, 0.50])
F.nogrid(ax)
nr, nc = len(ROWS), len(ROUNDS)
LEFT, CELL = 0.185, 0.052
ax.set_xlim(0, 1); ax.set_ylim(-0.03, 1.30)
for j, rl in enumerate(ROUNDS):
    ax.text(LEFT + (j + 0.5) * CELL, 1.05, rl.split()[0], ha="center", va="bottom",
            fontsize=7, fontweight="bold", color=F.GREY)
    ax.text(LEFT + (j + 0.5) * CELL, 1.035, " ".join(rl.split()[1:]), ha="right", va="bottom",
            fontsize=6.2, color=F.GREY, rotation=48, rotation_mode="anchor")
ax.text(LEFT + nc * CELL + 0.018, 1.05, "PILLARS THAT ACT ON IT", ha="left", va="bottom",
        fontsize=7, fontweight="bold", color=F.GREY)
rh = 0.093
for i, (code, title, rds, pillars, _ev) in enumerate(ROWS):
    y = 1.0 - 0.09 - (i + 1) * rh
    col = F.SERIES[i % len(F.SERIES)]
    thin = pillars.startswith("—")
    ax.text(0.005, y + rh / 2, code, fontsize=8, fontweight="bold",
            color=F.RUST if thin else col, va="center")
    ax.text(0.040, y + rh / 2, title, fontsize=7.2, color=F.INK, va="center")
    for j in range(nc):
        cx = LEFT + (j + 0.5) * CELL
        if (j + 1) in rds:
            ax.add_patch(plt.Rectangle((LEFT + j * CELL + 0.004, y + 0.012),
                                       CELL - 0.008, rh - 0.024,
                                       fc=F.PALE, ec=col, lw=1.0))
            ax.plot([cx], [y + rh / 2], marker=F.MARK[i % len(F.MARK)], ms=4.2, color=col)
        else:
            ax.plot([cx], [y + rh / 2], marker="_", ms=3.4, color="#D2DAE1")
    ax.text(LEFT + nc * CELL + 0.018, y + rh / 2, pillars, fontsize=7,
            color=F.RUST if thin else F.INK, va="center",
            fontweight="bold" if thin else "normal")

kx = fig.add_axes([0.005, 0.02, 0.99, 0.40]); F.nogrid(kx)
kx.set_xlim(0, 1); kx.set_ylim(0, 1)
kx.text(0.0, 1.0, "What each row is grounded in, at commit 0ad1246", fontsize=7.4,
        fontweight="bold", color=F.GREY, va="top")
yy = 0.90
for i, (code, _t, _r, _p, ev) in enumerate(ROWS):
    col = F.SERIES[i % len(F.SERIES)]
    kx.text(0.0, yy, code, fontsize=6.9, fontweight="bold", color=col, va="top")
    kx.text(0.038, yy, ev, fontsize=6.6, color=F.INK, va="top", wrap=True)
    yy -= 0.093 if code != "S4" else 0.115
F.source(fig, "Standard codes and titles: ESRS Set 1 as published by EFRAG. Rounds are the ten configured round "
              "titles; pillars are the five decision areas of the multi_toggles paradigm. Every mark is grounded "
              "in the listed state variable, dictionary entry or round option — a blank means the build carries "
              "no mechanic for that standard in that round, not that the standard does not apply.")
F.save(fig, "fig04_03_esrs_map")
print("ch04 done")
