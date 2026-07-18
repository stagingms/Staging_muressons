'use client';
import { useState, useEffect } from 'react';
import styles from './CohortPulse.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * CohortPulse — Facilitator-only real-time heatmap of all team KPIs.
 * Shows Treasury, Reputation, Carbon Intensity, and Social License across rounds.
 * Can be toggled to player-visible by facilitator.
 */
export default function CohortPulse({ cohortId, isPlayerVisible = false }) {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState('treasury');
  const [showToPlayers, setShowToPlayers] = useState(isPlayerVisible);
  const [saving, setSaving] = useState(false);

  const METRICS = [
    { key: 'treasury', label: 'Treasury', icon: '💰', format: v => `$${(v / 1_000_000).toFixed(1)}M`,
      tooltip: 'Corporate cash on hand. Funds every decision and allocation; a negative treasury means the team is borrowing to operate. Red cells = teams running dry — a common intervention trigger.' },
    { key: 'reputation', label: 'Reputation', icon: '⭐', format: v => Math.round(v),
      tooltip: 'Group reputation, 0–100. Moves with stakeholder reactions, crises, and disclosure choices, and feeds the Regenerative Multiple at valuation. Below ~40 is a warning zone; sustained lows cap pricing power.' },
    { key: 'carbon', label: 'Carbon Intensity', icon: '🏭', format: v => v?.toFixed(1) || '—',
      tooltip: 'Average carbon intensity across business units (lower is better). Drives the internal carbon fee, stranded-asset risk, and climate-leadership signals at end-of-game scoring.' },
    { key: 'social_license', label: 'Social License', icon: '🤝', format: v => Math.round(v || 0),
      tooltip: 'Community licence to operate, 0–100. Eroded by broken promises and hostile stakeholders; low values trigger the Green Premium Squeeze trap and social-collapse valuation discounts.' },
    { key: 'synergy', label: 'Synergy', icon: '🔗', format: v => (v || 1.0).toFixed(2) + '×',
      tooltip: 'Cross-BU synergy multiplier applied to group performance (1.00× = neutral). Built through coherent, mutually reinforcing strategies; instability and governance failures erode it.' },
    // Climate-specific metrics (shown for all sessions — values will be empty for non-climate)
    { key: 'green_fund', label: 'Green Fund', icon: '🌱', format: v => v != null ? `$${(v / 1_000_000).toFixed(1)}M` : '—',
      tooltip: 'Green Transition Fund balance, filled by the internal carbon fee (emissions × $/tonne). Auto-subsidises green CapEx; decarbonising shrinks the inflow. "—" = not used by this cohort’s paradigm.' },
    { key: 'cost_of_capital', label: 'Cost of Capital', icon: '📊', format: v => v != null ? `${(v * 100).toFixed(1)}%` : '—',
      tooltip: 'The rate at which markets lend to the team. Rises with governance risk, instability, and climate exposure; every point makes future investment more expensive. Watch it climb after crises.' },
    { key: 'carbon_fee_paid', label: 'Carbon Fee Paid', icon: '💨', format: v => v != null ? `$${(v / 1_000_000).toFixed(2)}M` : '—',
      tooltip: 'Cumulative internal carbon fee the team has paid on its emissions. High values with flat Carbon Intensity = paying the fee instead of decarbonising — a classic discussion prompt.' },
  ];

  useEffect(() => {
    if (!cohortId) return;
    let first = true;
    const fetchPulse = async () => {
      try {
        // credentials: the endpoint is now auth-guarded (facilitators always;
        // players only when player_visible) — the JWT cookie must reach it.
        const res = await fetch(`${API}/api/admin/cohort-pulse/${cohortId}`, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          setTeams(data.teams || []);
          // Seed toggle from server state on initial load
          if (first && data.player_visible !== undefined) {
            setShowToPlayers(!!data.player_visible);
            first = false;
          }
        }
      } catch {
        // Backend unreachable — show empty state
      }
      setLoading(false);
    };
    fetchPulse();
    const interval = setInterval(fetchPulse, 15000); // refresh every 15s
    return () => clearInterval(interval);
  }, [cohortId]);

  const getHeatColor = (value, metric) => {
    // Normalize value to 0-1 range based on metric type
    let normalized;
    switch (metric) {
      case 'treasury':
        normalized = Math.max(0, Math.min(1, (value + 50_000_000) / 200_000_000));
        break;
      case 'reputation':
      case 'social_license':
        normalized = Math.max(0, Math.min(1, value / 100));
        break;
      case 'carbon':
        normalized = 1 - Math.max(0, Math.min(1, value / 150)); // inverted — lower is better
        break;
      case 'synergy':
        normalized = Math.max(0, Math.min(1, (value - 0.8) / 0.8));
        break;
      case 'green_fund':
        normalized = Math.max(0, Math.min(1, value / 20_000_000)); // 0-20M range
        break;
      case 'cost_of_capital':
        normalized = 1 - Math.max(0, Math.min(1, (value - 0.03) / 0.08)); // inverted: lower is better
        break;
      case 'carbon_fee_paid':
        normalized = 1 - Math.max(0, Math.min(1, value / 5_000_000)); // inverted: lower is better
        break;
      default:
        normalized = 0.5;
    }
    // Green (good) → Yellow → Red (bad)
    if (normalized >= 0.6) return `rgba(16, 185, 129, ${0.15 + normalized * 0.3})`;
    if (normalized >= 0.3) return `rgba(245, 158, 11, ${0.15 + normalized * 0.3})`;
    return `rgba(239, 68, 68, ${0.15 + (1 - normalized) * 0.3})`;
  };

  const activeMetric = METRICS.find(m => m.key === selectedMetric);

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading cohort data...</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerIcon}>📊</span>
          <div>
            <h3 className={styles.headerTitle}>Cohort Pulse</h3>
            <span className={styles.headerSubtitle}>
              {teams.length} team{teams.length !== 1 ? 's' : ''} · Live data
            </span>
          </div>
        </div>
        <div className={styles.headerRight}>
          <label
            className={styles.toggleLabel}
            title="Who can see this pulse board. Facilitator Only keeps it on your dashboard; Player-Visible mirrors it to every team's cockpit — useful for debriefs, spicy mid-round."
          >
            <input
              type="checkbox"
              checked={showToPlayers}
              disabled={saving}
              onChange={async (e) => {
                const next = e.target.checked;
                setShowToPlayers(next);
                if (!cohortId) return;
                setSaving(true);
                try {
                  await fetch(`${API}/api/admin/cohort-pulse/${cohortId}/visibility`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player_visible: next }),
                  });
                } catch { /* degrade silently — local state still reflects intent */ }
                setSaving(false);
              }}
              className={styles.toggleInput}
            />
            <span className={styles.toggleText}>
              {saving ? '⏳ Saving...' : showToPlayers ? '👁️ Player-Visible' : '🔒 Facilitator Only'}
            </span>
          </label>
        </div>
      </div>

      {/* Metric Selector */}
      <div className={styles.metricSelector}>
        {METRICS.map(m => (
          <button
            key={m.key}
            className={`${styles.metricBtn} ${selectedMetric === m.key ? styles.metricBtnActive : ''}`}
            onClick={() => setSelectedMetric(m.key)}
            title={m.tooltip}
          >
            <span>{m.icon}</span> {m.label}
          </button>
        ))}
      </div>

      {/* Heatmap Grid */}
      {teams.length === 0 ? (
        <div className={styles.empty}>No teams in this cohort yet.</div>
      ) : (
        <div className={styles.heatmapGrid}>
          {/* Header row */}
          <div className={styles.heatmapHeaderRow}>
            <div className={styles.heatmapTeamHeader} title="One row per team in this cohort. Hover any cell for the exact value that round.">Team</div>
            {Array.from({ length: 10 }, (_, i) => (
              <div key={i} className={styles.heatmapRoundHeader} title={`Round ${i + 1} — the selected metric's committed value at the end of round ${i + 1}. Empty = not yet played.`}>R{i + 1}</div>
            ))}
            <div className={styles.heatmapRoundHeader} title="The team's live, uncommitted value for the selected metric — where they stand right now, before the current round commits.">Now</div>
            <div className={styles.heatmapRoundHeader} style={{ width: '120px', textAlign: 'left', paddingLeft: '8px' }} title="Systemic traps currently active on the team (Austerity, Defection, Squeeze, Ratchet). Hover a badge for what triggered it and what it does.">Active Traps</div>
          </div>

          {/* Team rows */}
          {teams.map((team, ti) => (
            <div key={ti} className={styles.heatmapRow}>
              <div className={styles.heatmapTeamName} title={team.name}>
                {team.name?.substring(0, 12) || `Team ${ti + 1}`}
              </div>
              {Array.from({ length: 10 }, (_, ri) => {
                const roundData = team.history?.[ri + 1];
                const value = roundData?.[selectedMetric];
                const hasData = value !== undefined && value !== null;
                return (
                  <div
                    key={ri}
                    className={styles.heatmapCell}
                    style={{
                      background: hasData ? getHeatColor(value, selectedMetric) : 'rgba(255,255,255,0.02)',
                    }}
                    title={hasData ? `R${ri + 1}: ${activeMetric.format(value)}` : 'No data'}
                  >
                    {hasData && (
                      <span className={styles.cellValue}>{activeMetric.format(value)}</span>
                    )}
                  </div>
                );
              })}
              {/* Current value */}
              <div
                className={`${styles.heatmapCell} ${styles.currentCell}`}
                style={{
                  background: team.current?.[selectedMetric] != null
                    ? getHeatColor(team.current[selectedMetric], selectedMetric)
                    : 'rgba(255,255,255,0.03)',
                }}
              >
                {team.current?.[selectedMetric] != null && (
                  <span className={styles.cellValue}>
                    {activeMetric.format(team.current[selectedMetric])}
                  </span>
                )}
              </div>
              {/* Active Traps */}
              <div className={styles.heatmapCell} style={{ width: '120px', justifyContent: 'flex-start', paddingLeft: '8px', fontSize: '0.65rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {team.current?.active_traps?.length > 0 ? (
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {team.current.active_traps.map((trap, idx) => {
                      const trapType = trap.split(' ')[1];
                      let tooltipDesc = trap;
                      if (trapType === 'Austerity') tooltipDesc = '🛑 CFO Austerity Override Active - ESG budgets frozen';
                      else if (trapType === 'Defection') tooltipDesc = '🏭 Supplier Defection - Mandates enforced without subsidies';
                      else if (trapType === 'Squeeze') tooltipDesc = '📉 Green Premium Squeeze - Low social license hurting sales';
                      else if (trapType === 'Ratchet') tooltipDesc = '⚖️ Regulatory Ratchet - Governance risk exceeds industry baseline';
                      
                      return (
                        <span key={idx} title={tooltipDesc} style={{ background: 'rgba(239,68,68,0.2)', color: '#fca5a5', padding: '2px 4px', borderRadius: '4px', cursor: 'help' }}>
                          {trap}
                        </span>
                      );
                    })}
                  </div>
                ) : (
                  <span style={{ color: 'var(--text-muted)' }}>—</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
