'use client';

import { useState, useEffect, useCallback } from 'react';
import { useConfirm } from './ConfirmModal';
import styles from './StudentBonuses.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const BADGES = [
    { key: 'mvp', icon: '🏆', label: 'MVP' },
    { key: 'sustainability', icon: '🌍', label: 'Sustainability Champion' },
    { key: 'innovation', icon: '💡', label: 'Innovation Award' },
    { key: 'collaboration', icon: '🤝', label: 'Best Collaboration' },
    { key: 'strategy', icon: '🎯', label: 'Strategic Thinker' },
    { key: 'resilience', icon: '🛡️', label: 'Resilience Award' },
];

export default function StudentBonuses({ sessionId }) {
    const [bonuses, setBonuses] = useState([]);
    const [playerName, setPlayerName] = useState('');
    const [points, setPoints] = useState(10);
    const [reason, setReason] = useState('');
    const [badge, setBadge] = useState('');
    const [loading, setLoading] = useState(false);
    // Phase R1 (V2-4): visible failure states for award/revoke.
    const [error, setError] = useState('');
    const [confirm, confirmModal] = useConfirm();

    const fetchBonuses = useCallback(async () => {
        if (!sessionId) return;
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/bonuses`, { credentials: 'include' });
            if (res.ok) { const data = await res.json(); setBonuses(data.bonuses || []); }
        } catch { /* offline */ }
    }, [sessionId]);

    useEffect(() => { fetchBonuses(); }, [fetchBonuses]);

    const handleAward = async (e) => {
        e.preventDefault();
        if (!playerName.trim()) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/bonuses`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ player_name: playerName.trim(), points, reason: reason.trim(), badge: badge || null }),
            });
            if (res.ok) {
                const b = await res.json(); setBonuses(prev => [b, ...prev]);
                setPlayerName(''); setReason(''); setBadge(''); setPoints(10); setError('');
            } else {
                const eb = await res.json().catch(() => ({}));
                setError(`❌ Bonus NOT awarded (${eb.detail || `HTTP ${res.status}`}) — the form is preserved.`);
            }
        } catch { setError('❌ Bonus NOT awarded — network error. The form is preserved.'); }
        finally { setLoading(false); }
    };

    const handleRevoke = async (bonusId) => {
        const bonus = bonuses.find(b => b.bonus_id === bonusId);
        const ok = await confirm({
            title: 'Revoke Bonus',
            message: `Revoke this bonus${bonus ? ` for ${bonus.player_name}` : ''}?`,
            impact: 'The bonus points and badge will be removed from the player score.',
            confirmLabel: 'Revoke Bonus',
            danger: true,
        });
        if (!ok) return;
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/bonuses/${bonusId}`, { method: 'DELETE', credentials: 'include' });
            if (res.ok) { setBonuses(prev => prev.filter(b => b.bonus_id !== bonusId)); setError(''); }
            else setError(`❌ Bonus NOT revoked (HTTP ${res.status}) — it still counts toward the player.`);
        } catch { setError('❌ Bonus NOT revoked — network error. It still counts toward the player.'); }
    };

    if (!sessionId) {
        return (
            <div className={styles.container}><div className={styles.header}><span className={styles.icon}>🏅</span><div><h2 className={styles.title}>Student Bonuses & Awards</h2><p className={styles.subtitle}>Select a session from the Leaderboard.</p></div></div><div className={styles.empty}>Select a session first.</div></div>
        );
    }

    const totalPoints = bonuses.reduce((s, b) => s + (b.points || 0), 0);

    return (
        <div className={styles.container}>
            <div className={styles.header}><span className={styles.icon}>🏅</span><div><h2 className={styles.title}>Student Bonuses & Awards</h2><p className={styles.subtitle}>Reward exceptional performance with bonus points and badges.</p></div></div>

            {error && (
                <div style={{
                    margin: '0.5rem 0', padding: '8px 12px', borderRadius: '6px',
                    background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                    color: '#ef4444', fontSize: '0.82rem', fontWeight: 600,
                }}>{error}</div>
            )}

            <form className={styles.form} onSubmit={handleAward}>
                <div className={styles.formGrid}>
                    <input className={styles.input} placeholder="Player name..." value={playerName} onChange={(e) => setPlayerName(e.target.value)} required />
                    <input className={styles.inputSmall} type="number" min="1" max="100" value={points} onChange={(e) => setPoints(parseInt(e.target.value) || 10)} />
                    <input className={styles.input} placeholder="Reason (optional)" value={reason} onChange={(e) => setReason(e.target.value)} />
                </div>
                <div className={styles.badgeRow}>
                    {BADGES.map(b => (
                        <button key={b.key} type="button" className={`${styles.badgeBtn} ${badge === b.key ? styles.badgeActive : ''}`} onClick={() => setBadge(badge === b.key ? '' : b.key)}>
                            {b.icon} {b.label}
                        </button>
                    ))}
                </div>
                <button className={styles.awardBtn} type="submit" disabled={loading || !playerName.trim()}>{loading ? '⏳' : '🏆'} Award Bonus</button>
            </form>

            <div className={styles.summary}>Total awarded: <strong>{bonuses.length}</strong> bonuses — <strong>{totalPoints}</strong> points</div>

            <div className={styles.bonusList}>
                {bonuses.length === 0 ? <div className={styles.empty}>No bonuses awarded yet.</div> : bonuses.map(b => (
                    <div key={b.bonus_id} className={styles.bonusCard}>
                        <div className={styles.bonusIcon}>{b.badge?.icon || '⭐'}</div>
                        <div className={styles.bonusInfo}>
                            <strong>{b.player_name}</strong>
                            <span className={styles.bonusPoints}>+{b.points} pts</span>
                            {b.badge && <span className={styles.bonusBadge}>{b.badge.label}</span>}
                            {b.reason && <p className={styles.bonusReason}>{b.reason}</p>}
                            <span className={styles.bonusTime}>{new Date(b.created_at).toLocaleString()}</span>
                        </div>
                        <button className={styles.revokeBtn} onClick={() => handleRevoke(b.bonus_id)}>🗑️</button>
                    </div>
                ))}
            </div>
            {confirmModal}
        </div>
    );
}
