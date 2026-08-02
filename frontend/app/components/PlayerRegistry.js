import React, { useState, useEffect, useCallback, useRef } from 'react';
import styles from './PlayerRegistry.module.css';
import { getShortCode } from '../utils/sessionUtils';
import CohortSummaryTooltip from './CohortSummaryTooltip';
import BulkPlayerUpload from './BulkPlayerUpload';
import { resolveVerticalMeta } from '../lib/verticalCatalog';

const ADJECTIVES = ["blue", "swift", "brave", "quiet", "lucky", "bold", "calm", "proud", "wild", "smart"];
const NOUNS = ["rhino", "eagle", "tiger", "panda", "fox", "bear", "wolf", "lion", "hawk", "owl"];

function generatePassword() {
    // Passwords are now generated server-side — this is only a last-resort fallback.
    // Returning empty string forces the client to use the server-provided password.
    return '';
}

const TOOLTIP_ROLES = new Set(['super_admin', 'god_mode', 'lead_facilitator']);

export default function PlayerRegistry({ leaderboard, isSuperAdmin, isLeadOrAdmin = false, onEditCohort, currentFacilitatorRole = 'facilitator' }) {
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sessions, setSessions] = useState([]);
    // Generated credentials: { sessionId: [{player_id, password}, ...] }
    const [generatedCreds, setGeneratedCreds] = useState({});
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    // Cohort summary tooltip
    const [hoveredSession, setHoveredSession] = useState(null);
    const [hoverAnchorRect, setHoverAnchorRect] = useState(null);
    const hoverTimerRef = useRef(null);
    const canSeeSummaryTooltip = TOOLTIP_ROLES.has(currentFacilitatorRole);
    // Password reset toast
    const [resetToast, setResetToast] = useState(null); // { playerId, password }
    const resetToastTimerRef = useRef(null);
    // Bulk upload dialog — { sessionId, cohortName } | null
    const [bulkFor, setBulkFor] = useState(null);

    const copyToClipboard = (text) => {
        if (navigator.clipboard?.writeText) {
            navigator.clipboard.writeText(text).catch(() => {
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.style.cssText = 'position:fixed;opacity:0';
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
            });
        } else {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;opacity:0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
        }
    };

    useEffect(() => {
        if (leaderboard && leaderboard.length > 0) {
            setSessions(leaderboard);
        }
    }, [leaderboard]);

    const fetchPlayers = useCallback(async () => {
        try {
            const res = await fetch(`${API}/api/admin/players`, { credentials: 'include' });
            if (res.ok) {
                const data = await res.json();
                setPlayers(data.players || []);
            }
        } catch {
            // Silent — backend may be offline during frontend-only development
        } finally {
            setLoading(false);
        }
    }, [API]);

    useEffect(() => {
        fetchPlayers();
        const interval = setInterval(fetchPlayers, 10000);
        return () => clearInterval(interval);
    }, [fetchPlayers]);

    // Rebuild generatedCreds from backend session data on mount / session refresh
    // so that player IDs + passwords persist across page refreshes
    useEffect(() => {
        const rebuilt = {};
        sessions.forEach(session => {
            const sid = session.session_id;
            const regPlayers = session.registered_players || [];
            const allowedIds = session.allowed_player_ids || [];
            const creds = [];
            // Build from registered_players (plaintext_password is set by the server on generate-player)
            regPlayers.forEach(rp => {
                if (rp.player_id && !creds.some(c => c.player_id === rp.player_id)) {
                    // July 2026: the server now sends `temp_password` on every roster
                    // read, for as long as the credential is still the live one, so
                    // the facilitator can read it out at any point during setup.
                    // It goes empty the moment the player sets a personal password —
                    // that is a "player owns their password now" state, NOT a
                    // "reset to reveal" prompt. `plaintext_password` is read as a
                    // fallback so an older backend still populates the row.
                    creds.push({
                        player_id: rp.player_id,
                        password: rp.temp_password || rp.plaintext_password || '',
                        pending: !!rp.must_change_password,
                    });
                }
            });
            // Also include allowed_player_ids that aren't in registered_players
            allowedIds.forEach(pid => {
                if (!creds.some(c => c.player_id === pid)) {
                    // Pre-generated id with no stored plaintext — reset to reveal a new one.
                    creds.push({ player_id: pid, password: '', pending: true });
                }
            });
            if (creds.length > 0) {
                rebuilt[sid] = creds;
            }
        });
        setGeneratedCreds(prev => {
            // Merge: keep any locally-generated creds that aren't in the rebuilt set yet
            const merged = { ...rebuilt };
            Object.entries(prev).forEach(([sid, localCreds]) => {
                if (!merged[sid]) {
                    merged[sid] = localCreds;
                } else {
                    localCreds.forEach(lc => {
                        if (!merged[sid].some(c => c.player_id === lc.player_id)) {
                            merged[sid].push(lc);
                        }
                    });
                }
            });
            return merged;
        });
    }, [sessions]);

    // Group players by session — merge from both /api/admin/players AND session.registered_players
    const playersBySession = {};
    const trueOrphans = [];
    const sessionIds = new Set(sessions.map(s => s.session_id));
    
    // First, categorize fetched players
    players.forEach(player => {
        if (player.is_orphan) {
            trueOrphans.push(player);
        } else if (sessionIds.has(player.session_id)) {
            if (!playersBySession[player.session_id]) playersBySession[player.session_id] = [];
            playersBySession[player.session_id].push(player);
        }
        // Valid players from OTHER facilitators are simply ignored (they aren't orphans, but aren't ours)
    });
    
    // Then, merge any session-level registered_players not already in the list
    // and enrich names from player sub-session data (cohort_name = "Player (username)")
    sessions.forEach(session => {
        const existing = playersBySession[session.session_id] || [];
        const existingIds = new Set(existing.map(p => p.player_id));
        (session.registered_players || []).forEach(rp => {
            if (!existingIds.has(rp.player_id)) {
                existing.push(rp);
                existingIds.add(rp.player_id);
            }
        });
        // Enrich names: if any existing player still has empty name, look for username
        existing.forEach(p => {
            if (!p.name && (p.username || p.player_name)) {
                p.name = p.username || p.player_name;
            }
        });
        if (existing.length > 0) playersBySession[session.session_id] = existing;
    });

    const handleTogglePublic = async (sessionId, currentStatus) => {
        const newStatus = !currentStatus;
        setSessions(prev => prev.map(s =>
            s.session_id === sessionId ? { ...s, is_public: newStatus } : s
        ));
        try {
            await fetch(`${API}/api/admin/${sessionId}/public-status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ is_public: newStatus })
            });
        } catch (e) {
            setSessions(prev => prev.map(s =>
                s.session_id === sessionId ? { ...s, is_public: currentStatus } : s
            ));
        }
    };

    const handleGenerateId = async (sessionId) => {
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/generate-player`, { method: 'POST', credentials: 'include' });
            if (!res.ok) {
                const errText = await res.text();
                alert(`Failed to generate player: ${res.status} — ${errText}`);
                return;
            }
            const data = await res.json();
            const playerId = data.player_id;
            if (!playerId) return;

            // Server always returns the password now (random temp password generated server-side)
            const password = data.password;
            if (!password) {
                console.warn('[PlayerRegistry] generate-player did not return a password — player may not be able to log in.');
            }

            setSessions(prev => prev.map(s =>
                s.session_id === sessionId
                    ? { ...s, allowed_player_ids: [...(s.allowed_player_ids || []), playerId] }
                    : s
            ));

            setGeneratedCreds(prev => ({
                ...prev,
                [sessionId]: [...(prev[sessionId] || []), { player_id: playerId, password: password || '(generating...)' }]
            }));
        } catch (e) {
            console.error('Failed to generate Player ID:', e);
        }
    };

    const handleResetPassword = async (playerId, sessionId) => {
        if (!confirm(`Reset password for ${playerId}? A new random password will be generated. You must share it with the player.`)) return;
        try {
            const res = await fetch(`${API}/api/admin/players/${playerId}/reset-password`, {
                method: 'POST',
                credentials: 'include',
            });
            if (!res.ok) {
                const errText = await res.text();
                alert(`Failed to reset password: ${res.status} — ${errText}`);
                return;
            }
            const data = await res.json();
            const newPassword = data.new_password;
            // Update displayed credentials
            setGeneratedCreds(prev => {
                const sessId = sessionId;
                const existing = prev[sessId] || [];
                const updated = existing.map(c =>
                    c.player_id === playerId ? { ...c, password: newPassword } : c
                );
                // If not found in existing creds, add it
                if (!updated.some(c => c.player_id === playerId)) {
                    updated.push({ player_id: playerId, password: newPassword });
                }
                return { ...prev, [sessId]: updated };
            });
            // Auto-copy to clipboard
            copyToClipboard(newPassword);
            // Show inline toast with copiable password
            clearTimeout(resetToastTimerRef.current);
            setResetToast({ playerId, password: newPassword });
            resetToastTimerRef.current = setTimeout(() => setResetToast(null), 15000);
        } catch (e) {
            console.error('Failed to reset password:', e);
            alert('Failed to reset password. Please try again.');
        }
    };


    const handleDeletePlayer = async (playerId) => {
        if (!confirm(`Remove player ${playerId}?`)) return;
        try {
            await fetch(`${API}/api/admin/players/${playerId}`, { method: 'DELETE', credentials: 'include' });
            setPlayers(prev => prev.filter(p => p.player_id !== playerId));
        } catch (e) {
            console.error('Failed to remove player:', e);
        }
    };

    const handleDeleteSession = async (sessionId) => {
        if (!confirm('Delete this entire cohort and all its players? This cannot be undone.')) return;
        try {
            await fetch(`${API}/api/admin/sessions/${sessionId}`, { method: 'DELETE', credentials: 'include' });
            setSessions(prev => prev.filter(s => s.session_id !== sessionId));
            setPlayers(prev => prev.filter(p => p.session_id !== sessionId));
            setGeneratedCreds(prev => { const copy = { ...prev }; delete copy[sessionId]; return copy; });
        } catch (e) {
            console.error('Failed to delete session:', e);
        }
    };

    const handleClearOrphans = async () => {
        if (!confirm('Remove all orphaned players?')) return;
        try {
            await fetch(`${API}/api/admin/players/orphans`, { method: 'DELETE', credentials: 'include' });
            await fetchPlayers();
        } catch (e) {
            console.error('Failed to clear orphans:', e);
        }
    };

    return (
        <>
        <section className={styles.panel}>
            <div className={styles.header}>
                <div className={styles.titleRow}>
                    <span className={styles.icon}>👥</span>
                    <h2>Active Player Roster</h2>
                </div>
                <div className={styles.stats}>
                    <span className={styles.statBadge}>{players.length} Total Registered</span>
                </div>
            </div>

            {/* Password reset toast */}
            {resetToast && (
                <div style={{
                    background: 'linear-gradient(135deg, rgba(16,185,129,0.12) 0%, rgba(5,150,105,0.08) 100%)',
                    border: '1px solid rgba(16,185,129,0.35)',
                    borderRadius: '10px',
                    padding: '0.75rem 1rem',
                    margin: '0.75rem 1rem 0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    flexWrap: 'wrap',
                    animation: 'fadeIn 0.25s ease',
                }}>
                    <span style={{ fontSize: '1.2rem' }}>✅</span>
                    <div style={{ flex: 1, minWidth: '200px' }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#34d399', marginBottom: '2px' }}>
                            Password reset for {resetToast.playerId}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                            New password (copied to clipboard):
                        </div>
                    </div>
                    <span
                        style={{
                            fontFamily: 'monospace',
                            fontSize: '1.05rem',
                            fontWeight: 800,
                            color: '#fcd34d',
                            background: 'rgba(15,23,42,0.6)',
                            padding: '6px 14px',
                            borderRadius: '6px',
                            border: '1px solid rgba(245,158,11,0.3)',
                            letterSpacing: '0.08em',
                            userSelect: 'all',
                            cursor: 'text',
                        }}
                        title="Click to select, then Ctrl+C to copy"
                    >
                        {resetToast.password}
                    </span>
                    <button
                        onClick={() => {
                            copyToClipboard(resetToast.password);
                            // Brief visual feedback
                            const btn = document.activeElement;
                            if (btn) { btn.textContent = '✓ Copied!'; setTimeout(() => { btn.textContent = '📋 Copy'; }, 1200); }
                        }}
                        style={{
                            background: 'rgba(99,102,241,0.15)',
                            border: '1px solid rgba(99,102,241,0.3)',
                            borderRadius: '6px', cursor: 'pointer',
                            padding: '5px 12px', fontSize: '0.75rem',
                            fontWeight: 600, color: '#a5b4fc', whiteSpace: 'nowrap',
                            transition: 'all 0.15s ease',
                        }}
                    >📋 Copy</button>
                    <button
                        onClick={() => { clearTimeout(resetToastTimerRef.current); setResetToast(null); }}
                        style={{
                            background: 'none', border: 'none',
                            color: '#64748b', cursor: 'pointer',
                            fontSize: '1.1rem', padding: '2px 4px', lineHeight: 1,
                        }}
                        title="Dismiss"
                    >×</button>
                </div>
            )}

            {loading ? (
                <div className={styles.loading}>Loading player database...</div>
            ) : sessions.length === 0 ? (
                <div className={styles.empty}>No cohorts found. Create one from the Leaderboard tab!</div>
            ) : (
                <div className={styles.body}>
                    {sessions.map(session => {
                        const sessionPlayers = playersBySession[session.session_id] || [];
                        const isPublic = session.is_public;
                        const allowedIds = session.allowed_player_ids || [];
                        const creds = generatedCreds[session.session_id] || [];

                        return (
                            <div key={session.session_id} className={styles.sessionGroup}>
                                <div className={styles.sessionHeader}>
                                    <div>
                                        <h3
                                            style={canSeeSummaryTooltip ? { cursor: 'help', display: 'inline-flex', alignItems: 'center', gap: '4px' } : undefined}
                                            onMouseEnter={canSeeSummaryTooltip ? (e) => {
                                                clearTimeout(hoverTimerRef.current);
                                                const rect = e.currentTarget.getBoundingClientRect();
                                                hoverTimerRef.current = setTimeout(() => {
                                                    setHoverAnchorRect(rect);
                                                    setHoveredSession(session);
                                                }, 220);
                                            } : undefined}
                                            onMouseLeave={canSeeSummaryTooltip ? () => {
                                                clearTimeout(hoverTimerRef.current);
                                                hoverTimerRef.current = setTimeout(() => setHoveredSession(null), 120);
                                            } : undefined}
                                        >
                                            {session.cohort_name}
                                            <span>({session.short_code || session.session_id.slice(0, 8)})</span>
                                            {canSeeSummaryTooltip && (
                                                <span style={{
                                                    fontSize: '0.6rem', fontWeight: 400,
                                                    color: 'var(--text-muted)', opacity: 0.55,
                                                }}>ⓘ</span>
                                            )}
                                        </h3>
                                        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
                                            <span style={{
                                                fontSize: '0.72rem', fontWeight: 700,
                                                background: 'rgba(99,102,241,0.15)',
                                                padding: '3px 9px', borderRadius: '6px',
                                                color: '#a5b4fc',
                                                border: '1px solid rgba(99,102,241,0.25)',
                                            }} title="Active Simulation Edition">
                                                {(() => {
                                                                                    const pd = session.decision_paradigm || 'legacy_abc';
                                                    if (pd === 'legacy_abc') return '🏭 Legacy (Mfg)';
                                                    if (pd === 'healthcare') return '🏥 Healthcare';
                                                    if (pd === 'un_sdg') return '🌍 UN SDG';
                                                    if (pd === 'multi_toggles') return '🎛️ Strategic Pillars';
                                                    if (pd === 'defense') return '🚀 Defense/Aero';
                                                    if (pd === 'brsr_ngrbc') return '🇮🇳 BRSR NGRBC';
                                                    return pd;
                                                })()}
                                            </span>
                                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.85rem' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={!!isPublic}
                                                    onChange={() => handleTogglePublic(session.session_id, isPublic)}
                                                />
                                                <span style={{ color: isPublic ? 'var(--gauge-green)' : 'var(--text-muted)' }}>
                                                    {isPublic ? '🌍 Publicly Joinable' : '🔒 Private / Hidden'}
                                                </span>
                                            </label>
                                            {/* Denominator is the cohort's configured cap, not a
                                                literal — a cohort set to 12 must not read "/20". */}
                                            <span className={styles.playerCount}>
                                                {sessionPlayers.length}/{session.max_players || 20} Inducted
                                            </span>
                                        </div>
                                    </div>

                                    <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end' }}>
                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <button
                                                className={styles.inductBtn}
                                                onClick={() => handleGenerateId(session.session_id)}
                                            >
                                                + Generate Player ID
                                            </button>
                                            <button
                                                className={styles.inductBtn}
                                                onClick={() => setBulkFor({
                                                    sessionId: session.session_id,
                                                    cohortName: session.cohort_name,
                                                    // A first-frame hint only. The modal fetches the
                                                    // authoritative shape from the server, which is
                                                    // the same object that builds the template and
                                                    // gates the upload.
                                                    shapeHint: {
                                                        mode: session.simulation_mode === 'single_bu'
                                                            ? 'single_bu' : 'conglomerate',
                                                        per_player_scope: session.simulation_mode === 'single_bu',
                                                        columns: session.simulation_mode === 'single_bu'
                                                            ? ['name', 'email', 'programme', 'industry_vertical', 'region_id']
                                                            : ['name', 'email', 'programme'],
                                                        cohort: {
                                                            cohort_name: session.cohort_name,
                                                            industry_vertical: session.industry_vertical || '',
                                                            region_id: session.region_id || '',
                                                        },
                                                    },
                                                })}
                                                title="Create many players at once from an Excel file"
                                            >
                                                📥 Bulk Upload
                                            </button>
                                            {/* ✏️ Edit Cohort — lead_facilitator / super_admin, zero players, pre-game only */}
                                            {isLeadOrAdmin && (!session.round_number || session.round_number <= 1) && (allowedIds.length === 0) && onEditCohort && (
                                                <button
                                                    onClick={() => onEditCohort(session)}
                                                    style={{
                                                        background: 'rgba(59,130,246,0.10)',
                                                        border: '1px solid rgba(59,130,246,0.35)',
                                                        color: '#60a5fa',
                                                        borderRadius: '6px',
                                                        padding: '0.4rem 0.85rem',
                                                        cursor: 'pointer',
                                                        fontSize: '0.72rem',
                                                        fontWeight: 700,
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: '4px',
                                                        transition: 'background 0.15s, border-color 0.15s',
                                                    }}
                                                    onMouseEnter={e => { e.currentTarget.style.background = 'rgba(59,130,246,0.2)'; e.currentTarget.style.borderColor = 'rgba(59,130,246,0.6)'; }}
                                                    onMouseLeave={e => { e.currentTarget.style.background = 'rgba(59,130,246,0.10)'; e.currentTarget.style.borderColor = 'rgba(59,130,246,0.35)'; }}
                                                    data-tooltip="Edit cohort settings (only available before game starts and before any players are inducted)"
                                                    title=""
                                                >
                                                    ✏️ Edit Cohort
                                                </button>
                                            )}
                                            {isSuperAdmin && (
                                                <button
                                                    onClick={() => handleDeleteSession(session.session_id)}
                                                    style={{
                                                        background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',
                                                        color: '#f87171', borderRadius: '6px', padding: '0.4rem 0.8rem',
                                                        cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600,
                                                    }}
                                                    title="Delete this cohort"
                                                >
                                                    🗑️ Delete Cohort
                                                </button>
                                             )}
                                        </div>

                                        {/* Generated credentials */}
                                        <div style={{ fontSize: '0.8rem', maxWidth: '450px', display: 'flex', flexDirection: 'column', gap: '6px', alignItems: 'flex-end' }}>
                                            {creds.length > 0 ? (
                                                creds.map(cred => (
                                                    <div key={cred.player_id} style={{
                                                        display: 'flex', gap: '8px', alignItems: 'center',
                                                        background: 'rgba(15,23,42,0.55)',
                                                        border: '1px solid rgba(148,163,184,0.15)',
                                                        borderRadius: '8px', padding: '6px 10px',
                                                    }}>
                                                        <span style={{
                                                            fontWeight: 700, fontSize: '0.82rem',
                                                            color: '#a5b4fc',
                                                            background: 'rgba(99,102,241,0.15)',
                                                            padding: '2px 8px', borderRadius: '4px',
                                                            border: '1px solid rgba(99,102,241,0.25)',
                                                            fontFamily: 'monospace',
                                                        }}>
                                                            {cred.player_id}
                                                        </span>
                                                        <span style={{
                                                            fontFamily: 'monospace', fontSize: '0.82rem', fontWeight: 700,
                                                            color: '#fcd34d',
                                                            background: 'rgba(245,158,11,0.12)',
                                                            padding: '2px 8px', borderRadius: '4px',
                                                            border: '1px solid rgba(245,158,11,0.25)',
                                                            whiteSpace: 'nowrap',
                                                        }}>
                                                            🔑 {cred.password
                                                                || (cred.pending ? '— (reset to reveal)' : '— (player has set their own)')}
                                                        </span>
                                                        {cred.pending && (
                                                            <span style={{
                                                                fontSize: '0.62rem', fontWeight: 700,
                                                                color: '#fb923c',
                                                                background: 'rgba(251,146,60,0.1)',
                                                                border: '1px solid rgba(251,146,60,0.25)',
                                                                borderRadius: '4px', padding: '1px 5px',
                                                                letterSpacing: '0.04em',
                                                            }}
                                                            title="Player has not yet set a personal password">
                                                                DEFAULT
                                                            </span>
                                                        )}
                                                        <button
                                                            style={{
                                                                background: 'rgba(148,163,184,0.1)',
                                                                border: '1px solid rgba(148,163,184,0.2)',
                                                                borderRadius: '4px', cursor: 'pointer',
                                                                padding: '4px 8px', fontSize: '0.72rem',
                                                                fontWeight: 600, color: '#94a3b8', whiteSpace: 'nowrap',
                                                            }}
                                                            onClick={() => {
                                                                const text = cred.password;
                                                                if (navigator.clipboard?.writeText) {
                                                                    navigator.clipboard.writeText(text).catch(() => {
                                                                        // Fallback for non-secure contexts
                                                                        const ta = document.createElement('textarea');
                                                                        ta.value = text;
                                                                        ta.style.position = 'fixed';
                                                                        ta.style.opacity = '0';
                                                                        document.body.appendChild(ta);
                                                                        ta.select();
                                                                        document.execCommand('copy');
                                                                        document.body.removeChild(ta);
                                                                    });
                                                                } else {
                                                                    const ta = document.createElement('textarea');
                                                                    ta.value = text;
                                                                    ta.style.position = 'fixed';
                                                                    ta.style.opacity = '0';
                                                                    document.body.appendChild(ta);
                                                                    ta.select();
                                                                    document.execCommand('copy');
                                                                    document.body.removeChild(ta);
                                                                }
                                                                alert('Copied to clipboard!');
                                                            }}
                                                        >📋 Copy</button>
                                                        {/* Reset Password button — shown for all entries; especially useful when password is unknown */}
                                                        <button
                                                            style={{
                                                                background: 'rgba(239,68,68,0.1)',
                                                                border: '1px solid rgba(239,68,68,0.25)',
                                                                borderRadius: '4px', cursor: 'pointer',
                                                                padding: '4px 8px', fontSize: '0.72rem',
                                                                fontWeight: 600, color: '#f87171', whiteSpace: 'nowrap',
                                                            }}
                                                            onClick={() => handleResetPassword(cred.player_id, session.session_id)}
                                                            title="Generate a new random password for this player"
                                                        >🔄 Reset</button>
                                                        <button
                                                            style={{
                                                                background: 'rgba(99,102,241,0.12)',
                                                                border: '1px solid rgba(99,102,241,0.25)',
                                                                borderRadius: '4px', cursor: 'pointer',
                                                                padding: '4px 8px', fontSize: '0.72rem',
                                                                fontWeight: 700, color: '#a5b4fc', whiteSpace: 'nowrap',
                                                            }}
                                                            onClick={() => {
                                                                // Find the player's child session and open it
                                                                fetch(`${API}/api/admin/${session.session_id}/player-sessions`, { credentials: 'include' })
                                                                    .then(r => r.json())
                                                                    .then(data => {
                                                                        const match = (data.players || []).find(p => p.player_id === cred.player_id);
                                                                        if (match) {
                                                                            window.open(`/?session=${match.session_id}&impersonate=true`, '_blank');
                                                                        } else {
                                                                            alert(`No active session found for ${cred.player_id}. Player may not have logged in yet.`);
                                                                        }
                                                                    })
                                                                    .catch(() => alert('Failed to fetch player session'));
                                                            }}
                                                            title={`View the game as ${cred.player_id}`}
                                                        >👁️ View</button>
                                                    </div>
                                                ))
                                            ) : allowedIds.length === 0 ? (
                                                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>No IDs generated yet</span>
                                            ) : allowedIds.map(id => (
                                                <span key={id} style={{
                                                    background: 'var(--bg-elevated)', padding: '2px 6px', borderRadius: '4px',
                                                    border: '1px solid var(--border-color)', fontSize: '0.75rem',
                                                }}>
                                                    {id}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* Player table */}
                                {sessionPlayers.length > 0 && (
                                    <div className={styles.tableWrapper}>
                                        <table className={styles.table}>
                                            <thead>
                                                <tr>
                                                    <th>Name / Call Sign</th>
                                                    <th>Player ID</th>
                                                    <th>Programme</th>
                                                    <th>Assigned BU</th>
                                                    <th style={{ textAlign: 'right' }}>Joined At</th>
                                                    <th style={{ textAlign: 'center', minWidth: '120px' }}>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {sessionPlayers.map(p => (
                                                    <tr key={p.player_id}>
                                                        <td className={styles.nameCell}>
                                                            <strong>{p.name || p.username || p.player_name || p.player_id}</strong>
                                                            {p.email && <><br /><span className={styles.emailText}>{p.email}</span></>}
                                                        </td>
                                                        <td>
                                                            <span style={{
                                                                fontFamily: 'monospace', fontWeight: 700,
                                                                fontSize: '0.78rem', color: '#a5b4fc',
                                                            }}>
                                                                {p.player_id}
                                                            </span>
                                                        </td>
                                                        {/* Programme is optional by design — an open-enrolment
                                                            cohort has none, so an em-dash is a valid state. */}
                                                        <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                                            {p.programme || '—'}
                                                        </td>
                                                        <td>
                                                            {(() => {
                                                            // What this player actually runs.
                                                            //
                                                            // The PLAYER's own industry_vertical comes
                                                            // first, because in single-business mode
                                                            // players can run different companies —
                                                            // falling straight through to the cohort's
                                                            // vertical would show every player the
                                                            // same business and hide exactly the
                                                            // variation the roster set up. assigned_bu
                                                            // is only the seed SLOT, so two rivals in
                                                            // (say) oil & gas and cosmetics would both
                                                            // read "Pharma".
                                                            const bu = p.industry_vertical
                                                                || p.assigned_bu
                                                                || (session.simulation_mode === 'single_bu' ? (session.industry_vertical || 'Single BU') : '');
                                                            if (bu) {
                                                                return (
                                                                    <span className={`${styles.buBadge} ${styles['bu_' + bu.toLowerCase()]}`}>
                                                                        {resolveVerticalMeta(bu).icon} {resolveVerticalMeta(bu).label}
                                                                    </span>
                                                                );
                                                            }
                                                            return '—';
                                                        })()}
                                                        </td>
                                                        <td style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                            {p.created_at ? new Date(p.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
                                                        </td>
                                                        <td style={{ textAlign: 'center' }}>
                                                            <div style={{ display: 'flex', gap: '6px', justifyContent: 'center', alignItems: 'center' }}>
                                                                <button
                                                                    onClick={() => handleResetPassword(p.player_id, session.session_id)}
                                                                    style={{
                                                                        background: 'rgba(245,158,11,0.1)',
                                                                        border: '1px solid rgba(245,158,11,0.3)',
                                                                        borderRadius: '5px', cursor: 'pointer',
                                                                        padding: '3px 8px', fontSize: '0.7rem',
                                                                        fontWeight: 600, color: '#fbbf24', whiteSpace: 'nowrap',
                                                                        transition: 'all 0.15s ease',
                                                                    }}
                                                                    onMouseEnter={e => { e.currentTarget.style.background = 'rgba(245,158,11,0.2)'; e.currentTarget.style.borderColor = 'rgba(245,158,11,0.5)'; }}
                                                                    onMouseLeave={e => { e.currentTarget.style.background = 'rgba(245,158,11,0.1)'; e.currentTarget.style.borderColor = 'rgba(245,158,11,0.3)'; }}
                                                                    title={`Reset password for ${p.player_id} — generates a new random password`}
                                                                >🔄 Reset Pwd</button>
                                                                <button
                                                                    onClick={() => handleDeletePlayer(p.player_id)}
                                                                    style={{
                                                                        background: 'none', border: 'none', color: '#ef4444',
                                                                        cursor: 'pointer', fontSize: '1rem', padding: '2px',
                                                                    }}
                                                                    title={`Remove ${p.name || p.player_id}`}
                                                                >✕</button>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        );
                    })}

                    {/* Orphan section */}
                    {trueOrphans.length > 0 && (
                        <div className={styles.sessionGroup} style={{ borderColor: '#fca5a5' }}>
                            <div className={styles.sessionHeader}>
                                <div>
                                    <h3 style={{ color: '#ef4444' }}>⚠️ Orphaned Players ({trueOrphans.length})</h3>
                                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0.25rem 0 0' }}>
                                        Players from deleted sessions
                                    </p>
                                </div>
                                {/* DELETE /players/orphans is super_admin-only — showing this
                                    button to facilitators produced a silent 403 (audit finding). */}
                                {isSuperAdmin && (
                                <button onClick={handleClearOrphans} style={{
                                    background: '#ef4444', color: '#fff', border: 'none',
                                    borderRadius: '6px', padding: '0.5rem 1rem', cursor: 'pointer',
                                    fontWeight: 600, fontSize: '0.8rem',
                                }}>🗑️ Clear All Orphans</button>
                                )}
                            </div>
                            <div className={styles.tableWrapper}>
                                <table className={styles.table}>
                                    <tbody>
                                        {trueOrphans.map(p => (
                                                <tr key={p.player_id}>
                                                    <td><strong>{p.name || '—'}</strong></td>
                                                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{p.player_id}</td>
                                                    <td style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{getShortCode(p.session_id, sessions)}</td>
                                                    <td>
                                                        <button
                                                            onClick={() => handleDeletePlayer(p.player_id)}
                                                            style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1rem' }}
                                                        >✕</button>
                                                    </td>
                                                </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </section>
        {/* Cohort Summary Tooltip — portal renders at document.body */}
        {canSeeSummaryTooltip && (
            <CohortSummaryTooltip
                session={hoveredSession}
                anchorRect={hoverAnchorRect}
                visible={!!hoveredSession}
            />
        )}
        {/* Bulk player upload — OverlayHost slot, summoned from the cohort header */}
        {bulkFor && (
            <BulkPlayerUpload
                mode="cohort"
                sessionId={bulkFor.sessionId}
                cohortName={bulkFor.cohortName}
                shapeHint={bulkFor.shapeHint}
                onClose={() => setBulkFor(null)}
                onDone={(payload) => {
                    // Surface the new credentials immediately rather than waiting
                    // for the next leaderboard poll — the facilitator is usually
                    // distributing them in the room right now.
                    const sid = bulkFor.sessionId;
                    setGeneratedCreds(prev => ({
                        ...prev,
                        [sid]: [
                            ...(prev[sid] || []),
                            ...(payload.created || []).map(c => ({
                                player_id: c.player_id,
                                password: c.temp_password,
                                pending: true,
                            })),
                        ],
                    }));
                    setSessions(prev => prev.map(s => s.session_id === sid ? {
                        ...s,
                        allowed_player_ids: [
                            ...(s.allowed_player_ids || []),
                            ...(payload.created || []).map(c => c.player_id),
                        ],
                    } : s));
                    fetchPlayers();
                }}
            />
        )}
    </>
    );
}
