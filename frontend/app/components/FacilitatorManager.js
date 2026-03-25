'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './FacilitatorManager.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function FacilitatorManager() {
    const [facilitators, setFacilitators] = useState([]);
    const [name, setName] = useState('');
    const [loading, setLoading] = useState(false);
    const [toast, setToast] = useState(null);

    const fetchFacilitators = useCallback(async () => {
        try {
            const res = await fetch(`${API}/api/admin/facilitators`);
            if (res.ok) {
                const data = await res.json();
                setFacilitators(data.facilitators || []);
            }
        } catch {
            /* backend offline */
        }
    }, []);

    useEffect(() => {
        fetchFacilitators();
        // Auto-refresh every 10s to catch real-time cohort creation updates
        const interval = setInterval(fetchFacilitators, 10000);
        return () => clearInterval(interval);
    }, [fetchFacilitators]);

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!name.trim()) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/facilitators`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.trim() }),
            });
            if (res.ok) {
                const fac = await res.json();
                setFacilitators(prev => [...prev, fac]);
                setName('');
                showToast(`Created ${fac.facilitator_id}`);
            } else {
                const err = await res.json();
                showToast(err.detail || 'Failed', 'error');
            }
        } catch {
            showToast('Network error', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (facId) => {
        if (!confirm(`Delete facilitator ${facId}? This cannot be undone.`)) return;
        try {
            const res = await fetch(`${API}/api/admin/facilitators/${facId}`, {
                method: 'DELETE',
            });
            if (res.ok) {
                setFacilitators(prev => prev.filter(f => f.facilitator_id !== facId));
                showToast(`Deleted ${facId}`);
            }
        } catch {
            showToast('Delete failed', 'error');
        }
    };

    const handleLimitChange = async (facId, newLimit) => {
        const limit = parseInt(newLimit, 10);
        if (isNaN(limit) || limit < 0) return;
        try {
            const res = await fetch(`${API}/api/admin/facilitators/${facId}/cohort-limit`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ max_cohorts: limit }),
            });
            if (res.ok) {
                const updated = await res.json();
                setFacilitators(prev =>
                    prev.map(f => f.facilitator_id === facId ? { ...f, max_cohorts: updated.max_cohorts } : f)
                );
                showToast(`Cohort limit updated to ${limit}`);
            } else {
                showToast('Failed to update limit', 'error');
            }
        } catch {
            showToast('Network error', 'error');
        }
    };

    const getUsagePct = (created, max) => {
        if (!max || max <= 0) return 100;
        return Math.min(100, Math.round((created / max) * 100));
    };

    const getUsageColor = (pct) => {
        if (pct >= 90) return '#ef4444';
        if (pct >= 60) return '#f59e0b';
        return '#22c55e';
    };

    return (
        <section className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🎓</span>
                <div>
                    <h2 className={styles.title}>Facilitator Roles</h2>
                    <p className={styles.subtitle}>
                        Create and manage facilitator accounts. Each facilitator can create cohorts up to their assigned limit.
                    </p>
                </div>
            </div>

            {/* ── Create Form ── */}
            <form className={styles.createForm} onSubmit={handleCreate}>
                <input
                    className={styles.nameInput}
                    type="text"
                    placeholder="Facilitator name (e.g. Prof. Smith)"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={loading}
                />
                <button
                    className={styles.createBtn}
                    type="submit"
                    disabled={loading || !name.trim()}
                >
                    {loading ? '⏳' : '➕'} Create Facilitator
                </button>
            </form>

            {/* ── Facilitator Table ── */}
            {facilitators.length === 0 ? (
                <div className={styles.empty}>
                    No facilitators created yet. Use the form above to add one.
                </div>
            ) : (
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th>Facilitator ID</th>
                                <th>Name</th>
                                <th>Password</th>
                                <th>Cohort Limit</th>
                                <th>Cohorts Created</th>
                                <th>Created</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {facilitators.map((fac) => {
                                const created = fac.cohorts_created || 0;
                                const max = fac.max_cohorts ?? 5;
                                const pct = getUsagePct(created, max);
                                const barColor = getUsageColor(pct);
                                return (
                                    <tr key={fac.facilitator_id}>
                                        <td>
                                            <code className={styles.facId}>{fac.facilitator_id}</code>
                                        </td>
                                        <td className={styles.facName}>{fac.name}</td>
                                        <td>
                                            <code className={styles.password}>{fac.password}</code>
                                        </td>
                                        <td>
                                            <input
                                                className={styles.limitInput}
                                                type="number"
                                                min="0"
                                                max="100"
                                                value={max}
                                                onChange={(e) =>
                                                    handleLimitChange(fac.facilitator_id, e.target.value)
                                                }
                                                title="Maximum cohorts this facilitator can create"
                                            />
                                        </td>
                                        <td>
                                            <div className={styles.usageWrap}>
                                                <span className={styles.usageText} style={{ color: barColor }}>
                                                    {created}/{max}
                                                </span>
                                                <div className={styles.usageBar}>
                                                    <div
                                                        className={styles.usageFill}
                                                        style={{ width: `${pct}%`, background: barColor }}
                                                    />
                                                </div>
                                            </div>
                                        </td>
                                        <td className={styles.date}>
                                            {new Date(fac.created_at).toLocaleDateString()}
                                        </td>
                                        <td>
                                            <button
                                                className={styles.deleteBtn}
                                                onClick={() => handleDelete(fac.facilitator_id)}
                                                title="Delete facilitator"
                                            >
                                                🗑️
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}

            {/* ── Toast ── */}
            {toast && (
                <div className={`${styles.toast} ${toast.type === 'error' ? styles.toastError : ''}`}>
                    {toast.msg}
                </div>
            )}
        </section>
    );
}
