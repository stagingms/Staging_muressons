"""Muressons — PostgreSQL race + classroom-50 burst drill (EVAL_AuditResponse
2026-09-10, action 11; audit G02 / G03 and the live verification of F01 / N2).

Plays N facilitator-issued teams, spread over C cohorts (a cohort holds at
most 20 driver seats — player_capacity.MAX_PLAYERS_CEILING — so a 50-seat
class is three cohorts, or one cohort of ≤ 20 teams with observers on view
codes), through R rounds against a running backend on real PostgreSQL, the
way a class does:

  logins      the facilitator mints N players; each joins, sets a personal
              password (first-login gate) and logs in — all within minutes,
              each from its own client IP (X-Forwarded-For, honoured because
              the backend trusts the local proxy).
  each round  every team autosaves its draft every AUTOSAVE seconds and polls
              the dashboard every POLL seconds; each team commits at a random
              moment inside a WINDOW-second deadline (WINDOW 0 = everyone at
              once — the burst). Two teams misbehave on purpose:
                team 0  "reload mid-commit": the moment its commit is sent it
                        also fetches the dashboard and posts a save with the
                        round it was showing — the F01 race.
                team 1  "duplicate tab": a second client keeps autosaving with
                        the OLD round after the first client's commit.
  after each  every team's stored R(n+1) row is compared, key by key, with
  round       the commit response it received (the F01 / N2 invariant).

What is counted: commit status codes and latency (p50 / p95 / max), 5xx,
503 commit_queue_full (the 45 s gate), stale-tab 409s, saves that returned
200 after the round had advanced (must be 0), rows that differ from their
commit response (must be 0), login latency.

Usage (the backend must be running on Postgres; production-like settings):
  python load_tests/pg_burst_drill.py --base-url http://127.0.0.1:8010 \
      --teams 50 --rounds 10 --window 60 --out DRILL_spread.json
  python load_tests/pg_burst_drill.py ... --window 0 --out DRILL_burst.json

MASTER_PASSWORD is read from the environment.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import statistics
import sys
import time
from typing import Any

import httpx

_ECONOMIC_GLOBAL = ("corporate_treasury", "group_reputation", "synergy_multiplier", "cost_of_capital")
_ECONOMIC_BU = ("revenue_base", "opex_base", "natural_capital_debt", "social_license_score",
                "reputation_score", "governance_risk_score", "carbon_intensity")


def _pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return round(s[k], 1)


def _summary(ms: list[float]) -> dict:
    return {"n": len(ms), "p50_ms": _pct(ms, 50), "p95_ms": _pct(ms, 95),
            "max_ms": round(max(ms), 1) if ms else None, "mean_ms": round(statistics.fmean(ms), 1) if ms else None}


class Team:
    def __init__(self, idx: int, base_url: str):
        self.idx = idx
        self.ip = f"10.7.{idx // 250}.{idx % 250 + 1}"
        self.client = httpx.AsyncClient(base_url=base_url, timeout=90.0,
                                        headers={"X-Forwarded-For": self.ip})
        self.pid = self.pw = self.sid = self.token = None
        self.bus: list[dict] = []
        self.round = 1
        self.last_commit: dict | None = None
        self.log: list[dict] = []

    @property
    def hdr(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "X-Player-Id": self.pid}

    async def close(self):
        await self.client.aclose()


class Drill:
    def __init__(self, a):
        self.a = a
        self.base = a.base_url
        self.fac = httpx.AsyncClient(base_url=self.base, timeout=60.0, headers={"X-Forwarded-For": "10.9.9.9"})
        self.teams: list[Team] = []
        self.cohort = None
        self.stats: dict[str, Any] = {
            "config": vars(a) | {"master_password": "***"},
            "logins": {"latency_ms": [], "failures": []},
            "rounds": [],
            "totals": {"commits_201": 0, "commits_409": 0, "commits_429": 0, "commits_503_queue": 0,
                       "commits_5xx": 0, "commits_other": 0, "saves_200": 0, "saves_409": 0,
                       "saves_other": 0, "stale_tab_saves_200_after_advance": 0,
                       "reload_saves": {}, "dashboard_polls": 0, "dashboard_errors": 0,
                       "row_mismatches": 0},
            "commit_latency_ms": [], "save_latency_ms": [], "dashboard_latency_ms": [],
            "server_errors": [],
        }

    # ── phase A: facilitator + N logins ────────────────────────────────────
    async def setup(self):
        r = await self.fac.post("/api/admin/facilitators/login",
                                json={"facilitator_id": "god_mode", "password": self.a.master_password})
        assert r.status_code == 200, f"facilitator login: {r.status_code} {r.text[:200]}"
        # the session cookie is path=/api; httpx's jar does not always replay
        # it to an IP-addressed origin, so send it explicitly (as a browser would)
        self.fac.headers["Cookie"] = f"mur_session={r.cookies.get('mur_session')}"
        self.cohorts = []
        stamp = int(time.time())
        for c in range(self.a.cohorts):
            r = await self.fac.post("/api/simulations/start",
                                    json={"cohort_name": f"DRILL-{stamp}-{c + 1}", "decision_paradigm": self.a.paradigm,
                                          "difficulty_tier": self.a.tier})
            assert r.status_code in (200, 201), f"start: {r.status_code} {r.text[:200]}"
            self.cohorts.append(r.json()["session_id"])
        self.cohort = self.cohorts[0]
        self.teams = [Team(i, self.base) for i in range(self.a.teams)]
        for t in self.teams:
            t.cohort = self.cohorts[t.idx % len(self.cohorts)]

        async def login(t: Team, delay: float):
            await asyncio.sleep(delay)
            t0 = time.perf_counter()
            try:
                g = await self.fac.post(f"/api/admin/{t.cohort}/generate-player", json={"player_name": f"Team{t.idx:02d}"})
                assert g.status_code in (200, 201), f"generate-player {g.status_code} {g.text[:120]}"
                t.pid, first_pw = g.json()["player_id"], g.json()["password"]
                j = await t.client.post(f"/api/simulations/public/sessions/{t.cohort}/join",
                                        json={"player_id": t.pid, "password": first_pw, "player_name": f"Team{t.idx:02d}"})
                assert j.status_code == 200, f"join {j.status_code} {j.text[:120]}"
                t.pw = f"Team{t.idx:02d}#Drill2026"
                c = await t.client.post("/api/simulations/change-password",
                                        json={"player_id": t.pid, "old_password": first_pw, "new_password": t.pw})
                assert c.status_code == 200, f"change-password {c.status_code} {c.text[:120]}"
                l = await t.client.post("/api/simulations/player-login", json={"player_id": t.pid, "password": t.pw})
                assert l.status_code == 200, f"player-login {l.status_code} {l.text[:120]}"
                t.sid, t.token = l.json()["session_id"], l.json()["player_token"]
                d = await t.client.get(f"/api/simulations/{t.sid}/dashboard", headers=t.hdr)
                assert d.status_code == 200, f"dashboard {d.status_code}"
                t.bus = d.json()["business_units"]
                t.round = d.json()["current_round"]
                self.stats["logins"]["latency_ms"].append((time.perf_counter() - t0) * 1000)
            except Exception as exc:  # noqa: BLE001
                self.stats["logins"]["failures"].append({"team": t.idx, "error": str(exc)[:200]})

        # N logins spread over LOGIN_WINDOW seconds (a class arriving)
        await asyncio.gather(*(login(t, random.uniform(0, self.a.login_window)) for t in self.teams))
        self.teams = [t for t in self.teams if t.sid]

    # ── one team, one round ────────────────────────────────────────────────
    def _decisions(self, t: Team) -> list[dict]:
        return [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 500_000.0,
                 "choice_selected": random.choice(("option_a", "option_b", "option_c"))} for b in t.bus]

    async def _save(self, t: Team, rnd: int, client: httpx.AsyncClient | None = None, tag: str = "autosave") -> int:
        client = client or t.client
        body = {"allocations": {b["bu_id"]: 500_000.0 for b in t.bus}, "decision_choice": "option_b", "expected_round": rnd}
        t0 = time.perf_counter()
        try:
            r = await client.post(f"/api/simulations/{t.sid}/save-decisions", json=body, headers=t.hdr)
        except Exception as exc:  # noqa: BLE001
            self.stats["server_errors"].append({"team": t.idx, "op": tag, "error": str(exc)[:160]})
            return -1
        self.stats["save_latency_ms"].append((time.perf_counter() - t0) * 1000)
        if r.status_code == 200:
            self.stats["totals"]["saves_200"] += 1
        elif r.status_code == 409:
            self.stats["totals"]["saves_409"] += 1
        else:
            self.stats["totals"]["saves_other"] += 1
            if r.status_code >= 500:
                self.stats["server_errors"].append({"team": t.idx, "op": tag, "status": r.status_code, "body": r.text[:160]})
        return r.status_code

    async def _poll(self, t: Team) -> dict | None:
        t0 = time.perf_counter()
        try:
            r = await t.client.get(f"/api/simulations/{t.sid}/dashboard", headers=t.hdr)
        except Exception as exc:  # noqa: BLE001
            self.stats["totals"]["dashboard_errors"] += 1
            self.stats["server_errors"].append({"team": t.idx, "op": "dashboard", "error": str(exc)[:160]})
            return None
        self.stats["dashboard_latency_ms"].append((time.perf_counter() - t0) * 1000)
        self.stats["totals"]["dashboard_polls"] += 1
        if r.status_code != 200:
            self.stats["totals"]["dashboard_errors"] += 1
            return None
        return r.json()

    async def _commit(self, t: Team, rnd: int) -> tuple[int, dict | None, float]:
        body = {"decisions": self._decisions(t), "dividends_paid": 0.0, "force_override_cfo": True, "expected_round": rnd}
        t0 = time.perf_counter()
        try:
            r = await t.client.post(f"/api/simulations/{t.sid}/commit-turn", json=body, headers=t.hdr)
        except Exception as exc:  # noqa: BLE001
            self.stats["server_errors"].append({"team": t.idx, "op": "commit", "error": str(exc)[:160]})
            return -1, None, (time.perf_counter() - t0) * 1000
        ms = (time.perf_counter() - t0) * 1000
        self.stats["commit_latency_ms"].append(ms)
        code = r.status_code
        tot = self.stats["totals"]
        if code == 201:
            tot["commits_201"] += 1
        elif code == 409:
            tot["commits_409"] += 1
        elif code == 429:
            tot["commits_429"] += 1
        elif code == 503 and "commit_queue_full" in r.text:
            tot["commits_503_queue"] += 1
        elif code >= 500:
            tot["commits_5xx"] += 1
            self.stats["server_errors"].append({"team": t.idx, "op": "commit", "status": code, "body": r.text[:200]})
        else:
            tot["commits_other"] += 1
            self.stats["server_errors"].append({"team": t.idx, "op": "commit", "status": code, "body": r.text[:200]})
        return code, (r.json() if code == 201 else None), ms

    async def play_round(self, rnd: int, round_stats: dict):
        window = self.a.window
        deadline = time.monotonic() + window + 2.0
        commit_at = {t.idx: time.monotonic() + (random.uniform(0.5, window) if window > 0 else 0.0) for t in self.teams}
        stale_tab = {t.idx: httpx.AsyncClient(base_url=self.base, timeout=60.0, headers={"X-Forwarded-For": t.ip})
                     for t in self.teams if t.idx == 1}

        async def team_loop(t: Team):
            committed = False
            next_save = time.monotonic() + random.uniform(0, self.a.autosave)
            next_poll = time.monotonic() + random.uniform(0, self.a.poll)
            while True:
                now = time.monotonic()
                if not committed and now >= commit_at[t.idx]:
                    committed = True
                    if t.idx == 0:
                        # reload mid-commit: the commit and a dashboard+save with the round the tab shows, at once
                        commit_task = asyncio.create_task(self._commit(t, rnd))
                        await asyncio.sleep(0.02)
                        poll_task = asyncio.create_task(self._poll(t))
                        save_code = await self._save(t, rnd, tag="reload_save")
                        code, resp, ms = await commit_task
                        await poll_task
                        self.stats["totals"]["reload_saves"][str(save_code)] = self.stats["totals"]["reload_saves"].get(str(save_code), 0) + 1
                    else:
                        code, resp, ms = await self._commit(t, rnd)
                    t.log.append({"round": rnd, "commit_status": code, "ms": round(ms, 1)})
                    if code == 201:
                        t.last_commit = resp
                        t.bus = resp.get("business_units") or t.bus
                        t.round = resp.get("new_round_number", rnd + 1)
                        if t.idx == 1:
                            # duplicate tab: still on the old round, keeps autosaving
                            for _ in range(2):
                                await asyncio.sleep(self.a.autosave / 2)
                                sc = await self._save(t, rnd, client=stale_tab[t.idx], tag="stale_tab")
                                if sc == 200:
                                    self.stats["totals"]["stale_tab_saves_200_after_advance"] += 1
                    elif code in (503, 429):
                        # 503: the gate said "try again" (the cockpit retries after
                        # Retry-After); 429: the 5-second double-submit cooldown
                        # (the cockpit disables the button). One retry, like the client.
                        await asyncio.sleep(5.5)
                        code2, resp2, ms2 = await self._commit(t, rnd)
                        t.log.append({"round": rnd, "commit_retry_status": code2, "ms": round(ms2, 1)})
                        if code2 == 201:
                            t.last_commit = resp2
                            t.bus = resp2.get("business_units") or t.bus
                            t.round = resp2.get("new_round_number", rnd + 1)
                    return
                if now >= next_save:
                    await self._save(t, rnd)
                    next_save = time.monotonic() + self.a.autosave
                if now >= next_poll:
                    await self._poll(t)
                    next_poll = time.monotonic() + self.a.poll
                if now > deadline:
                    return
                await asyncio.sleep(0.05)

        t0 = time.perf_counter()
        await asyncio.gather(*(team_loop(t) for t in self.teams))
        round_stats["wall_seconds"] = round(time.perf_counter() - t0, 1)
        for c in stale_tab.values():
            await c.aclose()

    async def verify_round(self, rnd: int, round_stats: dict):
        """Every team's stored row for R(n+1) equals its commit response."""
        mismatches = []
        not_advanced = []
        for t in self.teams:
            d = await self._poll(t)
            if d is None:
                mismatches.append({"team": t.idx, "error": "dashboard unavailable"})
                continue
            if t.last_commit is None or int(t.last_commit.get("new_round_number", 0)) != min(rnd + 1, self.a.rounds):
                not_advanced.append(t.idx)
                continue
            expected_round = min(rnd + 1, self.a.rounds)      # R10 commits in place (SEAM-08)
            if d["current_round"] != expected_round:
                mismatches.append({"team": t.idx, "error": f"current_round {d['current_round']} != {expected_round}"})
                continue
            gs, exp_gs = d["global_state"], t.last_commit["global_state"]
            for k in _ECONOMIC_GLOBAL:
                if abs(float(gs.get(k, 0)) - float(exp_gs.get(k, 0))) > 0.01:
                    mismatches.append({"team": t.idx, "key": k, "stored": gs.get(k), "committed": exp_gs.get(k)})
            by_id = {b["bu_id"]: b for b in t.last_commit["business_units"]}
            for b in d["business_units"]:
                for k in _ECONOMIC_BU:
                    if abs(float(b.get(k, 0) or 0) - float(by_id[b["bu_id"]].get(k, 0) or 0)) > 0.01:
                        mismatches.append({"team": t.idx, "bu": b["bu_id"], "key": k, "stored": b.get(k), "committed": by_id[b["bu_id"]].get(k)})
            if gs.get("saved_allocations"):
                mismatches.append({"team": t.idx, "error": "draft keys survived the commit (saved_allocations present)"})
        round_stats["row_mismatches"] = mismatches
        round_stats["teams_not_advanced"] = not_advanced
        self.stats["totals"]["row_mismatches"] += len(mismatches)

    async def run(self):
        t_all = time.perf_counter()
        await self.setup()
        self.stats["logins"]["summary"] = _summary(self.stats["logins"]["latency_ms"])
        self.stats["logins"]["teams_ready"] = len(self.teams)
        self.stats["cohorts"] = self.cohorts
        print(f"[drill] {len(self.cohorts)} cohort(s): {len(self.teams)} teams logged in "
              f"(p95 {self.stats['logins']['summary']['p95_ms']} ms, failures {len(self.stats['logins']['failures'])})", flush=True)
        for rnd in range(1, self.a.rounds + 1):
            if rnd > 1 and self.a.gap > 0:
                await asyncio.sleep(self.a.gap)     # the facilitator's debrief between rounds (≥ the 5-s cooldown)
            rs: dict[str, Any] = {"round": rnd}
            n_before = len(self.stats["commit_latency_ms"])
            await self.play_round(rnd, rs)
            rs["commit_latency"] = _summary(self.stats["commit_latency_ms"][n_before:])
            rs["commit_statuses"] = {}
            for t in self.teams:
                for e in t.log:
                    if e["round"] == rnd and "commit_status" in e:
                        rs["commit_statuses"][str(e["commit_status"])] = rs["commit_statuses"].get(str(e["commit_status"]), 0) + 1
            await self.verify_round(rnd, rs)
            self.stats["rounds"].append(rs)
            print(f"[drill] R{rnd}: statuses {rs['commit_statuses']} p95 {rs['commit_latency']['p95_ms']} ms "
                  f"max {rs['commit_latency']['max_ms']} ms wall {rs['wall_seconds']} s "
                  f"mismatches {len(rs['row_mismatches'])} not_advanced {rs['teams_not_advanced']}", flush=True)
        self.stats["commit_latency"] = _summary(self.stats["commit_latency_ms"])
        self.stats["save_latency"] = _summary(self.stats["save_latency_ms"])
        self.stats["dashboard_latency"] = _summary(self.stats["dashboard_latency_ms"])
        self.stats["wall_seconds"] = round(time.perf_counter() - t_all, 1)
        for k in ("commit_latency_ms", "save_latency_ms", "dashboard_latency_ms"):
            self.stats[k] = None   # raw samples not kept in the report
        for t in self.teams:
            await t.close()
        await self.fac.aclose()
        return self.stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://127.0.0.1:8010"))
    ap.add_argument("--teams", type=int, default=50)
    ap.add_argument("--cohorts", type=int, default=3, help="teams are spread round-robin; a cohort holds at most 20")
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--window", type=float, default=60.0, help="seconds over which a round's commits spread; 0 = burst")
    ap.add_argument("--gap", type=float, default=8.0, help="seconds between rounds (a class debriefs; the commit cooldown is 5 s)")
    ap.add_argument("--autosave", type=float, default=2.0)
    ap.add_argument("--poll", type=float, default=8.0)
    ap.add_argument("--login-window", type=float, default=30.0)
    ap.add_argument("--paradigm", default="legacy_abc")
    ap.add_argument("--tier", default="advanced")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="DRILL_result.json")
    ap.add_argument("--master-password", default=os.environ.get("MASTER_PASSWORD", ""))
    a = ap.parse_args()
    if not a.master_password:
        sys.exit("MASTER_PASSWORD is required (env or --master-password)")
    random.seed(a.seed)
    stats = asyncio.run(Drill(a).run())
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2, default=str)
    tot = stats["totals"]
    ok = (tot["commits_5xx"] == 0 and tot["row_mismatches"] == 0
          and tot["stale_tab_saves_200_after_advance"] == 0
          and tot["commits_201"] == a.teams * a.rounds)
    print(json.dumps({"verdict": "PASS" if ok else "FAIL", "totals": tot, "commit_latency": stats["commit_latency"],
                      "save_latency": stats["save_latency"], "dashboard_latency": stats["dashboard_latency"],
                      "logins": stats["logins"]["summary"], "wall_seconds": stats["wall_seconds"]}, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
