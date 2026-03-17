'use client';

import React, { useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * ChangePasswordModal — Allows a logged-in player to change their password.
 * Self-contained: asks for Player ID, current password, and new password.
 *
 * Props:
 *  - isOpen: boolean
 *  - onClose: () => void
 */
export default function ChangePasswordModal({ isOpen, onClose }) {
    const [playerId, setPlayerId] = useState('');
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        if (newPassword.trim().length < 3) {
            setError('New password must be at least 3 characters.');
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
        setPlayerId('');
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setError(null);
        setSuccess(false);
        onClose();
    };

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 9999,
            background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
            <div style={{
                background: '#fff', borderRadius: '12px', width: '90%', maxWidth: '400px',
                boxShadow: '0 20px 60px rgba(0,0,0,0.2)', overflow: 'hidden',
            }}>
                {/* Header */}
                <div style={{
                    padding: '1rem 1.5rem', borderBottom: '1px solid #e2e8f0',
                    background: '#f8fafc', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                    <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>
                        🔑 Change Password
                    </h2>
                    <button onClick={handleClose} style={{ background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer', color: '#94a3b8' }}>×</button>
                </div>

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
                                onClick={handleClose}
                                style={{
                                    marginTop: '1rem', background: '#3b82f6', color: '#fff',
                                    border: 'none', padding: '0.6rem 1.5rem', borderRadius: '8px',
                                    fontWeight: 600, cursor: 'pointer',
                                }}
                            >
                                Done
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
                                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>Player ID</label>
                                <input
                                    type="text"
                                    value={playerId}
                                    onChange={e => setPlayerId(e.target.value)}
                                    placeholder="MUR-XXX"
                                    required
                                    style={inputStyle}
                                />
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>Current Password</label>
                                <input
                                    type="password"
                                    value={oldPassword}
                                    onChange={e => setOldPassword(e.target.value)}
                                    placeholder="Your current password"
                                    required
                                    style={inputStyle}
                                />
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>New Password</label>
                                <input
                                    type="password"
                                    value={newPassword}
                                    onChange={e => setNewPassword(e.target.value)}
                                    placeholder="At least 3 characters"
                                    required
                                    style={inputStyle}
                                />
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>Confirm New Password</label>
                                <input
                                    type="password"
                                    value={confirmPassword}
                                    onChange={e => setConfirmPassword(e.target.value)}
                                    placeholder="Re-enter new password"
                                    required
                                    style={inputStyle}
                                />
                            </div>

                            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
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
                                <button
                                    type="submit"
                                    disabled={loading}
                                    style={{
                                        background: '#3b82f6', color: '#fff', border: 'none',
                                        padding: '0.5rem 1.25rem', borderRadius: '6px', fontSize: '0.85rem',
                                        fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
                                        opacity: loading ? 0.6 : 1,
                                    }}
                                >
                                    {loading ? 'Updating...' : 'Update Password'}
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}

const inputStyle = {
    background: '#f1f5f9',
    border: '1.5px solid #cbd5e1',
    borderRadius: '6px',
    padding: '0.7rem 0.85rem',
    color: '#1e293b',
    fontSize: '0.9rem',
};
