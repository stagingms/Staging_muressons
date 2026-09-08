import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import config as C, pillar_configs as PC, round_configs as RC, bu_profiles as BP

# tiers as round_logic._apply_hr_mechanics classifies them
HIGH = {"dei_program","people_analytics","green_skills_academy","crisis_employee_support",
        "emergency_trained","responsible_ai_trained","circular_reskilled",
        "water_stewards_trained","full_severance_redeployment","employee_ownership"}
MED  = {"leadership_pipeline","engagement_survey","ohs_basic","basic_ppe","ai_upskilling",
        "cross_trained","shift_optimized","statutory_minimum_hr","retention_bonuses"}
NEG  = {"burnout_risk","hr_absent_transition"}
def tier(flags):
    fs = set(flags or [])
    if fs & HIGH: return "high"
    if fs & MED:  return "medium"
    if fs & NEG:  return "negative"
    return "none"
TIER_PARAMS = {"high": (-10.0, 0.0, C.READINESS_DELTA_HIGH),
               "medium": (-4.0, 1.0, C.READINESS_DELTA_MEDIUM),
               "negative": (12.0, 3.0, C.READINESS_DELTA_NONE),
               "none": (0.0, 3.0, C.READINESS_DELTA_NONE)}
TCOL = {"high": F.NAVY, "medium": F.TEAL, "negative": F.RUST, "none": F.GREY}

# ══ Figure 9.1 — the burnout / readiness / licence loop ═══════════════════
fig, ax = F.newfig(h=4.3)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
F.box(ax, 0.375, 0.845, 0.250, 0.120, "HR pillar choice\nhigh · medium · none", fc="white",
      ec=F.NAVY, tc=F.NAVY, size=7.6, weight="bold", lw=1.5)
F.box(ax, 0.055, 0.560, 0.255, 0.140,
      "staff_burnout_index\nper unit\n−10 high · −4 medium\n+12 neglect · drift +3",
      fc=F.PALE, ec=F.RUST, tc=F.INK, size=6.9)
F.box(ax, 0.690, 0.560, 0.255, 0.140,
      "workforce_readiness\ngroup\n+16 high · +8 medium\n−10 none",
      fc=F.PALE, ec=F.TEAL, tc=F.INK, size=6.9)
F.arrow(ax, (0.400, 0.845), (0.230, 0.700), color=F.RUST, rad=0.15)
F.arrow(ax, (0.600, 0.845), (0.790, 0.700), color=F.TEAL, rad=-0.15)
F.box(ax, 0.020, 0.315, 0.300, 0.135,
      "OPEX penalty above 20\n(burnout − 20)² × 2.8125e-05\n18% of OPEX at burnout 100",
      fc="white", ec=F.RUST, tc=F.INK, size=6.6)
F.box(ax, 0.352, 0.315, 0.296, 0.135,
      "R9 strike probability\nrises with burnout,\nup to +20 points",
      fc="white", ec=F.RUST, tc=F.INK, size=6.6)
F.box(ax, 0.680, 0.315, 0.300, 0.135,
      "R7 synergy modifier\n0.70 below 40 · 1.00 to 60\n1.10 at 60 or above",
      fc="white", ec=F.TEAL, tc=F.INK, size=6.6)
F.arrow(ax, (0.170, 0.560), (0.170, 0.450), color=F.RUST)
F.arrow(ax, (0.260, 0.560), (0.470, 0.450), color=F.RUST, rad=-0.15)
F.arrow(ax, (0.818, 0.560), (0.830, 0.450), color=F.TEAL)
F.box(ax, 0.150, 0.065, 0.700, 0.145,
      "TERMINAL VALUATION — the Just Transition scaling on the Round 9 flag,\n"
      "and the readiness bonus of +0.05 above 75",
      fc=F.NAVY, ec=F.NAVY, tc="white", size=7.6, weight="bold")
for x0 in (0.170, 0.500, 0.830):
    F.arrow(ax, (x0, 0.315), (x0, 0.210), color=F.GREY)
ax.plot([0.150, 0.008, 0.008], [0.1375, 0.1375, 0.615], color=F.GREY, lw=1.0,
        ls=(0, (3, 2)), solid_capstyle="butt")
F.arrow(ax, (0.008, 0.615), (0.055, 0.628), color=F.GREY, lw=1.0, ls=(0, (3, 2)))
ax.text(0.030, 0.790, "the loop:\nlast round's neglect\nis this round's\nOPEX", fontsize=6.4,
        color=F.GREY, style="italic", ha="left", va="top")
ax.text(0.500, 0.020, "Nothing in the loop is reversible in one round: burnout drifts up at +3 "
                      "whenever HR is skipped, and readiness falls 10.",
        ha="center", fontsize=7, color=F.RUST, style="italic")
F.source(fig, "engine.calc_burnout_accumulation and calc_workforce_readiness, and round_logic's "
              "_apply_hr_mechanics, _post_r7_circularity and _post_r9_just_transition, at commit 0ad1246. "
              "The tier deltas are the literals _apply_hr_mechanics uses; note that config's "
              f"BURNOUT_NATURAL_DRIFT of {C.BURNOUT_NATURAL_DRIFT:.0f} is the function default and is never "
              "the value play passes.")
F.save(fig, "fig09_01_hr_loop")

# ══ Figure 9.2 — the quadratic OPEX penalty ═══════════════════════════════
b = np.linspace(0, 100, 500)
rate = np.where(b > C.BURNOUT_OPEX_THRESHOLD,
                (b - C.BURNOUT_OPEX_THRESHOLD) ** 2 * C.BURNOUT_OPEX_PENALTY_COEFF, 0.0)
OPEX = sum(BP.BU_PROFILES[x]["opex_base"] for x in
           ("pharma", "electronics", "consumer_goods", "software"))
fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.2),
                             gridspec_kw=dict(wspace=0.32))
a1.plot(b, rate * 100, color=F.NAVY, lw=2.1)
a1.axvline(C.BURNOUT_OPEX_THRESHOLD, color=F.GREY, ls=(0, (2, 2)), lw=1.0)
a1.text(C.BURNOUT_OPEX_THRESHOLD + 1.5, 17.4, "nothing below 20", fontsize=7, color=F.GREY)
a1.axvline(C.BURNOUT_CRITICAL_THRESHOLD, color=F.RUST, ls=(0, (4, 2)), lw=1.1)
a1.text(C.BURNOUT_CRITICAL_THRESHOLD - 1.5, 17.4, "critical, 70 →\ngovernance risk",
        fontsize=7, color=F.RUST, ha="right")
for x in (40, 60, 80, 100):
    y = ((x - 20) ** 2) * C.BURNOUT_OPEX_PENALTY_COEFF * 100
    a1.plot([x], [y], marker="o", ms=5, color=F.NAVY, zorder=5)
    a1.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(-4, 7),
                fontsize=7, color=F.NAVY, fontweight="bold", ha="right")
a1.set_xlabel("staff_burnout_index"); a1.set_ylabel("OPEX penalty rate, %")
a1.set_xlim(0, 100); a1.set_ylim(0, 19.6)
F.despine(a1)
a1.set_title("A curve, not a cliff", loc="left", color=F.NAVY, fontsize=8.8)

rounds = np.arange(1, 11)
for i, (lab, tk) in enumerate([("neglect every round", "none"),
                               ("cheapest medium every round", "medium"),
                               ("high-quality every round", "high")]):
    d, drift, _r = TIER_PARAMS[tk]
    bo, path = 10.0, []
    for _ in rounds:
        bo = max(0.0, min(100.0, bo + d + drift)); path.append(bo)
    a2.plot(rounds, path, color=F.SERIES[i], linestyle=F.DASH[i], marker=F.MARK[i],
            ms=4.0, lw=1.8)
    a2.text(10.15, path[-1], f" {lab}\n {path[-1]:.0f} → "
            f"{max(0.0,((path[-1]-20)**2)*C.BURNOUT_OPEX_PENALTY_COEFF)*OPEX/1e6:.2f}m OPEX",
            fontsize=6.6, color=F.SERIES[i], va="center", fontweight="bold")
a2.axhline(C.BURNOUT_OPEX_THRESHOLD, color=F.GREY, ls=(0, (2, 2)), lw=1.0)
a2.axhline(C.BURNOUT_CRITICAL_THRESHOLD, color=F.RUST, ls=(0, (4, 2)), lw=1.0)
a2.set_xlabel("Round"); a2.set_ylabel("staff_burnout_index")
a2.set_xticks(rounds); a2.set_xlim(0.8, 16.5); a2.set_ylim(0, 62)
F.despine(a2)
a2.set_title("Three HR strategies, from an opening index of 10", loc="left",
             color=F.NAVY, fontsize=8.8)
F.source(fig, "engine.calc_burnout_accumulation at commit 0ad1246: penalty rate = "
              f"(burnout − {C.BURNOUT_OPEX_THRESHOLD:.0f})² × {C.BURNOUT_OPEX_PENALTY_COEFF}, zero below the "
              "threshold, 18% at 100. The right-hand paths apply the per-tier burnout delta and drift that "
              "_apply_hr_mechanics uses, from the opening index of 10 that build_bu_states sets. The dollar "
              f"figures apply the rate to the group's opening OPEX base of ${OPEX/1e6:.1f}m.")
F.save(fig, "fig09_02_burnout_penalty")

# ══ Figure 9.3 — JT scaling against prior HR investment ══════════════════
fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.2),
                             gridspec_kw=dict(width_ratios=[1.0, 1.15], wspace=0.32))
n = np.arange(0, 11)
jt = np.minimum(1.5, 1.0 + n * 0.10)
a1.plot(n, jt, color=F.NAVY, lw=2.1, marker="o", ms=4.6)
a1.axhline(1.5, color=F.RUST, ls=(0, (4, 2)), lw=1.1)
a1.text(9.8, 1.512, "cap 1.5, reached at five rounds", ha="right", va="bottom",
        fontsize=7.2, color=F.RUST, fontweight="bold")
a1.plot([5], [1.5], marker="o", ms=8, mfc="none", mec=F.RUST, mew=1.8)
a1.set_xlabel("rounds with any HR investment (high OR medium)")
a1.set_ylabel("Just Transition scaling")
a1.set_xticks(n); a1.set_ylim(0.95, 1.60)
F.despine(a1)
a1.set_title("It counts rounds, not quality", loc="left", color=F.NAVY, fontsize=8.8)

hr_opts = {}
for r in range(1, 11):
    area = PC.PILLAR_OPTIONS[r]["areas"].get("human_resources")
    for ok, o in area["options"].items():
        t = tier(o.get("flags_set"))
        if t in ("high", "medium"):
            hr_opts.setdefault(t, []).append((r, o["title"], abs(o["cost"])))
cheap = sorted(hr_opts["medium"], key=lambda x: x[2])[:5]
dear = sorted(hr_opts["high"], key=lambda x: x[2])[:5]
routes = [("five cheapest MEDIUM\noptions", cheap, F.TEAL, 1),
          ("five cheapest HIGH\noptions", dear, F.NAVY, 0)]
for i, (lab, opts, col, hi) in enumerate(routes):
    total = sum(c for _r, _t, c in opts) / 1e6
    a2.bar(i, total, width=0.55, color=col, hatch=F.HATCH[hi], edgecolor="white", lw=0.8)
    a2.text(i, total + 0.25, F.esc(f"${total:.1f}m"), ha="center", va="bottom",
            fontsize=9, fontweight="bold", color=col)
    a2.text(i, total + 1.35, "\n".join(F.esc(f"R{r} {t[:22]}  ${c/1e6:.1f}m")
            for r, t, c in opts), ha="center", va="bottom", fontsize=5.9, color=col,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, lw=0.6))
a2.set_xticks([0, 1])
a2.set_xticklabels(["five cheapest\nMEDIUM options", "five cheapest\nHIGH options"], fontsize=7.4)
a2.set_ylabel(F.esc("cost of five qualifying rounds, $m"))
a2.set_ylim(0, 21.5); a2.set_xlim(-0.62, 1.62)
a2.grid(axis="x", visible=False); F.despine(a2)
a2.set_title("The same 1.5× multiplier, two prices", loc="left", color=F.NAVY, fontsize=8.8)
F.source(fig, "terminal_valuation at commit 0ad1246: jt_scaling = min(1.5, 1 + hr_investment_rounds × 0.10), "
              "applied only when the Round 9 flag community_fund or managed_transition is present. "
              "hr_investment_rounds counts distinct rounds in which hr_quality was high OR medium — "
              "_apply_hr_mechanics treats both as invested — so the cheap route buys the identical "
              "multiplier. What it does not buy is the burnout, readiness and licence the high route buys; "
              "that is the whole of the difference, and it is not in the multiplier.")
F.save(fig, "fig09_03_jt_scaling")

# ══ Figure 9.4 — three HR strategies across the ten rounds ═══════════════
def cheapest_that_counts(r):
    area = PC.PILLAR_OPTIONS[r]["areas"]["human_resources"]
    cands = [(abs(o["cost"]), o["title"], tier(o.get("flags_set")))
             for o in area["options"].values()
             if tier(o.get("flags_set")) in ("high", "medium")]
    return min(cands)
def dearest_high(r):
    area = PC.PILLAR_OPTIONS[r]["areas"]["human_resources"]
    cands = [(abs(o["cost"]), o["title"], tier(o.get("flags_set")))
             for o in area["options"].values() if tier(o.get("flags_set")) == "high"]
    return max(cands)

STRATS = [("high quality every round", dearest_high, F.NAVY, 0),
          ("cheapest that counts", cheapest_that_counts, F.TEAL, 1),
          ("never invest", None, F.RUST, 2)]
rounds = np.arange(1, 11)
fig, axes = plt.subplots(1, 4, figsize=(F.TEXT_WIDTH_IN, 2.9))
for si, (lab, pick, col, hi) in enumerate(STRATS):
    spend, burn, read, jt = [], [], [], []
    cum, bo, rd, cnt = 0.0, 10.0, 50.0, 0
    for r in rounds:
        if pick is None:
            d, drift, rdel = TIER_PARAMS["none"]
        else:
            cost, _title, t = pick(r)
            cum += cost / 1e6
            d, drift, rdel = TIER_PARAMS[t]
            cnt += 1
        bo = max(0.0, min(100.0, bo + d + drift))
        rd = max(0.0, min(100.0, rd + rdel))
        spend.append(cum); burn.append(bo); read.append(rd)
        jt.append(min(1.5, 1.0 + cnt * 0.10))
    for a, series in zip(axes, (spend, burn, read, jt)):
        a.plot(rounds, series, color=col, linestyle=F.DASH[si], marker=F.MARK[si],
               ms=3.2, lw=1.7)
TITLES = [("cumulative HR spend", "$m"), ("staff_burnout_index", ""),
          ("workforce_readiness", ""), ("Just Transition scaling", "×")]
for a, (t, u) in zip(axes, TITLES):
    a.set_title(t, fontsize=7.4, color=F.NAVY, pad=4)
    a.set_xlabel("Round", fontsize=7); a.set_xticks([1, 4, 7, 10])
    a.tick_params(labelsize=6.6)
    F.despine(a)
axes[1].axhline(C.BURNOUT_OPEX_THRESHOLD, color=F.GREY, ls=(0, (2, 2)), lw=0.9)
axes[2].axhline(C.READINESS_LOW_THRESHOLD, color=F.RUST, ls=(0, (2, 2)), lw=0.9)
axes[2].axhline(C.READINESS_HIGH_THRESHOLD, color=F.TEAL, ls=(0, (2, 2)), lw=0.9)
axes[3].set_ylim(0.95, 1.6)
handles = [plt.Line2D([], [], color=c, linestyle=F.DASH[i], marker=F.MARK[i], ms=3.4, lw=1.7)
           for i, (_l, _p, c, _h) in enumerate(STRATS)]
fig.legend(handles, [l for l, _p, _c, _h in STRATS], loc="lower center", ncol=3,
           fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.14))
F.source(fig, "\nExecuted at commit 0ad1246 over the ten human-resources pillar option sets, from the "
              "opening burnout of 10 and readiness of 50 that build_bu_states sets, applying the per-tier "
              "deltas of _apply_hr_mechanics. 'Cheapest that counts' takes the lowest-cost option each round "
              "that still classifies as high or medium — $10.0m over ten rounds against $30.0m for the "
              "high-quality route. Both reach the 1.5 Just Transition cap by Round 5; they part company on "
              "burnout and readiness, and readiness is what gates the Round 7 synergy modifier and the "
              "+0.05 terminal bonus above 75.")
F.save(fig, "fig09_04_hr_strategies")
print("ch09 done")
