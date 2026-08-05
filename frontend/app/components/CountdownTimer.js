'use client';
import { useState, useEffect, useRef } from 'react';

/**
 * CountdownTimer — Visible round timer when facilitator sets time limits.
 * NEW-11 fix: Resolves the parent cohort session ID from /session-info to
 * poll pacing against the cohort, not the player's sub-session ID.
 */
/* variant='bar' — the action bar's copy. Same clock, same poll, no chrome:
   the bar already has a surface and a border, and a bordered pill inside a
   bordered bar is a box in a box. The header keeps the tinted capsule, where
   it has to hold its own against the logo and the round line. */
export default function CountdownTimer({ sessionId, roundNumber, variant = 'badge' }) {
  const [timeLeft, setTimeLeft] = useState(null); // seconds remaining
  const [totalTime, setTotalTime] = useState(null);
  /* PHASE 8C — THE CLOCK HAS TO SAY SOMETHING, BUT NOT EVERY SECOND.
     A round can end under a screen-reader user with no warning: the digits
     were aria-hidden and the sr-only label was not live, so nothing was ever
     announced. The naive fix — aria-live on the clock — announces a new time
     every second and makes the whole page unusable.
     So: announce at THRESHOLDS. Five minutes, one minute, thirty seconds, ten.
     Four utterances per round, at the moments a decision is still possible. */
  const [announcement, setAnnouncement] = useState('');
  const announcedRef = useRef(new Set());
  // NEW-11: Resolved cohort session ID (may differ from player's own sessionId)
  const cohortIdRef = useRef(null);

  // Resolve the correct cohort ID on mount / sessionId change
  useEffect(() => {
    if (!sessionId || sessionId === 'demo') return;
    let cancelled = false;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sessionId}/session-info`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!cancelled && data) {
          // If this is a player sub-session, use the parent cohort ID for pacing polls
          cohortIdRef.current = data.parent_cohort_id || sessionId;
        }
      })
      .catch(() => { cohortIdRef.current = sessionId; });
    return () => { cancelled = true; };
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId || sessionId === 'demo') return;
    let cancelled = false;

    const fetchTimer = async () => {
      // NEW-11: Always poll pacing for the cohort, not the player's own sub-session
      const targetId = cohortIdRef.current || sessionId;
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/sessions/${targetId}/pacing`
        );
        if (res.ok && !cancelled) {
          const data = await res.json();
          /* FIELD NAMES. This read three keys the endpoint has never returned:
             pacing_mode, deadline_utc, round_duration_seconds. GET
             /api/admin/sessions/:id/pacing returns mode, next_unlock_at and
             interval_seconds. So `data.pacing_mode === 'timed'` was undefined
             on every poll, timeLeft stayed null, and the component returned
             null — which is why a facilitator could set a per-round time and no
             player ever saw a clock.

             The facilitator control and the backend were both already correct:
             POST /pacing with mode 'timed' + interval_seconds sets
             next_unlock_at to now + interval and starts the unlock task. The
             deadline has always been published. Nothing in the engine, the
             unlock path or the pacing contract is touched here — three names
             are. Changing the backend to match the frontend would have been the
             risky direction, since the facilitator dashboard reads these keys.

             next_unlock_at is when the round unlocks, which in timed mode IS
             the round's deadline. */
          const deadlineIso = data.next_unlock_at;
          if (data.mode === 'timed' && deadlineIso) {
            const deadline = new Date(deadlineIso).getTime();
            if (Number.isNaN(deadline)) { setTimeLeft(null); return; }
            const remaining = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
            setTimeLeft(remaining);
            /* interval_seconds is the round's full length — the denominator the
               urgency colour needs. Falling back to `remaining` would make the
               bar start full on every poll and never move. */
            setTotalTime(data.interval_seconds || remaining);
          } else {
            setTimeLeft(null);
          }
        }
      } catch { /* silent */ }
    };

    fetchTimer();
    const interval = setInterval(fetchTimer, 10000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [sessionId, roundNumber]);

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
  }, [timeLeft !== null]);

  /* Reset the thresholds when the round changes, so round 3 announces the
     same way round 2 did. */
  useEffect(() => { announcedRef.current = new Set(); setAnnouncement(''); }, [roundNumber]);

  useEffect(() => {
    if (timeLeft === null) return;
    const THRESHOLDS = [
      [300, 'Five minutes left in this round.'],
      [60,  'One minute left in this round.'],
      [30,  'Thirty seconds left.'],
      [10,  'Ten seconds left. The round will commit automatically.'],
    ];
    for (const [at, text] of THRESHOLDS) {
      /* Fire once, on the way DOWN through the threshold. The <= guard alone
         would re-fire every tick; the Set is what makes it once. A late join
         mid-round skips the thresholds already passed rather than announcing
         all of them at once. */
      if (timeLeft <= at && !announcedRef.current.has(at)) {
        announcedRef.current.add(at);
        setAnnouncement(text);
        return;
      }
    }
  }, [timeLeft, roundNumber]);

  if (timeLeft === null) return null;

  const mins = Math.floor(timeLeft / 60);
  const secs = timeLeft % 60;
  const pct = totalTime ? (timeLeft / totalTime) * 100 : 100;
  const urgency = pct > 50 ? '#4ade80' : pct > 20 ? '#fbbf24' : '#f87171';
  const clock = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

  if (variant === 'bar') {
    /* The word "left" is doing work: a bare 12:04 beside a commit button could
       be read as elapsed. And it is aria-hidden with a polite label beside it,
       because a clock that re-announces itself every second is unusable with a
       screen reader on. */
    return (
      <span
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '0.8125rem',
          fontWeight: 600,
          color: pct > 20 ? 'var(--text-muted)' : urgency,
          whiteSpace: 'nowrap',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        <span aria-hidden="true">{clock} left</span>
        {/* Not live: read on demand when a user navigates to it. */}
        <span style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}>
          {mins} minutes {secs} seconds left in this round
        </span>
        {/* Live, and empty except in the instant after a threshold passes. */}
        <span
          role="status"
          aria-live="polite"
          style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}
        >
          {announcement}
        </span>
      </span>
    );
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '3px 10px', borderRadius: 8,
      background: `${urgency}15`, border: `1px solid ${urgency}40`,
      fontFamily: "'JetBrains Mono', monospace",
    }}>
      <span style={{ fontSize: '0.7rem' }}>⏱️</span>
      <span style={{
        fontSize: '0.75rem', fontWeight: 800, color: urgency,
        letterSpacing: '0.03em',
      }}>
        {clock}
      </span>
      {/* Mini progress bar */}
      <div style={{
        width: 40, height: 3, borderRadius: 2, background: '#e2e8f0',
      }}>
        <div style={{
          width: `${pct}%`, height: '100%', borderRadius: 2,
          background: urgency, transition: 'width 1s linear',
        }} />
      </div>
    </div>
  );
}
