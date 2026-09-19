'use client';
import { useState, useEffect, useCallback } from 'react';
import { useConfirm } from './ConfirmModal';
import styles from './CohortPulse.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const METRICS = [
  { key: 'treasury', label: 'Treasury', icon: '💰', format: v => `$${(v / 1_000_000).toFixed(1)}M`, tooltip: 'Corporate Treasury across rounds' },
  { key: 'reputation', label: 'Reputation', icon: '⭐', format: v => Math.round(v), tooltip: 'Group Reputation score' },
  { key: 'carbon', label: 'Carbon Intensity', icon: '🏭', format: v => v?.toFixed(1) || '—', tooltip: 'Carbon emissions (tCO2e)' },
  { key: 'social_license', label: 'Social License', icon: '🤝', format: v => Math.round(v || 0), tooltip: 'Average Social License score across BUs' },
  { key: 'synergy', label: 'Synergy', icon: '🔗', format: v => (v || 1.0).toFixed(2) + '×', tooltip: 'Synergy multiplier' },
  // Climate-specific metrics (shown for all sessions — values will be empty for non-climate)
  { key: 'green_fund', label: 'Green Fund', icon: '🌱', format: v => v != null ? `$${(v / 1_000_000).toFixed(1)}M` : '—', tooltip: 'Green Transition Fund' },
  { key: 'cost_of_capital', label: 'Cost of Capital', icon: '📊', format: v => v != null ? `${(v * 100).toFixed(1)}%` : '—', tooltip: 'Cost of Capital percentage' },
  { key: 'carbon_fee_paid', label: 'Carbon Fee Paid', icon: '💨', format: v => v != null ? `$${(v / 1_000_000).toFixed(2)}M` : '—', tooltip: 'Cumulative Carbon Fee Paid' },
];

/**
 * CohortPulse — Facilitator-only real-time heatmap of all team KPIs.
 * Shows Treasury, Reputation, Carbon Intensity, and Social License across rounds.
 * Can be toggled to player-visible by facilitator.
 */
export default function CohortPulse({ cohortId, isPlayerVisible = false }) {
  const [teams, setTeams] = useState([]);
  const [progress, setProgress] = useState(null); // RB-2: commit_progress block
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState('treasury');
  const [showToPlayers, setShowToPlayers] = useState(isPlayerVisible);
  const [saving, setSaving] = useState(false);
  const [committingTeam, setCommittingTeam] = useState(null);
  const [confirmDialog, confirmModal] = useConfirm();

  const fetchPulse = useCallback(async () => {
    if (!cohortId) return;
    try {
      // credentials: the endpoint is now auth-guarded (facilitators always;
      // players only when player_visible) — the JWT cookie must reach it.
      const res = await fetch(`${API}/api/admin/cohort-pulse/${cohortId}`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        // RB-2 (UX audit §7.2): filter the cohort-shell row and keep the
        // commit-progress block the endpoint now returns.
        setTeams((data.teams || []).filter(t => !t.is_cohort_shell));
        setProgress(data.commit_progress || null);
        if (data.player_visible !== undefined) {
          setShowToPlayers(!!data.player_visible);
        }
      }
    } catch {
      // Backend unreachable — show empty state
    }
    setLoading(false);
  }, [cohortId]);

  useEffect(() => {
    if (!cohortId) return;
    fetchPulse();
    const interval = setInterval(() => {
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
      fetchPulse();
    }, 15000);
    return () => clearInterval(interval);
  }, [cohortId, fetchPulse]);

  const handleCommitTeam = async (team) => {
    const teamIdentifier = team?.team_id || team?.session_id;
    if (!teamIdentifier || committingTeam) return;
    const ok = await confirmDialog({
      title: `Auto-commit decisions for ${team.name || 'this team'}?`,
      message: team.has_saved_draft
        ? 'This team has a saved draft that will be committed.'
        : 'This team has NO saved draft. Standard Option B default decisions ($1 per BU) will be applied.',
      impact: [
        `Team: ${team.name || teamIdentifier}`,
        `Current Round: R${team.round || progress?.target_round || '—'}`,
        `Draft status: ${team.has_saved_draft ? 'Draft saved' : 'No draft (defaults will apply)'}`,
        'Isolation: Only this team will be committed. Other deliberating teams are unaffected.',
      ],
      confirmLabel: 'Auto-Commit Team',
      cancelLabel: 'Cancel',
      danger: true,
    });
    if (!ok) return;
    setCommittingTeam(team.session_id);
    try {
      const endpoint = cohortId
        ? `${API}/api/admin/sessions/${encodeURIComponent(cohortId)}/teams/${encodeURIComponent(teamIdentifier)}/force-commit`
        : `${API}/api/admin/sessions/${encodeURIComponent(team.session_id)}/commit-default`;
      const res = await fetch(endpoint, {
        method: 'POST',
        credentials: 'include',
      });
      if (res.ok) {
        fetchPulse();
      }
    } catch {
      // Network error
    } finally {
      setCommittingTeam(null);
    }
  };

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

  const activeMetric = METRICS.find(m => m.key === selectedMetric) || METRICS[0];

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
              {progress && progress.total_players > 0 && (
                <>
                  {' · '}
                  <strong style={{ color: '#a5b4fc' }}>
                    R{progress.target_round ?? '—'}: {progress.committed_count}/{progress.total_players} committed
                  </strong>
                  {progress.auto_committed_count > 0 && (
                    <span style={{ color: '#fbbf24' }}> · {progress.auto_committed_count} auto</span>
                  )}
                  {progress.diverged && (
                    <span style={{ color: '#fbbf24' }}> · ⚠ split R{progress.min_round}–R{progress.target_round}</span>
                  )}
                </>
              )}
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
            <div className={styles.heatmapTeamHeader} title="One row per TEAM in this cohort (each team runs one company; its driver commits). ✓ committed · ◐ draft saved · ○ nothing saved. Hover any cell for the exact value that round.">Team</div>
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
                {/* RB-2: commit state — symbol + colour, never colour alone */}
                <span
                  title={team.committed ? `Committed R${progress?.target_round ?? ''}` : team.has_saved_draft ? 'Not committed — has a saved draft' : 'Not committed — no draft saved'}
                  style={{ marginRight: 5, fontWeight: 800, color: team.committed ? '#4ade80' : team.has_saved_draft ? '#fbbf24' : '#94a3b8' }}
                >{team.committed ? '✓' : team.has_saved_draft ? '◐' : '○'}</span>
                {team.name?.substring(0, 12) || `Team ${ti + 1}`}
                {team.auto_committed_last_round && (
                  <span title="Last round was auto-committed, not played" style={{ marginLeft: 5, fontSize: 'var(--type-caption)', fontWeight: 800, padding: '1px 5px', borderRadius: 999, background: 'rgba(245,158,11,0.14)', border: '1px solid rgba(245,158,11,0.4)', color: '#fbbf24' }}>auto</span>
                )}
                {/* Negotiation rooms (Phase 2): live flag while a room is open */}
                {team.current?.negotiating && (
                  <span
                    title={`In negotiation with ${String(team.current.negotiating).replace(/^the_/, '').replace(/_/g, ' ')}`}
                    style={{ marginLeft: 6, fontSize: 'var(--type-caption)', fontWeight: 800, padding: '1px 6px', borderRadius: 999, background: 'rgba(239,68,68,0.14)', border: '1px solid rgba(239,68,68,0.4)', color: '#f87171' }}
                  >🤝 negotiating</span>
                )}
                {!team.committed && (
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); handleCommitTeam(team); }}
                    disabled={committingTeam === team.session_id}
                    title={team.has_saved_draft ? "Auto-commit this team from saved draft" : "Auto-commit this team with default options"}
                    style={{
                      marginLeft: 6,
                      fontSize: 'var(--type-caption)',
                      fontWeight: 700,
                      padding: '1px 6px',
                      borderRadius: 6,
                      border: '1px solid rgba(245,158,11,0.5)',
                      background: 'var(--caution-soft)',
                      color: 'var(--caution-text)',
                      cursor: committingTeam === team.session_id ? 'wait' : 'pointer',
                    }}
                  >
                    {committingTeam === team.session_id ? '…' : '⚡ Commit'}
                  </button>
                )}
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
              <div className={styles.heatmapCell} style={{ width: '120px', justifyContent: 'flex-start', paddingLeft: '8px', fontSize: 'var(--type-caption)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
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
      {confirmModal}
    </div>
  );
}
