'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * PeerComparison — Live anonymized leaderboard showing cohort rankings.
 * Fetches real data from GET /api/simulations/{sessionId}/peer-leaderboard
 * Falls back to demo data for solo sessions.
 */
export default function PeerComparison({ sessionId, isOpen, onClose }) {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!isOpen) return;

    if (!sessionId || sessionId === 'demo') {
      // Demo/solo mode — show placeholder data
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

    // Fetch real peer leaderboard data
    setLoading(true);
    setMessage('');
    fetch(`${API}/api/simulations/${sessionId}/peer-leaderboard`)
      .then(res => res.json())
      .then(data => {
        if (data.leaderboard && data.leaderboard.length > 0) {
          setLeaderboard(data.leaderboard);
          setMessage('');
        } else {
          // No peers — solo session
          setLeaderboard([]);
          setMessage(data.message || 'No peers in this cohort yet.');
        }
      })
      .catch(() => {
        setMessage('Unable to load leaderboard data.');
        setLeaderboard([]);
      })
      .finally(() => setLoading(false));
  }, [isOpen, sessionId]);

  if (!isOpen) return null;

  // Detect theme
  const isDark = typeof document !== 'undefined' &&
    document.documentElement.getAttribute('data-theme') !== 'light';

  const overlayStyle = {
    position: 'fixed', inset: 0, zIndex: 12000,
    background: isDark ? 'rgba(10,14,26,0.6)' : 'rgba(15,23,42,0.5)',
    backdropFilter: 'blur(4px)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontFamily: 'Inter, sans-serif',
  };

  const cardStyle = {
    background: isDark ? '#0f1524' : '#fff',
    borderRadius: 16, width: '90%', maxWidth: 620,
    maxHeight: '80vh', overflow: 'auto', padding: '1.5rem',
    boxShadow: isDark ? '0 25px 60px rgba(0,0,0,0.5)' : '0 25px 60px rgba(0,0,0,0.2)',
    border: isDark ? '1px solid rgba(45,212,191,0.15)' : 'none',
  };

  const thStyle = {
    padding: '8px 6px', textAlign: 'left',
    color: isDark ? '#64748b' : '#6b7280',
    fontWeight: 700, fontSize: '0.62rem',
    textTransform: 'uppercase', letterSpacing: '0.06em',
  };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={cardStyle}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: isDark ? '#e2e8f0' : '#0f172a' }}>
            📊 Cohort Leaderboard
          </h2>
          <button onClick={onClose} style={{
            background: isDark ? '#1e293b' : '#f1f5f9', border: 'none', borderRadius: '50%',
            width: 28, height: 28, cursor: 'pointer', fontSize: '0.85rem',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: isDark ? '#94a3b8' : '#64748b', fontWeight: 700,
          }}>✕</button>
        </div>

        <p style={{ fontSize: '0.72rem', color: isDark ? '#94a3b8' : '#64748b', margin: '0 0 1rem', lineHeight: 1.5 }}>
          See how your team compares to others in your cohort. Rankings are anonymized.
          {message && <span style={{ display: 'block', marginTop: 4, fontStyle: 'italic' }}>{message}</span>}
        </p>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>Loading...</div>
        ) : leaderboard.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
            {message || 'No peers to compare with in this cohort.'}
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.73rem' }}>
            <thead>
              <tr style={{ borderBottom: isDark ? '2px solid #1e293b' : '2px solid #e2e8f0' }}>
                <th style={thStyle}>#</th>
                <th style={thStyle}>Team</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Treasury</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Reputation</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>CO₂</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Bonus</th>
                <th style={{ ...thStyle, textAlign: 'center' }}>Trend</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map(team => (
                <tr key={team.rank} style={{
                  borderBottom: isDark ? '1px solid #1e293b' : '1px solid #f1f5f9',
                  background: team.isYou
                    ? (isDark ? 'rgba(45,212,191,0.08)' : '#f0f4ff')
                    : 'transparent',
                }}>
                  <td style={{ padding: '10px 6px', fontWeight: 800, color: isDark ? '#e2e8f0' : '#0f172a' }}>
                    {team.rank <= 3 ? ['🥇', '🥈', '🥉'][team.rank - 1] : team.rank}
                  </td>
                  <td style={{
                    padding: '10px 6px',
                    fontWeight: team.isYou ? 800 : 600,
                    color: team.isYou
                      ? (isDark ? '#2dd4bf' : '#6366f1')
                      : (isDark ? '#e2e8f0' : '#0f172a'),
                  }}>
                    {team.name}
                    {team.isYou && (
                      <span style={{
                        fontSize: '0.55rem',
                        background: isDark ? '#2dd4bf' : '#6366f1',
                        color: isDark ? '#0a0e1a' : '#fff',
                        padding: '1px 5px', borderRadius: 4, marginLeft: 4,
                      }}>YOU</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 6px', textAlign: 'right', fontWeight: 600, color: '#16a34a' }}>
                    ${(team.treasury / 1_000_000).toFixed(1)}M
                  </td>
                  <td style={{ padding: '10px 6px', textAlign: 'right', fontWeight: 600, color: '#f59e0b' }}>
                    {team.reputation.toFixed(0)}
                  </td>
                  <td style={{ padding: '10px 6px', textAlign: 'right', fontWeight: 600, color: isDark ? '#94a3b8' : '#64748b' }}>
                    {team.co2.toLocaleString()}t
                  </td>
                  <td style={{ padding: '10px 6px', textAlign: 'right', fontWeight: 600, color: team.bonus_score > 0 ? '#059669' : (isDark ? '#64748b' : '#94a3b8') }}>
                    {team.bonus_score > 0 ? `🏅 ${team.bonus_score.toLocaleString()}` : '–'}
                  </td>
                  <td style={{ padding: '10px 6px', textAlign: 'center', fontSize: '0.85rem' }}>
                    <span style={{ color: team.trend === '↑' ? '#16a34a' : team.trend === '↓' ? '#ef4444' : '#94a3b8' }}>
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
