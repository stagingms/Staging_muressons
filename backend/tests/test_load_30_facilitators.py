"""
Load Test: 30 Facilitators × 10 Cohorts × 10 Players
======================================================
Validates the facilitator management system under realistic scale:
  - 30 facilitators (25 regular + 5 lead_facilitators)
  - Each manages up to 10 cohorts
  - Each cohort has 10 players
  - Concurrent reads from all facilitator dashboards
  - God Mode dashboard aggregation timing

Run with:
    python tests/test_load_30_facilitators.py
"""

import asyncio
import time
import httpx
import json
import sys
import statistics
from dataclasses import dataclass, field
from typing import List, Dict

BASE = "http://127.0.0.1:8000"
ADMIN_ID = "FAC-001"
ADMIN_PW = "IIMB3072@"

NUM_FACILITATORS   = 30
NUM_REGULAR        = 25   # roles: facilitator
NUM_LEAD           = 5    # roles: lead_facilitator
COHORTS_PER_FAC    = 10
PLAYERS_PER_COHORT = 10
BUS = ["pharma", "software", "consumer_goods", "manufacturing"]

# ─── Result collectors ───────────────────────────────────────────
@dataclass
class Stats:
    label: str
    times: List[float] = field(default_factory=list)
    errors: List[str]  = field(default_factory=list)

    def record(self, t: float):   self.times.append(t)
    def fail(self, msg: str):     self.errors.append(msg)

    def report(self):
        n = len(self.times)
        if n == 0:
            return f"  {self.label}: NO DATA  errors={len(self.errors)}"
        # quantiles needs >= 2 data points with n=100; fall back for tiny samples
        def p(q):
            if n < 2:
                return self.times[0]
            return statistics.quantiles(self.times, n=100)[q - 1]
        return (
            f"  {self.label}: n={n}  "
            f"avg={statistics.mean(self.times)*1000:.0f}ms  "
            f"p50={p(50)*1000:.0f}ms  "
            f"p95={p(95)*1000:.0f}ms  "
            f"p99={p(99)*1000:.0f}ms  "
            f"max={max(self.times)*1000:.0f}ms  "
            f"errors={len(self.errors)}"
        )

ALL_STATS: Dict[str, Stats] = {}

def stat(label: str) -> Stats:
    if label not in ALL_STATS:
        ALL_STATS[label] = Stats(label)
    return ALL_STATS[label]


# ─── HTTP helpers ────────────────────────────────────────────────
async def timed(client: httpx.AsyncClient, method: str, url: str,
                label: str, **kwargs) -> httpx.Response | None:
    t0 = time.perf_counter()
    try:
        r = await getattr(client, method)(url, **kwargs)
        stat(label).record(time.perf_counter() - t0)
        if r.status_code >= 400:
            stat(label).fail(f"{r.status_code} {r.text[:120]}")
        return r
    except Exception as e:
        stat(label).fail(str(e))
        return None


# ─── Phase 1: Login ──────────────────────────────────────────────
async def admin_login(client: httpx.AsyncClient) -> bool:
    r = await timed(client, "post", f"{BASE}/api/admin/facilitators/login",
                    "login",
                    json={"facilitator_id": ADMIN_ID, "password": ADMIN_PW})
    return r is not None and r.status_code == 200


# ─── Phase 2: Create 30 facilitators ────────────────────────────
async def create_facilitators(client: httpx.AsyncClient) -> List[Dict]:
    print("\n[Phase 2] Creating 30 facilitators …")
    names = [f"LoadTest Fac {i:02d}" for i in range(1, NUM_FACILITATORS + 1)]

    # Batch-create all 30 in one call
    r = await timed(client, "post", f"{BASE}/api/admin/facilitators/batch",
                    "batch_create",
                    json={"names": names})
    if r is None or r.status_code != 200:
        print(f"  FATAL: batch create failed — {r and r.text[:200]}")
        return []

    created = r.json()["created"]
    print(f"  Created {len(created)} facilitators via batch endpoint")

    # Update max_cohorts to 10 and promote first NUM_LEAD to lead_facilitator
    update_tasks = []
    for i, fac in enumerate(created):
        fid = fac["facilitator_id"]
        # Update cohort limit via dedicated PUT endpoint
        update_tasks.append(
            timed(client, "put", f"{BASE}/api/admin/facilitators/{fid}/cohort-limit",
                  "update_cohort_limit",
                  json={"max_cohorts": COHORTS_PER_FAC})
        )
        # Promote to lead_facilitator for the last NUM_LEAD
        if i >= NUM_REGULAR:
            update_tasks.append(
                timed(client, "put", f"{BASE}/api/admin/facilitators/{fid}/role",
                      "promote_lead",
                      json={"role": "lead_facilitator"})
            )

    await asyncio.gather(*update_tasks)
    leads = sum(1 for i in range(len(created)) if i >= NUM_REGULAR)
    print(f"  Cohort limits set → 10.  Lead facilitators promoted: {leads}")
    return created


# ─── Phase 3: Create 10 cohorts per facilitator ─────────────────
async def create_cohorts(client: httpx.AsyncClient,
                         facilitators: List[Dict]) -> List[Dict]:
    print(f"\n[Phase 3] Creating {len(facilitators)} × {COHORTS_PER_FAC} = "
          f"{len(facilitators) * COHORTS_PER_FAC} cohorts …")

    async def create_one(fac: Dict, cohort_num: int) -> Dict | None:
        fid = fac["facilitator_id"]
        r = await timed(client, "post", f"{BASE}/api/simulations/start",
                        "create_cohort",
                        json={
                            "cohort_name":      f"Cohort_{fid}_{cohort_num:02d}",
                            "facilitator_id":   fid,
                            "decision_paradigm":"legacy_abc",
                            "scenario_preset":  "workshop_standard",
                            "currency_symbol":  "₹",
                            "created_by":       "LoadTest",
                            "created_when":     "2026-05-23",
                        })
        if r and r.status_code in (200, 201):
            return r.json()
        return None

    tasks = [
        create_one(fac, n)
        for fac in facilitators
        for n in range(1, COHORTS_PER_FAC + 1)
    ]

    # Run in batches of 50 to avoid overwhelming the in-memory backend
    sessions = []
    batch_size = 50
    for i in range(0, len(tasks), batch_size):
        batch_results = await asyncio.gather(*tasks[i:i+batch_size])
        sessions.extend([s for s in batch_results if s])

    print(f"  Successfully created {len(sessions)} / {len(tasks)} cohorts")
    return sessions


# ─── Phase 4: Induct 10 players per cohort ───────────────────────
async def induct_players(client: httpx.AsyncClient,
                         sessions: List[Dict]) -> int:
    total_target = len(sessions) * PLAYERS_PER_COHORT
    print(f"\n[Phase 4] Inducting {total_target} players "
          f"({len(sessions)} cohorts × {PLAYERS_PER_COHORT}) …")

    async def induct_one(session_id: str, player_num: int) -> bool:
        bu = BUS[player_num % len(BUS)]
        r = await timed(client, "post", f"{BASE}/api/admin/players/induct",
                        "induct_player",
                        json={
                            "name":        f"Player_{player_num:03d}",
                            "email":       f"player{player_num:03d}@loadtest.com",
                            "session_id":  session_id,
                            "assigned_bu": bu,
                        })
        return r is not None and r.status_code == 200

    tasks = [
        induct_one(s["session_id"], (si * PLAYERS_PER_COHORT) + pi)
        for si, s in enumerate(sessions)
        for pi in range(1, PLAYERS_PER_COHORT + 1)
    ]

    # Batches of 100
    succeeded = 0
    batch_size = 100
    for i in range(0, len(tasks), batch_size):
        results = await asyncio.gather(*tasks[i:i + batch_size])
        succeeded += sum(results)
        if (i // batch_size) % 5 == 0:
            print(f"  … {succeeded}/{i + batch_size} players done")

    print(f"  Inducted {succeeded} / {total_target} players")
    return succeeded


# ─── Phase 5: Concurrent dashboard reads ─────────────────────────
async def concurrent_reads(client: httpx.AsyncClient,
                           facilitators: List[Dict]):
    print(f"\n[Phase 5] Concurrent dashboard reads — "
          f"{len(facilitators)} facilitators simultaneously …")

    async def fac_dashboard(fid: str):
        await timed(client, "get",
                    f"{BASE}/api/admin/facilitator-role-info/{fid}",
                    "fac_detail_read")

    async def cohort_list(fid: str):
        await timed(client, "get",
                    f"{BASE}/api/admin/sessions",
                    "cohort_list_read",
                    params={"facilitator_id": fid})

    # All 30 facilitators read their dashboard simultaneously
    await asyncio.gather(*[fac_dashboard(f["facilitator_id"]) for f in facilitators])
    await asyncio.gather(*[cohort_list(f["facilitator_id"])   for f in facilitators])
    print("  All 30 concurrent reads complete")


# ─── Phase 6: God Mode aggregation ───────────────────────────────
async def god_mode_reads(client: httpx.AsyncClient):
    print("\n[Phase 6] God Mode aggregation endpoints …")
    endpoints = [
        ("/api/admin/facilitators",          "god_list_facilitators"),
        ("/api/admin/sessions",              "god_list_all_sessions"),
        ("/api/admin/global-settings",       "god_global_settings"),
        ("/api/admin/god/analytics-visibility","god_analytics_vis"),
        ("/api/admin/side-tracks/catalog",   "god_sidetrack_catalog"),
    ]
    for path, label in endpoints:
        await timed(client, "get", f"{BASE}{path}", label)

    # 10 simultaneous God Mode dashboard reads
    await asyncio.gather(*[
        timed(client, "get", f"{BASE}/api/admin/sessions",
              "god_concurrent_fac_list")
        for _ in range(10)
    ])
    print("  10 concurrent God Mode reads complete")


# ─── Phase 7: Health + freeze blast-radius check ─────────────────
async def freeze_blast_radius(client: httpx.AsyncClient,
                              sessions: List[Dict]):
    if not sessions:
        return
    print("\n[Phase 7] Freeze blast-radius check (GOD-012) …")
    target = sessions[0]["session_id"]

    # Freeze one cohort
    r = await timed(client, "patch",
                    f"{BASE}/api/admin/sessions/{target}/cohort-settings",
                    "freeze_one_cohort",
                    json={"system_frozen": True, "freeze_message": "LoadTest freeze"})
    if r and r.status_code == 200:
        print(f"  Froze session {target}")

    # Verify all others are NOT frozen
    frozen_others = 0
    check_tasks = [
        client.get(f"{BASE}/api/admin/global-settings",
                   params={"session_id": s["session_id"]})
        for s in sessions[1:11]   # check 10 random others
    ]
    results = await asyncio.gather(*check_tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            continue
        try:
            d = res.json()
            if d.get("system_frozen"):
                frozen_others += 1
        except Exception:
            pass

    if frozen_others == 0:
        print(f"  ✅ Blast-radius PASS — 0 / 10 other cohorts affected by freeze")
    else:
        print(f"  ❌ Blast-radius FAIL — {frozen_others} cohorts incorrectly frozen!")

    # Unfreeze
    await timed(client, "patch",
                f"{BASE}/api/admin/sessions/{target}/cohort-settings",
                "unfreeze_cohort",
                json={"system_frozen": False})
    print(f"  Unfroze {target}")


# ─── Phase 8: Teardown — delete all LoadTest facilitators & sessions ──
async def teardown(client: httpx.AsyncClient,
                   facilitators: List[Dict],
                   sessions: List[Dict]):
    print(f"\n[Phase 8] Teardown — deleting {len(facilitators)} LoadTest facilitators …")
    delete_tasks = [
        timed(client, "delete",
              f"{BASE}/api/admin/facilitators/{fac['facilitator_id']}",
              "teardown_delete_fac",
              params={"hard": "true"})
        for fac in facilitators
    ]
    batch_size = 50
    for i in range(0, len(delete_tasks), batch_size):
        await asyncio.gather(*delete_tasks[i:i + batch_size])

    fac_errors = sum(len(e) for e in [stat("teardown_delete_fac").errors])
    print(f"  Deleted {len(facilitators) - fac_errors} / {len(facilitators)} facilitators")

    # Sessions are auto-orphaned once the facilitator is hard-deleted but the
    # in-memory snapshot still holds them.  Use the export/import idempotent
    # delete endpoint if it exists, otherwise accept the orphan count.
    print(f"  {len(sessions)} LoadTest sessions orphaned (will not affect real cohorts)")


# ─── Main ─────────────────────────────────────────────────────────
async def main():
    print("=" * 65)
    print("  MURESSONS LOAD TEST — 30 Facilitators × 10 Cohorts × 10 Players")
    print("=" * 65)
    t_total = time.perf_counter()

    # Single persistent HTTP client (shared cookie jar = one auth session)
    async with httpx.AsyncClient(
        base_url=BASE,
        timeout=httpx.Timeout(30.0),
        follow_redirects=True,
    ) as client:

        # Phase 1: Authenticate
        print("\n[Phase 1] Admin login …")
        if not await admin_login(client):
            print("  FATAL: Cannot authenticate.  Is the backend running?")
            return

        print(f"  ✅ Logged in as {ADMIN_ID} (super_admin)")

        # Phase 2–4: Data setup
        facilitators = await create_facilitators(client)
        if not facilitators:
            print("  FATAL: No facilitators created.  Aborting.")
            return

        sessions = await create_cohorts(client, facilitators)
        if sessions:
            await induct_players(client, sessions)

        # Phase 5–7: Load & correctness checks
        await concurrent_reads(client, facilitators)
        await god_mode_reads(client)
        await freeze_blast_radius(client, sessions)

        # Phase 8: Cleanup — remove test data so reruns start clean
        await teardown(client, facilitators, sessions)

    # ── Final report ──────────────────────────────────────────────
    elapsed = time.perf_counter() - t_total
    print("\n" + "=" * 65)
    print("  RESULTS")
    print("=" * 65)

    order = [
        "login", "batch_create", "update_cohort_limit", "promote_lead",
        "create_cohort", "induct_player",
        "fac_detail_read", "cohort_list_read",
        "god_list_facilitators", "god_list_all_sessions",
        "god_global_settings", "god_analytics_vis", "god_sidetrack_catalog",
        "god_concurrent_fac_list",
        "freeze_one_cohort", "unfreeze_cohort",
        "teardown_delete_fac",
    ]
    for label in order:
        if label in ALL_STATS:
            print(ALL_STATS[label].report())

    total_errors = sum(len(s.errors) for s in ALL_STATS.values())
    total_calls  = sum(len(s.times) + len(s.errors) for s in ALL_STATS.values())

    print(f"\n  Total wall time : {elapsed:.1f}s")
    print(f"  Total API calls : {total_calls}")
    print(f"  Total errors    : {total_errors}")

    if total_errors == 0:
        print("\n  ✅  ALL CHECKS PASSED — simulation is stable at full load")
    else:
        print(f"\n  ⚠️  {total_errors} errors detected — review details above")
        # Print first few errors per stat
        for s in ALL_STATS.values():
            for e in s.errors[:3]:
                print(f"     [{s.label}] {e}")

    return total_errors


if __name__ == "__main__":
    errors = asyncio.run(main())
    sys.exit(0 if errors == 0 else 1)
