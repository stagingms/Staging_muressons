"""Quick test for all 7 CEO Interview improvements."""
import asyncio
import json

async def main():
    from ceo_interview import (
        score_responses_with_llm, calc_trajectory_modifiers,
        generate_evidence_citations, calc_calibration_gaps,
        store_peer_scores, calc_peer_benchmarks,
        generate_adaptive_questions, BASE_QUESTIONS, DIMENSIONS,
        calc_data_scores, blend_scores, generate_score_rationale,
    )

    print("=" * 60)
    print("  CEO DEBRIEF MODULE — FULL TEST RUN")
    print("=" * 60)

    # ── Mock simulation data ──
    gs = {
        "corporate_treasury": 48000000, "group_reputation": 72,
        "synergy_multiplier": 1.15, "cost_of_capital": 0.08,
        "active_event_flags": {
            "regenerative_multiple": 1.25, "terminal_value": 45000000,
            "profile_title": "Balanced Leader", "ending_pathway": "activist_ultimatum",
        },
    }
    bus = [
        {"bu_id": 1, "revenue_base": 20000000, "opex_base": 14000000,
         "social_license_score": 72, "carbon_intensity": 35, "governance_risk_score": 18,
         "staff_burnout_index": 30, "reputation_score": 68, "natural_capital_debt": 5000},
        {"bu_id": 2, "revenue_base": 15000000, "opex_base": 10000000,
         "social_license_score": 65, "carbon_intensity": 50, "governance_risk_score": 25,
         "staff_burnout_index": 45, "reputation_score": 60, "natural_capital_debt": 8000},
    ]
    flags = gs["active_event_flags"]
    extra = {
        "regenerative_multiple": 1.25,
        "terminal_value": 45000000,
        "profile_title": "Balanced Leader",
    }

    # ── Test 1: Data Scoring ──
    print("\n[1/7] DATA SCORING")
    data_scores = calc_data_scores(extra, gs, bus, flags)
    for k, v in data_scores.items():
        print(f"  {k}: {v:.1f}")

    # ── Test 2: Trajectory Modifiers ──
    print("\n[2/7] TRAJECTORY ANALYSIS")
    fake_history = []
    for rn in range(1, 11):
        fake_history.append({
            "round_number": rn,
            "global_state": {
                "corporate_treasury": 40000000 + rn * 800000,
                "synergy_multiplier": 1.0 + rn * 0.015,
                "active_event_flags": {"regenerative_multiple": 1.0 + rn * 0.025},
            },
            "business_units": [
                {"social_license_score": 60 + rn * 1.2},
                {"social_license_score": 55 + rn * 1.0},
            ],
        })
    fake_decisions = [
        {"round_number": 3, "choice_selected": "option_b", "capex_allocated": 5000000},
        {"round_number": 5, "choice_selected": "option_a", "capex_allocated": 8000000},
        {"round_number": 7, "choice_selected": "option_c", "capex_allocated": 3000000, "previous_choice": "option_a"},
    ]
    trajectory = calc_trajectory_modifiers(fake_history, fake_decisions)
    for dim_id, traj in trajectory.items():
        sign = "+" if traj["modifier"] >= 1 else ""
        print(f"  {dim_id}: {sign}{((traj['modifier'] - 1) * 100):.0f}% — {traj['narrative'][:80]}")

    # ── Test 3: Evidence Citations ──
    print("\n[3/7] EVIDENCE CITATIONS")
    citations = generate_evidence_citations(fake_decisions, fake_history, data_scores)
    for dim_id, cites in citations.items():
        if cites:
            for c in cites:
                print(f"  [{dim_id}] {c[:90]}")

    # ── Test 4: Peer Benchmarking ──
    print("\n[4/7] PEER BENCHMARKING")
    cohort_id = "test-cohort"
    store_peer_scores(cohort_id, {"strategic_thinking": 5.0, "stakeholder_empathy": 7.0, "financial_acumen": 6.0, "ethical_reasoning": 4.0, "systems_thinking": 6.5, "adaptive_leadership": 5.5})
    store_peer_scores(cohort_id, {"strategic_thinking": 7.5, "stakeholder_empathy": 6.0, "financial_acumen": 8.0, "ethical_reasoning": 7.0, "systems_thinking": 5.0, "adaptive_leadership": 7.0})
    store_peer_scores(cohort_id, data_scores)
    benchmarks = calc_peer_benchmarks(cohort_id, data_scores)
    for dim_id, b in benchmarks.items():
        print(f"  {dim_id}: P{b['percentile']} (cohort avg {b['cohort_avg']}, n={b['cohort_size']})")

    # ── Test 5: Self-Assessment Calibration ──
    print("\n[5/7] SELF-ASSESSMENT CALIBRATION")
    self_ratings = {"strategic_thinking": 8, "stakeholder_empathy": 6, "financial_acumen": 7, "ethical_reasoning": 5, "systems_thinking": 8, "adaptive_leadership": 7}
    final_scores = blend_scores(data_scores, data_scores)  # simplified for test
    calibration = calc_calibration_gaps(self_ratings, final_scores)
    for dim_id, cal in calibration.items():
        print(f"  {dim_id}: Self={cal['self']:.0f} Actual={cal['actual']:.1f} Gap={cal['gap']:+.1f} ({cal['label']})")

    # ── Test 6: Adaptive Questions ──
    print("\n[6/7] ADAPTIVE QUESTIONS")
    questions = generate_adaptive_questions(data_scores)
    for i, q in enumerate(questions):
        adaptive = " [ADAPTIVE]" if q.get("is_adaptive") else ""
        target = f" [targets: {q.get('target_dimension', '')}]" if q.get("target_dimension") else ""
        print(f"  Q{i+1}{adaptive}{target}: {q['text'][:80]}...")

    import config
    print(f"\n[7/7] LLM SCORING ({config.LLM_MODEL})")
    responses = [
        "I focused on building long-term stakeholder trust by investing in community programmes early in the simulation.",
        "My capital allocation strategy balanced R&D investment with maintaining treasury reserves for market shocks.",
    ]
    result = await score_responses_with_llm(questions[:2], responses, data_scores, extra)
    if result:
        print("  ✅ LLM call SUCCEEDED!")
        if "dimension_scores" in result:
            for k, v in result["dimension_scores"].items():
                print(f"    {k}: {v}")
        if "key_strengths" in result:
            for s in result.get("key_strengths", []):
                print(f"    💪 {s}")
        if "growth_areas" in result:
            for g in result.get("growth_areas", []):
                print(f"    📈 {g}")
    else:
        print("  ❌ LLM call returned None — check API key or model name")

    print("\n" + "=" * 60)
    print("  TEST RUN COMPLETE")
    print("=" * 60)

asyncio.run(main())
