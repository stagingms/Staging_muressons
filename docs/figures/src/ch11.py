import sys, os, math
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import black_swan_registry as B, bu_profiles as BP, pillar_configs as PC, config as C

BUS = ["pharma", "electronics", "consumer_goods", "software"]
REV = {b: BP.BU_PROFILES[b]["revenue_base"] for b in BUS}
OPX = {b: BP.BU_PROFILES[b]["opex_base"] for b in BUS}
TREAS = 50_000_000
GROUP_REV, GROUP_OPX = sum(REV.values()), sum(OPX.values())

# ══ Figure 11.1 — the loss distribution the registry actually carries ═════
def loss_m(ev):
    """Round-one dollar effect of an event on the opening state, in $m."""
    im = ev["impacts"]; tot = 0.0
    tot += im.get("treasury_pct_hit", 0.0) * TREAS
    tot += im.get("treasury_flat_hit", 0.0)
    tot += im.get("revenue_pct_reduction", 0.0) * GROUP_REV
    tot -= im.get("opex_pct_increase", 0.0) * GROUP_OPX
    tgt = im.get("affected_bus")
    if tgt:
        r = sum(REV[b] for b in tgt if b in REV)
        o = sum(OPX[b] for b in tgt if b in OPX)
        tot += im.get("revenue_pct_reduction_targeted", 0.0) * r
        tot -= im.get("opex_pct_increase_targeted", 0.0) * o
    if "software_revenue_boost_pct" in im:
        tot += im["software_revenue_boost_pct"] * REV["software"]
    return tot / 1e6

GLOBAL = {k: v for k, v in B.BLACK_SWAN_EVENTS.items()
          if v.get("applicable_regions") is None}
rows = sorted(((loss_m(v), v["trigger_conditions"]["base_probability"], v["title"], k)
               for k, v in GLOBAL.items()), key=lambda r: r[0])
p_any = 1.0 - np.prod([1 - p for _l, p, _t, _k in rows])
mean = sum(l * p for l, p, _t, _k in rows)
var = sum(p * (l - mean) ** 2 for l, p, _t, _k in rows) + (1 - sum(p for _l, p, _t, _k in rows)) * mean ** 2
sd = math.sqrt(var)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.4),
                             gridspec_kw=dict(width_ratios=[1.25, 1.0], wspace=0.30))
for i, (l, p, t, _k) in enumerate(rows):
    a1.bar(l, p * 100, width=0.55, color=F.RUST if l < 0 else F.TEAL,
           hatch="///" if l >= 0 else "", edgecolor="white", lw=0.6)
    a1.text(l, p * 100 + 0.5, str(i + 1), ha="center", va="bottom", fontsize=6.4,
            color=F.INK, fontweight="bold")
a1.bar(0, (1 - p_any) * 100, width=0.55, color=F.GREY, edgecolor="white", lw=0.6)
a1.text(0, (1 - p_any) * 100 + 0.6, f"nothing happens\n{(1-p_any)*100:.1f}%", ha="center",
        va="bottom", fontsize=6.6, color=F.GREY, fontweight="bold")
xs = np.linspace(-12, 4, 400)
norm = 100 * (1 / (sd * math.sqrt(2 * math.pi))) * np.exp(-0.5 * ((xs - mean) / sd) ** 2)
a1.plot(xs, norm, color=F.NAVY, lw=1.8, ls="--")
a1.text(-11.7, 74, F.esc(f"a normal with the same mean\n({mean:.2f}m) and SD ({sd:.2f}m)"),
        fontsize=6.8, color=F.NAVY, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=F.NAVY, lw=0.7))
a1.text(-11.7, 40, "\n".join(f"{i+1}  {t}" for i, (_l, _p, t, _k) in enumerate(rows)),
        fontsize=5.8, color=F.INK, va="top",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=F.GREY, lw=0.6))
a1.set_xlabel(F.esc("effect on the round, $m")); a1.set_ylabel("probability, %")
a1.set_xlim(-12, 4); a1.set_ylim(0, 95)
F.despine(a1)
a1.set_title("One round, eight global events", loc="left", color=F.NAVY, fontsize=8.6)

losses = [l for l, _p, _t, _k in rows if l < 0]
actual = [p for l, p, _t, _k in rows if l < 0]
implied = [float(0.5 * (1 + math.erf((l - mean) / (sd * math.sqrt(2))))) for l in losses]
y = np.arange(len(losses))[::-1]
a2.barh(y - 0.18, np.array(actual) * 100, height=0.34, color=F.RUST, edgecolor="white",
        lw=0.6, label="the registry")
a2.barh(y + 0.18, np.array(implied) * 100, height=0.34, color=F.NAVY, hatch="///",
        edgecolor="white", lw=0.6, label="a normal fitted to it")
for i, (l, a, im) in enumerate(zip(losses, actual, implied)):
    ratio = a / max(im, 1e-12)
    lab = (f"{ratio:,.0f}× understated" if ratio >= 2
           else (f"{ratio:.1f}× understated" if ratio > 1
                 else "the normal is generous here"))
    a2.text(max(a, im) * 100 * 1.5, y[i], lab, va="center", fontsize=6.3,
            color=F.RUST if ratio > 1 else F.GREY)
a2.set_yticks(y)
a2.set_yticklabels([F.esc(f"${l:.1f}m") for l in losses], fontsize=7)
a2.set_xscale("log"); a2.set_xlim(1e-4, 3e4)
a2.set_xlabel("probability of a loss at least this large, % (log)")
a2.legend(fontsize=6.6, loc="upper left")
a2.grid(axis="y", visible=False); F.despine(a2)
a2.set_title("What the normal would have told you", loc="left", color=F.NAVY, fontsize=8.6)
F.source(fig, "black_swan_registry.BLACK_SWAN_EVENTS at commit 0ad1246, the eight events with no region "
              "gate, at the advanced tier (probability multiplier 1.0). Dollar effects are each event's "
              f"impacts applied to the opening state: treasury ${TREAS/1e6:.0f}m, group revenue "
              f"${GROUP_REV/1e6:.1f}m, group OPEX ${GROUP_OPX/1e6:.1f}m. The AI disruption wave is the one "
              "event with a positive expected effect. The right-hand panel is the point of §11.2.1: a normal "
              "fitted to the same mean and variance prices the tail out of existence.")
F.save(fig, "fig11_01_fat_tails")

# ══ Figure 11.2 — the four indices, two contrasting teams ════════════════
def indices(ci_simple, ncd_total, slo, burnout, rep, synergy, treasury_m, margin):
    return {
        "Stranded Asset Exposure": ci_simple * ncd_total / 1000.0,
        "Social Capital Index": slo * 0.4 + (100 - burnout) * 0.3 + rep * 0.3,
        "Takeover Vulnerability": 100 - synergy * 30 - min(treasury_m, 10) * 5 - margin * 50,
        "Compliance Risk Index": ci_simple * 0.4 + (100 - slo) * 0.3 + (100 - rep) * 0.3,
    }
# Two named decision sets, applied from Round 5. Only option deltas; no
# stochastic events and no natural decay — stated on the figure.
def run(team):
    ci = sum(BP.BU_PROFILES[b]["carbon_intensity"] for b in BUS) / 4      # 41.75 simple
    ncd = sum(BP.BU_PROFILES[b]["natural_capital_debt"] for b in BUS)     # 500
    slo, burn, rep, syn = 50.0, 10.0, 55.0, 1.00
    out = {}
    for r in range(5, 11):
        areas = PC.PILLAR_OPTIONS[r]["areas"]
        if team == "invest":
            for key in ("energy", "offsetting", "human_resources"):
                a = areas.get(key)
                if not a: continue
                best = min(a["options"].values(), key=lambda o: o["cost"])   # dearest
                im = best.get("impacts", {})
                ci += im.get("carbon_intensity_delta", 0)
                ncd += im.get("natural_capital_debt_delta", 0) * 4
                slo += im.get("social_license_delta", 0)
                rep += im.get("reputation", 0)
                if key == "human_resources":
                    burn = max(0.0, burn - 10.0)
            syn = round(syn * (1 - 0.05 * max(0.2, 1 - 0.5)), 4)
        else:
            for key in ("energy", "offsetting", "human_resources"):
                a = areas.get(key)
                if not a: continue
                free = min(a["options"].values(), key=lambda o: abs(o["cost"]))
                im = free.get("impacts", {})
                ci += im.get("carbon_intensity_delta", 0)
                ncd += im.get("natural_capital_debt_delta", 0) * 4
                slo += im.get("social_license_delta", 0)
                rep += im.get("reputation", 0)
            burn = min(100.0, burn + 3.0)
            syn = round(syn * (1 - 0.05), 4)
        ci = max(0.0, ci); ncd = max(0.0, ncd)
        slo = max(0.0, min(100.0, slo)); rep = max(0.0, min(100.0, rep))
        margin = (GROUP_REV - GROUP_OPX) / GROUP_REV
        out[r] = indices(ci, ncd, slo, burn, rep, syn, 12.0, margin)
    return out
A, Bv = run("invest"), run("harvest")
NAMES = list(A[5].keys())
ENDING = {"Stranded Asset Exposure": "Climate Black Swan",
          "Social Capital Index": "Stakeholder Revolt",
          "Takeover Vulnerability": "Hostile Takeover",
          "Compliance Risk Index": "Regulatory Shutdown"}
fig, axes = plt.subplots(1, 4, figsize=(F.TEXT_WIDTH_IN, 2.95))
rr = list(range(5, 11))
for j, nm in enumerate(NAMES):
    ax = axes[j]
    ax.plot(rr, [A[r][nm] for r in rr], color=F.NAVY, lw=1.8, marker="o", ms=3.4)
    ax.plot(rr, [Bv[r][nm] for r in rr], color=F.RUST, lw=1.8, ls="--", marker="s", ms=3.4)
    ax.set_title(nm.replace(" ", "\n", 1), fontsize=6.9, color=F.NAVY, pad=3)
    ax.set_xlabel("Round", fontsize=7); ax.set_xticks([5, 7, 10])
    ax.tick_params(labelsize=6.4)
    ax.text(0.5, -0.30, f"shown only to\n{ENDING[nm]} teams", transform=ax.transAxes,
            ha="center", va="top", fontsize=5.9, color=F.GREY, style="italic")
    F.despine(ax)
handles = [plt.Line2D([], [], color=F.NAVY, marker="o", ms=3.4, lw=1.8),
           plt.Line2D([], [], color=F.RUST, marker="s", ms=3.4, lw=1.8, ls="--")]
fig.legend(handles, ["invests every round (dearest option in Energy, Offsetting and HR)",
                     "takes the free option every round"],
           loc="lower center", ncol=2, fontsize=6.8, frameon=False, bbox_to_anchor=(0.5, -0.22))
F.source(fig, "\n\nFormulae as tabulated in §11.6.4. Trajectories are computed from the actual pillar option "
              "impacts at commit 0ad1246 for the two named decision sets, applying only those impacts — no "
              "stochastic events and no natural decay — from the opening state. Note the engine computes "
              "ONE of these four for a given team, the one belonging to its ending, and only from Round 7: "
              "the other three are drawn here because the formulae are legitimate composites, not because "
              "any team is shown all four.")
F.save(fig, "fig11_02_four_indices")

# ══ Figure 11.3 — a conditional probability tree ═════════════════════════
ev = B.BLACK_SWAN_EVENTS["whistleblower_scandal"]
base = ev["trigger_conditions"]["base_probability"]
mods = ev["trigger_conditions"]["conditional_modifiers"]
m_gov = next(m for m in mods if m.get("metric") == "governance_risk_avg")
m_gw = next(m for m in mods if m.get("flag") == "greenwashing_detected")
fig, ax = F.newfig(h=3.5)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
F.box(ax, 0.005, 0.440, 0.185, 0.120, "Whistleblower\nscandal\nbase probability", fc="white",
      ec=F.NAVY, tc=F.NAVY, size=7, weight="bold", lw=1.5)
ax.text(0.098, 0.400, f"{base:.2%} a round", ha="center", fontsize=8,
        fontweight="bold", color=F.NAVY)
NODES = [
 (0.255, 0.700, f"governance risk\nabove {m_gov['above']}?", "no", "yes",
  m_gov["probability_add"]),
 (0.520, 0.700, "greenwashing\ndetected?", "no", "yes", m_gw["probability_add"]),
]
paths = [(base, [])]
x0, xs = 0.205, 0.265
for k, (mx, my, q, no, yes, add) in enumerate(NODES):
    F.box(ax, mx, 0.680, 0.185, 0.115, q, fc=F.PALE, ec=F.RUST, tc=F.INK, size=6.9)
    ax.text(mx + 0.093, 0.660, f"+{add:.0%} if yes", ha="center", va="top", fontsize=6.4,
            color=F.RUST, fontweight="bold")
    newp = []
    for p, hist in paths:
        newp.append((p, hist + [0]))
        newp.append((p + add, hist + [1]))
    paths = newp
paths.sort(key=lambda t: t[0])
ys = np.linspace(0.150, 0.945, len(paths))
for (p, hist), yy in zip(paths, ys):
    lab = " · ".join(("gov>50" if i == 0 else "greenwash") for i, h in enumerate(hist) if h) or "neither"
    col = F.RUST if p > 0.15 else (F.SERIES[3] if p > 0.05 else F.NAVY)
    F.box(ax, 0.760, yy - 0.052, 0.235, 0.104, f"{lab}\n{p:.0%} a round", fc=F.PALE if p > 0.15 else "white",
          ec=col, tc=col, size=6.9, weight="bold" if p > 0.15 else "normal")
    F.arrow(ax, (0.712, 0.737), (0.760, yy), color=col, rad=0.10)
F.arrow(ax, (0.190, 0.500), (0.255, 0.700), color=F.NAVY, rad=-0.15)
F.arrow(ax, (0.440, 0.737), (0.520, 0.737), color=F.NAVY)
ax.text(0.005, 0.055, "The base rate is 2% a round.\nTwo conditions the team controls\ntake it to 29% — a fourteen-fold\nmove, on nothing stochastic.",
        ha="left", va="bottom", fontsize=7.2, color=F.RUST, style="italic")
F.source(fig, "black_swan_registry.BLACK_SWAN_EVENTS['whistleblower_scandal'] at commit 0ad1246: base "
              f"probability {base:.4f} a round over Rounds "
              f"{ev['trigger_conditions']['round_range'][0]}–{ev['trigger_conditions']['round_range'][1]}, "
              f"with conditional modifiers of +{m_gov['probability_add']:.0%} when mean governance risk "
              f"exceeds {m_gov['above']} and +{m_gw['probability_add']:.0%} when the greenwashing flag is "
              "set. The modifiers add; they do not multiply.")
F.save(fig, "fig11_03_probability_tree")

# ══ Figure 11.4 — the risk register, pre-filled ══════════════════════════
def impact_words(ev):
    im = ev["impacts"]; bits = []
    if "treasury_pct_hit" in im: bits.append(F.esc(f"treasury {im['treasury_pct_hit']:.0%} (${abs(im['treasury_pct_hit'])*TREAS/1e6:.1f}m)"))
    if "treasury_flat_hit" in im: bits.append(F.esc(f"treasury ${im['treasury_flat_hit']/1e6:.0f}m"))
    if "revenue_pct_reduction" in im: bits.append(f"revenue {im['revenue_pct_reduction']:.0%}")
    if "revenue_pct_reduction_targeted" in im:
        bits.append(f"revenue {im['revenue_pct_reduction_targeted']:.0%} on {', '.join(im.get('affected_bus', []))}")
    if "opex_pct_increase" in im: bits.append(f"OPEX +{im['opex_pct_increase']:.0%}")
    if "reputation_delta" in im: bits.append(f"rep {im['reputation_delta']:+d}")
    if "social_license_delta" in im: bits.append(f"licence {im['social_license_delta']:+d}")
    if "governance_risk_delta" in im: bits.append(f"gov {im['governance_risk_delta']:+d}")
    if "burnout_delta" in im: bits.append(f"burnout {im['burnout_delta']:+d}")
    return " · ".join(bits[:4])
def corr_words(ev):
    mods = ev["trigger_conditions"].get("conditional_modifiers") or []
    if not mods: return "— none: fires on the roll alone"
    out = []
    for m in mods:
        if "metric" in m:
            side = f"above {m['above']}" if "above" in m else f"below {m['below']}"
            out.append(f"{m['metric']} {side} {m['probability_add']:+.0%}")
        else:
            out.append(f"flag {m['flag']} {m['probability_add']:+.0%}")
    return " · ".join(out)

ALL = sorted(B.BLACK_SWAN_EVENTS.items(),
             key=lambda kv: -kv[1]["trigger_conditions"]["base_probability"])
fig, ax = F.newfig(h=5.6)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
HEAD = [(0.005, "RISK"), (0.215, "LIKELIHOOD"), (0.320, "IMPACT"),
        (0.660, "VELOCITY"), (0.745, "CORRELATION — what moves it")]
for x, h in HEAD:
    ax.text(x, 0.992, h, fontsize=6.6, fontweight="bold", color=F.GREY, va="top")
rh = 0.0705
for i, (k, ev) in enumerate(ALL):
    y = 0.955 - (i + 1) * rh
    reg = ev.get("applicable_regions")
    col = F.GREY if reg else F.SERIES[i % len(F.SERIES)]
    tc = ev["trigger_conditions"]
    ax.add_patch(plt.Rectangle((0.0, y), 1.0, rh - 0.006,
                               fc=F.PALE if i % 2 == 0 else "white", ec="none"))
    nm = ev["title"] + (f"  [{reg[0]}]" if reg else "")
    ax.text(0.005, y + rh / 2, nm, fontsize=6.4, color=col, va="center",
            fontweight="normal" if reg else "bold")
    ax.text(0.215, y + rh / 2, f"{tc['base_probability']:.2%}/round\nR{tc['round_range'][0]}–{tc['round_range'][1]}",
            fontsize=5.9, color=F.INK, va="center")
    ax.text(0.320, y + rh / 2, impact_words(ev), fontsize=5.8, color=F.INK, va="center")
    ax.text(0.660, y + rh / 2, f"{ev.get('duration_rounds', 1)} round"
            + ("s" if ev.get("duration_rounds", 1) != 1 else ""),
            fontsize=5.9, color=F.INK, va="center")
    ax.text(0.745, y + rh / 2, corr_words(ev), fontsize=5.6, color=F.GREY, va="center")
ax.text(0.005, 0.022, "Five of the thirteen are region-gated and fire only for a cohort whose region is set "
                      "— and for none at all if the facilitator left it blank.",
        fontsize=6.6, color=F.RUST, style="italic")
F.source(fig, "The whole of black_swan_registry.BLACK_SWAN_EVENTS at commit 0ad1246, laid out in the four "
              "columns §11.7 prescribes. Likelihood is the base probability per round over the stated round "
              "range, before the difficulty tier's probability multiplier (0.5 foundation, 1.0 advanced, "
              "1.5 expert) and before a one-round global cool-down after any event fires. Velocity is the "
              "registry's own duration field; correlation is its conditional_modifiers, which name the "
              "state each risk shares with the others.")
F.save(fig, "fig11_04_risk_register")
print("ch11 done")
