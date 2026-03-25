'use client';
import { useState, useEffect } from 'react';
import styles from './GodModeAuditLog.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function GodModeAuditLog() {
    const [entries, setEntries] = useState([]);
    const [filter, setFilter] = useState('');
    const load = async () => {
        try {
            const res = await fetch(`${API}/api/admin/god/audit-log`);
            if (res.ok) { const d = await res.json(); setEntries(d.entries || []); }
        } catch {}
    };
    useEffect(() => { load(); const i = setInterval(load, 8000); return () => clearInterval(i); }, []);

    const filtered = filter ? entries.filter(e => e.action.includes(filter) || JSON.stringify(e.details).includes(filter)) : entries;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📋</span>
                <div>
                    <h2>Activity Log</h2>
                    <p className={styles.subtitle}>Every God Mode configuration change, tracked and timestamped.</p>
                </div>
            </div>
            <div className={styles.toolbar}>
                <input className={styles.search} placeholder="Filter by action or details…" value={filter} onChange={e => setFilter(e.target.value)} />
                <span className={styles.count}>{filtered.length} entries</span>
            </div>
            {filtered.length === 0 ? (
                <div className={styles.empty}>No audit entries yet. Changes made in God Mode will appear here.</div>
            ) : (
                <div className={styles.list}>
                    {filtered.map((e, i) => (
                        <div key={e.id || i} className={styles.entry}>
                            <div className={styles.entryHeader}>
                                <span className={styles.entryAction}>{e.action.replace(/_/g, ' ')}</span>
                                <span className={styles.entryId}>{e.id}</span>
                            </div>
                            <div className={styles.entryMeta}>
                                <span>👤 {e.actor}</span>
                                <span>🕐 {new Date(e.timestamp).toLocaleString()}</span>
                            </div>
                            {Object.keys(e.details || {}).length > 0 && (
                                <pre className={styles.details}>{JSON.stringify(e.details, null, 2)}</pre>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
