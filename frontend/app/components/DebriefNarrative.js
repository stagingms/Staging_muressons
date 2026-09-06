/**
 * DebriefNarrative — "the debrief writes itself" (UX audit §9 / item #12).
 *
 * Facilitator-facing narrative assembled from the read-only
 * GET /api/admin/debrief-narrative/{cohortId} endpoint. Each section is a
 * card written in declarative sentences the facilitator can read aloud,
 * with a "⛶ Project" button that expands it into a fullscreen overlay
 * (≥28px type) for the classroom screen.
 *
 * Props: { sessionId } — the cohort id. Pure presentation; no writes.
 */
'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import Dialog from './Dialog';
import { moneyM } from '../utils/format';
import { useCurrency } from '../contexts/CurrencyContext';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// SEAM-14 (audit 2026-09-04, Wave 3): the cohort's currency symbol AND rate,
// from the one source every player surface uses — this panel used to print a
// literal "$" at rate 1 while the room's cockpits showed ₹ at 83.
const money = (v) => moneyM(v || 0);
const signedMoney = (v) => `${(v || 0) >= 0 ? '+' : ''}${moneyM(v || 0)}`;
const signedRep = (v) => `${v >= 0 ? '+' : ''}${(v || 0).toFixed(1)}`;

const C = {
  cardBg: '#101625', border: '#2a3550', text: '#e6ebf5', dim: '#9fb0cc',
  accent: '#7fd4a8', warn: '#f0b45f', bad: '#f08f8f',
};

const styles = {
  wrap: { display: 'flex', flexDirection: 'column', gap: 16, color: C.text },
  card: { background: C.cardBg, border: `1px solid ${C.border}`, borderRadius: 10, padding: '16px 18px' },
  cardHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  h3: { margin: 0, fontSize: 16, fontWeight: 700, color: C.text },
  projectBtn: {
    background: 'transparent', color: C.dim, border: `1px solid ${C.border}`, borderRadius: 6,
    padding: '6px 12px', cursor: 'pointer', fontSize: 13, minHeight: 32,
  },
  overlay: {
    position: 'fixed', inset: 0, zIndex: 9000, background: '#0a0e1a', color: C.text,
    padding: '48px 6vw', overflowY: 'auto', fontSize: 28, lineHeight: 1.5,
  },
  closeBtn: {
    position: 'fixed', top: 20, right: 24, zIndex: 9001, minWidth: 44, minHeight: 44,
    background: '#1a2338', color: C.text, border: `1px solid ${C.border}`, borderRadius: 8,
    fontSize: 22, cursor: 'pointer',
  },
  row: { padding: '6px 0', borderBottom: `1px solid ${C.border}` },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 'inherit' },
  th: { textAlign: 'left', color: C.dim, fontWeight: 600, padding: '4px 10px 4px 0', borderBottom: `1px solid ${C.border}` },
  td: { padding: '6px 10px 6px 0', borderBottom: `1px solid ${C.border}` },
  empty: { color: C.dim, fontStyle: 'italic' },
  quote: { color: C.accent, fontStyle: 'italic' },
  retryBtn: {
    background: '#1a2338', color: C.text, border: `1px solid ${C.border}`, borderRadius: 6,
    padding: '10px 18px', cursor: 'pointer', fontSize: 14, minHeight: 44, marginTop: 10,
  },
};

/** Section card with a fullscreen "Project" mode for the classroom screen. */
function SectionCard({ title, children }) {
  const [projected, setProjected] = useState(false);
  const closeRef = useRef(null);
  const prevFocusRef = useRef(null);

  const close = useCallback(() => {
    setProjected(false);
    if (prevFocusRef.current) prevFocusRef.current.focus();
  }, []);

  // A11Y-F5: Escape, initial focus, focus trap and focus restore now come from
  // the shared Dialog primitive — this component's partial hand-rolled version
  // (focus + Escape, no trap) is gone. `close()` still restores focus itself
  // because the projecting button lives outside the dialog.

  return (
    <section style={styles.card}>
      <div style={styles.cardHead}>
        <h3 style={styles.h3}>{title}</h3>
        <button
          type="button"
          style={styles.projectBtn}
          onClick={(e) => { prevFocusRef.current = e.currentTarget; setProjected(true); }}
          aria-label={`Project section: ${title}`}
        >
          ⛶ Project
        </button>
      </div>
      {/* A11Y-F5: children render ONCE. Previously the inline copy and the
          projected copy both existed, so every table row was announced twice.
          aria-hidden would have masked it; not rendering it is the fix. */}
      {!projected && children}
      {/* A11Y-F5 (WCAG 4.1.2, 2.4.3): this declared aria-modal="true" while
          leaving 5 focusable controls outside it in the tab order, and rendered
          {children} a SECOND time — so every table row was announced twice.
          Now it uses the shared Dialog primitive (focus trap, Escape, focus
          restore, scroll lock), and the card behind is aria-hidden while
          projected so the duplicate content is not double-announced. */}
      {projected && (
        <Dialog
          onClose={close}
          label={title}
          className={undefined}
          style={styles.overlay}
          initialFocusRef={closeRef}
          closeOnBackdrop={false}
        >
          <button type="button" ref={closeRef} style={styles.closeBtn} onClick={close} aria-label="Close projection">
            ✕
          </button>
          <h2 style={{ margin: '0 0 24px', fontSize: 36 }}>{title}</h2>
          {children}
        </Dialog>
      )}
    </section>
  );
}

export default function DebriefNarrative({ sessionId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { loadSessionCurrency } = useCurrency();
  useEffect(() => { if (sessionId) loadSessionCurrency(sessionId); }, [sessionId, loadSessionCurrency]);   // SEAM-14

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/admin/debrief-narrative/${sessionId}`, { credentials: 'include' });
      if (!res.ok) {
        let detail = `Request failed (HTTP ${res.status}).`;
        try { detail = (await res.json()).detail || detail; } catch { /* keep default */ }
        throw new Error(detail);
      }
      setData(await res.json());
    } catch (e) {
      setError(e.message || 'The debrief narrative could not be loaded.');
    }
    setLoading(false);
  }, [sessionId]);

  useEffect(() => { setData(null); load(); }, [load]);

  if (!sessionId) {
    return <div style={{ ...styles.card, ...styles.empty }}>Select a cohort to generate its debrief narrative.</div>;
  }
  if (loading && !data) {
    return (
      <div style={styles.card} aria-busy="true">
        <div style={{ color: C.dim, marginBottom: 12 }}>Assembling the story of this run…</div>
        {[80, 60, 70].map((w, i) => (
          <div key={i} style={{ height: 12, width: `${w}%`, background: '#1a2338', borderRadius: 4, marginBottom: 8 }} />
        ))}
      </div>
    );
  }
  if (error) {
    return (
      <div style={styles.card} role="alert">
        <div style={{ color: C.bad, fontWeight: 600 }}>Could not load the debrief narrative.</div>
        <div style={{ color: C.dim, marginTop: 6 }}>{error}</div>
        <button type="button" style={styles.retryBtn} onClick={load}>Retry</button>
      </div>
    );
  }
  if (!data) return null;

  const players = data.players || [];
  const ranking = data.ranking || [];
  const div = data.divergence_round;
  const coverage = data.prediction_coverage || { players_with_predictions: 0, total_players: 0 };

  // Sort turning points by scale-normalized magnitude (same convention as the
  // backend: treasury per $10M vs reputation points) so mixed metrics compare.
  const turningPoints = players
    .filter((p) => p.turning_point)
    .map((p) => ({ name: p.name, ...p.turning_point }))
    .sort((a, b) => {
      const mag = (t) => (t.metric === 'treasury' ? Math.abs(t.delta) / 10_000_000 : Math.abs(t.delta));
      return mag(b) - mag(a);
    });

  const flagged = players.filter((p) => (p.auto_committed_rounds || []).length > 0);
  const withPredictions = players.filter((p) => (p.predicted_vs_actual || []).length > 0);

  return (
    <div style={styles.wrap}>
      <div style={{ color: C.dim, fontSize: 13 }}>
        Debrief narrative for {data.cohort_name} — assembled from {data.generated_over_rounds} round
        {data.generated_over_rounds === 1 ? '' : 's'} of play. Read each card aloud, or project it.
      </div>

      <SectionCard title="The headline">
        {ranking.length === 0 ? (
          <div style={styles.empty}>No player rounds have been committed yet — the story starts once Round 1 is in.</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th} scope="col">Rank</th>
                <th style={styles.th} scope="col">Player</th>
                <th style={styles.th} scope="col">Final treasury</th>
                <th style={styles.th} scope="col">Reputation</th>
              </tr>
            </thead>
            <tbody>
              {ranking.map((r, i) => (
                <tr key={r.name + i}>
                  <td style={styles.td}>{i + 1}</td>
                  <td style={styles.td}>{r.name}</td>
                  <td style={styles.td}>{money(r.treasury)}</td>
                  <td style={styles.td}>{Math.round(r.reputation)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </SectionCard>

      <SectionCard title="Where the run split">
        {div ? (
          <p style={{ margin: 0 }}>
            Round {div.round}: the field split — {div.leader} pulled ahead of {div.laggard} by{' '}
            ${((div.treasury_spread || 0) / 1_000_000).toFixed(1)}M.
          </p>
        ) : (
          <div style={styles.empty}>The field never meaningfully diverged — fewer than two players share a comparable round.</div>
        )}
      </SectionCard>

      <SectionCard title="Turning points">
        {turningPoints.length === 0 ? (
          <div style={styles.empty}>No round-over-round swings yet — turning points appear after the second committed round.</div>
        ) : (
          turningPoints.map((t, i) => (
            <div key={t.name + i} style={styles.row}>
              R{t.round}: {t.name} — {t.metric} swung{' '}
              <span style={{ color: t.delta >= 0 ? C.accent : C.bad, fontWeight: 600 }}>
                {t.metric === 'treasury' ? signedMoney(t.delta) : signedRep(t.delta)}
              </span>
            </div>
          ))
        )}
      </SectionCard>

      <SectionCard title="Predicted vs actual">
        {coverage.players_with_predictions === 0 ? (
          <div style={styles.empty}>
            No predictions were captured this run. Players&apos; pre-commit predictions appear here once the
            prediction step is used.
          </div>
        ) : (
          withPredictions.map((p) => (
            <div key={p.session_id} style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>{p.name}</div>
              {p.predicted_vs_actual.map((pa) => (
                <div key={pa.round} style={styles.row}>
                  R{pa.round}: <span style={styles.quote}>&ldquo;{pa.prediction}&rdquo;</span>
                  {' — '}
                  {pa.actual && pa.actual.treasury_delta != null ? (
                    <>Treasury {signedMoney(pa.actual.treasury_delta)}, Reputation {signedRep(pa.actual.reputation_delta)}</>
                  ) : (
                    <span style={styles.empty}>outcome not yet measurable</span>
                  )}
                </div>
              ))}
            </div>
          ))
        )}
      </SectionCard>

      <SectionCard title="Flags for grading">
        {flagged.length === 0 ? (
          <p style={{ margin: 0, color: C.accent }}>Every round was played by its player — no auto-commits.</p>
        ) : (
          flagged.map((p) => (
            <div key={p.session_id} style={{ ...styles.row, color: C.warn }}>
              {p.name}: Round(s) {p.auto_committed_rounds.join(', ')} were auto-committed, not played.
            </div>
          ))
        )}
      </SectionCard>
    </div>
  );
}
