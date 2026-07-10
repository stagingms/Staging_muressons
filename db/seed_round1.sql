-- ============================================================
-- Muressons Global Command – Round 1 Seed Insert
-- Run AFTER init.sql has created the schema.
-- ============================================================

BEGIN;

-- ----- 1. Create the demo session -----
INSERT INTO sessions (session_id, cohort_name, facilitator_id, start_time)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Default Cohort',
    'system',
    now()
);

-- ----- 2. Global round state for Round 1 -----
INSERT INTO global_round_states (
    state_id, session_id, round_number,
    corporate_treasury, group_reputation,
    synergy_multiplier, cost_of_capital,
    active_event_flags
) VALUES (
    '10000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    1,
    50000000.00,
    50.00,
    1.0000,
    0.0500,
    '{}'::jsonb
);

-- ----- 3. Business Unit round states -----

-- Pharma  (highest revenue)
INSERT INTO bu_round_states (
    global_state_id, bu_id,
    revenue_base, opex_base,
    natural_capital_debt, social_license_score,
    reputation_score, governance_risk_score,
    water_dependency, carbon_intensity,
    risk_factors
) VALUES (
    '10000000-0000-0000-0000-000000000001',
    'pharma',
    18000000.00, 11500000.00,
    0, 55.00,
    52.00, 15.00,
    82.00, 45.00,
    '{
        "regulatory_compliance": "high",
        "patent_cliff_exposure": "medium",
        "supply_chain_fragility": "medium",
        "community_health_impact": "high",
        "water_scarcity_risk": "high",
        "biodiversity_dependency": "medium"
    }'::jsonb
);

-- Electronics  (second-highest revenue)
INSERT INTO bu_round_states (
    global_state_id, bu_id,
    revenue_base, opex_base,
    natural_capital_debt, social_license_score,
    reputation_score, governance_risk_score,
    water_dependency, carbon_intensity,
    risk_factors
) VALUES (
    '10000000-0000-0000-0000-000000000001',
    'electronics',
    16500000.00, 10800000.00,
    0, 48.00,
    50.00, 20.00,
    58.00, 72.00,
    '{
        "regulatory_compliance": "medium",
        "rare_earth_dependency": "high",
        "e_waste_liability": "high",
        "supply_chain_fragility": "high",
        "labour_rights_exposure": "high",
        "carbon_transition_risk": "medium"
    }'::jsonb
);

-- Consumer Goods
INSERT INTO bu_round_states (
    global_state_id, bu_id,
    revenue_base, opex_base,
    natural_capital_debt, social_license_score,
    reputation_score, governance_risk_score,
    water_dependency, carbon_intensity,
    risk_factors
) VALUES (
    '10000000-0000-0000-0000-000000000001',
    'consumer_goods',
    10500000.00, 7800000.00,
    0, 52.00,
    53.00, 10.00,
    65.00, 38.00,
    '{
        "regulatory_compliance": "medium",
        "brand_boycott_risk": "high",
        "packaging_waste": "high",
        "palm_oil_dependency": "medium",
        "deforestation_exposure": "medium",
        "consumer_sentiment_volatility": "high"
    }'::jsonb
);

-- Software
INSERT INTO bu_round_states (
    global_state_id, bu_id,
    revenue_base, opex_base,
    natural_capital_debt, social_license_score,
    reputation_score, governance_risk_score,
    water_dependency, carbon_intensity,
    risk_factors
) VALUES (
    '10000000-0000-0000-0000-000000000001',
    'software',
    8500000.00, 4200000.00,
    0, 60.00,
    58.00, 8.00,
    12.00, 28.00,
    '{
        "regulatory_compliance": "low",
        "data_privacy_risk": "high",
        "ai_ethics_exposure": "medium",
        "talent_retention": "high",
        "data_centre_energy": "medium",
        "digital_divide_impact": "low"
    }'::jsonb
);

COMMIT;
