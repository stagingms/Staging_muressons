'use client';

import React, { useState, useEffect } from 'react';
import PasswordInput from './PasswordInput';
import Dialog from './Dialog';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * ChangePasswordModal — Allows a player to change their password.
 * Self-contained: asks for Player ID, current password, and new password.
 *
 * Props:
 *  - isOpen: boolean
 *  - onClose: () => void
 *  - prefillPlayerId: string (optional) — pre-fills the Player ID field
 *  - isForced: boolean — if true, hides Cancel and shows a mandatory change banner
 *  - onSuccess: () => void — called after a successful password change
 */
export default function ChangePasswordModal({ isOpen, onClose, prefillPlayerId = '', isForced = false, onSuccess }) {
    const [playerId, setPlayerId] = useState(prefillPlayerId);
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    // Sync prefillPlayerId whenever it changes (e.g. after login resolves)
    useEffect(() => {
        if (prefillPlayerId) {
            setPlayerId(prefillPlayerId.toUpperCase());
        }
    }, [prefillPlayerId]);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        if (newPassword.trim().length < 8) {
            setError('New password must be at least 8 characters.');
            return;
        }
        if (newPassword !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`${API}/api/simulations/change-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: playerId.trim().toUpperCase(),
                    old_password: oldPassword,
                    new_password: newPassword.trim(),
                }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || 'Failed to change password.');
            }

            setSuccess(true);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setPlayerId(prefillPlayerId || '');
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setError(null);
        setSuccess(false);
        onClose();
    };

    const handleSuccessDone = () => {
        setPlayerId(prefillPlayerId || '');
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setError(null);
        setSuccess(false);
        if (onSuccess) onSuccess();
        else onClose();
    };

    return (
        /* A11Y-3 (UX audit #18): dialog semantics, Escape, focus trap +
           restore. When isForced the password change is mandatory, so Escape
           and backdrop-click are suppressed — the form is the only way out. */
        <Dialog
            onClose={onClose}
            dismissible={!isForced}
            labelledBy="change-password-title"
            style={{
                position: 'fixed', inset: 0, zIndex: 9999,
                background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
        >
            <div style={{
                background: '#fff', borderRadius: '14px', width: '90%', maxWidth: '420px',
                boxShadow: '0 24px 64px rgba(0,0,0,0.25)', overflow: 'hidden',
            }}>
                {/* Header */}
                <div style={{
                    padding: '1rem 1.5rem', borderBottom: '1px solid #e2e8f0',
                    background: isForced ? '#fef3c7' : '#f8fafc',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                    <h2 id="change-password-title" style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: isForced ? '#92400e' : '#1e293b' }}>
                        {isForced ? '🔒 Set Your New Password' : '🔑 Change Password'}
                    </h2>
                    {!isForced && (
                        <button onClick={handleClose} style={{ background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer', color: '#94a3b8' }}>×</button>
                    )}
                </div>

                {/* Forced change banner */}
                {isForced && !success && (
                    <div style={{
                        background: '#fffbeb', borderBottom: '1px solid #fde68a',
                        padding: '0.65rem 1.5rem', fontSize: '0.82rem', color: '#92400e',
                        display: 'flex', gap: '0.5rem', alignItems: 'flex-start',
                    }}>
                        <span>⚠️</span>
                        <span>
                            Your current password is the <strong>temporary password your facilitator gave you</strong>. You must set a personal password before continuing.
                        </span>
                    </div>
                )}

                {/* Body */}
                <div style={{ padding: '1.5rem' }}>
                    {success ? (
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>✅</div>
                            <h3 style={{ color: '#1e293b', margin: '0 0 0.5rem' }}>Password Updated</h3>
                            <p style={{ color: '#64748b', fontSize: '0.85rem' }}>
                                Your password has been changed successfully. Use it next time you log in.
                            </p>
                            <button
                                onClick={handleSuccessDone}
                                style={{
                                    marginTop: '1rem', background: '#3b82f6', color: '#fff',
                                    border: 'none', padding: '0.6rem 1.5rem', borderRadius: '8px',
                                    fontWeight: 600, cursor: 'pointer',
                                }}
                            >
                                {isForced ? 'Continue to Simulation' : 'Done'}
                            </button>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {error && (
                                <div style={{
                                    background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                                    color: '#ef4444', padding: '0.6rem', borderRadius: '6px', fontSize: '0.85rem',
                                }}>
                                    {error}
                                </div>
                            )}

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <label style={labelStyle}>Player ID</label>
                                <input
                                    type="text"
                                    value={playerId}
                                    onChange={e => setPlayerId(e.target.value.toUpperCase())}
                                    placeholder="MUR-XXX"
                                    required
                                    disabled={!!isForced && !!prefillPlayerId}
                                    style={{ ...inputStyle, opacity: isForced && prefillPlayerId ? 0.75 : 1 }}
                                />
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <label style={labelStyle}>Current Password {isForced && <span style={{ color: '#94a3b8', fontWeight: 400 }}>(the temporary password from your facilitator)</span>}</label>
                                <PasswordInput
                                    value={oldPassword}
                                    onChange={e => setOldPassword(e.target.value)}
                                    placeholder="Your current password"
                                    required
                                    style={inputStyle}
                                />
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <label style={labelStyle}>New Password</label>
                                <PasswordInput
                                    value={newPassword}
                                    onChange={e => setNewPassword(e.target.value)}
                                    placeholder="At least 8 characters"
                                    required
                                    style={inputStyle}
                                />
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <label style={labelStyle}>Confirm New Password</label>
                                <PasswordInput
                                    value={confirmPassword}
                                    onChange={e => setConfirmPassword(e.target.value)}
                                    placeholder="Re-enter new password"
                                    required
                                    style={inputStyle}
                                />
                            </div>

                            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                                {!isForced && (
                                    <button
                                        type="button"
                                        onClick={handleClose}
                                        style={{
                                            background: 'transparent', border: '1px solid #cbd5e1', color: '#475569',
                                            padding: '0.5rem 1rem', borderRadius: '6px', fontSize: '0.85rem',
                                            fontWeight: 500, cursor: 'pointer',
                                        }}
                                    >
                                        Cancel
                                    </button>
                                )}
                                {/* suppressHydrationWarning — see AdminLogin. */}
                                <button
                                    type="submit"
                                    suppressHydrationWarning
                                    disabled={loading}
                                    style={{
                                        background: '#3b82f6', color: '#fff', border: 'none',
                                        padding: '0.5rem 1.25rem', borderRadius: '6px', fontSize: '0.85rem',
                                        fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
                                        opacity: loading ? 0.6 : 1,
                                        flex: isForced ? 1 : 'unset',
                                    }}
                                >
                                    {loading ? 'Updating...' : 'Update Password'}
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </Dialog>
    );
}

const labelStyle = {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#334155',
};

const inputStyle = {
    background: '#f1f5f9',
    border: '1.5px solid #cbd5e1',
    borderRadius: '6px',
    padding: '0.7rem 0.85rem',
    color: '#1e293b',
    fontSize: '0.9rem',
    width: '100%',
    boxSizing: 'border-box',
};
