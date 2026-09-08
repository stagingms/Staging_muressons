# Appendix I — The Side Tracks

Extraction basis: repo `muressons-sim`, git HEAD `0ad1246`.
All paths below are relative to `backend/` unless stated otherwise.
Every claim in this file was read from the code at that commit. Where a fact
is absent from the code it is written NOT FOUND. Nothing is inferred.

---

## 0. The common contract (`side_tracks/base_track.py`, 414 lines)

`BaseSideTrack(ABC)` — `base_track.py:30`.

Class docstring (`base_track.py:31-54`), quoted:

> "Abstract base class for side simulation tracks.
>
>     Architecture:
>         - Each track is a self-contained mini-simulation (4–7 rounds).
>         - Tracks run SEQUENTIALLY: the main sim pauses while a side track is active.
>         - Tracks use the FULL process_tick() engine with all 8 formulas.
>         - Data bridges allow bidirectional state flow with the main simulation."

(Note: the docstring says 4–7 rounds; `brsr_ngrbc` declares 10 — see §7.)

### Abstract members every track must implement
| Member | Line | Kind |
|---|---|---|
| `track_id` | `base_track.py:57-61` | property (str) |
| `display_name` | `base_track.py:63-67` | property (str) |
| `description` | `base_track.py:68-71` | property (str) |
| `icon` | `base_track.py:72-75` | property (str) |
| `num_rounds` | `base_track.py:79-83` | property (int) |
| `available_window` | `base_track.py:85-91` | property `tuple[int,int]` |
| `get_round_configs()` | `base_track.py:110-118` | method |
| `seed_from_main_state()` | `base_track.py:128-158` | READ bridge → `DataBridgeInput` |
| `write_back_to_main()` | `base_track.py:160-190` | WRITE bridge → `DataBridgeOutput` |
| `calculate_score()` | `base_track.py:192-212` | method |

### Non-abstract members with defaults
- `scoring_dimensions` → default `[]` (`base_track.py:92-99`). Each entry is
  `{"id": ..., "label": ..., "unit": ...}` — a **label only**, no weight field.
- `cross_track_prerequisites` → default `[]` (`base_track.py:101-107`).
- `base_crisis_severity: float = 40.0` (`base_track.py:220`). No track overrides it
  (verified: no `base_crisis_severity` assignment in any of the six `track.py` files).
- `pre_tick()` default pass-through (`base_track.py:222-243`).
- `post_tick()` default = `_apply_default_option_impacts` (`base_track.py:245-265`).

### `_apply_default_option_impacts` (`base_track.py:290-390`)
Generic impact applicator reading `option["impacts"]` from the round config and
writing into the **track's own** `gs` / `bus`:
- `treasury` → `gs["corporate_treasury"] += impacts["treasury"]` (`:302-308`)
- `reputation` → `gs["group_reputation"]`, clamped `[0,100]` (`:310-316`)
- `natural_capital_debt_delta` → each BU's `natural_capital_debt`, floor 0 (`:318-325`)
- `carbon_intensity_delta` → via `engine.apply_ci_delta_in_place` with
  `ci_routing` (default `"uniform"`); on any exception falls back to uniform (`:327-350`)
- `governance_risk_delta` → each BU, clamped `[0,100]` (`:352-359`)
- `social_license_delta` → each BU, clamped `[0,100]` (`:361-368`)
- Any other `impacts` key → emitted as event `st_{track_id}_custom_{key}` (`:370-387`),
  with a collision warning if the key starts with one of `_RESERVED_PREFIXES`
  = `("terminal_", "mr_", "strike_", "climate_", "pathway_", "insolvency_",
  "greenwashing_", "dividend_", "capex_")` (`:372-375`).

`_get_primary_choice` (`base_track.py:392-414`): returns the first
`decision["choice_selected"]`; **default when none supplied is `"option_b"`**
(`base_track.py:414`).

---

## 0b. The bridge constraints (`side_tracks/bridge_schemas.py`, 361 lines)

See §10 for the cross-track analysis. Constants:

- `_ALLOWED_FLAG_PREFIXES` (`bridge_schemas.py:31-43`), exactly:
  `("supply_", "sc_", "ethics_", "es_", "stakeholder_", "sm_", "reporting_",
  "sr_", "sdg_", "brsr_", "side_track_")`
- `_MAX_TREASURY_DELTA_ABS: float = 20_000_000.0` (`bridge_schemas.py:47`) — "±$20M"

---

## 1. Supply Chain Deep Dive

**1. Names.** display_name `"Supply Chain Deep Dive"` (`side_tracks/supply_chain/track.py:36`);
track_id `"supply_chain"` (`:32`); icon `"🔗"` (`:49`).
Registered at `side_tracks/__init__.py:73` (`register_track(SupplyChainTrack())`).

**2. Stated purpose** — `description` property, `supply_chain/track.py:39-44`, quoted verbatim (196 chars):

> "A 7-round deep dive into supply chain management covering supplier mapping, ethical sourcing, Scope 3 decarbonisation, circular procurement, digital traceability, geopolitical risk, and resilience stress testing."

**3. Scoring dimensions.**
Declared list, `supply_chain/track.py:62-71` — 7 entries (id / label / unit):
`supply_visibility` "/100"; `supplier_risk_score` "/100 (lower=better)";
`scope3_reduction` "%"; `circular_procurement_index` "/100";
`digital_maturity` "/100"; `geopolitical_resilience` "/100";
`consumer_trust_index` "/100".

Weights exist only inside `calculate_score` (`supply_chain/track.py:165-206`).
Each raw input is clamped `min(100, max(0, ...))` — range **0–100** (`:178-183`).
- `supply_visibility` × **0.20** (`:199`)
- `supplier_risk_score` inverted as `100 - risk_raw` (`:180`), × **0.17** (`:200`)
- `scope3_reduction` × **0.17** (`:201`)
- `circular_procurement_index` × **0.13** (`:202`)
- `digital_maturity` × **0.10** (`:203`)
- `geopolitical_resilience` × **0.10** (`:204`)
- `consumer_trust_index` × **0.13** (`:205`)
Weights sum to 1.00. `consumer_trust_index` is *derived*, not stored:
`digital*0.3 + vis*0.3 + rep_component*0.4`, where
`rep_component = min(100, max(0, 50 + cumulative_reputation_delta * 1.67))`
(`:189-196`).
Grade cutoffs (`:208-219`): A+ ≥85, A ≥75, B ≥65, C ≥50, D ≥35, else F.
Archetype cutoffs (`:222-…`): ≥80 "Resilient Network Architect", ≥60 "Responsible Operator", then lower tiers.

**4. Prerequisite chain.**
- `cross_track_prerequisites` → `[]` (`supply_chain/track.py:74-75`), comment:
  "Supply Chain has no prerequisites; it enriches Ethics track".
- Actual runtime gate is NOT the prerequisites list (see §10). It is:
  `unlock_after = cohort["side_track_timing"][track_id]["unlock_after_round"]`
  and `if current_main_round <= unlock_after: raise HTTPException(403, ...)`
  (`router.py:6291`, `router.py:6295-6299`).
- Seeding is conditioned on main flags: `has_deep_audit = "deep_audit_completed" in main_flags`
  and `has_blockchain = "blockchain_traceability" in main_flags`
  (`supply_chain/track.py:102-103`); these add `+10` to starting `supply_visibility`
  and `+15` to starting `digital_maturity` (`:118, :122`).
- In-track stage conditions (pre_tick, `:294-370`) and post_tick branches
  (`:372-524`) key off `accumulated_flags`, e.g. R6 doubles the geopolitical
  resilience impact only if BOTH `supplier_capacity_building` and
  `circular_procurement_leader` are accumulated (`:470-472`).

**5. Round window.**
`available_window` → `(3, 8)` (`supply_chain/track.py:58-59`), comment
"Can be started after main R3, must complete before R8".
Only element `[0]` is ever read: `raw_unlock = t.available_window[0] - 1`
(`admin_router.py:12517`) → `2`, then `max(SIDE_TRACK_MIN_UNLOCK_AFTER=2, 2)` = **2**
(`admin_router.py:12508, 12519`). The upper bound `8` is read nowhere.

**6. WRITE-BACK EFFECTS.** `write_back_to_main` — `supply_chain/track.py:132-161`.
Returns `DataBridgeOutput(flags_to_set=flags)` (`:161`). **No `kpi_deltas`, no `kpi_overrides`.**
| Key written | Value / magnitude | Line |
|---|---|---|
| `supply_chain_track_completed` | `True` | `supply_chain/track.py:143` |
| `supply_chain_final_score` | `score["total_score"]` (0–100 float) | `:144` |
| `supply_chain_grade` | grade letter | `:145` |
| `supply_chain_archetype` | archetype title string | `:146` |
| `supply_chain_resilient` | `True` if `supply_visibility >= 80` | `:149` |
| `supply_chain_adequate` | `True` if `supply_visibility >= 50` | `:150` |
| `supply_chain_fragile` | `True` otherwise | `:151` |
| `sc_track_mr_bonus` | `0.10` if total ≥ 80 | `:156` |
| `sc_track_mr_bonus` | `0.05` if total ≥ 60 | `:157` |
| `sc_track_mr_penalty` | `-0.05` if total < 40 | `:158` |
| `sc_cobalt_findings` | bool: `"sc_cobalt_clean" in accumulated_flags` | `:159` |
| `sc_digital_maturity` | `track_state["digital_maturity"]` (0–100) | `:160` |

In-code ruling at `supply_chain/track.py:152-155`:
> "DEEP-9 ruling (2026-09-01): these M_R flags are written but READ BY NOTHING, by design — the owner chose honest display over wiring them (pinned M_R ceilings 1.93/2.02 stay untouched)."

Consumer sweep (backend `*.py` excluding `side_tracks/` and `tests/`, plus `frontend/app`):
**zero mechanical consumers for every one of the 12 keys.** The only occurrences are
`frontend/app/components/GameOverSummary.js:574` (a display reverse-map of
scoreKey/gradeKey/archetypeKey/completedKey/mrBonusKey/mrPenaltyKey) and
`frontend/app/components/consequenceCatalog.js:1443` (`sc_digital_maturity` catalog entry).
`sc_cobalt_findings` is read only by another side track:
`side_tracks/ethics_sustainability/track.py:83-85`.
→ **WRITE-BACK INERT** with respect to the main game.

Track-internal effects (do NOT reach the main game — see §10 "ephemeral global_state"):
R7 disruption damage `base_damage = max_disruption_damage(20_000_000) * severity/100`,
`actual_damage = base_damage * (1 - resilience)` with resilience factors
option_a 0.80 / option_b 0.50 / option_c 0.10 (`supply_chain/track.py:491-516`);
R2 discount default `1_000_000` (`:424`); R5 greenwash penalty default `2_000_000` (`:433`).

**7. Number of decisions/stages.** `num_rounds` → **7** (`supply_chain/track.py:54-55`).
`SUPPLY_CHAIN_ROUND_CONFIGS` has exactly 7 round keys 1–7
(`supply_chain/configs.py:26` dict opens; keys at lines 33, 136, 249, 354, 455, 570, 682).
21 `option_a|b|c` blocks = 3 options per round. One primary choice per round.

---

## 2. Ethics & Sustainability Deep Dive

**1. Names.** display_name `"Ethics & Sustainability Deep Dive"`
(`side_tracks/ethics_sustainability/track.py:32`); track_id `"ethics_sustainability"` (`:28`);
icon `"⚖️"` (`:45`). Registered `side_tracks/__init__.py:74`.

**2. Stated purpose** — `description`, `ethics_sustainability/track.py:35-40`, quoted (183 chars):

> "A 5-round exploration of corporate ethics covering AI governance, human rights due diligence, greenwashing risk, biodiversity, and just transition — with real regulatory frameworks (EU AI Act, CSDDD, TNFD, SBTN)."

Module docstring (`:1-13`) adds: "5-round deep dive: AI governance, modern slavery, greenwashing, biodiversity, and just transition."

**3. Scoring dimensions.** Declared `:56-64` — 5 entries, all unit "/100":
`ethical_governance`, `human_rights_dd`, `green_claims_integrity`,
`biodiversity_stewardship`, `just_transition`.
Weights in `calculate_score` (`:138-170`); each input clamped 0–100 (`:139-143`):
- `ethical_governance` × **0.25**, `human_rights_dd` × **0.25**,
  `green_claims_integrity` × **0.20**, `biodiversity_stewardship` × **0.15**,
  `just_transition` × **0.15** — single expression at `ethics_sustainability/track.py:145`. Sum 1.00.
Grades `:147-152`: A+ ≥85, A ≥75, B ≥65, C ≥50, D ≥35, else F.
Archetypes `:154-161`: ≥80 "Ethical Vanguard", ≥60 "Responsible Steward",
≥40 "Compliance Minimalist", else "Ethics Liability".

**4. Prerequisite chain.**
- `cross_track_prerequisites` → `["supply_chain"]` (`ethics_sustainability/track.py:66-67`),
  comment "SC track enriches modern slavery context". **This list gates nothing** (§10).
- The only real cross-track effect is at seed: `has_sc_cobalt = bool(sc_state.get("sc_cobalt_findings") or flags.get("sc_cobalt_findings"))`
  (`:83-85`), which adds `+20` to starting `human_rights_dd` (`:95`).
  `flags.get("deep_audit_completed")` adds `+10` to starting `ethical_governance` (`:94`).
- Runtime gate: same `unlock_after_round` check, `router.py:6291, 6295-6299`.

**5. Round window.** `available_window` → `(2, 7)` (`ethics_sustainability/track.py:52-53`).
Derived `unlock_after_round` = `max(2, 2-1)` = **2** (`admin_router.py:12517, 12519`).
Upper bound `7` read nowhere.

**6. WRITE-BACK EFFECTS.** `write_back_to_main` — `ethics_sustainability/track.py:108-134`.
Returns `DataBridgeOutput(flags_to_set=flags)` (`:134`). **No kpi_deltas, no kpi_overrides.**
| Key written | Value / magnitude | Line |
|---|---|---|
| `ethics_track_completed` | `True` | `ethics_sustainability/track.py:115` |
| `ethics_final_score` | `score["total_score"]` | `:116` |
| `ethics_grade` | grade letter | `:117` |
| `ethics_archetype` | archetype title | `:118` |
| `es_track_mr_bonus` | `0.10` if total ≥ 80 | `:125` |
| `es_track_mr_bonus` | `0.05` if total ≥ 60 | `:127` |
| `es_track_mr_penalty` | `-0.05` if total < 40 | `:129` |
| `es_governance_excellence` | `True` if `ethical_governance >= 70` | `:131` |
| `es_just_transition_credible` | `True` if `just_transition >= 60` | `:133` |

Same DEEP-9 ruling comment at `:119-122`.

Consumer sweep: 8 of the 9 keys have **no consumer anywhere** (backend non-test, frontend).
The single exception is `ethics_track_completed`, read at
`brsr_controller.py:25` — `BRSR_PREREQUISITE_FLAGS = ["ethics_track_completed", "reporting_track_completed"]`.
That gate is evaluated at `brsr_controller.py:98-102` as
`eligible = god_mode_override or len(met) >= BRSR_PREREQ_MINIMUM`, and
`BRSR_PREREQ_MINIMUM = 0` (`brsr_controller.py:28`), so `len(met) >= 0` is
**always True regardless of the flag**. The read is therefore non-discriminating.
`frontend/app/components/GameOverSummary.js:575` is a display reverse-map only.
→ **WRITE-BACK INERT** (one read exists but cannot change any outcome).

**7. Number of decisions/stages.** `num_rounds` → **5** (`ethics_sustainability/track.py:48-49`).
`ETHICS_ROUND_CONFIGS` has 5 round keys 1–5 (`ethics_sustainability/configs.py:12` dict;
keys at lines 13, 67, 126, 182, 241). 15 option blocks = 3 per round.

---

## 3. Stakeholder Management Deep Dive

**1. Names.** display_name `"Stakeholder Management Deep Dive"`
(`side_tracks/stakeholder_management/track.py:24`); track_id `"stakeholder_management"` (`:22`);
icon `"🤝"` (`:29`). Registered `side_tracks/__init__.py:75`.

**2. Stated purpose** — `description`, `stakeholder_management/track.py:26-27`, quoted (139 chars):

> "A 4-round deep dive into stakeholder engagement: salience mapping, ESG disclosure, community relations, and crisis communication."

**3. Scoring dimensions.** Declared `:36-43` — 4 entries, all unit "/100":
`stakeholder_mapping`, `investor_confidence`, `community_trust`, `crisis_resilience`.
`calculate_score` (`:103-127`): each clamped 0–100 (`:104-107`);
all four weighted **0.25** each — `total = round(sm*0.25 + ic*0.25 + ct*0.25 + cr*0.25, 1)`
(`stakeholder_management/track.py:109`). Sum 1.00.
Grades `:111-116`: A+ ≥85, A ≥75, B ≥65, C ≥50, D ≥35, else F.
Archetypes `:118-125`: ≥80 "Stakeholder Champion", ≥60 "Engaged Operator",
≥40 "Transactional Manager", else "Isolated Enterprise".

**4. Prerequisite chain.**
- `cross_track_prerequisites` → `[]` (`stakeholder_management/track.py:45`).
- Seed conditions: `flags.get("stakeholder_map_completed")` adds `+10` to starting
  `stakeholder_mapping` (`:68`); `community_trust` seeded as `round(avg_social_license * 0.4, 1)`
  (`:70`); `main_stakeholder_accuracy` read from `flags.get("stakeholder_map_accuracy", 50)` (`:74`).
- In-track stage condition: R4 crisis severity reduced by 12 (floor 10) if
  `sm_engagement_policy` is in `accumulated_flags` (`:133-135`).
- Runtime gate: `unlock_after_round`, `router.py:6291, 6295-6299`.

**5. Round window.** `available_window` → `(1, 6)` (`stakeholder_management/track.py:33`).
Derived `unlock_after_round` = `max(2, 1-1)` = **2** (floor overrides the declared 1).
Upper bound `6` read nowhere.

**6. WRITE-BACK EFFECTS.** `write_back_to_main` — `stakeholder_management/track.py:78-101`.
Returns `DataBridgeOutput(flags_to_set=flags)` (`:101`). **No kpi_deltas, no kpi_overrides.**
| Key written | Value / magnitude | Line |
|---|---|---|
| `stakeholder_track_completed` | `True` | `stakeholder_management/track.py:85` |
| `stakeholder_final_score` | `score["total_score"]` | `:86` |
| `stakeholder_grade` | grade letter | `:87` |
| `stakeholder_archetype` | archetype title | `:88` |
| `sm_track_mr_bonus` | `0.08` if total ≥ 80 | `:94` |
| `sm_track_mr_bonus` | `0.04` if total ≥ 60 | `:95` |
| `sm_track_mr_penalty` | `-0.04` if total < 40 | `:96` |
| `sm_strong_social_license` | `True` if `community_trust >= 70` | `:98` |
| `sm_crisis_ready` | `True` if `crisis_resilience >= 60` | `:100` |

Same DEEP-9 ruling comment at `:89-92`.

Consumer sweep: **zero consumers for all 9 keys** (backend non-test, frontend).
`frontend/app/components/GameOverSummary.js:576` is a display reverse-map only.
→ **WRITE-BACK INERT.**

Important adjacent finding (a *near miss*, documented precisely):
`flag_taxonomy.py:93-95` states "side_tracks/stakeholder_management outcomes were
wired into NPC trust / agent tolerance on 2026-09-01 (EVAL rec 6)". The wiring
exists: `SM_TRACK_CREDITS` (`npc_stakeholders.py:762-785`) maps 12 `sm_*` option
flags to NPC trust and agent tolerance deltas — `sm_esg_gold_standard` +8 trust /
+6 tolerance; `sm_transparency_champion` +6/+5; `sm_community_partnership` +6/+6;
`sm_investor_focus` +5/+5; `sm_issb_aligned` +5/+4; `sm_voluntary_commitments` +4/+3;
`sm_structured_response` +3/+3; `sm_gap_closure` +3/+3; `sm_rating_challenge` −3/−3;
`sm_defensive_crisis` −4/−4; `sm_media_hostile` −6/−5; `sm_legal_escalation` −5/−4.
`apply_sm_track_credits` is called from the MAIN post_tick at `round_logic.py:1230-1237`
and reads `global_state["active_event_flags"]` (`round_logic.py:1231`).
However those 12 `sm_*` flags are declared ONLY in
`side_tracks/stakeholder_management/configs.py` (lines 26, 37, 47, 71, 81, 91, 115,
125, 135, 169, 179, 189) and are accumulated only into `track_data["accumulated_flags"]`
(`router.py:6407-6410`) and into the track's own ephemeral flag dict (`router.py:6331`).
The stakeholder `write_back_to_main` does not export any of them. So the consumer
is real but **unreachable from the side-track path**: the main `active_event_flags`
never receives an `sm_*` option flag.

**7. Number of decisions/stages.** `num_rounds` → **4** (`stakeholder_management/track.py:31`).
`STAKEHOLDER_ROUND_CONFIGS` has 4 round keys 1–4 (`stakeholder_management/configs.py:5`;
keys at lines 6, 51, 95, 139). 12 option blocks = 3 per round.

---

## 4. Sustainability Reporting Deep Dive

**1. Names.** display_name `"Sustainability Reporting Deep Dive"`
(`side_tracks/sustainability_reporting/track.py:25`); track_id `"sustainability_reporting"` (`:23`);
icon `"📊"` (`:30`). Registered `side_tracks/__init__.py:76`.

**2. Stated purpose** — `description`, `sustainability_reporting/track.py:27-28`, quoted (159 chars):

> "A 5-round deep dive into ESG/sustainability reporting covering CSRD readiness, climate disclosure, social metrics, assurance, and integrated value creation."

**3. Scoring dimensions.** Declared `:37-45` — 5 entries, all unit "/100":
`regulatory_readiness`, `climate_disclosure`, `social_governance`,
`assurance_credibility`, `integrated_value`.
`calculate_score` (`:109-134`): each clamped 0–100 (`:110-114`); weights at
`sustainability_reporting/track.py:116`:
- `regulatory_readiness` × **0.20**, `climate_disclosure` × **0.25**,
  `social_governance` × **0.20**, `assurance_credibility` × **0.20**,
  `integrated_value` × **0.15**. Sum 1.00.
Grades `:118-123`: A+ ≥85, A ≥75, B ≥65, C ≥50, D ≥35, else F.
Archetypes `:125-132`: ≥80 "Disclosure Pioneer", ≥60 "Compliant Reporter",
≥40 "Selective Discloser", else "Opaque Enterprise".

**4. Prerequisite chain.**
- `cross_track_prerequisites` → `["ethics_sustainability"]`
  (`sustainability_reporting/track.py:47-48`). **Gates nothing** (§10).
- Seed conditions: `flags.get("csrd_assessment_completed")` adds `+15` to starting
  `regulatory_readiness` (`:71`); `ethics_done = "ethics_sustainability" in completed_tracks`
  adds `+10` to starting `social_governance` (`:73`); `ethics_gov` is carried in as
  `ethics_governance_score` (`:62, :78`).
- In-track stage condition: R5 branch keyed on `accumulated_flags` (`:136-147`).
- Runtime gate: `unlock_after_round`, `router.py:6291, 6295-6299`.

**5. Round window.** `available_window` → `(2, 8)` (`sustainability_reporting/track.py:34`).
Derived `unlock_after_round` = `max(2, 2-1)` = **2**. Upper bound `8` read nowhere.

**6. WRITE-BACK EFFECTS.** `write_back_to_main` — `sustainability_reporting/track.py:84-107`.
Returns `DataBridgeOutput(flags_to_set=flags)` (`:107`). **No kpi_deltas, no kpi_overrides.**
| Key written | Value / magnitude | Line |
|---|---|---|
| `reporting_track_completed` | `True` | `sustainability_reporting/track.py:91` |
| `reporting_final_score` | `score["total_score"]` | `:92` |
| `reporting_grade` | grade letter | `:93` |
| `reporting_archetype` | archetype title | `:94` |
| `sr_track_mr_bonus` | `0.10` if total ≥ 80 | `:100` |
| `sr_track_mr_bonus` | `0.05` if total ≥ 60 | `:101` |
| `sr_track_mr_penalty` | `-0.05` if total < 40 | `:102` |
| `sr_high_assurance` | `True` if `assurance_credibility >= 70` | `:104` |
| `sr_value_creator` | `True` if `integrated_value >= 60` | `:106` |

Same DEEP-9 ruling comment at `:95-98`.

Consumer sweep: 8 of 9 keys have **no consumer**. The exception is
`reporting_track_completed`, read at `brsr_controller.py:25` in
`BRSR_PREREQUISITE_FLAGS` — and, as in §2, that gate is
`len(met) >= BRSR_PREREQ_MINIMUM` with `BRSR_PREREQ_MINIMUM = 0`
(`brsr_controller.py:28, 98-102`), i.e. always eligible.
`frontend/app/components/GameOverSummary.js:577` is a display reverse-map only.
→ **WRITE-BACK INERT** (one non-discriminating read).

**7. Number of decisions/stages.** `num_rounds` → **5** (`sustainability_reporting/track.py:32`).
`REPORTING_ROUND_CONFIGS` has 5 round keys 1–5 (`sustainability_reporting/configs.py:5`;
keys at lines 6, 49, 92, 137, 181). 15 option blocks = 3 per round.

---

## 5. Corporate SDG Deep Track

**1. Names.** display_name `"Corporate SDG Deep Track"`
(`side_tracks/corporate_sdg/track.py:77`); track_id `"corporate_sdg"` (`:73`);
icon `"🌐"` (`:91`). Registered `side_tracks/__init__.py:77`.

**2. Stated purpose** — `description`, `corporate_sdg/track.py:80-88`, quoted (275 chars):

> "Five-round SDG alignment track covering Principal Adverse Impact reporting, Living Wage commitments, Circular Procurement, Biodiversity Net-Gain, and Integrated Reporting. Decisions feed into the M_SDG terminal valuation multiplier and propagate real consequences into BU operational metrics."

Module docstring (`corporate_sdg/track.py:1-17`) states the formula:
"SDG Impact Score feeds into the M_SDG terminal valuation multiplier:
M_SDG = 1.0 + (SDG_Impact_Score / 100) × 0.25".

**3. Scoring dimensions.** Declared `:103-111` — 5 entries, **mixed units** (the only
track that is not all "/100"):
`sdg_impact_score` unit "/105"; `sdg_integrity` unit "✓/✗";
`circular_leader` unit "✓/✗"; `nature_positive` unit "✓/✗";
`greenwash_risk_level` unit "/100".
There are **no weights**. `calculate_score` (`:195-232`) is not a weighted average:
- `score = track_state["sdg_impact_score"]` (raw points)
- `normalized = round(max(0, min(100, (score / 105) * 100)), 1)` (`:203`) → `total_score`
- `dimensions` (`:220-226`): `sdg_impact_score` = raw score; `sdg_integrity`,
  `circular_leader`, `nature_positive` = booleans from `flags_earned`;
  `greenwash_risk_level` = `80 if flags_earned["greenwash_risk"] else 0` (`:225`).
- `m_sdg_projection = round(1.0 + (score / 100.0) * 0.25, 4)` (`:231`).
Raw point range: per-round `sdg_points` maxima 20, 25, 20, 20, 20 → **+105**;
minima 2, −5, −3, −2, −3 → **−11** (`corporate_sdg/configs.py:43, 58, 73, 108, 124,
139, 175, 190, 205, 241, 256, 271, 307, 322, 337`). Matches the docstring at
`terminal_valuation.py:365` ("Range: -11 (all Option C) to 105 (all Option A).
M_SDG range: 0.97 to 1.26").
Grades (`:206-215`) are on the **normalized 0–100** scale and use a **different
ladder from every other track**: A+ ≥90, A ≥75, B ≥60, C ≥40, else D. **There is no F grade.**
Archetypes: "SDG Champion", "SDG Leader", "SDG Performer", "SDG Starter", "SDG Laggard".

**4. Prerequisite chain.**
- `cross_track_prerequisites` → `[]` (`corporate_sdg/track.py:113-114`), comment "No prerequisites".
- Seed condition: `pai_blindspot_active = bool(flags.get("pai_blindspot", False))`
  (`:150`). This is the only main-state read that changes track behaviour.
- In-track stage condition: `pre_tick` R2 only — if `pai_blindspot_active`, sets
  `pre_events["pai_blindspot_triggered"]` and `pre_events["strike_severity_doubled"]`
  (`:252-255`); `post_tick` then re-applies the option's negative reputation impact
  a second time (`:289-298`).
- Runtime gate: `unlock_after_round`, `router.py:6291, 6295-6299`.

**5. Round window.** `available_window` → `(1, 8)` (`corporate_sdg/track.py:98-100`),
comment "Independently triggerable from R1 through R8".
Derived `unlock_after_round` = `max(2, 1-1)` = **2** (floor overrides the declared 1).
Upper bound `8` read nowhere.

**6. WRITE-BACK EFFECTS.** `write_back_to_main` — `corporate_sdg/track.py:159-193`.
Returns `DataBridgeOutput.from_legacy_dict(flags, filter_unregistered=True)` (`:193`)
— the only track using the deprecated shim (`bridge_schemas.py:317-361`), which emits
a `DeprecationWarning` (`bridge_schemas.py:346-352`) and silently drops any flag whose
key does not match a registered prefix (`bridge_schemas.py:353-357`).
**No kpi_deltas, no kpi_overrides.**
| Key written | Value / magnitude | Line |
|---|---|---|
| `sdg_impact_score` | `track_state["sdg_impact_score"]` — raw points, range −11…105 | `corporate_sdg/track.py:176` |
| `sdg_track_completed` | `True` | `:177` |
| `sdg_score_history` | list of per-round `{sdg_track_round, score, m_sdg, choice, points}` | `:178` |
| each key of `flags_earned` | copied verbatim, then filtered to registered prefixes | `:184-185` |
| `sdg_mr_bonus` | `track_state["mr_bonus_accumulated"]` if > 0 | `:192` |

**`sdg_impact_score` IS CONSUMED — this is the one genuinely live KPI write-back.**
- `round_logic.py:3164`: `_sdg_score = float((gs.get("active_event_flags") or {}).get("sdg_impact_score", 0.0) or 0.0)`
  → `round_logic.py:3165-3168` `calculate_sdg_multiplier(_sdg_score)` → `m_sdg`
  → terminal value `TV = max(EBITDA_FLOOR, terminal_ebitda) × multiple × M_R × M_SDG`.
- `round_logic.py:507`: the same read in the alternate finale path
  (`_m_sdg = _sdg_mult(float((gs.get("active_event_flags") or {}).get("sdg_impact_score", 0.0) or 0.0))["m_sdg"]`),
  applied at `round_logic.py:513` `terminal_value = round(_ebitda_for_tv * exit_multiple * mr * _m_sdg, 2)`.
- Formula: `terminal_valuation.py:359-373`,
  `m_sdg = round(1.0 + (sdg_impact_score / 100.0) * 0.25, 4)`.
  At the declared range this is **M_SDG ∈ [0.9725, 1.2625]** (docstring rounds to 0.97–1.26).
- `sdg_track_completed`: read at `consequence_dna_api.py:355` and `router.py:3942`
  (both display payloads).
- `sdg_mr_bonus`: **no consumer** — explicitly ruled unread at `flag_taxonomy.py:15-19`.
- `sdg_score_history`: **no consumer** outside the track.
→ **WRITE-BACK LIVE** (via `sdg_impact_score` → M_SDG only).

Non-effects to record precisely: `post_tick` (`corporate_sdg/track.py:258-401`) and its
helpers `_apply_custom_metrics_to_bus` (`:403-453`) and `_apply_sdg_drag_boost` (`:456-521`)
write a long list of values into the `global_state` argument —
`active_event_flags["greenwash_detected"] = True` (`:327`),
`active_event_flags["base_strike_risk"] = max(current, 0.50)` (`:339-342`),
`ncd_interest_rate` reduced by 0.01/round, floor 0.01 (`:350-352`),
`synergy_multiplier` `min(1.35, current + synergy_bonus*0.05)` (`:449-451`),
`regulatory_ratchet_active = True` when cumulative score < 40 and round ≥ 2 (`:483-484`),
`group_reputation + 2` per round when score > 70 (`:492-495`),
`synergy_multiplier` floored at `1.10` when `circular_leader` and round ≥ 3 (`:504-509`),
`governance_risk_score − 3` when `sdg_integrity_unlocked` and current > 40 (`:512-517`).
**None of these reach the main game** — see §10, "the ephemeral global_state".

**7. Number of decisions/stages.** `num_rounds` → **5** (`corporate_sdg/track.py:94-95`).
`SDG_ROUND_CONFIGS` has 5 round keys 1–5 (`corporate_sdg/configs.py:19`;
keys at lines 21, 86, 153, 218, 284). 15 option blocks = 3 per round.

---

## 6. BRSR: NGRBC Deep Dive

**1. Names.** display_name `"BRSR: NGRBC Deep Dive"`
(`side_tracks/brsr_ngrbc/track.py:18`); track_id `"brsr_ngrbc"` (`:16`);
icon `"🇮🇳"` (`:23`). Registered `side_tracks/__init__.py:78`.

**2. Stated purpose** — `description`, `brsr_ngrbc/track.py:20-21`, quoted (159 chars):

> "A 10-round deep dive into the SEBI BRSR framework, covering all nine NGRBC principles, Essential vs Leadership indicators, and BRSR Core assurance."

**3. Scoring dimensions.** Declared `:30-37` — 5 entries, all unit "/100":
`governance_ethics` "Governance & Ethics (P1/P7)"; `human_capital` "Human Capital (P3/P5)";
`environmental` "Environmental Stewardship (P6/P2)"; `value_chain` "Value Chain & Stakeholder (P4/P8/P9)";
`reporting_quality` "Integrated Disclosure".
`calculate_score` (`:109-134`): each clamped 0–100 (`:110-114`); weights at `brsr_ngrbc/track.py:116`:
- `governance_ethics` × **0.20**, `human_capital` × **0.20**, `environmental` × **0.25**,
  `value_chain` × **0.20**, `reporting_quality` × **0.15**. Sum 1.00.
Grades `:118-123`: A+ ≥85, A ≥75, B ≥65, C ≥50, D ≥35, else F.
Archetypes `:125-132`: ≥80 "BRSR Pioneer", ≥60 "Responsible Steward",
≥40 "Compliance Pragmatist", else "Regulatory Laggard".
Dimension values are set by `post_tick` from `_SCORE_MAP = {"option_a": 90, "option_b": 50,
"option_c": 0}` (`brsr_ngrbc/track.py:190`) via `_DIMENSION_MAP` (`:191-202`) which routes
10 rounds onto the 5 dimensions: R1→governance_ethics, R2→human_capital,
R3→environmental, R4→value_chain, R5→reporting_quality, R6→human_capital,
R7→governance_ethics, R8→value_chain, R9→value_chain, R10→reporting_quality.

**4. Prerequisite chain.** The most explicit of the six, and the only one with a
dedicated checker.
- `cross_track_prerequisites` → `["sustainability_reporting", "ethics_sustainability"]`
  (`brsr_ngrbc/track.py:40-41`). **Gates nothing** (§10).
- `BRSR_PREREQUISITE_FLAGS = ["ethics_track_completed", "reporting_track_completed"]`
  (`brsr_controller.py:25`).
- `check_brsr_prerequisites` (`brsr_controller.py:89-110`), exact condition at `:102`:
  `eligible = god_mode_override or len(met) >= BRSR_PREREQ_MINIMUM`
  with `BRSR_PREREQ_MINIMUM = 0` (`brsr_controller.py:28`, comment
  "How many prerequisites are required to unlock BRSR (0 = always open)").
  **The gate is therefore always `True`.**
- Seed conditions (`brsr_ngrbc/track.py:62-67`): `ethics_done` adds `+10` to starting
  `governance_ethics`; `reporting_data.get("regulatory_readiness", 0) > 60` adds `+15`
  to starting `reporting_quality`.
- In-track stage conditions, `pre_tick` (`brsr_ngrbc/track.py:136-165`), exact:
  - R5: `"governance_fragility" in accumulated` → crisis_severity `min(100, cs + 15)`;
    `"brsr_core_assured" in accumulated` → `max(10, cs - 10)`.
  - R9: `"brsr_greenwash_risk" in accumulated and "brsr_core_assured" not in accumulated`
    → `min(100, cs + 20)`; `"deep_hrdd_active" in accumulated` → `max(10, cs - 8)`.
  - R10: `"governance_fragility" in accumulated and "policy_leadership" not in accumulated`
    → `min(100, cs + 10)`; `"msme_champion" in accumulated` → `max(10, cs - 5)`.
- Idempotency gate in the controller path: `if round_number in track_state.get("round_choices", {}): return {"brsr_already_processed": True, ...}` (`brsr_controller.py:154-156`).

**5. Round window.** `available_window` → `(2, 8)` (`brsr_ngrbc/track.py:27`).
Derived `unlock_after_round` = `max(2, 2-1)` = **2**. Upper bound `8` read nowhere.
NOTE: 10 track rounds inside a declared 2→8 window; nothing enforces the window's end.
BRSR also has a second, entirely different runtime path: when the session's
`decision_paradigm == "brsr_ngrbc"` the track runs *as the main game*, one BRSR round
per main round, driven from `round_logic.py:626-652`, finalising at main round 10
(`round_logic.py:645-647`).

**6. WRITE-BACK EFFECTS.** `write_back_to_main` — `brsr_ngrbc/track.py:75-107`.
Returns `DataBridgeOutput(flags_to_set=flags)` (`:107`). **No kpi_deltas, no kpi_overrides.**
| Key written | Value / magnitude | Line |
|---|---|---|
| `brsr_track_completed` | `True` | `brsr_ngrbc/track.py:82` |
| `brsr_performance_score` | `score["total_score"]` (0–100) | `:83` |
| `brsr_grade` | grade letter | `:84` |
| `brsr_archetype` | archetype title | `:85` |
| `brsr_net_positive_dividend` | **`0.05`** if `total_score >= 80` | `:88` |
| `brsr_truth_premium_cost_doubled` | `True` if `"governance_fragility" in accumulated_flags` | `:91` |
| `brsr_pioneer` | `True` if in accumulated | `:95` |
| `brsr_core_assured` | `True` if in accumulated | `:95` |
| `brsr_living_wage` | `True` if in accumulated | `:95` |
| `sdg_12_leadership` | `True` if in accumulated | `:95` |
| `brsr_greenwash_risk` | `True` if in accumulated | `:95` |
| `brsr_deep_hrdd_active` | `True` if `"deep_hrdd_active"` in accumulated (renamed for prefix validity) | `:102-106` |
| `brsr_policy_leadership` | `True` if `"policy_leadership"` in accumulated | `:102-106` |
| `brsr_msme_champion_active` | `True` if `"msme_champion"` in accumulated | `:102-106` |
| `brsr_csrd_aligned` | `True` if `"csrd_aligned"` in accumulated | `:102-106` |

The rename block carries this comment (`brsr_ngrbc/track.py:97-101`):
> "VAL-06 (audit 2026-09-04, WP-27): the four option flags below carry no registered prefix, and exporting them raw made DataBridgeOutput raise on the R10 finalise — the first time the BRSR finale ever ran from the player commit path, it 500'd."

Consumer sweep — BRSR is the **most wired** of the six:
- `brsr_net_positive_dividend` = **0.05 → added directly to M_R**:
  `terminal_valuation.py:262-265` (`brsr_div = flags.get("brsr_net_positive_dividend", 0);
  if brsr_div: mr += brsr_div; breakdown["brsr_esg_alpha_dividend"] = brsr_div`).
  Also raises the published M_R ceiling: `terminal_valuation.py:70-77`
  `if flags and flags.get("brsr_net_positive_dividend"): return MR_PUBLISHED_CEILINGS["brsr"]`
  (docstring: "the BRSR dividend → 1.98; otherwise 1.93").
  Carried numerically (not coerced to True) by `flag_utils.py:67-76` (`mr_flags_from`).
  Also read at `round_logic.py:429` and `round_logic.py:3083-3084`,
  and `brsr_controller.py:583`.
- `brsr_performance_score` → `round_logic.py:449`, feeding `pathway_bonuses` from
  `round_logic.py:458` onward (`if _brsr_score >= 85: ...`). Also `admin_router.py:10180`.
- `brsr_pioneer` → `admin_router.py:10168`, `admin_shared.py:876` (value `30`).
- `brsr_core_assured`, `brsr_living_wage`, `sdg_12_leadership`, `brsr_greenwash_risk`
  → read in `brsr_controller.py` (`:211-213, 294, 342, 353`) and
  `consequence_dna_api.py` (`:118, 119, 121, 257, 452`).
- `brsr_policy_leadership` → `brsr_controller.py:443`;
  `brsr_msme_champion_active` → `brsr_controller.py:457`;
  `brsr_csrd_aligned` → `brsr_controller.py:476`.
- `brsr_truth_premium_cost_doubled` → **NO consumer anywhere** (backend non-test or frontend).
  It is also absent from `flag_taxonomy.py`.
- `brsr_deep_hrdd_active` → **NO consumer anywhere.**
→ **WRITE-BACK LIVE** (`brsr_net_positive_dividend` +0.05 M_R is the largest single
mechanical effect any side track has on the main game), with two individually inert keys.

Additional main-game effects on the `decision_paradigm == "brsr_ngrbc"` path only
(`brsr_controller._apply_brsr_consequences`, `brsr_controller.py:247-505`) — these mutate
the real main `global_state`/`bu_states`:
- R1 `brsr_pioneer`: every BU `governance_risk_score − 8`, floor 0 (`brsr_controller.py:280-283`)
- R1 `governance_fragility`: sets `brsr_governance_fragility_active` (`:286`)
- R2 `brsr_living_wage`: every BU `staff_burnout_index − 12` (floor 0) and
  `workforce_readiness + 8` (cap 100) (`:296-298`)
- R2 `brsr_statutory_minimums`: `base_strike_risk = round(min(0.6, current + 0.15), 3)` (`:302-303`)
- R3 `brsr_circular_symbiosis`: `ncd_interest_rate − 0.012` (floor 0.01)
  (`:312-315`, constant `BRSR_CIRCULAR_SYMBIOSIS_NCD_REDUCTION = 0.012` at `:37`);
  `synergy_multiplier = round(min(1.5, current + 0.30), 4)` (`:317-318`)
- R3 `brsr_regulatory_minimum`: `ncd_interest_rate + 0.01` (cap 0.12) (`:323-324`);
  treasury **− 5_000_000** (`:329-332`)
- R3 fragility drag: `governance_risk_score × 0.04` added, cap 100
  (`:336-339`, constant `BRSR_GOVERNANCE_DRAG_RATE = 0.04` at `:38`)
- R4 `brsr_core_assured`: `group_reputation + 8` cap 100
  (`:345-348`, constant `BRSR_CORE_ASSURED_BONUS_REPUTATION = 8` at `:33`);
  `audit_tolerance = max(current, 65)` (`:350-353`)
- R4 `brsr_greenwash_risk`: `greenwash_detected = True` (`:357`);
  `audit_tolerance = min(current, 20)` (`:365`); treasury **− 10_000_000** (`:367-370`)
- R5 `brsr_integrated_report`: `brsr_net_positive_dividend = 0.05` (`:376`);
  if score ≥ 70, `ncd_interest_rate − 0.015` floor 0.01 (`:392-394`)
- R5 `brsr_compliance_only`: `brsr_truth_premium_blocked = True` (`:397`)
Finalisation on this path: `finalise_brsr_track` (`brsr_controller.py:506-542`) calls
`_track.write_back_to_main(...)` and merges `wb.flags_to_set` straight into
`global_state["active_event_flags"]` (`:534-537`).

**7. Number of decisions/stages.** `num_rounds` → **10** (`brsr_ngrbc/track.py:25`).
`BRSR_ROUND_CONFIGS` has 10 round keys 1–10 (`brsr_ngrbc/configs.py:9` dict, closes at `:433`;
keys at lines 10, 55, 99, 140, 181, 221, 263, 305, 347, 390). 30 option blocks = 3 per round.
A second dict `BRSR_PILLAR_OPTIONS` (`brsr_ngrbc/configs.py:443-2695`) declares a
pillar-mode schema — header comment at `:437-439` says "10 rounds × 5 areas × 3 options each".
Its accessors `get_brsr_pillar_config` (`:2702`) and `aggregate_brsr_pillar_decisions` (`:2710`)
have **no caller** anywhere in the repo's Python outside their own module and
`brsr_ngrbc/add_tooltips.py` (a one-off text-rewriting script, 244 lines).

---

## 7. Summary table

| Track | track_id | `available_window` | derived `unlock_after_round` | Rounds/stages | Options/round | Write-back |
|---|---|---|---|---|---|---|
| Supply Chain Deep Dive | `supply_chain` | (3, 8) | 2 | 7 | 3 | INERT |
| Ethics & Sustainability Deep Dive | `ethics_sustainability` | (2, 7) | 2 | 5 | 3 | INERT |
| Stakeholder Management Deep Dive | `stakeholder_management` | (1, 6) | 2 | 4 | 3 | INERT |
| Sustainability Reporting Deep Dive | `sustainability_reporting` | (2, 8) | 2 | 5 | 3 | INERT |
| Corporate SDG Deep Track | `corporate_sdg` | (1, 8) | 2 | 5 | 3 | LIVE |
| BRSR: NGRBC Deep Dive | `brsr_ngrbc` | (2, 8) | 2 | 10 | 3 | LIVE |

Total stages across the six tracks: 7 + 5 + 4 + 5 + 5 + 10 = **36**.

---

## 8. Cross-track finding — write-backs that are absent or inert

**No track emits `kpi_deltas` or `kpi_overrides`.** Verified by grep across all six
`track.py` files: zero occurrences of `kpi_deltas`, `kpi_overrides`, `BridgeKPIDeltas(`
or `KPIOverrides(`. Every one of the six returns a flags-only `DataBridgeOutput`.

Consequence: the entire additive/absolute KPI machinery in
`engine.apply_side_track_results` (`engine.py:313-391`) — `_KPI_DELTA_MAP`
(`engine.py:283-290`), `_KPI_OVERRIDE_MAP` (`engine.py:292-299`), `_KPI_BOUNDS`
(`engine.py:302-310`), the delta loop (`:357-364`), the override loop (`:368-373`)
and the clamp pass (`:376-384`) — **never fires for any of the six tracks**.
The `_MAX_TREASURY_DELTA_ABS = 20_000_000.0` guard (`bridge_schemas.py:47, 174-183`)
is likewise never exercised. Only STEP 4, flag merging (`engine.py:387-391`), does anything.

**Fully inert write-backs (nothing in the main game consumes anything they write):**
- **Supply Chain** — all 12 keys unconsumed. Only reads are the
  `GameOverSummary.js:574` display reverse-map, `consequenceCatalog.js:1443`, and
  a cross-*side-track* seed read of `sc_cobalt_findings` at
  `side_tracks/ethics_sustainability/track.py:83-85`.
- **Stakeholder Management** — all 9 keys unconsumed. Only read is the
  `GameOverSummary.js:576` display reverse-map. The NPC/agent wiring described in
  `flag_taxonomy.py:93-95` operates on a *different* flag family (`sm_esg_gold_standard`
  etc.) that the write-back never exports and that never reaches main
  `active_event_flags` (see §3).

**Effectively inert (a read exists but cannot change any outcome):**
- **Ethics & Sustainability** — only `ethics_track_completed` is read
  (`brsr_controller.py:25`), inside a gate that is unconditionally true because
  `BRSR_PREREQ_MINIMUM = 0` (`brsr_controller.py:28`, condition at `:102`).
- **Sustainability Reporting** — identical situation for `reporting_track_completed`.

**Live write-backs:**
- **Corporate SDG** — `sdg_impact_score` → `calculate_sdg_multiplier`
  (`terminal_valuation.py:359-373`) → M_SDG in terminal value at
  `round_logic.py:3164-3166` and `round_logic.py:507, 513`.
  M_SDG = 1.0 + (score/100) × 0.25; declared score range −11…105 → M_SDG 0.97…1.26.
  Its other three write-back keys (`sdg_track_completed`, `sdg_score_history`,
  `sdg_mr_bonus`) are display-only or unread.
- **BRSR: NGRBC** — `brsr_net_positive_dividend` = 0.05 added to M_R
  (`terminal_valuation.py:262-265`) and raising the M_R ceiling from 1.93 to 1.98
  (`terminal_valuation.py:70-77`); `brsr_performance_score` feeds pathway bonuses
  (`round_logic.py:449, 458`); seven principle flags are read by `brsr_controller.py`
  and `consequence_dna_api.py`. Two of its keys are individually inert:
  `brsr_truth_premium_cost_doubled` (`brsr_ngrbc/track.py:91`) and
  `brsr_deep_hrdd_active` (`brsr_ngrbc/track.py:102-106`) have no reader anywhere.

**Ruling recorded in the codebase itself** — `flag_taxonomy.py:14-19`:
> "Also ruled 2026-09-01 (not in this dict because they are written by track code, not declared in flags_set): the five side-track M_R flags (sc/sm/sr/es)_track_mr_bonus/_mr_penalty and sdg_mr_bonus are deliberately unread — the owner chose honest display (no student-facing M_R promises) over wiring them, keeping the pinned M_R ceilings 1.93/2.02 untouched."

**The ephemeral `global_state`.** A second, structural reason in-track effects do not
reach the main game. In the side-track commit path the router builds a fresh
throwaway global dict per commit — `track_global = {...}` at `router.py:6323-6342`,
with hard-coded `synergy_multiplier: 1.0`, `cost_of_capital: 0.05`,
`tco2e_emissions: 0`, `tipping_point_active: False`, and an
`active_event_flags` containing only `side_track_{track_id}: True` plus the track's
own accumulated flags (`router.py:6329-6332`). `process_tick` returns
`new_global = tick_result["global_state"]` (`router.py:6382`), and that is what
`post_tick` receives as `global_state=` (`router.py:6394-6400`). From `new_global`
only two scalars are ever carried forward — `corporate_treasury` and
`group_reputation` into `track_data["state"]` (`router.py:6423-6425`) — plus the
round-history snapshot (`:6428-6435`) and `new_bus` into `track_data["bu_states"]`
(`:6437`). The main session's `global_state` is loaded and written **only** at
completion (`router.py:6452-6462`), exclusively through
`apply_side_track_results(main_state["global_state"], write_back)`.
Therefore every `global_state[...] = ...` inside a track's `post_tick` — including
all of Corporate SDG's advertised "Deep Integration (v2)" effects
(`corporate_sdg/track.py:327, 339-342, 350-352, 449-451, 483-484, 492-495, 504-509, 512-517`),
Supply Chain's treasury damage (`supply_chain/track.py:422, 431, 510`), and the
reputation penalties in Ethics (`:197, 203`), Stakeholder (`:148`) and
Reporting (`:156, 161`) — is discarded with respect to the main game.
The sole exception is BRSR when running as `decision_paradigm == "brsr_ngrbc"`,
where `brsr_controller.process_brsr_round` is handed the real main `global_state`
and `bu_states` (`round_logic.py:627-636`).

**Two additional mechanical facts about state hand-off (reported as read, not inferred):**
- `corporate_sdg/track.py:301-302` reads `track_state = previous_flags.get("track_state", {})`
  and its comment says "The router passes full track_data["state"] as previous_flags["track_state"]".
  The router passes `previous_flags={"accumulated_flags": track_data.get("accumulated_flags", [])}`
  (`router.py:6398`) — the key `"track_state"` is not present. See §11.
- `brsr_ngrbc/track.py:206` reads
  `current = previous_flags.get("_brsr_track_state", {}).get(dim, 0)` for its
  "preserve the maximum" logic (`:184-189`). Neither caller supplies that key:
  the router passes `{"accumulated_flags": [...]}` (`router.py:6398`), and
  `brsr_controller.py:166` passes `previous_flags=track_state` (the state dict itself,
  which does not contain a `_brsr_track_state` member at that point). See §11.

---

## 9. Cross-track finding — do the tracks share a scoring scale?

**Partly. Five of six share one scale; Corporate SDG does not.**

Shared by Supply Chain, Ethics, Stakeholder, Reporting and BRSR:
- `calculate_score` returns `{"total_score", "dimensions", "grade", "archetype"}`,
  the shape mandated by `base_track.py:192-212`.
- Every dimension is clamped `min(100, max(0, ...))` → **0–100**.
- `total_score` is a **weighted average of the dimensions, weights summing to 1.00**,
  so it lands on the same 0–100 scale.
- The **same six-step grade ladder**: A+ ≥85, A ≥75, B ≥65, C ≥50, D ≥35, else F
  (`supply_chain/track.py:208-219`; `ethics_sustainability/track.py:147-152`;
  `stakeholder_management/track.py:111-116`; `sustainability_reporting/track.py:118-123`;
  `brsr_ngrbc/track.py:118-123`).
- The same four-tier archetype ladder at 80/60/40.
- All declare `scoring_dimensions` units as `"/100"` (Supply Chain's
  `supplier_risk_score` is `"/100 (lower=better)"` and is inverted as `100 - risk_raw`
  before weighting; `scope3_reduction` is `"%"` but is clamped and weighted identically).

Corporate SDG diverges on every one of those points:
- Dimensions are **not commensurable**: one point score `"/105"`, three booleans `"✓/✗"`,
  one `"/100"` (`corporate_sdg/track.py:103-111`).
- **No weights.** `total_score` is a rescaling, not an average:
  `round(max(0, min(100, (score / 105) * 100)), 1)` (`:203`).
- The underlying raw scale is **−11 to +105**, not 0–100
  (`terminal_valuation.py:365`; per-round `sdg_points` in `corporate_sdg/configs.py`).
  Negative raw scores are clipped to 0 by the `max(0, ...)` in `:203`, so a team
  scoring −11 and a team scoring 0 are indistinguishable in `total_score` — though
  the *raw* value is what is written back and what drives M_SDG, where −11 does differ.
- A **five-step grade ladder with different cutoffs and no F**: A+ ≥90, A ≥75, B ≥60,
  C ≥40, else D (`:206-215`).
- It adds two keys the base contract does not define: `raw_sdg_points`,
  `max_possible_points` (`:219-220`) and `m_sdg_projection` (`:231`).

Aggregation across tracks: `router.py:6583` exposes a cross-track aggregate leaderboard.
Because five tracks produce a weighted 0–100 and SDG produces a clipped rescaling of a
−11…105 raw, the aggregate mixes two different constructions of `total_score`.

The `scoring_dimensions` contract itself carries **no weight field** —
`base_track.py:92-99` defines each entry as `{"id", "label", "unit"}` only. Weights
live exclusively inside each track's `calculate_score` body and are not exposed
through `get_track_catalog()` (`side_tracks/__init__.py:40-58`), which serialises
`scoring_dimensions` as-is.

---

## 10. Cross-track finding — what `bridge_schemas.py` constrains

`bridge_schemas.py` (361 lines) is the typed boundary. What it actually enforces:

**1. Flag namespacing (enforced, raises).**
`_ALLOWED_FLAG_PREFIXES` (`bridge_schemas.py:31-43`) is the master registry:
`supply_`, `sc_`, `ethics_`, `es_`, `stakeholder_`, `sm_`, `reporting_`, `sr_`,
`sdg_`, `brsr_`, `side_track_`.
`validate_flag_names` (`:270-288`) raises `ValueError` listing every offending key
if any `flags_to_set` key fails the prefix test. `validate_removal_names` (`:290-297`)
applies the same rule to `flags_to_remove` — comment: "prevents wildcard nuking".
This is a real constraint that has already forced a code change: the BRSR rename
block at `brsr_ngrbc/track.py:97-106` exists because four raw option flags without a
registered prefix "made DataBridgeOutput raise on the R10 finalise ... it 500'd".

**2. No set-and-remove of the same flag (enforced, raises).**
`no_overlap` model validator (`:300-313`).

**3. Deltas, not overwrites, for KPIs (enforced by shape).**
`BridgeKPIDeltas` (`:162-188`) exposes exactly six additive fields:
`treasury_delta`, `reputation_delta` (`ge=-100, le=100`), `carbon_intensity_delta`,
`ncd_delta`, `governance_risk_delta` (`ge=-100, le=100`),
`social_license_delta` (`ge=-100, le=100`). All default `0.0`.
`treasury_delta_bounded` (`:174-183`) raises if `abs(v) > 20_000_000.0`.
A track literally cannot express "set treasury to X" through this field.

**4. Absolute overrides exist but are opt-in and ordered second.**
`KPIOverrides` (`:194-218`): `corporate_treasury`, `group_reputation` (`ge=0, le=100`),
`avg_carbon_intensity` (`ge=0`), `total_ncd` (`ge=0`), `synergy_multiplier` (`ge=0`),
`group_social_license` (`ge=0, le=100`). All default `None`; only non-None fields
are written (`engine.py:368-373`). Documented order (`:206-210` and `engine.py:325-330`):
deltas first, overrides second, then clamping.

**5. The inbound payload is frozen.**
`BridgeKPIs` `model_config = {"frozen": True}` (`:93`, comment "Immutable — side tracks
must not mutate this"); `DataBridgeInput` frozen (`:157`); `KPIOverrides` frozen (`:217`).
`DataBridgeInput.to_seed_dict()` (`:137-155`) deep-copies `extra_state` before merging
— "V11 fix ... prevents the track state from mutating the original DataBridgeInput
object and causing cross-round contamination".

**6. Only three inbound keys are standardised.**
`to_seed_dict()` guarantees exactly `inherited_treasury`, `inherited_reputation`,
`inherited_kpis` (`:148-152`); everything track-specific goes through the untyped
`extra_state: dict[str, Any]` (`:113-122`), which is merged verbatim. So the *typed*
boundary is thin in the read direction: all six tracks put their scoring metrics in
`extra_state`, which Pydantic does not validate beyond "is a dict".

**7. A documented escape hatch.**
`DataBridgeOutput.from_legacy_dict(..., filter_unregistered=True)` (`:317-361`)
**silently drops** unregistered keys instead of raising (`:353-357`). It emits a
`DeprecationWarning` (`:346-352`) and its own docstring marks it "**DEPRECATED**".
Corporate SDG is the only track still using it (`corporate_sdg/track.py:193`).

**8. A typed decision schema that the router does not use.**
`SideTrackDecision` (`:53-76`) is described as the "Typed replacement for the raw
`list[dict]` in SideTrackCommitRequest" (`:55-58`, VUL-L3-004). But
`SideTrackCommitRequest` at `router.py:6221-6225` still declares
`decisions: list[dict]`, and the commit handler converts with
`[d if isinstance(d, dict) else d.model_dump() for d in body.decisions]`
(`router.py:6354`). `SideTrackDecision` is imported nowhere outside `bridge_schemas.py`
in non-test backend code. Its `capex_allocated: float = Field(default=0.0, ge=0.0)`
and `choice_selected` non-empty intent are therefore not enforced on the live path.

**What it does NOT constrain:** nothing in `bridge_schemas.py` refers to
`available_window`, `cross_track_prerequisites`, `num_rounds`, or round ordering.
Sequencing and unlocking are entirely the router's and the facilitator's concern.

**Gate reality check (the unlock chain end to end):**
`cross_track_prerequisites` is read in exactly two places — its own definitions and
`side_tracks/__init__.py:56`, where it is copied into the display catalog. **It gates nothing.**
`available_window` is read in exactly one functional place —
`admin_router.py:12517`, `raw_unlock = t.available_window[0] - 1`, immediately floored by
`SIDE_TRACK_MIN_UNLOCK_AFTER = 2` (`admin_router.py:12508, 12519`, comment "side tracks
may never unlock before Round 2 is complete"). **The upper bound of every window is
never read.** Because the floor is 2 and every track's `available_window[0] - 1` is
≤ 2, **all six tracks derive the same `unlock_after_round = 2`** — the six declared
windows collapse to one gate. The only runtime check is
`if current_main_round <= unlock_after: raise HTTPException(403, ...)`
(`router.py:6295-6299`), plus `is_unlocked = current_main_round > unlock_after`
(`router.py:6180`) and the 409 on an already-completed track (`router.py:6285-6286`).

---

## 11. NOT FOUND / UNCERTAIN

- **NOT FOUND: any per-dimension weight in a declared `scoring_dimensions` list.**
  The contract at `base_track.py:92-99` has no weight field. Weights exist only as
  literals inside each `calculate_score`.
- **NOT FOUND: any consumer of `brsr_truth_premium_cost_doubled`**
  (written `brsr_ngrbc/track.py:91`). Zero occurrences elsewhere in backend `*.py`
  (non-test) or `frontend/app`. It is also absent from `flag_taxonomy.py`.
- **NOT FOUND: any consumer of `brsr_deep_hrdd_active`** (written `brsr_ngrbc/track.py:102-106`).
- **NOT FOUND: any consumer of `sdg_score_history`** (written `corporate_sdg/track.py:178`).
- **NOT FOUND: any consumer of the five M_R side-track flags**
  `sc_track_mr_bonus`/`_mr_penalty`, `es_*`, `sm_*`, `sr_*`, `sdg_mr_bonus` —
  ruled deliberately unread at `flag_taxonomy.py:14-19`.
- **NOT FOUND: a caller for `BRSR_PILLAR_OPTIONS`' accessors**
  `get_brsr_pillar_config` (`brsr_ngrbc/configs.py:2702`) and
  `aggregate_brsr_pillar_decisions` (`:2710`), outside their own module and the
  one-off script `brsr_ngrbc/add_tooltips.py`. ~2250 lines of pillar config with
  no reader found.
- **NOT FOUND: any use of `SideTrackDecision`** (`bridge_schemas.py:53-76`) on the
  live commit path; `router.py:6221` still types `decisions: list[dict]`.
- **NOT FOUND: any track setting `kpi_deltas` or `kpi_overrides`.**
- **NOT FOUND: an explicit "stages within a track" concept.** Each track exposes
  `num_rounds` and one primary choice per round (`_get_primary_choice`,
  `base_track.py:392-414`). There is no sub-stage structure in any of the six
  except BRSR's unused pillar schema.
- **UNCERTAIN — Corporate SDG cumulative score.** `corporate_sdg/track.py:301`
  reads `previous_flags.get("track_state", {})`; `router.py:6398` supplies only
  `{"accumulated_flags": [...]}`. Read literally, `track_state` is `{}` on every
  tick, so `total_score = sum(track_state.get("round_points", {}).values())`
  (`:308`) equals the current round's points alone. The router's event-merge loop
  then adds the emitted `st_corporate_sdg_custom_sdg_impact_score` to the stored
  value numerically (`router.py:6412-6420`,
  `track_data["state"][metric_name] = round(current_val + val, 2)`), which would
  make the persisted total correct by accumulation. I did not execute the code and
  do not claim which behaviour occurs at runtime; both statements above are what
  the two files say. The same reading implies `round_points`, `round_choices`,
  `flags_earned` and `sdg_score_history` (non-numeric values, assigned verbatim at
  `router.py:6420`) would hold only the latest round.
- **UNCERTAIN — BRSR "preserve the maximum" dimension logic.**
  `brsr_ngrbc/track.py:206` reads `previous_flags.get("_brsr_track_state", {}).get(dim, 0)`.
  On the router path `previous_flags` is `{"accumulated_flags": [...]}` (`router.py:6398`);
  on the controller path it is `track_state` itself (`brsr_controller.py:166`). In
  neither case did I find a `_brsr_track_state` key inside the passed object at that
  moment, which would make `current` always `0` and `new_value = max(0, target) = target`.
  Downstream the two paths differ: the router accumulates additively
  (`router.py:6418-6419`), the controller assigns (`brsr_controller.py:180-182`).
  I did not run the code; reported as read.
- **UNCERTAIN — `_apply_default_option_impacts` custom-metric handling of the
  `supplier_risk_score` and `geopolitical_resilience` keys.** Supply Chain's
  `post_tick` writes them onto `global_state` (`supply_chain/track.py:412, 479`),
  whereas the base applicator routes unknown `impacts` keys into
  `st_{track_id}_custom_{key}` events (`base_track.py:376-387`). I read both code
  paths but did not trace which one wins for a given round config.
- **NOTE (not a gap): the base docstring says "4–7 rounds"** (`base_track.py:35`)
  while `brsr_ngrbc` declares `num_rounds = 10` (`brsr_ngrbc/track.py:25`).
  Nothing enforces the docstring.
