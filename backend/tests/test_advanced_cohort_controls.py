"""HIGH-tier advanced cohort controls — config model, validation & RNG seeding.

Covers the four setup data-points added to the cohort settings layer:
  - RNG seed (GAME-4 determinism),
  - result-visibility (reveal schedule + peer redaction),
  - quiz enable + grading,
  - team/roster provisioning.

Pins: (1) every control is a real, overridable, effective cohort setting with a
default; (2) the normaliser coerces/clamps hostile input; (3) a shared RNG seed
makes named event streams reproducible and identical across teams.
"""

import admin_shared
from admin_shared import (
    _god_mode_settings,
    COHORT_OVERRIDABLE_KEYS,
    cohort_settings,
    get_effective_settings,
    normalize_advanced_cohort_settings as normalize,
    resolve_roster_cap,
)
from rng_util import event_rng, event_seed

_ADVANCED_KEYS = [
    "rng_seed", "results_reveal_round", "redact_peer_identities",
    "quiz_enabled", "quiz_graded", "quiz_pass_threshold", "quiz_max_attempts",
    "team_count", "max_team_size", "join_method", "join_code",
]


# ── Config model ─────────────────────────────────────────────────────────────

def test_every_control_has_a_default_and_is_overridable():
    for k in _ADVANCED_KEYS:
        assert k in _god_mode_settings, f"missing default: {k}"
        assert k in COHORT_OVERRIDABLE_KEYS, f"not per-cohort overridable: {k}"


def test_defaults_are_off_by_default():
    assert _god_mode_settings["rng_seed"] == ""
    assert _god_mode_settings["results_reveal_round"] == 0
    assert _god_mode_settings["redact_peer_identities"] is False
    assert _god_mode_settings["quiz_enabled"] is False
    assert _god_mode_settings["join_method"] == "code"


# ── Validation / normalisation ───────────────────────────────────────────────

def test_numeric_controls_are_clamped():
    assert normalize({"results_reveal_round": 99})["results_reveal_round"] == 10
    assert normalize({"results_reveal_round": -3})["results_reveal_round"] == 0
    assert normalize({"quiz_pass_threshold": 150})["quiz_pass_threshold"] == 100
    assert normalize({"quiz_pass_threshold": -1})["quiz_pass_threshold"] == 0
    assert normalize({"quiz_max_attempts": 0})["quiz_max_attempts"] == 1
    assert normalize({"team_count": 10_000})["team_count"] == 500
    assert normalize({"max_team_size": -5})["max_team_size"] == 0


def test_bad_types_coerce_safely():
    assert normalize({"quiz_pass_threshold": "abc"})["quiz_pass_threshold"] == 70
    assert normalize({"redact_peer_identities": "yes"})["redact_peer_identities"] is True
    assert normalize({"redact_peer_identities": 0})["redact_peer_identities"] is False
    assert normalize({"join_method": "sneaky"})["join_method"] == "code"
    assert normalize({"join_method": "open"})["join_method"] == "open"


def test_seed_and_code_are_trimmed_and_bounded():
    assert normalize({"rng_seed": "  spring-2026  "})["rng_seed"] == "spring-2026"
    assert len(normalize({"rng_seed": "x" * 200})["rng_seed"]) == 64
    assert normalize({"join_code": "  ABCD  "})["join_code"] == "ABCD"


def test_unknown_keys_pass_through_untouched():
    out = normalize({"some_other_key": 42, "quiz_enabled": 1})
    assert out["some_other_key"] == 42
    assert out["quiz_enabled"] is True


# ── Effective settings merge ─────────────────────────────────────────────────

def test_controls_flow_through_effective_settings():
    sid = "cohort-adv-test"
    cohort_settings[sid] = {
        "rng_seed": "spring-2026",
        "results_reveal_round": 10,
        "quiz_enabled": True,
        "team_count": 6,
    }
    try:
        eff = get_effective_settings(sid)
        assert eff["rng_seed"] == "spring-2026"
        assert eff["results_reveal_round"] == 10
        assert eff["quiz_enabled"] is True
        assert eff["team_count"] == 6
        # Untouched control keeps the global default.
        assert eff["redact_peer_identities"] is False
    finally:
        cohort_settings.pop(sid, None)


# ── RNG determinism (the point of the seed) ──────────────────────────────────

def test_same_seed_reproduces_named_event_rolls():
    flags = {"stochastic_seed": "spring-2026"}
    r1 = [event_rng(flags, 3, "blackswan:ransomware").random() for _ in range(1)]
    r2 = [event_rng(flags, 3, "blackswan:ransomware").random() for _ in range(1)]
    assert r1 == r2, "same seed must reproduce the same roll"


def test_different_seeds_diverge_and_events_are_independent():
    a = event_seed({"stochastic_seed": "seed-A"}, 3, "blackswan:ransomware")
    b = event_seed({"stochastic_seed": "seed-B"}, 3, "blackswan:ransomware")
    assert a != b
    # Different event names off the same seed are independent streams.
    s1 = event_seed({"stochastic_seed": "seed-A"}, 3, "event:one")
    s2 = event_seed({"stochastic_seed": "seed-A"}, 3, "event:two")
    assert s1 != s2


def test_no_seed_is_non_deterministic_fallback():
    # No stochastic_seed ⇒ event_seed is None (system-seeded Random downstream).
    assert event_seed({}, 1, "any") is None


# ── Roster cap (enforced at join) ────────────────────────────────────────────

def test_roster_cap_defaults_to_five_when_unset():
    sid = "cohort-roster-default"
    cohort_settings.pop(sid, None)
    assert resolve_roster_cap(sid) == 5


def test_roster_cap_honours_configured_team_count():
    sid = "cohort-roster-set"
    cohort_settings[sid] = {"team_count": 3}
    try:
        assert resolve_roster_cap(sid) == 3
    finally:
        cohort_settings.pop(sid, None)


def test_roster_cap_zero_falls_back_to_default():
    sid = "cohort-roster-zero"
    cohort_settings[sid] = {"team_count": 0}
    try:
        assert resolve_roster_cap(sid) == 5
        assert resolve_roster_cap(sid, default=12) == 12
    finally:
        cohort_settings.pop(sid, None)


# ── Quiz policy (attempts / pass threshold / graded) ─────────────────────────

def test_quiz_policy_defaults_match_legacy_engine():
    # Attempts default to 2 so the existing notebook-quiz behaviour is unchanged.
    assert _god_mode_settings["quiz_max_attempts"] == 2
    assert _god_mode_settings["quiz_pass_threshold"] == 70


def test_quiz_policy_is_per_cohort_overridable():
    sid = "cohort-quiz-policy"
    cohort_settings[sid] = {"quiz_max_attempts": 3, "quiz_pass_threshold": 80, "quiz_graded": True}
    try:
        eff = get_effective_settings(sid)
        assert eff["quiz_max_attempts"] == 3
        assert eff["quiz_pass_threshold"] == 80
        assert eff["quiz_graded"] is True
    finally:
        cohort_settings.pop(sid, None)
