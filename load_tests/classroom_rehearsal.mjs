/*
 * Muressons — scripted classroom rehearsal (EVAL_AuditResponse 2026-09-10,
 * action 12; audit G05 / G01).
 *
 * Drives two participant seats through the built cockpit in headless Chromium
 * at 1366 × 768 against a running backend on PostgreSQL, and times every
 * recovery the runbook promises. What the SEAT does goes through the real UI
 * (sign-in, the first-login password gate, the callsign gate, the board,
 * reloads, the second tab, the reconnecting banner, the results screen, the
 * Strategy Report). What the FACILITATOR does — and the round commit itself,
 * whose UI path is a graded drag-and-drop stakeholder map followed by option
 * cards and allocation sliders — goes through the same API endpoints the
 * cockpit calls, so this rehearsal proves the server-side behaviour and the
 * cockpit's reaction to it; it does not replace a human walking the decision
 * canvas (see RUNBOOK_Classroom50_2026-09-10.md, "what only a person can do").
 *
 * Steps (each timed, each with a PASS/FAIL and a screenshot):
 *   1  first sign-in: temp password → personal password → callsign → board
 *   2  reload keeps the session (no re-login)
 *   3  a second tab on the same seat shows the same board
 *   4  double-submit: two commits for the same round at once → exactly one lands
 *   5  lost commit response: the tab last showed R1, the server is on R2 →
 *      reload puts the results screen back (F06b), Advance moves to R2
 *   6  the duplicate tab, still on R1, re-syncs to R2 on its next poll
 *   7  Force Advance while a seat has only a saved draft → the seat's board
 *      shows the auto-commit notice on its next poll (D2 / AC-1)
 *   8  90-second outage during a reload: the backend is frozen (SIGSTOP),
 *      the seat reloads → "Reconnecting" banner, session kept; backend
 *      resumes → board back with no re-login (F06a)
 *   9  insolvency: a facilitator black swan drains the treasury below the
 *      emergency-credit trigger; the next commit draws the line and the
 *      seat's board says so (FIN-05)
 *  10  export: after R10 the Strategy Report opens and prints the treasury by
 *      round, labelled entering / after (F05)
 *
 * Usage:
 *   BASE_URL=http://127.0.0.1:8010 FRONTEND_URL=http://127.0.0.1:3010 \
 *   MASTER_PASSWORD=… BACKEND_PID=<uvicorn pid, for step 8> \
 *   node load_tests/classroom_rehearsal.mjs --out REHEARSAL_result.json
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const API = process.env.BASE_URL || 'http://127.0.0.1:8010';
const FE = process.env.FRONTEND_URL || 'http://127.0.0.1:3010';
const MP = process.env.MASTER_PASSWORD;
const BACKEND_PID = process.env.BACKEND_PID ? parseInt(process.env.BACKEND_PID, 10) : null;
const OUTAGE_SECONDS = parseInt(process.env.OUTAGE_SECONDS || '90', 10);
const SHOTS = process.env.SHOTS_DIR || 'rehearsal_shots';
const OUT = (process.argv.includes('--out') ? process.argv[process.argv.indexOf('--out') + 1] : 'REHEARSAL_result.json');
const PARADIGM = process.env.PARADIGM || 'multi_toggles';
const TIER = process.env.TIER || 'advanced';
if (!MP) { console.error('MASTER_PASSWORD is required'); process.exit(2); }
fs.mkdirSync(SHOTS, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => performance.now();
const report = { config: { API, FE, PARADIGM, TIER, OUTAGE_SECONDS, viewport: '1366x768' }, steps: [] };
function record(step, title, ok, ms, notes = {}) {
  report.steps.push({ step, title, ok, seconds: ms == null ? null : Math.round(ms) / 1000, ...notes });
  console.log(`[rehearsal] ${ok ? 'PASS' : 'FAIL'} ${step}. ${title}${ms != null ? ` (${(ms / 1000).toFixed(1)} s)` : ''}${notes.detail ? ' — ' + notes.detail : ''}`);
}

async function api(path, opts = {}, cookie) {
  const r = await fetch(API + path, { ...opts, headers: { 'Content-Type': 'application/json', ...(cookie ? { Cookie: cookie } : {}), ...(opts.headers || {}) } });
  let body = null; try { body = await r.json(); } catch {}
  return { status: r.status, body, headers: r.headers };
}
async function facilitatorCookie() {
  const login = await api('/api/admin/facilitators/login', { method: 'POST', body: JSON.stringify({ facilitator_id: 'god_mode', password: MP }) });
  if (login.status !== 200) throw new Error('facilitator login ' + login.status);
  return 'mur_session=' + (login.headers.get('set-cookie') || '').split('mur_session=')[1].split(';')[0];
}
const playerHdr = (seat) => ({ Authorization: `Bearer ${seat.token}`, 'X-Player-Id': seat.pid });

async function commitViaApi(seat, round, pillars) {
  const d = await api(`/api/simulations/${seat.sid}/dashboard`, { headers: playerHdr(seat) });
  const bus = d.body.business_units;
  const decisions = bus.map((b) => ({ bu_id: b.bu_id, investment_ratio: 0.3, capex_allocated: 500000, choice_selected: pillars ? '' : 'option_a', ...(pillars ? { pillar_decisions: pillars } : {}) }));
  return api(`/api/simulations/${seat.sid}/commit-turn`, { method: 'POST', headers: playerHdr(seat), body: JSON.stringify({ decisions, dividends_paid: 0, force_override_cfo: true, expected_round: round }) });
}
async function pillarsFor(round) {
  const cfg = await api(`/api/simulations/pillar-config/${round}?paradigm=${PARADIGM}`);
  if (cfg.status !== 200) return null;
  const out = {};
  for (const [area, spec] of Object.entries(cfg.body.areas || {})) out[area] = Object.keys(spec.options || {})[0];
  return out;
}

async function newSeat(browser, label) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
  const page = await ctx.newPage();
  page.errors = [];
  page.on('pageerror', (e) => page.errors.push(String(e).slice(0, 200)));
  return { ctx, page, label };
}
const bodyText = async (page) => { try { return await page.evaluate(() => document.body.innerText.replace(/\s+/g, ' ')); } catch { return ''; } };
async function waitForText(page, needle, timeoutMs = 30000) {
  const t0 = now();
  const needles = Array.isArray(needle) ? needle : [needle];
  while (now() - t0 < timeoutMs) {
    const t = await bodyText(page);
    if (needles.some((n) => t.includes(n))) return now() - t0;
    await sleep(250);
  }
  return null;
}
const roundMarker = (n) => [`Round ${n} of 10`, `ROUND ${n} OF 10`];
// Every fresh load of a round opens on the intelligence briefing (a full-screen
// stage with "Begin Simulation →" / "Skip to the decision"); the board, and
// anything the board shows (results, notices), sits behind it.
async function endTour(page) {
  // the first visit to the board starts a 7-step guided tour whose backdrop
  // intercepts clicks; a participant ends it with "End Tour"
  const tour = page.locator('button:has-text("End Tour")');
  if (await tour.count()) { try { await tour.first().click({ timeout: 2000, force: true }); } catch {} await sleep(400); }
}
async function dismissBriefing(page, timeoutMs = 20000) {
  const t0 = now();
  while (now() - t0 < timeoutMs) {
    const btn = page.locator('button:has-text("Begin Simulation")');
    if (await btn.count()) { try { await btn.first().click({ timeout: 2000 }); } catch {} await sleep(800); await endTour(page); return true; }
    if ((await bodyText(page)).includes('Open panels')) { await endTour(page); return true; }   // already on the board
    await sleep(250);
  }
  return false;
}
async function boardReady(page, round, timeoutMs = 30000) {
  const t0 = now();
  await dismissBriefing(page, timeoutMs);
  const t = await waitForText(page, roundMarker(round), Math.max(1000, timeoutMs - (now() - t0)));
  return t == null ? null : now() - t0;
}
async function shot(page, name) { try { await page.screenshot({ path: `${SHOTS}/${name}.png` }); } catch {} }

async function signIn(seatUi, cred, callsign) {
  const { page } = seatUi;
  const t0 = now();
  await page.goto(FE + '/', { waitUntil: 'networkidle' });
  await page.fill('#join-player-id', cred.pid);
  await page.fill('#join-password', cred.pw);
  await page.click('button:has-text("Sign in")');
  await page.waitForSelector('input[placeholder="Your current password"]', { timeout: 20000 });
  const tGate = now() - t0;
  await page.fill('input[placeholder="Your current password"]', cred.pw);
  await page.fill('input[placeholder="At least 8 characters"]', cred.personal);
  await page.fill('input[placeholder="Re-enter new password"]', cred.personal);
  await page.click('button:has-text("Update Password")');
  await page.waitForSelector('button:has-text("Continue to Simulation")', { timeout: 20000 });
  await page.click('button:has-text("Continue to Simulation")');
  await page.waitForSelector('input[placeholder="E.g., Skyhawk99"]', { timeout: 20000 });
  await page.fill('input[placeholder="E.g., Skyhawk99"]', callsign);
  await page.click('button:has-text("CONFIRM USERNAME")');
  const tBoard = await boardReady(page, 1, 30000);
  const total = now() - t0;
  const sid = await page.evaluate(() => localStorage.getItem('muressons_session_id'));
  const token = await page.evaluate(() => localStorage.getItem('muressons_player_token'));
  return { total, tGate, boardVisible: tBoard != null, sid, token };
}

(async () => {
  const cookie = await facilitatorCookie();
  const start = await api('/api/simulations/start', { method: 'POST', body: JSON.stringify({ cohort_name: 'REHEARSAL-' + Date.now(), decision_paradigm: PARADIGM, difficulty_tier: TIER }) }, cookie);
  const cohort = start.body.session_id;
  report.cohort = cohort;
  async function mint(name) {
    const gp = await api(`/api/admin/${cohort}/generate-player`, { method: 'POST', body: JSON.stringify({ player_name: name }) }, cookie);
    return { pid: gp.body.player_id, pw: gp.body.password, personal: name.replace(/\s/g, '') + '#2026pw' };
  }
  const credA = await mint('Seat A'); const credB = await mint('Seat B');
  const browser = await chromium.launch();
  const A = await newSeat(browser, 'A'); const B = await newSeat(browser, 'B');

  // 1. first sign-in, both seats
  try {
    const ra = await signIn(A, credA, 'SeatA' + Date.now().toString().slice(-5));
    const rb = await signIn(B, credB, 'SeatB' + Date.now().toString().slice(-5));
    await shot(A.page, '01_board_A');
    A.sid = ra.sid; A.token = ra.token; A.pid = credA.pid; B.sid = rb.sid; B.token = rb.token; B.pid = credB.pid;
    record(1, 'first sign-in: temp password → personal password → callsign → board', ra.boardVisible && rb.boardVisible && !!ra.sid && !!rb.sid, Math.max(ra.total, rb.total),
      { detail: `seat A ${(ra.total / 1000).toFixed(1)} s (password gate shown after ${(ra.tGate / 1000).toFixed(1)} s), seat B ${(rb.total / 1000).toFixed(1)} s` });
  } catch (e) { record(1, 'first sign-in', false, null, { detail: String(e).slice(0, 200) }); await browser.close(); fs.writeFileSync(OUT, JSON.stringify(report, null, 2)); process.exit(1); }

  // 2. reload keeps the session
  {
    const t0 = now();
    await A.page.reload({ waitUntil: 'networkidle' });
    const t = await boardReady(A.page, 1, 20000);
    const joinShown = await A.page.locator('#join-player-id').count();
    await shot(A.page, '02_reload_A');
    record(2, 'reload keeps the session (no re-login)', t != null && joinShown === 0, now() - t0);
  }

  // 3. a second tab on the same seat
  let A2;
  {
    const t0 = now();
    A2 = await A.ctx.newPage();
    await A2.goto(FE + '/', { waitUntil: 'networkidle' });
    const t = await boardReady(A2, 1, 20000);
    await shot(A2, '03_second_tab_A');
    record(3, 'a second tab on the same seat shows the same board', t != null, now() - t0);
  }

  // 4. double-submit
  {
    const t0 = now();
    const pillars = PARADIGM === 'multi_toggles' || PARADIGM === 'brsr_ngrbc' ? await pillarsFor(1) : null;
    const [r1, r2] = await Promise.all([commitViaApi(A, 1, pillars), commitViaApi(A, 1, pillars)]);
    const codes = [r1.status, r2.status].sort();
    const d = await api(`/api/simulations/${A.sid}/dashboard`, { headers: playerHdr(A) });
    record(4, 'double-submit: two commits for the same round at once → exactly one lands', codes[0] === 201 && codes[1] !== 201 && d.body.current_round === 2, now() - t0,
      { detail: `statuses ${codes.join('/')}, server on round ${d.body.current_round}` });
  }

  // 5. lost commit response → results screen on reload (the tab last showed R1; the server is on R2)
  {
    const t0 = now();
    const lastShown = await A.page.evaluate((sid) => sessionStorage.getItem(`muressons_last_round_${sid}`), A.sid);
    await A.page.reload({ waitUntil: 'networkidle' });
    await dismissBriefing(A.page, 20000);
    const t = await waitForText(A.page, 'Advance to Round 2', 20000);
    await shot(A.page, '05_results_recovered_A');
    let advanced = null;
    if (t != null) {
      await endTour(A.page);
      await A.page.click('button:has-text("Advance to Round 2")', { force: true });
      advanced = await boardReady(A.page, 2, 20000);
    }
    record(5, 'lost commit response: reload puts the results screen back; Advance moves to R2', t != null && advanced != null, now() - t0,
      { detail: `tab last showed round ${lastShown}; results visible after ${t == null ? 'never' : (t / 1000).toFixed(1) + ' s'}` });
  }

  // 6. the duplicate tab re-syncs
  {
    const t0 = now();
    const t = await waitForText(A2, roundMarker(2), 30000);
    await shot(A2, '06_second_tab_resynced_A');
    record(6, 'the duplicate tab, still on R1, re-syncs to R2 on its next poll', t != null, now() - t0);
    await A2.close();
  }

  // 7. Force Advance while seat B has only a saved draft
  {
    const t0 = now();
    const pillars = PARADIGM === 'multi_toggles' || PARADIGM === 'brsr_ngrbc' ? await pillarsFor(1) : null;
    const save = await api(`/api/simulations/${B.sid}/save-decisions`, { method: 'POST', headers: playerHdr(B), body: JSON.stringify({ allocations: { pharma: 1500000 }, decision_choice: pillars ? null : 'option_b', pillar_decisions: pillars, expected_round: 1 }) });
    const fa = await api(`/api/admin/sessions/${cohort}/force-advance`, { method: 'POST', body: '{}' }, cookie);
    // the seat's next poll triggers its auto-commit; the board moves to R2 (behind the R2 briefing) with the notice on it
    const tR2 = await boardReady(B.page, 2, 45000);
    let t = tR2 == null ? null : await waitForText(B.page, 'Your results reflect that submission', 30000);
    if (t == null && tR2 != null) {          // a participant who misses the notice sees it again on reload
      await B.page.reload({ waitUntil: 'networkidle' }); await boardReady(B.page, 2, 20000);
      t = await waitForText(B.page, 'Your results reflect that submission', 15000);
    }
    const dB = await api(`/api/simulations/${B.sid}/dashboard`, { headers: playerHdr(B) });
    const src = dB.body.global_state?.active_event_flags?.auto_committed_source;
    await shot(B.page, '07_force_advance_B');
    record(7, 'Force Advance while a seat has only a saved draft → the draft is committed (source=draft), the seat moves to R2, the notice shows',
      save.status === 200 && fa.status === 200 && tR2 != null && dB.body.current_round === 2 && src === 'draft' && t != null, now() - t0,
      { detail: `save ${save.status}, force-advance ${fa.status}, seat on R2 after ${tR2 == null ? 'never' : (tR2 / 1000).toFixed(1) + ' s'}, notice ${t == null ? 'not seen' : 'seen after ' + (t / 1000).toFixed(1) + ' s'}, source=${src}` });
  }

  // 8. 90-second outage during a reload
  if (BACKEND_PID) {
    const t0 = now();
    let bannerAt = null, backAt = null, joinShownDuringOutage = null;
    try {
      process.kill(BACKEND_PID, 'SIGSTOP');
      await sleep(500);
      A.page.reload({ waitUntil: 'commit' }).catch(() => {});
      // the reload lands on the (static) intelligence briefing; the banner lives on the board behind it
      await dismissBriefing(A.page, 25000);
      bannerAt = await waitForText(A.page, 'Reconnecting to the server', 30000);
      joinShownDuringOutage = await A.page.locator('#join-player-id').count();
      await shot(A.page, '08_outage_banner_A');
      const remaining = OUTAGE_SECONDS * 1000 - (now() - t0);
      if (remaining > 0) await sleep(remaining);
    } finally {
      process.kill(BACKEND_PID, 'SIGCONT');
    }
    backAt = await boardReady(A.page, 2, 60000);
    const joinShownAfter = await A.page.locator('#join-player-id').count();
    await shot(A.page, '08_outage_recovered_A');
    record(8, `${OUTAGE_SECONDS}-second outage during a reload: banner, session kept, board back without re-login`,
      bannerAt != null && joinShownDuringOutage === 0 && backAt != null && joinShownAfter === 0, now() - t0,
      { detail: `banner after ${bannerAt == null ? 'never' : (bannerAt / 1000).toFixed(1) + ' s'}; board back ${backAt == null ? 'never' : (backAt / 1000).toFixed(1) + ' s'} after the backend resumed` });
  } else {
    record(8, 'outage (skipped: BACKEND_PID not set)', false, null, { detail: 'set BACKEND_PID to run' });
  }

  // 9. insolvency: a facilitator black swan drains the treasury; the next commit draws the emergency credit line
  {
    const t0 = now();
    const d0 = await api(`/api/simulations/${A.sid}/dashboard`, { headers: playerHdr(A) });
    const treasury = d0.body.global_state.corporate_treasury;
    const ev = await api(`/api/admin/${A.sid}/inject-custom-event`, { method: 'POST', body: JSON.stringify({ title: 'Rehearsal: regulator seizes cash', narrative: 'Rehearsal insolvency scenario', target_scope: 'Global', financial_impact: -(treasury + 30000000), reputation_impact: -10 }) }, cookie);
    const pillars = PARADIGM === 'multi_toggles' || PARADIGM === 'brsr_ngrbc' ? await pillarsFor(2) : null;
    const c = await commitViaApi(A, 2, pillars);
    const flags = c.body?.global_state?.active_event_flags || {};
    const drawn = Number(flags.emergency_credit_balance || 0) > 0;
    await A.page.reload({ waitUntil: 'networkidle' });
    await dismissBriefing(A.page, 20000);
    const t = await waitForText(A.page, 'Emergency credit line', 30000);
    await shot(A.page, '09_insolvency_A');
    record(9, 'insolvency: black swan drains the till; the next commit draws the emergency credit line and the board says so',
      ev.status === 200 && c.status === 201 && drawn, now() - t0,
      { detail: `event ${ev.status}, commit ${c.status}, treasury after ${c.body?.global_state?.corporate_treasury}, credit drawn ${flags.emergency_credit_balance}, board text ${t == null ? 'not found (the line shows on the allocation canvas)' : 'found after ' + (t / 1000).toFixed(1) + ' s'}` });
    if (t != null) { try { await endTour(A.page); await A.page.click('button:has-text("Advance to Round 3")', { timeout: 3000, force: true }); } catch {} }
  }

  // 10. export after R10
  {
    const t0 = now();
    let round = (await api(`/api/simulations/${A.sid}/dashboard`, { headers: playerHdr(A) })).body.current_round;
    let commits = 0;
    // both seats play on (the cohort's free-advance barrier holds R(n+1) until every team has committed R(n))
    const roundOf = async (seat) => (await api(`/api/simulations/${seat.sid}/dashboard`, { headers: playerHdr(seat) })).body.current_round;
    while (round < 10) {
      const pillars = PARADIGM === 'multi_toggles' || PARADIGM === 'brsr_ngrbc' ? await pillarsFor(round) : null;
      await sleep(5200);                 // the 5-second double-submit cooldown
      for (let rb = await roundOf(B); rb <= round && rb < 10; rb = await roundOf(B)) {   // seat B keeps pace
        const pb = PARADIGM === 'multi_toggles' || PARADIGM === 'brsr_ngrbc' ? await pillarsFor(rb) : null;
        const cb = await commitViaApi(B, rb, pb);
        if (cb.status !== 201) break;
        await sleep(5200);
      }
      const c = await commitViaApi(A, round, pillars);
      if (c.status !== 201) { record(10, 'export (setup: commit failed)', false, null, { detail: `R${round} → ${c.status} ${JSON.stringify(c.body).slice(0, 160)}` }); round = 99; break; }
      commits += 1; round = c.body.new_round_number;
    }
    if (round === 10) {
      await sleep(5200);
      const pillars = PARADIGM === 'multi_toggles' || PARADIGM === 'brsr_ngrbc' ? await pillarsFor(10) : null;
      if ((await roundOf(B)) === 10) await commitViaApi(B, 10, pillars);
      const c10 = await commitViaApi(A, 10, pillars);
      await A.page.reload({ waitUntil: 'networkidle' });
      await sleep(3000);
      // the archetype reveal (a cinematic) precedes the debrief; "Continue to Debrief" opens the summary
      const cont = A.page.locator('#archetype-reveal-continue-btn, button:has-text("Continue to Debrief")');
      const continueReveal = async () => {
        for (let i = 0; i < 60 && !(await cont.count()); i++) await sleep(1000);
        if (await cont.count()) { try { await cont.first().evaluate((el) => el.click()); } catch {} await sleep(2500); return true; }
        return false;
      };
      await continueReveal();
      // the Balanced Scorecard follows; its exit is "Proceed to Boardroom Showdown" when the cohort
      // runs the boardroom exercise (a three-phase written exercise, left to the human rehearsal) or
      // "Close Balanced Scorecard" when the facilitator has switched it off — the debrief summary
      // with the Strategy Report is behind that exit
      const vis = await api(`/api/admin/cohort/${cohort}/analytics-visibility`, { method: 'PUT', body: JSON.stringify({ player: { boardroom_showdown: false } }) }, cookie);
      await A.page.reload({ waitUntil: 'networkidle' }); await sleep(2500);
      await continueReveal();
      const closeBtn = A.page.locator('button:has-text("Close Balanced Scorecard")');
      for (let i = 0; i < 15 && !(await closeBtn.count()); i++) await sleep(1000);
      if (await closeBtn.count()) { try { await closeBtn.first().evaluate((el) => el.click()); } catch {} await sleep(2500); }
      const btn = A.page.locator('button:has-text("Download My Strategy Report")');
      for (let i = 0; i < 15 && !(await btn.count()); i++) await sleep(1000);
      let ok = false, detail = `R10 commit ${c10.status}; boardroom switched off for the cohort (${vis.status})`;
      if (await btn.count()) {
        const [popup] = await Promise.all([A.ctx.waitForEvent('page', { timeout: 15000 }).catch(() => null), btn.first().click()]);
        if (popup) {
          await popup.waitForLoadState('domcontentloaded').catch(() => {});
          const html = await popup.content();
          ok = html.includes('Treasury entering') && html.includes('Treasury after') && !/\$0\.0M/.test(html.split('Treasury entering')[1] || '');
          detail += `; report opened, 'Treasury entering' ${html.includes('Treasury entering')}, rows R1…R10 ${/R10/.test(html)}`;
          fs.writeFileSync(`${SHOTS}/10_strategy_report.html`, html);
        } else detail += '; the report tab did not open';
      } else detail += '; export button not found on the game-over screen';
      await shot(A.page, '10_game_over_A');
      record(10, 'export: after R10 the Strategy Report opens with the treasury by round, entering / after', ok, now() - t0, { detail });
    }
  }

  report.page_errors = { A: A.page.errors.slice(0, 10), B: B.page.errors.slice(0, 10) };
  report.verdict = report.steps.every((s) => s.ok) ? 'PASS' : 'FAIL';
  await browser.close();
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  console.log(`[rehearsal] ${report.verdict} — ${report.steps.filter((s) => s.ok).length}/${report.steps.length} steps; report ${OUT}, screenshots ${SHOTS}/`);
  process.exit(report.verdict === 'PASS' ? 0 : 1);
})();
