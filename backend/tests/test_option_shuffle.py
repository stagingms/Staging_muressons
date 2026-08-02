"""
Tests for the Option Shuffle Engine (anti-gaming measure).
Validates that:
  1. Shuffle is deterministic (same seed + round → same result)
  2. Shuffle produces valid permutations (no duplicates, no missing)
  3. Deshuffle correctly reverses the shuffle
  4. Different seeds produce different orderings
  5. Different rounds with the same seed produce different orderings
  6. Non-standard option keys (e.g. option_t) pass through unchanged
"""

import pytest
from option_shuffle import (
    generate_shuffle_seed,
    get_shuffle_mapping,
    shuffle_options_for_display,
    deshuffle_choice,
    strip_canonical_metadata,
    _CANONICAL_KEYS,
)


class TestShuffleSeedGeneration:
    def test_seed_is_integer(self):
        seed = generate_shuffle_seed()
        assert isinstance(seed, int)

    def test_seed_in_valid_range(self):
        for _ in range(100):
            seed = generate_shuffle_seed()
            assert 100_000 <= seed <= 999_999

    def test_different_seeds_generated(self):
        """Multiple seeds should not all be identical."""
        seeds = {generate_shuffle_seed() for _ in range(50)}
        assert len(seeds) > 1, "All generated seeds are identical"


class TestShuffleDeterminism:
    def test_same_seed_same_round_same_result(self):
        """Identical seed + round must always produce the same permutation."""
        seed = 123456
        m1 = get_shuffle_mapping(seed, 5)
        m2 = get_shuffle_mapping(seed, 5)
        assert m1 == m2

    def test_different_rounds_different_result(self):
        """Same seed but different rounds should (usually) differ."""
        seed = 654321
        results = set()
        for rn in range(1, 11):
            perm = tuple(get_shuffle_mapping(seed, rn)["permutation"])
            results.add(perm)
        # With 10 rounds and 6 possible permutations, we should see at least 2 different ones
        assert len(results) >= 2, "All rounds produced identical orderings"

    def test_different_seeds_different_result(self):
        """Different seeds on the same round should (usually) differ."""
        results = set()
        for seed in [100000, 200000, 300000, 400000, 500000, 600000]:
            perm = tuple(get_shuffle_mapping(seed, 3)["permutation"])
            results.add(perm)
        assert len(results) >= 2, "All seeds produced identical orderings"


class TestShuffleMapping:
    def test_permutation_is_valid(self):
        """Permutation must contain exactly the 3 canonical keys, no duplicates."""
        seed = 111222
        for rn in range(1, 11):
            m = get_shuffle_mapping(seed, rn)
            perm = m["permutation"]
            assert sorted(perm) == sorted(_CANONICAL_KEYS)

    def test_display_to_canonical_is_bijection(self):
        """display_to_canonical must be a bijection (one-to-one mapping)."""
        seed = 333444
        m = get_shuffle_mapping(seed, 7)
        d2c = m["display_to_canonical"]
        c2d = m["canonical_to_display"]
        # Both must have 3 entries
        assert len(d2c) == 3
        assert len(c2d) == 3
        # Values must be unique (bijection)
        assert len(set(d2c.values())) == 3
        assert len(set(c2d.values())) == 3

    def test_mappings_are_inverse(self):
        """display→canonical and canonical→display must be inverse of each other."""
        seed = 555666
        m = get_shuffle_mapping(seed, 4)
        d2c = m["display_to_canonical"]
        c2d = m["canonical_to_display"]
        for display_key, canonical_key in d2c.items():
            assert c2d[canonical_key] == display_key


class TestShuffleOptionsForDisplay:
    MOCK_OPTIONS = {
        "option_a": {"label": "A", "title": "Alpha", "impacts": {"treasury": -5}},
        "option_b": {"label": "B", "title": "Beta", "impacts": {"treasury": -3}},
        "option_c": {"label": "C", "title": "Gamma", "impacts": {"treasury": -1}},
    }

    def test_shuffled_keys_are_canonical(self):
        """Output should always have option_a, option_b, option_c keys."""
        result = shuffle_options_for_display(self.MOCK_OPTIONS, 123456, 1)
        assert set(k for k in result if k.startswith("option_")) == set(_CANONICAL_KEYS)

    def test_labels_match_display_position(self):
        """After shuffling, labels must match display position (A for option_a, etc.)."""
        result = shuffle_options_for_display(self.MOCK_OPTIONS, 789012, 3)
        assert result["option_a"]["label"] == "A"
        assert result["option_b"]["label"] == "B"
        assert result["option_c"]["label"] == "C"

    def test_titles_are_permuted(self):
        """Titles should come from different canonical options depending on shuffle."""
        seed = 345678
        result = shuffle_options_for_display(self.MOCK_OPTIONS, seed, 6)
        displayed_titles = {result[k]["title"] for k in _CANONICAL_KEYS}
        original_titles = {"Alpha", "Beta", "Gamma"}
        # All original titles must still be present (just potentially reordered)
        assert displayed_titles == original_titles

    def test_none_seed_returns_unchanged(self):
        """If shuffle_seed is None, return options unchanged."""
        result = shuffle_options_for_display(self.MOCK_OPTIONS, None, 1)
        assert result == self.MOCK_OPTIONS

    def test_empty_options_returns_unchanged(self):
        """Empty options dict should pass through unchanged."""
        result = shuffle_options_for_display({}, 123456, 1)
        assert result == {}

    def test_canonical_metadata_is_set(self):
        """Each shuffled option should have _canonical_key metadata."""
        result = shuffle_options_for_display(self.MOCK_OPTIONS, 123456, 2)
        for key in _CANONICAL_KEYS:
            assert "_canonical_key" in result[key]
            assert result[key]["_canonical_key"] in _CANONICAL_KEYS

    def test_nonstandard_keys_pass_through(self):
        """Non-standard keys like option_t should be preserved unchanged."""
        opts = {
            **self.MOCK_OPTIONS,
            "option_t": {"label": "T", "title": "Turnaround"},
        }
        result = shuffle_options_for_display(opts, 123456, 5)
        assert "option_t" in result
        assert result["option_t"]["title"] == "Turnaround"


class TestDeshuffleChoice:
    def test_round_trip(self):
        """shuffle → display_key → deshuffle should recover the canonical key."""
        seed = 654321
        for rn in range(1, 11):
            mapping = get_shuffle_mapping(seed, rn)
            for display_key, canonical_key in mapping["display_to_canonical"].items():
                # Player sees display_key, picks it, backend deshuffles
                recovered = deshuffle_choice(display_key, seed, rn)
                assert recovered == canonical_key, (
                    f"Round {rn}: deshuffle({display_key}) = {recovered}, "
                    f"expected {canonical_key}"
                )

    def test_all_canonical_keys_reachable(self):
        """Every canonical key must be reachable via deshuffle from some display key."""
        seed = 999888
        for rn in range(1, 11):
            deshuffled = {deshuffle_choice(dk, seed, rn) for dk in _CANONICAL_KEYS}
            assert deshuffled == set(_CANONICAL_KEYS)

    def test_none_seed_passthrough(self):
        """None seed should return the choice unchanged."""
        assert deshuffle_choice("option_b", None, 1) == "option_b"

    def test_empty_choice_passthrough(self):
        """Empty string choice should pass through."""
        assert deshuffle_choice("", 123456, 1) == ""

    def test_nonstandard_key_passthrough(self):
        """Non-standard keys like option_t should pass through unchanged."""
        assert deshuffle_choice("option_t", 123456, 1) == "option_t"


class TestStripCanonicalMetadata:
    def test_removes_underscore_keys(self):
        """_canonical_key and other underscore-prefixed keys should be removed."""
        options = {
            "option_a": {"label": "A", "title": "Test", "_canonical_key": "option_c"},
            "option_b": {"label": "B", "title": "Test2", "_internal": True},
        }
        result = strip_canonical_metadata(options)
        assert "_canonical_key" not in result["option_a"]
        assert "_internal" not in result["option_b"]
        # Non-underscore keys preserved
        assert result["option_a"]["label"] == "A"
        assert result["option_b"]["title"] == "Test2"


class TestEndToEndAntiGaming:
    """
    Integration test: simulates the full API flow.
    1. Options are shuffled for display
    2. Player picks a display key
    3. Backend deshuffles back to canonical
    4. Verify the canonical key matches the original data
    """

    OPTIONS = {
        "option_a": {"label": "A", "title": "Transparency", "flags_set": ["remediation"]},
        "option_b": {"label": "B", "title": "Damage Control", "flags_set": ["pr_containment"]},
        "option_c": {"label": "C", "title": "Deny", "flags_set": ["deny_deflect"]},
    }

    def test_player_always_gets_correct_canonical_outcome(self):
        """
        For every round, no matter what the shuffle is, if a player
        selects the option with title "Transparency" (which is canonical option_a),
        the backend should resolve it to canonical "option_a".
        """
        seed = 777888
        for rn in range(1, 11):
            # Step 1: Backend shuffles options for display
            shuffled = shuffle_options_for_display(self.OPTIONS, seed, rn)
            cleaned = strip_canonical_metadata(shuffled)

            # Step 2: Player finds "Transparency" and picks its display key
            player_pick = None
            for display_key, opt_data in cleaned.items():
                if opt_data["title"] == "Transparency":
                    player_pick = display_key
                    break
            assert player_pick is not None, f"Round {rn}: Transparency not found in shuffled options"

            # Step 3: Backend deshuffles the player's pick
            canonical = deshuffle_choice(player_pick, seed, rn)

            # Step 4: Verify it maps to the REAL option_a (Transparency)
            assert canonical == "option_a", (
                f"Round {rn}: Player picked '{player_pick}' (Transparency), "
                f"but deshuffle returned '{canonical}' instead of 'option_a'"
            )
