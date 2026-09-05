'use client';

/**
 * ConfigLiveStatus — "is the engine running the values I set?"
 *
 * SLOT: god-mode Engine Configuration panel, directly under the config
 * uploader. It is deliberately adjacent: the uploader is where a wrong belief
 * is formed, so this is where it has to be corrected.
 *
 * WHY THIS PANEL EXISTS
 *   There are three ways to tune this simulation and they fail three different
 *   ways:
 *     1. The Excel uploader above writes simulation_config.json onto the DATA
 *        VOLUME (it survives a redeploy) — but its hot-reload only reloads a
 *        few modules, leaving every `from config import X` consumer bound to
 *        the OLD value until a restart. It reports {"reload": "complete"}
 *        either way. And the volume keeps its copy forever: a build that
 *        changed a default is silently not in effect on a volume seeded by
 *        an earlier build, and config.py refuses (clamps) known-legacy values
 *        with nothing but a stdout line (CFG-02/03, audit 2026-09-04).
 *     2. The god-mode engine-tunable sliders forward 2 of their 24 values; the
 *        other 22 are write-only and the endpoint still returns {"changed":…}.
 *     3. Editing the JSON, committing and redeploying, then refreshing the
 *        volume copy (DEPLOYMENT_CHECKLIST §5b) — the path that fully works.
 *
 *   So "did my change take effect?" used to be answerable only by moving a
 *   parameter and watching the numbers — an observation the engine's
 *   non-determinism makes unreliable. This reads the values the RUNNING PROCESS
 *   holds and names every way they disagree with what was configured:
 *   `clamped_value` (the volume says X, the engine runs Y), `image_vs_volume`
 *   (the volume kept an earlier build's numbers), stale bindings, god-mode
 *   shadowing.
 *
 * READ `problems` FIRST. Empty means the file, this process and every consumer
 * module agree and nothing was clamped. Anything else tells you which failure
 * mode you hit, by name. `advisories` (inert god-mode tunables) are true of a
 * pristine install and never colour the verdict.
 *
 * Colours come from styles/tokens.css semantic tokens only (repo convention —
 * no raw hex for danger/caution/positive).
 */

import { useState, useEffect, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const SEVERITY = {
    high:   { token: 'danger',   label: 'HIGH' },
    medium: { token: 'caution',  label: 'MED' },
    low:    { token: 'info',     label: 'LOW' },
};

function severityOf(sev) {
    return SEVERITY[sev] || SEVERITY.low;
}

/* Most severe first, so the thing that matters is never below the fold. */
const SEVERITY_ORDER = { high: 0, medium: 1, low: 2 };

export default function ConfigLiveStatus({ refreshToken = 0 }) {
    const [report, setReport] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState('');

    const load = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const res = await fetch(`${API}/api/admin/config/live`, { credentials: 'include' });
            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                throw new Error(body.detail || `HTTP ${res.status}`);
            }
            setReport(await res.json());
        } catch (e) {
            setError(e.message || 'Could not read the live configuration.');
            setReport(null);
        } finally {
            setLoading(false);
        }
    }, []);

    // Re-read on mount and whenever the parent bumps refreshToken — which the
    // uploader does after a successful upload, so the answer to "did that take?"
    // appears without anyone having to think to ask.
    useEffect(() => { load(); }, [load, refreshToken]);

    const problems = [...(report?.problems || [])].sort(
        (a, b) => (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9)
    );
    const advisories = Array.isArray(report?.advisories) ? report.advisories : [];
    const healthy = !!report?.healthy;
    const constants = report?.constants || {};
    const constantNames = Object.keys(constants).filter(
        (n) => !filter || n.toLowerCase().includes(filter.toLowerCase())
    );

    const statusToken = healthy ? 'positive' : (problems.some((p) => p.severity === 'high') ? 'danger' : 'caution');

    return (
        <div
            data-testid="config-live-status"
            style={{
                marginTop: '1.5rem',
                background: 'var(--bg-card)',
                border: '1px solid rgba(255,255,255,0.04)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem 1.5rem',
            }}
        >
            {/* Header */}
            <div style={{
                display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
                marginBottom: '0.9rem', borderBottom: '1px solid rgba(255,255,255,0.04)',
                paddingBottom: '0.6rem',
            }}>
                <div>
                    <span style={{ color: 'var(--text-primary)', fontSize: '0.8rem', fontWeight: 700 }}>
                        🔎 Live Engine Configuration — what this process is actually running
                    </span>
                    <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.5 }}>
                        Read straight off the running process, not re-read from the file. Confirms whether the
                        values you last set are the values the engine is using.
                    </div>
                </div>
                <button
                    onClick={load}
                    disabled={loading}
                    style={{
                        flexShrink: 0, marginLeft: '1rem',
                        padding: '0.4rem 0.9rem', borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                        background: 'transparent',
                        color: 'var(--text-secondary)', fontSize: 'var(--type-caption)', fontWeight: 600,
                        cursor: loading ? 'not-allowed' : 'pointer',
                        opacity: loading ? 0.5 : 1,
                    }}
                >
                    {loading ? 'Reading…' : '↻ Re-check'}
                </button>
            </div>

            {error && (
                <div role="alert" style={{
                    background: 'var(--danger-soft)', color: 'var(--danger-text)',
                    border: '1px solid var(--danger)', borderRadius: 'var(--radius-sm)',
                    padding: '0.6rem 0.8rem', fontSize: 'var(--type-caption)',
                }}>
                    {error}
                </div>
            )}

            {report && (
                <>
                    {/* Verdict — the one line worth reading */}
                    <div
                        data-testid="config-live-summary"
                        style={{
                            display: 'flex', alignItems: 'center', gap: '0.7rem',
                            background: `var(--${statusToken}-soft)`,
                            border: `1px solid var(--${statusToken})`,
                            borderRadius: 'var(--radius-sm)',
                            padding: '0.7rem 0.9rem',
                            fontSize: '0.75rem',
                            color: `var(--${statusToken}-text)`,
                            fontWeight: 600,
                        }}
                    >
                        <span aria-hidden="true">{healthy ? '✅' : '⚠️'}</span>
                        <span>{report.summary}</span>
                    </div>

                    {/* Problems, worst first */}
                    {problems.length > 0 && (
                        <ul data-testid="config-live-problems" style={{
                            listStyle: 'none', padding: 0, margin: '0.8rem 0 0',
                            display: 'flex', flexDirection: 'column', gap: '0.5rem',
                        }}>
                            {problems.map((p, i) => {
                                const sev = severityOf(p.severity);
                                return (
                                    <li key={`${p.kind}-${i}`} style={{
                                        display: 'flex', gap: '0.6rem', alignItems: 'flex-start',
                                        background: 'rgba(255,255,255,0.02)',
                                        border: '1px solid var(--border-subtle)',
                                        borderLeft: `3px solid var(--${sev.token})`,
                                        borderRadius: 'var(--radius-sm)',
                                        padding: '0.55rem 0.75rem',
                                    }}>
                                        <span style={{
                                            flexShrink: 0, fontSize: 'var(--type-caption)', fontWeight: 800,
                                            letterSpacing: '0.04em',
                                            color: `var(--${sev.token}-text)`,
                                            fontFamily: 'var(--font-mono)', paddingTop: 2,
                                        }}>
                                            {sev.label}
                                        </span>
                                        <div>
                                            <div style={{
                                                fontSize: 'var(--type-caption)', fontFamily: 'var(--font-mono)',
                                                color: 'var(--text-muted)', marginBottom: 2,
                                            }}>
                                                {p.kind}
                                            </div>
                                            <div style={{
                                                fontSize: 'var(--type-caption)', color: 'var(--text-secondary)',
                                                lineHeight: 1.5,
                                            }}>
                                                {p.message}
                                            </div>
                                        </div>
                                    </li>
                                );
                            })}
                        </ul>
                    )}

                    {/* Fingerprint — stamp this on a run and a later reader can tell
                        whether the configuration has moved since. */}
                    <div style={{
                        marginTop: '0.8rem', display: 'flex', gap: '1.2rem', flexWrap: 'wrap',
                        fontSize: 'var(--type-caption)', fontFamily: 'var(--font-mono)',
                        color: 'var(--text-muted)', opacity: 0.75,
                    }}>
                        <span>fingerprint: {report.fingerprint}</span>
                        <span>constants: {report.constant_count}</span>
                        {report.file_vs_process?.status && (
                            <span>file_vs_process: {report.file_vs_process.status}</span>
                        )}
                        {report.image_vs_volume?.status && (
                            <span>image_vs_volume: {report.image_vs_volume.status}</span>
                        )}
                        {Array.isArray(report.clamped_values) && (
                            <span>clamped: {report.clamped_values.length}</span>
                        )}
                    </div>

                    {/* Advisories — inert god-mode tunables. Real, worth knowing,
                        and NOT a reason to call the configuration unhealthy. */}
                    {advisories.length > 0 && (
                        <details style={{ marginTop: '0.7rem' }} data-testid="config-live-advisories">
                            <summary style={{
                                cursor: 'pointer', fontSize: 'var(--type-caption)', fontWeight: 600,
                                color: 'var(--text-secondary)',
                            }}>
                                {advisories.length} advisory note{advisories.length === 1 ? '' : 's'} (inert tunables — informational)
                            </summary>
                            <ul style={{
                                listStyle: 'none', padding: 0, margin: '0.5rem 0 0',
                                display: 'flex', flexDirection: 'column', gap: '0.3rem',
                            }}>
                                {advisories.map((a, i) => (
                                    <li key={`${a.kind}-${i}`} style={{
                                        fontSize: 'var(--type-caption)', color: 'var(--text-muted)', lineHeight: 1.5,
                                        borderLeft: '2px solid var(--border-subtle)', paddingLeft: '0.6rem',
                                    }}>
                                        <span style={{ fontFamily: 'var(--font-mono)' }}>{a.kind}</span> — {a.message}
                                    </li>
                                ))}
                            </ul>
                        </details>
                    )}

                    {/* Everything else, summoned not ambient */}
                    <details style={{ marginTop: '0.9rem' }}>
                        <summary style={{
                            cursor: 'pointer', fontSize: 'var(--type-caption)', fontWeight: 600,
                            color: 'var(--text-secondary)',
                        }}>
                            All {report.constant_count} live values
                        </summary>

                        <input
                            type="text"
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            placeholder="Filter by name, e.g. CARBON"
                            aria-label="Filter constants by name"
                            style={{
                                width: '100%', marginTop: '0.6rem', padding: '0.4rem 0.6rem',
                                borderRadius: 'var(--radius-sm)',
                                border: '1px solid var(--border-subtle)',
                                background: 'transparent', color: 'var(--text-primary)',
                                fontSize: 'var(--type-caption)', fontFamily: 'var(--font-mono)',
                            }}
                        />

                        <div style={{ maxHeight: 320, overflowY: 'auto', marginTop: '0.5rem' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--type-caption)' }}>
                                <tbody>
                                    {constantNames.map((name) => (
                                        <tr key={name} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                                            <td style={{
                                                padding: '0.28rem 0.5rem 0.28rem 0',
                                                fontFamily: 'var(--font-mono)', color: 'var(--text-muted)',
                                                whiteSpace: 'nowrap',
                                            }}>
                                                {name}
                                            </td>
                                            <td style={{
                                                padding: '0.28rem 0', textAlign: 'right',
                                                fontFamily: 'var(--font-mono)', color: 'var(--text-primary)',
                                            }}>
                                                {String(constants[name])}
                                            </td>
                                        </tr>
                                    ))}
                                    {constantNames.length === 0 && (
                                        <tr>
                                            <td colSpan={2} style={{
                                                padding: '0.6rem 0', color: 'var(--text-muted)',
                                                fontSize: 'var(--type-caption)',
                                            }}>
                                                No constant matches “{filter}”.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </details>
                </>
            )}
        </div>
    );
}
