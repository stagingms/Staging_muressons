import sys, os
sys.path.insert(0, os.path.expanduser("~/audit_scratch/figs"))
sys.path.insert(0, os.path.expanduser("~/mnt/muressons-sim/backend"))
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
import bu_profiles as BP

# ══ Figure 17.1 — the value-creation model, populated ═══════════════════
CAPS = [("Financial", "treasury $50.0m\ncost of capital 6.18%", F.NAVY),
        ("Manufactured", "revenue base $53.5m\nopex base $36.5m", F.TEAL),
        ("Intellectual", "synergy 1.00\nVRIO advantage 0.80", F.RUST),
        ("Human", "readiness 50\nburnout 10", F.SERIES[3]),
        ("Social and relationship", "licence 50 · reputation 55\nfour named NPCs", F.SERIES[4]),
        ("Natural", "2,424 tCO2e · NCD 500\nwater dependency 54.25", F.SERIES[5])]
OUT = [("Outputs", "ten rounds of decisions,\nfive pillars each", F.NAVY),
       ("Outcomes — first ledger", "terminal EBITDA,\nexit multiple, equity value", F.TEAL),
       ("Outcomes — second ledger", "tonnes, licence, debt,\nreadiness at Year 5", F.RUST)]
fig, ax = F.newfig(h=4.6)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.add_patch(plt.Rectangle((0.005, 0.055), 0.990, 0.860, fc="none", ec=F.GREY, lw=1.1,
                           linestyle=(0, (5, 3))))
ax.text(0.012, 0.930, "EXTERNAL ENVIRONMENT — the macro rate cycle, the black-swan registry, "
                      "the disclosure regimes", fontsize=6.6, color=F.GREY, va="bottom")
ax.text(0.012, 0.028, "GOVERNANCE — the board, the C-suite coalition, the regulator NPC",
        fontsize=6.6, color=F.GREY, va="bottom")
rh = 0.128
for i, (nm, sub, col) in enumerate(CAPS):
    y = 0.880 - (i + 1) * rh
    F.box(ax, 0.020, y + 0.008, 0.250, rh - 0.022, f"{nm}\n{sub}", fc=F.PALE, ec=col,
          tc=F.INK, size=6.3)
    F.arrow(ax, (0.270, y + rh / 2), (0.345, 0.470), color=col, rad=0.10, lw=0.9)
ax.text(0.020, 0.895, "INPUTS — six capitals", fontsize=6.8, fontweight="bold", color=F.GREY)
F.box(ax, 0.345, 0.330, 0.230, 0.290, "THE BUSINESS MODEL\n\nfour business units,\nfive pillars,\n"
      "ten rounds", fc="white", ec=F.NAVY, tc=F.NAVY, size=7.4, weight="bold", lw=1.7)
for i, (nm, sub, col) in enumerate(OUT):
    y = 0.760 - i * 0.240
    F.box(ax, 0.650, y - 0.095, 0.330, 0.190, f"{nm}\n{sub}", fc=F.PALE, ec=col,
          tc=F.INK, size=6.5)
    F.arrow(ax, (0.575, 0.470), (0.650, y), color=col, rad=-0.10, lw=0.9)
ax.text(0.650, 0.895, "OUTPUTS AND OUTCOMES", fontsize=6.8, fontweight="bold", color=F.GREY)
F.arrow(ax, (0.815, 0.185), (0.145, 0.185), color=F.GREY, rad=-0.22, ls=(0, (3, 2)))
ax.text(0.480, 0.135, "outcomes become next year's inputs — the loop the report is supposed to close",
        ha="center", fontsize=6.4, color=F.GREY, style="italic")
F.source(fig, "The frame is the integrated-reporting value-creation model, §17.1.2. Every input is the "
              "opening state at commit 0ad1246: treasury and cost of capital from the seed and §6.2.3, the "
              "revenue and opex bases and the six-capital variables from BU_PROFILES, and the 2,424 tonnes "
              "from carbon intensity times revenue. The model is used as an organising frame; the chapter "
              "records that its custodianship is pending verification.")
F.save(fig, "fig17_01_value_creation")

# ══ Figure 17.2 — the same data, three ways ═════════════════════════════
rounds = np.arange(1, 11)
# A team that grows revenue 8% a round and cuts intensity 6% a round.
rev = 53.5 * (1.08 ** (rounds - 1))
ci = 45.31 * (0.94 ** (rounds - 1))
absol = ci * rev / 45.31 / 53.5 * 2424 / (2424 / 2424)
absol = ci * rev          # tonnes proxy: intensity x revenue, same units as the engine
fig, axes = plt.subplots(1, 3, figsize=(F.TEXT_WIDTH_IN, 3.1),
                         gridspec_kw=dict(wspace=0.48))
a = axes[0]
a.plot(rounds, ci, color=F.TEAL, lw=2.2, marker="o", ms=3.6)
a.set_ylim(0, 50); a.set_xticks([1, 5, 10]); a.set_xlabel("Round", fontsize=7)
a.set_ylabel("carbon intensity", fontsize=7)
a.set_title("MISLEADING\nintensity alone", fontsize=7.4, color=F.RUST, pad=4)
a.text(0.5, 0.06, "falls 43% — and is true", transform=a.transAxes, ha="center",
       va="bottom", fontsize=6.4, color=F.GREY, style="italic")
F.despine(a); a.tick_params(labelsize=6.6)
a = axes[1]
a.plot(rounds, absol, color=F.RUST, lw=2.2, marker="s", ms=3.6)
a.set_ylim(2000, 2900); a.set_xticks([1, 5, 10]); a.set_xlabel("Round", fontsize=7)
a.set_ylabel("tCO$_2$e", fontsize=7)
a.set_title("MISLEADING\ntruncated axis", fontsize=7.4, color=F.RUST, pad=4)
a.text(0.5, 0.06, "an 8% rise, drawn as a surge:\nthe axis starts at 2,000", transform=a.transAxes,
       ha="center", va="bottom", fontsize=6.4, color=F.GREY, style="italic")
F.despine(a); a.tick_params(labelsize=6.6)
a = axes[2]
a.plot(rounds, absol, color=F.RUST, lw=2.2, marker="s", ms=3.6, label="absolute tCO$_2$e")
a.set_ylim(0, 2900); a.set_ylabel("tCO$_2$e", fontsize=7); a.set_xlabel("Round", fontsize=7)
a2 = a.twinx()
a2.plot(rounds, ci, color=F.TEAL, lw=2.2, ls="--", marker="o", ms=3.6)
a2.set_ylim(0, 50); a2.set_ylabel("carbon intensity", fontsize=7, color=F.TEAL)
a2.tick_params(labelsize=6.6, colors=F.TEAL)
a.set_xticks([1, 5, 10]); a.tick_params(labelsize=6.6)
a.set_title("HONEST\nboth series, zero-based", fontsize=7.4, color=F.TEAL, pad=4)
a.text(0.5, 0.06, "intensity falls 43%,\nabsolute rises 8% —\nboth are true",
       transform=a.transAxes, ha="center", va="bottom", fontsize=6.4, color=F.INK,
       style="italic", fontweight="bold")
F.despine(a); F.despine(a2, keep=("right", "bottom"))
F.source(fig, "\n\nA constructed but stated example, as §17.5.1 asks for: a team growing revenue 8% a round "
              "from the opening $53.5m while cutting carbon intensity 6% a round from the opening "
              "revenue-weighted 45.31. Tonnes are intensity × revenue, the engine's own formula. Both "
              "statements are true; the first two charts each tell only one of them, and the third is the "
              "only one that lets a reader see the growth trap of Chapter 5 §5.2.2.")
F.save(fig, "fig17_02_three_ways")

# ══ Figure 17.3 — the section checklist, against two regimes ════════════
SECTIONS = [
 ("Governance", "who is accountable, and how often they look",
  "ESRS 2 GOV-1 to GOV-5", "BRSR Section A + P1"),
 ("Strategy and business model", "the value-creation model, populated",
  "ESRS 2 SBM-1 to SBM-3", "BRSR Section B"),
 ("Impacts, risks and opportunities", "the double-materiality assessment and its method",
  "ESRS 2 IRO-1, IRO-2", "BRSR Section A Q22–24"),
 ("Policies and actions", "what you decided to do about each material matter",
  "topical standards, each -1 and -2", "NGRBC principle-wise policies"),
 ("Targets and metrics", "the number, the base year, the boundary",
  "topical standards, each -3 onward", "BRSR Core, nine attributes"),
 ("Value chain", "how far the boundary reaches, and what is estimated",
  "ESRS 1 §5.1, value-chain estimation", "BRSR Core value-chain disclosure"),
 ("Assurance", "who checked it, to what standard, and what they excluded",
  "limited assurance, CSRD Art. 34", "reasonable assurance on BRSR Core"),
 ("Connectivity", "does the sustainability section explain the financial one?",
  "not a section — a test of the whole", "not a section — a test of the whole"),
]
fig, ax = F.newfig(h=4.3)
F.nogrid(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
HEAD = [(0.005, "SECTION"), (0.255, "WHAT IT HAS TO ANSWER"),
        (0.590, "ESRS / CSRD"), (0.800, "BRSR / NGRBC")]
for x, h in HEAD:
    ax.text(x, 0.995, h, fontsize=6.6, fontweight="bold", color=F.GREY, va="top")
rh = 0.111
for i, (nm, q, esrs, brsr) in enumerate(SECTIONS):
    y = 0.945 - (i + 1) * rh
    last = i == len(SECTIONS) - 1
    col = F.RUST if last else F.SERIES[i % len(F.SERIES)]
    ax.add_patch(plt.Rectangle((0.0, y + 0.004), 1.0, rh - 0.012,
                               fc=F.PALE if i % 2 == 0 else "white", ec="none"))
    ax.add_patch(plt.Rectangle((0.005, y + 0.020), 0.022, rh - 0.048, fc="white",
                               ec=col, lw=1.0, linestyle=(0, (2, 2))))
    ax.text(0.037, y + rh / 2, nm, fontsize=6.9, color=col, va="center",
            fontweight="bold")
    ax.text(0.255, y + rh / 2, q, fontsize=6.2, color=F.GREY, va="center")
    ax.text(0.590, y + rh / 2, esrs, fontsize=6.1, color=F.INK, va="center")
    ax.text(0.800, y + rh / 2, brsr, fontsize=6.1, color=F.INK, va="center")
ax.text(0.005, 0.035, "The last row is not a section and has no reference: connectivity is the test the "
                      "other seven have to pass together, and it is the one an assurer reads for.",
        fontsize=6.8, color=F.RUST, style="italic")
F.source(fig, "The eight rows are the reporting job as Chapter 17 §17.1 and §17.2 set it out. The two "
              "right-hand columns name where each is required under the two regimes Chapter 4 §4.4 "
              "describes — the European standards and India's BRSR against the NGRBC principles. The "
              "check-boxes are for the team: a section with no box ticked is a section nobody owns.")
F.save(fig, "fig17_03_section_checklist")
print("ch17 done")
