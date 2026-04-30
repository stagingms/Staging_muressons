'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import styles from './PeerComparison.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';
const WS_BASE = (API || 'http://localhost:8000').replace(/^http/, 'ws');

/**
 * PeerComparison — Live anonymized leaderboard with WebSocket real-time updates.
 *
 * Connects to ws://.../api/admin/ws/session/{sessionId} for push-based
 * leaderboard refreshes. Falls back to polling every 30s if WS fails.
 *
 * Props:
 *  - sessionId: current player's session ID
 *  - isOpen: boolean — controls modal visibility
 *  - onClose: () => void
 *  - roundNumber: current round (1 = locked placeholder)
 */
export default function PeerComparison({ sessionId, isOpen, onClose, roundNumber }) {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [wsConnected, setWsConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const wsRef = useRef(null);
  const pollRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const mountedRef = useRef(false);

  // ── Fetch leaderboard via REST ──────────────────────────────
  const fetchLeaderboard = useCallback(async () => {
    if (!sessionId || sessionId === 'demo') {
      setLeaderboard([
        { rank: 1, name: 'Team Alpha', treasury: 48200000, reputation: 62, co2: 2100, bonus_score: 3000, trend: '↑' },
        { rank: 2, name: 'Your Team', treasury: 45000000, reputation: 55, co2: 2635, bonus_score: 1000, trend: '→', isYou: true },
        { rank: 3, name: 'Team Bravo', treasury: 42000000, reputation: 58, co2: 2800, bonus_score: 0, trend: '↓' },
        { rank: 4, name: 'Team Charlie', treasury: 38500000, reputation: 47, co2: 3200, bonus_score: 2000, trend: '↓' },
        { rank: 5, name: 'Team Delta', treasury: 35000000, reputation: 44, co2: 3500, bonus_score: 0, trend: '↑' },
      ]);
      setMessage('Demo mode — showing sample data');
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${API}/api/simulations/${sessionId}/peer-leaderboard`);
      const data = await res.json();
      if (data.leaderboard && data.leaderboard.length > 0) {
        setLeaderboard(data.leaderboard);
        setMessage('');
      } else {
        setLeaderboard([]);
        setMessage(data.message || 'No peers in this cohort yet.');
      }
    } catch {
      setMessage('Unable to load leaderboard data.');
      setLeaderboard([]);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  // ── WebSocket connection ────────────────────────────────────
  const connectWs = useCallback(() => {
    if (!sessionId || sessionId === 'demo' || !isOpen) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${WS_BASE}/api/admin/ws/session/${sessionId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
        setReconnecting(false);
        clearTimeout(reconnectTimerRef.current);
      };

      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          // Server pushes leaderboard_update or commit events
          if (msg.type === 'leaderboard_update' && msg.leaderboard) {
            setLeaderboard(msg.leaderboard);
          } else if (
            msg.type === 'round_committed' ||
            msg.type === 'state_override' ||
            msg.type === 'sessions_refresh_trigger'
          ) {
            // Trigger a REST fetch on relevant events
            fetchLeaderboard();
          }
        } catch { /* ignore malformed messages */ }
      };

      ws.onclose = () => {
        setWsConnected(false);
        wsRef.current = null;
        // Auto-reconnect after 5s if modal still open
        if (mountedRef.current && isOpen) {
          setReconnecting(true);
          reconnectTimerRef.current = setTimeout(connectWs, 5000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // WebSocket not available — fall back to polling
      setWsConnected(false);
    }
  }, [sessionId, isOpen, fetchLeaderboard]);

  // ── Lifecycle: connect/disconnect on open/close ─────────────
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimerRef.current);
    };
  }, []);

  useEffect(() => {
    if (!isOpen) {
      // Close WebSocket when modal closes
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setWsConnected(false);
      setReconnecting(false);
      clearInterval(pollRef.current);
      clearTimeout(reconnectTimerRef.current);
      return;
    }

    // Initial fetch
    fetchLeaderboard();

    // Attempt WebSocket connection
    connectWs();

    // Polling fallback: every 30s if WS is not connected
    pollRef.current = setInterval(() => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        fetchLeaderboard();
      }
    }, 30000);

    return () => {
      clearInterval(pollRef.current);
    };
  }, [isOpen, fetchLeaderboard, connectWs]);

  if (!isOpen) return null;

  // ── Round 1: Locked placeholder ─────────────────────────────
  if (roundNumber === 1) {
    return (
      <div className={styles.overlay} onClick={onClose} data-testid="peer-overlay">
        <div className={styles.lockedCard} onClick={e => e.stopPropagation()}>
          <div className={styles.lockedIcon}>🏅</div>
          <h2 className={styles.lockedTitle}>Leaderboard</h2>
          <div className={styles.lockedBadge}>🔒 Available from Round 2</div>
          <p className={styles.lockedBody}>
            The leaderboard will unlock after your first round is committed.
            Complete your decisions and commit to see how your team ranks!
          </p>
          <button className={styles.gotItBtn} onClick={onClose}>Got it</button>
        </div>
      </div>
    );
  }

  // ── Main leaderboard ────────────────────────────────────────
  return (
    <div className={styles.overlay} onClick={onClose} data-testid="peer-overlay">
      <div className={styles.card} onClick={e => e.stopPropagation()} data-testid="peer-card">
        {/* Header */}
        <div className={styles.header}>
          <h2 className={styles.title}>📊 Cohort Leaderboard</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Live indicator */}
            {wsConnected && (
              <div className={styles.liveIndicator} data-testid="ws-live">
                <span className={styles.liveDot} />
                LIVE
              </div>
            )}
            <button className={styles.closeBtn} onClick={onClose} data-testid="peer-close">✕</button>
          </div>
        </div>

        <p className={styles.subtitle}>
          See how your team compares to others in your cohort. Rankings are anonymized.
          {message && <span className={styles.message}>{message}</span>}
        </p>

        {/* Reconnecting banner */}
        {reconnecting && (
          <div className={styles.reconnecting} data-testid="ws-reconnecting">
            ⏳ Reconnecting to live feed…
          </div>
        )}

        {loading ? (
          <div className={styles.loading}>Loading...</div>
        ) : leaderboard.length === 0 ? (
          <div className={styles.emptyState}>
            {message || 'No peers to compare with in this cohort.'}
          </div>
        ) : (
          <table className={styles.table} data-testid="peer-table">
            <thead>
              <tr className={styles.tableHeader}>
                <th className={styles.th}>#</th>
                <th className={styles.th}>Team</th>
                <th className={styles.thRight}>Treasury</th>
                <th className={styles.thRight}>Reputation</th>
                <th className={styles.thRight}>CO₂</th>
                <th className={styles.thRight}>Bonus</th>
                <th className={styles.thCenter}>Trend</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map(team => (
                <tr
                  key={team.rank}
                  className={team.isYou ? styles.rowYou : styles.row}
                  data-testid={team.isYou ? 'peer-row-you' : 'peer-row'}
                >
                  <td className={styles.rankCell}>
                    {team.rank <= 3 ? ['🥇', '🥈', '🥉'][team.rank - 1] : team.rank}
                  </td>
                  <td className={team.isYou ? styles.nameCellYou : styles.nameCell}>
                    {team.name}
                    {team.isYou && <span className={styles.youBadge}>YOU</span>}
                  </td>
                  <td className={styles.treasuryCell}>
                    ${(team.treasury / 1_000_000).toFixed(1)}M
                  </td>
                  <td className={styles.reputationCell}>
                    {team.reputation.toFixed(0)}
                  </td>
                  <td className={styles.co2Cell}>
                    {team.co2.toLocaleString()}t
                  </td>
                  <td className={`${styles.bonusCell} ${team.bonus_score > 0 ? styles.bonusActive : styles.bonusInactive}`}>
                    {team.bonus_score > 0 ? `🏅 ${team.bonus_score.toLocaleString()}` : '–'}
                  </td>
                  <td className={styles.trendCell}>
                    <span className={
                      team.trend === '↑' ? styles.trendUp
                        : team.trend === '↓' ? styles.trendDown
                        : styles.trendFlat
                    }>
                      {team.trend}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
