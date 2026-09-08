import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import terminal_valuation as TV, bu_profiles as BP, config as C

BUS = ["pharma", "electronics", "consumer_goods", "software"]
bus = [dict(bu_id=b, revenue_base=BP.BU_PROFILES[b]["revenue_base"],
            opex_base=BP.BU_PROFILES[b]["opex_base"],
            carbon_intensity=BP.BU_PROFILES[b]["carbon_intensity"]) for b in BUS]
GROSS = sum(b["revenue_base"] - b["opex_base"] for b in bus) / 1e6
TCO2E = sum(b["carbon_intensity"] * b["revenue_base"] / 1e6 for b in bus)
CARB = TCO2E * C.FINANCIAL_SHADOW_CARBON_PRICE / 1e6
EBITDA = GROSS - CARB

# ══ Figure 14.1 — the valuation bridge, every modifier as a bar ══════════
def mr_parts(profile):
    return profile
TEAMS = {
 "regenerative": [("base", 1.00), ("Materiality Governance", 0.10),
                  ("Synergy Strategic Premium", 0.15), ("Resilience Champion", 0.20),
                  ("Truth Premium", 0.15), ("Community Champion × JT 1.5", 0.27),
                  ("Workforce Excellence", 0.10), ("Wellbeing Champion", 0.05)],
 "competent": [("base", 1.00), ("Materiality Governance — partial", 0.05),
               ("Resilience Champion", 0.20), ("Just Transition × JT 1.2", 0.144),
               ("Workforce Excellence (part ramp)", 0.05)],
 "extractive": [("base", 1.00), ("Planet Expendable Penalty", -0.20),
                ("Instability Discount (full ramp)", -0.40)],
}
fig, ax = F.newfig(h=4.0)
parts = TEAMS["regenerative"]
run = 0.0
for i, (nm, v) in enumerate(parts):
    if i == 0:
        ax.bar(i, v, width=0.62, color=F.NAVY, edgecolor="white", lw=0.8)
        ax.text(i, v + 0.025, f"{v:.2f}", ha="center", va="bottom", fontsize=7.6,
                fontweight="bold", color=F.NAVY)
        run = v
    else:
        col = F.TEAL if v > 0 else F.RUST
        ax.bar(i, v, bottom=run, width=0.62, color=col, hatch="///" if v < 0 else "",
               edgecolor="white", lw=0.8)
        ax.text(i, run + v + 0.025, f"{v:+.2f}", ha="center", va="bottom", fontsize=7.2,
                fontweight="bold", color=col)
        run += v
    if i < len(parts) - 1:
        ax.plot([i + 0.31, i + 0.69], [run, run], color=F.GREY, lw=0.8, ls=(0, (2, 2)))
ax.bar(len(parts), run, width=0.62, color=F.NAVY, edgecolor="white", lw=0.8)
ax.text(len(parts), run + 0.025, f"{run:.2f}", ha="center", va="bottom", fontsize=8.6,
        fontweight="bold", color=F.NAVY)
ax.axhline(TV.MR_PUBLISHED_CEILINGS["jt_scaled"], color=F.RUST, ls=(0, (4, 2)), lw=1.2)
ax.text(0.15, TV.MR_PUBLISHED_CEILINGS["jt_scaled"] + 0.025,
        f"published ceiling with JT scaling: {TV.MR_PUBLISHED_CEILINGS['jt_scaled']:.2f}",
        fontsize=7, color=F.RUST, fontweight="bold")
ax.axhline(TV.MR_PUBLISHED_CEILINGS["base"], color=F.GREY, ls=(0, (2, 2)), lw=1.0)
ax.text(0.15, TV.MR_PUBLISHED_CEILINGS["base"] - 0.055,
        f"without it: {TV.MR_PUBLISHED_CEILINGS['base']:.2f}", fontsize=7, color=F.GREY)
ax.set_xticks(range(len(parts) + 1))
ax.set_xticklabels([p[0] for p in parts] + ["M_R"], fontsize=6.2, rotation=30, ha="right")
ax.set_ylabel("Regenerative Multiple"); ax.set_ylim(0, 2.30)
ax.grid(axis="x", visible=False); F.despine(ax)
ax.set_title("Every modifier the engine can add, on one path — the maximum a team can reach",
             loc="left", color=F.NAVY, fontsize=8.6)
F.source(fig, "terminal_valuation.calculate_mr at commit 0ad1246, every positive component on a single "
              "path. Community Champion is 0.18 scaled by the Just Transition factor, which reaches its 1.5 "
              "cap after five rounds of HR investment; without it the ceiling is 1.93. The defensive clamp "
              f"in the code is {TV.MR_CEILING}, above the published ceilings, so the clamp never binds on a "
              "legitimate path.")
F.save(fig, "fig14_01_valuation_bridge")

# ══ Figure 14.2 — M_R waterfalls for three contrasting teams ═════════════
fig, axes = plt.subplots(1, 3, figsize=(F.TEXT_WIDTH_IN, 3.9), sharey=True,
                         gridspec_kw=dict(wspace=0.10))
LABELS = {"regenerative": "Regenerative\nevery flag earned",
          "competent": "Competent\npartial credit, no premium",
          "extractive": "Extractive\ntwo penalties, no flags"}
for a, (key, parts) in zip(axes, TEAMS.items()):
    run = 0.0
    for i, (nm, v) in enumerate(parts):
        if i == 0:
            a.bar(i, v, width=0.66, color=F.NAVY, edgecolor="white", lw=0.7); run = v
        else:
            col = F.TEAL if v > 0 else F.RUST
            a.bar(i, v, bottom=run, width=0.66, color=col, hatch="///" if v < 0 else "",
                  edgecolor="white", lw=0.7)
            run += v
        a.text(i, max(run, run - v) + 0.03, f"{v:+.2f}" if i else f"{v:.2f}",
               ha="center", va="bottom", fontsize=5.9,
               color=F.NAVY if i == 0 else (F.TEAL if v > 0 else F.RUST))
    a.bar(len(parts), run, width=0.66, color=F.NAVY, edgecolor="white", lw=0.7)
    a.text(len(parts), run + 0.05, f"M_R {run:.2f}", ha="center", va="bottom",
           fontsize=8, fontweight="bold", color=F.NAVY)
    tvv = (EBITDA) * 18.0 * run
    a.text(len(parts) / 2, 2.05, F.esc(f"terminal value ${tvv:,.0f}m"),
           ha="center", va="top", fontsize=7.4, color=F.INK, fontweight="bold")
    a.set_xticks(range(len(parts) + 1))
    a.set_xticklabels([p[0] for p in parts] + ["M_R"], fontsize=5.4, rotation=42,
                      ha="right", rotation_mode="anchor")
    a.set_title(LABELS[key], fontsize=7.6, color=F.NAVY, pad=4)
    a.set_ylim(0, 2.15); a.grid(axis="x", visible=False); F.despine(a)
axes[0].set_ylabel("Regenerative Multiple")
F.source(fig, "\n\nterminal_valuation.calculate_mr at commit 0ad1246. The Instability Discount and the "
              "Workforce, Wellbeing and Synergy bonuses are ramped over a ten-point band rather than applied "
              "as cliffs, so partial credit is real. Terminal value is (EBITDA + green fund) × multiple × "
              f"M_R; the EBITDA shown is the opening gross profit of ${GROSS:.1f}m less the terminal carbon "
              f"charge of ${CARB:.2f}m on {TCO2E:,.0f} tonnes at ${C.FINANCIAL_SHADOW_CARBON_PRICE:.0f} a "
              "tonne, at the 18× ceiling. The spread between the first and third columns is the whole of "
              "what the second ledger is worth.")
F.save(fig, "fig14_02_mr_waterfalls")

# ══ Figure 14.3 — the multiple against the WACC, and M_R across it ═══════
def mult(w):
    return max(6.0, min(18.0, 1.02 / (w - 0.02)))
w = np.linspace(0.03, 0.20, 600)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.3),
                             gridspec_kw=dict(wspace=0.30))
a1.plot(w * 100, [mult(x) for x in w], color=F.NAVY, lw=2.2)
a1.fill_between(w * 100, 6, [mult(x) for x in w], color=F.PALE, alpha=0.6)
a1.axhline(18, color=F.GREY, ls=(0, (2, 2)), lw=1.0)
a1.axhline(6, color=F.GREY, ls=(0, (2, 2)), lw=1.0)
a1.axvline(7.67, color=F.RUST, ls=(0, (4, 2)), lw=1.2)
a1.text(7.9, 19.2, "the cap breaks\nat 7.67%", fontsize=7, color=F.RUST, fontweight="bold")
a1.text(19.6, 18.5, "18× cap", ha="right", fontsize=7, color=F.GREY)
a1.text(19.6, 6.5, "6× floor", ha="right", fontsize=7, color=F.GREY)
a1.text(19.6, 5.0, "the floor binds\nabove about 20%", ha="right", va="top",
        fontsize=6.6, color=F.GREY)
a1.set_xlabel("cost of capital, %"); a1.set_ylabel("exit multiple, ×")
a1.set_xlim(3, 20); a1.set_ylim(0, 22)
F.despine(a1)
a1.set_title("(1 + 2%) ÷ (WACC − 2%), floored and capped", loc="left", color=F.NAVY,
             fontsize=8.6)
for i, (mr, lab) in enumerate([(2.02, "M_R 2.02 — every flag"),
                               (1.44, "M_R 1.44 — competent"),
                               (1.00, "M_R 1.00 — no modifiers"),
                               (0.40, "M_R 0.40 — two penalties")]):
    tvv = [EBITDA * mult(x) * mr for x in w]
    a2.plot(w * 100, tvv, color=F.SERIES[i], linestyle=F.DASH[i], lw=1.9)
    a2.text(20.2, tvv[-1], f" {lab}\n {tvv[-1]:,.0f}m", color=F.SERIES[i], fontsize=6.6,
            va="center", fontweight="bold")
a2.axvline(6.18, color=F.GREY, ls=(0, (2, 2)), lw=1.0)
a2.text(6.4, 30, "opening\n6.18%", fontsize=6.8, color=F.GREY)
a2.set_xlabel("cost of capital, %"); a2.set_ylabel(F.esc("terminal value, $m"))
a2.set_xlim(3, 27); a2.set_ylim(0, 330)
F.despine(a2)
a2.set_title("What the two levers are worth together", loc="left", color=F.NAVY, fontsize=8.6)
F.source(fig, "terminal_valuation.calculate_dynamic_exit_multiple and calculate_terminal_value at commit "
              f"0ad1246. Terminal value = (EBITDA + green fund) × multiple × M_R × M_SDG; here EBITDA is the "
              f"opening ${EBITDA:.2f}m, the green fund is nil and M_SDG is 1.0. The right-hand panel shows "
              "why the multiple is the weaker of the two levers on a clean path: it is pinned at 18× across "
              "the whole plausible range of the cost of capital, while M_R moves terminal value by a factor "
              "of five.")
F.save(fig, "fig14_03_multiple_vs_wacc")

# ══ Figure 14.4 — the component reference table ══════════════════════════
COMP = [
 ("Materiality Governance", "+0.10", "materiality_aligned", "R2 full accuracy", "hard"),
 ("Materiality Governance — partial", "+0.05", "materiality_partial", "R2 at 80%+", "hard"),
 ("Synergy Strategic Premium", "+0.15", "synergy_unlock AND synergy ≥ 0.80",
  "R7 option C, and the multiplier still above the gate", "ramped ±0.10"),
 ("Resilience Champion", "+0.20", "the ABSENCE of insurance_only,\nelectronics_water_priority, civil_water_priority",
  "granted by default — you can only lose it", "hard"),
 ("Truth Premium", "+0.15", "ethical_ai_overhaul", "R6 option B", "hard"),
 ("Community Champion", "+0.18 × JT", "community_fund", "R9 option C, scaled by HR rounds", "hard"),
 ("Just Transition", "+0.12 × JT", "managed_transition", "R9 option B, scaled by HR rounds", "hard"),
 ("Workforce Excellence", "+0.10", "workforce_readiness ≥ 75", "ten-point ramp", "ramped ±10"),
 ("Wellbeing Champion", "+0.05", "average burnout ≤ 20", "ten-point ramp", "ramped ±10"),
 ("BRSR ESG Alpha Dividend", "+ variable", "brsr_net_positive_dividend", "the BRSR side track", "value"),
 ("Planet Expendable Penalty", "−0.20", "planet_expendable", "a named flag", "hard"),
 ("Instability Discount", "−0.40", "average licence < 75", "ten-point ramp, 70 to 80", "ramped ±10"),
]
fig, ax = F.newfig(h=5.0)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
HEAD = [(0.005, "COMPONENT"), (0.245, "VALUE"), (0.335, "WHAT SETS IT"),
        (0.640, "HOW IT IS EARNED"), (0.885, "CLIFF OR RAMP")]
for x, h in HEAD:
    ax.text(x, 0.995, h, fontsize=6.5, fontweight="bold", color=F.GREY, va="top")
rh = 0.0755
for i, row in enumerate(COMP):
    y = 0.950 - (i + 1) * rh
    neg = row[1].startswith("−")
    col = F.RUST if neg else F.TEAL
    ax.add_patch(plt.Rectangle((0.0, y + 0.004), 1.0, rh - 0.010,
                               fc=F.PALE if i % 2 == 0 else "white", ec="none"))
    ax.text(0.005, y + rh / 2, row[0], fontsize=6.4, color=F.INK, va="center",
            fontweight="bold" if neg else "normal")
    ax.text(0.245, y + rh / 2, row[1], fontsize=6.8, color=col, va="center",
            fontweight="bold")
    ax.text(0.335, y + rh / 2, row[2], fontsize=5.8, color=F.GREY, va="center",
            family="monospace")
    ax.text(0.640, y + rh / 2, row[3], fontsize=6.0, color=F.INK, va="center")
    ax.text(0.885, y + rh / 2, row[4], fontsize=6.0, color=F.NAVY, va="center")
ax.text(0.005, 0.030, "Four of the twelve are ramped rather than cliff-edged, so a team just outside a "
                      "threshold gets part of the component — the change §14 records as GAME-2.",
        fontsize=6.7, color=F.RUST, style="italic")
F.source(fig, "Every branch of terminal_valuation.calculate_mr at commit 0ad1246, in the order the function "
              f"applies them. The published ceilings are {TV.MR_PUBLISHED_CEILINGS['base']} without Just "
              f"Transition scaling, {TV.MR_PUBLISHED_CEILINGS['jt_scaled']} with it and "
              f"{TV.MR_PUBLISHED_CEILINGS['brsr']} with the BRSR dividend instead; the defensive clamp sits "
              f"at {TV.MR_CEILING} and never binds on a legitimate path. Resilience Champion is the only "
              "component granted by default: it is a thing to keep, not a thing to win.")
F.save(fig, "fig14_04_component_table")
print("ch14 done")
