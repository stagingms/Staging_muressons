"""flags/registry.py — the specification of every declared flag.

STATUS MEANS WHAT IT SAYS, WHICH IS THE POINT OF PHASE 2
    The first cut of this file derived LIVE from "absent from flag_taxonomy.py".
    That was wrong. The taxonomy records what a TEXTUAL sweep found unread, and
    that sweep counts a quoted occurrence as a read — so a flag whose only
    consumer can never fire looks read, escapes a ruling, and was labelled LIVE.
    Eleven of the sixteen round flags verified dead in Appendix B were LIVE here.

    LIVE             a consumer has been shown to observe it, and `effect` says
                     what moves and by how much, with `evidence` giving file:line
    DEAD_DEFECT      verified to have no reachable consumer; `effect` records why
                     and `evidence` where. This is a defect register, not a ruling
    INERT_BY_DESIGN  the owner ruled it deliberately unread; `ruling` carries it
    UNVERIFIED       declared, and reachability has NOT been established either
                     way. The honest default. Phase 3's runtime probe exists to
                     drive this count to zero; until then the registry does not
                     claim more than it can show.

WHY UNVERIFIED IS NOT A COP-OUT
    Reachability is a runtime property. Establishing it statically costs a full
    consumer trace per flag — roughly what the Appendix B extraction spent on 33
    of them. Asserting LIVE for the rest on the strength of a sweep that is known
    blind would put a false claim in the one artefact that is supposed to be
    authoritative.

At generation: 285 flags — 18 LIVE, 11 DEAD_DEFECT, 156 INERT_BY_DESIGN, 100 UNVERIFIED.
Round-flag facts verified at commit 0ad1246 and spot-checked against source.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FlagSpec:
    name: str
    status: str
    scope: tuple[str, ...]
    declared_in: tuple[str, ...]
    ruling: str = ""      # required when INERT_BY_DESIGN or DEPRECATED
    sets_at: str = ""     # which round and option writes it
    effect: str = ""      # required when LIVE or DEAD_DEFECT
    evidence: str = ""    # file:line — required when LIVE or DEAD_DEFECT
    # ── Phase 4 fields ────────────────────────────────────────────────────
    revived_in: str = ""  # the rules version in which the defect is FIXED.
    #   status stays DEAD_DEFECT while rules.CURRENT_VERSION predates it, because
    #   that is what is true of every session anyone is playing. When Phase 5
    #   moves CURRENT_VERSION, these become LIVE in one reviewed pass — and the
    #   field is what makes that pass a filter rather than an investigation.
    removes_at: str = ""  # the release in which a DEPRECATED flag is DELETED.
    #   Deprecation is not deletion. Dropping a declared flag mid-flight changes
    #   what a replayed session's r{N}_flags contains even when no number moves,
    #   so the flag stays declared and the registry carries the intent — which is
    #   the disposition the remediation plan §4.2 asks for and the place it says
    #   divest_all's belongs, rather than in a test allow-list.


LIVE = "LIVE"
DEAD_DEFECT = "DEAD_DEFECT"
INERT_BY_DESIGN = "INERT_BY_DESIGN"
UNVERIFIED = "UNVERIFIED"
DEPRECATED = "DEPRECATED"

REGISTRY: dict[str, FlagSpec] = {
    'adaptation_fund': FlagSpec('adaptation_fund', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'ai_monetised': FlagSpec('ai_monetised', LIVE, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R6 option A', 'EU AI Act liability from R7: $3,000,000 on first firing plus +5 governance risk per unit, then $1,000,000 in each later round. Black-swan probability +0.08.', 'round_logic.py:2201, :2204-2206, :2220-2221; black_swan_registry.py:205'),
    'ai_supply': FlagSpec('ai_supply', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'ai_upskilling': FlagSpec('ai_upskilling', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'air_freight_emergency': FlagSpec('air_freight_emergency', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'automation_pivot': FlagSpec('automation_pivot', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'basic_ppe': FlagSpec('basic_ppe', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'bid_accepted': FlagSpec('bid_accepted', INERT_BY_DESIGN, ('default',), ('ending_pathways.py',), 'owner ruling 2026-09-01, class: history', '', '', ''),
    'biodiversity_fund': FlagSpec('biodiversity_fund', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'blockchain_traceability': FlagSpec('blockchain_traceability', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'blockchain_traceability_sc': FlagSpec('blockchain_traceability_sc', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_circular_symbiosis': FlagSpec('brsr_circular_symbiosis', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_compliance_only': FlagSpec('brsr_compliance_only', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_core_assured': FlagSpec('brsr_core_assured', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_ethics_officer': FlagSpec('brsr_ethics_officer', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_greenwash_risk': FlagSpec('brsr_greenwash_risk', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_indicator_essential': FlagSpec('brsr_indicator_essential', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_indicator_leadership': FlagSpec('brsr_indicator_leadership', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'brsr_integrated_report': FlagSpec('brsr_integrated_report', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_living_wage': FlagSpec('brsr_living_wage', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_net_positive_dividend': FlagSpec('brsr_net_positive_dividend', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_pioneer': FlagSpec('brsr_pioneer', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_regulatory_minimum': FlagSpec('brsr_regulatory_minimum', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'brsr_statutory_minimums': FlagSpec('brsr_statutory_minimums', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'burnout_risk': FlagSpec('burnout_risk', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'cancelled_electives': FlagSpec('cancelled_electives', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'carbon_credits': FlagSpec('carbon_credits', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'carbon_deferred': FlagSpec('carbon_deferred', LIVE, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R3 option C', 'Balance-sheet effect (FLAG-8), plus stakeholder sentiment.', 'engine.py:3951; stakeholder_sentiment.py:36'),
    'ceo_only_signoff': FlagSpec('ceo_only_signoff', INERT_BY_DESIGN, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), "INERT_BY_DESIGN, ruling dated 2026-09-08 (remediation plan §4.3), and confirmed by execution rather than by a name sweep: tests/test_flag_reachability.py reports it dead under BOTH rule sets, never read by anything. A choice marker — the option's consequences travel through its KPI deltas, not through the flag. Supersedes the undated 2026-09-01 taxonomy entry, which reached the same conclusion from a textual sweep that could not tell a mention from a mechanic. R2 option C's cost is the CFO gate and its KPI deltas.", 'R2 option C', '', ''),
    'circular_hubs': FlagSpec('circular_hubs', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'circular_minimum_compliance': FlagSpec('circular_minimum_compliance', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'circular_procurement_leader': FlagSpec('circular_procurement_leader', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'circular_procurement_partial': FlagSpec('circular_procurement_partial', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'circular_redesign': FlagSpec('circular_redesign', DEAD_DEFECT, ('default', 'other', 'pillar'), ('journey_improvements.py', 'pillar_configs.py', 'round_configs.py'), '', 'R7 option A', 'engine.py:2054 (SDG 12 +15) reads ctx.events, which is empty-initialised; systemic_risk_engine.py:74 (+5) is unreachable. Live only through pillar-mode mutual exclusivity.', 'engine.py:2054, :5055; pillar_configs.py:1546', revived_in='2026.10'),
    'circular_reskilled': FlagSpec('circular_reskilled', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'civil_water_priority': FlagSpec('civil_water_priority', UNVERIFIED, ('healthcare',), ('healthcare_configs.py',), '', '', '', ''),
    'climate_adaptation': FlagSpec('climate_adaptation', INERT_BY_DESIGN, ('default',), ('ending_pathways.py',), 'owner ruling 2026-09-01, class: history', '', '', ''),
    'climate_deny': FlagSpec('climate_deny', INERT_BY_DESIGN, ('default',), ('ending_pathways.py',), 'owner ruling 2026-09-01, class: history', '', '', ''),
    'clinician_retraining': FlagSpec('clinician_retraining', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'closed_loop': FlagSpec('closed_loop', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'closed_loop_water': FlagSpec('closed_loop_water', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'community_fund': FlagSpec('community_fund', LIVE, ('default', 'healthcare', 'pillar'), ('healthcare_configs.py', 'pillar_configs.py', 'round_configs.py'), '', 'R9 option C', 'Gates the just-transition scaling. Community Champion premium +0.18, rising to +0.27 at the ceiling.', 'terminal_valuation.py:240-247'),
    'community_fund_r2': FlagSpec('community_fund_r2', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'community_water': FlagSpec('community_water', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'compliance_gap': FlagSpec('compliance_gap', UNVERIFIED, ('healthcare',), ('healthcare_configs.py',), '', '', '', ''),
    'consent_decree': FlagSpec('consent_decree', UNVERIFIED, ('default',), ('ending_pathways.py',), '', '', '', ''),
    'consolidation': FlagSpec('consolidation', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'contest_ruling': FlagSpec('contest_ruling', INERT_BY_DESIGN, ('default',), ('ending_pathways.py',), 'owner ruling 2026-09-01, class: history', '', '', ''),
    'cooperatives': FlagSpec('cooperatives', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'corporate_hardball': FlagSpec('corporate_hardball', INERT_BY_DESIGN, ('default',), ('ending_pathways.py',), 'owner ruling 2026-09-01, class: history', '', '', ''),
    'cost_optimized': FlagSpec('cost_optimized', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'crisis_employee_support': FlagSpec('crisis_employee_support', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'crisis_passive_response': FlagSpec('crisis_passive_response', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'crisis_response_full': FlagSpec('crisis_response_full', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'crisis_response_targeted': FlagSpec('crisis_response_targeted', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'cross_trained': FlagSpec('cross_trained', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'csrd_aligned': FlagSpec('csrd_aligned', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'dc_optimized': FlagSpec('dc_optimized', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'deep_audit_completed': FlagSpec('deep_audit_completed', LIVE, ('default', 'healthcare', 'pillar'), ('healthcare_configs.py', 'pillar_configs.py', 'round_configs.py'), '', 'R1 option B', '+7 stakeholder attitude for regulator, NGO, community, buyer and consumer, through the sentiment rules. Its four other consumers — the fog-of-war exemption, supply-chain transparency +20, and the two side-track reads — are all unreachable.', 'stakeholder_sentiment.py:43 via engine.py:4784-4791 and router.py:2960'),
    'deep_hrdd_active': FlagSpec('deep_hrdd_active', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'deferred_audit': FlagSpec('deferred_audit', LIVE, ('default',), ('round_configs.py',), '', 'R1 option C', 'Multiplies the R4 crisis severity by 1.5: 40 becomes 60.', 'round_logic.py:234'),
    'dei_program': FlagSpec('dei_program', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'deny_and_deflect': FlagSpec('deny_and_deflect', LIVE, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R4 option C', '-15 stakeholder attitude through the sentiment rules. Its supply-chain transparency -15 and NPC betrayal-scar consumers are unreachable.', 'stakeholder_sentiment.py via engine.py:4784-4791'),
    'desalination_built': FlagSpec('desalination_built', DEAD_DEFECT, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R8 option C', 'round_logic.py:2575, the same pillar-mode negative guard.', 'round_configs.py:598; round_logic.py:2575'),
    'diesel_backup': FlagSpec('diesel_backup', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'digital_inclusion': FlagSpec('digital_inclusion', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'digital_triage_active': FlagSpec('digital_triage_active', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'digital_twin': FlagSpec('digital_twin', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'digital_twin_supply': FlagSpec('digital_twin_supply', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'divest': FlagSpec('divest', DEPRECATED, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), "DEPRECATED 2026-09-08 (remediation plan §4.2, confirmed by execution: tests/test_flag_reachability.py reports it dead under BOTH rule sets). Round 10's effects come from the option's impacts dict — spinoff_weakest_bu and synergy_wipe at round_logic.py:2763-2781 — never from the flag. Kept DECLARED rather than deleted: dropping it now would change what a replayed session's r10_flags contains even though no number moves. NB divest_all is NOT a flag and does not belong in this registry: it is an IMPACTS key (round_configs.py:787) carrying its own 2026-08-31 ruling and correctly allow-listed in tests/test_engine_invariants.py. The remediation plan §4.2 said it belonged here; checked 2026-09-08, it does not.", 'R10 option C', 'No consumer, in either rule set. impacts["synergy_wipe"] carries the ending.', 'round_configs.py:765; round_logic.py:2775-2781', removes_at='2026.10'),
    'divest_weakest': FlagSpec('divest_weakest', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'dpp_non_compliant': FlagSpec('dpp_non_compliant', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'dry_cooling': FlagSpec('dry_cooling', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'dual_sourcing_active': FlagSpec('dual_sourcing_active', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'early_decarboniser': FlagSpec('early_decarboniser', LIVE, ('default', 'healthcare', 'pillar'), ('healthcare_configs.py', 'pillar_configs.py', 'round_configs.py'), '', 'R3 option A', '+0.10 to the synergy multiplier at R7. With nature_based_resilience it earns the +0.20 Adaptation Premium, on the climate black swan pathway only.', 'round_logic.py:2508-2512; ending_pathways.py:566-569'),
    'efficiency_upgrades': FlagSpec('efficiency_upgrades', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'electronics_blindspot': FlagSpec('electronics_blindspot', LIVE, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R1 option A', 'Doubles the R4 crisis severity: base 40 becomes 80.', 'round_logic.py:227'),
    'electronics_water_priority': FlagSpec('electronics_water_priority', LIVE, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R8 option B', 'Its PRESENCE blocks the +0.20 Resilience Champion premium.', 'terminal_valuation.py:233-235'),
    'emergency_decarb': FlagSpec('emergency_decarb', INERT_BY_DESIGN, ('default',), ('ending_pathways.py',), 'owner ruling 2026-09-01, class: history', '', '', ''),
    'emergency_trained': FlagSpec('emergency_trained', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'employee_ownership': FlagSpec('employee_ownership', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'employee_wellbeing': FlagSpec('employee_wellbeing', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'endowment_created': FlagSpec('endowment_created', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'energy_cut': FlagSpec('energy_cut', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'engagement_survey': FlagSpec('engagement_survey', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'epr_program': FlagSpec('epr_program', DEAD_DEFECT, ('default', 'other', 'pillar'), ('journey_improvements.py', 'pillar_configs.py', 'round_configs.py'), '', 'R7 option B', 'systemic_risk_engine.py:75 (+3) unreachable, and it is absent from FLAG_OVERRIDES.', 'round_configs.py:506; systemic_risk_engine.py:75', revived_in='2026.10'),
    'erp_integration_sc': FlagSpec('erp_integration_sc', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_ai_ethics_board': FlagSpec('es_ai_ethics_board', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_ai_quiet_fix': FlagSpec('es_ai_quiet_fix', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_biodiversity_deferred': FlagSpec('es_biodiversity_deferred', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_cobalt_certified': FlagSpec('es_cobalt_certified', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_community_invested': FlagSpec('es_community_invested', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_green_claims_verified': FlagSpec('es_green_claims_verified', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_greenwash_defended': FlagSpec('es_greenwash_defended', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_just_transition_leader': FlagSpec('es_just_transition_leader', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_legal_firewall': FlagSpec('es_legal_firewall', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_lobby_active': FlagSpec('es_lobby_active', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_nature_positive': FlagSpec('es_nature_positive', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_partial_conservation': FlagSpec('es_partial_conservation', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_partial_correction': FlagSpec('es_partial_correction', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_phased_transition': FlagSpec('es_phased_transition', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_sbti_aligned': FlagSpec('es_sbti_aligned', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_supplier_terminated': FlagSpec('es_supplier_terminated', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_tnfd_disclosed': FlagSpec('es_tnfd_disclosed', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_transparency_leader': FlagSpec('es_transparency_leader', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_union_strike_risk': FlagSpec('es_union_strike_risk', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_whistleblower_risk': FlagSpec('es_whistleblower_risk', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'es_workers_abandoned': FlagSpec('es_workers_abandoned', INERT_BY_DESIGN, ('other',), ('side_tracks/ethics_sustainability/configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'esg_report': FlagSpec('esg_report', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'ethical_ai_overhaul': FlagSpec('ethical_ai_overhaul', LIVE, ('default', 'healthcare', 'pillar'), ('healthcare_configs.py', 'pillar_configs.py', 'round_configs.py'), '', 'R6 option B', '+0.15 M_R Truth Premium; black-swan probability -0.05. The SDG 16 +15 bonus it appears to earn is unreachable.', 'terminal_valuation.py:236; black_swan_registry.py:204'),
    'ethical_sourcing_restructured': FlagSpec('ethical_sourcing_restructured', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'ethical_sourcing_transitional': FlagSpec('ethical_sourcing_transitional', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'fleet_electrified': FlagSpec('fleet_electrified', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'fossil_dependent': FlagSpec('fossil_dependent', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'fossil_status_quo': FlagSpec('fossil_status_quo', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'full_materiality_alignment': FlagSpec('full_materiality_alignment', LIVE, ('default',), ('round_configs.py',), '', 'R2 option A', 'Scales natural-capital-debt forgiveness by 1.25, advanced_climate paradigm only. Flags are written post-tick, so it cannot fire in R2 itself; effective from R3.', 'engine.py:3787 (gate at :3757); ordering router.py:2906/3003/3126'),
    'full_remediation': FlagSpec('full_remediation', UNVERIFIED, ('default',), ('ending_pathways.py',), '', '', '', ''),
    'full_severance_redeployment': FlagSpec('full_severance_redeployment', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'full_tier_mapping': FlagSpec('full_tier_mapping', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'geographic_diversified': FlagSpec('geographic_diversified', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'governance_fragility': FlagSpec('governance_fragility', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'green_bond_active': FlagSpec('green_bond_active', DEPRECATED, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), 'DEPRECATED 2026-09-08 (remediation plan §4.2). No consumer in either rule set. The Green Bond is priced by the ROUND 2 materiality TIER flags (round_logic.py:2252-2279), so the flag named after the instrument does not price the instrument. Retirement is the DEFAULT disposition, not the only one: moving the pricing onto this flag would be better design and would make the Round 3 case teachable, but that is a behaviour change and belongs with the Phase 5 cut-over. removes_at is set so the decision is forced rather than deferred indefinitely.', 'R3 option B', 'No consumer. The instrument is priced by the R2 tier flags instead.', 'round_configs.py:242; round_logic.py:2252-2279', removes_at='2026.10'),
    'green_dc': FlagSpec('green_dc', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'green_pivot': FlagSpec('green_pivot', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'green_reskilling': FlagSpec('green_reskilling', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'green_skills_academy': FlagSpec('green_skills_academy', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'green_tariff': FlagSpec('green_tariff', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'greenwash_advocacy': FlagSpec('greenwash_advocacy', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'greenwash_risk': FlagSpec('greenwash_risk', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    # RECLASSIFIED 2026-09-08 by tests/test_flag_reachability.py. It was LIVE on
    # the strength of an effect the flag does not deliver: impact_engine.py:93
    # takes the R5 resilience factor from the chosen option's IMPACTS dict,
    # keyed by choice, and never reads this flag. The flag's one real consumer
    # is round_logic._revert_r5_hard_engineering_pulse (:3509-3534), and it
    # cannot fire — a fourth defect shape, wrong GENERATION of the container.
    'hard_engineering': FlagSpec('hard_engineering', DEAD_DEFECT, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R5 option A', "round_logic.py:3518 reads the POST-TICK flag bag, which engine._assemble_global_state set to this round's events plus the seven session keys _forward_persistent_flags carries; r5_flags is not among them, so the R7 reversal of the +3 carbon-intensity construction pulse never applies and the pulse is permanent. The history is in previous_flags, which post_tick also receives and every other flattened reader in the file uses.", 'round_configs.py:353; round_logic.py:3518-3524; engine.py:4472,4905; router.py:2370-2392', revived_in='2026.10'),
    'hardened_hospital_grid': FlagSpec('hardened_hospital_grid', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'heat_recovery': FlagSpec('heat_recovery', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'heavy_icu_capex': FlagSpec('heavy_icu_capex', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'hr_absent_transition': FlagSpec('hr_absent_transition', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'human_triage_override': FlagSpec('human_triage_override', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'hybrid_fleet': FlagSpec('hybrid_fleet', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'immediate_closure': FlagSpec('immediate_closure', DEAD_DEFECT, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R9 option A', 'impact_engine.py:294 sits inside an `if pillar_mode:` branch.', 'round_configs.py:648; impact_engine.py:294'),
    'incinerator_lobbying': FlagSpec('incinerator_lobbying', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'independent_investigation': FlagSpec('independent_investigation', INERT_BY_DESIGN, ('other',), ('journey_improvements.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'insurance_only': FlagSpec('insurance_only', LIVE, ('default', 'healthcare', 'pillar'), ('healthcare_configs.py', 'pillar_configs.py', 'round_configs.py'), '', 'R5 option C', 'Resilience factor 0.0. Its PRESENCE blocks the +0.20 Resilience Champion premium, which is a three-flag negative conjunction.', 'round_configs.py:393; terminal_valuation.py:233-235'),
    'inventory_buffer_only': FlagSpec('inventory_buffer_only', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'leadership_pipeline': FlagSpec('leadership_pipeline', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'lean_process': FlagSpec('lean_process', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'local_ecosystem': FlagSpec('local_ecosystem', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'local_sterile_resilience': FlagSpec('local_sterile_resilience', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'low_carbon_path': FlagSpec('low_carbon_path', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'managed_transition': FlagSpec('managed_transition', LIVE, ('default', 'healthcare', 'pillar'), ('healthcare_configs.py', 'pillar_configs.py', 'round_configs.py'), '', 'R9 option B', 'Gates the just-transition scaling. Just Transition premium +0.12, rising to +0.18 at the 1.5 ceiling.', 'terminal_valuation.py:240-247'),
    'manual_compliance_sc': FlagSpec('manual_compliance_sc', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'manual_oversight': FlagSpec('manual_oversight', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'material_passport': FlagSpec('material_passport', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'materiality_board_established': FlagSpec('materiality_board_established', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'materiality_exceptions': FlagSpec('materiality_exceptions', INERT_BY_DESIGN, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), "INERT_BY_DESIGN, ruling dated 2026-09-08 (remediation plan §4.3), and confirmed by execution rather than by a name sweep: tests/test_flag_reachability.py reports it dead under BOTH rule sets, never read by anything. A choice marker — the option's consequences travel through its KPI deltas, not through the flag. Supersedes the undated 2026-09-01 taxonomy entry, which reached the same conclusion from a textual sweep that could not tell a mention from a mechanic. R2 option B's cost is its budget clawback and reputation deltas.", 'R2 option B', '', ''),
    'materiality_framework_ignored': FlagSpec('materiality_framework_ignored', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'microgrids': FlagSpec('microgrids', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'modern_slavery_unresolved': FlagSpec('modern_slavery_unresolved', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'msme_champion': FlagSpec('msme_champion', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'nature_based_resilience': FlagSpec('nature_based_resilience', LIVE, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R5 option B', 'Resilience factor 0.60, two-round build. Half of the +0.20 Adaptation Premium pair.', 'round_configs.py:373; ending_pathways.py:566-569'),
    'nature_offsets': FlagSpec('nature_offsets', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'nearshored': FlagSpec('nearshored', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'nearshored_supply': FlagSpec('nearshored_supply', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'net_zero_energy': FlagSpec('net_zero_energy', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'ngo_partner': FlagSpec('ngo_partner', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'offshored': FlagSpec('offshored', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'ohs_basic': FlagSpec('ohs_basic', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'outsource_opacity': FlagSpec('outsource_opacity', UNVERIFIED, ('healthcare',), ('healthcare_configs.py',), '', '', '', ''),
    'parametric_insurance': FlagSpec('parametric_insurance', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'partial_retraining': FlagSpec('partial_retraining', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'partial_tier_mapping': FlagSpec('partial_tier_mapping', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'patient_evacuation': FlagSpec('patient_evacuation', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'people_analytics': FlagSpec('people_analytics', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'poison_pill': FlagSpec('poison_pill', UNVERIFIED, ('default',), ('ending_pathways.py',), '', '', '', ''),
    'policy_leadership': FlagSpec('policy_leadership', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'pr_containment': FlagSpec('pr_containment', INERT_BY_DESIGN, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), "INERT_BY_DESIGN, ruling dated 2026-09-08 (remediation plan §4.3), and confirmed by execution rather than by a name sweep: tests/test_flag_reachability.py reports it dead under BOTH rule sets, never read by anything. A choice marker — the option's consequences travel through its KPI deltas, not through the flag. Supersedes the undated 2026-09-01 taxonomy entry, which reached the same conclusion from a textual sweep that could not tell a mention from a mechanic. R4 option B's effect is entirely in its impacts.", 'R4 option B', '', ''),
    'quiet_patch': FlagSpec('quiet_patch', LIVE, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R6 option C', "-10 attitude for regulator, NGO, investor, media and journalist. The option's 'if leaked, devastating' threat has no implementing code anywhere.", 'stakeholder_sentiment.py:62, :174-187'),
    'quiet_patch_oncology': FlagSpec('quiet_patch_oncology', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'reckless_automation': FlagSpec('reckless_automation', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'regen_agriculture': FlagSpec('regen_agriculture', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'regenerative_supply': FlagSpec('regenerative_supply', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'regional_clinics_built': FlagSpec('regional_clinics_built', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'remediation_active': FlagSpec('remediation_active', DEAD_DEFECT, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R4 option A', 'systemic_risk_engine.py:73 (+8 supply-chain transparency) is unreachable for the same shape reason.', 'round_configs.py:298; systemic_risk_engine.py:73', revived_in='2026.10'),
    'remediation_fund_active': FlagSpec('remediation_fund_active', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'renewable_ppa_signed': FlagSpec('renewable_ppa_signed', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'resilient_network': FlagSpec('resilient_network', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'resist_integrate': FlagSpec('resist_integrate', DEPRECATED, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), "DEPRECATED 2026-09-08 (remediation plan §4.2, confirmed by execution: tests/test_flag_reachability.py reports it dead under BOTH rule sets). Round 10's effects come from the option's impacts dict — spinoff_weakest_bu and synergy_wipe at round_logic.py:2763-2781 — never from the flag. Kept DECLARED rather than deleted: dropping it now would change what a replayed session's r10_flags contains even though no number moves.", 'R10 option A', 'No consumer, in either rule set. The R10-A effects are impacts-driven.', 'round_configs.py:726; round_logic.py:2763-2781', removes_at='2026.10'),
    'responsible_ai_trained': FlagSpec('responsible_ai_trained', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'retention_bonuses': FlagSpec('retention_bonuses', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'reverse_logistics': FlagSpec('reverse_logistics', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'sbti_committed': FlagSpec('sbti_committed', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'sbti_risk': FlagSpec('sbti_risk', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sc_cobalt_clean': FlagSpec('sc_cobalt_clean', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sc_deep_visibility': FlagSpec('sc_deep_visibility', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sc_greenwash_risk': FlagSpec('sc_greenwash_risk', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sc_monitoring_only': FlagSpec('sc_monitoring_only', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sc_resilient': FlagSpec('sc_resilient', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'scope3_deep_cut': FlagSpec('scope3_deep_cut', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'scope3_offset_only': FlagSpec('scope3_offset_only', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'scope_3_transparency': FlagSpec('scope_3_transparency', LIVE, ('default',), ('round_logic.py:2357',), '', 'engine-written, not declared in any flags_set', 'Half of an OR condition earning +0.20 M_R on the regulatory shutdown pathway.', 'round_logic.py:2357 writes; ending_pathways.py:754-757 reads'),
    'sdg_12_leadership': FlagSpec('sdg_12_leadership', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'selective_appeasement': FlagSpec('selective_appeasement', INERT_BY_DESIGN, ('default',), ('ending_pathways.py',), 'owner ruling 2026-09-01, class: history', '', '', ''),
    'self_assessment_only': FlagSpec('self_assessment_only', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'shareholder_only': FlagSpec('shareholder_only', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'shift_optimized': FlagSpec('shift_optimized', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'sm_cba_signed': FlagSpec('sm_cba_signed', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_community_overridden': FlagSpec('sm_community_overridden', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_community_partnership': FlagSpec('sm_community_partnership', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_crisis_leader': FlagSpec('sm_crisis_leader', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_defensive_crisis': FlagSpec('sm_defensive_crisis', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_dynamic_salience': FlagSpec('sm_dynamic_salience', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_engagement_policy': FlagSpec('sm_engagement_policy', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_esg_gold_standard': FlagSpec('sm_esg_gold_standard', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_gap_closure': FlagSpec('sm_gap_closure', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_investor_focus': FlagSpec('sm_investor_focus', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_issb_aligned': FlagSpec('sm_issb_aligned', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_legal_escalation': FlagSpec('sm_legal_escalation', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_media_hostile': FlagSpec('sm_media_hostile', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_rating_challenge': FlagSpec('sm_rating_challenge', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_reactive_approach': FlagSpec('sm_reactive_approach', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_structured_response': FlagSpec('sm_structured_response', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_transparency_champion': FlagSpec('sm_transparency_champion', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sm_voluntary_commitments': FlagSpec('sm_voluntary_commitments', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'solar_investment': FlagSpec('solar_investment', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'spinoff': FlagSpec('spinoff', DEPRECATED, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), "DEPRECATED 2026-09-08 (remediation plan §4.2, confirmed by execution: tests/test_flag_reachability.py reports it dead under BOTH rule sets). Round 10's effects come from the option's impacts dict — spinoff_weakest_bu and synergy_wipe at round_logic.py:2763-2781 — never from the flag. Kept DECLARED rather than deleted: dropping it now would change what a replayed session's r10_flags contains even though no number moves.", 'R10 option B', 'No consumer, in either rule set. impacts["spinoff_weakest_bu"] zeroes the weakest BU.', 'round_configs.py:746; round_logic.py:2763-2771', removes_at='2026.10'),
    'sr_activist_opposition': FlagSpec('sr_activist_opposition', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_ar_integrated': FlagSpec('sr_ar_integrated', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_climate_adequate': FlagSpec('sr_climate_adequate', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_climate_gap': FlagSpec('sr_climate_gap', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_climate_leader': FlagSpec('sr_climate_leader', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_credibility_gap': FlagSpec('sr_credibility_gap', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sr_data_infrastructure': FlagSpec('sr_data_infrastructure', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sr_esg_controls': FlagSpec('sr_esg_controls', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_full_esrs': FlagSpec('sr_full_esrs', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_integrated_leader': FlagSpec('sr_integrated_leader', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_limited_assurance': FlagSpec('sr_limited_assurance', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_living_wage': FlagSpec('sr_living_wage', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_minimum_compliance': FlagSpec('sr_minimum_compliance', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sr_no_external_assurance': FlagSpec('sr_no_external_assurance', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'sr_phased_compliance': FlagSpec('sr_phased_compliance', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_reasonable_assurance': FlagSpec('sr_reasonable_assurance', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_sbti_targets': FlagSpec('sr_sbti_targets', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_scope3_complete': FlagSpec('sr_scope3_complete', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_sfdr_compliant': FlagSpec('sr_sfdr_compliant', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_siloed_reporting': FlagSpec('sr_siloed_reporting', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_social_gap': FlagSpec('sr_social_gap', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_social_leader': FlagSpec('sr_social_leader', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'sr_value_demonstrated': FlagSpec('sr_value_demonstrated', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'stakeholder_compact': FlagSpec('stakeholder_compact', INERT_BY_DESIGN, ('default',), ('ending_pathways.py',), 'owner ruling 2026-09-01, class: history', '', '', ''),
    'stakeholder_compensated': FlagSpec('stakeholder_compensated', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'stakeholder_covenant': FlagSpec('stakeholder_covenant', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'statutory_minimum_hr': FlagSpec('statutory_minimum_hr', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'supplier_capacity_building': FlagSpec('supplier_capacity_building', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'supplier_remediation': FlagSpec('supplier_remediation', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'supplier_switching': FlagSpec('supplier_switching', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'supply_chain_disruption_risk': FlagSpec('supply_chain_disruption_risk', DEAD_DEFECT, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R3 option A', 'systemic_risk_engine.py:71 tests it as a top-level key; it is written into the r3_flags LIST. The -10 supply-chain transparency never applies. Independently confirmed by fault injection in tests/test_option_matrix_golden.py.', 'round_configs.py:222 writes; systemic_risk_engine.py:71 reads', revived_in='2026.10'),
    'supply_chain_fragile': FlagSpec('supply_chain_fragile', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'supply_concentration_risk': FlagSpec('supply_concentration_risk', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'supply_disruption_risk': FlagSpec('supply_disruption_risk', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'supply_diversified': FlagSpec('supply_diversified', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'supply_ignored': FlagSpec('supply_ignored', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'supply_water_audit': FlagSpec('supply_water_audit', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'synergy_unlock': FlagSpec('synergy_unlock', LIVE, ('default', 'healthcare', 'other', 'pillar'), ('healthcare_configs.py', 'journey_improvements.py', 'pillar_configs.py', 'round_configs.py'), '', 'R7 option C', 'Up to +0.15 M_R, gated on the synergy multiplier reaching 0.80, ramped by +/-0.05.', 'terminal_valuation.py:209-224; round_logic.py:2714'),
    'take_back_active': FlagSpec('take_back_active', INERT_BY_DESIGN, ('other',), ('configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'targeted_fix': FlagSpec('targeted_fix', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'tech_scholarships': FlagSpec('tech_scholarships', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'telehealth_litigation': FlagSpec('telehealth_litigation', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'telehealth_overhaul': FlagSpec('telehealth_overhaul', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'tier2_human_rights_risk': FlagSpec('tier2_human_rights_risk', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
    'transition_bonds': FlagSpec('transition_bonds', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'turnaround_restructuring': FlagSpec('turnaround_restructuring', INERT_BY_DESIGN, ('default',), ('round_configs.py',), "INERT_BY_DESIGN, ruling dated 2026-09-08 (remediation plan §4.3), and confirmed by execution rather than by a name sweep: tests/test_flag_reachability.py reports it dead under BOTH rule sets, never read by anything. A choice marker — the option's consequences travel through its KPI deltas, not through the flag. Supersedes the undated 2026-09-01 taxonomy entry, which reached the same conclusion from a textual sweep that could not tell a mention from a mechanic. Option T's effects — the divestiture, the -15% OPEX haircut, +10 reputation and the -20% synergy — are all in its impacts. AND A CORRECTION, 2026-09-08: the option's own description (round_configs.py:894) says it 'Sets turnaround_restructuring flag, enabling Phase 2 transition'. It enables nothing. turnaround_engine keys the phase machine off turnaround_phase, a STRING state it writes itself (:135, :177, :182-183, :284), and has never read this flag. Either the description is wrong or the wiring is missing; recorded here as the former, which is what the code says.", 'Option T (survival mode)', '', ''),
    'union_busted': FlagSpec('union_busted', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'universal_care_charter': FlagSpec('universal_care_charter', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'vendor_replacement': FlagSpec('vendor_replacement', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'voluntary_offsets': FlagSpec('voluntary_offsets', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'waste_compliance_gap': FlagSpec('waste_compliance_gap', UNVERIFIED, ('healthcare',), ('healthcare_configs.py',), '', '', '', ''),
    'waste_reduction': FlagSpec('waste_reduction', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'waste_to_energy': FlagSpec('waste_to_energy', DEAD_DEFECT, ('default', 'other', 'pillar'), ('journey_improvements.py', 'pillar_configs.py', 'round_configs.py'), '', 'R7 option C', 'Pillar-mode mutual exclusivity only; no consumer on the default path.', 'pillar_configs.py:1546, :1680'),
    'water_efficiency_all': FlagSpec('water_efficiency_all', DEAD_DEFECT, ('default', 'pillar'), ('pillar_configs.py', 'round_configs.py'), '', 'R8 option A', 'round_logic.py:2574 reads only the pillar-mode flag set, and only as a negative guard.', 'round_configs.py:557; round_logic.py:2574'),
    'water_efficient_supply': FlagSpec('water_efficient_supply', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'water_recycling': FlagSpec('water_recycling', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'water_stewards_trained': FlagSpec('water_stewards_trained', UNVERIFIED, ('pillar',), ('pillar_configs.py',), '', '', '', ''),
    'water_trucking': FlagSpec('water_trucking', INERT_BY_DESIGN, ('healthcare',), ('healthcare_configs.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'watershed_restored': FlagSpec('watershed_restored', INERT_BY_DESIGN, ('pillar',), ('pillar_configs.py',), 'owner ruling 2026-09-01, class: choice-marker', '', '', ''),
    'whistleblower_accountability': FlagSpec('whistleblower_accountability', INERT_BY_DESIGN, ('other',), ('journey_improvements.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'whistleblower_suppressed': FlagSpec('whistleblower_suppressed', INERT_BY_DESIGN, ('other',), ('journey_improvements.py',), 'owner ruling 2026-09-01, class: narrative', '', '', ''),
    'white_knight_defence': FlagSpec('white_knight_defence', INERT_BY_DESIGN, ('default',), ('ending_pathways.py',), 'owner ruling 2026-09-01, class: history', '', '', ''),
    'working_capital_hoarder': FlagSpec('working_capital_hoarder', UNVERIFIED, ('other',), ('configs.py',), '', '', '', ''),
}


def get(name: str) -> FlagSpec | None:
    return REGISTRY.get(name)


def by_status(status: str) -> list[FlagSpec]:
    return [s for s in REGISTRY.values() if s.status == status]


def live() -> list[FlagSpec]:
    return by_status(LIVE)


def dead() -> list[FlagSpec]:
    return by_status(DEAD_DEFECT)


def inert() -> list[FlagSpec]:
    return by_status(INERT_BY_DESIGN)


def unverified() -> list[FlagSpec]:
    return by_status(UNVERIFIED)


def deprecated() -> list[FlagSpec]:
    return by_status(DEPRECATED)


def revived_in(version: str) -> list[FlagSpec]:
    """Flags whose defect is fixed in this rules version. Phase 5's cut-over
    filter: these are the entries whose status becomes LIVE when
    rules.CURRENT_VERSION moves."""
    return [s for s in REGISTRY.values() if s.revived_in == version]
