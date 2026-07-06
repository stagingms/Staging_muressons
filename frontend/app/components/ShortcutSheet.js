'use client';

/**
 * ShortcutSheet — Phase 6 (F12): discoverable keyboard shortcuts.
 * Toggled with '?' on both admin dashboards. Purely presentational.
 */
export default function ShortcutSheet({ shortcuts = [], onClose }) {
    return (
        <div
            style={{
                position: 'fixed', inset: 0, zIndex: 24000,
                background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(3px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}
            role="dialog"
            aria-modal="true"
            aria-label="Keyboard shortcuts"
        >
            <div style={{
                background: 'var(--bg-card, #111827)', border: '1px solid var(--border-subtle, #334155)',
                borderRadius: '12px', padding: '1.5rem 1.75rem', width: '92%', maxWidth: '440px',
                boxShadow: '0 20px 60px rgba(0,0,0,0.35)',
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary, #e2e8f0)' }}>
                        ⌨️ Keyboard shortcuts
                    </h2>
                    <button
                        onClick={onClose}
                        style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: 'var(--text-muted, #94a3b8)' }}
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {shortcuts.map(([keys, desc]) => (
                        <div key={keys} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', fontSize: '0.82rem' }}>
                            <span style={{ color: 'var(--text-secondary, #cbd5e1)' }}>{desc}</span>
                            <code style={{
                                background: 'rgba(148,163,184,0.12)', border: '1px solid var(--border-subtle, #334155)',
                                borderRadius: '5px', padding: '1px 8px', color: 'var(--text-primary, #e2e8f0)',
                                fontSize: '0.75rem', whiteSpace: 'nowrap',
                            }}>{keys}</code>
                        </div>
                    ))}
                </div>
                <div style={{ marginTop: '1rem', fontSize: '0.72rem', color: 'var(--text-muted, #64748b)' }}>
                    Press ? or Esc to close
                </div>
            </div>
        </div>
    );
}
