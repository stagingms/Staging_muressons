/*
 * Muressons — cross-worker coordination (split-brain) probe (audit #8/#5/#7).
 *
 * The whole point of externalizing coordination state to Postgres (#5) is that a
 * facilitator action on ONE worker becomes visible to players served by OTHER
 * workers. This probe verifies that: it flips the global God-Mode freeze, then
 * hammers a freeze-reflecting endpoint many times so requests fan out across all
 * workers/replicas behind the load balancer, and asserts EVERY response agrees
 * within the coordination refresh window.
 *
 * If any sampled response still reports the old value after the window, that is a
 * split-brain — a worker holding stale in-process state — and the test fails.
 *
 * Prerequisites:
 *   • Backend on Postgres with WEB_CONCURRENCY>1 (or multiple Railway replicas).
 *   • God-Mode master password (logs in as god_mode).
 *
 * Usage:
 *   k6 run -e BASE_URL=https://staging.example \
 *          -e MASTER_PASSWORD=... \
 *          -e REFRESH_SECONDS=3 \
 *          load_tests/split_brain_probe.js
 */
import http from 'k6/http';
import { check, sleep, fail } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';
const MASTER_PASSWORD = __ENV.MASTER_PASSWORD || '';
const REFRESH_SECONDS = parseFloat(__ENV.REFRESH_SECONDS || '3');
const SAMPLES = parseInt(__ENV.SAMPLES || '60', 10); // fan-out samples per assertion

export const options = {
  scenarios: {
    probe: { executor: 'shared-iterations', vus: 1, iterations: 1, maxDuration: '3m' },
  },
  // This is a correctness probe, not a load test: any split-brain fails the run.
  thresholds: { checks: ['rate==1.0'] },
};

const JSON_HDR = { headers: { 'Content-Type': 'application/json' } };

function login() {
  // Master password logs in as god_mode; the JWT is returned as a cookie which
  // k6's cookie jar reuses for subsequent authenticated calls.
  const res = http.post(
    `${BASE_URL}/api/admin/facilitators/login`,
    JSON.stringify({ password: MASTER_PASSWORD }),
    { ...JSON_HDR, tags: { name: 'login' } },
  );
  check(res, { 'login ok': (r) => r.status === 200 });
  if (res.status !== 200) fail(`login failed (${res.status}) — set MASTER_PASSWORD`);
}

function setFreeze(frozen) {
  const path = frozen ? 'god/freeze' : 'god/unfreeze';
  const body = frozen ? JSON.stringify({ message: 'split-brain probe' }) : '{}';
  const res = http.post(`${BASE_URL}/api/admin/${path}`, body, { ...JSON_HDR, tags: { name: path } });
  check(res, { [`${path} accepted`]: (r) => r.status === 200 });
}

function readFrozen() {
  // GET /god/settings returns the per-worker _god_mode_settings; hitting it many
  // times fans requests across workers via the load balancer.
  const res = http.get(`${BASE_URL}/api/admin/god/settings`, { tags: { name: 'read_settings' } });
  if (res.status !== 200) return null;
  try { return res.json().system_frozen === true; } catch (e) { return null; }
}

function assertAllAgree(expected, label) {
  // Give the cross-worker refresh window time to propagate, plus a safety margin.
  sleep(REFRESH_SECONDS + 1.5);
  let agree = 0;
  let disagree = 0;
  for (let i = 0; i < SAMPLES; i++) {
    const v = readFrozen();
    if (v === expected) agree += 1;
    else disagree += 1;
  }
  const ok = disagree === 0;
  check(null, { [`${label}: all ${SAMPLES} workers agree frozen=${expected}`]: () => ok });
  if (!ok) {
    fail(`SPLIT-BRAIN: ${disagree}/${SAMPLES} samples still reported the stale ` +
         `value after ${REFRESH_SECONDS + 1.5}s. A worker is holding stale ` +
         `in-process coordination state — check coordination_store refresh.`);
  }
}

export default function () {
  if (!MASTER_PASSWORD) fail('MASTER_PASSWORD env is required for this probe.');
  login();

  // 1) Freeze on one connection → every worker must report frozen=true.
  setFreeze(true);
  assertAllAgree(true, 'freeze');

  // 2) Unfreeze → every worker must report frozen=false.
  setFreeze(false);
  assertAllAgree(false, 'unfreeze');
}
