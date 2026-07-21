'use client';
/**
 * ArchiveAccordion — collapsed previous-round message groups in the mailbox.
 * Phase A (player redesign): verbatim extraction from ExecutiveCockpit.js.
 */
import { useState } from 'react';

/* ── Sub-component: Archive Accordion for previous rounds ── */
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
      borderTop: '1px solid #eef0f6',
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
          background: open ? '#eef4ff' : '#f7f8fc',
          border: open ? '1px solid #c7d2fe' : '1px solid transparent',
          borderRadius: 5,
          cursor: 'pointer',
          fontSize: '0.65rem',
          fontWeight: 700,
          color: open ? '#3b5998' : '#6b7a8d',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          fontFamily: 'Inter, sans-serif',
          transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
        }}
      >
        <span>{open ? '▾' : '▸'} {roundLabel || `Round ${round}`}</span>
        <span style={{
          fontSize: '0.68rem',
          background: open ? '#c7d2fe' : '#e2e8f0',
          color: open ? '#3b5998' : '#475569',
          padding: '2px 6px',
          borderRadius: 4,
          fontWeight: 700,
        }}>{items.length}</span>
      </button>
      {open && (
        <div style={{ padding: '4px 0' }}>
          {items.map((msg, idx) => (
            <div
              key={msg.id || `archived-msg-${idx}`}
              onClick={(e) => { e.stopPropagation(); onMarkRead?.(msg.id); onExpand?.(msg); }}
              style={{
                padding: '6px 10px 6px 18px',
                fontSize: '0.65rem',
                color: '#334155',
                lineHeight: 1.5,
                borderLeft: '2px solid #c7d2fe',
                marginLeft: 10,
                marginBottom: 3,
                cursor: 'pointer',
                opacity: msg.read ? 0.7 : 1,
                borderRadius: '0 4px 4px 0',
                background: '#fafbff',
                transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
              }}
            >
              <strong style={{ fontSize: '0.65rem', color: '#334155' }}>{msg.title}</strong>
              <p style={{ margin: '2px 0 0', fontSize: '0.6rem', color: '#475569' }}>
                {msg.body?.substring(0, 80)}...
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
