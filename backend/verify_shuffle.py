"""Quick verification script for the option shuffle round-trip."""
from option_shuffle import get_shuffle_mapping, deshuffle_choice
import database_memory as db

# Get the session's shuffle seed
sess = db._sessions.get('6c7079c7-f132-499c-b841-601313b7dc80')
seed = sess['shuffle_seed']
print(f"Session shuffle_seed: {seed}")
print()

# For Round 1, verify the deshuffle
m = get_shuffle_mapping(seed, 1)
print("Round 1 mapping:")
for dk, ck in m['display_to_canonical'].items():
    print(f"  Display {dk} -> Canonical {ck}")

# Simulate: player picks 'option_a' (which displays 'Deep Forensic Audit')
# Backend should deshuffle to the canonical key for 'Deep Forensic Audit' = option_b
player_pick = 'option_a'
canonical = deshuffle_choice(player_pick, seed, 1)
print()
print("Player picks display option_a (Deep Forensic Audit)")
print(f"Deshuffle -> canonical {canonical}")
expected = m['display_to_canonical']['option_a']
print(f"Expected: {expected}")
match = canonical == expected
print(f"PASS: {match}")

# Test all 10 rounds
print()
print("=== Full 10-round round-trip test ===")
all_pass = True
for rn in range(1, 11):
    mapping = get_shuffle_mapping(seed, rn)
    for display_key in ['option_a', 'option_b', 'option_c']:
        result = deshuffle_choice(display_key, seed, rn)
        expected_canonical = mapping['display_to_canonical'][display_key]
        ok = result == expected_canonical
        if not ok:
            print(f"FAIL R{rn}: deshuffle({display_key}) = {result}, expected {expected_canonical}")
            all_pass = False

if all_pass:
    print("ALL 30 round-trip tests PASSED (10 rounds x 3 options)")
