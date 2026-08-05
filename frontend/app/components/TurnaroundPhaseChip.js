'use client';

/**
 * TurnaroundPhaseChip — read-only phase indicator for the post-completion
 * Turnaround arc (P4). SLOT: KPI belt (always-glanceable state — numbers/status
 * only; deep detail lives in the facilitator console / results stage per the
 * V-D slotting rule). Renders nothing unless the arc is active.
 *
 * Props are read from the player's existing game state — this component never
 * fetches, so it stays a pure glanceable belt tile.
 *   phase       'crisis' | 'stabilisation' | 'recovery' | 'exit'
 *   round       current turnaround round (1..max)
 *   maxRounds   total arc rounds (default 4)
 *   active      whether the arc is in progress
 */

const PHASES = ['crisis', 'stabilisation', 'recovery', 'exit'];
const LABEL = { crisis: 'Crisis', stabilisation: 'Stabilise', recovery: 'Recovery', exit: 'Exit' };
const GATE = {
    crisis: 'Need: Treasury > $0 · Rep > 20',
    stabilisation: 'Need: Treasury > $10M · Rep > 45',
    recovery: 'Need: Treasury > $20M · Rep > 55',
    exit: 'Comeback complete',
};

export default function TurnaroundPhaseChip({ phase = 'crisis', round = 1, maxRounds = 4, active = false }) {
    // active defaults FALSE (was true): a mount that forgets the prop must
    // never paint a phantom "T1/4 · Crisis" chip. NOTE the name collision this
    // chip must survive: the always-on MID-SIM distress arc (engine FEATURE 25)
    // also writes `turnaround_phase` into flags on distressed sessions — this
    // chip is ONLY for the facilitator-gated POST-COMPLETION module, so callers
    // gate `active` on flags.turnaround_status === 'open' (set exclusively by
    // turnaround_engine.enter_arc after R10 + eligibility + facilitator grant).
    if (!active) return null;
    const idx = PHASES.indexOf(phase);

    return (
        <div
            role="status"
            aria-label={`Turnaround arc: ${LABEL[phase] || phase} phase, round ${round} of ${maxRounds}`}
            style={{
                display: 'flex', flexDirection: 'column', gap: '4px',
                padding: 'var(--space-2, 8px) var(--space-3, 12px)',
                background: 'var(--danger-soft)', border: '1px solid var(--danger)',
                borderRadius: 'var(--radius-chip, 6px)', minWidth: '180px',
            }}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '0.8rem' }}>🔧</span>
                <span style={{
                    fontSize: 'var(--type-caption, 0.75rem)', fontWeight: 700,
                    letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--danger-text)',
                }}>Turnaround · T{round}/{maxRounds}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                {PHASES.map((p, i) => (
                    <span key={p} style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <span style={{
                            fontSize: 'var(--type-caption)', fontWeight: 700,
                            color: i === idx ? 'var(--text-primary)'
                                 : i < idx ? 'var(--positive-text)' : 'var(--text-muted)',
                        }}>{LABEL[p]}</span>
                        {i < PHASES.length - 1 && <span style={{ color: 'var(--text-muted)', fontSize: 'var(--type-caption)' }}>›</span>}
                    </span>
                ))}
            </div>
            <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)' }}>{GATE[phase]}</div>
        </div>
    );
}
