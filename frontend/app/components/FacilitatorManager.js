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

    return (
        <section className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🎓</span>
                <div>
                    <h2 className={styles.title}>Facilitator Roles</h2>
                    <p className={styles.subtitle}>
                        Create and manage facilitator accounts. Each facilitator logs in with their ID and password to access the Workshop dashboard.
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
                                <th>Created</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {facilitators.map((fac) => (
                                <tr key={fac.facilitator_id}>
                                    <td>
                                        <code className={styles.facId}>{fac.facilitator_id}</code>
                                    </td>
                                    <td className={styles.facName}>{fac.name}</td>
                                    <td>
                                        <code className={styles.password}>{fac.password}</code>
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
                            ))}
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
