'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './BulkMessaging.module.css';
import { formatSessionId } from '../utils/sessionUtils';

const API = process.env.NEXT_PUBLIC_API_URL || '';


export default function BulkMessaging({ leaderboard = [] }) {
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [selectedSessions, setSelectedSessions] = useState([]);
    const [scheduledRound, setScheduledRound] = useState('');
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    // Phase R1 (V2-4): a failed broadcast must be loudly visible — the old
    // handler had no failure branch at all.
    const [error, setError] = useState('');

    const fetchHistory = useCallback(async () => {
        try {
            const res = await fetch(`${API}/api/admin/broadcast/history`, { credentials: 'include' });
            if (res.ok) { const data = await res.json(); setHistory(data.broadcasts || []); }
        } catch { /* offline */ }
    }, []);

    useEffect(() => { fetchHistory(); }, [fetchHistory]);

    const toggleSession = (sid) => {
        setSelectedSessions(prev => prev.includes(sid) ? prev.filter(s => s !== sid) : [...prev, sid]);
    };

    const selectAll = () => setSelectedSessions(leaderboard.map(s => s.session_id));
    const clearSelection = () => setSelectedSessions([]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!title.trim() || !body.trim()) return;
        setLoading(true);
        setResult(null);
        setError('');
        try {
            const res = await fetch(`${API}/api/admin/broadcast`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    title: title.trim(),
                    body: body.trim(),
                    target_sessions: selectedSessions,
                    scheduled_round: scheduledRound ? parseInt(scheduledRound) : null,
                }),
            });
            if (res.ok) {
                const data = await res.json();
                setResult(data);
                setTitle(''); setBody(''); setScheduledRound('');
                fetchHistory();
            } else {
                const eb = await res.json().catch(() => ({}));
                setError(`❌ Broadcast NOT sent (${eb.detail || `HTTP ${res.status}`}) — your message is preserved above. Retry when ready.`);
            }
        } catch {
            setError('❌ Broadcast NOT sent — network error. Your message is preserved above.');
        }
        finally { setLoading(false); }
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📢</span>
                <div>
                    <h2 className={styles.title}>Bulk Messaging</h2>
                    <p className={styles.subtitle}>Broadcast messages to all or selected cohorts.</p>
                </div>
            </div>

            <form className={styles.form} onSubmit={handleSend}>
                <input className={styles.input} placeholder="Message title" value={title} onChange={(e) => setTitle(e.target.value)} required />
                <textarea className={styles.textarea} placeholder="Message body..." value={body} onChange={(e) => setBody(e.target.value)} rows={4} required />

                <div className={styles.targetSection}>
                    <div className={styles.targetHeader}>
                        <span className={styles.targetLabel}>Target ({selectedSessions.length > 0 ? `${selectedSessions.length} selected` : 'All cohorts'})</span>
                        <button type="button" className={styles.linkBtn} onClick={selectAll}>Select All</button>
                        <button type="button" className={styles.linkBtn} onClick={clearSelection}>Clear</button>
                    </div>
                    <div className={styles.sessionChips}>
                        {leaderboard.map(s => (
                            <button
                                key={s.session_id}
                                type="button"
                                className={`${styles.chip} ${selectedSessions.includes(s.session_id) ? styles.chipActive : ''}`}
                                onClick={() => toggleSession(s.session_id)}
                            >
                                {s.cohort_name || formatSessionId(s)}
                            </button>
                        ))}
                    </div>
                </div>

                <div className={styles.scheduleRow}>
                    <label className={styles.scheduleLabel}>Schedule for round:</label>
                    <input className={styles.roundInput} type="number" min="1" max="10" placeholder="—" value={scheduledRound} onChange={(e) => setScheduledRound(e.target.value)} />
                    <span className={styles.scheduleHint}>(leave empty to send immediately)</span>
                </div>

                <button className={styles.sendBtn} type="submit" disabled={loading || !title.trim() || !body.trim()}>
                    {loading ? '⏳ Sending...' : scheduledRound ? `📅 Schedule for R${scheduledRound}` : '📢 Broadcast Now'}
                </button>
            </form>

            {error && (
                <div style={{
                    marginTop: '0.75rem', padding: '8px 12px', borderRadius: '6px',
                    background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                    color: '#ef4444', fontSize: '0.82rem', fontWeight: 600,
                }}>{error}</div>
            )}
            {result && (
                <div className={styles.success}>
                    ✅ {result.status === 'scheduled' ? `Scheduled for Round ${result.scheduled_round}` : `Sent to ${result.delivered_to?.length || 0} session(s)`}
                </div>
            )}

            {/* ── History ── */}
            {history.length > 0 && (
                <div className={styles.historySection}>
                    <h3 className={styles.historyTitle}>Broadcast History</h3>
                    {history.map(b => (
                        <div key={b.broadcast_id} className={styles.historyCard}>
                            <div className={styles.historyHeader}>
                                <strong>{b.title}</strong>
                                <span className={`${styles.statusBadge} ${b.status === 'sent' ? styles.statusSent : styles.statusScheduled}`}>
                                    {b.status}
                                </span>
                            </div>
                            <p className={styles.historyBody}>{b.body}</p>
                            <div className={styles.historyMeta}>
                                <span>{new Date(b.sent_at).toLocaleString()}</span>
                                {b.delivered_to?.length > 0 && <span>Delivered to {b.delivered_to.length} session(s)</span>}
                                {b.scheduled_round && <span>Scheduled: R{b.scheduled_round}</span>}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
