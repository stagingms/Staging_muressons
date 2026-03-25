'use client';
import { useState, useEffect } from 'react';

/**
 * CountdownTimer — Visible round timer when facilitator sets time limits.
 * Improvement #2.1: Real-time countdown timer
 */
export default function CountdownTimer({ sessionId, roundNumber }) {
  const [timeLeft, setTimeLeft] = useState(null); // seconds remaining
  const [totalTime, setTotalTime] = useState(null);

  useEffect(() => {
    if (!sessionId || sessionId === 'demo') return;
    let cancelled = false;

    const fetchTimer = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/sessions/${sessionId}/pacing`
        );
        if (res.ok && !cancelled) {
          const data = await res.json();
          if (data.pacing_mode === 'timed' && data.deadline_utc) {
            const deadline = new Date(data.deadline_utc).getTime();
            const now = Date.now();
            const remaining = Math.max(0, Math.floor((deadline - now) / 1000));
            setTimeLeft(remaining);
            setTotalTime(data.round_duration_seconds || remaining);
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

  if (timeLeft === null) return null;

  const mins = Math.floor(timeLeft / 60);
  const secs = timeLeft % 60;
  const pct = totalTime ? (timeLeft / totalTime) * 100 : 100;
  const urgency = pct > 50 ? '#4ade80' : pct > 20 ? '#fbbf24' : '#f87171';

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
        {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
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
