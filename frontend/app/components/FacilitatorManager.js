'use client';

import { useState, useEffect, useCallback, useRef, Fragment } from 'react';
import styles from './FacilitatorManager.module.css';
import PasswordInput from './PasswordInput';
import dynamic from 'next/dynamic';
import { VERTICAL_CATALOG, VERTICAL_SLOT_MAP, SLOT_META, resolveVerticalMeta } from '../lib/verticalCatalog';

const CreateCohortModal = dynamic(() => import('./CreateCohortModal'), { ssr: false });

const API = process.env.NEXT_PUBLIC_API_URL || '';

// ─── Date formatting ─────────────────────────────────────────────────────
function formatCreatedDate(dateStr) {
    if (!dateStr) return { display: '—', relative: '' };
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return { display: '—', relative: '' };
    const display = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    const diff = Date.now() - d.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    let relative = '';
    if (days === 0) relative = 'Today';
    else if (days === 1) relative = 'Yesterday';
    else if (days < 7) relative = `${days}d ago`;
    else if (days < 30) relative = `${Math.floor(days / 7)}w ago`;
    else relative = `${Math.floor(days / 30)}mo ago`;
    return { display, relative };
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
    brsr_ngrbc: { label: 'BRSR NGRBC', color: '#f97316', bg: 'rgba(249,115,22,0.1)' },
};

const PARADIGM_OPTIONS = [
    { id: 'legacy_abc', label: 'Narrative Crises', sub: 'Classic A/B/C options format — decision-node driven', icon: '≡' },
    { id: 'multi_toggles', label: 'Strategic Pillars', sub: 'Toggle-based multi-vector decisions', icon: '⊞' },
    { id: 'advanced_climate', label: 'Advanced Climate', sub: 'Full climate engine with carbon markets', icon: '🌍' },
    { id: 'healthcare', label: 'Healthcare Edition', sub: 'Clinical operations & patient outcomes', icon: '🏥' },
    { id: 'un_sdg', label: 'UN SDG Goals', sub: 'Sustainable Development Goals framework', icon: '🎯' },
    { id: 'brsr_ngrbc', label: 'BRSR NGRBC Edition', sub: 'India ESG responsibility framework', icon: '🇮🇳' },
];

const EMPTY_FORM = {
    name: '',
    email: '',
    phone: '',
    programme: '',
    cohorts: 5,
    role: 'facilitator',
    paradigm: 'legacy_abc',
    endingPathway: 'activist_ultimatum',
    sideTracks: [],
    simulationMode: 'conglomerate',
    industryVertical: '',
    buSubstitutions: {},
    startDate: '',
    endDate: '',
    shockwaveEnabled: true,
    tradingFloorEnabled: true,   // Feature 1: Trading-Floor finale console capability
    situationRoomEnabled: true,  // W-D (W4): Situation-Room voice bulletin capability
    notes: '',
    createdBy: '',
    dateCreated: new Date().toISOString().slice(0, 10),
    permissions: {
        can_undo_rounds: false,
        can_override_decisions: false,
        can_modify_materiality: false,
        can_manage_auto_pause: false,
        can_create_cohorts: false,
        can_enable_side_tracks: false,
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


export default function FacilitatorManager({ onNavigate, authContext }) {
    // ── Derive operator (the admin using this UI) role ──────────────
    // Priority: explicit authContext prop → localStorage godmode_auth → localStorage facilitator_auth
    const operatorRole = (() => {
        if (authContext?.role) return authContext.role;
        try {
            const stored =
                JSON.parse(localStorage.getItem('godmode_auth') || 'null') ||
                JSON.parse(localStorage.getItem('facilitator_auth') || 'null');
            return stored?.role || null;
        } catch { return null; }
    })();

    // Full permission override: super_admin operators can set ANY permission on
    // ANY facilitator, regardless of the facilitatee's role.
    const isElevatedOperator = operatorRole === 'super_admin';
    const [facilitators, setFacilitators] = useState([]);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState(null);

    const [endingPathways, setEndingPathways] = useState([]);
    const [sideTrackCatalog, setSideTrackCatalog] = useState([]);

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
    const [deleteModal, setDeleteModal] = useState(null);   // { facId, facName } | null
    const [deleteConfirmInput, setDeleteConfirmInput] = useState('');
    const [expandedVisRow, setExpandedVisRow] = useState(null); // facilitator_id of expanded row
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

        // Fetch available ending pathways
        fetch(`${API}/api/admin/ending-pathways`, { credentials: 'include' })
            .then(r => r.json())
            .then(d => {
                setEndingPathways((d.pathways || []).filter(p => p.implemented));
            })
            .catch(() => {});

        // Fetch side track catalog
        fetch(`${API}/api/admin/side-tracks/catalog`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : null)
            .then(d => {
                if (d?.catalog) {
                    setSideTrackCatalog(d.catalog);
                }
            })
            .catch(() => {});

        return () => clearInterval(interval);
    }, [fetchFacilitators]);

    // Persistent toasts (e.g. generated passwords) stay until the browser tab is
    // hidden or the user clicks the toast. Regular toasts auto-dismiss after 4 s.
    const showToast = (msg, type = 'success', { persistent = false } = {}) => {
        setToast({ msg, type, persistent });
        if (!persistent) {
            setTimeout(() => setToast(null), 4000);
        }
    };

    // Dismiss persistent toasts when the user switches / closes the browser tab
    useEffect(() => {
        const handleVisChange = () => {
            if (document.hidden) setToast(prev => (prev?.persistent ? null : prev));
        };
        document.addEventListener('visibilitychange', handleVisChange);
        return () => document.removeEventListener('visibilitychange', handleVisChange);
    }, []);

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
                showToast(`${facId} ${newVal ? 'enabled' : 'disabled'}`);
            } else {
                setFacilitators(prev => prev.map(f => f.facilitator_id === facId ? { ...f, enabled: currentEnabled } : f));
                showToast('Failed to toggle', 'error');
            }
        } catch {
            setFacilitators(prev => prev.map(f => f.facilitator_id === facId ? { ...f, enabled: currentEnabled } : f));
            showToast('Network error', 'error');
        }
    };

    // ── God Mode: inline can_create_cohorts toggle ───────────
    // Allows super_admin operators to flip cohort-creation permission directly
    // from the table row without opening the full edit drawer.
    const toggleCohortCreationPermission = async (fac) => {
        const currentVal = fac.permissions?.can_create_cohorts !== false;
        const newVal = !currentVal;
        // Optimistic update
        setFacilitators(prev => prev.map(f =>
            f.facilitator_id === fac.facilitator_id
                ? { ...f, permissions: { ...(f.permissions || {}), can_create_cohorts: newVal } }
                : f
        ));
        try {
            const headers = { 'Content-Type': 'application/json' };
            try {
                const auth = JSON.parse(
                    localStorage.getItem('godmode_auth') ||
                    localStorage.getItem('facilitator_auth') || '{}'
                );
                if (auth.facilitator_id) headers['x-facilitator-id'] = auth.facilitator_id;
            } catch { /* ignore */ }

            // Send the minimal delta — backend merges with existing record
            const res = await fetch(`${API}/api/admin/facilitators/${fac.facilitator_id}`, {
                method: 'PUT',
                headers,
                credentials: 'include',
                body: JSON.stringify({
                    permissions: { ...(fac.permissions || {}), can_create_cohorts: newVal },
                }),
            });
            if (res.ok) {
                showToast(
                    newVal
                        ? `✅ Cohort creation enabled for ${fac.name}`
                        : `🔒 Cohort creation disabled for ${fac.name}`
                );
            } else {
                // Rollback on failure
                setFacilitators(prev => prev.map(f =>
                    f.facilitator_id === fac.facilitator_id
                        ? { ...f, permissions: { ...(f.permissions || {}), can_create_cohorts: currentVal } }
                        : f
                ));
                const err = await res.json().catch(() => ({}));
                showToast(err.detail || 'Failed to update permission', 'error');
            }
        } catch {
            // Rollback on network error
            setFacilitators(prev => prev.map(f =>
                f.facilitator_id === fac.facilitator_id
                    ? { ...f, permissions: { ...(f.permissions || {}), can_create_cohorts: currentVal } }
                    : f
            ));
            showToast('Network error — permission not saved', 'error');
        }
    };

    // ── New Cohort Modal ─────────────────────────────────────────────
    const [showCohortModal, setShowCohortModal] = useState(false);
    const [cohortFacilitatorId, setCohortFacilitatorId] = useState(null);

    // ── Role Change Verification Modal ──────────────────────────────
    const [roleChangeModal, setRoleChangeModal] = useState(null); // { facId, facName, newRole, currentRole } | null
    const [roleVerifyFacId, setRoleVerifyFacId] = useState('');
    const [roleVerifyPassword, setRoleVerifyPassword] = useState('');
    const [roleVerifyError, setRoleVerifyError] = useState('');
    const [roleVerifyLoading, setRoleVerifyLoading] = useState(false);

    const openRoleChangeModal = (facId, facName, newRole, currentRole) => {
        setRoleChangeModal({ facId, facName, newRole, currentRole });
        setRoleVerifyFacId('');
        setRoleVerifyPassword('');
        setRoleVerifyError('');
        setRoleVerifyLoading(false);
    };

    const closeRoleChangeModal = () => {
        setRoleChangeModal(null);
        setRoleVerifyFacId('');
        setRoleVerifyPassword('');
        setRoleVerifyError('');
        setRoleVerifyLoading(false);
    };

    const handleRoleChangeVerified = async () => {
        if (!roleChangeModal) return;
        const { facId, facName, newRole } = roleChangeModal;
        if (!roleVerifyFacId.trim() || !roleVerifyPassword.trim()) {
            setRoleVerifyError('Please enter your God Mode Facilitator ID and password.');
            return;
        }
        setRoleVerifyLoading(true);
        setRoleVerifyError('');
        try {
            const res = await fetch(`${API}/api/admin/facilitators/${facId}/role`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    role: newRole,
                    god_mode_fac_id: roleVerifyFacId.trim(),
                    god_mode_password: roleVerifyPassword.trim(),
                }),
            });
            if (res.ok) {
                setFacilitators(prev => prev.map(f =>
                    f.facilitator_id === facId
                        ? { ...f, role: newRole, is_admin: newRole === 'super_admin' }
                        : f
                ));
                showToast(`${facName} role changed to ${newRole.replace(/_/g, ' ')}`);
                closeRoleChangeModal();
            } else {
                const err = await res.json().catch(() => ({}));
                setRoleVerifyError(err.detail || 'Verification failed. Check your credentials.');
            }
        } catch {
            setRoleVerifyError('Network error — could not reach server.');
        } finally {
            setRoleVerifyLoading(false);
        }
    };

    const handleOpenNewCohort = (facId) => {
        setCohortFacilitatorId(facId || (facilitators[0]?.facilitator_id ?? null));
        setShowCohortModal(true);
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
            endingPathway: fac.ending_pathway || 'activist_ultimatum',
            sideTracks: fac.side_tracks || [],
            simulationMode: fac.simulation_mode || 'conglomerate',
            industryVertical: fac.industry_vertical || '',
            buSubstitutions: fac.bu_substitutions || {},
            startDate: formatDateInput(fac.start_date),
            endDate: formatDateInput(fac.end_date),
            notes: fac.notes || '',
            role: fac.role || (fac.is_admin ? 'super_admin' : 'facilitator'),
            permissions: fac.permissions || { ...EMPTY_FORM.permissions },
            // Console capabilities — hydrate from the record. (Pre-existing
            // bug fixed here: shockwaveEnabled was NOT hydrated on edit, so
            // saving any edit silently re-enabled Shockwave.)
            shockwaveEnabled: fac.shockwave_enabled !== false,
            tradingFloorEnabled: fac.trading_floor_enabled !== false,
            situationRoomEnabled: fac.situation_room_enabled !== false,
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
    const handleRoleSelect = (selectedRole) => {
        const isFac = selectedRole === 'facilitator';
        setForm(prev => ({
            ...prev,
            role: selectedRole,
            permissions: {
                can_undo_rounds: !isFac,
                can_override_decisions: !isFac,
                can_modify_materiality: !isFac,
                can_manage_auto_pause: !isFac,
                can_create_cohorts: !isFac,
                can_enable_side_tracks: !isFac,
            }
        }));
    };

    // ── Validation per step ─────────────────────────────────
    const canAdvanceStep = (s) => {
        if (s === 1) return form.name.trim().length > 0 && form.createdBy.trim().length > 0 && !!form.dateCreated;
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
                ending_pathway: form.endingPathway,
                side_tracks: form.sideTracks,
                simulation_mode: form.simulationMode,
                industry_vertical: form.industryVertical,
                bu_substitutions: form.buSubstitutions,
                permissions: form.permissions,
                created_by: form.createdBy.trim(),
                date_created: form.dateCreated,
                role: form.role,
                shockwave_enabled: form.shockwaveEnabled !== false,  // Feature 6 capability
                trading_floor_enabled: form.tradingFloorEnabled !== false,  // Feature 1 capability
                situation_room_enabled: form.situationRoomEnabled !== false,  // W-D (W4) capability
            };

            const getAuthHeaders = () => {
                let headers = { 'Content-Type': 'application/json' };
                try {
                    const auth = JSON.parse(
                        localStorage.getItem('godmode_auth') || 
                        localStorage.getItem('facilitator_auth') || '{}'
                    );
                    if (auth.facilitator_id) {
                        headers['x-facilitator-id'] = auth.facilitator_id;
                    }
                } catch (e) {}
                return headers;
            };

            if (drawerMode === 'edit' && editingFacId) {
                // Update existing
                const res = await fetch(`${API}/api/admin/facilitators/${editingFacId}`, {
                    method: 'PUT',
                    headers: getAuthHeaders(),
                    credentials: 'include',
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
                    headers: getAuthHeaders(),
                    credentials: 'include',
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
                    headers: getAuthHeaders(),
                    credentials: 'include',
                    body: JSON.stringify({
                        cohort_name: cohortName,
                        decision_paradigm: form.paradigm,
                        facilitator_id: fac.facilitator_id,
                        created_by: form.createdBy.trim(),
                        created_when: form.dateCreated,
                        ending_pathway: form.endingPathway,
                        simulation_mode: form.simulationMode === 'single_bu' ? 'single_bu' : 'standard',
                        industry_vertical: form.simulationMode === 'single_bu' ? form.industryVertical : undefined,
                    }),
                });

                if (seedRes.ok) {
                    const newSession = await seedRes.json();
                    if (newSession.session_id) {
                        // Apply side tracks defaults
                        if (form.sideTracks && form.sideTracks.length > 0) {
                            await fetch(`${API}/api/admin/cohorts/${newSession.session_id}/side-tracks`, {
                                method: 'PUT',
                                headers: getAuthHeaders(),
                                credentials: 'include',
                                body: JSON.stringify({ tracks: form.sideTracks }),
                            }).catch(() => {});
                        }
                        // Apply BU substitutions defaults
                        if (form.simulationMode === 'single_bu' && form.buSubstitutions && Object.keys(form.buSubstitutions).length > 0) {
                            await fetch(`${API}/api/admin/${newSession.session_id}/bu-composition`, {
                                method: 'PUT',
                                headers: getAuthHeaders(),
                                credentials: 'include',
                                body: JSON.stringify({ substitutions: form.buSubstitutions, bu_regions: {} }),
                            }).catch(() => {});
                        }
                    }
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
    // W-PA: .xlsx files are parsed SERVER-side by /facilitators/bulk-upload
    // (openpyxl) — creation happens immediately with per-row results.
    // CSV/TXT keep the existing client-side parse → preview → submit flow.
    const handleExcelUpload = async (file) => {
        setBulkUploading(true);
        setBulkErrors([]);
        try {
            const fd = new FormData();
            fd.append('file', file);
            const res = await fetch(`${API}/api/admin/facilitators/bulk-upload`, {
                method: 'POST', credentials: 'include', body: fd,
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                setBulkErrors([typeof data.detail === 'string' ? data.detail : `Upload failed (${res.status})`]);
                return;
            }
            setBulkErrors((data.errors || []).map(e => `Row ${e.row}: ${e.error}`));
            showToast(`✅ ${data.total_created} facilitator(s) created from Excel${data.total_errors ? ` · ${data.total_errors} row(s) skipped` : ''}`);
            await fetchFacilitators();
            if (!data.total_errors) closeDrawer();
        } catch {
            setBulkErrors(['Network error during Excel upload']);
        } finally {
            setBulkUploading(false);
        }
    };

    const handleFileSelect = (file) => {
        if (!file) return;
        if (/\.xlsx$/i.test(file.name || '')) { handleExcelUpload(file); return; }
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
                credentials: 'include',
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

    // ── Delete: open typed-confirmation modal ─────────────────
    const handleDeleteClick = (facId, facName) => {
        setDeleteModal({ facId, facName });
        setDeleteConfirmInput('');
    };

    const handleDelete = async (facId) => {
        setDeleteModal(null);
        setDeleteConfirmInput('');
        try {
            const res = await fetch(`${API}/api/admin/facilitators/${facId}`, {
                method: 'DELETE',
                credentials: 'include',
            });
            if (res.ok) {
                setFacilitators(prev => prev.filter(f => f.facilitator_id !== facId));
                showToast(`Deleted ${facId}`);
            } else {
                const err = await res.json().catch(() => ({}));
                showToast(`Delete failed: ${err.detail || res.status}`, 'error');
            }
        } catch {
            showToast('Delete failed: network error', 'error');
        }
    };



    // ── Reset Password ───────────────────────────────────────
    const [pwCopied, setPwCopied] = useState(false);
    const handleResetPassword = async (facId) => {
        try {
            const res = await fetch(`${API}/api/admin/facilitators/${facId}/reset-password`, {
                method: 'POST',
                credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                const newPw = data.new_password || data.password || '(check server)';
                const emailSent = data.email_sent;
                const emailTo = data.email_to;
                setPwCopied(false);
                showToast(
                    { password: newPw, emailSent, emailTo, facId },
                    'success',
                    { persistent: true }
                );
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
    const stepTitles = ['Identity', 'Programme', 'Permissions', 'Review & Confirm'];

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
                    <p className={styles.stepDesc}>Enter the facilitator&apos;s personal details. A unique ID (FAC-XXX) and default password will be auto-generated.</p>
                </div>
            </div>

            {/* Role Selection at the top of Step 1 */}
            <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '1.25rem' }}>
                <label className={styles.formLabel} style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem', display: 'block' }}>Assign Operative Role <span className={styles.required}>*</span></label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                    {[
                        { id: 'facilitator', label: 'Facilitator', icon: '🎓', desc: 'Can run preassigned cohorts' },
                        { id: 'lead_facilitator', label: 'Lead Facilitator', icon: '⭐', desc: 'Can configure all parameters' },
                        { id: 'super_admin', label: 'Super Admin', icon: '👑', desc: 'Full administrative access' },
                    ].map(r => {
                        const isSelected = form.role === r.id;
                        const activeColor = r.id === 'super_admin' ? '#f59e0b' : r.id === 'lead_facilitator' ? '#818cf8' : '#3b82f6';
                        const activeBg = r.id === 'super_admin' ? 'rgba(245,158,11,0.1)' : r.id === 'lead_facilitator' ? 'rgba(99,102,241,0.1)' : 'rgba(59,130,246,0.1)';
                        return (
                            <button
                                key={r.id}
                                type="button"
                                onClick={() => handleRoleSelect(r.id)}
                                style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    gap: '6px',
                                    padding: '12px 10px',
                                    borderRadius: '10px',
                                    cursor: 'pointer',
                                    textAlign: 'center',
                                    border: isSelected ? `2px solid ${activeColor}` : '1.5px solid rgba(100,116,139,0.15)',
                                    background: isSelected ? activeBg : 'rgba(15,23,42,0.3)',
                                    transition: 'all 0.15s ease',
                                    outline: 'none',
                                }}
                            >
                                <span style={{ fontSize: '1.5rem' }}>{r.icon}</span>
                                <span style={{ fontWeight: 700, fontSize: '0.8rem', color: isSelected ? '#fff' : '#94a3b8' }}>{r.label}</span>
                                <span style={{ fontSize: '0.62rem', color: isSelected ? '#cbd5e1' : '#64748b', lineHeight: 1.2 }}>{r.desc}</span>
                            </button>
                        );
                    })}
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

                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Created By <span className={styles.required}>*</span></label>
                    <input
                        id="fac-created-by-input"
                        className={styles.formInput}
                        type="text"
                        placeholder="e.g. Admin, Prof. Sharma"
                        value={form.createdBy}
                        onChange={e => updateForm('createdBy', e.target.value)}
                        style={{ borderColor: !form.createdBy.trim() && form.name.trim() ? 'rgba(239,68,68,0.5)' : undefined }}
                    />
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>Person creating this facilitator account</span>
                </div>

                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Date Created <span className={styles.required}>*</span></label>
                    <input
                        id="fac-date-created-input"
                        className={styles.formInput}
                        type="date"
                        value={form.dateCreated}
                        onChange={e => updateForm('dateCreated', e.target.value)}
                        style={{ borderColor: !form.dateCreated && form.name.trim() ? 'rgba(239,68,68,0.5)' : undefined }}
                    />
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>Date this account is being created</span>
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
                <button className={styles.navBtnPrimary} onClick={() => setStep(3)}>Continue → Permissions</button>
            </div>
        </div>
    );

    // ── Step 3: Permissions ──────────────────────────────────
    const renderStep3 = () => (
        <div className={styles.stepContent}>
            <div className={styles.stepHeader}>
                <span className={styles.stepIcon}>⚙️</span>
                <div>
                    <h4 className={styles.stepTitle}>Permissions & Cohort Defaults</h4>
                    <p className={styles.stepDesc}>Configure what this facilitator is allowed to do, and set the default simulation parameters for their cohorts.</p>
                </div>
            </div>

            {form.role === 'super_admin' ? (
                <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', padding: '16px', borderRadius: 10, marginBottom: '1.25rem' }}>
                    <span style={{ fontSize: '1.25rem', marginRight: 8 }}>👑</span>
                    <span style={{ fontSize: '0.82rem', color: '#f59e0b', fontWeight: 700 }}>Super Administrator Privileges Enabled</span>
                    <p style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 6, lineHeight: 1.4 }}>Super administrators have unrestricted access across the entire platform, including user management, database resets, and all simulation orchestration tools. Permissions cannot be customized.</p>
                </div>
            ) : (
                <div className={styles.permissionsSection} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', paddingBottom: '1.25rem' }}>
                    <label className={styles.formLabel} style={{ marginBottom: '0.6rem' }}>Admin Permissions</label>
                    <div className={styles.permGrid}>
                        {/* God Mode Override Banner — visible only when operator is super_admin
                             editing a plain facilitator (whose perms would normally be locked) */}
                        {isElevatedOperator && form.role === 'facilitator' && (
                            <div style={{
                                gridColumn: '1 / -1',
                                display: 'flex', alignItems: 'flex-start', gap: '10px',
                                padding: '10px 14px',
                                borderRadius: '8px',
                                background: 'rgba(245,158,11,0.08)',
                                border: '1px solid rgba(245,158,11,0.3)',
                                marginBottom: '4px',
                            }}>
                                <span style={{ fontSize: '1rem', flexShrink: 0 }}>👑</span>
                                <div>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b', display: 'block' }}>
                                        God Mode Override Active
                                    </span>
                                    <span style={{ fontSize: '0.68rem', color: '#94a3b8', lineHeight: 1.4 }}>
                                        All permissions are individually editable for this Facilitator.
                                        Role-based locking is suspended for Super Administrators.
                                    </span>
                                </div>
                            </div>
                        )}

                        {[
                            { key: 'can_create_cohorts', label: 'Create Cohorts', icon: '🚀' },
                            { key: 'can_undo_rounds', label: 'Undo Rounds', icon: '↩️' },
                            { key: 'can_override_decisions', label: 'Override Decisions', icon: '🔧' },
                            { key: 'can_modify_materiality', label: 'Modify Materiality', icon: '📊' },
                            { key: 'can_manage_auto_pause', label: 'Manage Auto-Pause', icon: '⏸️' },
                            { key: 'can_enable_side_tracks', label: 'Enable Side Tracks', icon: '🛤️' },
                        ].map(perm => {
                            // Elevated operators (super_admin) can set any permission on any
                            // facilitatee regardless of role. Otherwise, plain Facilitator
                            // role locks all permissions to their role defaults.
                            const isEditable = isElevatedOperator || form.role !== 'facilitator';
                            return (
                                <div
                                    key={perm.key}
                                    className={`${styles.permCard} ${form.permissions[perm.key] ? styles.permCardActive : ''}`}
                                    onClick={() => {
                                        if (isEditable) {
                                            updatePermission(perm.key, !form.permissions[perm.key]);
                                        }
                                    }}
                                    style={{
                                        opacity: !isEditable ? 0.5 : 1,
                                        cursor: !isEditable ? 'not-allowed' : 'pointer',
                                        // Subtle amber glow on god-mode-unlocked cards for a facilitator
                                        ...(isElevatedOperator && form.role === 'facilitator' ? {
                                            borderColor: 'rgba(245,158,11,0.25)',
                                        } : {}),
                                    }}
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
                            );
                        })}
                    </div>
                </div>
            )}

            {form.role === 'super_admin' ? (
                <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', padding: '16px', borderRadius: 10, marginTop: '1.25rem' }}>
                    <span style={{ fontSize: '1.25rem', marginRight: 8 }}>⚙️</span>
                    <span style={{ fontSize: '0.82rem', color: '#cbd5e1', fontWeight: 700 }}>Cohort Creation Presets Not Applicable</span>
                    <p style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 6, lineHeight: 1.4 }}>Presets are not required because Super Administrators have full configuration rights on the cohort creation screen itself.</p>
                </div>
            ) : (
                <div className={styles.permissionsSection} style={{ marginTop: '1.25rem' }}>
                    <label className={styles.formLabel} style={{ marginBottom: '0.6rem' }}>Cohort Defaults Configuration</label>
                    <p className={styles.stepDesc} style={{ marginBottom: '1rem' }}>
                        These features will be pre-selected and locked for any cohorts this facilitator creates.
                    </p>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        {/* Decision Paradigm */}
                        <div className={styles.formGroup}>
                            <label className={styles.formLabel}>Decision Paradigm</label>
                            <select
                                className={styles.formInput}
                                value={form.paradigm}
                                onChange={e => updateForm('paradigm', e.target.value)}
                            >
                                {PARADIGM_OPTIONS.map(opt => (
                                    <option key={opt.id} value={opt.id}>{opt.label}</option>
                                ))}
                            </select>
                        </div>

                        {/* Ending Pathway */}
                        <div className={styles.formGroup}>
                            <label className={styles.formLabel}>Ending Pathway</label>
                            <select
                                className={styles.formInput}
                                value={form.endingPathway}
                                onChange={e => updateForm('endingPathway', e.target.value)}
                            >
                                <option value="random">🎲 Random (Surprise Ending)</option>
                                {endingPathways.map(p => (
                                    <option key={p.id} value={p.id}>{p.icon} {p.title}</option>
                                ))}
                                {endingPathways.length === 0 && (
                                    <>
                                        <option value="activist_ultimatum">📣 Activist Ultimatum</option>
                                        <option value="hostile_takeover">💼 Hostile Takeover</option>
                                        <option value="regulatory_collapse">⚖️ Regulatory Collapse</option>
                                        <option value="black_swan_epidemic">🦢 Black Swan Epidemic</option>
                                    </>
                                )}
                            </select>
                        </div>
                    </div>

                    {/* Feature 6: per-facilitator Shockwave capability */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem', padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.06)' }}>
                        <div>
                            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>🌊 Shockwave detonation</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #8899a6)' }}>Allow this facilitator to trigger synchronized cohort-wide crisis events.</div>
                        </div>
                        <label style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: form.shockwaveEnabled !== false ? '#ef4444' : '#8899a6' }}>{form.shockwaveEnabled !== false ? 'ON' : 'OFF'}</span>
                            <span onClick={() => updateForm('shockwaveEnabled', !(form.shockwaveEnabled !== false))} style={{ position: 'relative', width: 44, height: 24, borderRadius: 12, background: form.shockwaveEnabled !== false ? '#ef4444' : 'rgba(148,163,184,0.3)', transition: 'background 0.2s', display: 'inline-block' }}>
                                <span style={{ position: 'absolute', top: 3, left: 3, width: 18, height: 18, borderRadius: '50%', background: '#fff', transition: 'transform 0.2s', transform: form.shockwaveEnabled !== false ? 'translateX(20px)' : 'translateX(0)' }} />
                            </span>
                        </label>
                    </div>

                    {/* Feature 1: per-facilitator Trading-Floor finale capability */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.6rem', padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(245,158,11,0.3)', background: 'rgba(245,158,11,0.06)' }}>
                        <div>
                            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>🔔 Trading-Floor finale</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #8899a6)' }}>Allow this facilitator to open the projector market board and ring the closing bell.</div>
                        </div>
                        <label style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: form.tradingFloorEnabled !== false ? '#f59e0b' : '#8899a6' }}>{form.tradingFloorEnabled !== false ? 'ON' : 'OFF'}</span>
                            <span onClick={() => updateForm('tradingFloorEnabled', !(form.tradingFloorEnabled !== false))} style={{ position: 'relative', width: 44, height: 24, borderRadius: 12, background: form.tradingFloorEnabled !== false ? '#f59e0b' : 'rgba(148,163,184,0.3)', transition: 'background 0.2s', display: 'inline-block' }}>
                                <span style={{ position: 'absolute', top: 3, left: 3, width: 18, height: 18, borderRadius: '50%', background: '#fff', transition: 'transform 0.2s', transform: form.tradingFloorEnabled !== false ? 'translateX(20px)' : 'translateX(0)' }} />
                            </span>
                        </label>
                    </div>

                    {/* W-D (W4): per-facilitator Situation-Room bulletin capability */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.6rem', padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(201,168,76,0.3)', background: 'rgba(201,168,76,0.06)' }}>
                        <div>
                            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>🎙️ Situation-Room bulletin</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #8899a6)' }}>Allow this facilitator to fire voiced market-news bulletins from the Teleprompter (facilitator screen only).</div>
                        </div>
                        <label style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: form.situationRoomEnabled !== false ? '#c9a84c' : '#8899a6' }}>{form.situationRoomEnabled !== false ? 'ON' : 'OFF'}</span>
                            <span onClick={() => updateForm('situationRoomEnabled', !(form.situationRoomEnabled !== false))} style={{ position: 'relative', width: 44, height: 24, borderRadius: 12, background: form.situationRoomEnabled !== false ? '#c9a84c' : 'rgba(148,163,184,0.3)', transition: 'background 0.2s', display: 'inline-block' }}>
                                <span style={{ position: 'absolute', top: 3, left: 3, width: 18, height: 18, borderRadius: '50%', background: '#fff', transition: 'transform 0.2s', transform: form.situationRoomEnabled !== false ? 'translateX(20px)' : 'translateX(0)' }} />
                            </span>
                        </label>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                        {/* Simulation Mode */}
                        <div className={styles.formGroup}>
                            <label className={styles.formLabel}>Simulation Mode</label>
                            <select
                                className={styles.formInput}
                                value={form.simulationMode}
                                onChange={e => updateForm('simulationMode', e.target.value)}
                            >
                                <option value="conglomerate">🏢 4-BU Conglomerate</option>
                                <option value="single_bu">🏭 Single Business</option>
                            </select>
                        </div>

                        {/* Industry Vertical (only for single_bu) */}
                        {form.simulationMode === 'single_bu' && (
                            <div className={styles.formGroup}>
                                <label className={styles.formLabel}>Industry Vertical</label>
                                <select
                                    className={styles.formInput}
                                    value={form.industryVertical}
                                    onChange={e => {
                                        const vertical = e.target.value;
                                        updateForm('industryVertical', vertical);
                                        // Auto-set buSubstitutions: only for non-default verticals
                                        if (vertical) {
                                            const slot = VERTICAL_SLOT_MAP[vertical];
                                            const isDefault = VERTICAL_CATALOG.find(v => v.id === vertical)?.isDefault;
                                            updateForm('buSubstitutions', isDefault ? {} : (slot ? { [slot]: vertical } : {}));
                                        } else {
                                            updateForm('buSubstitutions', {});
                                        }
                                    }}
                                    required
                                >
                                    <option value="">-- Select Industry --</option>
                                    {SLOT_META.map(sm => {
                                        const entries = VERTICAL_CATALOG.filter(v => v.slot === sm.slot);
                                        return (
                                            <optgroup key={sm.slot} label={`${sm.icon} ${sm.label} slot`}>
                                                {entries.map(v => (
                                                    <option key={v.id} value={v.id}>
                                                        {v.icon} {v.label}{v.isDefault ? '' : ' ↔'}
                                                    </option>
                                                ))}
                                            </optgroup>
                                        );
                                    })}
                                </select>
                            </div>
                        )}
                    </div>

                    {/* Side Tracks Checkboxes */}
                    <div style={{ marginTop: '1.25rem' }}>
                        <label className={styles.formLabel} style={{ marginBottom: '0.4rem' }}>Default Side Tracks</label>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
                            {sideTrackCatalog.map(track => {
                                const isChecked = form.sideTracks.includes(track.track_id);
                                return (
                                    <label key={track.track_id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)', cursor: 'pointer', background: 'rgba(255,255,255,0.02)', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)' }}>
                                        <input
                                            type="checkbox"
                                            checked={isChecked}
                                            onChange={() => {
                                                if (isChecked) {
                                                    updateForm('sideTracks', form.sideTracks.filter(id => id !== track.track_id));
                                                } else {
                                                    updateForm('sideTracks', [...form.sideTracks, track.track_id]);
                                                }
                                            }}
                                        />
                                        <span>{track.icon || '📦'} {track.display_name || track.track_id}</span>
                                    </label>
                                );
                            })}
                            {sideTrackCatalog.length === 0 && (
                                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>Loading side tracks...</span>
                            )}
                        </div>
                    </div>
                </div>
            )}

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
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Created By</span>
                                <span className={styles.reviewValue}>{form.createdBy || '—'}</span>
                            </div>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Date Created</span>
                                <span className={styles.reviewValue}>{form.dateCreated || '—'}</span>
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
                        <h5 className={styles.reviewSectionTitle}>Permissions & Cohort Defaults</h5>
                        <div className={styles.reviewGrid}>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Paradigm</span>
                                <span className={styles.reviewValue}>
                                    {PARADIGM_LABELS[form.paradigm]?.label || form.paradigm}
                                </span>
                            </div>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Ending Pathway</span>
                                <span className={styles.reviewValue}>
                                    {form.endingPathway === 'random' ? '🎲 Random (Surprise)' : (endingPathways.find(p => p.id === form.endingPathway)?.title || form.endingPathway)}
                                </span>
                            </div>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Simulation Mode</span>
                                <span className={styles.reviewValue}>
                                    {form.simulationMode === 'single_bu' ? `🏭 Single BU (${resolveVerticalMeta(form.industryVertical).icon} ${resolveVerticalMeta(form.industryVertical).label})` : '🏢 Conglomerate'}
                                </span>
                            </div>
                            <div className={styles.reviewItem}>
                                <span className={styles.reviewKey}>Side Tracks</span>
                                <span className={styles.reviewValue}>
                                    {form.sideTracks && form.sideTracks.length > 0 ? form.sideTracks.map(tid => sideTrackCatalog.find(t => t.track_id === tid)?.display_name || tid).join(', ') : 'None'}
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
                    <button className={styles.navBtnSecondary} onClick={() => setStep(3)} disabled={creating}>← Permissions</button>
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
        const activePerms = Object.entries(form.permissions).filter(([_, v]) => v).length;
        const totalPerms = Object.keys(form.permissions).length;
        return (
            <div className={styles.stepContent}>
                <div className={styles.stepHeader}>
                    <span className={styles.stepIcon}>✏️</span>
                    <div>
                        <h4 className={styles.stepTitle}>Edit Facilitator</h4>
                        <p className={styles.stepDesc}>Update details for <strong style={{ color: 'var(--text-primary)' }}>{editingFacId}</strong></p>
                    </div>
                </div>

                {/* Role Selection */}
                <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '1.25rem' }}>
                    <label className={styles.formLabel} style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem', display: 'block' }}>Assign Operative Role <span className={styles.required}>*</span></label>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                        {[
                            { id: 'facilitator', label: 'Facilitator', icon: '🎓', desc: 'Can run preassigned cohorts' },
                            { id: 'lead_facilitator', label: 'Lead Facilitator', icon: '⭐', desc: 'Can configure all parameters' },
                            { id: 'super_admin', label: 'Super Admin', icon: '👑', desc: 'Full administrative access' },
                        ].map(r => {
                            const isSelected = form.role === r.id;
                            const activeColor = r.id === 'super_admin' ? '#f59e0b' : r.id === 'lead_facilitator' ? '#818cf8' : '#3b82f6';
                            const activeBg = r.id === 'super_admin' ? 'rgba(245,158,11,0.1)' : r.id === 'lead_facilitator' ? 'rgba(99,102,241,0.1)' : 'rgba(59,130,246,0.1)';
                            return (
                                <button
                                    key={r.id}
                                    type="button"
                                    onClick={() => handleRoleSelect(r.id)}
                                    style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        gap: '6px',
                                        padding: '12px 10px',
                                        borderRadius: '10px',
                                        cursor: 'pointer',
                                        textAlign: 'center',
                                        border: isSelected ? `2px solid ${activeColor}` : '1.5px solid rgba(100,116,139,0.15)',
                                        background: isSelected ? activeBg : 'rgba(15,23,42,0.3)',
                                        transition: 'all 0.15s ease',
                                        outline: 'none',
                                    }}
                                >
                                    <span style={{ fontSize: '1.5rem' }}>{r.icon}</span>
                                    <span style={{ fontWeight: 700, fontSize: '0.8rem', color: isSelected ? '#fff' : '#94a3b8' }}>{r.label}</span>
                                    <span style={{ fontSize: '0.62rem', color: isSelected ? '#cbd5e1' : '#64748b', lineHeight: 1.2 }}>{r.desc}</span>
                                </button>
                            );
                        })}
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
                        <label className={styles.formLabel}>Decision Paradigm</label>
                        <select className={styles.formInput} value={form.paradigm} onChange={e => updateForm('paradigm', e.target.value)}>
                            {PARADIGM_OPTIONS.map(opt => (
                                <option key={opt.id} value={opt.id}>{opt.label}</option>
                            ))}
                        </select>
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>Ending Pathway</label>
                        <select
                            className={styles.formInput}
                            value={form.endingPathway}
                            onChange={e => updateForm('endingPathway', e.target.value)}
                        >
                            <option value="random">🎲 Random (Surprise Ending)</option>
                            {endingPathways.map(p => (
                                <option key={p.id} value={p.id}>{p.icon} {p.title}</option>
                            ))}
                            {endingPathways.length === 0 && (
                                <>
                                    <option value="activist_ultimatum">📣 Activist Ultimatum</option>
                                    <option value="hostile_takeover">💼 Hostile Takeover</option>
                                    <option value="regulatory_collapse">⚖️ Regulatory Collapse</option>
                                    <option value="black_swan_epidemic">🦢 Black Swan Epidemic</option>
                                </>
                            )}
                        </select>
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>Simulation Mode</label>
                        <select
                            className={styles.formInput}
                            value={form.simulationMode}
                            onChange={e => updateForm('simulationMode', e.target.value)}
                        >
                            <option value="conglomerate">🏢 4-BU Conglomerate</option>
                            <option value="single_bu">🏭 Single Business</option>
                        </select>
                    </div>

                    {form.simulationMode === 'single_bu' && (
                        <div className={styles.formGroup}>
                            <label className={styles.formLabel}>Industry Vertical</label>
                            <select
                                className={styles.formInput}
                                value={form.industryVertical}
                                onChange={e => {
                                    const vertical = e.target.value;
                                    updateForm('industryVertical', vertical);
                                    if (vertical) {
                                        const slot = VERTICAL_SLOT_MAP[vertical];
                                        const isDefault = VERTICAL_CATALOG.find(v => v.id === vertical)?.isDefault;
                                        updateForm('buSubstitutions', isDefault ? {} : (slot ? { [slot]: vertical } : {}));
                                    } else {
                                        updateForm('buSubstitutions', {});
                                    }
                                }}
                                required
                            >
                                <option value="">-- Select Industry --</option>
                                {SLOT_META.map(sm => {
                                    const entries = VERTICAL_CATALOG.filter(v => v.slot === sm.slot);
                                    return (
                                        <optgroup key={sm.slot} label={`${sm.icon} ${sm.label} slot`}>
                                            {entries.map(v => (
                                                <option key={v.id} value={v.id}>
                                                    {v.icon} {v.label}{v.isDefault ? '' : ' ↔'}
                                                </option>
                                            ))}
                                        </optgroup>
                                    );
                                })}
                            </select>
                        </div>
                    )}

                </div>

                {/* Edit Side Tracks */}
                <div style={{ marginTop: '1.25rem', borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '1rem' }}>
                    <label className={styles.formLabel} style={{ marginBottom: '0.4rem' }}>Default Side Tracks</label>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
                        {sideTrackCatalog.map(track => {
                            const isChecked = form.sideTracks.includes(track.track_id);
                            return (
                                <label key={track.track_id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)', cursor: 'pointer', background: 'rgba(255,255,255,0.02)', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)' }}>
                                    <input
                                        type="checkbox"
                                        checked={isChecked}
                                        onChange={() => {
                                            if (isChecked) {
                                                updateForm('sideTracks', form.sideTracks.filter(id => id !== track.track_id));
                                            } else {
                                                updateForm('sideTracks', [...form.sideTracks, track.track_id]);
                                            }
                                        }}
                                    />
                                    <span>{track.icon || '📦'} {track.display_name || track.track_id}</span>
                                </label>
                            );
                        })}
                    </div>
                </div>

                {/* Edit Permissions */}
                {form.role === 'super_admin' ? (
                    <div style={{ marginTop: '1.25rem', borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '1rem' }}>
                        <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', padding: '16px', borderRadius: 10 }}>
                            <span style={{ fontSize: '1.25rem', marginRight: 8 }}>👑</span>
                            <span style={{ fontSize: '0.82rem', color: '#f59e0b', fontWeight: 700 }}>Super Administrator Privileges Enabled</span>
                            <p style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 6, lineHeight: 1.4 }}>Super administrators have unrestricted access across the entire platform. Permissions cannot be customized.</p>
                        </div>
                    </div>
                ) : (
                    <div className={styles.permissionsSection} style={{ marginTop: '1.25rem', borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '1rem' }}>
                        <label className={styles.formLabel} style={{ marginBottom: '0.6rem' }}>Admin Permissions</label>
                        <div className={styles.permGrid}>
                            {/* God Mode Override Banner — shown in edit drawer when operator is
                             super_admin and the target is a plain Facilitator */}
                        {isElevatedOperator && form.role === 'facilitator' && (
                            <div style={{
                                gridColumn: '1 / -1',
                                display: 'flex', alignItems: 'flex-start', gap: '10px',
                                padding: '10px 14px',
                                borderRadius: '8px',
                                background: 'rgba(245,158,11,0.08)',
                                border: '1px solid rgba(245,158,11,0.3)',
                                marginBottom: '4px',
                            }}>
                                <span style={{ fontSize: '1rem', flexShrink: 0 }}>👑</span>
                                <div>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b', display: 'block' }}>
                                        God Mode Override Active
                                    </span>
                                    <span style={{ fontSize: '0.68rem', color: '#94a3b8', lineHeight: 1.4 }}>
                                        All permissions are individually editable for this Facilitator.
                                        Role-based locking is suspended for Super Administrators.
                                    </span>
                                </div>
                            </div>
                        )}

                        {[
                                { key: 'can_create_cohorts', label: 'Create Cohorts', icon: '🚀' },
                                { key: 'can_undo_rounds', label: 'Undo Rounds', icon: '↩️' },
                                { key: 'can_override_decisions', label: 'Override Decisions', icon: '🔧' },
                                { key: 'can_modify_materiality', label: 'Modify Materiality', icon: '📊' },
                                { key: 'can_manage_auto_pause', label: 'Manage Auto-Pause', icon: '⏸️' },
                                { key: 'can_enable_side_tracks', label: 'Enable Side Tracks', icon: '🛤️' },
                            ].map(perm => {
                                // Elevated operators (super_admin) can set any permission on any
                                // facilitatee regardless of role. Otherwise, plain Facilitator
                                // role locks all permissions to their role defaults.
                                const isEditable = isElevatedOperator || form.role !== 'facilitator';
                                return (
                                    <div
                                        key={perm.key}
                                        className={`${styles.permCard} ${form.permissions[perm.key] ? styles.permCardActive : ''}`}
                                        onClick={() => {
                                            if (isEditable) {
                                                updatePermission(perm.key, !form.permissions[perm.key]);
                                            }
                                        }}
                                        style={{
                                            opacity: !isEditable ? 0.5 : 1,
                                            cursor: !isEditable ? 'not-allowed' : 'pointer',
                                            // Subtle amber glow on god-mode-unlocked cards for a facilitator
                                            ...(isElevatedOperator && form.role === 'facilitator' ? {
                                                borderColor: 'rgba(245,158,11,0.25)',
                                            } : {}),
                                        }}
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
                                );
                            })}
                        </div>
                    </div>
                )}

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
                <button className={styles.bulkDownloadBtn} style={{ marginLeft: 8 }} onClick={() => {
                    window.open(`${API}/api/admin/facilitators/bulk-upload/template`, '_blank');
                }}>
                    ⬇️ Download Template Excel
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
                    accept=".csv,.txt,.xlsx"
                    style={{ display: 'none' }}
                    onChange={e => handleFileSelect(e.target.files[0])}
                />
                <span className={styles.dropzoneIcon}>{isDragOver ? '📥' : '📄'}</span>
                <p className={styles.dropzoneText}>
                    {isDragOver ? 'Drop your file here' : 'Drag & drop a CSV file here, or click to browse'}
                </p>
                <span className={styles.dropzoneHint}>Supports .csv, .txt and Excel (.xlsx) — Excel rows are created immediately with per-row results</span>
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
                                <th style={{ width: 40 }} />{/* toggle */}
                                <th onClick={() => toggleSort('name')} className={styles.sortable}>
                                    Facilitator <SortIcon col="name" />
                                </th>
                                <th onClick={() => toggleSort('role')} className={styles.sortable}>
                                    Role <SortIcon col="role" />
                                </th>
                                <th onClick={() => toggleSort('created_at')} className={styles.sortable}>
                                    Date Created <SortIcon col="created_at" />
                                </th>
                                <th>Key Details</th>
                                <th style={{ textAlign: 'right' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((fac) => {
                                const created = fac.cohorts_created || 0;
                                const max = fac.max_cohorts ?? 5;
                                const pct = getUsagePct(created, max);
                                const barColor = getUsageColor(pct);
                                const paradigm = PARADIGM_LABELS[fac.decision_paradigm] || null;
                                const createdDate = formatCreatedDate(fac.created_at);
                                const isVisExpanded = expandedVisRow === fac.facilitator_id;
                                // player visibility defaults
                                const vis = fac.player_visibility || {};

                                return (
                                    <Fragment key={fac.facilitator_id}>
                                    <tr className={fac.enabled === false ? styles.rowDisabled : ''}>
                                        {/* Enable/Disable toggle */}
                                        <td style={{ paddingRight: 0 }}>
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
                                        </td>
                                        {/* Facilitator Name & ID */}
                                        <td>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                                <span className={styles.facName}>{fac.name}</span>
                                                <code className={styles.facId} style={{ opacity: fac.enabled === false ? 0.5 : 1, fontSize: '0.7rem' }}>
                                                    {fac.facilitator_id}
                                                </code>
                                            </div>
                                        </td>
                                        {/* Role */}
                                        <td>
                                            <select
                                                value={fac.role || (fac.is_admin ? 'super_admin' : 'facilitator')}
                                                onChange={(e) => {
                                                    const newRole = e.target.value;
                                                    const currentRole = fac.role || (fac.is_admin ? 'super_admin' : 'facilitator');
                                                    if (newRole !== currentRole) {
                                                        openRoleChangeModal(fac.facilitator_id, fac.name, newRole, currentRole);
                                                        e.target.value = currentRole;
                                                    }
                                                }}
                                                style={{
                                                    fontSize: '0.75rem', padding: '4px 8px', borderRadius: '6px',
                                                    border: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)',
                                                    color: 'var(--text-primary)', cursor: 'pointer', outline: 'none'
                                                }}
                                                title="Change facilitator role"
                                            >
                                                <option value="facilitator">🎓 Facilitator</option>
                                                <option value="lead_facilitator">⭐ Lead</option>
                                                <option value="super_admin">👑 Super Admin</option>
                                            </select>
                                        </td>
                                        {/* Date Created */}
                                        <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                                <span>{createdDate.display}</span>
                                                {createdDate.relative && (
                                                    <span style={{ fontSize: '0.68rem', opacity: 0.7 }}>{createdDate.relative}</span>
                                                )}
                                            </div>
                                        </td>
                                        {/* Key Details */}
                                        <td>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.75rem' }}>
                                                {fac.programme ? (
                                                    <span className={styles.programmeBadge} style={{ width: 'fit-content' }}>{fac.programme}</span>
                                                ) : <span style={{ color: 'var(--text-muted)' }}>No Programme</span>}
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)' }}>
                                                    <span>Cohorts: <strong style={{ color: barColor }}>{created}</strong>/{max}</span>
                                                    {fac.email && <span title={fac.email}>• ✉️ {fac.email}</span>}
                                                </div>
                                            </div>
                                        </td>

                                        {/* Actions */}
                                        <td>
                                            <div style={{ display: 'flex', gap: '4px', justifyContent: 'flex-end', alignItems: 'center', flexWrap: 'wrap' }}>
                                                <button className={styles.actionBtn} onClick={() => openEditDrawer(fac)} title="Edit facilitator">✏️</button>
                                                {onNavigate && (
                                                    <button className={styles.actionBtn} onClick={() => onNavigate('cohort_manager')} title="View cohorts">🗂️</button>
                                                )}
                                                {/* Open as Facilitator deep-link */}
                                                <button
                                                    className={styles.actionBtn}
                                                    onClick={() => window.open(`/admin/facilitator`, '_blank')}
                                                    title={`Open Facilitator dashboard for ${fac.name}`}
                                                    style={{ color: '#60a5fa', borderColor: 'rgba(59,130,246,0.3)' }}
                                                >🔗</button>
                                                {/* ── Cohort Creation button ───────────────────────────────
                                                 *  Elevated operators (super_admin / God Mode) always see a
                                                 *  live 🚀 button plus an inline toggle pill to flip
                                                 *  can_create_cohorts without opening the edit drawer.
                                                 *  Non-elevated operators see the original behaviour.
                                                 * ──────────────────────────────────────────────────────── */}
                                                {isElevatedOperator ? (
                                                    <>
                                                        {/* Inline can_create_cohorts toggle pill */}
                                                        <button
                                                            onClick={() => toggleCohortCreationPermission(fac)}
                                                            title={
                                                                fac.permissions?.can_create_cohorts !== false
                                                                    ? `Disable cohort creation for ${fac.name}`
                                                                    : `Enable cohort creation for ${fac.name}`
                                                            }
                                                            style={{
                                                                display: 'inline-flex',
                                                                alignItems: 'center',
                                                                gap: '4px',
                                                                padding: '2px 8px',
                                                                borderRadius: '20px',
                                                                border: fac.permissions?.can_create_cohorts !== false
                                                                    ? '1px solid rgba(16,185,129,0.4)'
                                                                    : '1px solid rgba(245,158,11,0.4)',
                                                                background: fac.permissions?.can_create_cohorts !== false
                                                                    ? 'rgba(16,185,129,0.1)'
                                                                    : 'rgba(245,158,11,0.08)',
                                                                color: fac.permissions?.can_create_cohorts !== false
                                                                    ? '#34d399'
                                                                    : '#f59e0b',
                                                                fontSize: '0.6rem',
                                                                fontWeight: 700,
                                                                letterSpacing: '0.04em',
                                                                cursor: 'pointer',
                                                                textTransform: 'uppercase',
                                                                transition: 'all 0.15s ease',
                                                                flexShrink: 0,
                                                            }}
                                                        >
                                                            {/* Toggle track */}
                                                            <span style={{
                                                                position: 'relative',
                                                                display: 'inline-block',
                                                                width: '22px',
                                                                height: '12px',
                                                                borderRadius: '6px',
                                                                background: fac.permissions?.can_create_cohorts !== false
                                                                    ? '#10b981'
                                                                    : '#f59e0b',
                                                                transition: 'background 0.2s',
                                                                flexShrink: 0,
                                                            }}>
                                                                <span style={{
                                                                    position: 'absolute',
                                                                    top: '2px',
                                                                    left: fac.permissions?.can_create_cohorts !== false ? '12px' : '2px',
                                                                    width: '8px',
                                                                    height: '8px',
                                                                    borderRadius: '50%',
                                                                    background: '#fff',
                                                                    transition: 'left 0.2s',
                                                                }} />
                                                            </span>
                                                            Cohorts
                                                        </button>

                                                        {/* 🚀 always clickable for God Mode operators */}
                                                        <button
                                                            className={styles.actionBtn}
                                                            onClick={() => handleOpenNewCohort(fac.facilitator_id)}
                                                            title={
                                                                fac.permissions?.can_create_cohorts !== false
                                                                    ? `Set up a new cohort for ${fac.name}`
                                                                    : `God Mode override — create cohort for ${fac.name} (permission is off)`
                                                            }
                                                            style={{
                                                                color: fac.permissions?.can_create_cohorts !== false
                                                                    ? '#34d399'
                                                                    : '#f59e0b',
                                                                borderColor: fac.permissions?.can_create_cohorts !== false
                                                                    ? 'rgba(16,185,129,0.3)'
                                                                    : 'rgba(245,158,11,0.35)',
                                                            }}
                                                        >
                                                            🚀
                                                        </button>
                                                    </>
                                                ) : fac.permissions?.can_create_cohorts !== false ? (
                                                    <button
                                                        className={styles.actionBtn}
                                                        onClick={() => handleOpenNewCohort(fac.facilitator_id)}
                                                        title={`Set up a new cohort for ${fac.name}`}
                                                        style={{ color: '#34d399', borderColor: 'rgba(16,185,129,0.3)' }}
                                                    >
                                                        🚀
                                                    </button>
                                                ) : (
                                                    <button
                                                        className={styles.actionBtn}
                                                        disabled
                                                        title="Cohort creation disabled for this facilitator"
                                                        style={{ color: '#475569', borderColor: 'rgba(71,85,105,0.2)', cursor: 'not-allowed', opacity: 0.4 }}
                                                    >
                                                        🚀
                                                    </button>
                                                )}
                                                <button className={styles.actionBtn} onClick={() => handleResetPassword(fac.facilitator_id)} title="Reset password">🔑</button>
                                                <button
                                                    className={styles.deleteBtn}
                                                    onClick={() => handleDeleteClick(fac.facilitator_id, fac.name)}
                                                    title="Delete facilitator"
                                                >
                                                    🗑️
                                                </button>
                                            </div>
                                        </td>
                                    </tr>

                                    </Fragment>
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

                    <div className={`${styles.drawer} ${(drawerMode === 'bulk' || drawerMode === 'edit' || (drawerMode === 'create' && step >= 3)) ? styles.drawerWide : ''}`}>
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

            {/* ── Delete Confirmation Modal ── */}
            {deleteModal && (
                <>
                    <div
                        onClick={() => setDeleteModal(null)}
                        style={{
                            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
                            zIndex: 9998, backdropFilter: 'blur(4px)',
                        }}
                    />
                    <div style={{
                        position: 'fixed', top: '50%', left: '50%',
                        transform: 'translate(-50%,-50%)',
                        zIndex: 9999,
                        background: 'var(--bg-card, #1e293b)',
                        border: '1px solid rgba(239,68,68,0.35)',
                        borderRadius: 14,
                        padding: '28px 32px',
                        width: 400,
                        boxShadow: '0 24px 60px rgba(0,0,0,0.5)',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                            <span style={{ fontSize: '1.6rem' }}>⚠️</span>
                            <div>
                                <div style={{ fontWeight: 800, fontSize: '1rem', color: '#ef4444' }}>Delete Facilitator</div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>This action cannot be undone.</div>
                            </div>
                        </div>
                        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 18 }}>
                            You are about to permanently delete <strong style={{ color: 'var(--text-primary)' }}>{deleteModal.facName}</strong> ({deleteModal.facId}) and all their associated data.
                        </p>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 8 }}>
                            Type <code style={{ background: 'rgba(239,68,68,0.1)', padding: '1px 6px', borderRadius: 4, color: '#f87171', fontWeight: 700 }}>{deleteModal.facId}</code> to confirm:
                        </p>
                        <input
                            autoFocus
                            value={deleteConfirmInput}
                            onChange={e => setDeleteConfirmInput(e.target.value)}
                            placeholder={deleteModal.facId}
                            onKeyDown={e => { if (e.key === 'Enter' && deleteConfirmInput === deleteModal.facId) handleDelete(deleteModal.facId); }}
                            style={{
                                width: '100%', padding: '9px 12px', borderRadius: 8,
                                border: deleteConfirmInput === deleteModal.facId ? '1.5px solid #ef4444' : '1px solid var(--border-subtle)',
                                background: 'var(--bg-elevated)', color: 'var(--text-primary)',
                                fontFamily: 'var(--font-mono)', fontSize: '0.9rem',
                                outline: 'none', transition: 'border 0.15s',
                                marginBottom: 18,
                                boxSizing: 'border-box',
                            }}
                        />
                        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                            <button
                                onClick={() => setDeleteModal(null)}
                                style={{
                                    padding: '8px 18px', borderRadius: 8, border: '1px solid var(--border-subtle)',
                                    background: 'transparent', color: 'var(--text-secondary)',
                                    cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600,
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                disabled={deleteConfirmInput !== deleteModal.facId}
                                onClick={() => handleDelete(deleteModal.facId)}
                                style={{
                                    padding: '8px 18px', borderRadius: 8, border: 'none',
                                    background: deleteConfirmInput === deleteModal.facId ? '#ef4444' : 'rgba(239,68,68,0.2)',
                                    color: deleteConfirmInput === deleteModal.facId ? '#fff' : 'rgba(239,68,68,0.4)',
                                    cursor: deleteConfirmInput === deleteModal.facId ? 'pointer' : 'not-allowed',
                                    fontSize: '0.82rem', fontWeight: 700, transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                }}
                            >
                                Delete Permanently
                            </button>
                        </div>
                    </div>
                </>
            )}

            {/* ── Role Change Verification Modal ── */}
            {roleChangeModal && (
                <>
                    <div
                        onClick={closeRoleChangeModal}
                        style={{
                            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
                            zIndex: 9998, backdropFilter: 'blur(4px)',
                        }}
                    />
                    <div style={{
                        position: 'fixed', top: '50%', left: '50%',
                        transform: 'translate(-50%,-50%)',
                        zIndex: 9999,
                        background: 'var(--bg-card, #1e293b)',
                        border: '1px solid rgba(245,158,11,0.35)',
                        borderRadius: 14,
                        padding: '28px 32px',
                        width: 420,
                        boxShadow: '0 24px 60px rgba(0,0,0,0.5)',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                            <span style={{ fontSize: '1.6rem' }}>👑</span>
                            <div>
                                <div style={{ fontWeight: 800, fontSize: '1rem', color: '#f59e0b' }}>God Mode Verification</div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>Role changes require Super Administrator credentials.</div>
                            </div>
                        </div>

                        <div style={{
                            padding: '12px 14px', borderRadius: 8, marginBottom: 16,
                            background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)',
                        }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4 }}>Requested change:</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                                <span style={{ color: 'var(--text-muted)' }}>{roleChangeModal.facName}</span>
                                {' '}
                                <span style={{ color: '#94a3b8' }}>→</span>
                                {' '}
                                <span style={{
                                    color: roleChangeModal.newRole === 'super_admin' ? '#f59e0b'
                                        : roleChangeModal.newRole === 'lead_facilitator' ? '#6366f1'
                                        : '#22c55e',
                                    fontWeight: 700,
                                }}>
                                    {roleChangeModal.newRole === 'super_admin' ? '👑 Super Admin'
                                        : roleChangeModal.newRole === 'lead_facilitator' ? '⭐ Lead Facilitator'
                                        : '🎓 Facilitator'}
                                </span>
                            </div>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: 16 }}>
                            <div>
                                <label style={{
                                    display: 'block', fontSize: '0.7rem', fontWeight: 700,
                                    textTransform: 'uppercase', letterSpacing: '0.1em',
                                    color: 'var(--text-muted)', marginBottom: '0.35rem',
                                }}>God Mode Facilitator ID</label>
                                <input
                                    autoFocus
                                    value={roleVerifyFacId}
                                    onChange={e => setRoleVerifyFacId(e.target.value)}
                                    placeholder="e.g. FAC-001"
                                    onKeyDown={e => { if (e.key === 'Enter') document.getElementById('role-verify-pw')?.focus(); }}
                                    disabled={roleVerifyLoading}
                                    style={{
                                        width: '100%', padding: '9px 12px', borderRadius: 8,
                                        border: '1px solid var(--border-subtle)',
                                        background: 'var(--bg-elevated)', color: 'var(--text-primary)',
                                        fontFamily: 'var(--font-mono)', fontSize: '0.88rem',
                                        outline: 'none', transition: 'border 0.15s',
                                        boxSizing: 'border-box',
                                    }}
                                />
                            </div>
                            <div>
                                <label style={{
                                    display: 'block', fontSize: '0.7rem', fontWeight: 700,
                                    textTransform: 'uppercase', letterSpacing: '0.1em',
                                    color: 'var(--text-muted)', marginBottom: '0.35rem',
                                }}>Password</label>
                                <PasswordInput
                                    id="role-verify-pw"
                                    value={roleVerifyPassword}
                                    onChange={e => setRoleVerifyPassword(e.target.value)}
                                    placeholder="Enter God Mode password"
                                    onKeyDown={e => { if (e.key === 'Enter' && roleVerifyFacId.trim() && roleVerifyPassword.trim()) handleRoleChangeVerified(); }}
                                    disabled={roleVerifyLoading}
                                    style={{
                                        width: '100%', padding: '9px 12px', borderRadius: 8,
                                        border: '1px solid var(--border-subtle)',
                                        background: 'var(--bg-elevated)', color: 'var(--text-primary)',
                                        fontSize: '0.88rem',
                                        outline: 'none', transition: 'border 0.15s',
                                        boxSizing: 'border-box',
                                    }}
                                />
                            </div>
                        </div>

                        {roleVerifyError && (
                            <div style={{
                                padding: '8px 12px', borderRadius: 8, marginBottom: 14,
                                background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)',
                                color: '#ef4444', fontSize: '0.8rem', fontWeight: 600,
                            }}>{roleVerifyError}</div>
                        )}

                        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                            <button
                                onClick={closeRoleChangeModal}
                                disabled={roleVerifyLoading}
                                style={{
                                    padding: '8px 18px', borderRadius: 8, border: '1px solid var(--border-subtle)',
                                    background: 'transparent', color: 'var(--text-secondary)',
                                    cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600,
                                }}
                            >Cancel</button>
                            <button
                                onClick={handleRoleChangeVerified}
                                disabled={roleVerifyLoading || !roleVerifyFacId.trim() || !roleVerifyPassword.trim()}
                                style={{
                                    padding: '8px 18px', borderRadius: 8, border: 'none',
                                    background: (roleVerifyFacId.trim() && roleVerifyPassword.trim() && !roleVerifyLoading)
                                        ? 'linear-gradient(135deg, #f59e0b, #ef4444)' : 'rgba(245,158,11,0.2)',
                                    color: (roleVerifyFacId.trim() && roleVerifyPassword.trim() && !roleVerifyLoading)
                                        ? '#fff' : 'rgba(245,158,11,0.4)',
                                    cursor: (roleVerifyFacId.trim() && roleVerifyPassword.trim() && !roleVerifyLoading)
                                        ? 'pointer' : 'not-allowed',
                                    fontSize: '0.82rem', fontWeight: 700, transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                    boxShadow: (roleVerifyFacId.trim() && roleVerifyPassword.trim() && !roleVerifyLoading)
                                        ? '0 4px 16px rgba(245,158,11,0.3)' : 'none',
                                }}
                            >
                                {roleVerifyLoading ? '⏳ Verifying…' : '👑 Verify & Apply'}
                            </button>
                        </div>
                    </div>
                </>
            )}

            {/* ── Toast ── */}
            {toast && (() => {
                const isPasswordToast = toast.persistent && typeof toast.msg === 'object' && toast.msg?.password;
                if (isPasswordToast) {
                    const { password, emailSent, emailTo, facId } = toast.msg;
                    return (
                        <div
                            className={styles.toast}
                            style={{
                                paddingRight: '2.2rem',
                                display: 'flex', flexDirection: 'column', gap: '6px',
                                minWidth: '280px', maxWidth: '380px',
                            }}
                        >
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                                <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>
                                    🔐 New password {facId ? `for ${facId}` : ''}
                                </span>
                                <button
                                    onClick={(e) => { e.stopPropagation(); setToast(null); }}
                                    style={{
                                        background: 'none', border: 'none', color: '#64748b',
                                        cursor: 'pointer', fontSize: '1rem', lineHeight: 1, padding: '0 2px',
                                    }}
                                    title="Dismiss"
                                >×</button>
                            </div>
                            <div style={{
                                display: 'flex', alignItems: 'center', gap: '8px',
                                background: 'rgba(15,23,42,0.6)',
                                border: '1px solid rgba(34,197,94,0.25)',
                                borderRadius: '8px', padding: '8px 12px',
                            }}>
                                <code
                                    onClick={async (e) => {
                                        e.stopPropagation();
                                        try {
                                            await navigator.clipboard.writeText(password);
                                            setPwCopied(true);
                                            setTimeout(() => setPwCopied(false), 2500);
                                        } catch { /* fallback: user can still select text */ }
                                    }}
                                    style={{
                                        flex: 1,
                                        fontFamily: "'Courier New', monospace",
                                        fontSize: '1rem', fontWeight: 700, letterSpacing: '0.08em',
                                        color: '#22c55e',
                                        cursor: 'pointer',
                                        userSelect: 'all',
                                    }}
                                    title="Click to copy"
                                >{password}</code>
                                <button
                                    onClick={async (e) => {
                                        e.stopPropagation();
                                        try {
                                            await navigator.clipboard.writeText(password);
                                            setPwCopied(true);
                                            setTimeout(() => setPwCopied(false), 2500);
                                        } catch {}
                                    }}
                                    style={{
                                        background: pwCopied ? 'rgba(34,197,94,0.15)' : 'rgba(99,102,241,0.12)',
                                        border: pwCopied ? '1px solid rgba(34,197,94,0.3)' : '1px solid rgba(99,102,241,0.25)',
                                        borderRadius: '6px', padding: '4px 10px',
                                        color: pwCopied ? '#22c55e' : '#818cf8',
                                        fontSize: '0.7rem', fontWeight: 700, cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        whiteSpace: 'nowrap',
                                    }}
                                    title="Copy to clipboard"
                                >{pwCopied ? '✅ Copied!' : '📋 Copy'}</button>
                            </div>
                            {emailSent !== undefined && (
                                <div style={{
                                    fontSize: '0.68rem', color: emailSent ? '#22c55e' : '#f59e0b',
                                    fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px',
                                }}>
                                    {emailSent
                                        ? <>✉️ Email sent to {emailTo || 'facilitator'}</>
                                        : <>⚠️ {emailTo ? `No SMTP configured — email not sent to ${emailTo}` : 'No email on file — password not emailed'}</>
                                    }
                                </div>
                            )}
                        </div>
                    );
                }
                // Regular string toast
                return (
                    <div
                        className={`${styles.toast} ${toast.type === 'error' ? styles.toastError : ''}`}
                        style={toast.persistent ? { cursor: 'pointer', paddingRight: '2rem', userSelect: 'all' } : undefined}
                        onClick={toast.persistent ? () => setToast(null) : undefined}
                        title={toast.persistent ? 'Click to dismiss' : undefined}
                    >
                        {toast.msg}
                        {toast.persistent && (
                            <span style={{
                                position: 'absolute', top: '50%', right: '10px',
                                transform: 'translateY(-50%)',
                                fontSize: '0.9rem', opacity: 0.6, lineHeight: 1,
                            }}>×</span>
                        )}
                    </div>
                );
            })()}

            {/* ── Set Up New Cohort Modal ─────────────────────────── */}
            {showCohortModal && (
                <CreateCohortModal
                    isOpen={true}
                    currentFacilitatorId={cohortFacilitatorId}
                    currentFacilitatorRole="super_admin"
                    onClose={() => setShowCohortModal(false)}
                    onCreated={() => {
                        setShowCohortModal(false);
                        showToast('Cohort created successfully! 🚀', 'success');
                        // Refresh facilitator list to pick up updated cohorts_created count
                        fetchFacilitators?.();
                    }}
                />
            )}
        </section>
    );
}
