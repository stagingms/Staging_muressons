import React from 'react';

export default function EngineEventsPanel({ globalState }) {
  const flags = globalState?.active_event_flags || {};
  const events = [];

  if (flags.inflation_active || globalState?.inflation_index > 1.0) {
    const rate = ((globalState?.inflation_index - 1) * 100).toFixed(1);
    // fallback if inflation_index not present but active
    const displayRate = rate !== "NaN" && rate > 0 ? rate : "2.5";
    events.push({ icon: '📈', color: '#f59e0b', text: `Inflation increased OPEX by ${displayRate}%.` });
  }
  if (flags.tech_lock_in_active) {
    events.push({ icon: '🔒', color: '#ef4444', text: `Technology Lock-In active — synergy penalty on non-dominant BUs.` });
  }
  if (flags.greenwashing_penalty_active) {
    events.push({ icon: '🎭', color: '#ef4444', text: `Greenwashing detected! Severe reputation penalty applied.` });
  }
  if (flags.cogs_penalty_ratio > 1) {
    events.push({ icon: '⚙️', color: '#f59e0b', text: `Supply chain drag increased COGS by ${((flags.cogs_penalty_ratio - 1) * 100).toFixed(1)}%.` });
  }
  if (flags.cannibalization_active) {
    events.push({ icon: '🔄', color: '#f59e0b', text: `Product cannibalization reduced revenue efficiency.` });
  }

  if (events.length === 0) return null;

  return (
    <div style={{
      marginTop: 12, padding: '10px 14px', borderRadius: 8,
      background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.2)',
    }}>
      <div style={{ fontSize: '0.65rem', fontWeight: 800, color: '#f59e0b', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
        <span>🔍</span> What Happened This Round (Engine Events)
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {events.map((evt, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>{evt.icon}</span>
            <span style={{ fontSize: '0.75rem', color: '#e2e8f0' }}>{evt.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
