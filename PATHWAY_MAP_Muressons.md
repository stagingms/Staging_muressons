# Muressons Global Corporation — Complete Pathway Map

A structural review of every branching mechanism in the simulation: configuration levers, the round-by-round decision spine, side-tracks, the mid-game archetype branch, the five alternate endings, and terminal outcomes. Reconstructed directly from the codebase (`round_configs.py`, `branching_engine.py`, `ending_pathways.py`, `paradigm_registry.py`, `side_tracks/*`, `terminal_valuation.py`) and cross-checked against `SIMULATION_CONTEXT.md`.

The companion file `PATHWAY_MAP_Muressons.html` renders this as an interactive visual — open it in any browser.

---

## The seven-layer architecture

Muressons is not a single linear game. It is a linear 10-round spine wrapped in a large configuration space, interrupted by optional parallel tracks, forked in the middle by a hidden archetype classifier, and terminated by one of five pre-selected crisis endings. The pathways compose across seven layers.

### Layer 0 — Session configuration (set before play)

Seven independent levers are chosen by God Mode / the Facilitator at session creation, before any player decision:

1. **Paradigm (5):** `legacy_abc`, `advanced_climate`, `un_sdg`, `healthcare`, `multi_toggles`. Each swaps the round-config provider in `paradigm_registry.py`. `advanced_climate` shares the legacy round configs but changes engine behaviour; only `multi_toggles` adds the five-pillar decision layer on top of the crisis. Unknown or blank paradigms fall back to `legacy_abc`.
2. **Vertical BU substitutions (5):** Oil & Gas, Banking/Financial Services, Retail/FMCG, Agriculture, Technology can replace default slots (Pharma, Electronics, Consumer Goods, Software) under slot-fit rules. Each vertical carries its own Round-1 "blindspot" flag (e.g. `refinery_blindspot`, `governance_blindspot`, `land_use_blindspot`).
3. **Difficulty tier (3):** Easy (0.5× probability, 0.7× impact, −$500M treasury floor), Standard (1.0×/1.0×/−$200M), Expert (1.5×/1.3×/−$50M).
4. **Region (5):** ASEAN, South Asia, Europe, North America, Africa — unlocks region-specific Black Swan events.
5. **Ending pathway (5 + random):** replaces the R10 crisis and drives R5–R8 foreshadowing.
6. **Side tracks (0–6):** any subset of six parallel mini-sims plus injection timing.
7. **Extended horizon / Turnaround mode:** optional add-ons (Rounds 11–20; or the 4-stage crisis-recovery ladder).

### Layer 1 — The 10-round main spine

Each round presents one thematic crisis with three strategic options (A / B / C). In `multi_toggles`, the player *also* chooses one of three options across five pillars (Energy, Operations, Supply Chain, Offsetting, Human Resources) each round. Post-round, the engine resolves ~40 coupled mechanics.

| Round | Theme | Option A | Option B | Option C |
|---|---|---|---|---|
| R1 | Foundations (ESG audit) | Surface-Level Scan | Deep Forensic Audit | Phased Rollout |
| R2 | Double Materiality | Full Alignment | Strategic Exceptions | CEO-Only Sign-Off |
| R3 | Scope 3 supply chain | Rapid Supplier Switch | Green Bond Investment | Offset & Defer |
| R4 | Contagion (rep cascade) | Full Transparency | Damage-Control PR | Deny & Deflect |
| R5 ★ | Climate physical risk | Hard Engineering | Nature-Based Solutions | Insurance Only |
| R6 | AI Bias | Monetise the Algorithm | Ethical AI Overhaul | Quiet Patch |
| R7 | Circularity | Full Circular Redesign | Extended Producer Responsibility | Waste-to-Energy |
| R8 | Blue Stress (water) | Efficiency for All BUs | Prioritise Electronics | Desalination Mega-Project |
| R9 | Just Transition | Immediate Closure | Managed Transition | Community Investment Fund |
| R10 🏁 | Grand Finale | *(branches by ending pathway — Layer 4)* | | |

**R5 is the structural pivot.** Beyond the climate crisis, three things fire: the Shadow Board director decisions (Layer 3), the hidden archetype classification (Layer 3), and the start of ending-pathway foreshadowing (Layer 4). R4's severity is pre-wired by the R1 audit choice — a deep audit halves it (40), a blindspot doubles it (80).

Decisions set boolean flags that rewire later rounds. Notable chains: `deep_audit_completed`/`electronics_blindspot` (R1→R4 severity), `materiality_aligned` (R2→+0.10 M_R), `blockchain_traceability` (R2→prevents R8 scandal), `early_decarboniser` (R3→+0.10 synergy at R7), `insurance_only` (R5→blocks resilience bonus at R10), `ethical_ai_overhaul` (R6→+0.15 M_R), `synergy_unlock` (R7→+0.15 M_R), `community_fund`/`managed_transition` (R9→+0.18/+0.12 M_R).

### Layer 2 — Side tracks (6 parallel mini-sims)

Self-contained tracks that pause the main sim when injected. They read main state in (`seed_from_main_state`) and write flags back out (`write_back_to_main`). Prerequisites form a dependency graph.

| Track | Rounds | Window | Prerequisite | Terminal effect |
|---|---|---|---|---|
| 🔗 Supply Chain | 7 | R3–R8 | none | Cuts Black-Swan probability |
| ⚖️ Ethics & Sustainability | 5 | R2–R7 | supply_chain | Improves BRSR start |
| 🤝 Stakeholder Management | 4 | R1–R6 | none | SLO floor + fatigue modifiers |
| 📊 Sustainability Reporting | 5 | R2–R8 | ethics_sustainability | `regulatory_readiness` |
| 🌐 Corporate SDG Deep Track | 5 | R1–R8 | none | **M_SDG** multiplier (0.97–1.26) |
| 🇮🇳 BRSR NGRBC Deep Dive | 10 | R2–R8 | sustainability_reporting + ethics_sustainability | `brsr_net_positive_dividend` (+0.05 M_R) |

The prerequisite chain **supply_chain → ethics_sustainability → sustainability_reporting → brsr_ngrbc** means a facilitator building toward BRSR must enable the whole upstream chain. Stakeholder Management and Corporate SDG are standalone.

### Layer 3 — The R5 archetype branch

At the R5 checkpoint, `classify_player_archetype()` reads cumulative reputation, average social licence, average carbon intensity, and reputation trend, then routes the player into one of four archetypes that set a crisis-severity multiplier and reskin the R6–R10 narrative:

- 🌱 **Regenerative Leader** (rep ≥65, SLO ≥60, CI ≤45): crisis ×0.8, +10 stakeholder support — scaling & legacy opportunities.
- ⚖️ **Pragmatic Optimizer** (rep 40–65, treasury ≥$30M): crisis ×1.0 — the "sensible middle," disruption tests.
- 🔄 **Turnaround Candidate** (reputation improving vs R2 + recent ESG spend): crisis ×1.2, +5 support — credibility tests.
- 🔥 **Fragile Extractor** (rep ≤40, SLO ≤40): crisis ×1.5, −10 support — "the reckoning," survival mode.

On top of the archetype multiplier, `calc_adaptive_crisis_severity()` computes a performance index and scales crises up to 1.3× for strong players or down to 0.8× for strugglers, with a further +5%/round escalation after R5.

**Shadow Board (also R5):** three directors present recommendations; rejecting each sets a penalty flag — Planet → `planet_expendable` (−0.20 M_R, amplifies Climate Black Swan), Shareholder → `shareholder_alienated` (−0.20 M_R in Hostile Takeover), Governance → `governance_fragility` (−0.25 M_R in Regulatory Shutdown, plus a BRSR whistleblower leak).

### Layer 4 — Alternate endings (5 pathways × 3 options)

The pre-selected pathway (or `random`) replaces the R10 crisis. Players are fed matching foreshadowing news from R5–R8 but never see the pathway name.

| Pathway | R10 crisis | Difficulty | Options (A / B / C) |
|---|---|---|---|
| 🏛️ Activist Ultimatum *(default)* | Activist Ultimatum | 1.00 | Resist & Integrate *(needs synergy>80)* / Spin-off / Divest |
| 🌋 Climate Black Swan | The Stranded Asset Reckoning | 1.15 | Emergency Decarbonisation / Climate Adaptation / Deny & Delay |
| 🪧 Stakeholder Revolt | The Social Reckoning | 1.10 | Total Compact / Selective Appeasement / Corporate Hardball |
| 🦈 Hostile Takeover | The Corporate Raider | 1.20 | White Knight / Poison Pill + Crown Jewel / Accept Bid |
| ⚖️ Regulatory Shutdown | The Compliance Reckoning | 1.12 | Full Remediation / Consent Decree / Contest the Ruling |

Each pathway additionally carries four **archetype-override skins** that rename the final outcome by terminal M_R (e.g. Climate Black Swan → Climate Pioneer / Adapted Enterprise / Stranded Giant / Fossil Relic). That yields 5 × 3 × 4 = **60 distinct R10 outcome states** before terminal-valuation numbers. The difficulty coefficient normalises M_R across pathways for fair leaderboard comparison.

### Layer 5 — Terminal valuation → company archetype

After R10 the game collapses into the **Regenerative Multiple (M_R, 0.0–~2.03)**, assembled from every flag earned across all layers, then multiplied by the exit multiple, M_SDG (side-track), and pathway difficulty. M_R lands the company in one of five terminal archetypes: 🌱 Regenerative Titan (≥1.8), 🏦 De-risked Safe-Haven (1.2–1.79), ⚠️ Fragile Giant (0.8–1.19), 💀 Stranded Relic (<0.8), or 🔧 Turnaround Manager (survival mode, M_R capped 0.80).

### Layer 6 — Always-on stochastic overlays

Independent of the chosen path, every round rolls: 8 global + 5 region-specific Black Swan events (probability compounding on poor metrics, scaled by difficulty tier); scripted stochastics (R5 cyclone damage roll, R9 strike probability, greenwashing engine, macro rate cycles, FX risk); and the R5–R8 foreshadowing feed.

---

## How large is the pathway space?

The pathways multiply rather than add. A single illustrative configuration slice:

- Paradigm (5) × difficulty (3) × region (5) × ending (5) = **375 session frames** before any player choice.
- The main spine alone: 10 rounds × 3 crisis options = 3¹⁰ ≈ **59,000** crisis-only sequences; in `multi_toggles`, the five pillars add 3⁵ = 243 combinations *per round*, i.e. (3 × 243)¹⁰ decision states.
- The R5 branch (4 archetypes) × adaptive scaling reshapes R6–R10 on top of that.
- Side tracks: any subset of 6 (respecting the prerequisite DAG) with variable injection timing.
- Endings: 60 distinct R10 outcome states, funnelling into 5 terminal archetypes.

The design intent is that the *config layer* gives facilitators a bounded, curated set of scenarios, while the *decision + branch + ending layers* make each team's run through a given scenario meaningfully distinct and non-repeatable.

---

## Coverage checklist

- [x] Configuration levers — paradigms, verticals, difficulty, region, ending, side-tracks, extended/turnaround modes
- [x] Main 10-round spine — every crisis + A/B/C options + pillar layer
- [x] Cross-round flag dependency graph
- [x] All 6 side tracks + prerequisite DAG + write-back effects
- [x] R5 archetype branch (4 archetypes) + adaptive severity + Shadow Board
- [x] All 5 endings × 3 options × 4 archetype skins
- [x] Terminal valuation → 5 company archetypes
- [x] Stochastic overlays (Black Swans, scripted rolls, foreshadowing)

*Sources: `backend/round_configs.py`, `branching_engine.py`, `ending_pathways.py`, `paradigm_registry.py`, `side_tracks/*`, `terminal_valuation.py`, `shadow_board_audit.py`, `config.py`, `simulation_config.json`, `SIMULATION_CONTEXT.md`.*
