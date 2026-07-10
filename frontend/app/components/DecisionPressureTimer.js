/**
 * DecisionPressureTimer — WOW-11
 *
 * Enhanced decision timer that adds competitive pressure to the existing
 * CountdownTimer. Shows a prominent "X of Y teams committed" live counter
 * alongside the countdown, creating social accountability.
 *
 * SAFETY: Pure presentation. Polls the existing /peer-leaderboard or
 * /session-info endpoints for commit count. No changes to pacing logic,
 * auto-commit, or round advancement. Falls back gracefully when data
 * is unavailable (solo play, no cohort, etc.).
 *
 * Timer range: 3-30 minutes (180-1800 seconds), configurable by facilitator.
 * The backend already supports any interval_seconds value via RoundPacingRequest.
 *
 * Props:
 *   sessionId   — current session ID
 *   roundNumber — current round
 *   isCommitted — whether this player has committed this round
 *   globalState — for cohort_team_count
 */
'use client';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import styles from './DecisionPressureTimer.module.css';

const POLL_INTERVAL_MS = 5000; // Poll every 5 seconds

export default function DecisionPressureTimer({
  sessionId,
  roundNumber,
  isCommitted = false,
  globalState,
}) {
  const [timeLeft, setTimeLeft] = useState(null); // seconds
  const [totalTime, setTotalTime] = useState(null);
  const [commitStats, setCommitStats] = useState({ committed: 0, total: 0 });
  const cohortIdRef = useRef(null);

  // Resolve cohort ID (same pattern as existing CountdownTimer)
  useEffect(() => {
    if (!sessionId || sessionId === 'demo') return;
    let cancelled = false;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sessionId}/session-info`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!cancelled && data) {
          cohortIdRef.current = data.parent_cohort_id || sessionId;
        }
      })
      .catch(() => { cohortIdRef.current = sessionId; });
    return () => { cancelled = true; };
  }, [sessionId]);

  // Poll timer + commit status
  useEffect(() => {
    if (!sessionId || sessionId === 'demo') return;
    let cancelled = false;
    const API = process.env.NEXT_PUBLIC_API_URL || '';

    const poll = async () => {
      const targetId = cohortIdRef.current || sessionId;
      try {
        // Pacing data
        const pacingRes = await fetch(`${API}/api/admin/sessions/${targetId}/pacing`);
        if (pacingRes.ok && !cancelled) {
          const data = await pacingRes.json();
          if (data.pacing_mode === 'timed' && data.deadline_utc) {
            const deadline = new Date(data.deadline_utc).getTime();
            const remaining = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
            setTimeLeft(remaining);
            setTotalTime(data.round_duration_seconds || remaining);
          } else {
            setTimeLeft(null);
          }
        }

        // Commit stats from globalState (set by backend on each poll)
        const teamCount = globalState?.cohort_team_count || 0;
        const commits = globalState?.team_commits_this_round || 0;
        if (teamCount > 1) {
          setCommitStats({ committed: commits, total: teamCount });
        }
      } catch { /* silent */ }
    };

    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => { cancelled = true; clearInterval(interval); };
  }, [sessionId, roundNumber, globalState?.cohort_team_count, globalState?.team_commits_this_round]);

  // Countdown tick
  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0) return;
    const tick = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) { clearInterval(tick); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(tick);
  }, [timeLeft !== null]); // eslint-disable-line react-hooks/exhaustive-deps

  // Don't render if no timer is active
  if (timeLeft === null) return null;

  const mins = Math.floor(timeLeft / 60);
  const secs = timeLeft % 60;
  const pct = totalTime ? (timeLeft / totalTime) * 100 : 100;
  const isUrgent = pct <= 20;
  const isWarning = pct <= 50 && !isUrgent;

  const urgencyColor = isUrgent ? '#ef4444' : isWarning ? '#fbbf24' : '#4ade80';
  const hasMultiTeam = commitStats.total > 1;
  const allCommitted = commitStats.committed >= commitStats.total;

  return (
    <div
      className={`${styles.container} ${isUrgent ? styles.urgent : ''} ${timeLeft === 0 ? styles.expired : ''}`}
      style={{ '--urgency-color': urgencyColor }}
    >
      {/* Timer display */}
      <div className={styles.timerSection}>
        <span className={styles.timerIcon}>{isUrgent ? '🔥' : '⏱️'}</span>
        <span className={styles.timerDigits}>
          {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
        </span>

        {/* Progress ring */}
        <svg className={styles.progressRing} viewBox="0 0 28 28">
          <circle cx="14" cy="14" r="12" fill="none" stroke="rgba(148,163,184,0.15)" strokeWidth="2" />
          <circle
            cx="14" cy="14" r="12"
            fill="none"
            stroke={urgencyColor}
            strokeWidth="2"
            strokeDasharray={`${2 * Math.PI * 12}`}
            strokeDashoffset={`${2 * Math.PI * 12 * (1 - pct / 100)}`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s linear', transform: 'rotate(-90deg)', transformOrigin: 'center' }}
          />
        </svg>
      </div>

      {/* Commit counter (competitive pressure) */}
      {hasMultiTeam && (
        <div className={styles.commitSection}>
          <div className={styles.commitBar}>
            <div
              className={styles.commitBarFill}
              style={{
                width: `${(commitStats.committed / commitStats.total) * 100}%`,
                background: allCommitted ? '#10b981' : urgencyColor,
              }}
            />
          </div>
          <div className={styles.commitText}>
            <span className={styles.commitCount}>{commitStats.committed}/{commitStats.total}</span>
            <span className={styles.commitLabel}>
              {isCommitted ? '✓ You committed' : allCommitted ? 'All committed' : 'teams committed'}
            </span>
          </div>
        </div>
      )}

      {/* Expired message */}
      {timeLeft === 0 && !isCommitted && (
        <div className={styles.expiredMsg}>
          ⚡ Time's up — auto-committing...
        </div>
      )}
    </div>
  );
}
