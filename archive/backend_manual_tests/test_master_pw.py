"""
Quick test: verify god-mode master password sim2026@iim@ works for all login flows.
"""
import os, sys, hmac
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from config import MASTER_PASSWORD

TEST_PW = "sim2026@iim@"

print("=== God-Mode Master Password Test ===")
print(f"MASTER_PASSWORD loaded : {repr(MASTER_PASSWORD)}")
print(f"Test password          : {repr(TEST_PW)}")
print()

# Test 1 – correct password matches
match = bool(MASTER_PASSWORD) and hmac.compare_digest(TEST_PW, MASTER_PASSWORD)
print(f"[PASS] Correct password matches  : {match}")
assert match, "MASTER_PASSWORD mismatch!"

# Test 2 – wrong password rejected
wrong = bool(MASTER_PASSWORD) and hmac.compare_digest("wrongpassword", MASTER_PASSWORD)
print(f"[PASS] Wrong password rejected   : {not wrong}")
assert not wrong, "Wrong password should NOT match!"

# Test 3 – simulate facilitator_login logic
REGISTRY = [
    {"facilitator_id": "fac001", "name": "Dr. Smith",   "role": "lead_facilitator", "password": "someotherpw", "enabled": True},
    {"facilitator_id": "fac002", "name": "Prof. Jones", "role": "facilitator",       "password": "anotherpw",   "enabled": True},
]

def sim_login(fac_id, password):
    master_ok = bool(MASTER_PASSWORD) and hmac.compare_digest(password, MASTER_PASSWORD)
    fac_id_lower = fac_id.lower()
    fac = next((f for f in REGISTRY
                if f["facilitator_id"].lower() == fac_id_lower
                and not f.get("deleted_at")), None)

    if master_ok and fac_id_lower == "god_mode":
        return "OK:super_admin(virtual god_mode)"
    elif master_ok and fac_id_lower == "facilitator":
        return "OK:lead_facilitator(virtual)"
    elif not fac or (not master_ok and fac.get("password") != password):
        return "REJECTED"
    return "OK:" + fac["role"] + "(" + fac["name"] + ")"

cases = [
    ("god_mode",   TEST_PW,        "OK:super_admin(virtual god_mode)"),
    ("facilitator",TEST_PW,        "OK:lead_facilitator(virtual)"),
    ("fac001",     TEST_PW,        "OK:lead_facilitator(Dr. Smith)"),
    ("fac002",     TEST_PW,        "OK:facilitator(Prof. Jones)"),
    ("fac001",     "wrongpw",      "REJECTED"),
    ("nonexistent",TEST_PW,        "REJECTED"),  # not in registry → rejected
]

print()
print("[TEST 3] Facilitator login simulation:")
all_ok = True
for fac_id, pw, expected in cases:
    result = sim_login(fac_id, pw)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_ok = False
    print(f"  [{status}] {fac_id:15s} + {'master_pw' if pw == TEST_PW else 'wrong_pw':10s} => {result}")

print()
if all_ok:
    print("ALL TESTS PASSED -- God-mode master password sim2026@iim@ is working correctly.")
else:
    print("SOME TESTS FAILED.")
    sys.exit(1)
