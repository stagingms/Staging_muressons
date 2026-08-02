/*
 * Muressons — 500-user throughput load test (audit #8).
 *
 * Models the steady-state classroom load the audit flagged (§6.1): ~100 cohorts
 * x 5 players = 500 concurrent users, each holding a session and polling the
 * dashboard, with periodic commits at round boundaries.
 *
 * To keep the harness auth-free and self-seeding, each virtual user (VU) creates
 * its OWN solo session via /solo-start (no facilitator/login needed) and then
 * behaves like a player: poll the dashboard on the real ~8s cadence and commit a
 * turn every few cycles. This exercises the two hot paths that saturate a single
 * worker — GET /dashboard (the bulk of the load) and POST /commit-turn (which
 * runs the synchronous engine) — so it measures the throughput wall directly.
 *
 * PASS CRITERIA (thresholds below): dashboard reads p95 < 1s, <1% read errors,
 * and no 5xx on commits. Run it once on a SINGLE worker to find the ceiling,
 * then again with WEB_CONCURRENCY>1 on Postgres to confirm scale-out.
 *
 * Usage:
 *   k6 run -e BASE_URL=https://staging.example \
 *          -e VUS=500 -e DURATION=15m \
 *          load_tests/throughput_test.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';
const VUS = parseInt(__ENV.VUS || '500', 10);
const DURATION = __ENV.DURATION || '15m';
const POLL_SECONDS = parseFloat(__ENV.POLL_SECONDS || '8');   // player poll cadence
const COMMIT_EVERY = parseInt(__ENV.COMMIT_EVERY || '5', 10); // commit every N polls

const dashboardLatency = new Trend('dashboard_latency', true);
const dashboardErrors = new Rate('dashboard_errors');
const commitServerErrors = new Rate('commit_5xx');
const commitsAttempted = new Counter('commits_attempted');

export const options = {
  scenarios: {
    classroom: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: VUS },   // ramp up
        { duration: DURATION, target: VUS },// steady state
        { duration: '1m', target: 0 },      // ramp down
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    dashboard_latency: ['p(95)<1000'],     // §6.1 target: p95 < 1s
    dashboard_errors: ['rate<0.01'],       // <1% read errors
    commit_5xx: ['rate<0.001'],            // commits must not 5xx
    http_req_failed: ['rate<0.05'],
  },
};

// Per-VU state (each VU has its own JS context).
let sessionId = null;
let buIds = [];
let pollCount = 0;

function createSoloSession() {
  const res = http.post(
    `${BASE_URL}/api/simulations/solo-start`,
    JSON.stringify({ player_name: `LoadVU-${__VU}`, decision_paradigm: 'legacy_abc' }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'solo_start' } },
  );
  if (res.status !== 201 && res.status !== 200) return false;
  try {
    const body = res.json();
    sessionId = body.session_id;
    buIds = (body.business_units || []).map((b) => b.bu_id).filter(Boolean);
    return !!sessionId;
  } catch (e) {
    return false;
  }
}

function pollDashboard() {
  const res = http.get(`${BASE_URL}/api/simulations/${sessionId}/dashboard`, {
    tags: { name: 'dashboard' },
  });
  dashboardLatency.add(res.timings.duration);
  const ok = res.status === 200;
  dashboardErrors.add(!ok);
  if (!ok) return null;
  try { return res.json(); } catch (e) { return null; }
}

function commitTurn(dashboard) {
  if (!buIds.length) return;
  const decisions = buIds.map((id) => ({
    bu_id: id,
    investment_ratio: 0.5,
    capex_allocated: 1000000,     // server recomputes ratio from capex (VULN-002)
    time_to_decision_seconds: 30,
  }));
  const payload = { decisions };
  if (dashboard && dashboard.current_round) payload.expected_round = dashboard.current_round;
  const res = http.post(
    `${BASE_URL}/api/simulations/${sessionId}/commit-turn`,
    JSON.stringify(payload),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'commit_turn' } },
  );
  commitsAttempted.add(1);
  // 201 = committed; 409 = round done / concurrent; 429 = cooldown; 403 = locked.
  // Only 5xx is a real failure — the server choking under load.
  commitServerErrors.add(res.status >= 500);
}

export default function () {
  if (!sessionId) {
    if (!createSoloSession()) { sleep(1); return; }
  }
  const dash = pollDashboard();
  pollCount += 1;
  if (dash && pollCount % COMMIT_EVERY === 0) {
    commitTurn(dash);
  }
  // Jitter the poll so 500 VUs don't align into a thundering herd.
  sleep(POLL_SECONDS * (0.75 + Math.random() * 0.5));
}
