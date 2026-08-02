'use client';
import React from 'react';

/**
 * PanelEmptyState (D5) — a small, consistent placeholder so an async panel
 * never renders a blank region when a fetch fails, is loading, or has no data.
 * Purely presentational; no fetch, no state. Drop it into a panel's
 * loading/error/empty branch.
 *
 * Props:
 *   - reason:  'loading' | 'unavailable' | 'empty'  (default 'unavailable')
 *   - label:   optional custom message (overrides the default for the reason)
 *   - compact: tighter padding for small panels
 */
const PRESETS = {
  loading:     { icon: '⏳', text: 'Loading…' },
  unavailable: { icon: '🔌', text: 'Temporarily unavailable — retrying shortly.' },
  empty:       { icon: '📭', text: 'Nothing to show yet.' },
};

export default function PanelEmptyState({ reason = 'unavailable', label, compact = false }) {
  const preset = PRESETS[reason] || PRESETS.unavailable;
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: 6, textAlign: 'center',
        padding: compact ? '0.75rem' : '1.5rem 1rem',
        color: 'var(--text-muted, #8899a6)', fontSize: '0.82rem', lineHeight: 1.5,
      }}
    >
      <span aria-hidden="true" style={{ fontSize: compact ? '1.1rem' : '1.5rem', opacity: 0.8 }}>{preset.icon}</span>
      <span>{label || preset.text}</span>
    </div>
  );
}
