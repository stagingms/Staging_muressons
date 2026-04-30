"""Test C7 salience migration logic."""
from stakeholder_map import apply_salience_migrations, MASTER_MAP

# Simulate: R4 with electronics_blindspot active
gs = {"active_event_flags": {"electronics_blindspot": True}}

m4 = apply_salience_migrations(4, gs)
print(f"R4 migrations: {len(m4)}")
for m in m4:
    print(f"  {m['stakeholder_name']}: {m['from_quadrant']} -> {m['to_quadrant']}")

m6 = apply_salience_migrations(6, gs)
print(f"\nR6 migrations: {len(m6)}")
for m in m6:
    print(f"  {m['stakeholder_name']}: {m['from_quadrant']} -> {m['to_quadrant']}")

m9 = apply_salience_migrations(9, gs)
print(f"\nR9 migrations: {len(m9)}")
for m in m9:
    print(f"  {m['stakeholder_name']}: {m['from_quadrant']} -> {m['to_quadrant']}")

current = gs["stakeholder_salience_current"]
mc = sum(1 for v in current.values() if v == "manage_closely")
print(f"\nFinal salience map: {mc}/10 in Manage Closely")
print(f"Migration history: {len(gs['salience_migration_history'])} total events")

# Verify idempotency — running R4 again should not produce new migrations
m4_again = apply_salience_migrations(4, gs)
assert len(m4_again) == 0, "Idempotency failed"
print("\n[OK] Idempotency check passed")

# Without electronics_blindspot, R6 syndicate_banks should NOT migrate
gs2 = {"active_event_flags": {}}
apply_salience_migrations(4, gs2)
m6_no_blindspot = apply_salience_migrations(6, gs2)
bank_migrated = any(m["stakeholder_id"] == "syndicate_banks" for m in m6_no_blindspot)
assert not bank_migrated, "Banks should not migrate without blindspot"
print("[OK] Conditional migration check passed")

print("\n[OK] ALL C7 MIGRATION TESTS PASSED")
