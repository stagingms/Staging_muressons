'use client';

/**
 * CohortSelector — Phase 3 (F2/G5): the single, global way to choose which
 * cohort the session-scoped tools (Override, Undo, Messages, Debrief, …) act
 * on. It writes to the same selectedSession state every consumer already
 * reads, so per-tab pickers become synchronized views of one selection
 * instead of three competing selection models.
 *
 * Pure UI: emits the same session_id values the previous pickers emitted —
 * no change to which requests are sent or how.
 */
export default function CohortSelector({
    leaderboard = [],
    selectedSession = null,
    onSelect,
    compact = false,
    label = '🎯 Target cohort:',
}) {
    const cohorts = leaderboard.filter(s => !s.player_id);

    return (
        <label style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
            fontSize: compact ? '0.72rem' : '0.8rem',
            color: 'var(--text-muted)', fontWeight: 600, whiteSpace: 'nowrap',
        }}>
            {!compact && <span>{label}</span>}
            <select
                value={selectedSession || ''}
                onChange={e => onSelect?.(e.target.value || null)}
                title="Which cohort session-scoped tools (Override, Undo, Messages, Debrief…) act on"
                style={{
                    padding: compact ? '0.25rem 0.5rem' : '0.4rem 0.7rem',
                    borderRadius: '6px', border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-body)', color: 'var(--text-primary)',
                    fontSize: compact ? '0.72rem' : '0.82rem', maxWidth: '280px',
                    cursor: 'pointer',
                }}
            >
                <option value=''>— Select a cohort —</option>
                {cohorts.map(c => (
                    <option key={c.session_id} value={c.session_id}>
                        {(c.cohort_name || c.session_id.slice(0, 12))} · R{c.round_number || 1}
                    </option>
                ))}
            </select>
        </label>
    );
}
