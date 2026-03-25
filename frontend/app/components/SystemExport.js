'use client';
import { useState } from 'react';
import styles from './SystemExport.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function SystemExport() {
    const [exportData, setExportData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState('');

    const handleExport = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/god/export`);
            if (res.ok) {
                const data = await res.json();
                setExportData(data);
                setResult(`✅ Export ready — ${data.total_sessions} sessions, ${data.facilitators.length} facilitators`);
            } else { setResult('❌ Export failed'); }
        } catch { setResult('❌ Network error'); }
        setLoading(false);
    };

    const downloadJSON = () => {
        if (!exportData) return;
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `muressons_backup_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const downloadCSV = () => {
        if (!exportData) return;
        const sessions = exportData.sessions || {};
        const rows = [['Session ID', 'Cohort Name', 'Round', 'Treasury', 'Reputation', 'Player ID']];
        for (const [sid, s] of Object.entries(sessions)) {
            rows.push([sid, s.cohort_name, s.current_round, s.treasury, s.reputation, s.player_id || 'cohort']);
        }
        const csv = rows.map(r => r.join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `muressons_sessions_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>💾</span>
                <div>
                    <h2>Backup & Export</h2>
                    <p className={styles.subtitle}>Export full system state for backup or analysis.</p>
                </div>
            </div>

            <div className={styles.card}>
                <h3>📦 Generate System Snapshot</h3>
                <p>Creates a full export of all sessions, facilitators, settings, and audit logs.</p>
                <button className={styles.exportBtn} onClick={handleExport} disabled={loading}>
                    {loading ? '⏳ Exporting…' : '📦 Generate Snapshot'}
                </button>
                {result && <div className={styles.result}>{result}</div>}
            </div>

            {exportData && (
                <>
                    <div className={styles.card}>
                        <h3>📥 Download</h3>
                        <div className={styles.downloadRow}>
                            <button className={styles.dlBtn} onClick={downloadJSON}>📄 Download JSON</button>
                            <button className={styles.dlBtn} onClick={downloadCSV}>📊 Download CSV</button>
                        </div>
                    </div>

                    <div className={styles.card}>
                        <h3>📋 Export Summary</h3>
                        <div className={styles.statsGrid}>
                            <div className={styles.stat}>
                                <div className={styles.statVal}>{exportData.total_sessions}</div>
                                <div className={styles.statLabel}>Sessions</div>
                            </div>
                            <div className={styles.stat}>
                                <div className={styles.statVal}>{exportData.facilitators.length}</div>
                                <div className={styles.statLabel}>Facilitators</div>
                            </div>
                            <div className={styles.stat}>
                                <div className={styles.statVal}>{exportData.audit_log.length}</div>
                                <div className={styles.statLabel}>Audit Entries</div>
                            </div>
                            <div className={styles.stat}>
                                <div className={styles.statVal}>{new Date(exportData.exported_at).toLocaleDateString()}</div>
                                <div className={styles.statLabel}>Export Date</div>
                            </div>
                        </div>
                    </div>

                    <details className={styles.preview}>
                        <summary>🔍 Preview Raw JSON</summary>
                        <pre className={styles.json}>{JSON.stringify(exportData, null, 2)}</pre>
                    </details>
                </>
            )}
        </div>
    );
}
