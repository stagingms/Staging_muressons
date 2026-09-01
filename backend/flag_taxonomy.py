"""Flag taxonomy — the ruling record for every declared-but-unread flag.

DEEP-5/9 resolution (owner rulings, 2026-09-01). The invariant is enforced by
tests/test_flag_taxonomy.py: every flag declared in a `flags_set` list must
either be READ somewhere (backend non-test code or frontend/src) or carry an
entry here saying WHY it is deliberately unread. Entries for flags that gain
a reader, or stop being declared, fail the test until removed — the registry
cannot rot in either direction.

Classes:
  choice-marker  records which option a team took; effects applied elsewhere
  narrative      flavour/bookkeeping the model deliberately does not consume
  history        permanent record written at game end; nothing runs after it

Also ruled 2026-09-01 (not in this dict because they are written by track
code, not declared in flags_set): the five side-track M_R flags
(sc/sm/sr/es)_track_mr_bonus/_mr_penalty and sdg_mr_bonus are deliberately
unread — the owner chose honest display (no student-facing M_R promises)
over wiring them, keeping the pinned M_R ceilings 1.93/2.02 untouched.
"""

FLAG_TAXONOMY: dict[str, dict[str, str]] = {
    # ── ending_pathways.py ──
    "bid_accepted": {"class": "history", "declared_in": "ending_pathways.py"},
    "climate_adaptation": {"class": "history", "declared_in": "ending_pathways.py"},
    "climate_deny": {"class": "history", "declared_in": "ending_pathways.py"},
    "contest_ruling": {"class": "history", "declared_in": "ending_pathways.py"},
    "corporate_hardball": {"class": "history", "declared_in": "ending_pathways.py"},
    "emergency_decarb": {"class": "history", "declared_in": "ending_pathways.py"},
    "selective_appeasement": {"class": "history", "declared_in": "ending_pathways.py"},
    "stakeholder_compact": {"class": "history", "declared_in": "ending_pathways.py"},
    "white_knight_defence": {"class": "history", "declared_in": "ending_pathways.py"},
    # ── healthcare_configs.py ──
    "air_freight_emergency": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "cancelled_electives": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "circular_hubs": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "clinician_retraining": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "closed_loop_water": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "consolidation": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "digital_triage_active": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "divest_weakest": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "hardened_hospital_grid": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "heavy_icu_capex": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "human_triage_override": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "incinerator_lobbying": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "local_sterile_resilience": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "patient_evacuation": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "quiet_patch_oncology": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "regional_clinics_built": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "telehealth_litigation": {"class": "narrative", "declared_in": "healthcare_configs.py", "note": "future-mechanics candidate: could feed a liability event like the EU AI Act path."},
    "telehealth_overhaul": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "union_busted": {"class": "narrative", "declared_in": "healthcare_configs.py", "note": "future-mechanics candidate: could raise strike probability (R9 special_rules)."},
    "universal_care_charter": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "vendor_replacement": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    "water_trucking": {"class": "narrative", "declared_in": "healthcare_configs.py"},
    # ── journey_improvements.py ──
    "independent_investigation": {"class": "narrative", "declared_in": "journey_improvements.py"},
    "whistleblower_accountability": {"class": "narrative", "declared_in": "journey_improvements.py"},
    "whistleblower_suppressed": {"class": "narrative", "declared_in": "journey_improvements.py"},
    # ── pillar_configs.py ──
    "ai_supply": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "community_fund_r2": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "cooperatives": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "cost_optimized": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "dc_optimized": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "diesel_backup": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "employee_wellbeing": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "endowment_created": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "esg_report": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "green_dc": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "hybrid_fleet": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "low_carbon_path": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "nature_offsets": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "nearshored": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "net_zero_energy": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "ngo_partner": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "offshored": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "reckless_automation": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "regen_agriculture": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "shareholder_only": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "supply_diversified": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "supply_water_audit": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "tech_scholarships": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "water_efficient_supply": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    "watershed_restored": {"class": "choice-marker", "declared_in": "pillar_configs.py"},
    # ── pillar_configs.py, round_configs.py ──
    "materiality_exceptions": {"class": "choice-marker", "declared_in": "pillar_configs.py, round_configs.py"},
    # ── round_configs.py ──
    "ceo_only_signoff": {"class": "choice-marker", "declared_in": "round_configs.py"},
    "full_materiality_alignment": {"class": "choice-marker", "declared_in": "round_configs.py"},
    "turnaround_restructuring": {"class": "choice-marker", "declared_in": "round_configs.py"},
    # ── side_tracks/brsr_ngrbc/configs.py ──
    "brsr_indicator_leadership": {"class": "narrative", "declared_in": "side_tracks/brsr_ngrbc/configs.py"},
    # ── side_tracks/stakeholder_management/configs.py ──
    "sm_community_partnership": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_defensive_crisis": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_esg_gold_standard": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_gap_closure": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_investor_focus": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_issb_aligned": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_legal_escalation": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_media_hostile": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_rating_challenge": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_structured_response": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_transparency_champion": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    "sm_voluntary_commitments": {"class": "narrative", "declared_in": "side_tracks/stakeholder_management/configs.py"},
    # ── side_tracks/supply_chain/configs.py ──
    "circular_minimum_compliance": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "circular_procurement_partial": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "crisis_passive_response": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "crisis_response_full": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "crisis_response_targeted": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "digital_twin_supply": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "erp_integration_sc": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "ethical_sourcing_restructured": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "ethical_sourcing_transitional": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "geographic_diversified": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "inventory_buffer_only": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "manual_compliance_sc": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "partial_tier_mapping": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "remediation_fund_active": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "sbti_risk": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "sc_monitoring_only": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "sc_resilient": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "scope3_deep_cut": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "scope3_offset_only": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "supplier_switching": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "supply_disruption_risk": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    "take_back_active": {"class": "narrative", "declared_in": "side_tracks/supply_chain/configs.py"},
    # ── side_tracks/sustainability_reporting/configs.py ──
    "sr_activist_opposition": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_ar_integrated": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_climate_adequate": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_climate_gap": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_climate_leader": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_esg_controls": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_full_esrs": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_integrated_leader": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_limited_assurance": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_living_wage": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_phased_compliance": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_reasonable_assurance": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_sbti_targets": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_scope3_complete": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_sfdr_compliant": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_siloed_reporting": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_social_gap": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_social_leader": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
    "sr_value_demonstrated": {"class": "narrative", "declared_in": "side_tracks/sustainability_reporting/configs.py"},
}

# One shared reason per declaring file (kept out of each row for size):
TAXONOMY_REASONS: dict[str, str] = {
    "pillar_configs.py": "Pillar-mode option identity marker; the router is the single impact applier (fix/pillar-impact-ownership), so the flag records WHICH option was taken, not an effect.",
    "healthcare_configs.py": "Healthcare vertical consequence marker with no wired mechanic; candidates for future wiring are noted below.",
    "side_tracks/supply_chain/configs.py": "Supply-chain side-track outcome marker; the track keeps its own score/leaderboard, main-sim mechanics unaffected by owner ruling 2026-09-01.",
    "side_tracks/sustainability_reporting/configs.py": "Sustainability-reporting side-track outcome marker; same ruling.",
    "side_tracks/stakeholder_management/configs.py": "Stakeholder-management side-track outcome marker; same ruling.",
    "side_tracks/brsr_ngrbc/configs.py": "BRSR side-track outcome marker; same ruling.",
    "ending_pathways.py": "R10 ending identity — set in the final tick as the permanent record of how the game ended; nothing runs after R10 to read it.",
    "round_configs.py": "Core-game choice marker with no consumer (ceo_only_signoff already ruled a marker in its config comment).",
    "journey_improvements.py": "Whistleblower-arc narrative marker (R6 crisis flavour), no wired mechanic.",
}
