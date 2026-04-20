'use client';

import { useState, useEffect, useCallback, useRef, Fragment } from 'react';
import styles from './FacilitatorManager.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// ─── Relative timestamp ────────────────────────────────────────────────────
function relativeDate(dateStr) {
    if (!dateStr) return '—';
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return new Date(dateStr).toLocaleDateString();
}

function formatDateInput(dateStr) {
    if (!dateStr) return '';
    try { return new Date(dateStr).toISOString().split('T')[0]; } catch { return ''; }
}

// ─── Paradigm label map ────────────────────────────────────────────────────
const PARADIGM_LABELS = {
    legacy_abc: { label: 'Narrative Crises', color: '#6366f1', bg: 'rgba(99,102,241,0.1)' },
    multi_toggles: { label: 'Strategic Pillars', color: '#06b6d4', bg: 'rgba(6,182,212,0.1)' },
    advanced_climate: { label: 'Advanced Climate', color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
    healthcare: { label: 'Healthcare Ed.', color: '#f43f5e', bg: 'rgba(244,63,94,0.1)' },
    un_sdg: { label: 'UN SDG', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
};

const PARADIGM_OPTIONS = [
    { id: 'legacy_abc', label: 'Narrative Crises', sub: 'Classic A/B/C options format — decision-node driven', icon: '≡' },
    { id: 'multi_toggles', label: 'Strategic Pillars', sub: 'Toggle-based multi-vector decisions', icon: '⊞' },
    { id: 'advanced_climate', label: 'Advanced Climate', sub: 'Full climate engine with carbon markets', icon: '🌍' },
    { id: 'healthcare', label: 'Healthcare Edition', sub: 'Clinical operations & patient outcomes', icon: '🏥' },
    { id: 'un_sdg', label: 'UN SDG Goals', sub: 'Sustainable Development Goals framework', icon: '🎯' },
];

const EMPTY_FORM = {
    name: '',
    email: '',
    phone: '',
    programme: '',
    cohorts: 5,
    paradigm: 'legacy_abc',
    startDate: '',
    endDate: '',
    notes: '',
    permissions: {
        can_undo_rounds: true,
        can_override_decisions: true,
        can_modify_materiality: true,
        can_manage_auto_pause: true,
    },
};

// ─── CSV/Excel Parser helpers ──────────────────────────────────────────────
function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
        const c = line[i];
        if (c === '"') { inQuotes = !inQuotes; continue; }
        if (c === ',' && !inQuotes) { result.push(current.trim()); current = ''; continue; }
        current += c;
    }
    result.push(current.trim());
    return result;
}

function parseCSV(text) {
    const lines = text.split(/\r?\n/).filter(l => l.trim());
    if (lines.length < 2) return [];
    const headers = parseCSVLine(lines[0]).map(h => h.toLowerCase().replace(/[\s_]+/g, '_'));
    return lines.slice(1).map(line => {
        const cols = parseCSVLine(line);
        const row = {};
        headers.forEach((h, i) => { row[h] = cols[i] || ''; });
        return row;
    });
}

function mapCSVRowToFacilitator(row) {
    return {
        name: row.name || row.facilitator_name || row.full_name || '',
        email: row.email || row.email_id || row.email_address || '',
        contact_number: row.phone || row.phone_number || row.contact || row.contact_number || row.mobile || '',
        programme: row.programme || row.program || row.course || '',
        max_cohorts: parseInt(row.cohorts || row.max_cohorts || '5', 10) || 5,
        decision_paradigm: row.paradigm || row.decision_paradigm || 'legacy_abc',
        start_date: row.start_date || row.start || '',
        end_date: row.end_date || row.end || '',
    };
}


export default function FacilitatorManager({ onNavigate }) {
    const [facilitators, setFacilitators] = useState([]);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState(null);

    // Drawer state
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [drawerMode, setDrawerMode] = useState('create'); // 'create' | 'bulk' | 'edit'
    const [step, setStep] = useState(1);
    const [form, setForm] = useState({ ...EMPTY_FORM });
    const [creating, setCreating] = useState(false);
    const [editingFacId, setEditingFacId] = useState(null);

    // Bulk upload
    const [bulkData, setBulkData] = useState([]);
    const [bulkErrors, setBulkErrors] = useState([]);
    const [bulkUploading, setBulkUploading] = useState(false);
    const [isDragOver, setIsDragOver] = useState(false);
    const fileInputRef = useRef(null);

    // Table state
    const [search, setSearch] = useState('');
    const [sortKey, setSortKey] = useState('created_at');
    const [sortDir, setSortDir] = useState('desc');
    const [confirmDeleteId, setConfirmDeleteId] = useState(null);
    const deleteTimerRef = useRef(null);



    // ────────────────────────────────────────────────────────
    const fetchFacilitators = useCallback(async () => {
        try {
            const res = await fetch(`${API}/api/admin/facilitators`);
            if (res.ok) {
                const data = await res.json();
                setFacilitators(data.facilitators || []);
            }
        } catch { /* backend offline */ }
        setLoading(false);
    }, []);

    useEffect(() => {
        fetchFacilitators();
        const interval = setInterval(fetchFacilitators, 10000);
        return () => clearInterval(interval);
    }, [fetchFacilitators]);

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 4000);
    };

    // ── Per-facilitator enabled toggle ───────────────────────
    const toggleFacilitatorEnabled = async (facId, currentEnabled) => {
        const newVal = !currentEnabled;
        setFacilitators(prev => prev.map(f => f.facilitator_id === facId ? { ...f, enabled: newVal } : f));
        try {
            const res = await fetch(`${API}/api/admin/facilitators/${facId}/enabled`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: newVal }),
            });
            if (res.ok) {
                showToast(`${facId} cohort creation ${newVal ? 'enabled' : 'disabled'}`);
            } else {
                setFacilitators(prev => prev.map(f => f.facilitator_id === facId ? { ...f, enabled: currentEnabled } : f));
                showToast('Failed to toggle', 'error');
            }
        } catch {
            setFacilitators(prev => prev.map(f => f.facilitator_id === facId ? { ...f, enabled: currentEnabled } : f));
            showToast('Network error', 'error');
        }
    };

    // ── Drawer ──────────────────────────────────────────────
    const openDrawer = (mode = 'create') => {
        setStep(1);
        setForm({ ...EMPTY_FORM });
        setDrawerMode(mode);
        setBulkData([]);
        setBulkErrors([]);
        setEditingFacId(null);
        setDrawerOpen(true);
    };

    const openEditDrawer = (fac) => {
        setStep(1);
        setForm({
            name: fac.name || '',
            email: fac.email || '',
            phone: fac.contact_number || '',
            programme: fac.programme || '',
            cohorts: fac.max_cohorts ?? 5,
            paradigm: fac.decision_paradigm || 'legacy_abc',
            startDate: formatDateInput(fac.start_date),
            endDate: formatDateInput(fac.end_date),
            notes: fac.notes || '',
            permissions: fac.permissions || { ...EMPTY_FORM.permissions },
        });
        setDrawerMode('edit');
        setEditingFacId(fac.facilitator_id);
        setDrawerOpen(true);
    };

    const closeDrawer = () => { setDrawerOpen(false); setStep(1); setForm({ ...EMPTY_FORM }); setEditingFacId(null); };

    const updateForm = (field, value) => setForm(prev => ({ ...prev, [field]: value }));
    const updatePermission = (key, value) => setForm(prev => ({
        ...prev,
        permissions: { ...prev.permissions, [key]: value },
    }));

    // ── Validation per step ─────────────────────────────────
    const canAdvanceStep = (s) => {
        if (s === 1) return form.name.trim().length > 0;
        if (s === 2) return true; // programme is optional
        if (s === 3) return true; // paradigm always has a default
        return true;
    };

    // ── Create / Update facilitator ─────────────────────────
    const handleSubmit = async () => {
        setCreating(true);
        try {
            const payload = {
                name: form.name.trim(),
                email: form.email.trim() || null,
                contact_number: form.phone.trim() || null,
                programme: form.programme.trim() || null,
                start_date: form.startDate || null,
                end_date: form.endDate || null,
                max_cohorts: form.cohorts,
                decision_paradigm: form.paradigm,
                permissions: form.permissions,
            };

            if (drawerMode === 'edit' && editingFacId) {
                // Update existing
                const res = await fetch(`${API}/api/admin/facilitators/${editingFacId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (res.ok) {
                    const updated = await res.json();
                    setFacilitators(prev => prev.map(f => f.facilitator_id === editingFacId ? { ...f, ...updated } : f));
                    showToast(`✅ ${editingFacId} updated`);
                    closeDrawer();
                } else {
                    const err = await res.json().catch(() => ({}));
                    showToast(err.detail || 'Failed to update', 'error');
                }
            } else {
                // Create new
                const res = await fetch(`${API}/api/admin/facilitators`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    showToast(err.detail || 'Failed to create facilitator', 'error');
                    return;
                }
                const fac = await res.json();

                // Seed first cohort
                const cohortName = `${form.name.trim()}'s Alpha Cohort`;
                const seedRes = await fetch(`${API}/api/simulations/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        cohort_name: cohortName,
                        decision_paradigm: form.paradigm,
                        facilitator_id: fac.facilitator_id,
                    }),
                });

                if (seedRes.ok) {
                    setFacilitators(prev => [...prev, { ...fac, cohorts_created: 1 }]);
                    showToast(`✅ ${fac.facilitator_id} created & seeded`);
                    closeDrawer();
                } else {
                    setFacilitators(prev => [...prev, fac]);
                    showToast('Facilitator created but seed cohort failed', 'error');
                    closeDrawer();
                }
            }
        } catch {
            showToast('Network error during submission', 'error');
        } finally {
            setCreating(false);
        }
    };

    // ── Bulk CSV Upload ─────────────────────────────────────
    const handleFileSelect = (file) => {
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const text = e.target.result;
                const rows = parseCSV(text);
                if (rows.length === 0) {
                    setBulkErrors(['No data rows found in file']);
                    return;
                }
                const mapped = rows.map(mapCSVRowToFacilitator);
                const errors = [];
                mapped.forEach((m, i) => {
                    if (!m.name) errors.push(`Row ${i + 2}: Name is missing`);
                });
                setBulkData(mapped);
                setBulkErrors(errors);
            } catch (err) {
                setBulkErrors([`Failed to parse file: ${err.message}`]);
            }
        };
        reader.readAsText(file);
    };

    const handleDrop = (e) => {
        e.preventDefault(); setIsDragOver(false);
        const file = e.dataTransfer?.files?.[0];
        if (file) handleFileSelect(file);
    };

    const handleBulkSubmit = async () => {
        if (bulkErrors.length > 0 || bulkData.length === 0) return;
        setBulkUploading(true);
        try {
            const res = await fetch(`${API}/api/admin/facilitators/bulk`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ facilitators: bulkData }),
            });
            if (res.ok) {
                const data = await res.json();
                showToast(`✅ ${data.created} facilitator(s) created`);
                await fetchFacilitators();
                closeDrawer();
            } else {
                const err = await res.json().catch(() => ({}));
                showToast(err.detail || 'Bulk creation failed', 'error');
            }
        } catch {
            showToast('Network error during bulk upload', 'error');
        } finally {
            setBulkUploading(false);
        }
    };

    // ── Delete (inline double-click confirm) ────────────────
    const handleDeleteClick = (facId) => {
        if (confirmDeleteId === facId) {
            clearTimeout(deleteTimerRef.current);
            setConfirmDeleteId(null);
            handleDelete(facId);
        } else {
            clearTimeout(deleteTimerRef.current);
            setConfirmDeleteId(facId);
            deleteTimerRef.current = setTimeout(() => setConfirmDeleteId(null), 3000);
        }
    };

    const handleDelete = async (facId) => {
        try {
            const res = await fetch(`${API}/api/admin/facilitators/${facId}`, { method: 'DELETE' });
            if (res.ok) {
                setFacilitators(prev => prev.filter(f => f.facilitator_id !== facId));
                showToast(`Deleted ${facId}`);
            } else {
                showToast('Delete failed', 'error');
            }
        } catch {
            showToast('Delete failed: network error', 'error');
        }
    };



    // ── Reset Password ───────────────────────────────────────
    const handleResetPassword = async (facId) => {
        try {
            const res = await fetch(`${API}/api/admin/facilitators/${facId}/reset-password`, { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                showToast(`New password: ${data.new_password || data.password || '(check server)'}`, 'success');
            } else {
                showToast('Reset failed', 'error');
            }
        } catch {
            showToast('Reset failed: network error', 'error');
        }
    };

    // ── Sort ─────────────────────────────────────────────────
    const toggleSort = (key) => {
        if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('asc'); }
    };

    const SortIcon = ({ col }) => {
        if (sortKey !== col) return <span style={{ opacity: 0.3, fontSize: '0.6rem' }}>⇅</span>;
        return <span style={{ fontSize: '0.6rem', color: '#06b6d4' }}>{sortDir === 'asc' ? '↑' : '↓'}</span>;
    };

    // ── Derived data ─────────────────────────────────────────
    const totalCohortsUsed = facilitators.reduce((s, f) => s + (f.cohorts_created || 0), 0);
    const totalCapacity = facilitators.reduce((s, f) => s + (f.max_cohorts ?? 5), 0);
    const atCapacity = facilitators.filter(f => (f.cohorts_created || 0) >= (f.max_cohorts ?? 5)).length;

    const filtered = facilitators
        .filter(f => !search.trim() ||
            f.name?.toLowerCase().includes(search.toLowerCase()) ||
            f.facilitator_id?.toLowerCase().includes(search.toLowerCase()) ||
            f.email?.toLowerCase().includes(search.toLowerCase()) ||
            f.programme?.toLowerCase().includes(search.toLowerCase())
        )
        .sort((a, b) => {
            let va = a[sortKey] ?? '';
            let vb = b[sortKey] ?? '';
            if (typeof va === 'string') va = va.toLowerCase();
            if (typeof vb === 'string') vb = vb.toLowerCase();
            if (typeof va === 'number' && typeof vb === 'number') {
                return sortDir === 'asc' ? va - vb : vb - va;
            }
            if (va < vb) return sortDir === 'asc' ? -1 : 1;
            if (va > vb) return sortDir === 'asc' ? 1 : -1;
            return 0;
        });

    const getUsagePct = (created, max) => !max || max <= 0 ? 100 : Math.min(100, Math.round((created / max) * 100));
    const getUsageColor = (pct) => pct >= 90 ? '#ef4444' : pct >= 60 ? '#f59e0b' : '#22c55e';

    const TOTAL_STEPS = 4;

    // ── Step content titles ─────────────────────────────────
    const stepTitles = ['Identity', 'Programme', 'Configuration', 'Review & Confirm'];

    // ────────────────────────────────────────────────────────
    // ── RENDER ──────────────────────────────────────────────
    // ────────────────────────────────────────────────────────

    const renderStepContent = () => {
        if (drawerMode === 'bulk') return renderBulkUpload();
        if (drawerMode === 'edit') return renderEditForm();

        switch (step) {
            case 1: return renderStep1();
            case 2: return renderStep2();
            case 3: return renderStep3();
            case 4: return renderStep4();
            default: return null;
        }
    };

    // ── Step 1: Identity ────────────────────────────────────
    const renderStep1 = () => (
        <div className={styles.stepContent}>
            <div className={styles.stepHeader}>
                <span className={styles.stepIcon}>👤</span>
                <div>
                    <h4 className={styles.stepTitle}>Facilitator Identity</h4>
                    <p className={styles.stepDesc}>Enter the facilitator's personal details. A unique ID (FAC-XXX) and default password will be auto-generated.</p>
                </div>
            </div>

            <div className={styles.formGrid}>
                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Full Name <span className={styles.required}>*</span></label>
                    <input
                        id="fac-name-input"
                        className={styles.formInput}
                        type="text"
                        placeholder="e.g. Prof. Avery Smith"
                        value={form.name}
                        onChange={e => updateForm('name', e.target.value)}
                        autoFocus
                    />
                </div>

                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Email Address</label>
                    <input
                        id="fac-email-input"
                        className={styles.formInput}
                        type="email"
                        placeholder="facilitator@university.edu"
                        value={form.email}
                        onChange={e => updateForm('email', e.target.value)}
                    />
                </div>

                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Phone Number</label>
                    <input
                        id="fac-phone-input"
                        className={styles.formInput}
                        type="tel"
                        placeholder="+44 7700 900000"
                        value={form.phone}
                        onChange={e => updateForm('phone', e.target.value)}
                    />
                </div>
            </div>

            <div className={styles.stepNavigation}>
                <div />
                <button
                    className={styles.navBtnPrimary}
                    disabled={!canAdvanceStep(1)}
                    onClick={() => setStep(2)}
                >
                    Continue → Programme
                </button>
            </div>
        </div>
    );

    // ── Step 2: Programme & Schedule ────────────────────────
    const renderStep2 = () => (
        <div className={styles.stepContent}>
            <div className={styles.stepHeader}>
                <span className={styles.stepIcon}>🎓</span>
                <div>
                    <h4 className={styles.stepTitle}>Programme & Schedule</h4>
                    <p className={styles.stepDesc}>Associate this facilitator with a programme and define the simulation window.</p>
                </div>
            </div>

            <div className={styles.formGrid}>
                <div className={styles.formGroupFull}>
                    <label className={styles.formLabel}>Programme / Course</label>
                    <input
                        id="fac-programme-input"
                        className={styles.formInput}
                        type="text"
                        placeholder="e.g. MBA Sustainability, Executive Development Cohort 2026"
                        value={form.programme}
                        onChange={e => updateForm('programme', e.target.value)}
                    />
                </div>

                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Max Cohorts</label>
                    <input
                        id="fac-cohorts-input"
                        className={styles.formInput}
                        type="number"
                        min="1"
                        max="50"
                        value={form.cohorts}
                        onChange={e => updateForm('cohorts', parseInt(e.target.value, 10) || 1)}
                    />
                    <span className={styles.formHint}>How many cohorts this facilitator can create</span>
                </div>

                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Start Date</label>
                    <input
                        id="fac-start-date"
                        className={styles.formInput}
                        type="date"
                        value={form.startDate}
                        onChange={e => updateForm('startDate', e.target.value)}
                    />
                </div>

                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>End Date</label>
                    <input
                        id="fac-end-date"
                        className={styles.formInput}
                        type="date"
                        value={form.endDate}
                        onChange={e => updateForm('endDate', e.target.value)}
                    />
                </div>

                <div className={styles.formGroupFull}>
                    <label className={styles.formLabel}>Notes / Instructions</label>
                    <textarea
                        id="fac-notes-input"
                        className={styles.formTextarea}
                        placeholder="Internal notes: exam timing, special configurations, cohort size expectations…"
                        rows={3}
                        value={form.notes}
                        onChange={e => updateForm('notes', e.target.value)}
                    />
                </div>
            </div>

            <div className={styles.stepNavigation}>
                <button className={styles.navBtnSecondary} onClick={() => setStep(1)}>← Identity</button>
                <button className={styles.navBtnPrimary} onClick={() => setStep(3)}>Continue → Configuration</button>
            </div>
        </div>
    );

    // ── Step 3: Paradigm & Permissions ──────────────────────
    const renderStep3 = () => (
        <div className={styles.stepContent}>
            <div className={styles.stepHeader}>
                <span className={styles.stepIcon}>⚙️</span>
                <div>
                    <h4 className={styles.stepTitle}>Simulation Configuration</h4>
                    <p className={styles.stepDesc}>Choose the decision paradigm and configure permissions for this facilitator.</p>
                </div>
            </div>

            <label className={styles.formLabel} style={{ marginBottom: '0.5rem' }}>Decision Paradigm</label>
            <div className={styles.paradigmGrid}>
                {PARADIGM_OPTIONS.map(opt => (
                    <div
                        key={opt.id}
                        onClick={() => updateForm('paradigm', opt.id)}
                        className={`${styles.paradigmCard} ${form.paradigm === opt.id ? styles.paradigmCardActive : ''}`}
                    >
                        <span className={styles.paradigmIcon}>{opt.icon}</span>
                        <div style={{ flex: 1 }}>
                            <div className={styles.paradigmLabel}>{opt.label}</div>
                            <div className={styles.paradigmSub}>{opt.sub}</div>
                        </div>
                        {form.paradigm === opt.id && (
                            <span className={styles.paradigmCheck}>✓</span>
                        )}
                    </div>
                ))}
            </div>

            <div className={styles.permissionsSection}>
                <label className={styles.formLabel} style={{ marginBottom: '0.6rem' }}>Admin Permissions</label>
                <div className={styles.permGrid}>
                    {[
                        { key: 'can_undo_rounds', label: 'Undo Rounds', icon: '↩️' },
                        { key: 'can_override_decisions', label: 'Override Decisions', icon: '🔧' },
                        { key: 'can_modify_materiality', label: 'Modify Materiality', icon: '📊' },
                        { key: 'can_manage_auto_pause', label: 'Manage Auto-Pause', icon: '⏸️' },
                    ].map(perm => (
                        <div
                            key={perm.key}
                            className={`${styles.permCard} ${form.permissions[perm.key] ? styles.permCardActive : ''}`}
                            onClick={() => updatePermission(perm.key, !form.permissions[perm.key])}
                        >
                            <span className={styles.permIcon}>{perm.icon}</span>
                            <span className={styles.permLabel}>{perm.label}</span>
                            <div className={styles.permToggle}>
                                <div
                                    className={styles.permToggleTrack}
                                    style={{ background: form.permissions[perm.key] ? '#10b981' : '#475569' }}
                                >
                                    <div
                                        className={styles.permToggleThumb}
                                        style={{ left: form.permissions[perm.key] ? '14px' : '2px' }}
                                    />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className={styles.stepNavigation}>
                <button className={styles.navBtnSecondary} onClick={() => setStep(2)}>← Programme</button>
                <button className={styles.navBtnPrimary} onClick={() => setStep(4)}>Continue → Review</button>
            </div>
        </div>
    );

    // ── Step 4: Review ──────────────────────────────────────
    const renderStep4 = () => {
        const paradigmInfo = PARADIGM_LABELS[form.paradigm] || {};
        const activePerms = Object.entries(form.permissions).filter(([_, v]) => v).length;
        const totalPerms = Object.keys(form.permissions).length;

        return (
            <div className={styles.stepContent}>
                <div className={styles.stepHeader}>
                    <span className={styles.stepIcon}>📋</span>
                    <div>
                        <h4 className={styles.stepTitle}>Review & Confirm</h4>
                        <p className={styles.stepDesc}>Verify the details below. The facilitator will be created with a default password and their first cohort will be auto-seeded.</p>
                    </div>
                </div>

                <div className={styles.reviewCard}>
                    <div className={styles.reviewSection}>
                        <h5 className={styles.reviewSectionTitle}>Identity</h5>
                        <div className={styles.reviewGrid}>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Name</span>
                                <span className={styles.reviewValue}>{form.name || '—'}</span>
                            </div>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Email</span>
                                <span className={styles.reviewValue}>{form.email || '—'}</span>
                            </div>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Phone</span>
                                <span className={styles.reviewValue}>{form.phone || '—'}</span>
                            </div>
                        </div>
                    </div>

                    <div className={styles.reviewDivider} />

                    <div className={styles.reviewSection}>
                        <h5 className={styles.reviewSectionTitle}>Programme</h5>
                        <div className={styles.reviewGrid}>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Programme</span>
                                <span className={styles.reviewValue}>{form.programme || '—'}</span>
                            </div>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Cohort Limit</span>
                                <span className={styles.reviewValue}>{form.cohorts}</span>
                            </div>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Schedule</span>
                                <span className={styles.reviewValue}>
                                    {form.startDate && form.endDate ? `${form.startDate} → ${form.endDate}`
                                        : form.startDate ? `From ${form.startDate}`
                                        : form.endDate ? `Until ${form.endDate}`
                                        : 'Not set'}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className={styles.reviewDivider} />

                    <div className={styles.reviewSection}>
                        <h5 className={styles.reviewSectionTitle}>Configuration</h5>
                        <div className={styles.reviewGrid}>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Paradigm</span>
                                <span className={styles.paradigmBadge} style={{ color: paradigmInfo.color, background: paradigmInfo.bg }}>
                                    {paradigmInfo.label || form.paradigm}
                                </span>
                            </div>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Permissions</span>
                                <span className={styles.reviewValue}>{activePerms}/{totalPerms} enabled</span>
                            </div>
                        </div>
                    </div>
                </div>

                {form.notes && (
                    <div className={styles.reviewNotes}>
                        <span className={styles.reviewKey}>Notes</span>
                        <p className={styles.reviewNotesText}>{form.notes}</p>
                    </div>
                )}

                <div className={styles.stepNavigation}>
                    <button className={styles.navBtnSecondary} onClick={() => setStep(3)} disabled={creating}>← Configuration</button>
                    <button
                        className={styles.navBtnCreate}
                        onClick={handleSubmit}
                        disabled={creating}
                    >
                        {creating ? '⏳ Creating…' : '✅ Create & Seed Facilitator'}
                    </button>
                </div>
            </div>
        );
    };

    // ── Edit form (all fields on one screen) ────────────────
    const renderEditForm = () => {
        const paradigmInfo = PARADIGM_LABELS[form.paradigm] || {};
        return (
            <div className={styles.stepContent}>
                <div className={styles.stepHeader}>
                    <span className={styles.stepIcon}>✏️</span>
                    <div>
                        <h4 className={styles.stepTitle}>Edit Facilitator</h4>
                        <p className={styles.stepDesc}>Update details for <strong style={{ color: 'var(--text-primary)' }}>{editingFacId}</strong></p>
                    </div>
                </div>

                <div className={styles.formGrid}>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>Full Name</label>
                        <input className={styles.formInput} type="text" value={form.name} onChange={e => updateForm('name', e.target.value)} />
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>Email</label>
                        <input className={styles.formInput} type="email" value={form.email} onChange={e => updateForm('email', e.target.value)} />
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>Phone</label>
                        <input className={styles.formInput} type="tel" value={form.phone} onChange={e => updateForm('phone', e.target.value)} />
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>Programme</label>
                        <input className={styles.formInput} type="text" value={form.programme} onChange={e => updateForm('programme', e.target.value)} />
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>Start Date</label>
                        <input className={styles.formInput} type="date" value={form.startDate} onChange={e => updateForm('startDate', e.target.value)} />
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>End Date</label>
                        <input className={styles.formInput} type="date" value={form.endDate} onChange={e => updateForm('endDate', e.target.value)} />
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>Max Cohorts</label>
                        <input className={styles.formInput} type="number" min="1" max="50" value={form.cohorts} onChange={e => updateForm('cohorts', parseInt(e.target.value, 10) || 1)} />
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>Paradigm</label>
                        <select className={styles.formInput} value={form.paradigm} onChange={e => updateForm('paradigm', e.target.value)}>
                            {PARADIGM_OPTIONS.map(opt => (
                                <option key={opt.id} value={opt.id}>{opt.label}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className={styles.stepNavigation} style={{ marginTop: '1.5rem' }}>
                    <button className={styles.navBtnSecondary} onClick={closeDrawer} disabled={creating}>Cancel</button>
                    <button className={styles.navBtnCreate} onClick={handleSubmit} disabled={creating}>
                        {creating ? '⏳ Saving…' : '💾 Save Changes'}
                    </button>
                </div>
            </div>
        );
    };

    // ── Bulk upload ─────────────────────────────────────────
    const renderBulkUpload = () => (
        <div className={styles.stepContent}>
            <div className={styles.stepHeader}>
                <span className={styles.stepIcon}>📦</span>
                <div>
                    <h4 className={styles.stepTitle}>Bulk Upload Facilitators</h4>
                    <p className={styles.stepDesc}>Upload a CSV or Excel file to create multiple facilitators at once.</p>
                </div>
            </div>

            {/* Expected format help */}
            <div className={styles.bulkFormatBox}>
                <h5 className={styles.bulkFormatTitle}>Expected CSV Columns</h5>
                <code className={styles.bulkFormatCode}>
                    name, email, phone, programme, cohorts, paradigm, start_date, end_date
                </code>
                <p className={styles.bulkFormatHint}>
                    Only <strong>name</strong> is required. Paradigm values: <code>legacy_abc</code>, <code>multi_toggles</code>, <code>advanced_climate</code>, <code>healthcare</code>, <code>un_sdg</code>
                </p>
                <button className={styles.bulkDownloadBtn} onClick={() => {
                    const csv = 'name,email,phone,programme,cohorts,paradigm,start_date,end_date\nProf. Smith,smith@uni.edu,+44 7700 900001,MBA 2026,5,legacy_abc,2026-01-15,2026-06-30\nDr. Jones,jones@uni.edu,,Executive Programme,3,healthcare,,';
                    const blob = new Blob([csv], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url; a.download = 'facilitator_template.csv'; a.click();
                    URL.revokeObjectURL(url);
                }}>
                    ⬇️ Download Template CSV
                </button>
            </div>

            {/* Dropzone */}
            <div
                className={`${styles.dropzone} ${isDragOver ? styles.dropzoneActive : ''}`}
                onDragOver={e => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.txt"
                    style={{ display: 'none' }}
                    onChange={e => handleFileSelect(e.target.files[0])}
                />
                <span className={styles.dropzoneIcon}>{isDragOver ? '📥' : '📄'}</span>
                <p className={styles.dropzoneText}>
                    {isDragOver ? 'Drop your file here' : 'Drag & drop a CSV file here, or click to browse'}
                </p>
                <span className={styles.dropzoneHint}>Supports .csv and .txt formats</span>
            </div>

            {/* Errors */}
            {bulkErrors.length > 0 && (
                <div className={styles.bulkErrors}>
                    {bulkErrors.map((err, i) => (
                        <div key={i} className={styles.bulkErrorRow}>⚠️ {err}</div>
                    ))}
                </div>
            )}

            {/* Preview */}
            {bulkData.length > 0 && (
                <div className={styles.bulkPreview}>
                    <h5 className={styles.bulkPreviewTitle}>
                        Preview — {bulkData.length} facilitator{bulkData.length !== 1 ? 's' : ''} detected
                    </h5>
                    <div className={styles.bulkPreviewTable}>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Name</th>
                                    <th>Email</th>
                                    <th>Programme</th>
                                    <th>Paradigm</th>
                                    <th>Cohorts</th>
                                </tr>
                            </thead>
                            <tbody>
                                {bulkData.map((row, i) => (
                                    <tr key={i} className={!row.name ? styles.rowDanger : ''}>
                                        <td style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>{i + 1}</td>
                                        <td className={styles.facName}>{row.name || <span style={{ color: '#ef4444' }}>MISSING</span>}</td>
                                        <td>{row.email || '—'}</td>
                                        <td>{row.programme || '—'}</td>
                                        <td>
                                            {PARADIGM_LABELS[row.decision_paradigm] ? (
                                                <span className={styles.paradigmBadge} style={{
                                                    color: PARADIGM_LABELS[row.decision_paradigm].color,
                                                    background: PARADIGM_LABELS[row.decision_paradigm].bg,
                                                }}>{PARADIGM_LABELS[row.decision_paradigm].label}</span>
                                            ) : row.decision_paradigm}
                                        </td>
                                        <td>{row.max_cohorts}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            <div className={styles.stepNavigation}>
                <button className={styles.navBtnSecondary} onClick={closeDrawer}>Cancel</button>
                <button
                    className={styles.navBtnCreate}
                    onClick={handleBulkSubmit}
                    disabled={bulkUploading || bulkData.length === 0 || bulkErrors.length > 0}
                >
                    {bulkUploading ? '⏳ Uploading…' : `✅ Create ${bulkData.length} Facilitator${bulkData.length !== 1 ? 's' : ''}`}
                </button>
            </div>
        </div>
    );

    // ────────────────────────────────────────────────────────
    return (
        <section className={styles.container}>

            {/* ── Header ── */}
            <div className={styles.header}>
                <span className={styles.icon}>🎓</span>
                <div style={{ flex: 1 }}>
                    <h2 className={styles.title}>Facilitator Manager</h2>
                    <p className={styles.subtitle}>
                        Create and manage facilitator accounts. Each facilitator can create cohorts up to their assigned limit.
                    </p>
                </div>
                <div className={styles.headerActions}>
                    <button className={styles.bulkBtn} onClick={() => openDrawer('bulk')}>
                        📦 Bulk Import
                    </button>
                    <button className={styles.addBtn} onClick={() => openDrawer('create')}>
                        ➕ Add Facilitator
                    </button>
                </div>
            </div>

            {/* ── Summary Stats Bar ── */}
            {facilitators.length > 0 && (
                <div className={styles.statsBar}>
                    <div className={styles.statCard}>
                        <span className={styles.statValue}>{facilitators.length}</span>
                        <span className={styles.statLabel}>Total Facilitators</span>
                    </div>
                    <div className={styles.statDivider} />
                    <div className={styles.statCard}>
                        <span className={styles.statValue} style={{ color: totalCohortsUsed / Math.max(totalCapacity, 1) > 0.8 ? '#f59e0b' : '#22c55e' }}>
                            {totalCohortsUsed}<span style={{ fontSize: '0.75em', fontWeight: 400, color: 'var(--text-muted)' }}>/{totalCapacity}</span>
                        </span>
                        <span className={styles.statLabel}>Cohort Slots Used</span>
                    </div>
                    <div className={styles.statDivider} />
                    <div className={styles.statCard}>
                        <span className={styles.statValue} style={{ color: atCapacity > 0 ? '#ef4444' : 'var(--text-muted)' }}>
                            {atCapacity}
                        </span>
                        <span className={styles.statLabel}>At Capacity</span>
                    </div>
                    <div style={{ flex: 1 }} />
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Global utilisation</span>
                        <div style={{ width: '80px', height: '6px', borderRadius: '3px', background: 'var(--border-subtle)', overflow: 'hidden' }}>
                            <div style={{
                                width: `${Math.round((totalCohortsUsed / Math.max(totalCapacity, 1)) * 100)}%`,
                                height: '100%', borderRadius: '3px',
                                background: totalCohortsUsed / Math.max(totalCapacity, 1) > 0.8 ? '#ef4444' : '#22c55e',
                                transition: 'width 0.4s ease',
                            }} />
                        </div>
                        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                            {Math.round((totalCohortsUsed / Math.max(totalCapacity, 1)) * 100)}%
                        </span>
                    </div>
                </div>
            )}


            {/* ── Search ── */}
            <div className={styles.searchBar}>
                <span className={styles.searchIcon}>🔍</span>
                <input
                    className={styles.searchInput}
                    type="search"
                    placeholder="Filter by name, ID, email, or programme…"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                />
                {search && (
                    <button onClick={() => setSearch('')} className={styles.clearSearch}>✕</button>
                )}
            </div>

            {/* ── Table ── */}
            {loading ? (
                <div className={styles.empty}>Loading facilitators…</div>
            ) : filtered.length === 0 ? (
                <div className={styles.empty}>
                    {search ? `No facilitators match "${search}"` : 'No facilitators yet — click Add Facilitator to create one.'}
                </div>
            ) : (
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th onClick={() => toggleSort('facilitator_id')} className={styles.sortable}>
                                    Facilitator ID <SortIcon col="facilitator_id" />
                                </th>
                                <th onClick={() => toggleSort('name')} className={styles.sortable}>
                                    Name <SortIcon col="name" />
                                </th>
                                <th>Contact</th>
                                <th onClick={() => toggleSort('programme')} className={styles.sortable}>
                                    Programme <SortIcon col="programme" />
                                </th>
                                <th>Paradigm</th>
                                <th onClick={() => toggleSort('cohorts_created')} className={styles.sortable}>
                                    Cohorts <SortIcon col="cohorts_created" />
                                </th>
                                <th>Schedule</th>
                                <th onClick={() => toggleSort('created_at')} className={styles.sortable}>
                                    Created <SortIcon col="created_at" />
                                </th>
                                <th style={{ textAlign: 'right' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((fac) => {
                                const created = fac.cohorts_created || 0;
                                const max = fac.max_cohorts ?? 5;
                                const pct = getUsagePct(created, max);
                                const barColor = getUsageColor(pct);
                                const isConfirmDelete = confirmDeleteId === fac.facilitator_id;
                                const paradigm = PARADIGM_LABELS[fac.decision_paradigm] || null;

                                return (
                                    <tr key={fac.facilitator_id} className={`${isConfirmDelete ? styles.rowDanger : ''} ${fac.enabled === false ? styles.rowDisabled : ''}`}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <button
                                                    onClick={() => toggleFacilitatorEnabled(fac.facilitator_id, fac.enabled !== false)}
                                                    title={fac.enabled !== false ? 'Enabled — click to disable' : 'Disabled — click to enable'}
                                                    style={{
                                                        position: 'relative', width: '32px', height: '18px', borderRadius: '9px', border: 'none',
                                                        cursor: 'pointer', transition: 'background 0.2s', flexShrink: 0,
                                                        background: fac.enabled !== false ? '#10b981' : '#94a3b8',
                                                    }}
                                                >
                                                    <span style={{
                                                        position: 'absolute', top: '2px',
                                                        left: fac.enabled !== false ? '16px' : '2px',
                                                        width: '14px', height: '14px', borderRadius: '50%',
                                                        background: '#fff', transition: 'left 0.2s',
                                                        boxShadow: '0 1px 2px rgba(0,0,0,0.2)',
                                                    }} />
                                                </button>
                                                <code className={styles.facId} style={{ opacity: fac.enabled === false ? 0.5 : 1 }}>{fac.facilitator_id}</code>
                                            </div>
                                        </td>
                                        <td className={styles.facName}>{fac.name}</td>
                                        <td>
                                            <div className={styles.contactCell}>
                                                {fac.email && <span className={styles.contactItem} title={fac.email}>✉️ {fac.email}</span>}
                                                {fac.contact_number && <span className={styles.contactItem} title={fac.contact_number}>📱 {fac.contact_number}</span>}
                                                {!fac.email && !fac.contact_number && <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>—</span>}
                                            </div>
                                        </td>
                                        <td>
                                            {fac.programme ? (
                                                <span className={styles.programmeBadge}>{fac.programme}</span>
                                            ) : (
                                                <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>—</span>
                                            )}
                                        </td>
                                        <td>
                                            {paradigm ? (
                                                <span className={styles.paradigmBadge} style={{ color: paradigm.color, background: paradigm.bg }}>
                                                    {paradigm.label}
                                                </span>
                                            ) : (
                                                <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>—</span>
                                            )}
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
                                        <td>
                                            <div className={styles.scheduleCell}>
                                                {fac.start_date && <span className={styles.scheduleItem}>From: {fac.start_date}</span>}
                                                {fac.end_date && <span className={styles.scheduleItem}>To: {fac.end_date}</span>}
                                                {!fac.start_date && !fac.end_date && <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>—</span>}
                                            </div>
                                        </td>
                                        <td className={styles.date}>{relativeDate(fac.created_at)}</td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '4px', justifyContent: 'flex-end', alignItems: 'center' }}>
                                                {/* Edit */}
                                                <button
                                                    className={styles.actionBtn}
                                                    onClick={() => openEditDrawer(fac)}
                                                    title="Edit facilitator"
                                                >
                                                    ✏️
                                                </button>
                                                {/* View Cohorts */}
                                                {onNavigate && (
                                                    <button
                                                        className={styles.actionBtn}
                                                        onClick={() => onNavigate('cohort_manager')}
                                                        title="View cohorts"
                                                    >
                                                        🗂️
                                                    </button>
                                                )}
                                                {/* Reset Password */}
                                                <button
                                                    className={styles.actionBtn}
                                                    onClick={() => handleResetPassword(fac.facilitator_id)}
                                                    title="Reset password"
                                                >
                                                    🔑
                                                </button>
                                                {/* Delete */}
                                                <button
                                                    className={`${styles.deleteBtn} ${isConfirmDelete ? styles.deleteBtnConfirm : ''}`}
                                                    onClick={() => handleDeleteClick(fac.facilitator_id)}
                                                    title={isConfirmDelete ? 'Click again to confirm delete' : 'Delete facilitator'}
                                                >
                                                    {isConfirmDelete ? '⚠️ Confirm?' : '🗑️'}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}



            {/* ── Slide-Over Drawer ── */}
            {drawerOpen && (
                <>
                    <div className={styles.drawerOverlay} onClick={closeDrawer} />

                    <div className={`${styles.drawer} ${drawerMode === 'bulk' ? styles.drawerWide : ''}`}>
                        <div className={styles.drawerHeader}>
                            <div>
                                <h3 className={styles.drawerTitle}>
                                    {drawerMode === 'bulk' ? '📦 Bulk Import Facilitators'
                                        : drawerMode === 'edit' ? `✏️ Edit ${editingFacId}`
                                        : '➕ Add New Facilitator'}
                                </h3>
                                <p className={styles.drawerSubtitle}>
                                    {drawerMode === 'bulk' ? 'Upload a CSV or Excel file'
                                        : drawerMode === 'edit' ? 'Modify facilitator details'
                                        : `Step ${step} of ${TOTAL_STEPS} — ${stepTitles[step - 1]}`}
                                </p>
                            </div>
                            <button className={styles.drawerClose} onClick={closeDrawer}>✕</button>
                        </div>

                        {/* Step indicator (create mode only) */}
                        {drawerMode === 'create' && (
                            <div className={styles.stepIndicator}>
                                {[1, 2, 3, 4].map(s => (
                                    <Fragment key={s}>
                                        {s > 1 && <div className={`${styles.stepLine} ${step >= s ? styles.stepLineActive : ''}`} />}
                                        <div
                                            className={`${styles.stepDot} ${step >= s ? styles.stepDotActive : ''} ${step === s ? styles.stepDotCurrent : ''}`}
                                            onClick={() => { if (s < step) setStep(s); }}
                                            style={{ cursor: s < step ? 'pointer' : 'default' }}
                                        >
                                            {step > s ? '✓' : s}
                                        </div>
                                    </Fragment>
                                ))}
                            </div>
                        )}

                        <div className={styles.drawerBody}>
                            {renderStepContent()}
                        </div>
                    </div>
                </>
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
