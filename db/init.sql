-- ============================================================
-- Muressons Global Command – Database Initialization Script
-- Immutable audit-trail design: past rounds are INSERT-only.
-- ============================================================

BEGIN;

-- =========================  EXTENSIONS  =========================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";    -- gen_random_uuid() fallback

-- =========================  ENUM TYPES  =========================
CREATE TYPE consensus_level AS ENUM (
    'unanimous',
    'majority',
    'split',
    'facilitator_override'
);

-- ============================================================
-- 1. SESSIONS
-- One row per simulation run (cohort playthrough).
-- ============================================================
CREATE TABLE sessions (
    session_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cohort_name         VARCHAR(120)    NOT NULL,
    facilitator_id      VARCHAR(80)     NOT NULL,
    start_time          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    end_time            TIMESTAMPTZ,
    final_terminal_value            NUMERIC(18,2),
    final_regenerative_multiple     NUMERIC(8,4),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_cohort   ON sessions (cohort_name);
CREATE INDEX idx_sessions_start    ON sessions (start_time);

-- ============================================================
-- 2. GLOBAL ROUND STATES
-- Snapshot of the global game state at each round.
-- ============================================================
CREATE TABLE global_round_states (
    state_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id          UUID            NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    round_number        SMALLINT        NOT NULL CHECK (round_number BETWEEN 1 AND 10),
    corporate_treasury  NUMERIC(18,2)   NOT NULL,
    group_reputation    NUMERIC(6,2)    NOT NULL,
    synergy_multiplier  NUMERIC(6,4)    NOT NULL DEFAULT 1.0,
    cost_of_capital     NUMERIC(6,4)    NOT NULL DEFAULT 0.05,
    active_event_flags  JSONB           NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uq_session_round UNIQUE (session_id, round_number)
);

CREATE INDEX idx_grs_session       ON global_round_states (session_id);
CREATE INDEX idx_grs_round         ON global_round_states (round_number);
CREATE INDEX idx_grs_events_gin    ON global_round_states USING GIN (active_event_flags);

-- ============================================================
-- 3. BUSINESS UNIT (BU) ROUND STATES
-- Per-BU snapshot linked to the global round state.
-- ============================================================
CREATE TABLE bu_round_states (
    bu_state_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    global_state_id         UUID            NOT NULL REFERENCES global_round_states(state_id) ON DELETE CASCADE,
    bu_id                   VARCHAR(40)     NOT NULL,      -- e.g. 'pharma', 'electronics'
    revenue_base            NUMERIC(18,2)   NOT NULL,
    opex_base               NUMERIC(18,2)   NOT NULL,
    natural_capital_debt    NUMERIC(12,2)   NOT NULL DEFAULT 0,
    social_license_score    NUMERIC(6,2)    NOT NULL DEFAULT 50,
    reputation_score        NUMERIC(6,2)    NOT NULL DEFAULT 50,
    governance_risk_score   NUMERIC(6,2)    NOT NULL DEFAULT 0,

    -- Extended ESG / operational attributes (JSONB for flexibility)
    water_dependency        NUMERIC(6,2)    DEFAULT 0,
    carbon_intensity        NUMERIC(6,2)    DEFAULT 0,
    risk_factors            JSONB           NOT NULL DEFAULT '{}',

    created_at              TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uq_bu_per_round UNIQUE (global_state_id, bu_id)
);

CREATE INDEX idx_bu_global_state   ON bu_round_states (global_state_id);
CREATE INDEX idx_bu_bu_id          ON bu_round_states (bu_id);

-- ============================================================
-- 4. DECISION AUDIT LOG
-- Every player/team decision is recorded here, append-only.
-- ============================================================
CREATE TABLE decision_audit_log (
    log_id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id              UUID            NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    round_number            SMALLINT        NOT NULL CHECK (round_number BETWEEN 1 AND 10),
    bu_id                   VARCHAR(40),                 -- NULL = global-level decision
    decision_node_id        VARCHAR(120)    NOT NULL,    -- e.g. 'pharma_water_invest'
    choice_selected         VARCHAR(200)    NOT NULL,
    capex_allocated         NUMERIC(18,2)   DEFAULT 0,
    time_to_decision_seconds INTEGER        DEFAULT 0,
    team_consensus          consensus_level NOT NULL DEFAULT 'majority',
    metadata                JSONB           DEFAULT '{}',
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE INDEX idx_dal_session       ON decision_audit_log (session_id);
CREATE INDEX idx_dal_round         ON decision_audit_log (round_number);
CREATE INDEX idx_dal_node          ON decision_audit_log (decision_node_id);

-- ============================================================
-- IMMUTABILITY GUARD
-- Prevent UPDATE / DELETE on round-state & audit tables.
-- Only INSERTs are permitted for historical data.
-- ============================================================

-- Helper function: raises an exception on UPDATE/DELETE
CREATE OR REPLACE FUNCTION fn_immutable_guard()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION
        'Immutability violation: % on table "%" is not allowed. '
        'Historical round data is append-only.',
        TG_OP, TG_TABLE_NAME;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply to global_round_states
CREATE TRIGGER trg_immutable_global_round_states
    BEFORE UPDATE OR DELETE ON global_round_states
    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();

-- Apply to bu_round_states
CREATE TRIGGER trg_immutable_bu_round_states
    BEFORE UPDATE OR DELETE ON bu_round_states
    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();

-- Apply to decision_audit_log
CREATE TRIGGER trg_immutable_decision_audit_log
    BEFORE UPDATE OR DELETE ON decision_audit_log
    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();

COMMIT;
