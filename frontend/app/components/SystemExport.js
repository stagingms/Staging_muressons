'use client';
import { useState, useRef } from 'react';
import styles from './SystemExport.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function SystemExport() {
    const [exportData, setExportData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState('');
    const [importStatus, setImportStatus] = useState('');
    const [gdprLoading, setGdprLoading] = useState(false);
    const [gdprPlayerId, setGdprPlayerId] = useState('');
    const [backupHistory, setBackupHistory] = useState(() => {
        if (typeof window !== 'undefined') {
            try { return JSON.parse(localStorage.getItem('muressons_backup_history') || '[]'); } catch { return []; }
        }
        return [];
    });
    const fileInputRef = useRef(null);

    const handleExport = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/god/export`);
            if (res.ok) {
                const data = await res.json();
                setExportData(data);
                setResult(`✅ Export ready — ${data.total_sessions} sessions, ${data.facilitators.length} facilitators`);
                // Track backup in history
                const entry = {
                    date: new Date().toISOString(),
                    sessions: data.total_sessions,
                    facilitators: data.facilitators.length,
                    auditEntries: data.audit_log.length,
                };
                const newHistory = [entry, ...backupHistory].slice(0, 10);
                setBackupHistory(newHistory);
                localStorage.setItem('muressons_backup_history', JSON.stringify(newHistory));
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

    // ── Import / Restore ──
    const handleImport = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setImportStatus('⏳ Validating backup file…');
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            // Basic structure validation
            if (!data.exported_at || !data.sessions || !data.facilitators) {
                setImportStatus('❌ Invalid backup file: missing required fields (exported_at, sessions, facilitators)');
                return;
            }
            const sessionCount = Object.keys(data.sessions).length;
            const facCount = data.facilitators?.length || 0;
            if (!confirm(`⚠️ Import backup from ${new Date(data.exported_at).toLocaleDateString()}?\n\nThis contains ${sessionCount} sessions and ${facCount} facilitators.\n\nNote: This will NOT overwrite existing data — it will be merged. Duplicate session IDs will be skipped.`)) {
                setImportStatus('Import cancelled');
                return;
            }
            const res = await fetch(`${API}/api/admin/god/import`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: text,
            });
            if (res.ok) {
                const result = await res.json();
                setImportStatus(`✅ Imported: ${result.sessions_imported || 0} sessions, ${result.facilitators_imported || 0} facilitators`);
            } else {
                const err = await res.json().catch(() => ({}));
                setImportStatus(`❌ Import failed: ${err.detail || res.status}`);
            }
        } catch (err) {
            setImportStatus(`❌ File parse error: ${err.message}`);
        }
        e.target.value = '';
    };

    // ── GDPR Data Export ──
    const handleGdprExport = async () => {
        if (!gdprPlayerId.trim()) return;
        setGdprLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/god/gdpr-export/${encodeURIComponent(gdprPlayerId.trim())}`);
            if (res.ok) {
                const data = await res.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `gdpr_export_${gdprPlayerId.trim()}_${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                URL.revokeObjectURL(url);
                setResult(`✅ GDPR export downloaded for player ${gdprPlayerId.trim()}`);
            } else {
                setResult(`❌ GDPR export failed: player not found`);
            }
        } catch { setResult('❌ Network error during GDPR export'); }
        setGdprLoading(false);
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>💾</span>
                <div>
                    <h2>Backup & Export</h2>
                    <p className={styles.subtitle}>Full system backup, restore from snapshots, GDPR compliance exports.</p>
                </div>
            </div>

            {/* ── Generate Snapshot ── */}
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
                            <button className={styles.dlBtn} onClick={downloadJSON}>📄 Full JSON Backup</button>
                            <button className={styles.dlBtn} onClick={downloadCSV}>📊 Sessions CSV</button>
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

            {/* ── Import / Restore ── */}
            <div className={styles.card} style={{ borderLeft: '3px solid #f59e0b' }}>
                <h3>📤 Import / Restore from Backup</h3>
                <p>Upload a previously exported JSON backup to restore sessions and facilitator data. Existing data will be merged — duplicates are skipped.</p>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".json"
                        onChange={handleImport}
                        style={{ display: 'none' }}
                    />
                    <button
                        className={styles.dlBtn}
                        onClick={() => fileInputRef.current?.click()}
                        style={{ borderColor: 'rgba(245,158,11,0.3)', color: '#f59e0b' }}
                    >
                        📂 Select Backup File
                    </button>
                    {importStatus && (
                        <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>{importStatus}</span>
                    )}
                </div>
            </div>

            {/* ── GDPR Data Export ── */}
            <div className={styles.card} style={{ borderLeft: '3px solid #06b6d4' }}>
                <h3>🔒 GDPR Compliance Export</h3>
                <p>Export all personal data held for a specific player (Right of Access — Article 15 GDPR). Downloads a JSON file containing the player's decisions, KPIs, session history, and any stored personal information.</p>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <input
                        type="text"
                        placeholder="Player ID (e.g. alice-alpha-01)"
                        value={gdprPlayerId}
                        onChange={e => setGdprPlayerId(e.target.value)}
                        style={{
                            padding: '0.5rem 0.8rem', borderRadius: '6px', fontSize: '0.82rem',
                            border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
                            color: 'var(--text-primary)', width: '260px', fontFamily: 'var(--font-mono)',
                        }}
                    />
                    <button
                        className={styles.dlBtn}
                        onClick={handleGdprExport}
                        disabled={gdprLoading || !gdprPlayerId.trim()}
                        style={{ borderColor: 'rgba(6,182,212,0.3)', color: '#06b6d4' }}
                    >
                        {gdprLoading ? '⏳' : '🔒'} Export Player Data
                    </button>
                </div>
            </div>

            {/* ── Backup History ── */}
            {backupHistory.length > 0 && (
                <div className={styles.card}>
                    <h3>🕐 Backup History</h3>
                    <p>Recent snapshots generated from this browser (stored locally).</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                        {backupHistory.map((entry, i) => (
                            <div key={i} style={{
                                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                padding: '0.5rem 0.75rem', borderRadius: '6px',
                                background: i === 0 ? 'rgba(99,102,241,0.04)' : 'transparent',
                                border: i === 0 ? '1px solid rgba(99,102,241,0.15)' : '1px solid transparent',
                                fontSize: '0.78rem',
                            }}>
                                <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                                    {new Date(entry.date).toLocaleString()}
                                </span>
                                <span style={{ color: 'var(--text-muted)' }}>
                                    {entry.sessions} sessions · {entry.facilitators} facilitators · {entry.auditEntries} audit entries
                                </span>
                                {i === 0 && <span style={{ fontSize: '0.68rem', color: '#6366f1', fontWeight: 700 }}>LATEST</span>}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
