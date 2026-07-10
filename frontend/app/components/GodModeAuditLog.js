'use client';
import { useState, useEffect } from 'react';
import styles from './GodModeAuditLog.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// Action icon mapping for visual differentiation
const ACTION_ICONS = {
    facilitator_role_changed: '👑',
    facilitator_created: '➕',
    facilitator_deleted: '🗑️',
    global_settings_updated: '⚙️',
    session_created: '🚀',
    session_deleted: '💥',
    pacing_updated: '⏱️',
    override_applied: '⚡',
    broadcast_sent: '📢',
    crisis_triggered: '🚨',
    password_reset: '🔑',
    regulatory_sandbox_activated: '🧪',
    regulatory_sandbox_deactivated: '📋',
    exogenous_event_triggered: '💥',
};

// Quick filter chips
const QUICK_FILTERS = [
    { label: 'All', value: '' },
    { label: '👑 Role Changes', value: 'role_changed' },
    { label: '➕ Facilitators', value: 'facilitator' },
    { label: '⚙️ Settings', value: 'settings' },
    { label: '🚀 Sessions', value: 'session' },
    { label: '⚡ Overrides', value: 'override' },
    { label: '📢 Broadcasts', value: 'broadcast' },
    { label: '🚨 Crises', value: 'crisis' },
    { label: '🧪 Sandbox', value: 'regulatory_sandbox' },
];

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

    // Count role changes and sandbox activations for badges
    const roleChangeCount = entries.filter(e => e.action.includes('role_changed')).length;
    const sandboxCount = entries.filter(e => e.action.includes('regulatory_sandbox')).length;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📋</span>
                <div>
                    <h2>Activity Log</h2>
                    <p className={styles.subtitle}>Every God Mode configuration change, tracked and timestamped.</p>
                </div>
            </div>
            {/* Quick filter chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.75rem' }}>
                {QUICK_FILTERS.map(qf => (
                    <button
                        key={qf.value}
                        onClick={() => setFilter(qf.value)}
                        style={{
                            padding: '0.25rem 0.6rem', borderRadius: '12px', fontSize: '0.7rem',
                            fontWeight: filter === qf.value ? 700 : 500, cursor: 'pointer',
                            border: `1px solid ${filter === qf.value ? 'rgba(59,130,246,0.4)' : 'var(--border-subtle)'}`,
                            background: filter === qf.value ? 'rgba(59,130,246,0.12)' : 'transparent',
                            color: filter === qf.value ? '#60a5fa' : 'var(--text-muted)',
                            transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                        }}
                    >
                        {qf.label}
                        {qf.value === 'role_changed' && roleChangeCount > 0 && (
                            <span style={{
                                marginLeft: '4px', padding: '0 4px', borderRadius: '8px',
                                background: 'rgba(245,158,11,0.2)', color: '#f59e0b', fontSize: '0.6rem', fontWeight: 700,
                            }}>{roleChangeCount}</span>
                        )}
                        {qf.value === 'regulatory_sandbox' && sandboxCount > 0 && (
                            <span style={{
                                marginLeft: '4px', padding: '0 4px', borderRadius: '8px',
                                background: 'rgba(16,185,129,0.2)', color: '#10b981', fontSize: '0.6rem', fontWeight: 700,
                            }}>{sandboxCount}</span>
                        )}
                    </button>
                ))}
            </div>
            <div className={styles.toolbar}>
                <input className={styles.search} placeholder="Filter by action or details…" value={filter} onChange={e => setFilter(e.target.value)} />
                <span className={styles.count}>{filtered.length} entries</span>
            </div>
            {filtered.length === 0 ? (
                <div className={styles.empty}>No audit entries{filter ? ` matching "${filter}"` : ' yet'}. Changes made in God Mode will appear here.</div>
            ) : (
                <div className={styles.list}>
                    {filtered.map((e, i) => {
                        const isRoleChange = e.action.includes('role_changed');
                        const actionIcon = Object.entries(ACTION_ICONS).find(([k]) => e.action.includes(k))?.[1] || '📝';
                        return (
                            <div
                                key={e.id || i}
                                className={styles.entryRow}
                                style={isRoleChange ? {
                                    borderLeft: '3px solid #f59e0b',
                                    background: 'rgba(245,158,11,0.04)',
                                } : undefined}
                            >
                                <span className={styles.entryAction}>
                                    {actionIcon} {e.action.replace(/_/g, ' ')}
                                </span>
                                
                                <span className={styles.entryMeta}>
                                    👤 {e.actor}
                                </span>

                                <span className={styles.entryMeta}>
                                    🕐 {new Date(e.timestamp).toLocaleString()}
                                </span>

                                <div className={styles.entryDetailsContainer}>
                                    {isRoleChange && e.details ? (
                                        <div className={styles.roleChangeInline}>
                                            <span>{e.details.facilitator_id}</span>
                                            <span>→</span>
                                            <span style={{
                                                padding: '0.15rem 0.4rem', borderRadius: '4px',
                                                background: e.details.new_role === 'super_admin' ? 'rgba(245,158,11,0.15)' :
                                                            e.details.new_role === 'lead_facilitator' ? 'rgba(99,102,241,0.15)' : 'rgba(59,130,246,0.15)',
                                                color: e.details.new_role === 'super_admin' ? '#f59e0b' :
                                                       e.details.new_role === 'lead_facilitator' ? '#818cf8' : '#60a5fa',
                                            }}>
                                                {e.details.new_role === 'super_admin' ? '👑' :
                                                 e.details.new_role === 'lead_facilitator' ? '⭐' : '🎓'} {(e.details.new_role || '').replace('_', ' ')}
                                            </span>
                                        </div>
                                    ) : (
                                        Object.entries(e.details || {}).map(([k, v]) => (
                                            <span key={k} className={styles.entryDetailChip}>
                                                <strong>{k}</strong>: {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                                            </span>
                                        ))
                                    )}
                                </div>

                                <span className={styles.entryId}>{e.id}</span>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
