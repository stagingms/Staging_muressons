'use client';

import { useState, useEffect } from 'react';
import styles from './MaterialityConfig.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// ── Excel Import/Export Sub-component ─────────────────────────
function ExcelImportExport({ selectedDict, dictOptions, onUploadSuccess }) {
    const [uploading, setUploading] = useState(false);
    const [dragOver, setDragOver] = useState(false);
    const [result, setResult] = useState(null);  // { status, diff, error }

    const scopeLabel = selectedDict === 'global'
        ? 'Global (Narrative Crisis)'
        : (dictOptions.find(o => o.id === selectedDict)?.label || selectedDict);

    const handleDownload = async () => {
        try {
            const res = await fetch(
                `${API}/api/admin/materiality-config/download?scope=${encodeURIComponent(selectedDict)}`,
                { credentials: 'include' }
            );
            if (!res.ok) {
                let detail = 'Download failed.';
                try { detail = (await res.json()).detail || detail; } catch { /* plain-text body */ }
                console.error('[MatDownload] Server error', res.status, detail);
                alert(detail);
                return;
            }
            // Use a real Blob + object URL but revoke *after* the click event
            // loop tick to avoid CSP issues with immediate revocation.
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `materiality_config_${selectedDict}.xlsx`;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            // Defer revocation — browsers need the URL to persist through the
            // download initiation before it can be safely cleaned up.
            setTimeout(() => {
                a.remove();
                URL.revokeObjectURL(url);
            }, 5000);
        } catch (err) {
            console.error('[MatDownload] Fetch threw:', err);
            alert('Network error downloading Excel file: ' + (err?.message || String(err)));
        }
    };


    const doUpload = async (file) => {
        if (!file) return;
        if (!file.name.toLowerCase().endsWith('.xlsx')) {
            setResult({ error: 'Only .xlsx files are accepted.' });
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            setResult({ error: 'File too large. Maximum 5 MB.' });
            return;
        }
        if (!confirm(`Upload "${file.name}" and REPLACE the ${scopeLabel} materiality dictionary?`)) return;

        setUploading(true);
        setResult(null);
        try {
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch(
                `${API}/api/admin/materiality-config/upload?scope=${encodeURIComponent(selectedDict)}`,
                { method: 'POST', credentials: 'include', body: formData }
            );
            // Parse body — some error responses are plain text, not JSON
            let data = {};
            const ct = res.headers.get('content-type') || '';
            if (ct.includes('application/json')) {
                data = await res.json().catch(() => ({}));
            } else {
                const txt = await res.text().catch(() => '');
                data = { detail: txt || `HTTP ${res.status}` };
            }
            if (res.ok) {
                setResult({ status: 'ok', ...data });
                if (onUploadSuccess) onUploadSuccess(data);
            } else {
                console.error('[MatUpload] Server error', res.status, data);
                setResult({ error: `${res.status}: ${data.detail || 'Upload failed.'}` });
            }
        } catch (err) {
            console.error('[MatUpload] Fetch threw:', err);
            setResult({ error: `Upload error: ${err?.message || String(err)}` });
        }
        setUploading(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer?.files?.[0];
        doUpload(file);
    };

    const handleFileInput = (e) => {
        doUpload(e.target.files?.[0]);
        e.target.value = '';
    };

    const diff = result?.diff;
    const totalChanges = diff ? (diff.added?.length || 0) + (diff.removed?.length || 0) + (diff.modified?.length || 0) : 0;

    return (
        <div style={{
            background: 'var(--bg-card, #fff)', border: '1px solid var(--border-subtle, #e2e8f0)',
            borderRadius: '10px', padding: '1.25rem', marginBottom: '1.25rem',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <div>
                    <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary, #1e293b)' }}>
                        📊 Excel Import / Export
                    </h4>
                    <p style={{ margin: '2px 0 0', fontSize: '0.74rem', color: 'var(--text-muted, #94a3b8)' }}>
                        Scope: <strong>{scopeLabel}</strong> — Two sheets: Issues + Interdependencies
                    </p>
                </div>
                <button
                    onClick={handleDownload}
                    style={{
                        display: 'flex', alignItems: 'center', gap: '6px',
                        background: 'linear-gradient(135deg, #3b82f6, #2563eb)', color: '#fff',
                        border: 'none', padding: '0.45rem 1rem', borderRadius: '8px',
                        fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer',
                        boxShadow: '0 1px 3px rgba(37,99,235,0.25)',
                    }}
                >
                    <span style={{ fontSize: '1rem' }}>⬇</span> Download .xlsx
                </button>
            </div>

            {/* Drop zone */}
            <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => document.getElementById('excelUploadInput')?.click()}
                style={{
                    border: `2px dashed ${dragOver ? '#3b82f6' : 'var(--border-subtle, #cbd5e1)'}`,
                    borderRadius: '8px',
                    background: dragOver ? 'rgba(59,130,246,0.06)' : 'var(--bg-elevated, #f8fafc)',
                    padding: '1.5rem', textAlign: 'center', cursor: 'pointer',
                    transition: 'border-color 0.2s, background 0.2s',
                }}
            >
                <input
                    type="file"
                    id="excelUploadInput"
                    accept=".xlsx"
                    style={{ display: 'none' }}
                    onChange={handleFileInput}
                />
                {uploading ? (
                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#3b82f6', fontWeight: 600 }}>
                        ⏳ Uploading & validating…
                    </p>
                ) : (
                    <>
                        <p style={{ margin: 0, fontSize: '1.4rem' }}>📂</p>
                        <p style={{ margin: '0.3rem 0 0', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary, #475569)' }}>
                            Drag & drop an .xlsx file here, or click to browse
                        </p>
                        <p style={{ margin: '0.2rem 0 0', fontSize: '0.72rem', color: 'var(--text-muted, #94a3b8)' }}>
                            Max 5 MB · Must contain an "Issues" sheet
                        </p>
                    </>
                )}
            </div>

            {/* Result feedback */}
            {result && (
                <div style={{
                    marginTop: '0.75rem', padding: '0.7rem 0.9rem', borderRadius: '8px', fontSize: '0.82rem',
                    ...(result.error
                        ? { background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b' }
                        : { background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }
                    ),
                }}>
                    {result.error ? (
                        <div>
                            <strong>⚠️ Upload Failed</strong>
                            <p style={{ margin: '4px 0 0', whiteSpace: 'pre-wrap' }}>{result.error}</p>
                        </div>
                    ) : (
                        <div>
                            <strong>✅ Upload Successful</strong>
                            <span style={{ marginLeft: '0.5rem', opacity: 0.8 }}>
                                {result.issues_count} issues · {result.interdependencies_count} links · Fee ${(result.consultant_fee_usd || 0).toLocaleString()}
                            </span>
                            {totalChanges > 0 && (
                                <div style={{ marginTop: '0.4rem', display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                                    {diff.added?.length > 0 && (
                                        <span style={{ background: '#dcfce7', padding: '2px 8px', borderRadius: '6px', fontWeight: 600, fontSize: '0.76rem' }}>
                                            +{diff.added.length} added
                                        </span>
                                    )}
                                    {diff.removed?.length > 0 && (
                                        <span style={{ background: '#fee2e2', padding: '2px 8px', borderRadius: '6px', fontWeight: 600, fontSize: '0.76rem' }}>
                                            −{diff.removed.length} removed
                                        </span>
                                    )}
                                    {diff.modified?.length > 0 && (
                                        <span style={{ background: '#fef9c3', padding: '2px 8px', borderRadius: '6px', fontWeight: 600, fontSize: '0.76rem' }}>
                                            ~{diff.modified.length} modified
                                        </span>
                                    )}
                                </div>
                            )}
                            {totalChanges === 0 && (
                                <div style={{ marginTop: '0.3rem', fontSize: '0.76rem', opacity: 0.7 }}>No changes detected (identical config).</div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default function MaterialityConfig({ sessionId, isFacilitator }) {
    const [config, setConfig] = useState({ issues: [], interdependencies: [], consultant_fee_usd: 1500000 });
    const [isSandboxed, setIsSandboxed] = useState(false);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('economic');
    const [showConfigurator, setShowConfigurator] = useState(false);

    // Dictionary selector: loaded dynamically from backend.
    // Only the Global (Narrative Crisis) dictionary is a non-vertical category.
    // Pharma, Electronics, Consumer Goods, and Software are classified as
    // Industry Verticals and appear in the dedicated verticals row below.
    const [selectedDict, setSelectedDict] = useState('global');
    const [dictOptions, setDictOptions] = useState([
        { id: 'global', label: 'Global (Narrative Crisis)', icon: '🌐', is_custom: false },
    ]);
    const [showAddCategory, setShowAddCategory] = useState(false);
    const [newCategory, setNewCategory] = useState({ id: '', label: '', icon: '🏢' });
    const [categoryMsg, setCategoryMsg] = useState('');

    // Industry vertical blueprints (from /api/admin/industry-verticals)
    const [industryVerticals, setIndustryVerticals] = useState([]);
    const [verticalSessions, setVerticalSessions] = useState([]);
    const [applyingVertical, setApplyingVertical] = useState(false);
    const [applyTarget, setApplyTarget] = useState('');
    const [applyMsg, setApplyMsg] = useState('');

    // Load BU categories dynamically from backend
    useEffect(() => {
        fetch(`${API}/api/admin/bu-categories`)
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (data?.categories) {
                    // Exclude industry verticals — they have their own dedicated row
                    const buOpts = data.categories
                        .filter(c => !c.is_industry_vertical)
                        .map(c => ({
                            id: c.id, label: c.label, icon: c.icon, is_custom: c.is_custom || false,
                        }));
                    setDictOptions([
                        { id: 'global', label: 'Global (Narrative Crisis)', icon: '🌐', is_custom: false },
                        ...buOpts,
                    ]);
                }
            })
            .catch(() => {});

        // Load industry vertical blueprints
        fetch(`${API}/api/admin/industry-verticals`)
            .then(r => r.ok ? r.json() : null)
            .then(data => { if (data?.verticals) setIndustryVerticals(data.verticals); })
            .catch(() => {});

        // Load sessions for the vertical-apply dropdown
        fetch(`${API}/api/admin/sessions`)
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (Array.isArray(data)) setVerticalSessions(data);
                else if (data?.sessions) setVerticalSessions(data.sessions);
            })
            .catch(() => {});
    }, []);

    const handleApplyVertical = async () => {
        if (!applyTarget || !selectedDict) return;
        setApplyingVertical(true);
        setApplyMsg('');
        try {
            const res = await fetch(`${API}/api/admin/industry-verticals/${selectedDict}/apply/${applyTarget}`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                setApplyMsg(`✅ Applied to session (${data.issue_count} issues loaded).`);
            } else {
                setApplyMsg(`⚠️ ${data.detail || 'Apply failed'}`);
            }
        } catch {
            setApplyMsg('⚠️ Network error.');
        }
        setApplyingVertical(false);
    };

    const handleAddCategory = async () => {
        const id = newCategory.id.trim().toLowerCase().replace(/\s+/g, '_');
        if (!id || !newCategory.label.trim()) {
            setCategoryMsg('⚠️ ID and Label are required.');
            return;
        }
        try {
            const res = await fetch(`${API}/api/admin/bu-categories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, label: newCategory.label.trim(), icon: newCategory.icon || '🏢' }),
            });
            if (!res.ok) {
                const e = await res.json().catch(() => ({}));
                setCategoryMsg(`⚠️ ${e.detail || 'Failed to add category'}`);
                return;
            }
            setNewCategory({ id: '', label: '', icon: '🏢' });
            setShowAddCategory(false);
            setCategoryMsg('');
            // Reload categories
            const data = await fetch(`${API}/api/admin/bu-categories`).then(r => r.json());
            if (data?.categories) {
                setDictOptions([
                    { id: 'global', label: 'Global (Narrative Crisis)', icon: '🌐', is_custom: false },
                    ...data.categories.map(c => ({ id: c.id, label: c.label, icon: c.icon, is_custom: c.is_custom || false })),
                ]);
                setSelectedDict(id);
            }
        } catch {
            setCategoryMsg('⚠️ Network error adding category.');
        }
    };

    const handleDeleteCategory = async (catId) => {
        if (!confirm(`Remove custom category "${catId}"? Its materiality config will be preserved on disk.`)) return;
        try {
            const res = await fetch(`${API}/api/admin/bu-categories/${catId}`, { method: 'DELETE' });
            if (!res.ok) {
                const e = await res.json().catch(() => ({}));
                alert(e.detail || 'Failed to remove category.');
                return;
            }
            const data = await fetch(`${API}/api/admin/bu-categories`).then(r => r.json());
            if (data?.categories) {
                setDictOptions([
                    { id: 'global', label: 'Global (Narrative Crisis)', icon: '🌐', is_custom: false },
                    ...data.categories.map(c => ({ id: c.id, label: c.label, icon: c.icon, is_custom: c.is_custom || false })),
                ]);
            }
            if (selectedDict === catId) setSelectedDict('global');
        } catch {
            alert('Network error removing category.');
        }
    };

    // Form state for new issue
    const [newIssue, setNewIssue] = useState({
        id: '', title: '', hover_description: '',
        category: 'economic', financial_impact: 'medium', societal_impact: 'medium'
    });

    // Form state for new interdependence link
    const [newLink, setNewLink] = useState({
        source_issue_id: '', target_issue_id: '', severity: 3, description: ''
    });

    const [feeInput, setFeeInput] = useState('');

    useEffect(() => {
        fetchConfig();
    }, [selectedDict]);

    // Build the correct API endpoint based on selectedDict
    const getBaseEndpoint = () => {
        if (selectedDict === 'global') {
            return `${API}/api/admin/materiality-config`;
        }
        return `${API}/api/admin/materiality-config/bu/${selectedDict}`;
    };

    const fetchConfig = async () => {
        setLoading(true);
        try {
            // First, see if the session has an active sandbox override
            let sandboxConfig = null;
            if (sessionId) {
                const sessionRes = await fetch(`${API}/api/simulations/${sessionId}/state`);
                if (sessionRes.ok) {
                    const sessionData = await sessionRes.json();
                    // Check for BU-specific override or global override
                    const overrideKey = selectedDict === 'global'
                        ? 'materiality_dictionary_override'
                        : `materiality_dictionary_override_${selectedDict}`;
                    if (sessionData.global_state?.[overrideKey]) {
                        sandboxConfig = sessionData.global_state[overrideKey];
                        setIsSandboxed(true);
                    }
                }
            }

            // If a sandbox override exists, use it. Otherwise, fetch the God Mode config.
            if (sandboxConfig) {
                setConfig(sandboxConfig);
                setFeeInput(sandboxConfig.consultant_fee_usd?.toString() || "1500000");
            } else {
                const res = await fetch(getBaseEndpoint());
                if (res.ok) {
                    const data = await res.json();
                    setConfig(data);
                    setFeeInput(data.consultant_fee_usd?.toString() || "1500000");
                    setIsSandboxed(false);
                }
            }
        } catch {
            // Silent — backend may be offline during frontend-only development
        }
        setLoading(false);
    };

    const handleToggleSandbox = async () => {
        if (!sessionId) return;

        if (isSandboxed) {
            if (!confirm("Are you sure you want to disable the custom dictionary? This cohort will revert to the global God Mode defaults, and all local changes will be lost.")) return;
            try {
                await fetch(`${API}/api/admin/${sessionId}/materiality-dictionary`, { method: 'DELETE' });
                setIsSandboxed(false);
                fetchConfig(); // Reload from master
            } catch (err) {
                console.error(err);
            }
        } else {
            if (!confirm("Enable Sandbox Mode? This will clone the current global dictionary so you can make local edits just for this cohort.")) return;
            try {
                // The current `config` is the master. Save it as the override.
                await fetch(`${API}/api/admin/${sessionId}/materiality-dictionary`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                setIsSandboxed(true);
            } catch (err) {
                console.error(err);
            }
        }
    };

    const saveUpdatedConfig = async (updatedConfig) => {
        try {
            const isCohortScoped = isSandboxed || (isFacilitator && sessionId);
            const endpoint = isCohortScoped
                ? `${API}/api/admin/${sessionId}/materiality-dictionary`
                : getBaseEndpoint();

            const res = await fetch(endpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedConfig)
            });

            if (res.ok) {
                const data = await res.json();
                if (isCohortScoped) {
                    setConfig(updatedConfig);
                    if (!isSandboxed) setIsSandboxed(true);
                } else {
                    setConfig(data);
                }
                return true;
            } else {
                alert("Failed to save configuration.");
                return false;
            }
        } catch (err) {
            console.error(err);
            alert("Network error while saving.");
            return false;
        }
    };

    // Direct cost edit (Optimistic UI update)
    const handleSaveOverrideCost = async (issueId, newCost) => {
        const updatedIssues = config.issues.map(i => i.id === issueId ? { ...i, mitigation_cost_usd: newCost } : i);
        const updatedConfig = { ...config, issues: updatedIssues };
        setConfig(updatedConfig); // Optimistic wait
        await saveUpdatedConfig(updatedConfig);
    };

    const handleUpdateFee = async () => {
        const fee = parseInt(feeInput, 10);
        if (isNaN(fee)) return;

        const updatedConfig = { ...config, consultant_fee_usd: fee };
        if (await saveUpdatedConfig(updatedConfig)) {
            alert('Consultant Fee Updated!');
        }
    };

    const handleAddIssue = async (e) => {
        e.preventDefault();
        const issueToSubmit = { ...newIssue, category: activeTab };
        if (!issueToSubmit.id) {
            issueToSubmit.id = issueToSubmit.title.toLowerCase().replace(/[^a-z0-9]+/g, '_');
        }

        const updatedConfig = { ...config, issues: [...config.issues, issueToSubmit] };
        if (await saveUpdatedConfig(updatedConfig)) {
            setNewIssue({ id: '', title: '', hover_description: '', category: activeTab, financial_impact: 'medium', societal_impact: 'medium' });
        }
    };

    const handleDeleteIssue = async (id) => {
        if (!confirm(`Are you sure you want to delete issue "${id}"?`)) return;

        const updatedConfig = { ...config, issues: config.issues.filter(i => i.id !== id) };
        await saveUpdatedConfig(updatedConfig);
    };

    const handleAddLink = async (e) => {
        e.preventDefault();
        if (!newLink.source_issue_id || !newLink.target_issue_id || newLink.source_issue_id === newLink.target_issue_id) {
            alert('Please select two distinct issues.');
            return;
        }

        const linkToSubmit = {
            ...newLink,
            id: `${newLink.source_issue_id}_to_${newLink.target_issue_id}_${Date.now()}`
        };

        try {
            // Re-use current config and just append the link
            const updatedConfig = { ...config, interdependencies: [...config.interdependencies, linkToSubmit] };
            const res = await fetch(`${API}/api/admin/materiality-config`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedConfig)
            });
            if (res.ok) {
                const data = await res.json();
                setConfig(data);
                setNewLink({ source_issue_id: '', target_issue_id: '', severity: 3, description: '' });
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleDeleteLink = async (linkId) => {
        try {
            const updatedConfig = { ...config, interdependencies: config.interdependencies.filter(l => l.id !== linkId) };
            const res = await fetch(`${API}/api/admin/materiality-config`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedConfig)
            });
            if (res.ok) {
                const data = await res.json();
                setConfig(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleCSVUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (event) => {
            const text = event.target.result;

            // Basic CSV parser to handle quotes
            const parseCSVLine = (line) => {
                let ret = [], inQuote = false, value = '';
                for (let i = 0; i < line.length; i++) {
                    let char = line[i];
                    if (inQuote) {
                        if (char === '"') {
                            if (i + 1 < line.length && line[i + 1] === '"') { value += '"'; i++; }
                            else { inQuote = false; }
                        } else { value += char; }
                    } else {
                        if (char === '"') { inQuote = true; }
                        else if (char === ',') { ret.push(value); value = ''; }
                        else { value += char; }
                    }
                }
                ret.push(value);
                return ret;
            };

            const lines = text.split('\n').map(l => l.trim()).filter(l => l);
            if (lines.length < 2) return alert('CSV must have a header row and at least one data row.');

            // Normalize headers
            const normalizeHeader = (h) => {
                const lower = h.trim().toLowerCase();
                if (lower === 'interdependency 1') return 'interdependency_1';
                if (lower === 'interdependency 2') return 'interdependency_2';
                if (lower === 'other affected bu1') return 'affected_bu_1';
                if (lower === 'other affected bu2') return 'affected_bu_2';
                return lower;
            };
            const headers = parseCSVLine(lines[0]).map(normalizeHeader);

            const required = ['title', 'category'];
            if (required.some(r => !headers.includes(r))) {
                return alert(`Missing headers. Your CSV must at least have: ${required.join(', ')}`);
            }

            const newIssues = [];
            for (let i = 1; i < lines.length; i++) {
                const parsed = parseCSVLine(lines[i]);
                if (parsed.length < headers.length) continue;

                const issue = {
                    financial_impact: "medium", // Fallbacks if user omitted them in new schema
                    societal_impact: "medium",
                    hover_description: "Added via CSV upload"
                };
                headers.forEach((h, idx) => {
                    if (parsed[idx]) issue[h] = parsed[idx].trim();
                });

                if (!issue.title) continue;
                if (!issue.id) {
                    issue.id = issue.title.toLowerCase().replace(/[^a-z0-9]+/g, '_');
                }

                // Parse the mitigation cost specifically
                issue.mitigation_cost_usd = parseInt(issue.mitigation_cost_usd, 10);
                if (isNaN(issue.mitigation_cost_usd)) issue.mitigation_cost_usd = 0;

                newIssues.push(issue);
            }

            if (!confirm(`Found ${newIssues.length} issues. This will REPLACE your entire existing dictionary. Proceed?`)) return;

            const updatedConfig = { ...config, issues: newIssues, interdependencies: [] };

            try {
                const res = await fetch(`${API}/api/admin/materiality-config`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedConfig)
                });
                if (res.ok) {
                    const data = await res.json();
                    setConfig(data);
                    alert(`Successfully imported and replaced dictionary with ${newIssues.length} issues!`);
                } else {
                    alert("Failed to save imported issues via API.");
                }
            } catch (err) {
                console.error(err);
                alert("Network error while importing issues.");
            }
        };
        reader.readAsText(file);
        // reset input so the same file can be uploaded again if needed
        e.target.value = '';
    };

    const handleInterdependenciesCSVUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (event) => {
            const text = event.target.result;

            const parseCSVLine = (line) => {
                let ret = [], inQuote = false, value = '';
                for (let i = 0; i < line.length; i++) {
                    let char = line[i];
                    if (inQuote) {
                        if (char === '"') {
                            if (i + 1 < line.length && line[i + 1] === '"') { value += '"'; i++; }
                            else { inQuote = false; }
                        } else { value += char; }
                    } else {
                        if (char === '"') { inQuote = true; }
                        else if (char === ',') { ret.push(value); value = ''; }
                        else { value += char; }
                    }
                }
                ret.push(value);
                return ret;
            };

            const lines = text.split('\n').map(l => l.trim()).filter(l => l);
            if (lines.length < 2) return alert('CSV must have a header row and at least one data row.');

            const headers = parseCSVLine(lines[0]).map(h => h.trim().toLowerCase());
            const required = ['source_issue_id', 'target_issue_id', 'severity', 'description'];
            if (required.some(r => !headers.includes(r))) {
                return alert(`Missing headers. Your CSV must have: ${required.join(', ')}`);
            }

            const newLinks = [];
            for (let i = 1; i < lines.length; i++) {
                const parsed = parseCSVLine(lines[i]);
                if (parsed.length < headers.length) continue;

                const link = {};
                headers.forEach((h, idx) => {
                    if (parsed[idx]) link[h] = parsed[idx].trim();
                });

                if (!link.source_issue_id || !link.target_issue_id) continue;

                link.severity = parseInt(link.severity, 10);
                if (isNaN(link.severity) || link.severity < 1 || link.severity > 5) link.severity = 3;

                link.id = `${link.source_issue_id}_to_${link.target_issue_id}_${Date.now()}_${i}`;
                newLinks.push(link);
            }

            if (!confirm(`Found ${newLinks.length} interdependencies. This will REPLACE your existing links. Proceed?`)) return;

            const updatedConfig = { ...config, interdependencies: newLinks };

            try {
                const res = await fetch(`${API}/api/admin/materiality-config`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedConfig)
                });
                if (res.ok) {
                    const data = await res.json();
                    setConfig(data);
                    alert(`Successfully imported and replaced ${newLinks.length} interdependencies!`);
                } else {
                    alert("Failed to save imported links via API.");
                }
            } catch (err) {
                console.error(err);
                alert("Network error while importing links.");
            }
        };
        reader.readAsText(file);
        e.target.value = '';
    };

    if (loading) return <div>Loading configuration...</div>;

    const filteredIssues = config.issues.filter(i => i.category === activeTab);

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div>
                    <h2>🧩 Materiality Matrix</h2>
                    <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: 'var(--text-muted,#94a3b8)', fontWeight: 400 }}>
                        Issue dictionaries, interdependencies & consultant fee configuration
                    </p>
                </div>
                <span style={{
                    fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.1em',
                    textTransform: 'uppercase', padding: '4px 10px', borderRadius: '6px',
                    background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)',
                    color: '#60a5fa', fontFamily: 'var(--font-mono,monospace)',
                }}>
                    {config.issues.length} Issues · {config.interdependencies.length} Links
                </span>
            </div>

            {/* Dictionary Selector */}
            <div style={{ borderBottom: '1px solid var(--border-subtle)', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', gap: '6px', padding: '0.75rem 0', flexWrap: 'wrap', alignItems: 'center' }}>
                    {dictOptions.map(opt => (
                        <div key={opt.id} style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
                            <button
                                onClick={() => { setSelectedDict(opt.id); setShowConfigurator(false); }}
                                style={{
                                    padding: '6px 14px', borderRadius: opt.is_custom ? '20px 0 0 20px' : '20px', cursor: 'pointer',
                                    fontSize: '0.78rem', fontWeight: 600, 
                                    borderWidth: '1.5px', borderStyle: 'solid',
                                    transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                    background: selectedDict === opt.id ? 'var(--accent-blue, #3b82f6)' : 'transparent',
                                    color: selectedDict === opt.id ? '#fff' : 'var(--text-primary, #334155)',
                                    borderColor: selectedDict === opt.id ? 'var(--accent-blue, #3b82f6)' : 'var(--border-subtle, #d1d5db)',
                                    borderRightWidth: opt.is_custom ? '0' : '1.5px',
                                }}
                            >
                                {opt.icon} {opt.label}
                            </button>
                            {opt.is_custom && !isFacilitator && (
                                <button
                                    onClick={() => handleDeleteCategory(opt.id)}
                                    title={`Remove "${opt.label}" category`}
                                    style={{
                                        padding: '6px 8px', borderRadius: '0 20px 20px 0', cursor: 'pointer',
                                        fontSize: '0.7rem', fontWeight: 700, 
                                        borderWidth: '1.5px', borderStyle: 'solid', borderLeftWidth: '0',
                                        transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                        background: selectedDict === opt.id ? '#dc2626' : 'transparent',
                                        color: selectedDict === opt.id ? '#fff' : '#ef4444',
                                        borderColor: selectedDict === opt.id ? '#dc2626' : 'var(--border-subtle, #d1d5db)',
                                    }}
                                >✕</button>
                            )}
                        </div>
                    ))}

                {/* ── Industry Vertical Blueprints row ──────────────────── */}
                {industryVerticals.length > 0 && (
                    <>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem', width: '100%' }}>
                            <span style={{
                                fontSize: '0.68rem', fontWeight: 800, letterSpacing: '0.1em',
                                textTransform: 'uppercase', color: '#6366f1', whiteSpace: 'nowrap',
                            }}>★ Industry Verticals</span>
                            <div style={{ flex: 1, height: 1, background: 'rgba(99,102,241,0.25)' }} />
                        </div>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', paddingTop: '2px' }}>
                            {industryVerticals.map(v => (
                                <button
                                    key={v.id}
                                    onClick={() => { setSelectedDict(v.id); setShowConfigurator(false); setApplyMsg(''); }}
                                    title={`Q1 issues: ${v.q1_titles?.join(', ') || 'none'}`}
                                    style={{
                                        padding: '6px 14px', borderRadius: '20px', cursor: 'pointer',
                                        fontSize: '0.78rem', fontWeight: 700,
                                        borderWidth: '1.5px', borderStyle: 'solid',
                                        transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                        background: selectedDict === v.id ? '#6366f1' : 'rgba(99,102,241,0.08)',
                                        color: selectedDict === v.id ? '#fff' : '#6366f1',
                                        borderColor: selectedDict === v.id ? '#6366f1' : 'rgba(99,102,241,0.35)',
                                    }}
                                >
                                    {v.icon} {v.label}
                                    {v.q1_count > 0 && (
                                        <span style={{
                                            marginLeft: '0.4rem', fontSize: '0.68rem', fontWeight: 800,
                                            background: selectedDict === v.id ? 'rgba(255,255,255,0.25)' : 'rgba(99,102,241,0.15)',
                                            padding: '1px 5px', borderRadius: '10px',
                                        }}>{v.q1_count} Q1</span>
                                    )}
                                </button>
                            ))}
                        </div>
                    </>
                )}

                    {/* Add Category Button */}
                    <button
                        onClick={() => { setShowAddCategory(!showAddCategory); setCategoryMsg(''); }}
                        style={{
                            padding: '6px 12px', borderRadius: '20px', cursor: 'pointer',
                            fontSize: '0.75rem', fontWeight: 700, border: '1.5px dashed',
                            background: showAddCategory ? 'rgba(16,185,129,0.1)' : 'transparent',
                            color: '#10b981', borderColor: '#10b981', transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                        }}
                    >
                        {showAddCategory ? '✕ Cancel' : '+ Add Category'}
                    </button>
                </div>

                {/* Inline Add-Category Form */}
                {showAddCategory && (
                    <div style={{
                        background: 'linear-gradient(135deg, #f0fdf4, #ecfdf5)', border: '1px solid #bbf7d0',
                        borderRadius: 10, padding: '0.9rem 1rem', marginBottom: '0.75rem',
                        display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'flex-end',
                    }}>
                        <div>
                            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#065f46', marginBottom: 3 }}>ICON</div>
                            <input
                                value={newCategory.icon}
                                onChange={e => setNewCategory(c => ({ ...c, icon: e.target.value }))}
                                placeholder="🏢"
                                style={{ width: 44, padding: '0.35rem', borderRadius: 6, border: '1px solid #a7f3d0', fontSize: '1rem', textAlign: 'center' }}
                            />
                        </div>
                        <div style={{ flex: 1, minWidth: 120 }}>
                            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#065f46', marginBottom: 3 }}>LABEL</div>
                            <input
                                value={newCategory.label}
                                onChange={e => setNewCategory(c => ({ ...c, label: e.target.value }))}
                                placeholder="e.g. Renewables"
                                style={{ width: '100%', padding: '0.35rem 0.5rem', borderRadius: 6, border: '1px solid #a7f3d0', fontSize: '0.8rem' }}
                            />
                        </div>
                        <div style={{ flex: 1, minWidth: 120 }}>
                            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#065f46', marginBottom: 3 }}>ID (slug)</div>
                            <input
                                value={newCategory.id}
                                onChange={e => setNewCategory(c => ({ ...c, id: e.target.value.replace(/\s+/g, '_').toLowerCase() }))}
                                placeholder="e.g. renewables"
                                style={{ width: '100%', padding: '0.35rem 0.5rem', borderRadius: 6, border: '1px solid #a7f3d0', fontSize: '0.8rem', fontFamily: 'monospace' }}
                            />
                        </div>
                        <button
                            onClick={handleAddCategory}
                            style={{
                                background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff',
                                border: 'none', padding: '0.4rem 1rem', borderRadius: 8,
                                fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer',
                            }}
                        >✓ Add</button>
                        {categoryMsg && (
                            <div style={{ width: '100%', fontSize: '0.72rem', color: '#b45309', fontWeight: 600 }}>{categoryMsg}</div>
                        )}
                    </div>
                )}
            </div>

            {selectedDict !== 'global' && (() => {
                const isVertical = industryVerticals.some(v => v.id === selectedDict);
                const vertMeta = isVertical ? industryVerticals.find(v => v.id === selectedDict) : null;
                return (
                    <div style={{
                        padding: '0.6rem 0.8rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.82rem',
                        ...(isVertical
                            ? { background: 'rgba(99,102,241,0.07)', borderLeft: '4px solid #6366f1', color: '#4f46e5' }
                            : { background: '#eff6ff', borderLeft: '4px solid #3b82f6', color: '#1e40af' })
                    }}>
                        {isVertical ? (
                            <>
                                <strong>★ Industry Vertical Blueprint: {vertMeta?.label}</strong>
                                {vertMeta && <span style={{ marginLeft: '0.75rem', opacity: 0.75 }}>{vertMeta.q1_count} doubly-material issues · {vertMeta.issue_count} total</span>}
                                <div style={{ marginTop: '0.4rem', fontSize: '0.78rem', opacity: 0.8 }}>
                                    Q1 issues: {vertMeta?.q1_titles?.join(', ') || '—'}
                                </div>
                                <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
                                    <span style={{ fontWeight: 700, fontSize: '0.78rem' }}>Apply to session:</span>
                                    <select
                                        value={applyTarget}
                                        onChange={e => setApplyTarget(e.target.value)}
                                        style={{ padding: '0.3rem 0.6rem', borderRadius: '6px', border: '1px solid #c7d2fe', background: '#eef2ff', color: '#3730a3', fontSize: '0.78rem', minWidth: 160 }}
                                    >
                                        <option value=''>-- choose session --</option>
                                        {verticalSessions.map(s => (
                                            <option key={s.session_id || s.id} value={s.session_id || s.id}>
                                                {s.cohort_name || s.session_id || s.id}
                                            </option>
                                        ))}
                                    </select>
                                    <button
                                        onClick={handleApplyVertical}
                                        disabled={!applyTarget || applyingVertical}
                                        style={{
                                            background: 'linear-gradient(135deg,#6366f1,#4f46e5)', color: '#fff',
                                            border: 'none', padding: '0.3rem 0.85rem', borderRadius: '6px',
                                            fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer',
                                            opacity: (!applyTarget || applyingVertical) ? 0.5 : 1,
                                        }}
                                    >
                                        {applyingVertical ? '⏳ Applying...' : '▶ Apply Blueprint'}
                                    </button>
                                    {applyMsg && <span style={{ fontSize: '0.76rem', fontWeight: 600 }}>{applyMsg}</span>}
                                </div>
                            </>
                        ) : (
                            <>📌 You are editing the <strong>{dictOptions.find(o => o.id === selectedDict)?.label}</strong> issue dictionary.
                            This dictionary is used when the <strong>Strategic Pillars</strong> paradigm is active and this BU is randomly selected for Round 2 materiality analysis.</>
                        )}
                    </div>
                );
            })()}

            {!showConfigurator && (
                <div className={styles.gatePrompt}>
                    <div className={styles.gateIcon}>
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                    </div>
                    <p className={styles.gateText}>
                        {isFacilitator ? (
                            sessionId ? (
                                <>The Materiality Matrix defines the specific issue dictionary, interdependencies, and consultant fees for <strong>Cohort {sessionId.slice(0,8)}</strong>. Modifying these values will automatically fork the global settings and <strong>only affect this active cohort</strong>.</>
                            ) : (
                                <>Please <strong>select a session</strong> from the Leaderboard or Dashboard before attempting to modify its isolated Materiality parameters.</>
                            )
                        ) : (
                            <>The Materiality Matrix defines the core issue dictionary, interdependencies, and consultant fees used across <strong>all cohorts</strong>. Modifying these values will affect <strong>all future simulation runs</strong>.</>
                        )}
                    </p>
                    <button
                        className={styles.gateBtn}
                        onClick={() => setShowConfigurator(true)}
                        disabled={isFacilitator && !sessionId}
                        style={{ opacity: (isFacilitator && !sessionId) ? 0.5 : 1 }}
                    >
                        {(isFacilitator && !sessionId) ? 'Select a Session First' : 'Edit Materiality Matrix'}
                    </button>
                </div>
            )}

            {showConfigurator && (<>

            {/* Excel Import/Export Section */}
            {!isFacilitator && (
                <ExcelImportExport
                    selectedDict={selectedDict}
                    dictOptions={dictOptions}
                    onUploadSuccess={(data) => { fetchConfig(); }}
                />
            )}

            {/* Consultant Fee Section */}
            <div className={styles.section}>
                <h3>Consultant Lifeline Settings</h3>
                <div className={styles.formGroup}>
                    <label>Big 4 Consultant Fee (USD)</label>
                    <input
                        type="number"
                        className={styles.input}
                        value={feeInput}
                        onChange={(e) => setFeeInput(e.target.value)}
                        style={{ maxWidth: '300px' }}
                    />
                    <button className={`${styles.btnPrimary} ${styles.saveFeeBtn}`} onClick={handleUpdateFee}>
                        Save Fee
                    </button>
                    <small style={{ color: 'var(--text-muted)' }}>
                        This fee is deducted from the Corporate Treasury when the player clicks "Hire Consultant" in Round 2.
                    </small>
                </div>
            </div>

            {/* Issue Dictionary Section */}
            <div className={styles.section}>
                {sessionId ? (
                    <div style={{ padding: '1rem', background: 'var(--bg-elevated)', borderLeft: `4px solid ${isSandboxed ? 'var(--accent-orange)' : 'var(--border-subtle)'}`, marginBottom: '1.5rem', borderRadius: '4px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <h4 style={{ margin: 0, color: isSandboxed ? 'var(--accent-orange)' : 'var(--text-primary)' }}>
                                Cohort Override Sandbox
                            </h4>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                <input
                                    type="checkbox"
                                    checked={isSandboxed}
                                    onChange={handleToggleSandbox}
                                />
                                <strong>Enable Custom Dictionary</strong>
                            </label>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                            {isSandboxed
                                ? `You are editing a fully custom dictionary strictly for ${sessionId}. Structure (Add/Delete/Costs) is completely editable locally.`
                                : `Viewing the global "God Mode" dictionary. Enable the custom dictionary to make cohort-specific changes.`}
                        </p>
                    </div>
                ) : isFacilitator ? (
                    <div style={{ padding: '1rem', background: 'var(--bg-elevated)', borderLeft: '4px solid var(--accent-blue)', marginBottom: '1.5rem', borderRadius: '4px' }}>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                            {sessionId 
                                ? `You are editing an isolated configuration fork for the selected cohort (${sessionId.slice(0,8)}). Global defaults will NOT be altered.`
                                : `Select a session from the Leaderboard to override issue parameters for a specific cohort.`
                            }
                        </p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h3>The Issue Dictionary</h3>
                        {!isFacilitator && (
                            <div>
                                <input
                                    type="file"
                                    accept=".csv"
                                    id="csvUpload"
                                    style={{ display: 'none' }}
                                    onChange={handleCSVUpload}
                                />
                                <button
                                    className={styles.btnPrimary}
                                    style={{ background: 'var(--accent-green)', borderColor: 'var(--accent-green)' }}
                                    onClick={() => document.getElementById('csvUpload').click()}
                                >
                                    <span style={{ marginRight: '8px' }}>📁</span> Override with CSV
                                </button>
                            </div>
                        )}
                    </div>
                )}

                <div className={styles.tabs}>
                    {['economic', 'ecological', 'social', 'governance'].map(tab => (
                        <button
                            key={tab}
                            className={`${styles.tabBtn} ${activeTab === tab ? styles.active : ''}`}
                            onClick={() => setActiveTab(tab)}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)} Issues
                        </button>
                    ))}
                </div>

                <div className={styles.issueList}>
                    {filteredIssues.map(issue => {
                        return (
                            <div key={issue.id} className={styles.issueCard}>
                                <div className={styles.issueInfo}>
                                    <h4>{issue.title}</h4>
                                    <p className={styles.issueDesc}>{issue.hover_description}</p>
                                    <div className={styles.impactBadges}>
                                        <span className={`${styles.badge} ${styles[issue.financial_impact]}`}>
                                            Fin: {issue.financial_impact.toUpperCase()}
                                        </span>
                                        <span className={`${styles.badge} ${styles[issue.societal_impact]}`}>
                                            Impact: {issue.societal_impact.toUpperCase()}
                                        </span>
                                        {sessionId && isSandboxed ? (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Cost Override: $</span>
                                                <input
                                                    type="number"
                                                    className={styles.input}
                                                    style={{ padding: '0.2rem 0.5rem', width: '120px' }}
                                                    value={issue.mitigation_cost_usd}
                                                    onChange={(e) => {
                                                        const updatedIssues = config.issues.map(i => i.id === issue.id ? { ...i, mitigation_cost_usd: parseInt(e.target.value) || 0 } : i);
                                                        setConfig({ ...config, issues: updatedIssues });
                                                    }}
                                                    onBlur={(e) => handleSaveOverrideCost(issue.id, parseInt(e.target.value) || 0)}
                                                />
                                            </div>
                                        ) : (
                                            <span className={`${styles.badge}`} style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
                                                Cost: ${Number(issue.mitigation_cost_usd || 0).toLocaleString()}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                {(!isFacilitator || isSandboxed) && (
                                    <div className={styles.issueActions}>
                                        <button className={styles.btnDanger} onClick={() => handleDeleteIssue(issue.id)}>Delete</button>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                    {filteredIssues.length === 0 && (
                        <p style={{ color: 'var(--text-muted)' }}>No issues found in this category.</p>
                    )}
                </div>

                {/* Add New Issue Form (Global or Sandboxed Cohort) */}
                {(!isFacilitator || isSandboxed) && (
                    <form className={styles.addForm} onSubmit={handleAddIssue}>
                        <h4 style={{ marginTop: 0, marginBottom: '1rem', color: 'var(--accent-blue)' }}>Add New {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Issue</h4>
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label>Internal ID (optional, auto-generated)</label>
                                <input className={styles.input} value={newIssue.id} onChange={e => setNewIssue({ ...newIssue, id: e.target.value })} placeholder="e.g. water_scarcity" />
                            </div>
                            <div className={styles.formGroup}>
                                <label>Title</label>
                                <input className={styles.input} required value={newIssue.title} onChange={e => setNewIssue({ ...newIssue, title: e.target.value })} placeholder="e.g. Water Scarcity in Deccan Plateau" />
                            </div>
                        </div>
                        <div className={styles.formGroup}>
                            <label>Hover Description (Tooltip)</label>
                            <input className={styles.input} required value={newIssue.hover_description} onChange={e => setNewIssue({ ...newIssue, hover_description: e.target.value })} placeholder="Short description shown on hover..." />
                        </div>
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label>Financial Materiality (Enterprise Value)</label>
                                <select className={styles.select} value={newIssue.financial_impact} onChange={e => setNewIssue({ ...newIssue, financial_impact: e.target.value })}>
                                    <option value="low">Low Impact</option>
                                    <option value="medium">Medium Impact</option>
                                    <option value="high">High Impact</option>
                                </select>
                            </div>
                            <div className={styles.formGroup}>
                                <label>Impact Materiality (People/Planet)</label>
                                <select className={styles.select} value={newIssue.societal_impact} onChange={e => setNewIssue({ ...newIssue, societal_impact: e.target.value })}>
                                    <option value="low">Low Impact</option>
                                    <option value="medium">Medium Impact</option>
                                    <option value="high">High Impact</option>
                                </select>
                            </div>
                        </div>
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label>Stakeholders Group</label>
                                <input className={styles.input} value={newIssue.stakeholders_group || ''} onChange={e => setNewIssue({ ...newIssue, stakeholders_group: e.target.value })} placeholder="e.g. External; Activist" />
                            </div>
                            <div className={styles.formGroup}>
                                <label>Stakeholders Subgroup</label>
                                <input className={styles.input} value={newIssue.stakeholders_subgroup || ''} onChange={e => setNewIssue({ ...newIssue, stakeholders_subgroup: e.target.value })} placeholder="e.g. Patients; Digital Rights Activists" />
                            </div>
                        </div>
                        <div className={styles.formGroup}>
                            <label>Nature of Impact</label>
                            <input className={styles.input} value={newIssue.nature_of_impact || ''} onChange={e => setNewIssue({ ...newIssue, nature_of_impact: e.target.value })} placeholder="e.g. Identity theft risk..." />
                        </div>
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label>Affected BU 1</label>
                                <select className={styles.select} value={newIssue.affected_bu_1 || ''} onChange={e => setNewIssue({ ...newIssue, affected_bu_1: e.target.value })}>
                                    <option value="">None / Corporate</option>
                                    {dictOptions.filter(o => o.id !== 'global').map(o => (
                                        <option key={o.id} value={o.id}>{o.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div className={styles.formGroup}>
                                <label>Affected BU 2 (Optional)</label>
                                <select className={styles.select} value={newIssue.affected_bu_2 || ''} onChange={e => setNewIssue({ ...newIssue, affected_bu_2: e.target.value })}>
                                    <option value="">None</option>
                                    {dictOptions.filter(o => o.id !== 'global').map(o => (
                                        <option key={o.id} value={o.id}>{o.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className={styles.formGroup}>
                            <label>Mitigation Cost (USD)</label>
                            <input type="number" className={styles.input} value={newIssue.mitigation_cost_usd} onChange={e => setNewIssue({ ...newIssue, mitigation_cost_usd: parseInt(e.target.value) || 0 })} placeholder="0" />
                        </div>
                        <button type="submit" className={styles.btnPrimary} style={{ marginTop: '0.5rem' }}>+ Add Issue</button>
                    </form>
                )}
            </div>

            {/* Interdependence Matrix Section (Global Only) */}
            {(!sessionId || isSandboxed) && (
                <div className={styles.section}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <h3>Interdependence Matrix</h3>
                            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                                Define how perspectives are interconnected (e.g. an Ecological impact leading to future Financial risks).
                            </p>
                        </div>
                        {!isFacilitator && (
                            <div style={{ marginTop: '1rem' }}>
                                <input
                                    type="file"
                                    accept=".csv"
                                    id="interdepsCsvUpload"
                                    style={{ display: 'none' }}
                                    onChange={handleInterdependenciesCSVUpload}
                                />
                                <button
                                    className={styles.btnPrimary}
                                    style={{ background: 'var(--accent-green)', borderColor: 'var(--accent-green)' }}
                                    onClick={() => document.getElementById('interdepsCsvUpload').click()}
                                >
                                    <span style={{ marginRight: '8px' }}>📁</span> Override with CSV
                                </button>
                            </div>
                        )}
                    </div>

                    <div className={styles.issueList}>
                        {config.interdependencies.map((link, idx) => {
                            const srcId = link.source_issue_id || link.source;
                            const tgtId = link.target_issue_id || link.target;
                            const source = config.issues.find(i => i.id === srcId);
                            const target = config.issues.find(i => i.id === tgtId);
                            return (
                                <div key={link.id || `${srcId}_${tgtId}_${idx}`} className={styles.issueCard}>
                                    <div className={styles.issueInfo}>
                                        <h4>{source?.title || srcId} <span style={{ color: 'var(--accent-blue)' }}>➔</span> {target?.title || tgtId}</h4>
                                        <p className={styles.issueDesc}>{link.description}</p>
                                        <div className={styles.impactBadges}>
                                            <span className={styles.badge} style={{ border: '1px solid var(--accent-blue)' }}>Severity: {link.severity}/5</span>
                                        </div>
                                    </div>
                                    <div className={styles.issueActions}>
                                        <button className={styles.btnDanger} onClick={() => handleDeleteLink(link.id)}>Remove</button>
                                    </div>
                                </div>
                            );
                        })}
                        {config.interdependencies.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No interdependencies mapped.</p>}
                    </div>

                    <form className={styles.addForm} onSubmit={handleAddLink}>
                        <h4 style={{ marginTop: 0, marginBottom: '1rem', color: 'var(--accent-blue)' }}>Map New Interdependence</h4>
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label>Source Issue</label>
                                <select className={styles.select} required value={newLink.source_issue_id} onChange={e => setNewLink({ ...newLink, source_issue_id: e.target.value })}>
                                    <option value="">-- Select Source --</option>
                                    {config.issues.map(i => <option key={i.id} value={i.id}>{i.title}</option>)}
                                </select>
                            </div>
                            <div className={styles.formGroup}>
                                <label>Target Issue</label>
                                <select className={styles.select} required value={newLink.target_issue_id} onChange={e => setNewLink({ ...newLink, target_issue_id: e.target.value })}>
                                    <option value="">-- Select Target --</option>
                                    {config.issues.map(i => <option key={i.id} value={i.id}>{i.title}</option>)}
                                </select>
                            </div>
                        </div>
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label>Link Description (How are they related?)</label>
                                <input className={styles.input} required value={newLink.description} onChange={e => setNewLink({ ...newLink, description: e.target.value })} placeholder="e.g. Pollution leads to regulatory fines." />
                            </div>
                            <div className={styles.formGroup}>
                                <label>Severity (1-5)</label>
                                <input className={styles.input} type="number" min="1" max="5" value={newLink.severity} onChange={e => setNewLink({ ...newLink, severity: parseInt(e.target.value, 10) })} />
                            </div>
                        </div>
                        <button type="submit" className={styles.btnPrimary} style={{ marginTop: '0.5rem' }}>+ Link Issues</button>
                    </form>
                </div>
            )}
            </>)}
        </div >
    );
}
