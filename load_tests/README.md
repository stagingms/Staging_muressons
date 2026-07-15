# Muressons load & scale test suite (audit #7 / #8)

This directory holds the k6 harness that gates the ~500-concurrent-user launch.
It exists because the app was built for a single classroom (~5–40 users) and the
audit re-rated the 500-user target as the top architectural risk (§1.2/§6.1).

**You must run these against a real deployment** (staging on Railway, or a local
Docker build). They cannot be run meaningfully in the authoring sandbox — 500
virtual users need real CPU, a real Postgres, and a real load balancer.

## Prerequisites

- [k6](https://k6.io/docs/get-started/installation/) installed (`brew install k6`,
  `choco install k6`, or the Docker image `grafana/k6`).
- A deployed backend + frontend reachable at a `BASE_URL`.
- **Postgres** configured (`USE_MEMORY_DB=false`, reachable `DATABASE_URL`,
  `DEBUG=false`). The in-memory store cannot be load-tested for scale — it is
  clamped to one worker by `scale_preflight`.

## The two tests

| Script | Question it answers | Pass criteria |
|---|---|---|
| `throughput_test.js` | Can the server carry 500 users' dashboard polls + commits? | dashboard reads **p95 < 1s**, read errors **< 1%**, **no 5xx** on commits |
| `split_brain_probe.js` | Does a facilitator freeze/unlock on one worker reach players on other workers? | **100%** of fan-out samples agree within the refresh window (zero split-brain) |

## Runbook

### Step 0 — establish the single-worker ceiling (baseline)
Deploy with `WEB_CONCURRENCY=1` and run throughput. This shows where one worker
saturates and is the "before" number for scale-out.

```bash
k6 run -e BASE_URL=https://staging.example -e VUS=500 -e DURATION=15m throughput_test.js
```

Expect this to breach the p95 threshold — that failure is the point (it proves
the §1.2 throughput wall). Note the VU count / RPS at which p95 crosses 1s.

### Step 1 — scale out and re-run throughput
Set `WEB_CONCURRENCY` to roughly `(2 × vCPU) + 1` on a Postgres deployment, and/or
add Railway replicas (Service → Settings → **Replicas**). Re-run the same command.
The thresholds should now pass. Increase `VUS` past 500 to find real headroom.

```bash
# scale_preflight will refuse >1 worker unless Postgres is active — check the boot
# log for:  "⚙️  Backend workers: N"
k6 run -e BASE_URL=https://staging.example -e VUS=500 -e DURATION=15m throughput_test.js
```

### Step 2 — prove no split-brain across workers
With `WEB_CONCURRENCY>1` (or ≥2 replicas) still active:

```bash
k6 run -e BASE_URL=https://staging.example -e MASTER_PASSWORD='***' \
       -e REFRESH_SECONDS=3 split_brain_probe.js
```

A green run means the freeze flipped on one worker and **every** sampled worker
reported the change within `COORDINATION_REFRESH_SECONDS + 1.5s`. A failure prints
`SPLIT-BRAIN: X/N samples still reported the stale value` — that worker is holding
stale in-process state; check that `coordination_store` is on Postgres and its
background refresher is running (it starts in the FastAPI lifespan).

### Tunables (env)
- `VUS` (default 500), `DURATION` (default 15m), `POLL_SECONDS` (8), `COMMIT_EVERY` (5)
- `REFRESH_SECONDS` must match the server's `COORDINATION_REFRESH_SECONDS` (default 3)
- `SAMPLES` (default 60) — fan-out samples per assertion in the split-brain probe

## Interpreting results / where to look when it fails

- **Throughput p95 > 1s even after scale-out** → add workers/replicas; confirm
  Postgres connection-pool size (`DB_MAX_CONNECTIONS`) is not the bottleneck;
  check `GET /dashboard` isn't doing full-history reads (use `?since_round=`).
- **Commit 5xx** → the synchronous engine or the Postgres advisory-lock path is
  choking; inspect worker CPU and DB lock waits.
- **Split-brain** → coordination refresher not running, or the deployment silently
  fell back to memory mode (check `/health` → `database: "postgresql"`).

## Known limitation (document before launch)

Timed/scheduled auto-unlocks are driven by an in-process `asyncio` timer on the
worker that scheduled them. The *unlock result* is shared across workers (it
publishes to the coordination store), but if that specific worker dies before the
timer fires, the scheduled unlock is lost. Manual unlock and freeze — the common
live-facilitation actions — are unaffected. A fully HA scheduler (single leader or
a DB-backed job runner) is future work; call this out in the run plan and prefer
manual pacing for high-stakes 500-user sessions until it lands.
