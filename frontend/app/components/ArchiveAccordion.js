'use client';
/**
 * ArchiveAccordion — collapsed previous-round message groups in the mailbox.
 * Phase A (player redesign): verbatim extraction from ExecutiveCockpit.js.
 */
import { useState } from 'react';

/* ── Sub-component: Archive Accordion for previous rounds ──
 *
 * A11Y-M4 (WCAG 1.4.3) — real-browser pass, 2026-08-02.
 * Every surface and every colour in here was hard-coded light: #f7f8fc and
 * #eef4ff headers, a #fafbff message row, slate text. Inside a rail that is
 * #0e1222 in dark mode, this rendered as a white slab holding the ARCHIVE of
 * the very messages listed above it in theme-aware colours — the same
 * conversation in two different themes, six pixels apart. Its own header
 * label also measured 4.13:1 on its own light background, so it failed in
 * light mode too.
 *
 * Everything now runs through the token tiers used by the live mailbox item,
 * so the archive matches the list it archives. */
export default function ArchiveAccordion({ round, roundLabel, items, onMarkRead, onExpand }) {
  const [open, setOpen] = useState(false);
  const handleToggle = (e) => {
    e.stopPropagation();
    e.preventDefault();
    setOpen(prev => !prev);
  };
  return (
    <div style={{
      marginTop: 6,
      borderTop: '1px solid var(--ck-border, rgba(148,163,184,0.12))',
    }}>
      <button
        onClick={handleToggle}
        type="button"
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 10px',
          background: open ? 'rgba(99, 102, 241, 0.14)' : 'var(--ck-surface-2, rgba(255,255,255,0.03))',
          border: open ? '1px solid rgba(99, 102, 241, 0.40)' : '1px solid transparent',
          borderRadius: 5,
          cursor: 'pointer',
          fontSize: '0.65rem',
          fontWeight: 700,
          color: open ? 'var(--accent-text)' : 'var(--text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          fontFamily: 'Inter, sans-serif',
          transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
        }}
      >
        <span>{open ? '▾' : '▸'} {roundLabel || `Round ${round}`}</span>
        <span style={{
          fontSize: '0.68rem',
          background: open ? 'rgba(99, 102, 241, 0.22)' : 'var(--ck-surface-2, rgba(255,255,255,0.06))',
          color: open ? 'var(--accent-text)' : 'var(--text-secondary)',
          padding: '2px 6px',
          borderRadius: 4,
          fontWeight: 700,
        }}>{items.length}</span>
      </button>
      {open && (
        <div style={{ padding: '4px 0' }}>
          {items.map((msg, idx) => (
            <button
              type="button"
              key={msg.id || `archived-msg-${idx}`}
              onClick={(e) => { e.stopPropagation(); onMarkRead?.(msg.id); onExpand?.(msg); }}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                background: 'none', font: 'inherit',
                padding: '6px 10px 6px 18px',
                fontSize: '0.65rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
                borderLeft: '2px solid rgba(99, 102, 241, 0.45)',
                marginLeft: 10,
                marginBottom: 3,
                cursor: 'pointer',
                /* A11Y-M5: was 0.7. Opacity composites text toward its surface
                   — the F8 / F16 trap — and "read" is the state a message
                   spends the rest of the game in. 0.85 keeps the read/unread
                   affordance and keeps the body above 4.5:1. */
                opacity: msg.read ? 0.85 : 1,
                borderRadius: '0 4px 4px 0',
                background: 'var(--ck-surface-2, rgba(255,255,255,0.03))',
                transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
              }}
            >
              <strong style={{ fontSize: '0.65rem', color: 'var(--text-primary)' }}>{msg.title}</strong>
              <p style={{ margin: '2px 0 0', fontSize: '0.62rem', color: 'var(--text-secondary)' }}>
                {msg.body?.substring(0, 80)}...
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
