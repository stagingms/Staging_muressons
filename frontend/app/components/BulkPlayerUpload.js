'use client';
import React, { useCallback, useRef, useState } from 'react';

/**
 * BulkPlayerUpload — Excel provisioning for players (and, in master mode, for
 * facilitators and cohorts too).
 *
 * SLOT: OverlayHost (interrupt) — summoned from a button, never ambient.
 *
 * Two modes, one flow, because the flow is what carries the guarantee:
 *
 *   mode="cohort"  → up to 20 players into ONE cohort the caller operates.
 *   mode="master"  → facilitators + cohorts + players in a single workbook
 *                    (project-admin provisioning).
 *
 * The template → preview → commit sequence is deliberate. The backend contract
 * is ALL-OR-NOTHING: one bad row and nothing at all is created. Preview is a
 * separate endpoint (not a dry_run flag), so an older backend answers 404 and
 * this component reports that plainly rather than silently committing a file
 * the operator never reviewed. Errors are always rendered in FULL — the whole
 * point of validating the workbook totally is that the author fixes every
 * problem in one pass instead of re-uploading to discover the next one.
 */

const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

const MODES = {
    cohort: {
        title: '📥 Bulk Add Players',
        blurb: 'Upload one row per player. Only "name" is required — email, programme, '
             + 'business unit and region are optional. Every player receives their own '
             + 'temporary password, shown in the roster until they change it.',
        templateUrl: () => `/api/admin/players/bulk-template`,
        previewUrl: (sid) => `/api/admin/${sid}/players/bulk-preview`,
        commitUrl: (sid) => `/api/admin/${sid}/players/bulk-upload`,
        templateName: 'muressons_player_roster_template.xlsx',
    },
    master: {
        title: '🏛️ Master Provisioning Upload',
        blurb: 'One workbook, three sheets — Facilitators, Cohorts and Players — that '
             + 'provisions an entire programme. Link rows using your own "ref" values '
             + '(f1, c1, …); a cohort may instead cite an existing facilitator ID.',
        templateUrl: () => `/api/admin/provisioning/master-template`,
        previewUrl: () => `/api/admin/provisioning/master-preview`,
        commitUrl: () => `/api/admin/provisioning/master-upload`,
        templateName: 'muressons_master_provisioning_template.xlsx',
    },
};

/** FastAPI puts our structured payload in `detail`; it may be a string or an object. */
function readError(payload) {
    const detail = payload?.detail ?? payload;
    if (typeof detail === 'string') return { message: detail, errors: [] };
    return { message: detail?.message || 'Upload failed.', errors: detail?.errors || [] };
}

export default function BulkPlayerUpload({ mode = 'cohort', sessionId, cohortName, onClose, onDone }) {
    const cfg = MODES[mode] || MODES.cohort;
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    const fileRef = useRef(null);

    const [file, setFile] = useState(null);
    const [busy, setBusy] = useState('');          // '' | 'preview' | 'commit'
    const [preview, setPreview] = useState(null);  // successful preview payload
    const [problem, setProblem] = useState(null);  // { message, errors[] }
    const [result, setResult] = useState(null);    // successful commit payload

    const post = useCallback(async (url, f) => {
        const fd = new FormData();
        fd.append('file', f);
        const res = await fetch(`${API}${url}`, { method: 'POST', credentials: 'include', body: fd });
        let payload = null;
        try { payload = await res.json(); } catch { payload = null; }
        return { res, payload };
    }, [API]);

    const downloadTemplate = useCallback(async () => {
        try {
            const res = await fetch(`${API}${cfg.templateUrl()}`, { credentials: 'include' });
            if (!res.ok) {
                setProblem({ message: `Could not download the template (${res.status}).`, errors: [] });
                return;
            }
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = cfg.templateName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch {
            setProblem({ message: 'Could not download the template — is the backend running?', errors: [] });
        }
    }, [API, cfg]);

    const choose = (f) => {
        setFile(f || null);
        setPreview(null);
        setProblem(null);
        setResult(null);
    };

    const runPreview = useCallback(async () => {
        if (!file) return;
        setBusy('preview');
        setProblem(null);
        setPreview(null);
        try {
            const { res, payload } = await post(cfg.previewUrl(sessionId), file);
            if (res.status === 404 || res.status === 405) {
                setProblem({
                    message: 'This backend does not support bulk upload yet. Restart the server after updating.',
                    errors: [],
                });
            } else if (!res.ok) {
                setProblem(readError(payload));
            } else if (payload?.ok === false) {
                // A validated-but-rejected workbook comes back 200 with ok:false,
                // because "your file has errors" is not an HTTP failure.
                setProblem({ message: payload.message, errors: payload.errors || [] });
            } else {
                setPreview(payload);
            }
        } catch {
            setProblem({ message: 'Network error — could not reach the server.', errors: [] });
        } finally {
            setBusy('');
        }
    }, [file, post, cfg, sessionId]);

    const runCommit = useCallback(async () => {
        if (!file) return;
        setBusy('commit');
        setProblem(null);
        try {
            const { res, payload } = await post(cfg.commitUrl(sessionId), file);
            if (!res.ok) {
                setProblem(readError(payload));
            } else {
                setResult(payload);
                onDone?.(payload);
            }
        } catch {
            setProblem({ message: 'Network error — nothing was created.', errors: [] });
        } finally {
            setBusy('');
        }
    }, [file, post, cfg, sessionId, onDone]);

    const S = {
        backdrop: {
            position: 'fixed', inset: 0, zIndex: 19000,
            background: 'rgba(2,6,15,0.72)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem',
        },
        card: {
            background: 'var(--bg-card, #0f172a)', border: '1px solid var(--border-subtle, #334155)',
            borderRadius: 16, width: '100%', maxWidth: 720, maxHeight: '86vh',
            display: 'flex', flexDirection: 'column', overflow: 'hidden',
        },
        head: { padding: '1.1rem 1.4rem', borderBottom: '1px solid var(--border-subtle, #334155)' },
        body: { padding: '1.1rem 1.4rem', overflowY: 'auto' },
        foot: {
            padding: '0.9rem 1.4rem', borderTop: '1px solid var(--border-subtle, #334155)',
            display: 'flex', gap: '0.6rem', justifyContent: 'flex-end', alignItems: 'center',
        },
        btn: (kind) => ({
            padding: '0.55rem 1.05rem', borderRadius: 8, cursor: 'pointer',
            fontSize: '0.8rem', fontWeight: 700, whiteSpace: 'nowrap',
            border: '1px solid',
            ...(kind === 'primary'
                ? { background: 'rgba(99,102,241,0.9)', borderColor: 'rgba(99,102,241,1)', color: '#fff' }
                : kind === 'go'
                ? { background: 'rgba(34,197,94,0.9)', borderColor: 'rgba(34,197,94,1)', color: '#052e16' }
                : { background: 'rgba(148,163,184,0.10)', borderColor: 'rgba(148,163,184,0.3)', color: '#cbd5e1' }),
        }),
        note: { fontSize: '0.78rem', color: 'var(--text-muted, #94a3b8)', lineHeight: 1.55 },
        errBox: {
            marginTop: '0.9rem', background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '0.8rem 0.95rem',
        },
        okBox: {
            marginTop: '0.9rem', background: 'rgba(34,197,94,0.08)',
            border: '1px solid rgba(34,197,94,0.3)', borderRadius: 10, padding: '0.8rem 0.95rem',
        },
        mono: { fontFamily: 'monospace', fontSize: '0.78rem' },
        th: { textAlign: 'left', padding: '5px 8px', color: '#94a3b8', fontSize: '0.68rem',
              textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid rgba(148,163,184,0.2)' },
        td: { padding: '5px 8px', fontSize: '0.78rem', borderBottom: '1px solid rgba(148,163,184,0.08)' },
    };

    const totals = preview?.totals;

    return (
        <div style={S.backdrop} onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}>
            <div style={S.card}>
                <div style={S.head}>
                    <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary, #e2e8f0)' }}>
                        {cfg.title}
                        {mode === 'cohort' && cohortName ? ` — ${cohortName}` : ''}
                    </h3>
                    <p style={{ ...S.note, margin: '0.45rem 0 0' }}>{cfg.blurb}</p>
                </div>

                <div style={S.body}>
                    <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'center' }}>
                        <button style={S.btn('ghost')} onClick={downloadTemplate}>⬇️ Download template</button>
                        <button style={S.btn('ghost')} onClick={() => fileRef.current?.click()}>
                            📄 {file ? 'Choose a different file' : 'Choose .xlsx file'}
                        </button>
                        <input
                            ref={fileRef}
                            type="file"
                            accept=".xlsx"
                            style={{ display: 'none' }}
                            onChange={(e) => choose(e.target.files?.[0])}
                        />
                        {file && <span style={{ ...S.mono, color: '#a5b4fc' }}>{file.name}</span>}
                    </div>

                    <p style={{ ...S.note, marginTop: '0.9rem' }}>
                        <strong style={{ color: '#fcd34d' }}>All or nothing.</strong>{' '}
                        The workbook is validated in full before anything is created. If any row is
                        rejected, nothing at all is created — so a failed upload never leaves a
                        half-provisioned cohort behind.
                    </p>

                    {problem && (
                        <div style={S.errBox}>
                            <div style={{ fontWeight: 700, color: '#f87171', fontSize: '0.82rem' }}>
                                {problem.message}
                            </div>
                            {problem.errors?.length > 0 && (
                                <ul style={{ margin: '0.6rem 0 0', paddingLeft: '1.1rem', ...S.mono, color: '#fca5a5' }}>
                                    {problem.errors.map((e, i) => (
                                        <li key={i} style={{ marginBottom: 3 }}>
                                            {e.sheet ? `${e.sheet} ` : ''}{e.row ? `row ${e.row}: ` : ''}{e.error}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    )}

                    {preview && !result && (
                        <div style={S.okBox}>
                            <div style={{ fontWeight: 700, color: '#4ade80', fontSize: '0.82rem' }}>
                                ✓ File is valid — nothing has been created yet.
                            </div>
                            <div style={{ ...S.note, marginTop: '0.4rem' }}>
                                {mode === 'master' ? (
                                    <>Will create <strong>{totals?.facilitators || 0}</strong> facilitator(s),{' '}
                                       <strong>{totals?.cohorts || 0}</strong> cohort(s) and{' '}
                                       <strong>{totals?.players || 0}</strong> player(s).</>
                                ) : (
                                    <>Will create <strong>{preview.total}</strong> player(s).{' '}
                                       This cohort holds {preview.limit} and currently has {preview.used}
                                       {' '}({preview.remaining} place{preview.remaining === 1 ? '' : 's'} free).</>
                                )}
                            </div>
                            {preview.warnings?.length > 0 && (
                                <ul style={{ margin: '0.6rem 0 0', paddingLeft: '1.1rem', fontSize: '0.76rem', color: '#fbbf24' }}>
                                    {preview.warnings.map((w, i) => <li key={i}>{w}</li>)}
                                </ul>
                            )}
                            {preview.players?.length > 0 && (
                                <table style={{ width: '100%', marginTop: '0.75rem', borderCollapse: 'collapse' }}>
                                    <thead><tr>
                                        <th style={S.th}>Name</th><th style={S.th}>Email</th>
                                        <th style={S.th}>Programme</th>
                                        {mode === 'master' && <th style={S.th}>Cohort</th>}
                                    </tr></thead>
                                    <tbody>
                                        {preview.players.slice(0, 25).map((p, i) => (
                                            <tr key={i}>
                                                <td style={S.td}>{p.name}</td>
                                                <td style={S.td}>{p.email || '—'}</td>
                                                <td style={S.td}>{p.programme || '—'}</td>
                                                {mode === 'master' && <td style={S.td}>{p.cohort_ref}</td>}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    )}

                    {result && (
                        <div style={S.okBox}>
                            <div style={{ fontWeight: 700, color: '#4ade80', fontSize: '0.82rem' }}>
                                ✓ Created successfully.
                            </div>
                            {/* Temp passwords are shown here AND remain readable in the
                                Player Registry until each player changes them, so closing
                                this dialog is not a destructive act. */}
                            {result.created?.length > 0 && (
                                <table style={{ width: '100%', marginTop: '0.7rem', borderCollapse: 'collapse' }}>
                                    <thead><tr>
                                        <th style={S.th}>Player ID</th><th style={S.th}>Name</th>
                                        <th style={S.th}>Temp password</th>
                                    </tr></thead>
                                    <tbody>
                                        {result.created.map((c) => (
                                            <tr key={c.player_id}>
                                                <td style={{ ...S.td, ...S.mono, color: '#a5b4fc' }}>{c.player_id}</td>
                                                <td style={S.td}>{c.name}</td>
                                                <td style={{ ...S.td, ...S.mono, color: '#fcd34d' }}>{c.temp_password}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                            {result.facilitators?.length > 0 && (
                                <table style={{ width: '100%', marginTop: '0.7rem', borderCollapse: 'collapse' }}>
                                    <thead><tr>
                                        <th style={S.th}>Facilitator</th><th style={S.th}>Name</th>
                                        <th style={S.th}>Role</th><th style={S.th}>One-time password</th>
                                    </tr></thead>
                                    <tbody>
                                        {result.facilitators.map((f) => (
                                            <tr key={f.facilitator_id}>
                                                <td style={{ ...S.td, ...S.mono, color: '#a5b4fc' }}>{f.facilitator_id}</td>
                                                <td style={S.td}>{f.name}</td>
                                                <td style={S.td}>{f.role}</td>
                                                <td style={{ ...S.td, ...S.mono, color: '#fcd34d' }}>{f.one_time_password}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                            {result.credential_note && (
                                <p style={{ ...S.note, marginTop: '0.6rem' }}>{result.credential_note}</p>
                            )}
                        </div>
                    )}
                </div>

                <div style={S.foot}>
                    <button style={S.btn('ghost')} onClick={onClose}>
                        {result ? 'Done' : 'Cancel'}
                    </button>
                    {!result && (
                        <>
                            <button
                                style={{ ...S.btn('primary'), opacity: !file || busy ? 0.5 : 1 }}
                                disabled={!file || !!busy}
                                onClick={runPreview}
                            >
                                {busy === 'preview' ? 'Checking…' : '🔍 Preview'}
                            </button>
                            <button
                                style={{ ...S.btn('go'), opacity: !preview || busy ? 0.5 : 1 }}
                                disabled={!preview || !!busy}
                                onClick={runCommit}
                                title={preview ? '' : 'Preview the file first'}
                            >
                                {busy === 'commit' ? 'Creating…' : '✓ Create'}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
