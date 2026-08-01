'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * ConfirmModal / useConfirm — Phase 5 (F4): ONE confirmation pattern for the
 * whole admin surface.
 *
 * Replaces (a) chains of identical native confirm() dialogs, which train
 * click-through — exactly how a live cohort gets deleted — and (b) the fake
 * "Type OK to proceed" prompt (native confirm() has no typing; that guard was
 * an illusion). Modeled on the one genuinely good pattern already in the
 * codebase: Factory Reset's typed phrase.
 *
 * Tiers:
 *   1. plain   — single styled confirm (recoverable actions, e.g. soft delete)
 *   2. impact  — confirm + blast-radius preview (hard deletes, rollbacks,
 *                platform-wide toggles while players are live)
 *   3. phrase  — typed-phrase unlock (irreversible AND plural, e.g. reset-all)
 *
 * Boundary guarantee: the hook resolves a Promise<boolean> and callers keep
 * their request payloads byte-identical — only the gate in front changed.
 * Cancel means NO request is sent.
 */
export function useConfirm() {
    const [config, setConfig] = useState(null);
    const resolver = useRef(null);

    const confirm = useCallback((opts) => new Promise((resolve) => {
        resolver.current = resolve;
        setConfig(opts);
    }), []);

    const close = useCallback((result) => {
        const r = resolver.current;
        resolver.current = null;
        setConfig(null);
        r?.(result);
    }, []);

    const modal = config ? <ConfirmModal {...config} onClose={close} /> : null;
    return [confirm, modal];
}

export default function ConfirmModal({
    title,
    message,
    impact = null,
    requirePhrase = null,
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    danger = true,
    onClose,
}) {
    const [phrase, setPhrase] = useState('');
    // Trim + case-fold: a trailing space (autofill) or a mobile keyboard's
    // auto-capitalised "Delete" left the button silently locked — the user
    // typed the phrase, saw a disabled button, and reported "delete not
    // working". The friction is the TYPING, not the exact casing.
    const unlocked = !requirePhrase
        || phrase.trim().toUpperCase() === String(requirePhrase).trim().toUpperCase();

    useEffect(() => {
        const onKey = (e) => { if (e.key === 'Escape') onClose(false); };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [onClose]);

    const accent = danger ? '#ef4444' : '#10b981';

    return (
        <div
            style={{
                position: 'fixed', inset: 0, zIndex: 25000,
                background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            onClick={(e) => { if (e.target === e.currentTarget) onClose(false); }}
            role="dialog"
            aria-modal="true"
            aria-label={typeof title === 'string' ? title : 'Confirm action'}
        >
            <div style={{
                background: 'var(--bg-card, #111827)', border: '1px solid var(--border-subtle, #334155)',
                borderTop: `3px solid ${accent}`,
                borderRadius: 'var(--radius-lg, 12px)', padding: '1.75rem', maxWidth: '460px', width: '92%',
                boxShadow: '0 20px 60px rgba(0,0,0,0.35)',
            }}>
                <h2 style={{ margin: '0 0 0.75rem', fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary, #e2e8f0)' }}>
                    {title}
                </h2>

                {message && (
                    <div style={{ fontSize: '0.86rem', color: 'var(--text-secondary, #94a3b8)', lineHeight: 1.55, marginBottom: impact ? '0.75rem' : '1.25rem' }}>
                        {message}
                    </div>
                )}

                {impact && (
                    <div style={{
                        padding: '0.6rem 0.9rem', borderRadius: '8px', marginBottom: '1.25rem',
                        background: danger ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.08)',
                        border: `1px solid ${danger ? 'rgba(239,68,68,0.25)' : 'rgba(245,158,11,0.3)'}`,
                        fontSize: '0.8rem', fontWeight: 600,
                        color: danger ? '#f87171' : '#fbbf24', lineHeight: 1.5,
                    }}>
                        {impact}
                    </div>
                )}

                {requirePhrase && (
                    <div style={{ marginBottom: '1.25rem' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #64748b)', marginBottom: '0.4rem' }}>
                            Type <code style={{
                                background: 'rgba(239,68,68,0.12)', color: '#ef4444', padding: '2px 6px',
                                borderRadius: '3px', fontWeight: 700, fontSize: '0.72rem',
                            }}>{requirePhrase}</code> to unlock:
                        </div>
                        <input
                            type="text"
                            autoFocus
                            value={phrase}
                            onChange={(e) => setPhrase(e.target.value)}
                            placeholder={requirePhrase}
                            style={{
                                width: '100%', boxSizing: 'border-box', padding: '0.55rem 0.9rem',
                                border: `1.5px solid ${unlocked ? 'rgba(16,185,129,0.5)' : 'rgba(239,68,68,0.3)'}`,
                                borderRadius: '6px', background: 'var(--bg-body, #0b1220)',
                                color: 'var(--text-primary, #e2e8f0)', fontSize: '0.85rem',
                                fontFamily: 'var(--font-mono, monospace)', outline: 'none',
                            }}
                        />
                    </div>
                )}

                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                    <button
                        type="button"
                        autoFocus={!requirePhrase}
                        onClick={() => onClose(false)}
                        style={{
                            background: 'transparent', border: '1px solid var(--border-subtle, #475569)',
                            color: 'var(--text-secondary, #cbd5e1)', padding: '0.5rem 1.1rem', borderRadius: '6px',
                            fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer',
                        }}
                    >
                        {cancelLabel}
                    </button>
                    <button
                        type="button"
                        disabled={!unlocked}
                        onClick={() => unlocked && onClose(true)}
                        style={{
                            background: unlocked ? accent : `${accent}33`,
                            color: unlocked ? '#fff' : `${accent}88`,
                            border: 'none', padding: '0.5rem 1.25rem', borderRadius: '6px',
                            fontSize: '0.85rem', fontWeight: 700,
                            cursor: unlocked ? 'pointer' : 'not-allowed',
                        }}
                    >
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}
