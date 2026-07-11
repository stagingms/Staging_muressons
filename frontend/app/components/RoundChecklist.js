'use client';

/**
 * RoundChecklist — Persistent progress bar showing round completion steps.
 * Improvement #1.1: Progress Tracker
 *
 * V-C (player v2, V-6): docked, not floating. The old version was
 * position:fixed (escaping its in-flow mount point and overlapping option
 * cards) and dismissible via ✕ — a flow indicator should never cover the
 * work or disappear. It now renders in normal flow where it is mounted
 * (bottom of the center console), always visible, never overlapping.
 */
export default function RoundChecklist({
  roundNumber,
  hasReadBriefing,
  hasCompletedStakeholderMap,
  hasSubmittedMatrix,
  hasDecision,
  hasAllocated,
  hasCommitted,
}) {
  const steps = [];

  steps.push({ id: 'briefing', label: 'Read Briefing', done: hasReadBriefing !== false, icon: '📖' });

  if (roundNumber === 1) {
    steps.push({ id: 'stakeholder', label: 'Stakeholder Map', done: hasCompletedStakeholderMap, icon: '⚖️' });
  }
  if (roundNumber === 2) {
    steps.push({ id: 'csrd', label: 'CSRD Assessment', done: hasSubmittedMatrix, icon: '📋' });
  }

  steps.push({ id: 'decision', label: 'Strategic Decision', done: hasDecision, icon: '🎯' });
  steps.push({ id: 'allocation', label: 'Capital Allocation', done: hasAllocated, icon: '💰' });
  steps.push({ id: 'commit', label: 'Commit Turn', done: hasCommitted, icon: '✅' });

  const completed = steps.filter(s => s.done).length;

  return (
    <>
      <style>{`
        .checklist-wrapper {
          /* V-C (V-6): in-flow, docked by the mount point — no fixed, no z-war */
          background: rgba(255,255,255,0.98);
          border-radius: 14px;
          padding: 10px 16px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.12);
          border: 1px solid #e2e8f0;
          font-family: Inter, sans-serif;
          display: flex;
          flex-wrap: nowrap;
          justify-content: center;
          align-items: center;
          gap: 8px;
          width: max-content;
          max-width: 100%;
          margin: 0 auto;
          white-space: nowrap;
        }
        .checklist-item {
          display: flex; align-items: center; gap: 5px;
          padding: 6px 14px; border-radius: 8px;
          font-size: 0.75rem; font-weight: 600;
          transition: background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s;
        }
        .checklist-icon { font-size: 0.85rem; }
        .checklist-arrow { font-size: 0.7rem; }
        
        @media (max-width: 1300px) {
          .checklist-wrapper { padding: 8px 12px; gap: 6px; }
          .checklist-item { font-size: 0.7rem; padding: 5px 10px; gap: 4px; }
          .checklist-icon { font-size: 0.75rem; }
        }
        @media (max-width: 1000px) {
          .checklist-wrapper { padding: 6px 10px; gap: 4px; }
          .checklist-item { font-size: 0.6rem; padding: 4px 8px; gap: 3px; }
          .checklist-icon { font-size: 0.65rem; }
          .checklist-arrow { font-size: 0.6rem; }
        }
        @media (max-width: 800px) {
          .checklist-wrapper { transform: scale(0.85); transform-origin: bottom center; }
        }
      `}</style>
      <div className="checklist-wrapper">
        {steps.map((step, i) => (
          <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div className="checklist-item" style={{
              background: step.done ? '#f0fdf4' : '#f8fafc',
              border: `1px solid ${step.done ? '#bbf7d0' : '#e2e8f0'}`,
              color: step.done ? '#15803d' : '#64748b',
            }}>
              <span className="checklist-icon">{step.done ? '✅' : step.icon}</span>
              {step.label}
            </div>
            {i < steps.length - 1 && (
              <span className="checklist-arrow" style={{ color: step.done ? '#bbf7d0' : '#d1d5db' }}>→</span>
            )}
          </div>
        ))}
        {/* V-C (V-6): ✕ removed — a flow indicator is not dismissible. */}
        <span style={{ fontSize: '0.65rem', color: '#94a3b8', marginLeft: 4, fontWeight: 700 }}>
          {completed}/{steps.length}
        </span>
      </div>
    </>
  );
}
