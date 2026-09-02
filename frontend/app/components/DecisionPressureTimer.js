/**
 * DecisionPressureTimer — WOW-11
 *
 * Enhanced countdown timer with competitive commit tracking:
 *   - Live "X of Y teams committed" badge (polls pacing endpoint)
 *   - Urgency visual states: green → amber → red
 *   - SVG progress ring showing time remaining
 *   - Auto-commit warning notification
 *
 * SAFETY: Pure presentation. Polls the existing /api/admin/sessions/{id}/pacing
 * endpoint for timer and commit data. Falls back silently if endpoint unavailable.
 *
 * Props:
 *   sessionId    — current session ID
 *   roundNumber  — current round
 *   isCommitted  — whether this team has committed
 *   globalState  — current global state
 */
'use client';
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import styles from './DecisionPressureTimer.module.css';
import { playerIdHeader } from '../hooks/useSimulation';

function formatTime(seconds) {
  if (seconds <= 0) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function urgencyLevel(secondsLeft, totalSeconds) {
  if (totalSeconds <= 0) return 'green';
  const pct = secondsLeft / totalSeconds;
  if (pct <= 0.15) return 'red';
  if (pct <= 0.35) return 'amber';
  return 'green';
}

export default function DecisionPressureTimer({ sessionId, roundNumber, isCommitted, globalState }) {
  const [pacing, setPacing] = useState(null);
  const [secondsLeft, setSecondsLeft] = useState(-1);
  const [totalSeconds, setTotalSeconds] = useState(0);

  const API = process.env.NEXT_PUBLIC_API_URL || '';

  // Poll pacing endpoint every 5s
  const fetchPacing = useCallback(() => {
    if (!sessionId) return;
    fetch(`${API}/api/admin/sessions/${encodeURIComponent(sessionId)}/pacing`, { credentials: 'include', headers: { ...playerIdHeader() } })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return;
        setPacing(d);

        // Calculate time remaining from next_unlock_at
        if (d.next_unlock_at) {
          const unlockTime = new Date(d.next_unlock_at).getTime();
          const now = Date.now();
          const remaining = Math.max(0, Math.floor((unlockTime - now) / 1000));
          setSecondsLeft(remaining);
          if (d.interval_seconds) setTotalSeconds(d.interval_seconds);
        } else if (d.mode === 'timed' && d.interval_seconds) {
          setTotalSeconds(d.interval_seconds);
        }
      })
      .catch(() => {}); // Silent fallback
  }, [sessionId, API]);

  useEffect(() => {
    fetchPacing();
    const poll = setInterval(fetchPacing, 5000);
    return () => clearInterval(poll);
  }, [fetchPacing]);

  // Countdown tick
  useEffect(() => {
    if (secondsLeft <= 0) return;
    const tick = setInterval(() => {
      setSecondsLeft(prev => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(tick);
  }, [secondsLeft]);

  // TIMER-1 (UX audit #15): this used to `return null` for BOTH "no pacing yet"
  // and mode==='free', which meant the player had NO deadline surface at all in
  // the component's own default mode — the timer was silently absent rather
  // than honestly absent. It now renders an honest state in every mode:
  //
  //   timed   — countdown to the next unlock (unchanged)
  //   manual  — no clock exists, so say so: "Facilitator paces this round"
  //   free    — no deadline, but the X/Y commit tally still matters
  //
  // Rule: never imply time pressure that isn't real, and never leave the
  // player guessing whether a clock is running.
  if (!pacing) return null;

  const hasClock = pacing.mode === 'timed' && (secondsLeft > 0 || totalSeconds > 0);

  if (!hasClock) {
    const committedN = pacing.committed_count || 0;
    const totalN = pacing.total_count || 0;
    const label = pacing.mode === 'manual'
      ? 'Facilitator paces this round'
      : 'No time limit this round';
    return (
      <div
        className={styles.container}
        role="status"
        title={pacing.mode === 'manual'
          ? 'There is no countdown. The facilitator opens the next round when the room is ready.'
          : 'There is no countdown. The round advances when every team has committed.'}
      >
        <span aria-hidden="true" style={{ fontSize: '0.95rem', lineHeight: 1 }}>
          {pacing.mode === 'manual' ? '🎬' : '∞'}
        </span>
        <div style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: '#94a3b8', whiteSpace: 'nowrap' }}>
          {label}
        </div>
        {totalN > 0 && (
          <div className={styles.commitBadge}>
            <span className={styles.commitCount}>{committedN}</span>
            <span className={styles.commitSep}>/</span>
            <span className={styles.commitTotal}>{totalN}</span>
            <span className={styles.commitLabel}>{isCommitted ? '✓' : '⏳'}</span>
          </div>
        )}
      </div>
    );
  }

  const urgency = urgencyLevel(secondsLeft, totalSeconds);
  const progressPct = totalSeconds > 0 ? Math.max(0, Math.min(1, secondsLeft / totalSeconds)) : 1;
  const committed = pacing.committed_count || 0;
  const total = pacing.total_count || 0;

  // SVG progress ring
  const ringSize = 36;
  const ringR = 14;
  const ringC = 2 * Math.PI * ringR;
  const ringOffset = ringC * (1 - progressPct);

  const urgencyColors = {
    green: '#10b981',
    amber: '#f59e0b',
    red: '#ef4444',
  };
  const color = urgencyColors[urgency];

  return (
    <div className={`${styles.container} ${styles[`urgency_${urgency}`]}`}>
      {/* Progress ring */}
      <svg width={ringSize} height={ringSize} className={styles.ring}>
        <circle cx={ringSize / 2} cy={ringSize / 2} r={ringR}
          fill="none" stroke="rgba(148,163,184,0.1)" strokeWidth={3} />
        <circle cx={ringSize / 2} cy={ringSize / 2} r={ringR}
          fill="none" stroke={color} strokeWidth={3}
          strokeDasharray={ringC} strokeDashoffset={ringOffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${ringSize / 2} ${ringSize / 2})`}
          className={styles.progressArc}
        />
      </svg>

      {/* Time */}
      <div className={styles.timeDisplay} style={{ color }}>
        {secondsLeft >= 0 ? formatTime(secondsLeft) : '—'}
      </div>

      {/* Commit counter */}
      {total > 0 && (
        <div className={styles.commitBadge}>
          <span className={styles.commitCount}>{committed}</span>
          <span className={styles.commitSep}>/</span>
          <span className={styles.commitTotal}>{total}</span>
          <span className={styles.commitLabel}>
            {isCommitted ? '✓' : '⏳'}
          </span>
        </div>
      )}

      {/* Warning flash when time is critical */}
      {urgency === 'red' && !isCommitted && secondsLeft > 0 && (
        <div className={styles.warningPulse}>⚠️</div>
      )}
    </div>
  );
}
