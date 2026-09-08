import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import engine, config as CFG, bu_profiles as BP

DAMP = engine.SYNERGY_DAMPENING_FACTOR              # 0.70
CEIL = engine.SYNERGY_MAX_REDUCTION_PER_ROUND       # 0.06
DECAY = CFG.DEFAULT_IMITATION_DECAY_RATE            # 0.05

def reduction(ratio, S=1.0):
    captured = min(1.0, np.sqrt(ratio) * DAMP * S)
    return CEIL * captured

# ══ Figure 3.1 — the synergy curve, and why spreading wins ═════════════════
fig, (a1, a2) = plt.subplots(1, 2, figsize=(F.TEXT_WIDTH_IN, 3.15),
                             gridspec_kw=dict(width_ratios=[1.32, 1.0], wspace=0.34))

r = np.linspace(0, 1, 400)
for i, S in enumerate([0.80, 1.00, 1.30, 1.60]):
    y = np.array([reduction(x, S) for x in r]) * 100
    a1.plot(r, y, color=F.SERIES[i], linestyle=F.DASH[i], lw=1.7)
    a1.text(1.015, y[-1] + (0.22 if S == 1.60 else 0), f"S = {S:.2f}", color=F.SERIES[i], fontsize=7.4,
            va="center", fontweight="bold")
a1.axhline(CEIL * 100, color=F.RUST, lw=1.0, ls=(0, (1, 1.6)))
a1.text(0.02, CEIL * 100 - 0.16, f"ceiling {CEIL:.0%} a round", color=F.RUST,
        fontsize=7.2, va="top", fontweight="bold")
MARKS = [(0.05, 0.94), (0.10, 1.33), (0.25, 2.10), (0.50, 2.97), (1.00, 4.20)]
for x, v in MARKS:
    a1.plot([x], [v], marker="o", ms=4.4, color=F.NAVY, zorder=5)
    a1.annotate(f"{v:.2f}%", (x, v), textcoords="offset points", xytext=(2, -9),
                fontsize=6.8, color=F.NAVY)
a1.set_xlabel("Investment ratio (capex ÷ CSF pool)")
a1.set_ylabel("OPEX reduction this round, %")
a1.set_xlim(0, 1.30); a1.set_ylim(0, 6.8)
a1.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
a1.set_title("reduction = 6% × min(1, √ratio × 0.7 × S)", loc="left",
             color=F.NAVY, fontsize=8.6)
F.despine(a1)

OPEX = {k: BP.BU_PROFILES[k]["opex_base"] for k in
        ("pharma", "electronics", "consumer_goods", "software")}
POOL = 10_000_000
conc = OPEX["pharma"] * reduction(1.0)
spread = {k: v * reduction(0.25) for k, v in OPEX.items()}
names = ["Pharma", "Electronics", "Consumer\nGoods", "Software"]
a2.bar([0], [conc / 1000], width=0.62, color=F.SERIES[0], hatch=F.HATCH[0],
       edgecolor="white", lw=0.7)
bottom = 0.0
for i, (k, v) in enumerate(spread.items()):
    a2.bar([1], [v / 1000], bottom=bottom / 1000, width=0.62, color=F.SERIES[i],
           hatch=F.HATCH[i], edgecolor="white", lw=0.7)
    a2.text(1.36, (bottom + v / 2) / 1000, names[i].replace("\n", " "),
            ha="left", va="center", fontsize=6.5, color=F.SERIES[i], fontweight="bold")
    bottom += v
a2.text(0, conc / 1000 + 18, f"${conc/1000:,.0f}k", ha="center", fontsize=8,
        fontweight="bold", color=F.NAVY)
a2.text(1, bottom / 1000 + 18, f"${bottom/1000:,.0f}k", ha="center", fontsize=8,
        fontweight="bold", color=F.RUST)
a2.set_xticks([0, 1])
a2.set_xticklabels(["all $10m\ninto Pharma", "$2.5m into\neach unit"], fontsize=7.4)
a2.set_ylabel("OPEX reduction, $ thousand")
a2.set_xlim(-0.55, 2.25)
a2.set_ylim(0, bottom / 1000 * 1.22)
a2.grid(axis="x", visible=False)
a2.set_title(f"Same cash. {(bottom/conc - 1)*100:.0f}% more reduction.",
             loc="left", color=F.NAVY, fontsize=8.6)
F.despine(a2)
F.source(fig, "Executed against engine.calc_synergy_opex at commit 0ad1246 "
              f"(dampening {DAMP}, ceiling {CEIL:.0%} a round). Marked points and the right-hand comparison "
              "reproduce the worked figures in §3.3.2 and §3.3.3. OPEX bases are BU_PROFILES. "
              "Note the ceiling binds only when √ratio × 0.7 × S reaches 1 — at a full ratio that needs S ≥ 1.43.")
F.save(fig, "fig03_01_synergy_curve")

# ══ Figure 3.2 — the stock that leaks ══════════════════════════════════════
fig, ax = F.newfig(h=3.3)
rounds = np.arange(1, 11)
GATE = 0.80
for i, ratio in enumerate([0.00, 0.25, 0.50, 0.80]):
    eff = DECAY * max(0.2, 1.0 - ratio)
    s = [1.0]
    for _ in range(9):                       # nine decays, Round 1 to Round 10
        s.append(s[-1] * (1 - eff))
    ax.plot(rounds, s, color=F.SERIES[i], linestyle=F.DASH[i], marker=F.MARK[i],
            ms=3.6, lw=1.7)
    ax.text(10.12, s[-1], f"  {ratio:.0%} ratio → {s[-1]:.3f}", color=F.SERIES[i],
            fontsize=7.4, va="center", fontweight="bold")
ax.axhline(GATE, color=F.RUST, lw=1.2, ls=(0, (4, 2)))
ax.text(1.05, GATE + 0.008, "Round-10 synergy gate, 0.80 — below it, Resist & Integrate is not offered",
        color=F.RUST, fontsize=7.2, va="bottom", fontweight="bold")
ax.annotate("0.796 — a hair under", xy=(10, 0.7963), xytext=(7.4, 0.700),
            fontsize=7.2, color=F.RUST,
            arrowprops=dict(arrowstyle="->", color=F.RUST, lw=0.9))
ax.set_xlabel("Round"); ax.set_ylabel("Group synergy multiplier S")
ax.set_xlim(0.9, 12.6); ax.set_ylim(0.58, 1.03); ax.set_xticks(rounds)
ax.set_title("Advantage is a stock, and it leaks at a rate reinvestment slows",
             loc="left", color=F.NAVY)
F.despine(ax)
F.source(fig, f"Executed from S = 1.00 over the nine decays between Round 1 and Round 10. "
              f"effective_rate = {DECAY} × max(0.2, 1 − average investment ratio); "
              "S_next = S × (1 − effective_rate), engine.py §5 at commit 0ad1246. End values reproduce §3.4.2. "
              "The 0.20 floor means even a fully reinvesting group still leaks 1% a round.")
F.save(fig, "fig03_02_vrio_decay")

# ══ Figure 3.3 — the slot-fit matrix ═══════════════════════════════════════
SLOTS = BP.DEFAULT_SLOTS
fit = BP.SLOT_FIT_MAP
rows = []
for s in SLOTS:
    rows.append((s, s, True))                       # the default occupant
    for v in fit[s]:
        rows.append((v, s, False))

fig, ax = F.newfig(h=4.15)
F.nogrid(ax)
ncol = len(SLOTS)
ax.set_ylim(-0.15, len(rows) + 1.0)
SLOT_LABEL = {"pharma": "PHARMA", "electronics": "ELECTRONICS",
              "consumer_goods": "CONS. GOODS", "software": "SOFTWARE"}
for j, s in enumerate(SLOTS):
    ax.text(j + 0.5, len(rows) + 0.62, SLOT_LABEL[s], ha="center", va="center",
            fontsize=6.8, fontweight="bold", color=F.SERIES[j])
    ax.text(j + 0.5, len(rows) + 0.24, "slot", ha="center", va="center",
            fontsize=6.8, color=F.GREY)
for i, (v, s, is_default) in enumerate(rows):
    y = len(rows) - 1 - i
    prof = BP.BU_PROFILES[v]
    ax.text(-0.12, y + 0.5, prof["label"].replace("Muressons ", ""), ha="right",
            va="center", fontsize=7.2,
            fontweight="bold" if is_default else "normal",
            color=F.INK if is_default else F.GREY)
    ax.text(ncol + 0.10, y + 0.5,
            f"${prof['revenue_base']/1e6:.1f}m rev   CI {prof['carbon_intensity']:>3}   "
            f"gov {prof['governance_risk_score']:>2}   water {prof['water_dependency']:>2}",
            ha="left", va="center", fontsize=6.6, color=F.GREY, family="monospace")
    for j, sl in enumerate(SLOTS):
        ok = (sl == s)
        if ok:
            ax.add_patch(plt.Rectangle((j + 0.06, y + 0.10), 0.88, 0.80,
                                       facecolor=F.PALE, edgecolor=F.SERIES[j],
                                       lw=1.2 if is_default else 0.8,
                                       linestyle="-" if is_default else "--"))
            ax.text(j + 0.5, y + 0.5, "default" if is_default else "eligible",
                    ha="center", va="center", fontsize=6.8,
                    fontweight="bold" if is_default else "normal",
                    color=F.SERIES[j])
        else:
            ax.plot([j + 0.5], [y + 0.5], marker="_", ms=5, color="#C7D0D8")
ax.set_xlim(-2.35, ncol + 3.15)
F.source(fig, "bu_profiles.SLOT_FIT_MAP, DEFAULT_SLOTS and BU_PROFILES at engine commit 0ad1246: seventeen "
              "profiles, four defaults and thirteen verticals, each eligible for exactly one slot. "
              "A dash means the registry will not accept that substitution. CI is carbon intensity; "
              "gov is the opening governance-risk score; water is water dependency.")
F.save(fig, "fig03_03_slot_fit")
print("ch03 done")
