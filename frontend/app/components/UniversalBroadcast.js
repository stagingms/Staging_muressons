'use client';
import { useState } from 'react';
import styles from './UniversalBroadcast.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function UniversalBroadcast() {
    const [title, setTitle] = useState('');
    const [message, setMessage] = useState('');
    const [priority, setPriority] = useState('info');
    const [sending, setSending] = useState(false);
    const [history, setHistory] = useState([]);
    const [result, setResult] = useState('');

    const [target, setTarget] = useState('all'); // 'all', 'students', 'facilitators'

    const handleSend = async () => {
        if (!title.trim() || !message.trim()) return;
        setSending(true);
        try {
            const res = await fetch(`${API}/api/admin/god/universal-broadcast`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, message, priority, target }),
            });
            if (res.ok) {
                const data = await res.json();
                setHistory(prev => [data.payload, ...prev]);
                setResult('✅ Broadcast sent to all connected clients');
                setTitle(''); setMessage('');
            } else { setResult('❌ Broadcast failed'); }
        } catch { setResult('❌ Network error'); }
        setSending(false);
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📢</span>
                <div>
                    <h2>Universal Broadcast</h2>
                    <p className={styles.subtitle}>Send announcements to ALL connected facilitators and students.</p>
                </div>
            </div>

            <div className={styles.form}>
                <input className={styles.input} placeholder="Announcement title" value={title} onChange={e => setTitle(e.target.value)} />
                <textarea className={styles.textarea} placeholder="Message body…" rows={4} value={message} onChange={e => setMessage(e.target.value)} />

                <div className={styles.priorityRow} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className={styles.priorityLabel}>Target:</span>
                        <select 
                            className={styles.input} 
                            style={{ padding: '0.4rem', width: 'auto' }}
                            value={target} 
                            onChange={e => setTarget(e.target.value)}
                        >
                            <option value="all">All Clients</option>
                            <option value="students">Students Only</option>
                            <option value="facilitators">Facilitators Only</option>
                        </select>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'auto' }}>
                        <span className={styles.priorityLabel}>Priority:</span>
                    {['info', 'warning', 'critical'].map(p => (
                        <button key={p} className={`${styles.priorityBtn} ${priority === p ? styles[`priority_${p}`] : ''}`} onClick={() => setPriority(p)}>
                            {p === 'info' ? 'ℹ️' : p === 'warning' ? '⚠️' : '🚨'} {p}
                        </button>
                    ))}
                    </div>
                </div>

                <button className={styles.sendBtn} disabled={sending || !title.trim() || !message.trim()} onClick={handleSend}>
                    {sending ? '⏳ Sending…' : '📢 Broadcast Now'}
                </button>

                {result && <div className={styles.result}>{result}</div>}
            </div>

            {history.length > 0 && (
                <div className={styles.history}>
                    <h3>Broadcast History</h3>
                    {history.map((h, i) => (
                        <div key={i} className={`${styles.historyItem} ${styles[`hist_${h.priority}`]}`}>
                            <div className={styles.histTitle}>{h.title}</div>
                            <div className={styles.histMsg}>{h.message}</div>
                            <div className={styles.histMeta}>
                                <span className={styles.histPriority}>{h.priority}</span>
                                <span>{new Date(h.timestamp).toLocaleString()}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
