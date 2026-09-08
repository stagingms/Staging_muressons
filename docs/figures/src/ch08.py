import sys, os, math
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import stakeholder_map as SM, config as C, bu_profiles as BP, round_configs as RC

# ══ Figure 8.1 — the power–interest grid, with the roster placed ═══════════
QPOS = {"manage_closely": (1, 1), "keep_satisfied": (0, 1),
        "keep_informed": (1, 0), "monitor": (0, 0)}
QLABEL = {"manage_closely": "MANAGE CLOSELY", "keep_satisfied": "KEEP SATISFIED",
          "keep_informed": "KEEP INFORMED", "monitor": "MONITOR"}
SHORT = {s["id"]: s["name"] for s in SM.STAKEHOLDERS}
ABBR = {"activist_fund": "Activist Fund", "eu_regulators": "EU Regulators",
        "local_communities": "Local Communities", "tier3_miners": "Tier-3 Miners",
        "factory_employees": "Factory Employees", "syndicate_banks": "Syndicate Banks",
        "national_gov": "National Government", "cafeteria_vendors": "Cafeteria Vendors",
        "gen_public": "General Public", "local_media": "Regional Journalist"}
ABBRQ = {"manage_closely": "MC", "keep_satisfied": "KS",
         "keep_informed": "KI", "monitor": "M"}
fig, ax = F.newfig(h=4.3)
F.nogrid(ax)
ax.set_xlim(0, 2); ax.set_ylim(-0.34, 2)
FILL = {"manage_closely": "#E4EDE9", "keep_satisfied": F.PALE,
        "keep_informed": F.PALE, "monitor": "#F4F1EC"}
for q, (qx, qy) in QPOS.items():
    ax.add_patch(plt.Rectangle((qx, qy), 1, 1, fc=FILL[q], ec=F.GREY, lw=0.9))
    ax.text(qx + 0.035, qy + 0.955, QLABEL[q], fontsize=7.8, fontweight="bold",
            color=F.NAVY, va="top")
buckets = {}
for sid, q in SM.MASTER_MAP.items():
    buckets.setdefault(q, []).append(sid)
mig_from = {m["stakeholder"]: m for m in SM.SALIENCE_MIGRATIONS}
for q, ids in buckets.items():
    qx, qy = QPOS[q]
    ids = sorted(ids)
    n_i = len(ids)
    for k, sid in enumerate(ids):
        yy = qy + 0.56 - (k - (n_i - 1) / 2) * 0.155
        moves = sid in mig_from
        alt = sid in SM.ALTERNATE_MAP
        mk = "s" if moves else ("D" if alt else "o")
        col = F.RUST if moves else (F.TEAL if alt else F.NAVY)
        ax.plot([qx + 0.070], [yy], marker=mk, ms=5.2, color=col, zorder=4)
        txt = ABBR[sid]
        if moves:
            m = mig_from[sid]
            txt += f"   → R{m['round']} {ABBRQ[m['to_quadrant']]}"
        if alt:
            txt += "   ±"
        ax.text(qx + 0.105, yy, txt, fontsize=6.9, va="center", color=col,
                fontweight="bold" if moves else "normal")
ax.set_xticks([]); ax.set_yticks([])
ax.text(0.5, 2.045, "low power", ha="center", fontsize=8, color=F.INK)
ax.text(1.5, 2.045, "high power", ha="center", fontsize=8, color=F.INK)
ax.text(-0.035, 1.5, "high\ninterest", ha="right", va="center", fontsize=8, color=F.INK)
ax.text(-0.035, 0.5, "low\ninterest", ha="right", va="center", fontsize=8, color=F.INK)
ax.grid(False); F.despine(ax, keep=())
leg = [("o", F.NAVY, "stays where you put it"),
       ("s", F.RUST, "migrates later — seven of the ten do"),
       ("D", F.TEAL, "±  the ambiguous one: two answers score")]
for i, (mk, col, lab) in enumerate(leg):
    ax.plot([0.02], [-0.06 - i * 0.093], marker=mk, ms=5.0, color=col)
    ax.text(0.065, -0.06 - i * 0.093, lab, fontsize=6.9, color=col, va="center")
ax.text(0.86, -0.06, "MC manage closely · KS keep satisfied · KI keep informed · M monitor",
        fontsize=6.9, color=F.GREY, va="center")
ax.text(0.86, -0.153, F.esc(f"Round 1 scoring: {SM.SCORING_TIERS[0][0]:.0%} → "
                            f"${SM.SCORING_TIERS[0][1]:,} · {SM.SCORING_TIERS[2][0]:.0%} → "
                            f"${SM.SCORING_TIERS[2][1]:,}"),
        fontsize=6.9, color=F.GREY, va="center")
ax.text(0.86, -0.246, F.esc(f"below 60%: {abs(SM.FAILURE_REPUTATION_PENALTY)} reputation points and a "
                            f"${abs(SM.POOR_ANALYSIS_TREASURY_PENALTY):,} treasury penalty"),
        fontsize=6.9, color=F.GREY, va="center")
F.source(fig, "Placements are stakeholder_map.MASTER_MAP at commit 0ad1246; the migrations are "
              "SALIENCE_MIGRATIONS, which move seven of the ten in Rounds 4, 6 and 9. The Regional "
              "Journalist has an ALTERNATE_MAP entry, so both Monitor and Keep Informed score. The grid is "
              "the planning device; Chapter 1's salience Venn is the diagnostic that explains why the sort "
              "changes — §8.1.2.")
F.save(fig, "fig08_01_power_interest_grid")

# ══ Figure 8.2 — the contagion sigmoid ════════════════════════════════════
AVG_REP = sum(BP.BU_PROFILES[b]["reputation_score"] for b in
              ("pharma", "electronics", "consumer_goods", "software")) / 4
def contagion(sev):
    s = 1.0 / (1.0 + math.exp(-((sev - C.CONTAGION_MIDPOINT) / C.CONTAGION_STEEPNESS)))
    return AVG_REP - C.CONTAGION_MAX_DROP * s, C.CONTAGION_MAX_DROP * s
sev = np.linspace(0, 100, 400)
drops = np.array([contagion(s)[1] for s in sev])
fig, ax = F.newfig(h=3.4)
ax.plot(sev, drops, color=F.NAVY, lw=2.0)
ax.axhline(C.CONTAGION_MAX_DROP, color=F.GREY, lw=1.0, ls=(0, (2, 2)))
ax.text(99, C.CONTAGION_MAX_DROP - 1.2, f"saturation: {C.CONTAGION_MAX_DROP:.0f} points",
        ha="right", va="top", fontsize=7, color=F.GREY)
ax.axvline(C.CONTAGION_MIDPOINT, color=F.GREY, lw=1.0, ls=(0, (2, 2)))
ax.text(C.CONTAGION_MIDPOINT + 1.2, 2, f"midpoint {C.CONTAGION_MIDPOINT:.0f}\nhalf the drop",
        fontsize=7, color=F.GREY, va="bottom")
for s, col in [(40, F.RUST), (80, "#7A2E12")]:
    rep, d = contagion(s)
    ax.plot([s], [d], marker="o", ms=7, color=col, zorder=5)
    ax.annotate(f"severity {s}\n−{d:.1f} points → group reputation {rep:.1f}",
                xy=(s, d), xytext=(s + 6, d - 13), fontsize=7.4, color=col,
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=col, lw=1.0))
ax.set_xlabel("crisis severity"); ax.set_ylabel("reputation points erased")
ax.set_xlim(0, 100); ax.set_ylim(0, 55)
F.despine(ax)
ax.set_title("The contagion sigmoid: no cliff, but the doubling from 40 to 80 buys only 15 more points",
             loc="left", color=F.NAVY, fontsize=8.6)
F.source(fig, "engine.calc_contagion at commit 0ad1246: group reputation = mean unit reputation − "
              f"{C.CONTAGION_MAX_DROP:.0f} × sigmoid((severity − {C.CONTAGION_MIDPOINT:.0f}) ÷ "
              f"{C.CONTAGION_STEEPNESS:.0f}). Mean opening unit reputation is {AVG_REP:.0f}. The curve is "
              "already past its inflection at severity 40, which is why a crisis that doubles in severity "
              "does not double in damage — and why the marginal point of severity is cheapest to prevent early.")
F.save(fig, "fig08_02_contagion_sigmoid")

# ══ Figure 8.3 — the fatigue curve ════════════════════════════════════════
fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.1),
                             gridspec_kw=dict(wspace=0.30))
n = np.arange(0, 11)
eff = 1.0 / (1.0 + C.STAKEHOLDER_FATIGUE_FACTOR * n)
a1.plot(n, eff * 100, color=F.NAVY, lw=2.0, marker="o", ms=4.4)
for k in (0, 3, 6, 10):
    a1.annotate(f"{eff[k]*100:.0f}%", (k, eff[k] * 100), textcoords="offset points",
                xytext=(4, 6), fontsize=7.2, color=F.NAVY, fontweight="bold")
a1.set_xlabel("crises survived, lifetime"); a1.set_ylabel("recovery efficiency, %")
a1.set_xticks(n); a1.set_ylim(0, 108)
F.despine(a1)
a1.set_title("Every crisis makes the next recovery cheaper to lose", loc="left",
             color=F.NAVY, fontsize=8.6)
RECOVER = 10.0
a2.bar(n, RECOVER * eff, width=0.68, color=[F.NAVY if k % 2 == 0 else F.TEAL for k in n],
       hatch=["" if k % 2 == 0 else "///" for k in n], edgecolor="white", lw=0.7)
for k in n:
    a2.text(k, RECOVER * eff[k] + 0.18, f"{RECOVER*eff[k]:.1f}", ha="center",
            va="bottom", fontsize=6.4, color=F.INK)
a2.set_xlabel("crises survived, lifetime")
a2.set_ylabel("points actually recovered\nfrom a 10-point action")
a2.set_xticks(n); a2.set_ylim(0, 11.6)
a2.grid(axis="x", visible=False); F.despine(a2)
a2.set_title("The same action, later in the game", loc="left", color=F.NAVY, fontsize=8.6)
F.source(fig, "engine.calc_stakeholder_fatigue at commit 0ad1246: recovery_efficiency = 1 ÷ "
              f"(1 + {C.STAKEHOLDER_FATIGUE_FACTOR} × lifetime crisis count), applied to the recovery amount. "
              "A team that has been through six crises recovers a third of what the same action would have "
              "bought it in Round 1. Nothing in the interface tells the player this; the crisis count is "
              "carried in each unit's risk_factors.")
F.save(fig, "fig08_03_fatigue_curve")

# ══ Figure 8.4 — Round 4, costed today and at Year 5 ══════════════════════
BUS = ["pharma", "electronics", "consumer_goods", "software"]
NB = len(BUS)
T_PER_POINT = sum(NB * (BP.BU_PROFILES[b]["revenue_base"] / sum(BP.BU_PROFILES[x]["revenue_base"]
                  for x in BUS)) * BP.BU_PROFILES[b]["revenue_base"] / 1e6 for b in BUS)
MEAN_SLO = sum(BP.BU_PROFILES[b]["social_license_score"] for b in BUS) / NB
ROUNDS_LEFT = 7          # Round 4 through Round 10 inclusive
MULTIPLE = 18.0          # the opening state sits on the cap — §6.2.3
r4 = RC.ROUND_CONFIGS[4]["options"]
OPTS = [("A · Full Transparency\n& Remediation", "option_a", F.NAVY),
        ("B · Damage Control PR", "option_b", F.TEAL),
        ("C · Deny & Deflect", "option_c", F.RUST)]
rows = []
for label, k, col in OPTS:
    im = r4[k]["impacts"]
    cash = abs(im.get("treasury", 0)) / 1e6
    rev_group = im.get("revenue_delta", 0) * NB / 1e6
    rev_total = rev_group * ROUNDS_LEFT
    ebitda_term = rev_group
    tv = ebitda_term * MULTIPLE
    carbon = -im.get("carbon_intensity_delta", 0) * T_PER_POINT * 250 / 1e6
    ncd_round = im.get("natural_capital_debt_delta", 0) * NB * C.NCD_OPEX_PENALTY_PER_UNIT * 5 / 1e6
    slo_after = MEAN_SLO + im.get("social_license_delta", 0)
    rows.append((label, col, cash, rev_group, rev_total, tv, carbon, ncd_round, slo_after))

fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.5),
                             gridspec_kw=dict(width_ratios=[1.0, 1.55], wspace=0.30))
x = np.arange(3)
a1.bar(x, [r[2] for r in rows], width=0.62, color=[r[1] for r in rows],
       hatch=F.HATCH[:3], edgecolor="white", lw=0.8)
for i, r in enumerate(rows):
    a1.text(i, r[2] + 0.12, F.esc(f"${r[2]:.1f}m"), ha="center", va="bottom", fontsize=8,
            fontweight="bold", color=r[1])
a1.set_xticks(x); a1.set_xticklabels(["A", "B", "C"], fontsize=8)
a1.set_ylabel("cash out of treasury, $m"); a1.set_ylim(0, 7.4)
a1.grid(axis="x", visible=False); F.despine(a1)
a1.set_title("What it costs today", loc="left", color=F.NAVY, fontsize=8.8)

w = 0.26
CH = [("permanent revenue\nbase, per round", 3),
      ("cumulative revenue\nRounds 4–10", 4),
      ("terminal value\nvia EBITDA, 18×", 5)]
xs = np.arange(len(CH))
for i, r in enumerate(rows):
    vals = [r[idx] for _n, idx in CH]
    a2.bar(xs + (i - 1) * w, vals, width=w * 0.9, color=r[1], hatch=F.HATCH[i],
           edgecolor="white", lw=0.7)
    for j, v in enumerate(vals):
        if abs(v) > 0.01:
            a2.text(xs[j] + (i - 1) * w, v - 1.4, f"{v:,.0f}", ha="center", va="top",
                    fontsize=6.6, color=r[1], fontweight="bold")
        else:
            a2.plot([xs[j] + (i - 1) * w], [0], marker="_", ms=7, color=r[1])
            a2.text(xs[j] + (i - 1) * w, -1.4, "0", ha="center", va="top",
                    fontsize=6.6, color=r[1], fontweight="bold")
a2.axhline(0, color=F.GREY, lw=0.9)
a2.set_xticks(xs); a2.set_xticklabels([n for n, _i in CH], fontsize=7.0)
a2.set_ylabel(F.esc("$m, negative is value destroyed"))
a2.set_ylim(-82, 5)
a2.grid(axis="x", visible=False); F.despine(a2)
a2.set_title("What it is still worth at Year 5", loc="left", color=F.NAVY, fontsize=8.8)
a2.text(0.02, 0.06, "Reputation, licence and governance deltas\n"
                    f"all evaluate to zero here: mean licence is {MEAN_SLO:.0f}\n"
                    "and stays below the 70-point floor of the\n"
                    "Instability Discount ramp under every option,\n"
                    "and the exit multiple is on its 18× ceiling\n"
                    "either way.",
        transform=a2.transAxes, ha="left", va="bottom", fontsize=6.3, color=F.RUST,
        bbox=dict(boxstyle="round,pad=0.34", fc=F.PALE, ec=F.RUST, lw=0.7))
F.source(fig, "Impacts from round_configs.ROUND_CONFIGS[4] at commit 0ad1246. revenue_delta is added to "
              "every unit's revenue_base permanently (round_logic, generic applicator), so the per-unit figure "
              "is four times larger at group level and recurs for the seven remaining rounds. The terminal "
              "column applies the 18× exit multiple the opening state sits on. The point of the figure is the "
              "gap between the two panels: Option C is free today and the most expensive of the three by "
              "Year 5, and none of that is in the reputational language the option is written in.")
F.save(fig, "fig08_04_round4_today_year5")
print("ch08 done")
