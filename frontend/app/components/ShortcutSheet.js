'use client';

/**
 * ShortcutSheet — Phase 6 (F12): discoverable keyboard shortcuts.
 * Toggled with '?' on both admin dashboards.
 *
 * PHASE 8. This hand-rolled its own role="dialog" overlay: no focus trap, no
 * focus restore. Tab walked straight out of it into the dashboard behind
 * (2.1.2), and closing it dropped focus on <body> rather than returning it to
 * whatever opened it (2.4.3). Both parents already bound Escape, so the
 * "Press ? or Esc to close" line was true — it was the only true part.
 *
 * A keyboard-shortcut sheet that a keyboard user cannot navigate is the
 * sharpest version of this defect in the product.
 *
 * Dialog is a wrapper, not a redesign: className, styles and inner markup are
 * unchanged. Escape now comes from Dialog (topmost-only, so it cannot collapse
 * a stack), which is strictly better than the parents' unconditional handler.
 */
import Dialog from './Dialog';

export default function ShortcutSheet({ shortcuts = [], onClose }) {
    return (
        <Dialog
            onClose={onClose}
            label="Keyboard shortcuts"
            style={{
                position: 'fixed', inset: 0, zIndex: 24000,
                background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(3px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
        >
            <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                borderRadius: '12px', padding: '1.5rem 1.75rem', width: '92%', maxWidth: '440px',
                boxShadow: '0 20px 60px rgba(0,0,0,0.35)',
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                        ⌨️ Keyboard shortcuts
                    </h2>
                    <button
                        onClick={onClose}
                        style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: 'var(--text-muted)' }}
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {shortcuts.map(([keys, desc]) => (
                        <div key={keys} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', fontSize: '0.82rem' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>{desc}</span>
                            <code style={{
                                background: 'rgba(148,163,184,0.12)', border: '1px solid var(--border-subtle)',
                                borderRadius: '5px', padding: '1px 8px', color: 'var(--text-primary)',
                                fontSize: '0.75rem', whiteSpace: 'nowrap',
                            }}>{keys}</code>
                        </div>
                    ))}
                </div>
                <div style={{ marginTop: '1rem', fontSize: 'var(--type-caption)', color: 'var(--text-muted)' }}>
                    Press ? or Esc to close
                </div>
            </div>
        </Dialog>
    );
}
