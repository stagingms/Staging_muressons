# Muressons SDD — Fact-Check Changelog (v1.0 → v1.1)

Every claim in the Simulation Design Document was checked against the live code and config
(`simulation_config.json`, `backend/`, `SIMULATION_CONTEXT.md`). Structure and prose were kept;
only factual drift was corrected. Corrections below, with the authoritative source.

| # | §  | Was | Now (corrected) | Source |
|---|----|-----|-----------------|--------|
| 1 | 3 · Round 1 | R1 sets/fails to set the `stakeholder_audit_complete` flag, cascading to R4 **and R7** | R1 sets `deep_audit_completed` (Full Supplier Audit) or, on a shallow tier-1 screen/deferral, `electronics_blindspot`; the **`electronics_blindspot`** flag is what cascades to R4, doubling its contagion severity. `stakeholder_audit_complete` does not exist. | `backend/pillar_configs.py`, `admin_teleprompter.py`, `admin_router.py` (R1→R4 severity 40→80) |
| 2 | 3 · Round 3 | Deferral activates the `scope3_deferred` flag | Deferral activates the **`carbon_deferred`** flag. `scope3_deferred` does not exist. | `backend/pillar_configs.py` (R3 `carbon_deferred`) |
| 3 | 7.2 | M_R range **0.6 to 2.0+** | M_R range **≈ 0.0 to 2.03**; the 0.6 figure is only the survival-mode/turnaround cap | `SIMULATION_CONTEXT.md` §8; `turnaround_pathway.crisis.mr_cap = 0.6` |
| 4 | 7.4 | Archetypes: Regenerative Leader / Pragmatic Steward / Idealistic Innovator / Legacy Operator (2-axis M_R × Terminal Value) | Actual M_R-banded archetypes: **The Regenerative Titan** (≥1.8), **The De-risked Safe-Haven** (1.2–1.79), **The Fragile Giant** (0.8–1.19), **The Stranded Relic** (<0.8), plus **The Turnaround Manager** (survival, M_R capped 0.80); each pathway supplies override titles/icons | `SIMULATION_CONTEXT.md` §8 (Company Archetypes) |
| 5 | 7.5 | Pathways: Renewable Transition, Carbon Lock-In, Circular Reboot | Five real pathways: **Activist Ultimatum** (default), **Climate Black Swan**, **Stakeholder Revolt**, **Hostile Takeover**, **Regulatory Shutdown** | `simulation_config.json` `pathway_difficulty`; `backend/admin_shared.py`; `SIMULATION_CONTEXT.md` §6 |
| 6 | 8.1 | Difficulty tiers implied as Standard → Advanced → Expert with an omitted lower tier | Added the **Introductory (Easy)** tier below Standard: 0.5× Black Swan probability, 0.7× impact, −$500M treasury floor | `backend/black_swan_registry.py` `DIFFICULTY_TIERS` |
| 7 | 8.3 | Expert tier: "Black Swan multiplier increases to **2.0x**" | Corrected: the Executive (Expert) tier is the platform maximum — **1.5× probability, 1.3× impact**, treasury floor −$50M; there is **no** higher multiplier tier | `backend/black_swan_registry.py` (`expert`: 1.5/1.3) |

## Verified correct — no change needed
- **10 rounds** (`simulation_settings.rounds = 10`).
- **JT Scaling Factor** `min(1.5, 1.0 + HR_investment_rounds × 0.10)` — matches `backend/terminal_valuation.py` / `round_logic.py` exactly.
- **Greenwashing:** 15% investment threshold and −15 reputation penalty — matches `engine_parameters.greenwashing` (`investment_threshold 0.15`, `bu_rep_penalty -15`).
- **M_SDG** up to **1.26** — matches `SIMULATION_CONTEXT.md` §8 (range 0.97→1.26).
- **RBAC (§15):** role ladder, level numbers, guards, and rights matrix all match `backend/admin_shared.py` `ROLE_HIERARCHY` and the five FastAPI guards. No drift.
- **Verticals (§9):** Oil & Gas, Banking, Agriculture, and the Healthcare Edition are all real (`backend/bu_profiles.py`, `healthcare_configs.py`). Note: the engine also ships Retail/FMCG and Technology (AI/Cloud) verticals not described here — left untouched per "fact-check & correct" scope (not gap-filling).

## Residual items (flagged, not changed — could not confirm from code)
- **§2.2 / §3 Round 2:** the "18 ESG topics" count and the "−10 reputation penalty for missing Q1 nodes below 90% accuracy." The 90% accuracy gate is confirmed (`CFO Materiality Gate → $2M bonus at ≥90%`), but the specific topic count and the −10 penalty value were not verifiable in the current code; the materiality set is vertical-specific in `backend/materiality_db.py`. Recommend confirming with the R2 owner before the next revision.
