"""
Muressons — BRSR NGRBC Track Implementation (10 rounds)
"""

from __future__ import annotations
from typing import Any
from side_tracks.base_track import BaseSideTrack
from side_tracks.brsr_ngrbc.configs import BRSR_ROUND_CONFIGS
from side_tracks.bridge_schemas import DataBridgeInput, DataBridgeOutput


class BRSRNGRBCTrack(BaseSideTrack):
    """10-round BRSR NGRBC side simulation."""

    @property
    def track_id(self) -> str: return "brsr_ngrbc"
    @property
    def display_name(self) -> str: return "BRSR: NGRBC Deep Dive"
    @property
    def description(self) -> str:
        return "A 10-round deep dive into the SEBI BRSR framework, covering all nine NGRBC principles, Essential vs Leadership indicators, and BRSR Core assurance."
    @property
    def icon(self) -> str: return "🇮🇳"
    @property
    def num_rounds(self) -> int: return 10
    @property
    def available_window(self) -> tuple[int, int]: return (2, 8)

    @property
    def scoring_dimensions(self) -> list[dict[str, str]]:
        return [
            {"id": "governance_ethics", "label": "Governance & Ethics (P1/P7)", "unit": "/100"},
            {"id": "human_capital", "label": "Human Capital (P3/P5)", "unit": "/100"},
            {"id": "environmental", "label": "Environmental Stewardship (P6/P2)", "unit": "/100"},
            {"id": "value_chain", "label": "Value Chain & Stakeholder (P4/P8/P9)", "unit": "/100"},
            {"id": "reporting_quality", "label": "Integrated Disclosure", "unit": "/100"},
        ]

    @property
    def cross_track_prerequisites(self) -> list[str]:
        return ["sustainability_reporting", "ethics_sustainability"]

    def get_round_configs(self) -> dict[int, dict[str, Any]]:
        return BRSR_ROUND_CONFIGS

    def seed_from_main_state(
        self,
        main_global: dict,
        main_bus: list[dict],
        completed_tracks: dict[str, dict] = None,
    ) -> DataBridgeInput:
        completed_tracks = completed_tracks or {}
        flags = main_global.get("active_event_flags", {})
        reporting_data = completed_tracks.get("sustainability_reporting", {})
        ethics_done    = "ethics_sustainability" in completed_tracks
        kpis = self._build_bridge_kpis(main_bus, main_global)
        return DataBridgeInput(
            treasury=main_global.get("corporate_treasury", 50_000_000),
            reputation=main_global.get("group_reputation", 50.0),
            active_flags=dict(flags),
            kpis=kpis,
            extra_state={
                # Track-specific initial scoring metrics
                "governance_ethics":  10 + (10 if ethics_done else 0),
                "human_capital":      10,
                "environmental":      10,
                "value_chain":         5,
                "reporting_quality":   5 + (15 if reporting_data.get("regulatory_readiness", 0) > 60 else 0),
                # Context for post_tick hooks
                "inherited_governance_risk": round(kpis.avg_governance_risk, 2),
                "accumulated_flags":         [],
            },
        )

    def write_back_to_main(
        self,
        track_state: dict,
        main_global: dict,
    ) -> DataBridgeOutput:
        score = self.calculate_score(track_state)
        flags: dict = {
            "brsr_track_completed":     True,
            "brsr_performance_score":   score["total_score"],
            "brsr_grade":               score["grade"],
            "brsr_archetype":           score["archetype"]["title"],
        }
        if score["total_score"] >= 80:
            flags["brsr_net_positive_dividend"] = 0.05
        accumulated = set(track_state.get("accumulated_flags", []))
        if "governance_fragility" in accumulated:
            flags["brsr_truth_premium_cost_doubled"] = True
        for f in ["brsr_pioneer", "brsr_core_assured", "brsr_living_wage",
                  "sdg_12_leadership", "brsr_greenwash_risk",
                  "deep_hrdd_active", "policy_leadership", "msme_champion",
                  "csrd_aligned"]:
            if f in accumulated:
                flags[f] = True
        return DataBridgeOutput(flags_to_set=flags)

    def calculate_score(self, track_state: dict) -> dict[str, Any]:
        ge = min(100, max(0, track_state.get("governance_ethics", 0)))
        hc = min(100, max(0, track_state.get("human_capital", 0)))
        en = min(100, max(0, track_state.get("environmental", 0)))
        vc = min(100, max(0, track_state.get("value_chain", 0)))
        rq = min(100, max(0, track_state.get("reporting_quality", 0)))

        total = round(ge * 0.20 + hc * 0.20 + en * 0.25 + vc * 0.20 + rq * 0.15, 1)

        if total >= 85: grade = "A+"
        elif total >= 75: grade = "A"
        elif total >= 65: grade = "B"
        elif total >= 50: grade = "C"
        elif total >= 35: grade = "D"
        else: grade = "F"

        if total >= 80:
            archetype = {"title": "BRSR Pioneer", "description": "Exemplary implementation of NGRBC Leadership Indicators and rigorous BRSR Core value chain assurance.", "icon": "🏆", "gradient": "linear-gradient(135deg, #10b981, #059669)"}
        elif total >= 60:
            archetype = {"title": "Responsible Steward", "description": "Meets Essential Indicators reliably and adopts strategic Leadership practices in material areas.", "icon": "🌿", "gradient": "linear-gradient(135deg, #3b82f6, #2563eb)"}
        elif total >= 40:
            archetype = {"title": "Compliance Pragmatist", "description": "Fulfills mandatory SEBI BRSR requirements but exposes value chain to unchecked ESG risks.", "icon": "📋", "gradient": "linear-gradient(135deg, #f59e0b, #d97706)"}
        else:
            archetype = {"title": "Regulatory Laggard", "description": "Fails basic Essential indicators. High risk of regulatory action and ESG rating downgrades.", "icon": "⚠️", "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)"}

        return {"total_score": total, "dimensions": {"governance_ethics": ge, "human_capital": hc, "environmental": en, "value_chain": vc, "reporting_quality": rq}, "grade": grade, "archetype": archetype}

    def pre_tick(self, round_number: int, track_state: dict, bus: list[dict], decisions: list[dict], crisis_severity: float) -> dict[str, Any]:
        result = {"crisis_severity": crisis_severity, "pre_events": {}}
        accumulated = set(track_state.get("accumulated_flags", []))

        if round_number == 5:
            if "governance_fragility" in accumulated:
                result["pre_events"]["fragility_penalty"] = True
                result["crisis_severity"] = min(100, crisis_severity + 15)
            if "brsr_core_assured" in accumulated:
                result["pre_events"]["assurance_bonus"] = True
                result["crisis_severity"] = max(10, crisis_severity - 10)

        # Round 9: BRSR Core statutory mandate — unfixed value chain incurs correction expense
        if round_number == 9:
            if "brsr_greenwash_risk" in accumulated and "brsr_core_assured" not in accumulated:
                result["pre_events"]["brsr_core_correction_penalty"] = True
                result["crisis_severity"] = min(100, crisis_severity + 20)
            if "deep_hrdd_active" in accumulated:
                result["pre_events"]["hrdd_assurance_bonus"] = True
                result["crisis_severity"] = max(10, crisis_severity - 8)

        # Round 10: Final filing — governance fragility final reckoning
        if round_number == 10:
            if "governance_fragility" in accumulated and "policy_leadership" not in accumulated:
                result["pre_events"]["governance_final_reckoning"] = True
                result["crisis_severity"] = min(100, crisis_severity + 10)
            if "msme_champion" in accumulated:
                result["pre_events"]["msme_goodwill_bonus"] = True
                result["crisis_severity"] = max(10, crisis_severity - 5)
        return result

    def post_tick(self, round_number: int, global_state: dict, bu_states: list[dict], decisions: list[dict], events: dict, extra_events: dict, previous_flags: dict) -> dict[str, Any]:
        extra = self._apply_default_option_impacts(round_number, global_state, bu_states, decisions, events, extra_events)
        
        choice = self._get_primary_choice(decisions)
        opts = self.get_round_options(round_number)
        opt = opts.get(choice, {})
        flags_set = opt.get("flags_set") or []   # VUL-008 guard: explicit null yields None
        
        # Track metric state updates based on choices
        accumulated = list(previous_flags.get("accumulated_flags", []))
        for f in flags_set:
            if f not in accumulated:
                accumulated.append(f)
        
        extra[f"st_{self.track_id}_accumulated_flags"] = accumulated

        # VUL-007 FIX: Emit absolute target scores, preserving the maximum.
        # Multiple rounds may map to the same dimension (e.g., R1 + R7 → governance_ethics).
        # We emit max(current, target) so early Leadership investments are never overwritten
        # by weaker later-round choices on the same dimension.
        # Seed values: governance_ethics=10-20, human_capital=10, environmental=10,
        #              value_chain=5, reporting_quality=5-20 (all set in extra_state).
        # Target scores per choice: A=90, B=50, C=0.
        _SCORE_MAP = {"option_a": 90, "option_b": 50, "option_c": 0}
        _DIMENSION_MAP = {
            1: "governance_ethics",
            2: "human_capital",
            3: "environmental",
            4: "value_chain",
            5: "reporting_quality",
            6: "human_capital",        # P5 Human Rights
            7: "governance_ethics",    # P7 Policy Advocacy
            8: "value_chain",          # P8 MSME/Vendor
            9: "value_chain",          # P4/P9 Value Chain Assurance
            10: "reporting_quality",   # Integrated Double Materiality
        }
        if round_number in _DIMENSION_MAP:
            dim = _DIMENSION_MAP[round_number]
            target = _SCORE_MAP.get(choice, 0)
            # Read current dimension value from the BRSR track state (correct key)
            current = previous_flags.get("_brsr_track_state", {}).get(dim, 0)
            # Preserve the higher score: early Leadership should never regress
            new_value = max(current, target)
            extra[f"st_{self.track_id}_custom_{dim}"] = new_value

        # Special side effects directly modifying global state
        if round_number == 2 and choice == "option_a":
            # Reduce burnout across BUs
            for bu in bu_states:
                bu["staff_burnout_index"] = max(0, bu.get("staff_burnout_index", 0) - 12)
                
        if round_number == 3 and choice == "option_a":
            # VUL-008 FIX: cap at 1.35 (engine design ceiling), not 2.0
            global_state["synergy_multiplier"] = min(1.35, global_state.get("synergy_multiplier", 1.0) + 0.30)
            extra["brsr_synergy_boost"] = True

        # Dynamic BRSR Crisis Events injected into the engine loop
        if round_number == 4 and "brsr_greenwash_risk" in accumulated:
            extra["brsr_greenwash_crisis"] = (
                '<div style="font-family: Arial, sans-serif; border-top: 8px solid #1a365d; border-bottom: 8px solid #1a365d; '
                'padding: 25px; background-color: white; color: #333; max-width: 600px; margin: 0 auto;">'
                '<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; '
                'padding-bottom: 15px; margin-bottom: 20px;">'
                '<div><h2 style="margin: 0; color: #1a365d; font-size: 22px;">SEBI</h2>'
                '<p style="margin: 2px 0 0; font-size: 12px; color: #666;">Securities and Exchange Board of India</p></div>'
                '<div style="text-align: right; font-size: 12px; color: #666;">'
                '<p style="margin: 0;">Division of Corporate Finance</p>'
                '<p style="margin: 0;">Ref: SEBI/CFD/CMD/ESG/2026/089</p></div></div>'
                '<h3 style="margin-top: 0; font-size: 16px;">ATTENTION: CHIEF FINANCIAL OFFICER &amp; BOARD OF DIRECTORS</h3>'
                '<p style="font-size: 14px; line-height: 1.6; text-align: justify;">'
                'This communication serves as an official notice of regulatory discrepancy. A preliminary algorithmic review '
                'of your submitted Business Responsibility and Sustainability Report (BRSR) indicates material inconsistencies.</p>'
                '<p style="font-size: 14px; line-height: 1.6; text-align: justify; font-weight: bold; color: #b71c1c;">'
                'Specifically, your reliance on self-assessment for Tier-1 supply chain human rights due diligence contradicts '
                'the &quot;Reasonable Assurance&quot; mandate established for the top 250 market-cap entities under the BRSR Core framework.</p>'
                '<p style="font-size: 14px; line-height: 1.6; text-align: justify;">'
                'You are required to submit an audited rectification file within 15 working days. Failure to comply will result '
                'in an immediate downgrade of ESG indices listing eligibility and a formal public notification of greenwashing '
                'risk to institutional stakeholders.</p>'
                '<div style="border-top: 1px solid #eee; padding-top: 12px; margin-top: 20px; text-align: right; font-size: 11px; color: #999;">'
                'This is an auto-generated regulatory communication. Do not reply.</div></div>'
            )
            extra["brsr_greenwash_crisis_is_html"] = True
            current_rep = global_state.get("group_reputation", 50)
            if current_rep is not None:  # VUL-009 pattern: None guard
                global_state["group_reputation"] = max(10, current_rep - 12)

        if round_number == 5 and "governance_fragility" in accumulated:
            extra["brsr_governance_crisis"] = (
                '<div style="font-family: \'Helvetica Neue\', Helvetica, Arial, sans-serif; background-color: #e5ddd5; padding: 20px; '
                'max-width: 400px; margin: 0 auto; border-radius: 8px; border: 1px solid #ccc;">'
                '<div style="background-color: #075e54; color: white; padding: 10px; border-radius: 6px 6px 0 0; '
                'font-weight: bold; text-align: center;">Forwarded Message Alert</div>'
                '<div style="background-color: white; padding: 12px; border-radius: 8px; margin-top: 10px; '
                'position: relative; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">'
                '<p style="margin: 0 0 8px 0; font-size: 14px; color: #303030; line-height: 1.4;">'
                'Did you see the board minutes? They are completely suppressing the Delhi lobbying numbers. '
                'The promoter group just vetoed the transparency audit again.</p>'
                '<p style="margin: 0; font-size: 14px; color: #303030; line-height: 1.4;">'
                'I\'m taking this to the Mint reporter. We can\'t file this BRSR report legally.</p>'
                '<span style="font-size: 10px; color: #999; display: block; text-align: right; margin-top: 5px;">14:32 PM ✔✔</span></div>'
                '<div style="text-align: center; margin-top: 15px;">'
                '<span style="background-color: #d32f2f; color: white; padding: 4px 8px; border-radius: 4px; '
                'font-size: 12px; font-weight: bold;">⚠️ ATTACHED BY: CHENNAI BUSINESS DESK</span></div></div>'
            )
            extra["brsr_governance_crisis_is_html"] = True
            global_state["corporate_treasury"] = max(0, global_state.get("corporate_treasury", 0) - 2_500_000)

        # Round 3+5: SPCB Show-Cause Notice — fires at R5 if regulatory minimum was chosen at R3
        if round_number == 5 and "brsr_regulatory_minimum" in accumulated:
            extra["spcb_show_cause"] = (
                '<div style="font-family: \'Times New Roman\', serif; border: 2px solid #000; padding: 20px; '
                'background-color: #fdfbf7; color: #333; max-width: 600px; margin: 0 auto; '
                'box-shadow: 2px 2px 8px rgba(0,0,0,0.1);">'
                '<div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px;">'
                '<h2 style="margin: 0; font-size: 18px; text-transform: uppercase;">State Pollution Control Board (SPCB)</h2>'
                '<p style="margin: 5px 0 0; font-size: 14px; font-weight: bold;">Government of Telangana</p>'
                '<p style="margin: 2px 0 0; font-size: 12px;">Notice Reference: SPCB/HYD/ENF-2026/044</p></div>'
                '<h3 style="text-align: center; color: #d32f2f; text-decoration: underline; margin-bottom: 20px;">'
                'SHOW CAUSE NOTICE FOR CLOSURE</h3>'
                '<p style="font-size: 14px; line-height: 1.6;"><strong>To:</strong> The Managing Director, '
                'Muressons (Pharma BU), Hyderabad API Facility.</p>'
                '<p style="font-size: 14px; line-height: 1.6; text-align: justify;">'
                '<strong>Sub:</strong> Notice under Section 33(A) of the Water (Prevention and Control of Pollution) Act, 1974.</p>'
                '<p style="font-size: 14px; line-height: 1.6; text-align: justify;">'
                'Whereas, it has been observed during the unannounced inspection conducted on 28th May that your facility '
                'is discharging untreated synthetic effluents into the municipal drainage network, bypassing the mandated '
                'Zero Liquid Discharge (ZLD) protocols.</p>'
                '<p style="font-size: 14px; line-height: 1.6; text-align: justify; font-weight: bold; '
                'background-color: #ffebee; padding: 5px;">'
                'You are hereby directed to show cause within 48 hours as to why immediate closure orders should not be '
                'issued and basic amenities (power and water supply) disconnected.</p>'
                '<div style="margin-top: 30px; text-align: right;">'
                '<p style="margin: 0; font-style: italic; font-size: 12px; color: #666;">[Illegible Signature]</p>'
                '<p style="margin: 0; font-size: 14px;"><strong>Regional Officer, Enforcement Wing</strong></p>'
                '<p style="margin: 0; font-size: 12px; color: #666;">Telangana State Pollution Control Board</p></div></div>'
            )
            extra["spcb_show_cause_is_html"] = True

        # Round 6: Tier-2 human rights exposure — downstream cost if unaddressed
        if round_number == 6 and "tier2_human_rights_risk" in accumulated:
            extra["brsr_tier2_hr_crisis"] = "International buyers suspend contracts citing unresolved child labor allegations in your Tier-2 supply chain."
            current_rep = global_state.get("group_reputation", 50)
            if current_rep is not None:
                global_state["group_reputation"] = max(10, current_rep - 8)

        # Round 8: MSME payment crisis compound — working capital hoarding triggers SEBI penalty
        if round_number == 8 and "working_capital_hoarder" in accumulated:
            extra["brsr_msme_penalty"] = "SEBI imposes penalty for systematic MSME payment delays exceeding 45-day statutory limits."
            global_state["corporate_treasury"] = max(0, global_state.get("corporate_treasury", 0) - 1_500_000)

        # Round 9: Value chain assurance correction expense
        if round_number == 9 and "brsr_greenwash_risk" in accumulated and "brsr_core_assured" not in accumulated:
            extra["brsr_core_correction_crisis"] = "BRSR Core statutory mandate enforcement: extreme correction expense imposed for unverified value chain claims."
            global_state["corporate_treasury"] = max(0, global_state.get("corporate_treasury", 0) - 4_000_000)

        # Round 10: Terminal governance reckoning
        if round_number == 10 and "governance_fragility" in accumulated and "policy_leadership" not in accumulated:
            extra["brsr_governance_terminal_crisis"] = "Institutional investors downgrade ESG rating citing persistent governance weaknesses across the BRSR filing period."
            current_rep = global_state.get("group_reputation", 50)
            if current_rep is not None:
                global_state["group_reputation"] = max(10, current_rep - 6)

        return extra
