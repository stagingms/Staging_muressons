'use client';
import { useState } from 'react';

/**
 * RoundChecklist — Persistent progress bar showing round completion steps.
 * Improvement #1.1: Progress Tracker
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
  const [collapsed, setCollapsed] = useState(false);

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
  const total = steps.length;
  const pct = Math.round((completed / total) * 100);

  if (collapsed) {
    return (
      <div
        onClick={() => setCollapsed(false)}
        style={{
          background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(8px)',
          borderRadius: 20, padding: '6px 18px', zIndex: 8000,
          fontSize: '0.78rem', fontWeight: 700, color: '#475569',
          cursor: 'pointer', boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
          border: '1px solid #e2e8f0', fontFamily: 'Inter, sans-serif',
          display: 'flex', alignItems: 'center', gap: 6,
        }}
      >
        <div style={{
          width: 18, height: 18, borderRadius: '50%',
          background: pct === 100 ? '#16a34a' : `conic-gradient(#6366f1 ${pct * 3.6}deg, #e2e8f0 0deg)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            width: 12, height: 12, borderRadius: '50%', background: '#fff',
            fontSize: '0.5rem', fontWeight: 800, display: 'flex',
            alignItems: 'center', justifyContent: 'center', color: '#6366f1',
          }}>{completed}</div>
        </div>
        {completed}/{total}
      </div>
    );
  }

  return (
    <>
      <style>{`
        .checklist-wrapper {
          position: fixed;
          bottom: 30px;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(255,255,255,0.97);
          backdrop-filter: blur(12px);
          border-radius: 14px;
          padding: 10px 16px;
          z-index: 8000;
          box-shadow: 0 4px 20px rgba(0,0,0,0.12);
          border: 1px solid #e2e8f0;
          font-family: Inter, sans-serif;
          display: flex;
          flex-wrap: nowrap;
          justify-content: center;
          align-items: center;
          gap: 8px;
          width: max-content;
          max-width: 90vw;
          white-space: nowrap;
        }
        .checklist-item {
          display: flex; align-items: center; gap: 5px;
          padding: 6px 14px; border-radius: 8px;
          font-size: 0.75rem; font-weight: 600;
          transition: all 0.2s;
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
          .checklist-wrapper { transform: translateX(-50%) scale(0.85); transform-origin: bottom center; }
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
        <button
          onClick={() => setCollapsed(true)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: '0.65rem', color: '#94a3b8', marginLeft: 4,
            padding: '2px 4px', flexShrink: 0,
          }}
        >✕</button>
      </div>
    </>
  );
}
