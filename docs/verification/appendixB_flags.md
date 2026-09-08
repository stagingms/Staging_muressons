# Appendix B — Flag dependency quick reference
Repo: muressons-sim @ git HEAD `0ad1246`. Backend root: `backend/`.
Every claim below is anchored to a file:line read at this HEAD. Where the code
does not say something, the entry says NOT FOUND rather than inferring it.

---

## B.0 How a flag physically exists (read this first — it explains most dead reads)

Option flags are persisted as a **LIST under a per-round key**, never as
top-level booleans:

- Legacy A/B/C paradigm: `round_logic._apply_option_flags`
  (`backend/round_logic.py:3770-3773`) writes
  `active_event_flags["r{N}_flags"] = [flag, ...]`.
- Pillar ("multi_toggles") paradigm: `backend/router.py:3077-3079` writes
  `active_event_flags["r{N}_pillar_flags"] = [flag, ...]`.
- `_apply_option_flags` **returns early without writing anything** when the tick
  is a pillar tick (`backend/round_logic.py:3761-3763`, stamping
  `proxy_option_flags_skipped_r{N}`) — FLAG-2.
- Commit-time merge: `backend/router.py:3322-3325`
  `merged = current_flags ∪ new_global_flags ∪ events`.

Therefore there are **two kinds of read** in this codebase and they do not
behave the same:

1. **Flattened read** — `flag_utils.collect_all_flags(...)`
   (`backend/flag_utils.py:21-56`), aliased in round_logic as
   `_collect_all_flags`. Expands any key containing "flag" whose value is a
   list. **This is the only read that can see an option flag.**
2. **Top-level key read** — `"x" in active_event_flags` or
   `active_event_flags.get("x")`. **Cannot see an option flag**, because the
   flag name is an element inside a list, not a key.

`collect_all_flags` also carries a hard-coded fallback list
(`backend/flag_utils.py:49-54`: `electronics_blindspot`, `deep_audit_completed`,
`electronics_blindspot_triggered`, `deep_audit_protected`) that adds those names
if they happen to be present as top-level keys.

Flags written as genuine top-level booleans (and therefore visible to BOTH read
styles) are the exception. Confirmed writers at this HEAD:
- `round_logic.py:2430` — `ai_monetised = True` (R6 option_a, in addition to `r6_flags`)
- `round_logic.py:3613-3616` — `materiality_aligned` / `materiality_partial` / `materiality_ignored` (exactly one True)
- `round_logic.py:2357` — `scope_3_transparency = True`
- `shadow_board_audit.py:252` — `planet_expendable` / `shareholder_alienated` / `governance_fragility` (R5)

Several documented consumers use style 2 against option flags and are therefore
**structurally unreachable**. They are listed individually below and again in
§B.13.

### Non-consumer locations (must not be counted as consumers)
- `backend/pillar_configs.py:1649-1697` — `FLAG_OVERRIDES`. Reverse map used by
  the pillar→legacy proxy-choice inference. Its own comment at
  `pillar_configs.py:1655` reads "Reverse map ONLY (proxy-choice inference) —
  never a write path." Consumed at `pillar_configs.py:1699`.
- `backend/flag_taxonomy.py` — the declared-but-unread registry (see §B.1).
- `backend/terminal_valuation.py:683-703` — `FLAG_DEPENDENCY_GRAPH`, a static
  documentation list. Its only readers are `get_flag_dependency_graph`
  (`terminal_valuation.py:705`), called from `admin_router.py:12606` (admin API)
  and `consequence_dna_api.py:249` (visualiser). **Display only.** Several of
  its claims are not implemented (flagged inline below).
- `backend/consequence_dna_api.py:88-106` (`FLAG_METRIC_SHIFTS`) and `:591-615`
  (`_get_flag_projection_mapping`) — Sankey node labels. Display only.
- `backend/admin_router.py:1705-1745`, `backend/admin_teleprompter.py` — facilitator display.
- `backend/journey_improvements.py:440-500` (`FLAG_DEPENDENCY_WARNINGS`) — student-facing
  warning text; imported only by `admin_teleprompter.py:1272-1274`.
- `backend/journey_improvements.py:240-290` — the R7 budget-split variant; its own
  instruction text (`journey_improvements.py:244-245`) says the allocation
  "is discussed in the debrief; it is not applied by the engine."
- `backend/meadows_leverage.py:225-250` (`SYSTEM_ARCHETYPES`) — narrative only;
  `detect_archetypes` (`meadows_leverage.py:317-344`) DOES flatten list values and
  fires, but writes only `extra["system_archetypes_detected"]` (debrief text).
- `backend/pedagogical_engine.py:118-121` (`CASCADE_FLAGS`), `:435-495`
  (`generate_r5_checkpoint`) — mid-game diagnostic text, no state mutation.
- `backend/bu_profiles.py:383-398` (`VERTICAL_BLINDSPOT_FLAGS`) — vertical name map.

### Frontend
A whole-word sweep of all 33 `round_configs.py` flags over `frontend/src`
returned **zero** occurrences. No flag in this appendix has a frontend consumer.

---

## B.1 Classification scheme in `flag_taxonomy.py`

`backend/flag_taxonomy.py` is described in its own docstring
(`flag_taxonomy.py:1-20`) as "the ruling record for every declared-but-unread
flag". The invariant, enforced by `tests/test_flag_taxonomy.py`, is: every flag
declared in a `flags_set` list must either be READ somewhere (backend non-test
code or `frontend/src`) or carry an entry here explaining why it is deliberately
unread. **Membership in `FLAG_TAXONOMY` is therefore an assertion that the flag
is dead.**

Three classes (`flag_taxonomy.py:15-18`):
- `choice-marker` — records which option a team took; effects applied elsewhere.
- `narrative` — flavour/bookkeeping the model deliberately does not consume.
- `history` — permanent record written at game end; nothing runs after it.

`FLAG_TAXONOMY` (`flag_taxonomy.py:22-201`) holds **156 entries**. Per-file
rationales live in `TAXONOMY_REASONS` (`flag_taxonomy.py:203-212`), keyed by
declaring file.

Entries by declaring file (all names as written in the dict):
- **ending_pathways.py — 9, all `history`**: bid_accepted, climate_adaptation,
  climate_deny, contest_ruling, corporate_hardball, emergency_decarb,
  selective_appeasement, stakeholder_compact, white_knight_defence.
- **healthcare_configs.py — 22, all `narrative`**: air_freight_emergency,
  cancelled_electives, circular_hubs, clinician_retraining, closed_loop_water,
  consolidation, digital_triage_active, divest_weakest, hardened_hospital_grid,
  heavy_icu_capex, human_triage_override, incinerator_lobbying,
  local_sterile_resilience, patient_evacuation, quiet_patch_oncology,
  regional_clinics_built, telehealth_litigation (note: "future-mechanics
  candidate"), telehealth_overhaul, union_busted (note: "future-mechanics
  candidate"), universal_care_charter, vendor_replacement, water_trucking.
- **journey_improvements.py — 3, `narrative`**: independent_investigation,
  whistleblower_accountability, whistleblower_suppressed.
- **pillar_configs.py — 54, all `choice-marker`**: ai_supply, community_fund_r2,
  cooperatives, cost_optimized, dc_optimized, diesel_backup, employee_wellbeing,
  endowment_created, esg_report, green_dc, hybrid_fleet, low_carbon_path,
  nature_offsets, nearshored, net_zero_energy, ngo_partner, offshored,
  reckless_automation, regen_agriculture, shareholder_only, supply_diversified,
  supply_water_audit, tech_scholarships, water_efficient_supply,
  watershed_restored, plus the FLAG-11 block (`flag_taxonomy.py:146-175`):
  adaptation_fund, automation_pivot, biodiversity_fund, closed_loop,
  community_water, digital_inclusion, digital_twin, dry_cooling,
  efficiency_upgrades, fossil_dependent, green_pivot, green_reskilling,
  green_tariff, heat_recovery, lean_process, local_ecosystem, manual_oversight,
  material_passport, microgrids, parametric_insurance, partial_retraining,
  regenerative_supply, resilient_network, reverse_logistics,
  stakeholder_covenant, targeted_fix, transition_bonds, voluntary_offsets,
  waste_reduction.
- **pillar_configs.py + round_configs.py — 3, `choice-marker`**:
  materiality_exceptions (`:87`), pr_containment (`:175`), spinoff (`:176`).
- **round_configs.py — 2, `choice-marker`**: ceo_only_signoff (`:89`),
  turnaround_restructuring (`:90`).
- **side_tracks/brsr_ngrbc/configs.py — 1, `narrative`**: brsr_indicator_leadership.
- **side_tracks/supply_chain/configs.py — 22, `narrative`**:
  circular_minimum_compliance, circular_procurement_partial,
  crisis_passive_response, crisis_response_full, crisis_response_targeted,
  digital_twin_supply, erp_integration_sc, ethical_sourcing_restructured,
  ethical_sourcing_transitional, geographic_diversified, inventory_buffer_only,
  manual_compliance_sc, partial_tier_mapping, remediation_fund_active, sbti_risk,
  sc_monitoring_only, sc_resilient, scope3_deep_cut, scope3_offset_only,
  supplier_switching, supply_disruption_risk, take_back_active.
- **side_tracks/sustainability_reporting/configs.py — 19, `narrative`**: sr_activist_opposition,
  sr_ar_integrated, sr_climate_adequate, sr_climate_gap, sr_climate_leader,
  sr_esg_controls, sr_full_esrs, sr_integrated_leader, sr_limited_assurance,
  sr_living_wage, sr_phased_compliance, sr_reasonable_assurance, sr_sbti_targets,
  sr_scope3_complete, sr_sfdr_compliant, sr_siloed_reporting, sr_social_gap,
  sr_social_leader, sr_value_demonstrated.
- **side_tracks/ethics_sustainability/configs.py — 21, `narrative`**:
  es_ai_ethics_board, es_ai_quiet_fix, es_biodiversity_deferred,
  es_cobalt_certified, es_community_invested, es_green_claims_verified,
  es_greenwash_defended, es_just_transition_leader, es_legal_firewall,
  es_lobby_active, es_nature_positive, es_partial_conservation,
  es_partial_correction, es_phased_transition, es_sbti_aligned,
  es_supplier_terminated, es_tnfd_disclosed, es_transparency_leader,
  es_union_strike_risk, es_whistleblower_risk, es_workers_abandoned.

Also ruled unread but deliberately NOT in the dict (docstring
`flag_taxonomy.py:15-19`, because track code rather than `flags_set` writes them):
the five side-track M_R flags `(sc|sm|sr|es)_track_mr_bonus` / `_mr_penalty` and
`sdg_mr_bonus`. The docstring states the owner chose honest display over wiring
them, keeping the pinned M_R ceilings 1.93 / 2.02 untouched.

`flag_taxonomy.py:98-100` records that the `side_tracks/stakeholder_management`
entries were RETIRED on 2026-09-01 because they gained readers (NPC trust /
agent tolerance), "per this registry's own contract (a read flag may not keep a
ruling)".

---

## B.2 Round 1 — Foundations (`round_configs.py:29-100`)
R4 base crisis severity = 40 (`round_configs.py:291`);
switch `electronics_blindspot_doubles_crisis: True` (`round_configs.py:290`).

### `electronics_blindspot` — R1 option_a "Surface-Level Scan" (`round_configs.py:50`)
Also declared in pillar mode at `pillar_configs.py:102` and `:109`, and in
`FLAG_OVERRIDES` R1 option_c (`pillar_configs.py:1652` — not a consumer).
Consumers (all flattened reads, so LIVE):
1. `round_logic.py:227-232` — `_pre_r4_contagion`: sets
   `result["crisis_severity"] = base * 2`, i.e. **40 → 80** at R4. Also stamps
   `electronics_blindspot_triggered` and `crisis_severity_doubled`.
   Effect lands: **Round 4**.
2. `router.py:4693-4700` — R2 materiality config endpoint: when set, every issue
   marked `electronics_sensitive` has its `hover_description` replaced by its
   `blindspot_description`; `global_state["r1_blindspot_active_in_r2"] = True`.
   Effect lands: **Round 2** (information degradation, no numeric delta).
3. `stakeholder_map.py:798` + gate at `:961-963` — `apply_salience_migrations`
   (called from `round_logic.py:707-708`); the R6 rule moving `syndicate_banks`
   from `keep_satisfied` → `manage_closely` fires only if this flag is held.
   The reader flattens list values (`stakeholder_map.py:922-936`).
   Effect lands: **Round 6**.
4. `stakeholder_sentiment.py:48-53` (`FLAG_SENTIMENT_RULES`) — **attitude −8** for
   stakeholders matching ngo / community / regulator. Reached because
   `router.py:2946-2955` attaches the chosen option's `flags_set` to
   `decisions_raw[0]["flags_set"]` and `engine.py:4785-4786` feeds those into
   `update_stakeholder_sentiment`. Effect lands: **round of choice (R1)**.
5. `meadows_leverage.py:229-233` — "Fixes That Fail" archetype narrative
   (debrief text only).
6. `pedagogical_engine.py:460-461` — adds the string "R1 Blindspot will double R4
   crisis severity" to the R5 checkpoint `locked_out` list (display).
Terminal-valuation condition: **No** — absent from `terminal_valuation.calculate_mr`.
Taxonomy class: none (it is read).

### `deep_audit_completed` — R1 option_b "Deep Forensic Audit" (`round_configs.py:68`)
Also `pillar_configs.py:95`, `healthcare_configs.py:41`, `FLAG_OVERRIDES` R1
option_b (`pillar_configs.py:1651`).
Consumers:
1. **LIVE** — `stakeholder_sentiment.py:42-47`: **attitude +7** for regulator /
   ngo / community / buyer / consumer. Effect lands: **round of choice (R1)**.
2. **STRUCTURALLY DEAD** — `engine.py:4369`:
   `deep_audit = "deep_audit_completed" in current_global.get("active_event_flags", {})`
   — a top-level key read (see §B.0). Intended effect: exempt the team from Fog of
   War in rounds 1-2 (`engine.py:4368-4383`, ±10% noise on NCD / social licence /
   governance risk). Never fires.
3. **STRUCTURALLY DEAD** — `systemic_risk_engine.py:68` inside `flag_boosts`,
   applied at `:79-83` by `if flag in flags or flag in flags.get("flags_set", [])`.
   `flags` is the raw `active_event_flags` dict (`engine.py:3703-3705`), and no
   code writes an `events["flags_set"]` key. Intended effect: **+20** to the
   Supply-Chain Transparency score. Never fires.
4. **STRUCTURALLY DEAD** — `side_tracks/supply_chain/track.py:102`
   (`"deep_audit_completed" in main_flags`, raw dict) → `_sc_deep_audit_done`.
5. **STRUCTURALLY DEAD** — `side_tracks/ethics_sustainability/track.py:95`
   (`flags.get("deep_audit_completed")`, raw dict from `:81`) — intended
   `ethical_governance` seed +10.
Note: `_pre_r4_contagion` does **NOT** read this flag. The "protection" is the
`else` branch at `round_logic.py:248-250` (absence of `electronics_blindspot`,
`deferred_audit`, `compliance_gap`, `outsource_opacity`), which stamps
`deep_audit_protected`. The `FLAG_DEPENDENCY_GRAPH` claim "Halves crisis severity
(40 vs 80)" (`terminal_valuation.py:685`) is display text, not a read of this flag.
Terminal-valuation condition: **No**. Taxonomy class: none.

### `deferred_audit` — R1 option_c "Phased Audit Rollout" (`round_configs.py:87`)
Consumers:
1. **LIVE** — `round_logic.py:234-237`: `crisis_severity = round(base * 1.5)`,
   i.e. **40 → 60** at R4; stamps `deferred_audit_penalty`,
   `crisis_severity_multiplied = 1.5`. Effect lands: **Round 4**.
2. `router.py:2935-2937` — UI crisis-source label "⚠️ +50% — Audit deferred in
   Round 1" (display).
No pillar declaration; not in `FLAG_OVERRIDES`. Terminal-valuation: **No**.
Taxonomy class: none.

---

## B.3 Round 2 — Double Materiality (`round_configs.py:102-199`)
Structural note: the R2 flags in `flags_set` are decoupled from the flags that
actually earn the M_R premium. `round_logic._post_r2_materiality`
(`round_logic.py:3600-3622`) combines the A/B/C choice with the matrix accuracy
(`accuracy_threshold_pct`, default 80) and writes exactly one of
`materiality_aligned` / `materiality_partial` / `materiality_ignored` as a
top-level boolean. `round_configs.py:144-146` states this explicitly.

### `full_materiality_alignment` — R2 option_a (`round_configs.py:149`)
**LIVE — and the in-file comment is stale.** `round_configs.py:147-148` says
"full_materiality_alignment is a choice marker with no consumer". That is
contradicted at this HEAD by:
- `engine.py:3787-3789` (FLAG-10.5): flattened read via
  `flag_utils.collect_all_flags`; multiplies the logarithmic NCD-forgiveness
  per BU by **×1.25** and stamps `ncd_forgiveness_materiality_bonus = 1.25`.
  Base formula `2.0 × ln(1 + CapEx_M$)` (`engine.py:3780`, `:3796`).
  Effect lands: **every round in which green capex is allocated, from R2 onward**
  (the block runs whenever `total_green_capex > 0`).
Not in `FLAG_OVERRIDES`. Terminal-valuation: **No**. Taxonomy class: none.

### `materiality_exceptions` — R2 option_b (`round_configs.py:174`)
Occurrences outside its declarations: `flag_taxonomy.py:87` only.
Also declared `pillar_configs.py:220`. **DEAD (case ii).**
Taxonomy class: `choice-marker`.

### `ceo_only_signoff` — R2 option_c (`round_configs.py:190`)
Occurrences: its own comment (`round_configs.py:189`), `flag_taxonomy.py:89`,
and the shared reason at `flag_taxonomy.py:209`. **DEAD (case i/ii).**
Taxonomy class: `choice-marker`.

### Cross-reference: `materiality_aligned` / `materiality_partial`
Not declared in any `flags_set`; written top-level by `round_logic.py:3613-3616`.
Consumers: `terminal_valuation.py:198-206` (**+0.10** M_R aligned / **+0.05**
partial, mutually exclusive) and `round_logic.py:2254-2264` (R3 Green Bond
treasury discount **$500,000**, halved for `materiality_partial` per `§5.2`).
Terminal-valuation condition: **Yes**.

---

## B.4 Round 3 — Scope 3 Emissions (`round_configs.py:200-275`)

### `supply_chain_disruption_risk` — R3 option_a (`round_configs.py:222`)
Occurrences: `pillar_configs.py:384` (declaration), `pillar_configs.py:1661`
(`FLAG_OVERRIDES`), `systemic_risk_engine.py:71` (**−10** Supply-Chain
Transparency). The systemic read is the broken top-level style described in
§B.0 (`systemic_risk_engine.py:79-83`, raw dict from `engine.py:3703-3705`).
**DEAD in practice (case ii + one unreachable consumer).**
Taxonomy class: none — note this flag is neither read nor registered.

### `early_decarboniser` — R3 option_a, second flag (`round_configs.py:222`)
Also `pillar_configs.py:384`, `healthcare_configs.py:167`.
Consumers (LIVE):
1. `round_logic.py:2507-2512` — flattened read; `gs["synergy_multiplier"] += 0.10`
   inside the R7 circularity handler; stamps `early_decarboniser_synergy_bonus`.
   Effect lands: **Round 7**.
2. `ending_pathways.py:566-569` — **cross-round pairing** (see §B.14).
3. `pedagogical_engine.py:483-484` — absence + avg CI > 35 produces a
   recommendation string (display).
Terminal-valuation: **No** direct term in `calculate_mr`; it reaches M_R only
through the synergy multiplier gate and through the Adaptation Premium.
Taxonomy class: none.

### `green_bond_active` — R3 option_b (`round_configs.py:242`)
Occurrences: `pillar_configs.py:391` (declaration), `pillar_configs.py:1662`
(`FLAG_OVERRIDES`). Nothing else. **DEAD (case ii).**
Not registered in `flag_taxonomy.py`.
(The R3 Green Bond mechanics that do exist — `round_logic.py:2249-2266` — key off
`choice == "option_b"` and the R2 materiality tier, never off this flag.)

### `carbon_deferred` — R3 option_c (`round_configs.py:261`)
Also `pillar_configs.py:344`, `:398`; `FLAG_OVERRIDES` `pillar_configs.py:1663`.
Consumers (LIVE):
1. `engine.py:3947-3985` (FLAG-8, WP-23) — flattened read at `engine.py:3951`;
   gates the entire **Carbon Credit Futures Market** block: seeded spot price
   `500_000 × (1 + U(−0.30, +0.30))`, forward-contract settlement, and the
   `carbon_forward_used` / `carbon_forward_savings` events. The in-code comment
   states the top-level test previously made this block unreachable.
   Effect lands: **every round from the round of choice onward**.
2. `stakeholder_sentiment.py:35-40` — **attitude −6** for regulator / ngo /
   advocacy / community. Effect lands: **round of choice (R3)**.
Terminal-valuation: **No**. Taxonomy class: none.

---

## B.5 Round 4 — Contagion (`round_configs.py:276-318`)

### `remediation_active` — R4 option_a (`round_configs.py:298`)
Occurrences: `pillar_configs.py:501` (declaration), `pillar_configs.py:1666`
(`FLAG_OVERRIDES`), `admin_teleprompter.py:1484` (facilitator text),
`systemic_risk_engine.py:73` (**+8** SCT, unreachable top-level read).
**DEAD in practice (case ii + one unreachable consumer).** Not in taxonomy.

### `pr_containment` — R4 option_b (`round_configs.py:305`)
Occurrences: `flag_taxonomy.py:175`, `pillar_configs.py:503`/`:508`
(declaration). Nothing else. **DEAD (case ii).**
Taxonomy class: `choice-marker`.

### `deny_and_deflect` — R4 option_c (`round_configs.py:312`)
Also `pillar_configs.py:515`; `FLAG_OVERRIDES` `pillar_configs.py:1667`.
Consumers:
1. **LIVE** — `stakeholder_sentiment.py:74-79`: **attitude −8** for employee /
   community / media / journalist. Effect lands: **round of choice (R4)**.
2. **STRUCTURALLY DEAD** — `systemic_risk_engine.py:72`: **−15** SCT, top-level read.
3. **STRUCTURALLY DEAD** — `npc_stakeholders.py:40-56` `_BETRAYAL_FLAGS` /
   `detect_betrayal`, and the duplicate at `autonomous_agents.py:845-885`.
   `detect_betrayal` reads `{k for k,v in events.items() if v is True}` plus
   `events.get("flags_set")`. Nothing writes `events["deny_and_deflect"] = True`
   and nothing writes an `events["flags_set"]` key, so this flag can never
   trigger the NPC trust scar. (The set's engine-written members —
   `greenwashing_scandal`, `greenwashing_detected` — can.)
   Callers: `npc_stakeholders.py:660`, `autonomous_agents.py:499`.
4. `consequence_dna_api.py:63` — "⛔ Brain Drain" node label (display).
Terminal-valuation: **No**. Taxonomy class: none.

---

## B.6 Round 5 — Climate (`round_configs.py:319-403`)

### `hard_engineering` — R5 option_a (`round_configs.py:350`)
Also `pillar_configs.py:639`/`:644`; `FLAG_OVERRIDES` `pillar_configs.py:1670`.

**CORRECTED 2026-09-08 — this flag is DEAD.** The ruling below was written from
reading the code and is superseded; it is kept so the correction can be checked
against what it replaces.

> ~~Consumer (LIVE): `round_logic.py:3511-3534` `_revert_r5_hard_engineering_pulse`
> — flattened read at `:3521-3523` (FLAG-8, WP-23; the comment records that the
> old top-level test made the +3 CI construction pulse permanent). Applies
> **carbon_intensity −3.0 to every BU**, once, guarded by
> `hard_engineering_pulse_reverted`. Effect lands: **Round 7 exactly**
> (`round_number == 7`). Terminal-valuation: **No**.~~

The consumer is real and it cannot fire. `_revert_r5_hard_engineering_pulse`
reads `gs.get("active_event_flags")` (`round_logic.py:3518`), but `post_tick`
receives the **post-tick** state, whose flag bag `engine._assemble_global_state`
set to *this round's events* (`engine.py:4472`, `:4905`) plus the seven session
keys `_forward_persistent_flags` carries (`router.py:2370-2392`). `r5_flags` is
not among them. The history is in `previous_flags`, which `post_tick` also
receives and which every **other** flattened reader in the file uses
(`round_logic.py:423`, `:2195`, `:2507`, `:2537`, `:2666`, `:2675`, `:2683`,
`:2690`). `:3522` is the single exception, and that asymmetry is the proof.

Measured at R7 on the all_a path (the only matrix path taking R5 option_a): the
collected set the function sees is `['greenwashing_checked',
'technology_lockin_penalty']`; `hard_engineering` is absent; the reversal never
applies and the +3 carbon-intensity construction pulse is **permanent** — the
exact defect FLAG-8 / WP-23 believed it had fixed. That fix swapped the reader
(top-level test → `_collect_all_flags`) and left the container wrong.

This is a **fourth defect shape**, not one of the three in §B.0 or in the
remediation plan §1.2:

> **Shape D — wrong generation of the container.** The reader uses the correct
> flattened reader on the correct key, but on the POST-TICK state, which holds
> only this round's events. The history is one parameter away.

The R5 resilience factor of 0.85 that `round_configs.py:353` documents is **not**
delivered by this flag: `impact_engine.py:93` reads
`impacts.get("resilience_factor")` from the chosen option's impacts dict, keyed
by `choice`. So the flag has no second consumer to fall back on.

Evidence: `backend/tests/test_flag_reachability.py::test_hard_engineering_reads_the_wrong_generation_of_the_flag_bag`
proves it without the probe, by spying on the function during a real run.
Also `journey_improvements.py:456-463` (positive warning text, display).
Taxonomy class: none. **Disposition: REVIVE** (read `previous_flags` as well).

### `nature_based_resilience` — R5 option_b (`round_configs.py:370`)
Also `pillar_configs.py:651`; `FLAG_OVERRIDES` `pillar_configs.py:1671`.
Consumer (LIVE): `ending_pathways.py:566-569` — **cross-round pairing**, see §B.14.
Also `journey_improvements.py:465-473` (display).
Terminal-valuation: **Conditionally** — only via the Climate-Black-Swan pathway
calculator, not via `calculate_mr`. Taxonomy class: none.

### `insurance_only` — R5 option_c (`round_configs.py:389`)
Also `pillar_configs.py:653`/`:658`, `healthcare_configs.py:256` (where
`healthcare_configs.py:243` records a deliberate FLAG INVERSION: option A in the
healthcare vertical, option C in the corporate one); `FLAG_OVERRIDES`
`pillar_configs.py:1672`.
Consumer (LIVE): `terminal_valuation.py:233-235` — a **blocking** condition:
```
if not flags.get("insurance_only") and not flags.get("electronics_water_priority")
   and not flags.get("civil_water_priority"):
    mr += 0.20   # "Resilience Champion"
```
Holding it forfeits **+0.20 M_R**. Effect lands: **Round 10 (terminal valuation)**.
(`calculate_mr` is safe against §B.0 because every non-finale caller routes
through `flag_utils.mr_input_from_state` / `mr_flags_from`, `flag_utils.py:67-90`,
which flattens first.)
Also `pedagogical_engine.py:466-467` (locked-out text), `consequence_dna_api.py:64`, `:93`, `:600`.
Terminal-valuation condition: **YES (blocking).** Taxonomy class: none.

---

## B.7 Round 6 — AI Bias (`round_configs.py:404-472`)

### `ai_monetised` — R6 option_a (`round_configs.py:425`)
Also written as a **top-level boolean** at `round_logic.py:2430`
(`gs["active_event_flags"]["ai_monetised"] = True`), plus `pillar_configs.py:801`;
`FLAG_OVERRIDES` `pillar_configs.py:1675`.
Consumers (LIVE):
1. `round_logic.py:2180-2216` `_apply_eu_ai_act_liability` — flattened read at
   `:2195-2197`, runs from post_tick for every round ≥ 7. First qualifying round:
   **treasury −$3,000,000** and **governance_risk_score +5 on every BU** (once,
   marked by `eu_ai_act_assessed`), then **−$1,000,000 per round** ongoing.
   The docstring records that the charge was previously dead code inside
   `_post_r6_ai_bias`. Effect lands: **Round 7 onward**.
2. `black_swan_registry.py:205` — `probability_add: +0.08` on the AI-disruption
   black swan (`round_range [6,10]`, base 0.0333). Reached because
   `black_swan_registry.py:623-629` flattens with `collect_all_flags`.
3. `stakeholder_sentiment.py:60-65` — **attitude −10** for regulator / ngo /
   investor / media / journalist.
4. `admin_router.py:10250-10251` — cohort analytics counter (display).
5. `pedagogical_engine.py:119` (`CASCADE_FLAGS` label), `consequence_dna_api.py:65`, `:95`.
Terminal-valuation: **No**. Taxonomy class: none.

### `ethical_ai_overhaul` — R6 option_b (`round_configs.py:443`)
Also `pillar_configs.py:787`, `healthcare_configs.py:320`; `FLAG_OVERRIDES`
`pillar_configs.py:1676`.
Consumers:
1. **LIVE** — `terminal_valuation.py:236-238`: **+0.15 M_R** "Truth Premium".
   Effect lands: **Round 10**.
2. **LIVE** — `black_swan_registry.py:204`: `probability_add: −0.05` on the
   AI-disruption black swan (comment at `:624` records this was dead before WP-23).
3. **LIVE** — `stakeholder_sentiment.py:54-59`: **attitude +6** for regulator /
   investor / analyst.
4. **STRUCTURALLY DEAD** — `engine.py:2053` `_SDG_FLAG_BONUSES`
   (`{"sdg": 16, "bonus": 15.0}`). Applied at `engine.py:2121-2122` by
   `flags.get(flag_key)`, where `flags` is `ctx.events`
   (`engine.py:4457`) — a dict initialised empty at `engine.py:5055`
   (`events = {}`). No writer ever puts `ethical_ai_overhaul` into `ctx.events`
   as a top-level key. The +15 SDG-16 bonus never applies.
5. **STRUCTURALLY DEAD** — `ceo_interview.py:191-192` (`ethical_score += 2.5`) and
   `:906` — `calc_data_scores` receives the raw `active_event_flags`
   (`router.py:7010`) and uses `.get()`.
Terminal-valuation condition: **YES (+0.15).** Taxonomy class: none.

### `quiet_patch` — R6 option_c (`round_configs.py:458`)
Also `pillar_configs.py:789`/`:794`; `FLAG_OVERRIDES` `pillar_configs.py:1677`.
Consumer (LIVE, sole): `stakeholder_sentiment.py:60-65` — **attitude −10** for
regulator / ngo / investor / media / journalist. Effect lands: **R6**.
Terminal-valuation: **No**. Taxonomy class: none.

---

## B.8 Round 7 — Circularity (`round_configs.py:473-538`)

### `circular_redesign` — R7 option_a (`round_configs.py:490`)
Also `pillar_configs.py:929`; `FLAG_OVERRIDES` `pillar_configs.py:1681`.
Consumers:
1. **PILLAR-ONLY** — `pillar_configs.py:1543-1547` `MUTUAL_EXCLUSIVITY[7]`:
   `[{"synergy_unlock","waste_to_energy"}, {"circular_redesign"}]`, enforced at
   `pillar_configs.py:1596-1617`. On conflict the later group's flags are removed
   from `flags_set` AND that area's impacts are subtracted back out of
   `combined_impacts` (cost still charged). Reachable only through
   `aggregate_pillar_decisions`, i.e. the multi_toggles paradigm.
2. **STRUCTURALLY DEAD** — `engine.py:2054` `_SDG_FLAG_BONUSES`
   (`{"sdg": 12, "bonus": 15.0}`) — same `ctx.events` defect as above.
3. **STRUCTURALLY DEAD** — `systemic_risk_engine.py:74` (**+5** SCT, top-level read).
4. Display: `journey_improvements.py:259`, `admin_teleprompter.py:490`, `:526`, `:1397-1401`.
**DEAD on the default legacy path (case iii + two unreachable consumers).**
Not in taxonomy. Terminal-valuation: **No**.

### `epr_program` — R7 option_b (`round_configs.py:506`)
Occurrences: `pillar_configs.py:936` (declaration), `journey_improvements.py:271`
(display), `systemic_risk_engine.py:75` (**+3** SCT, unreachable top-level read).
Not in `FLAG_OVERRIDES`. **DEAD in practice (case ii + one unreachable consumer).**
Not in taxonomy.

### `waste_to_energy` — R7 option_c, first flag (`round_configs.py:525`)
Occurrences: `pillar_configs.py:897`/`:902` (declaration),
`pillar_configs.py:1546` (`MUTUAL_EXCLUSIVITY`, pillar-only),
`pillar_configs.py:1680` (`FLAG_OVERRIDES`), `journey_improvements.py:273`/`:285`
(display). **DEAD on the default legacy path (case iii).** Not in taxonomy.

### `synergy_unlock` — R7 option_c, second flag (`round_configs.py:525`)
Also `pillar_configs.py:902`, `healthcare_configs.py:378`;
`FLAG_OVERRIDES` `pillar_configs.py:1680`.
Consumer (LIVE): `terminal_valuation.py:209-224` — a **two-condition gate**:
- Condition A: the flag is present (`:213`).
- Condition B: `synergy_multiplier >= 0.80`, ramped over a ±0.05 band
  (`_MR_RAMP_BAND_SYNERGY = 0.10`, `terminal_valuation.py:89`; `_ramp_fraction`
  at `:216`).
Bonus `= round(0.15 × synergy_frac, 4)`, i.e. **up to +0.15 M_R** ("Synergy
Strategic Premium"). `terminal_valuation.py:225-227` records STRAT-010: reduced
from +0.30 because the OPEX savings already flow through `terminal_ebitda`.
Effect lands: **Round 10**. Note the facilitator material still quotes +0.30
(`admin_router.py:1712`, `admin_teleprompter.py:1401`, `:1426`) — stale display.
Terminal-valuation condition: **YES (up to +0.15, gated).** Taxonomy class: none.
Also pillar-only: `MUTUAL_EXCLUSIVITY[7]` (`pillar_configs.py:1546`).

---

## B.9 Round 8 — Blue Stress (`round_configs.py:539-621`)

### `water_efficiency_all` — R8 option_a (`round_configs.py:557`)
Also `pillar_configs.py:1071`; `FLAG_OVERRIDES` `pillar_configs.py:1686`.
Only consumer: `round_logic.py:2574` — appears as a **negative guard** inside
`explicit_electronics_priority`, and only against `r8_pillar_flags`
(built at `round_logic.py:2567-2571` from `events["pillar_flags"]` /
`r8_pillar_flags`). On the legacy path that set is empty, so the clause
collapses to `choice == "option_b"` and this flag is never consulted.
**DEAD on the default path (case iii).** Not in taxonomy.

### `electronics_water_priority` — R8 option_b (`round_configs.py:575`)
Also `pillar_configs.py:1078`; `FLAG_OVERRIDES` `pillar_configs.py:1685`.
Consumers (LIVE):
1. `terminal_valuation.py:233-235` — **blocks the +0.20 "Resilience Champion"
   M_R bonus** (same three-way `not` as `insurance_only`).
   Effect lands: **Round 10**.
2. `round_logic.py:2572-2589` (pillar mode) — when present in `r8_pillar_flags`,
   permits the severe social-licence drop (`social_license_drop_amount`, default
   **−25**) on the listed target BUs; otherwise the drop is suppressed and
   `social_license_severe_drop_skipped` is stamped.
Also display: `consequence_dna_api.py:104`, `:601`; `pedagogical_engine.py:120`.
Terminal-valuation condition: **YES (blocking).** Taxonomy class: none.

### `desalination_built` — R8 option_c (`round_configs.py:598`)
Also `pillar_configs.py:1085`; `FLAG_OVERRIDES` `pillar_configs.py:1684`.
Only consumer: `round_logic.py:2575` — negative guard against `r8_pillar_flags`,
same pillar-only structure as `water_efficiency_all`.
**DEAD on the default path (case iii).** Not in taxonomy.
(The R8 option_c NCD/CapEx mechanics at `round_logic.py:2592-2606` key off
`impacts`, not this flag; `round_configs.py:606-612` documents the F-05 fix that
set `payback_rounds` to 2 so the project matures at the R10 tick.)

---

## B.10 Round 9 — Just Transition (`round_configs.py:622-694`)

### `immediate_closure` — R9 option_a (`round_configs.py:648`)
Also `pillar_configs.py:1215`/`:1220`; `FLAG_OVERRIDES` `pillar_configs.py:1691`;
`MUTUAL_EXCLUSIVITY[9]` `pillar_configs.py:1551`.
Consumers:
1. **PILLAR-ONLY** — `impact_engine.py:292-294`: inside `if pillar_mode:`,
   `has_strike_risk = "immediate_closure" in pillar_flags`. On the legacy path
   strike risk comes from `impacts.get("strike_risk")` (`impact_engine.py:291`),
   an option-impact key, not from this flag.
2. **PILLAR-ONLY** — `MUTUAL_EXCLUSIVITY[9]` (`pillar_configs.py:1549-1552`).
3. `meadows_leverage.py:238-241` — "Fixes That Fail" narrative (debrief text).
4. `consequence_dna_api.py:66` — "⛔ Community Revolt" label.
**DEAD on the default legacy path (case iii).** Not in taxonomy.
Terminal-valuation: **No** — but see §B.11: holding it means holding neither
`managed_transition` nor `community_fund`, so the R9 M_R bonus is forgone and
`just_transition_passed` is False.

### `managed_transition` — R9 option_b (`round_configs.py:663`)
Also `pillar_configs.py:1208`/`:1213`, `healthcare_configs.py:462`,
`side_tracks/corporate_sdg/configs.py:129`; `FLAG_OVERRIDES` `pillar_configs.py:1690`;
`MUTUAL_EXCLUSIVITY[9]` `pillar_configs.py:1551`.
Consumers (LIVE):
1. `terminal_valuation.py:245-247` — `elif` branch (loses to `community_fund`):
   `b = round(0.12 × jt_scaling, 4)`, **+0.12 M_R** "Just Transition".
   Effect lands: **Round 10**. See §B.14 for the `jt_scaling` pairing.
2. `round_logic.py:3441-3444` — sets `extra["just_transition_passed"]`
   (flattened `all_flags`). The comment at `:3430-3440` records B-1: the old
   expression read `just_transition_fund` / `worker_retraining`, which no code
   path ever wrote.
3. **STRUCTURALLY DEAD** — `ceo_interview.py:195-196` (`ethical_score += 1.0`),
   `:314`, `:811` — raw-dict `.get()` reads.
Terminal-valuation condition: **YES (+0.12 × jt_scaling).** Taxonomy class: none.

### `community_fund` — R9 option_c (`round_configs.py:680`)
Also `pillar_configs.py:263` and `:1262`/`:1267`, `healthcare_configs.py:480`,
`side_tracks/corporate_sdg/configs.py:114` (the one place it is written as a
top-level `True`); `FLAG_OVERRIDES` `pillar_configs.py:1689`;
`MUTUAL_EXCLUSIVITY[9]` `pillar_configs.py:1551`.
Consumers:
1. **LIVE** — `terminal_valuation.py:242-244`: `b = round(0.18 × jt_scaling, 4)`,
   **+0.18 M_R** "Community Champion". Takes precedence over `managed_transition`.
   Effect lands: **Round 10**.
2. **LIVE** — `round_logic.py:3441-3444` — `just_transition_passed`.
3. **STRUCTURALLY DEAD** — `engine.py:2052` `_SDG_FLAG_BONUSES`
   (`{"sdg": 1, "bonus": 10.0}`) — `ctx.events` defect.
4. **STRUCTURALLY DEAD** — `ceo_interview.py:193-194` (`ethical_score += 2.0`),
   `:312`, `:811`, `:912`.
Terminal-valuation condition: **YES (+0.18 × jt_scaling).** Taxonomy class: none.

---

## B.11 Round 10 — Grand Finale (`round_configs.py:695-798`)
All three R10 endings apply their effects through the option `impacts` dict, not
through the flag: `round_logic.py:2764` reads `impacts["spinoff_weakest_bu"]`,
`round_logic.py:2777` reads `impacts["synergy_wipe"]`, and R10-C's
`divest_all` / `treasury` / `revenue_delta` / `social_license_delta`
(`round_configs.py:782-793`) are likewise impact keys. A whole-repo search for
the three flag names finds no reader.

### `resist_integrate` — R10 option_a (`round_configs.py:726`)
Occurrences: `pillar_configs.py:1350`/`:1355` (declaration),
`pillar_configs.py:1694` (`FLAG_OVERRIDES`), `admin_router.py:4018` (a comment
listing permitted values of an unrelated `boardroom_choice` request field).
**DEAD (case i/ii).** Not in taxonomy.

### `spinoff` — R10 option_b (`round_configs.py:746`)
Occurrences: `flag_taxonomy.py:176`, `pillar_configs.py:1357`/`:1362`.
Absent from `FLAG_OVERRIDES[10]`. **DEAD (case ii).**
Taxonomy class: `choice-marker`.

### `divest` — R10 option_c (`round_configs.py:765`)
Occurrences: `pillar_configs.py:1364`/`:1369` (declaration),
`pillar_configs.py:1695` (`FLAG_OVERRIDES`). All other whole-word matches are
unrelated English prose (`autonomous_agents.py:874`, `dynamic_cases.py:38`,
`quiz_banks_rounds.py:72`, `admin_teleprompter.py:710`). **DEAD (case i/ii).**
Not in taxonomy.

---

## B.12 Turnaround Option T (`round_configs.py:880-905`)

### `turnaround_restructuring` (`round_configs.py:888`)
Its own description (`round_configs.py:886`) claims it "Sets
turnaround_restructuring flag, enabling Phase 2 transition." No code reads it.
The turnaround module's phase state is a **different key**, `turnaround_phase`
(`turnaround_engine.py:135`, `:177`, `:183`, `:204`, `:284`), driven by the
distress calculation, not by this flag.
Occurrences: `round_configs.py:886`/`:888`, `flag_taxonomy.py:90`.
**DEAD (case ii).** Taxonomy class: `choice-marker`.

---

## B.13 DEAD FLAG REGISTER

Case key:
- **(i)** no occurrence at all outside its own definition;
- **(ii)** occurrences only in `flag_taxonomy.py`, `pillar_configs.FLAG_OVERRIDES`,
  or other reverse-map / display-only locations;
- **(iii)** consumed only in a non-default paradigm (pillar / healthcare) and
  dead on the default path.

### Dead flags declared in `round_configs.py` (16 of 33)

| Flag | Round/option | Case | Evidence |
|---|---|---|---|
| `materiality_exceptions` | R2-B `round_configs.py:174` | ii | Only `flag_taxonomy.py:87` + `pillar_configs.py:220` declaration |
| `ceo_only_signoff` | R2-C `round_configs.py:190` | i/ii | Only its own comment `round_configs.py:189` + `flag_taxonomy.py:89`, `:209` |
| `supply_chain_disruption_risk` | R3-A `round_configs.py:222` | ii | `pillar_configs.py:1661` reverse map; sole nominal consumer `systemic_risk_engine.py:71` (−10 SCT) is an unreachable top-level read |
| `green_bond_active` | R3-B `round_configs.py:242` | ii | `pillar_configs.py:391` decl + `:1662` reverse map only |
| `remediation_active` | R4-A `round_configs.py:298` | ii | `pillar_configs.py:1666` reverse map, `admin_teleprompter.py:1484` display; `systemic_risk_engine.py:73` (+8 SCT) unreachable |
| `pr_containment` | R4-B `round_configs.py:305` | ii | `flag_taxonomy.py:175` + `pillar_configs.py:508` decl only |
| `circular_redesign` | R7-A `round_configs.py:490` | iii | Live consumer only in pillar `MUTUAL_EXCLUSIVITY` `pillar_configs.py:1546`; `engine.py:2054` SDG +15 and `systemic_risk_engine.py:74` +5 both unreachable |
| `epr_program` | R7-B `round_configs.py:506` | ii | `journey_improvements.py:271` display; `systemic_risk_engine.py:75` (+3) unreachable; not in `FLAG_OVERRIDES` |
| `waste_to_energy` | R7-C `round_configs.py:525` | iii | `pillar_configs.py:1546` exclusivity (pillar only) + `:1680` reverse map |
| `water_efficiency_all` | R8-A `round_configs.py:557` | iii | Negative guard `round_logic.py:2574` reads `r8_pillar_flags` only |
| `desalination_built` | R8-C `round_configs.py:598` | iii | Negative guard `round_logic.py:2575` reads `r8_pillar_flags` only |
| `immediate_closure` | R9-A `round_configs.py:648` | iii | `impact_engine.py:294` inside `if pillar_mode:`; `pillar_configs.py:1551` exclusivity |
| `resist_integrate` | R10-A `round_configs.py:726` | i/ii | `pillar_configs.py:1694` reverse map; `admin_router.py:4018` is an unrelated comment |
| `spinoff` | R10-B `round_configs.py:746` | ii | `flag_taxonomy.py:176` + `pillar_configs.py:1362` decl; absent from `FLAG_OVERRIDES[10]` |
| `divest` | R10-C `round_configs.py:765` | i/ii | `pillar_configs.py:1695` reverse map; every other match is English prose |
| `turnaround_restructuring` | Option T `round_configs.py:888` | ii | `flag_taxonomy.py:90` only; real phase key is `turnaround_phase` |

(16 rows: 11 in case (i)/(ii) — no reachable consumer anywhere — plus 5 in case (iii), pillar-mode-only. See the summary table in §B.16.)

### Dead flags declared only in `pillar_configs.py`
Sweep method: whole-word search over `backend` + `frontend/src`, excluding tests,
`flag_taxonomy.py` and `pillar_configs.py` itself. **58 of the 90 pillar-only
flags returned zero hits** — case (i)/(ii) dead choice-markers, and the great
majority carry a `choice-marker` ruling in `flag_taxonomy.py`:

adaptation_fund, ai_supply, automation_pivot, biodiversity_fund, closed_loop,
community_fund_r2, community_water, cost_optimized, dc_optimized, diesel_backup,
digital_inclusion, digital_twin, dry_cooling, efficiency_upgrades,
employee_wellbeing, endowment_created, esg_report, fossil_dependent, green_dc,
green_pivot, green_reskilling, green_tariff, heat_recovery, hybrid_fleet,
lean_process, local_ecosystem, low_carbon_path, manual_oversight,
material_passport, materiality_board_established, materiality_framework_ignored,
nature_offsets, nearshored, net_zero_energy, ngo_partner, offshored,
parametric_insurance, partial_retraining, reckless_automation, regen_agriculture,
regenerative_supply, resilient_network, reverse_logistics, shareholder_only,
stakeholder_compensated, stakeholder_covenant, supply_diversified,
supply_water_audit, targeted_fix, tech_scholarships, transition_bonds,
voluntary_offsets, waste_reduction, water_efficient_supply, watershed_restored,
cooperatives (only hit is an unrelated `side_tracks/supply_chain/configs.py`
declaration), carbon_credits (`admin_shared.py` only), microgrids
(`healthcare_configs.py` declaration only).

Two pillar-only flags NOT in the taxonomy and NOT read:
`materiality_board_established` and `materiality_framework_ignored` — they appear
only in `FLAG_OVERRIDES[2]` (`pillar_configs.py:1657-1658`), whose comment says
they are "Legacy flag names retained so replays of old saves still resolve."

**Case (iii) pillar-only flags with a pillar-mode consumer** (HR-tier
classification at `round_logic.py:1885-1900`, read from `events["pillar_flags"]`):
HIGH — dei_program, people_analytics, green_skills_academy,
crisis_employee_support, emergency_trained, responsible_ai_trained,
circular_reskilled, water_stewards_trained, full_severance_redeployment,
employee_ownership. MEDIUM — leadership_pipeline, engagement_survey, ohs_basic,
basic_ppe, ai_upskilling, cross_trained, shift_optimized, statutory_minimum_hr,
retention_bonuses. NEGATIVE — burnout_risk, hr_absent_transition.
Magnitudes: burnout_delta −10.0 / −4.0 / +12.0 and natural_drift 0.0 / 1.0 / 3.0
(`round_logic.py:1902-1916`).

**Pillar-only flags that ARE live via `stakeholder_sentiment.py`** (reachable in
pillar mode through `events["pillar_flags"]`, `engine.py:4787-4790`, and in legacy
mode where the flag is also a `round_configs` flag): renewable_ppa_signed,
solar_investment, fleet_electrified, sbti_committed (+5); fossil_status_quo,
energy_cut (−6); supplier_remediation (+7); supply_ignored (−8);
greenwash_risk (−10); dei_program, crisis_employee_support, green_skills_academy,
emergency_trained (+6); burnout_risk (−8).

**`blockchain_traceability`** (pillar R2, `pillar_configs.py`) is LIVE and worth
noting: `round_logic.py:2536-2542` (flattened read) — at R8 it sets
`scandal_shock_prevented` and adds **group_reputation +5**.

**`greenwash_risk`** (pillar R3, `pillar_configs.py:420-425`) has NO mechanical
consumer. `terminal_valuation.py:690` claims "R3 → R5, Triggers greenwash if
inv<15%"; that code was NOT FOUND. Its only live read is the −10 sentiment rule.

### Dead flags declared in `ending_pathways.py`
All twelve are written in the final R10 tick. Nine carry a `history` ruling
(`flag_taxonomy.py:24-32`) — nothing runs after R10 to read them:
`emergency_decarb` (`:188`), `climate_adaptation` (`:203`), `climate_deny` (`:218`),
`stakeholder_compact` (`:284`), `selective_appeasement` (`:299`),
`corporate_hardball` (`:314`), `white_knight_defence` (`:381`), `bid_accepted` (`:413`),
`contest_ruling` (`:512`). All case (i)/(ii) — `contest_ruling` has literally zero
occurrences outside its declaration and its taxonomy row.

Three are NOT in the taxonomy:
- `full_remediation` (`ending_pathways.py:480`) — **LIVE**, read at
  `ending_pathways.py:755` (see §B.14).
- `poison_pill` (`ending_pathways.py:397`) — the flag is unread. The mechanic
  fires from the identically-named **impacts** key at `round_logic.py:2881` and
  `:2889`. Case (ii)-equivalent, and see §B.17.
- `consent_decree` (`ending_pathways.py:495`) — same shape; mechanic from
  `impacts["consent_decree"]` at `round_logic.py:2904`.

### Structurally unreachable consumers (a flag with a reader that cannot fire)
This is the most consequential category and is reported separately because these
are not "no consumer" — they are "a consumer the storage format hides".

| Location | Flag(s) | Documented effect that never applies |
|---|---|---|
| `engine.py:4369` | `deep_audit_completed` | Fog-of-War exemption in R1-R2. **CORRECTED 2026-09-08: the documented effect does not exist.** `ctx.events["fog_noise"]` is computed at `engine.py:4372-4382` and read by NOTHING — not in the backend, and not in the frontend, where the only references are a key in a "don't render raw" list (`consequenceCatalog.js:2138`) and two unrelated tunables. The ±10% noise is generated and discarded whether or not the flag is held. What the exemption actually gates is `fog_of_war_active`, which drives one banner in `EngineEventsPanel.js:122`. Not a revival candidate: turning it on would mean implementing a mechanic nobody wrote. Phase 4 left it alone deliberately. |
| `engine.py:2052-2054` + `:2121-2122` (`flags` = `ctx.events`, `engine.py:4457`, initialised `{}` at `:5055`) | `community_fund`, `ethical_ai_overhaul`, `circular_redesign` | SDG-1 +10, SDG-16 +15, SDG-12 +15 — the entire `_SDG_FLAG_BONUSES` registry |
| `systemic_risk_engine.py:66-83` (raw dict from `engine.py:3703-3705`; `flags.get("flags_set")` has no writer) | `deep_audit_completed` +20, `supply_chain_disruption_risk` −10, `deny_and_deflect` −15, `remediation_active` +8, `circular_redesign` +5, `epr_program` +3 (also `blockchain_traceability` +15, `materiality_aligned` +5) | Supply-Chain Transparency score deltas. Note `materiality_aligned` IS a top-level boolean, so its +5 does fire. |
| `npc_stakeholders.py:50-56`, `autonomous_agents.py:880-885` | `deny_and_deflect` | NPC trust betrayal scar |
| `ceo_interview.py:191-196`, `:310-314`, `:811`, `:906-912` (raw dict, `router.py:7010`) | `ethical_ai_overhaul`, `community_fund`, `managed_transition` | CEO-interview `ethical_reasoning` score +2.5 / +2.0 / +1.0 |
| `side_tracks/supply_chain/track.py:102` | `deep_audit_completed` | `_sc_deep_audit_done` bridge value |
| `side_tracks/ethics_sustainability/track.py:95` | `deep_audit_completed` | `ethical_governance` seed +10 |
| `round_logic.py:3518-3524` (**added 2026-09-08**) | `hard_engineering` | R7 reversal of the R5 +3 carbon-intensity construction pulse — see §B.6. **Shape D**, wrong generation of the container: the post-tick flag bag holds this round's events, not the history. |
| `biodiversity_engine.py:442` (**added 2026-09-08**) | `deep_audit` — a name NO configuration declares | Species-risk audit mitigation. **Shape E**, and the only one that FAILS OPEN. See below. |

### Shape E — string containment over the repr of a nested dict

`biodiversity_engine.py:442` reads

```
audit_active = "deep_audit" in str(events.get("active_event_flags", {}))
```

which asks whether eleven characters appear anywhere in the STRINGIFIED flag bag
— keys, values, and the insides of nested dicts and lists alike — against a name
that appears in no `flags_set` anywhere (the flag is `deep_audit_completed`).

Shapes A–D always return False, so their mechanic is simply absent. This one
returns True on unrelated grounds. Measured across the golden matrix on the
deep-audit paths, it is True at exactly three rounds and for three different
reasons, and False in between:

| Round | What it matched |
|---|---|
| R1 | the repr of the `r1_flags` **list**, `"['deep_audit_completed']"` |
| R4 | the **key** `deep_audit_protected` — a pre_tick pre_event, a different flag entirely, set when the team took NEITHER the blindspot nor the deferred audit |
| R10 | inside the stringified `_finale_inputs` blob (renamed from `finale_inputs` on 2026-09-08 — see Shape F below; `str()` does not honour the private prefix, so this 2026.09 behaviour is unchanged) |

Fixing it therefore turns the gate OFF at R4 and R10 as well as ON from R2, so
Phase 4 versioned it (`rules.SWITCHES["biodiversity_audit_gate_reads_flags"]`)
rather than correcting it outright.

Note that this read is invisible to BOTH guards: to `tests/test_flag_sweep.py`
because the name it uses is not a declared flag, and to `tests/flag_probe.py`
because a substring test over a string is not a keyed read of any container. It
was found by reading `biodiversity_engine.py` while tracing the fifth of the six
Phase 4 revivals.

### Shape F — a storage record parked in the flag namespace (added 2026-09-08)

Found in Phase 5, by MEASURING rather than by reading: shapes A–E are all reads
that cannot see a flag; this is the mirror image — a **write** that makes the
reader see flags that are not there.

`round_logic._post_r10_grand_finale` records the inputs its valuation resolved,
because `router.commit_turn` re-runs that valuation on the closing state (audit
F-08 / SEAM-05) and the replay must be exact. The record carries `all_flags` — a
snapshot of every flag in force at R10 — and `special`, the ending pathway's
config dict. It was written under a bare key on `active_event_flags`, which **is**
the flag namespace, and `flag_utils.collect_all_flags` recurses into any nested
dict whose key is not underscore-prefixed and harvests every list under a key
containing "flag".

So at R10 the record handed the entire game's flag history back to any consumer
asking the events bag what was set *this round*. Attributed per container on path
`all_c` under rules 2026.10:

| Fire | Round | Container | Flags |
|---|---|---|---|
| 1 | R2 | `materiality_ignored` (a top-level boolean) | `materiality_ignored` — correct, set at R2 |
| 2 | R4 | `r4_flags` / `flags_set_r4` | `deny_and_deflect` — correct, set at R4 |
| 3 | R10 | `finale_inputs` | `deny_and_deflect`, `materiality_ignored` — **neither was set at R10** |

One R4 decision, two NPC/agent trust scars. The record also contributed
`is_healthcare`, `brsr` and every boolean inside the pathway config as flag names
(`exit_multiple_ci_haircut` is a config key and a float stamp, and it was in the
golden matrix's flag list for a year on that basis), and in the closing bag it
resurrected flags the round had already cleared — `insolvency_warning`,
`phase_transition`, `micro_strike_triggered`, `distress_detected`,
`reflection_required`.

**Why it hid.** The other five shapes are visible to a reader who knows what to
look for. This one is invisible to reading, because nothing at the read site is
wrong: `collect_all_flags` behaves exactly as documented, and `detect_betrayal`
asks the right question of the right bag. Only the *contents* of the bag are
wrong, and only in one round. `tests/flag_probe.py` cannot see it either — the
read is a legitimate keyed read that returns True, which is what the probe is
looking for. It surfaced only when 3,300 sampled games made the resulting M_R
distribution too heavy to ignore.

**The fix is the convention this appendix's own reading module already states.**
`flag_utils.py:30-35` records that an underscore prefix marks a private state bag
as storage, because recursing into them "polluted the flag namespace with names
no writer ever intended as flags." The record now follows it
(`flag_utils.FINALE_INPUTS_KEY = "_finale_inputs"`), with `finale_inputs_of()`
still reading the legacy key so persisted sessions replay.

**Not versioned.** Re-running the full 3,300-pair sweep before and after: the
2026.09 arm is bit-identical in M_R, terminal value and archetype, in both black-
swan regimes. Across the golden matrix the only 2026.09 movement is the
diagnostic `flags` listing at R10 on four paths. There is no 2026.09 behaviour to
preserve here — the defect only became load-bearing when 2026.10 turned on a
reader that asks the events bag what happened this round. Full measurement:
`docs/verification/phase5_recalibration.md` §5.2.

**Count.** The table now has nine locations. Six were found by reading the code
for this appendix; `round_logic.py:3518` was found by RUNNING it
(`tests/test_flag_reachability.py`, 2026-09-08), which is the argument for the
executable probe in one row; `biodiversity_engine.py:442` was found by reading
again, with the shapes already named — which is the argument for naming them.
Shape F was found by neither: it was found by SAMPLING (Phase 5, 2026-09-08),
which is the argument for the third instrument.

---

## B.14 CROSS-ROUND FLAG COMBINATIONS
Places where the code requires **two or more flags together**, or a flag together
with a second gating quantity, before an effect applies.

### 1. Adaptation Premium — TWO FLAGS, +0.20 M_R
`backend/ending_pathways.py:566-569`
```
# +0.20: Adaptation Premium — nature_based_resilience AND early_decarboniser
if "nature_based_resilience" in all_flags and "early_decarboniser" in all_flags:
    mr_delta += 0.20
    extra["mr_adaptation_premium"] = True
```
- Flags: `nature_based_resilience` (**R5 option_b**, `round_configs.py:370`) AND
  `early_decarboniser` (**R3 option_a**, `round_configs.py:222`).
- Magnitude: **+0.20 M_R**, flat (not ramped — the only un-ramped bonus in
  `calc_climate_black_swan_mr`).
- Lands: Round 10, and ONLY on the **Climate Black Swan** ending pathway
  (`calc_climate_black_swan_mr`). On any other pathway the pairing pays nothing.

### 2. Supply Chain Transparency — EITHER OF TWO FLAGS, +0.20 M_R
`backend/ending_pathways.py:754-757`
```
if "scope_3_transparency" in all_flags or "full_remediation" in all_flags:
    mr_delta += 0.20
    extra["mr_supply_chain_transparency"] = True
```
- Flags: `scope_3_transparency` (top-level boolean, written `round_logic.py:2357`)
  OR `full_remediation` (R10 ending flag, `ending_pathways.py:480`).
- Magnitude: **+0.20 M_R**. Lands: Round 10, **Regulatory Shutdown** pathway only.
- This is an OR, not an AND — listed for completeness of the pathway-bonus set.

### 3. Synergy Strategic Premium — FLAG + STATE THRESHOLD, up to +0.15 M_R
`backend/terminal_valuation.py:209-224`
- Condition A: `synergy_unlock` (**R7 option_c**, `round_configs.py:525`).
- Condition B: `synergy_multiplier >= 0.80`, ramped ±0.05
  (`_MR_RAMP_BAND_SYNERGY = 0.10`, `terminal_valuation.py:89`).
- Magnitude: `round(0.15 × synergy_frac, 4)` — **up to +0.15 M_R**.
- The docstring at `terminal_valuation.py:156-160` states BOTH must hold: "a flag
  earned while synergy had already decayed below threshold does not qualify".
- Interacts with the R3 flag: `early_decarboniser` adds **+0.10** to
  `synergy_multiplier` at R7 (`round_logic.py:2508-2512`), which is exactly the
  quantity Condition B tests. R3-A therefore materially raises the odds that the
  R7-C flag pays out at R10 — an implicit R3+R7 combination.

### 4. Just Transition scaling — R9 FLAG × HR INVESTMENT ROUNDS
`backend/terminal_valuation.py:240-247`
```
jt_scaling = 1.0
if hr_investment_rounds > 0 and (flags.get("community_fund") or flags.get("managed_transition")):
    jt_scaling = round(min(1.5, 1.0 + hr_investment_rounds * 0.10), 2)
if flags.get("community_fund"):
    b = round(0.18 * jt_scaling, 4)   # up to +0.27
elif flags.get("managed_transition"):
    b = round(0.12 * jt_scaling, 4)   # up to +0.18
```
- Flags: `community_fund` (R9-C) or `managed_transition` (R9-B) — mutually
  exclusive here by `elif` — combined with the count of distinct rounds carrying
  an `hr_invested_r{N}` key (`flag_utils.hr_investment_rounds_from`, `:59-65`).
- Magnitude: scaling **1.0 → 1.5** at +0.10 per HR round, capped at 1.5
  (5 HR rounds). Community Champion **+0.18 → +0.27**; Just Transition
  **+0.12 → +0.18**. Lands: Round 10.
- `round_logic.py:1919-1930` records B-4: the only writer previously wrote a
  plain `hr_invested` key with no round number, so `hr_investment_rounds` was
  structurally always 0 and this scaling was dead. Fixed at this HEAD.

### 5. Resilience Champion — THREE-FLAG NEGATIVE CONJUNCTION, +0.20 M_R
`backend/terminal_valuation.py:233-235`
```
if not flags.get("insurance_only") and not flags.get("electronics_water_priority")
   and not flags.get("civil_water_priority"):
    mr += 0.20
```
- Flags: `insurance_only` (**R5-C**), `electronics_water_priority` (**R8-B**),
  `civil_water_priority` (healthcare vertical R8 equivalent — NOT declared in
  `round_configs.py`). **All three must be absent.**
- Magnitude: **+0.20 M_R**, all-or-nothing (no ramp). Lands: Round 10.
- This is the only cross-round condition in the codebase that spans R5 and R8
  and is decided by absence rather than presence.

### 6. Fortress Premium — MARGIN GATE × SCANDAL-FLAG SET, up to +0.20 M_R
`backend/ending_pathways.py:690-701`
```
scandal_flags = {"scandal_erupted", "whistleblower_investigation", "greenwash_exposed",
                 "greenwashing_scandal", "greenwashing_detected", "greenwash_detected"}
_f = _ramp_fraction(ebitda_margin, 0.20, _BAND_MARGIN, "above") if not all_flags.intersection(scandal_flags) else 0.0
```
- Magnitude: **up to +0.20 M_R**, ramped over ±0.025 EBITDA margin around 20%.
  Lands: Round 10, **Hostile Takeover** pathway only.
- FLAG-9 note at `ending_pathways.py:692-695`: `scandal_erupted` and
  `greenwash_exposed` "are written nowhere"; the engine's real scandal keys are
  `greenwashing_scandal` / `greenwashing_detected`.

### 7. Regulatory Exemplar — SCORE GATE × SCANDAL-FLAG SET, up to +0.30 M_R
`backend/ending_pathways.py:746-752` — same scandal-set structure (minus
`whistleblower_investigation`'s position), ramped on a composite `ethical_score`
above 7.0 with `_BAND_ETHICAL = 1.0`. Lands: Round 10, **Regulatory Shutdown**
pathway only.

### 8. Mutual exclusivity — PILLAR MODE ONLY
`backend/pillar_configs.py:1543-1553`, enforced `:1596-1617`
- R7: `[{synergy_unlock, waste_to_energy}, {circular_redesign}]`
- R9: `[{community_fund}, {managed_transition}, {immediate_closure}]`
- Effect: on conflict the first-listed group wins; every conflicting flag is
  removed from `flags_set` AND that area's impacts are subtracted back out of
  `combined_impacts` — the cost is deliberately NOT refunded
  (`pillar_configs.py:1610-1616`). Reachable only in the multi_toggles paradigm.

### 9. R5 Shadow Board rejection flags (declared outside the four named files)
Written top-level at `shadow_board_audit.py:252` from `REJECTION_FLAGS`
(`shadow_board_audit.py:121-160`). Each is an R5→R10 dependency:
- `planet_expendable` → `terminal_valuation.py:258-260`, **−0.20 M_R**, on every
  ending. `ending_pathways.py:587-608` documents that the same −0.20 used to be
  applied a second time here (total −0.40) and that the duplicate was removed
  because 0.80 is exactly the `fragile_giant` / `stranded_relic` boundary in
  `terminal_valuation._THRESHOLDS`; the block now carries narrative only.
- `shareholder_alienated` → `ending_pathways.py:716-723`, **−0.20 M_R**,
  Hostile Takeover pathway only.
- `governance_fragility` → `ending_pathways.py:772-779`, **−0.25 M_R**,
  Regulatory Shutdown pathway only.

---

## B.15 Terminal-valuation conditions (`backend/terminal_valuation.py:127-320`)
Flags that `calculate_mr` reads directly:
| Flag | Line | Effect |
|---|---|---|
| `materiality_aligned` | `:198` | +0.10 |
| `materiality_partial` | `:201` (elif) | +0.05 |
| `synergy_unlock` | `:213` | up to +0.15, gated on synergy ≥ 0.80 (ramped) |
| `insurance_only` | `:233` | blocks +0.20 |
| `electronics_water_priority` | `:233` | blocks +0.20 |
| `civil_water_priority` | `:233` | blocks +0.20 |
| `ethical_ai_overhaul` | `:236` | +0.15 |
| `community_fund` | `:240`, `:242` | +0.18 × jt_scaling |
| `managed_transition` | `:240`, `:245` (elif) | +0.12 × jt_scaling |
| `planet_expendable` | `:258` | −0.20 |
| `brsr_net_positive_dividend` | `:262` | + its numeric value |
Non-flag ramped terms: workforce_readiness ≥ 75 (+0.10, `:249`), avg_burnout < 20
(+0.05, `:254`), avg_slo < 75 (−0.40, `:267`).
`max_achievable_mr_for` (`:70-75`) reads `brsr_net_positive_dividend`.
`what_if_terminal` (`:625-654`) merges `flag_overrides` over `base_flags` for the
replay tool.

---

## B.16 Summary table — the 33 `round_configs.py` flags

| # | Flag | Round / option | Set at | Status |
|---|---|---|---|---|
| 1 | electronics_blindspot | R1 A | `round_configs.py:50` | LIVE |
| 2 | deep_audit_completed | R1 B | `round_configs.py:68` | LIVE (1 live consumer; 4 unreachable) |
| 3 | deferred_audit | R1 C | `round_configs.py:87` | LIVE |
| 4 | full_materiality_alignment | R2 A | `round_configs.py:149` | LIVE **in `advanced_climate` only** (in-file comment stale) — its consumer `engine.py:3787` sits inside `if ctx.decision_paradigm == "advanced_climate":` (`engine.py:3763`), so it is inert on the default path. Measured 2026-09-08: NCD forgiveness 1.23 → 1.54 with the flag under `advanced_climate`, unchanged under `legacy_abc`. |
| 5 | materiality_exceptions | R2 B | `round_configs.py:174` | DEAD (ii) |
| 6 | ceo_only_signoff | R2 C | `round_configs.py:190` | DEAD (i/ii) |
| 7 | supply_chain_disruption_risk | R3 A | `round_configs.py:222` | DEAD (ii) |
| 8 | early_decarboniser | R3 A | `round_configs.py:222` | LIVE |
| 9 | green_bond_active | R3 B | `round_configs.py:242` | DEAD (ii) |
| 10 | carbon_deferred | R3 C | `round_configs.py:261` | LIVE |
| 11 | remediation_active | R4 A | `round_configs.py:298` | DEAD (ii) |
| 12 | pr_containment | R4 B | `round_configs.py:305` | DEAD (ii) |
| 13 | deny_and_deflect | R4 C | `round_configs.py:312` | LIVE (sentiment only; 2 unreachable) |
| 14 | hard_engineering | R5 A | `round_configs.py:350` | **DEAD (shape D)** — corrected 2026-09-08, see §B.6 |
| 15 | nature_based_resilience | R5 B | `round_configs.py:370` | LIVE (pathway-conditional) |
| 16 | insurance_only | R5 C | `round_configs.py:389` | LIVE |
| 17 | ai_monetised | R6 A | `round_configs.py:425` | LIVE |
| 18 | ethical_ai_overhaul | R6 B | `round_configs.py:443` | LIVE (3 live; 2 unreachable) |
| 19 | quiet_patch | R6 C | `round_configs.py:458` | LIVE (sentiment only) |
| 20 | circular_redesign | R7 A | `round_configs.py:490` | DEAD (iii) |
| 21 | epr_program | R7 B | `round_configs.py:506` | DEAD (ii) |
| 22 | waste_to_energy | R7 C | `round_configs.py:525` | DEAD (iii) |
| 23 | synergy_unlock | R7 C | `round_configs.py:525` | LIVE |
| 24 | water_efficiency_all | R8 A | `round_configs.py:557` | DEAD (iii) |
| 25 | electronics_water_priority | R8 B | `round_configs.py:575` | LIVE |
| 26 | desalination_built | R8 C | `round_configs.py:598` | DEAD (iii) |
| 27 | immediate_closure | R9 A | `round_configs.py:648` | DEAD (iii) |
| 28 | managed_transition | R9 B | `round_configs.py:663` | LIVE |
| 29 | community_fund | R9 C | `round_configs.py:680` | LIVE |
| 30 | resist_integrate | R10 A | `round_configs.py:726` | DEAD (i/ii) |
| 31 | spinoff | R10 B | `round_configs.py:746` | DEAD (ii) |
| 32 | divest | R10 C | `round_configs.py:765` | DEAD (i/ii) |
| 33 | turnaround_restructuring | Option T | `round_configs.py:888` | DEAD (ii) |

**17 LIVE / 16 DEAD** as first written. **Corrected 2026-09-08 to 16 LIVE / 17
DEAD**, `hard_engineering` having moved — and of the 16 remaining LIVE, one
(`full_materiality_alignment`) is live in the `advanced_climate` paradigm only.
Both corrections came from `tests/test_flag_reachability.py`, which reaches its
verdicts by scrubbing a flag out of the namespace and re-running the ten-round
matrix rather than by reading the source.

---

## B.17 NOT FOUND / UNCERTAIN

1. **NOT FOUND** — any code implementing `terminal_valuation.py:688`
   ("R2 `blockchain_traceability` → R8: Prevents supply chain scandal"). The
   nearest real code is `round_logic.py:2536-2542`, which sets
   `scandal_shock_prevented` and **group_reputation +5** at R8. The graph entry
   understates it (it is a reputation gain, not only a prevention) and misstates
   the source round (the flag is declared in pillar R2 config; NOT FOUND in any
   `round_configs.py` R2 option).
2. **NOT FOUND** — any code implementing `terminal_valuation.py:690`
   ("R3 `greenwash_risk` → R5: Triggers greenwash if inv<15%"). No reader.
3. **NOT FOUND** — the "+0.30 synergy M_R" quoted at `admin_router.py:1712`,
   `admin_teleprompter.py:1401` and `:1426`. The code value is **+0.15**
   (`terminal_valuation.py:219-224`, STRAT-010). The teleprompter's
   "Max M_R pathway … = 1.98" arithmetic is built on the stale +0.30.
4. **NOT FOUND** — `civil_water_priority` in any `flags_set` list in the four
   named files. It is read at `terminal_valuation.py:233` and listed in
   `pedagogical_engine.py:120`; its declaration is in the healthcare vertical.
   Not audited further (outside the four named files).
5. **NOT FOUND** — any writer for `just_transition_fund` or `worker_retraining`;
   `round_logic.py:3432-3434` states outright that these were read by the old
   Just-Transition expression and "no code path ever wrote" them. Now removed.
6. **NOT FOUND** — any writer for `scandal_erupted` or `greenwash_exposed`,
   confirmed by the FLAG-9 comment at `ending_pathways.py:692-695`.
7. **UNCERTAIN** — why `poison_pill` and `consent_decree` (declared in
   `ending_pathways.py:397`, `:495`) are absent from `FLAG_TAXONOMY` when the
   other nine ending flags are present. Both names also exist as **impacts** keys
   read at `round_logic.py:2881`, `:2889`, `:2904`; a name-based "is it read?"
   sweep would see those and count the flag as read. I could not confirm from
   `tests/test_flag_taxonomy.py` (not read at this HEAD) whether that is the
   actual mechanism. The flags themselves have no reader.
8. **UNCERTAIN** — `flag_utils.collect_all_flags`'s fallback list
   (`flag_utils.py:49-54`) implies `electronics_blindspot` and
   `deep_audit_completed` can appear as top-level keys. I found no writer that
   puts either there. If some legacy save format did, `engine.py:4369` and the
   `systemic_risk_engine.py` boosts would fire for those saves only. Not
   verifiable from code alone.
9. **UNCERTAIN** — whether `side_tracks/corporate_sdg/configs.py:114`
   (`"flags": {"sdg_living_wage": True, "community_fund": True}`) reaches
   `ctx.events` as a top-level key. If a track write-back path merges that dict
   into events, the SDG-1 +10 bonus at `engine.py:2052` could fire for
   corporate-SDG-track sessions. I did not trace the side-track write-back
   (`router.py:6462`, `events["write_back_flags"]`) far enough to rule it in or out.
10. **NOT AUDITED (out of scope)** — `healthcare_configs.py`,
    `journey_improvements.py`, `side_tracks/*/configs.py` and
    `black_swan_registry.py` declarations were read only where a
    `round_configs` / `pillar_configs` / `ending_pathways` flag appeared in them.
    Their own flag sets are enumerated in §B.1 from `flag_taxonomy.py` but their
    consumers were not individually traced.
11. **NOTE, not a finding** — `pillar_configs.py:1543-1553` `MUTUAL_EXCLUSIVITY`
    is a genuine consumer, unlike `FLAG_OVERRIDES` in the same file. The two
    blocks must not be conflated.
