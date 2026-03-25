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
          position: 'fixed', bottom: 42, left: '50%', transform: 'translateX(-50%)',
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
    <div style={{
      position: 'fixed', bottom: 42, left: '50%', transform: 'translateX(-50%)',
      background: 'rgba(255,255,255,0.97)', backdropFilter: 'blur(12px)',
      borderRadius: 14, padding: '10px 16px', zIndex: 8000,
      boxShadow: '0 4px 20px rgba(0,0,0,0.12)', border: '1px solid #e2e8f0',
      fontFamily: 'Inter, sans-serif', display: 'flex', alignItems: 'center', gap: 8,
      maxWidth: '90vw',
    }}>
      {steps.map((step, i) => (
        <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 5,
            padding: '6px 14px', borderRadius: 8,
            background: step.done ? '#f0fdf4' : '#f8fafc',
            border: `1px solid ${step.done ? '#bbf7d0' : '#e2e8f0'}`,
            fontSize: '0.75rem', fontWeight: 600,
            color: step.done ? '#15803d' : '#64748b',
            transition: 'all 0.2s',
            whiteSpace: 'nowrap',
          }}>
            <span style={{ fontSize: '0.85rem' }}>{step.done ? '✅' : step.icon}</span>
            {step.label}
          </div>
          {i < steps.length - 1 && (
            <span style={{ color: step.done ? '#bbf7d0' : '#d1d5db', fontSize: '0.7rem' }}>→</span>
          )}
        </div>
      ))}
      <button
        onClick={() => setCollapsed(true)}
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          fontSize: '0.65rem', color: '#94a3b8', marginLeft: 4,
          padding: '2px 4px',
        }}
      >✕</button>
    </div>
  );
}
