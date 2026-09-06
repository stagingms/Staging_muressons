'use client';
import { Suspense, useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { moneyM } from '../../utils/format';
import { useCurrency } from '../../contexts/CurrencyContext';

/**
 * Projector view (UX audit §9 — projector view).
 *
 * A full-screen, read-only board a facilitator puts on the room's big screen
 * during a live simulation round. It polls the existing cohort-pulse endpoint
 * (GET /api/admin/cohort-pulse/{cohortId}) every 5 seconds and renders, in
 * room-legible type (readable from ~10 metres):
 *   1. the target round + a commit tally (one dot per player),
 *   2. pacing status — live countdown to the next unlock, or "facilitator
 *      advances", plus an amber banner when players have diverged in rounds,
 *   3. the top 5 teams by treasury,
 *   4. a rotating footer of active traps / tipping points.
 * It reads game state only — no writes, no game mutations. If a fetch fails
 * the board keeps the last good data and flips its corner stamp from
 * "LIVE" to an amber "STALE" — it never renders wrong data silently.
 *
 * Open on the room screen:  /admin/projector?cohort=<cohortId>
 * (also accepts ?session=<id>; with neither, shows a large-type chooser).
 */

const API = process.env.NEXT_PUBLIC_API_URL || '';
// SEAM-14 (Wave 3): the cohort's symbol and rate, not a literal "$" at rate 1
const fmtM = (v) => moneyM(Number(v) || 0);
const clock = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

/* ---------- cohort chooser (no ?cohort= in the URL) ---------- */
function CohortChooser() {
  const [cohorts, setCohorts] = useState(null); // null = loading
  const [error, setError] = useState(false);
  useEffect(() => {
    let alive = true;
    fetch(`${API}/api/admin/sessions`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('http'))))
      .then((d) => { if (alive) setCohorts((d.sessions || []).filter((s) => !s.player_id)); })
      .catch(() => { if (alive) setError(true); });
    return () => { alive = false; };
  }, []);
  return (
    <div style={{ ...S.page, ...S.centerCol }}>
      <div style={{ fontSize: 48, fontWeight: 900, letterSpacing: '0.04em', marginBottom: 12 }}>PROJECTOR VIEW</div>
      <div style={{ fontSize: 26, color: '#94a3b8', marginBottom: 36 }}>Choose the cohort to project on this screen.</div>
      {error ? (
        <div style={{ fontSize: 28, color: '#fbbf24' }}>⚠ Could not load cohorts — sign in on the Facilitator Dashboard, then reload.</div>
      ) : cohorts === null ? (
        <div style={{ fontSize: 28, color: '#94a3b8' }}>Loading cohorts…</div>
      ) : cohorts.length === 0 ? (
        <div style={{ fontSize: 28, color: '#94a3b8' }}>No cohorts found.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, width: 'min(720px, 90vw)' }}>
          {cohorts.map((s) => (
            <a key={s.session_id} href={`?cohort=${encodeURIComponent(s.session_id)}`} style={S.chooserBtn}>
              {s.cohort_name || `Cohort ${String(s.session_id).slice(0, 8)}`}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- live board ---------- */
function ProjectorBoard({ cohortId }) {
  const { loadSessionCurrency } = useCurrency();
  useEffect(() => { if (cohortId) loadSessionCurrency(cohortId); }, [cohortId, loadSessionCurrency]);   // SEAM-14
  const [data, setData] = useState(null);       // last GOOD payload — kept on failure
  const [stale, setStale] = useState(false);
  const [lastOk, setLastOk] = useState(null);   // Date of last successful fetch
  const [now, setNow] = useState(() => Date.now());
  const [footIdx, setFootIdx] = useState(0);
  const pollRef = useRef(null);

  const load = useCallback(() => {
    fetch(`${API}/api/admin/cohort-pulse/${encodeURIComponent(cohortId)}`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('http'))))
      .then((d) => { setData(d); setStale(false); setLastOk(new Date()); })
      .catch(() => setStale(true)); // keep last good data on screen, stamped STALE
  }, [cohortId]);

  useEffect(() => {
    load();
    pollRef.current = setInterval(load, 5000);
    return () => clearInterval(pollRef.current);
  }, [load]);

  // 1-second heartbeat for the countdown.
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const teams = useMemo(
    () => (data?.teams || []).filter((t) => t.is_cohort_shell !== true),
    [data]
  );
  const cp = data?.commit_progress || {};
  const pacing = data?.pacing || {};
  const targetRound = cp.target_round;
  const committed = Number(cp.committed_count) || 0;
  const totalPlayers = Number(cp.total_players) || 0;
  const autoCommitted = Number(cp.auto_committed_count) || 0;

  const top5 = useMemo(
    () => [...teams].sort((a, b) => (b.current?.treasury || 0) - (a.current?.treasury || 0)).slice(0, 5),
    [teams]
  );

  // Footer rotation: union of active traps + tipping-point teams, every 8s.
  const footerItems = useMemo(() => {
    const traps = new Set();
    teams.forEach((t) => (t.current?.active_traps || []).forEach((s) => traps.add(String(s))));
    const items = [...traps];
    teams.forEach((t) => { if (t.tipping_point) items.push(`⚡ ${t.name}: tipping point active`); });
    return items;
  }, [teams]);
  useEffect(() => {
    if (footerItems.length < 2) { setFootIdx(0); return undefined; }
    const t = setInterval(() => setFootIdx((i) => (i + 1) % footerItems.length), 8000);
    return () => clearInterval(t);
  }, [footerItems.length]);

  // Countdown to the next unlock (client-side, per second).
  let countdown = null;
  if (pacing.next_unlock_at) {
    const ms = new Date(pacing.next_unlock_at).getTime() - now;
    if (Number.isFinite(ms) && ms > 0) {
      const s = Math.floor(ms / 1000);
      countdown = `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
    }
  }

  if (!data && !stale) return <div style={{ ...S.page, ...S.centerCol }}><div style={{ fontSize: 32, color: '#94a3b8' }}>Connecting to cohort…</div></div>;
  if (!data && stale) {
    return (
      <div style={{ ...S.page, ...S.centerCol }}>
        <div style={{ fontSize: 34, color: '#fbbf24' }}>⚠ No data yet — backend unreachable or you are signed out.</div>
        <div style={{ fontSize: 24, color: '#94a3b8', marginTop: 14 }}>Sign in on the Facilitator Dashboard in another tab. Retrying every 5 seconds…</div>
      </div>
    );
  }

  const dots = Array.from({ length: Math.min(totalPlayers, 60) }, (_, i) => i < committed);

  return (
    <div style={S.page}>
      {/* Freshness stamp — never lie about data age. */}
      <div style={{ ...S.stamp, color: stale ? '#fbbf24' : '#94a3b8' }}>
        {stale ? '⚠ STALE · last data ' : 'LIVE · updated '}{lastOk ? clock(lastOk) : '—'}
      </div>

      {/* ROW 1 — round numeral + commit tally */}
      <div style={S.row1}>
        <div>
          <div style={S.roundLabel}>ROUND</div>
          <div style={S.roundNum}>{targetRound ?? '—'}</div>
        </div>
        <div style={{ flex: 1, minWidth: 320 }}>
          <div style={S.dotsWrap}>
            {dots.map((filled, i) => (
              <span key={i} style={{ ...S.dot, ...(filled ? S.dotOn : S.dotOff) }} aria-hidden="true" />
            ))}
          </div>
          <div style={S.tallyText}>
            <span style={{ color: '#4ade80' }}>✓</span> {committed} of {totalPlayers} committed
            {autoCommitted > 0 && <span style={{ fontSize: 26, color: '#94a3b8' }}> ({autoCommitted} auto)</span>}
          </div>
        </div>
      </div>

      {/* ROW 2 — pacing */}
      <div style={S.row2}>
        {countdown ? (
          <div style={{ fontSize: 44, fontWeight: 800 }}>Next round opens in <span style={{ fontVariantNumeric: 'tabular-nums', color: '#4ade80' }}>{countdown}</span></div>
        ) : pacing.mode === 'manual' ? (
          <div style={{ fontSize: 40, fontWeight: 700, color: '#94a3b8' }}>Facilitator advances the round</div>
        ) : null}
        {cp.diverged === true && (
          <div style={S.divergedBanner}>
            ⚠ Players are at different rounds (R{cp.min_round}–R{targetRound})
          </div>
        )}
      </div>

      {/* ROW 3 — top 5 by treasury */}
      <div style={S.board}>
        <div style={{ ...S.boardRow, ...S.boardHead }}>
          <span>#</span><span>TEAM</span><span style={S.num}>TREASURY</span><span style={S.num}>REPUTATION</span>
        </div>
        {top5.length === 0 ? (
          <div style={{ fontSize: 28, color: '#94a3b8', padding: '18px 24px' }}>No teams yet.</div>
        ) : top5.map((t, i) => (
          <div key={t.session_id || i} style={S.boardRow}>
            <span style={{ fontWeight: 900 }}>{i + 1}</span>
            <span style={{ fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.name || 'Team'}</span>
            <span style={{ ...S.num, color: '#4ade80', fontWeight: 800 }}>✓ {fmtM(t.current?.treasury)}</span>
            <span style={{ ...S.num, fontWeight: 700 }}>{Math.round(t.current?.reputation ?? 0)}</span>
          </div>
        ))}
      </div>

      {/* ROW 4 — rotating footer (plain swap; no animation, reduced-motion safe) */}
      <div style={S.footer}>
        {footerItems.length > 0
          ? <span style={{ color: '#fbbf24', fontWeight: 700 }}>⚠ {footerItems[footIdx % footerItems.length]}</span>
          : <span style={{ color: '#94a3b8' }}>{data?.cohort_name || teams[0]?.name || `Cohort ${String(cohortId).slice(0, 8)}`}</span>}
      </div>
    </div>
  );
}

/* ---------- entry — Next requires Suspense around useSearchParams ---------- */
function ProjectorInner() {
  const params = useSearchParams();
  const cohortId = params.get('cohort') || params.get('session') || '';
  if (!cohortId) return <CohortChooser />;
  return <ProjectorBoard cohortId={cohortId} />;
}

export default function ProjectorPage() {
  return (
    <Suspense fallback={<div style={{ ...S.page, ...S.centerCol }}><div style={{ fontSize: 28, color: '#94a3b8' }}>Loading…</div></div>}>
      <ProjectorInner />
    </Suspense>
  );
}

/* ---------- styles — inline objects only; contrast ≥ 7:1 on #0a0e1a ---------- */
const S = {
  page: {
    minHeight: '100vh', background: '#0a0e1a', color: '#f1f5f9', padding: '48px 64px 32px',
    fontFamily: 'var(--font-sans, system-ui, sans-serif)', fontSize: 24,
    display: 'flex', flexDirection: 'column', gap: 36, position: 'relative',
  },
  centerCol: { alignItems: 'center', justifyContent: 'center', textAlign: 'center' },
  stamp: { position: 'absolute', top: 16, right: 24, fontSize: 24, fontWeight: 700, letterSpacing: '0.06em', fontVariantNumeric: 'tabular-nums' },
  chooserBtn: {
    display: 'block', padding: '22px 32px', fontSize: 32, fontWeight: 800, textAlign: 'center',
    color: '#f1f5f9', textDecoration: 'none', borderRadius: 16,
    background: 'rgba(148,163,184,0.10)', border: '2px solid rgba(148,163,184,0.35)',
  },
  row1: { display: 'flex', alignItems: 'center', gap: 64, flexWrap: 'wrap' },
  roundLabel: { fontSize: 34, fontWeight: 800, letterSpacing: '0.3em', color: '#94a3b8' },
  roundNum: { fontSize: 150, fontWeight: 900, lineHeight: 1, fontVariantNumeric: 'tabular-nums' },
  dotsWrap: { display: 'flex', flexWrap: 'wrap', gap: 14, marginBottom: 18 },
  dot: { width: 34, height: 34, borderRadius: '50%', display: 'inline-block' },
  dotOn: { background: '#4ade80', border: '3px solid #4ade80' },
  dotOff: { background: 'transparent', border: '3px solid #94a3b8' },
  tallyText: { fontSize: 42, fontWeight: 800 },
  row2: { display: 'flex', flexDirection: 'column', gap: 18 },
  divergedBanner: {
    padding: '16px 28px', borderRadius: 14, fontSize: 34, fontWeight: 800,
    background: '#fbbf24', color: '#0a0e1a', alignSelf: 'flex-start',
  },
  board: { display: 'flex', flexDirection: 'column', gap: 6 },
  boardRow: {
    display: 'grid', gridTemplateColumns: '80px 1fr 300px 260px', alignItems: 'center', gap: 20,
    fontSize: 30, padding: '14px 24px', borderRadius: 12, background: 'rgba(148,163,184,0.07)',
  },
  boardHead: { fontSize: 24, fontWeight: 800, letterSpacing: '0.12em', color: '#94a3b8', background: 'transparent', paddingBottom: 4 },
  num: { textAlign: 'right', fontVariantNumeric: 'tabular-nums' },
  footer: { marginTop: 'auto', fontSize: 30, minHeight: 44, textAlign: 'center' },
};
