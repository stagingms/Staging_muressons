'use client';
import React, { useCallback, useEffect, useRef, useState } from 'react';

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
 *
 * COHORT MODE HAS TWO VARIANTS, and this component does not decide which.
 * It FETCHES the cohort's roster shape and renders that:
 *
 *   4-BU conglomerate → every player runs all four business units, so there is
 *                       no per-player company to assign and the sheet is
 *                       identity-only.
 *   Single business   → each player runs their own company, so the sheet carries
 *                       industry + region per row, picked from the cohort's own
 *                       formation vocabulary.
 *
 * The shape is fetched rather than inferred from a prop because the server owns
 * it: the same object shapes the .xlsx template and gates the upload (see
 * backend/roster_shape.py). A modal that guessed the mode locally would
 * eventually promise a column the template does not ship — which is the class of
 * bug this replaces, not a new one to introduce. `shapeHint` is accepted only to
 * avoid a blank frame on open, and is overwritten the moment the fetch lands.
 */

const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

// Column → the label the operator sees. The set of columns is the server's;
// only their presentation is ours.
const COLUMN_LABELS = {
    name: 'Name',
    email: 'Email',
    programme: 'Programme',
    industry_vertical: 'Industry',
    region_id: 'Region',
    assigned_bu: 'BU slot',
};

const prettyId = (id) =>
    !id ? '—' : String(id).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

const MODES = {
    cohort: {
        title: '📥 Bulk Add Players',
        // Replaced by the shape's own description once it arrives; this is only
        // what the first frame says.
        blurb: 'Upload one row per player. Only "name" is required. Every player '
             + 'receives their own temporary password, shown in the roster until '
             + 'they change it.',
        // Cohort-scoped: a single-business cohort needs its own industry and
        // region dropdowns, which the cohort-less route cannot know about.
        templateUrl: (sid) => `/api/admin/${sid}/players/bulk-template`,
        shapeUrl: (sid) => `/api/admin/${sid}/players/roster-shape`,
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

export default function BulkPlayerUpload({
    mode = 'cohort', sessionId, cohortName, shapeHint = null, onClose, onDone,
}) {
    const cfg = MODES[mode] || MODES.cohort;
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    const fileRef = useRef(null);

    const [file, setFile] = useState(null);
    const [busy, setBusy] = useState('');          // '' | 'preview' | 'commit'
    const [preview, setPreview] = useState(null);  // successful preview payload
    const [problem, setProblem] = useState(null);  // { message, errors[] }
    const [result, setResult] = useState(null);    // successful commit payload
    const [shape, setShape] = useState(shapeHint); // cohort's roster shape

    // Fetch the roster shape once per cohort. A failure is NOT surfaced as an
    // error: the template and the upload are both gated server-side by the same
    // shape, so a missing shape costs the operator the tailored copy and nothing
    // more. Reporting it would be alarming about something that cannot cause a
    // wrong import.
    useEffect(() => {
        if (mode !== 'cohort' || !sessionId) return;
        let alive = true;
        (async () => {
            try {
                const res = await fetch(`${API}${cfg.shapeUrl(sessionId)}`, { credentials: 'include' });
                if (!res.ok) return;
                const body = await res.json();
                if (alive && body?.shape) setShape(body.shape);
            } catch { /* keep the generic copy */ }
        })();
        return () => { alive = false; };
    }, [API, cfg, mode, sessionId]);

    const perPlayerScope = !!shape?.per_player_scope;
    // Which columns the preview table shows. Server-driven, so it can never
    // display a column this cohort's sheet does not have.
    const previewColumns = mode === 'master'
        ? ['name', 'email', 'programme']
        : (shape?.columns || ['name', 'email', 'programme']);

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
            const res = await fetch(`${API}${cfg.templateUrl(sessionId)}`, { credentials: 'include' });
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
    }, [API, cfg, sessionId]);

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
                // A rejection still carries the shape, and it is exactly when the
                // operator most needs the columns described.
                if (payload.shape) setShape(payload.shape);
            } else {
                setPreview(payload);
                if (payload?.shape) setShape(payload.shape);
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
        modeChip: (single) => ({
            display: 'inline-flex', alignItems: 'center', gap: 5,
            marginTop: '0.55rem', padding: '3px 9px', borderRadius: 999,
            fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.02em',
            border: '1px solid',
            ...(single
                ? { background: 'rgba(99,102,241,0.12)', borderColor: 'rgba(99,102,241,0.45)', color: '#a5b4fc' }
                : { background: 'rgba(34,197,94,0.10)', borderColor: 'rgba(34,197,94,0.40)', color: '#86efac' }),
        }),
        scopeBox: {
            marginTop: '0.85rem', background: 'rgba(99,102,241,0.06)',
            border: '1px solid rgba(99,102,241,0.22)', borderRadius: 10,
            padding: '0.7rem 0.9rem',
        },
        pill: {
            display: 'inline-block', margin: '2px 4px 2px 0', padding: '2px 7px',
            borderRadius: 5, background: 'rgba(148,163,184,0.12)',
            border: '1px solid rgba(148,163,184,0.22)', fontSize: '0.7rem',
            color: '#cbd5e1', fontFamily: 'monospace',
        },
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
                    <p style={{ ...S.note, margin: '0.45rem 0 0' }}>
                        {mode === 'cohort' && shape
                            ? (perPlayerScope
                                ? 'One row per player. Each player runs their OWN company — pick '
                                  + 'their industry and region per row. Only "name" is required; '
                                  + 'leave the rest blank to inherit the cohort’s own settings. '
                                  + 'Every player receives their own temporary password.'
                                : 'One row per player. Every player in this cohort runs all four '
                                  + 'business units, so there is no company to assign — just who '
                                  + 'they are. Only "name" is required. Every player receives their '
                                  + 'own temporary password.')
                            : cfg.blurb}
                    </p>
                    {/* The mode, stated once and unmissably. The two variants
                        differ in what they MEAN, not just in which columns they
                        have, so naming the mode is worth the line. */}
                    {mode === 'cohort' && shape && (
                        <span style={S.modeChip(perPlayerScope)}>
                            {perPlayerScope ? '🏭 Single Business' : '🏢 4-BU Conglomerate'}
                            {' · '}
                            {perPlayerScope ? 'one company per player' : 'all four BUs per player'}
                        </span>
                    )}
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

                    {/* What the sheet looks like, BEFORE the download — so the
                        operator recognises the file they get, and so an author
                        reusing last term's roster can see at a glance that the
                        columns have changed. */}
                    {mode === 'cohort' && shape && (
                        <div style={S.scopeBox}>
                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#cbd5e1',
                                          textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Columns on this cohort’s sheet
                            </div>
                            <div style={{ marginTop: '0.4rem' }}>
                                {previewColumns.map((c) => (
                                    <span key={c} style={S.pill}>
                                        {c}{c === 'name' ? ' *' : ''}
                                    </span>
                                ))}
                            </div>
                            {perPlayerScope ? (
                                <div style={{ ...S.note, marginTop: '0.5rem' }}>
                                    <strong style={{ color: '#a5b4fc' }}>Industry</strong> and{' '}
                                    <strong style={{ color: '#a5b4fc' }}>region</strong> are
                                    dropdowns — free text is rejected. Blank inherits this cohort’s
                                    own setting
                                    {shape.cohort?.industry_vertical
                                        ? ` (${prettyId(shape.cohort.industry_vertical)}`
                                          + `${shape.cohort.region_id ? ` · ${prettyId(shape.cohort.region_id)}` : ''})`
                                        : ''}
                                    . Two players may run different industries in different regions.
                                    You do not set a BU slot — it is derived from the industry.
                                </div>
                            ) : (
                                <div style={{ ...S.note, marginTop: '0.5rem' }}>
                                    No business unit, industry or region column: this cohort’s four
                                    verticals and its region are set once for everyone in{' '}
                                    <em>Edit Cohort</em>. A per-player business unit here would
                                    scope that player down to a single business, so such a column is
                                    refused on upload rather than half-honoured.
                                </div>
                            )}
                        </div>
                    )}

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
                            {perPlayerScope && (
                                <div style={{ ...S.note, marginTop: '0.5rem', color: '#a5b4fc' }}>
                                    Industry and region below are the <strong>resolved</strong>{' '}
                                    values — blanks already inherited from the cohort, and the BU
                                    slot derived. This is what each player will actually run.
                                </div>
                            )}
                            {preview.players?.length > 0 && (
                                <table style={{ width: '100%', marginTop: '0.75rem', borderCollapse: 'collapse' }}>
                                    <thead><tr>
                                        {previewColumns.map((c) => (
                                            <th key={c} style={S.th}>{COLUMN_LABELS[c] || c}</th>
                                        ))}
                                        {/* Derived, so it is shown but never
                                            authored — the operator can confirm
                                            the industry landed in the slot they
                                            expect. */}
                                        {perPlayerScope && <th style={S.th}>BU slot</th>}
                                        {mode === 'master' && <th style={S.th}>Cohort</th>}
                                    </tr></thead>
                                    <tbody>
                                        {preview.players.slice(0, 25).map((p, i) => (
                                            <tr key={i}>
                                                {previewColumns.map((c) => (
                                                    <td key={c} style={S.td}>
                                                        {c === 'industry_vertical' || c === 'region_id'
                                                            ? prettyId(p[c])
                                                            : (p[c] || '—')}
                                                    </td>
                                                ))}
                                                {perPlayerScope && (
                                                    <td style={{ ...S.td, ...S.mono, color: '#94a3b8' }}>
                                                        {p.assigned_bu || '—'}
                                                    </td>
                                                )}
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
                                        {/* The one screen where "who runs what"
                                            is checkable before anyone logs in. */}
                                        {perPlayerScope && <th style={S.th}>Company</th>}
                                        <th style={S.th}>Temp password</th>
                                    </tr></thead>
                                    <tbody>
                                        {result.created.map((c) => (
                                            <tr key={c.player_id}>
                                                <td style={{ ...S.td, ...S.mono, color: '#a5b4fc' }}>{c.player_id}</td>
                                                <td style={S.td}>{c.name}</td>
                                                {perPlayerScope && (
                                                    <td style={S.td}>
                                                        {prettyId(c.industry_vertical)}
                                                        {c.region_id && (
                                                            <span style={{ color: '#64748b' }}>
                                                                {' · '}{prettyId(c.region_id)}
                                                            </span>
                                                        )}
                                                    </td>
                                                )}
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
