import React, { useState, useEffect, useCallback } from 'react';
import styles from './PlayerRegistry.module.css';

const ADJECTIVES = ["blue", "swift", "brave", "quiet", "lucky", "bold", "calm", "proud", "wild", "smart"];
const NOUNS = ["rhino", "eagle", "tiger", "panda", "fox", "bear", "wolf", "lion", "hawk", "owl"];

function generatePassword() {
    return '123';
}

export default function PlayerRegistry({ leaderboard }) {
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sessions, setSessions] = useState([]);
    // Generated credentials: { sessionId: [{player_id, password}, ...] }
    const [generatedCreds, setGeneratedCreds] = useState({});
    const API = process.env.NEXT_PUBLIC_API_URL || '';

    useEffect(() => {
        if (leaderboard && leaderboard.length > 0) {
            setSessions(leaderboard);
        }
    }, [leaderboard]);

    const fetchPlayers = useCallback(async () => {
        try {
            const res = await fetch(`${API}/api/admin/players`);
            if (res.ok) {
                const data = await res.json();
                setPlayers(data.players || []);
            }
        } catch (err) {
            console.error("Failed to fetch players:", err);
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
            // Build from registered_players (has password)
            regPlayers.forEach(rp => {
                if (rp.player_id && !creds.some(c => c.player_id === rp.player_id)) {
                    creds.push({ player_id: rp.player_id, password: rp.password || '123' });
                }
            });
            // Also include allowed_player_ids that aren't in registered_players
            allowedIds.forEach(pid => {
                if (!creds.some(c => c.player_id === pid)) {
                    creds.push({ player_id: pid, password: '123' });
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
    // First, add from fetched players
    players.forEach(player => {
        if (!playersBySession[player.session_id]) playersBySession[player.session_id] = [];
        playersBySession[player.session_id].push(player);
    });
    // Then, merge any session-level registered_players not already in the list
    sessions.forEach(session => {
        const existing = playersBySession[session.session_id] || [];
        const existingIds = new Set(existing.map(p => p.player_id));
        (session.registered_players || []).forEach(rp => {
            if (!existingIds.has(rp.player_id)) {
                existing.push(rp);
                existingIds.add(rp.player_id);
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
            const res = await fetch(`${API}/api/admin/${sessionId}/generate-player`, { method: 'POST' });
            if (!res.ok) {
                const errText = await res.text();
                alert(`Failed to generate player: ${res.status} — ${errText}`);
                return;
            }
            const data = await res.json();
            const playerId = data.player_id;
            if (!playerId) return;

            // Use server password if provided, otherwise generate client-side
            const password = data.password || generatePassword();

            // If server didn't return password, register it separately
            if (!data.password) {
                try {
                    // Save the client-generated password to the player registry
                    await fetch(`${API}/api/admin/players/set-password`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ player_id: playerId, password: password })
                    });
                } catch (e) { console.error('Failed to save password:', e); }
            }

            setSessions(prev => prev.map(s =>
                s.session_id === sessionId
                    ? { ...s, allowed_player_ids: [...(s.allowed_player_ids || []), playerId] }
                    : s
            ));

            setGeneratedCreds(prev => ({
                ...prev,
                [sessionId]: [...(prev[sessionId] || []), { player_id: playerId, password }]
            }));
        } catch (e) {
            console.error('Failed to generate Player ID:', e);
        }
    };

    const handleDeletePlayer = async (playerId) => {
        if (!confirm(`Remove player ${playerId}?`)) return;
        try {
            await fetch(`${API}/api/admin/players/${playerId}`, { method: 'DELETE' });
            setPlayers(prev => prev.filter(p => p.player_id !== playerId));
        } catch (e) {
            console.error('Failed to remove player:', e);
        }
    };

    const handleDeleteSession = async (sessionId) => {
        if (!confirm('Delete this entire cohort and all its players? This cannot be undone.')) return;
        try {
            await fetch(`${API}/api/admin/sessions/${sessionId}`, { method: 'DELETE' });
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
            await fetch(`${API}/api/admin/players/orphans`, { method: 'DELETE' });
            await fetchPlayers();
        } catch (e) {
            console.error('Failed to clear orphans:', e);
        }
    };

    // Find orphan session IDs
    const sessionIds = new Set(sessions.map(s => s.session_id));
    const orphanSessionIds = Object.keys(playersBySession).filter(sid => !sessionIds.has(sid));
    const totalOrphans = orphanSessionIds.reduce((sum, sid) => sum + playersBySession[sid].length, 0);


    return (
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
                                        <h3>{session.cohort_name} <span>({session.session_id.slice(0, 8)})</span></h3>
                                        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', alignItems: 'center' }}>
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
                                            <span className={styles.playerCount}>{sessionPlayers.length}/5 Inducted</span>
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
                                                onClick={() => handleDeleteSession(session.session_id)}
                                                style={{
                                                    background: 'none', border: '1px solid #fca5a5', color: '#ef4444',
                                                    borderRadius: '6px', padding: '0.4rem 0.8rem', cursor: 'pointer',
                                                    fontSize: '0.75rem', fontWeight: 500,
                                                }}
                                                title="Delete this cohort"
                                            >
                                                🗑️ Delete Cohort
                                            </button>
                                        </div>

                                        {/* Generated credentials */}
                                        <div style={{ fontSize: '0.8rem', maxWidth: '450px', display: 'flex', flexDirection: 'column', gap: '6px', alignItems: 'flex-end' }}>
                                            {creds.length > 0 ? (
                                                creds.map(cred => (
                                                    <div key={cred.player_id} style={{
                                                        display: 'flex', gap: '8px', alignItems: 'center',
                                                        background: '#f8fafc', border: '1px solid #e2e8f0',
                                                        borderRadius: '8px', padding: '6px 10px',
                                                    }}>
                                                        <span style={{
                                                            fontWeight: 700, fontSize: '0.85rem', color: '#1e293b',
                                                            background: '#eef2ff', padding: '2px 8px', borderRadius: '4px',
                                                            border: '1px solid #c7d2fe',
                                                        }}>
                                                            {cred.player_id}
                                                        </span>
                                                        <span style={{
                                                            fontFamily: 'monospace', fontSize: '0.85rem', fontWeight: 700,
                                                            color: '#b45309', background: '#fef3c7', padding: '2px 8px',
                                                            borderRadius: '4px', border: '1px solid #fcd34d',
                                                            whiteSpace: 'nowrap',
                                                        }}>
                                                            🔑 {cred.password}
                                                        </span>
                                                        <button
                                                            style={{
                                                                background: '#e2e8f0', border: 'none', borderRadius: '4px',
                                                                cursor: 'pointer', padding: '4px 8px', fontSize: '0.75rem',
                                                                fontWeight: 600, color: '#475569', whiteSpace: 'nowrap',
                                                            }}
                                                            onClick={() => {
                                                                const text = `Player ID: ${cred.player_id}\nPassword: ${cred.password}`;
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
                                                        <button
                                                            style={{
                                                                background: '#eef2ff', border: '1px solid #c7d2fe',
                                                                borderRadius: '4px', cursor: 'pointer',
                                                                padding: '4px 8px', fontSize: '0.75rem',
                                                                fontWeight: 600, color: '#4338ca', whiteSpace: 'nowrap',
                                                            }}
                                                            onClick={() => {
                                                                // Find the player's child session and open it
                                                                fetch(`${API}/api/admin/${session.session_id}/player-sessions`)
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
                                                    <th>Assigned BU</th>
                                                    <th style={{ textAlign: 'right' }}>Joined At</th>
                                                    <th style={{ width: '40px' }}></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {sessionPlayers.map(p => (
                                                    <tr key={p.player_id}>
                                                        <td className={styles.nameCell}>
                                                            <strong>{p.name || '—'}</strong>
                                                            {p.email && <><br /><span className={styles.emailText}>{p.email}</span></>}
                                                        </td>
                                                        <td>
                                                            <span style={{
                                                                fontFamily: 'monospace', fontWeight: 600,
                                                                fontSize: '0.8rem', color: '#4338ca',
                                                            }}>
                                                                {p.player_id}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            {p.assigned_bu ? (
                                                                <span className={`${styles.buBadge} ${styles['bu_' + (p.assigned_bu || '').toLowerCase()]}`}>
                                                                    {p.assigned_bu}
                                                                </span>
                                                            ) : '—'}
                                                        </td>
                                                        <td style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                            {p.created_at ? new Date(p.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
                                                        </td>
                                                        <td>
                                                            <button
                                                                onClick={() => handleDeletePlayer(p.player_id)}
                                                                style={{
                                                                    background: 'none', border: 'none', color: '#ef4444',
                                                                    cursor: 'pointer', fontSize: '1rem', padding: '2px',
                                                                }}
                                                                title={`Remove ${p.name || p.player_id}`}
                                                            >✕</button>
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
                    {orphanSessionIds.length > 0 && (
                        <div className={styles.sessionGroup} style={{ borderColor: '#fca5a5' }}>
                            <div className={styles.sessionHeader}>
                                <div>
                                    <h3 style={{ color: '#ef4444' }}>⚠️ Orphaned Players ({totalOrphans})</h3>
                                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0.25rem 0 0' }}>
                                        Players from deleted sessions
                                    </p>
                                </div>
                                <button onClick={handleClearOrphans} style={{
                                    background: '#ef4444', color: '#fff', border: 'none',
                                    borderRadius: '6px', padding: '0.5rem 1rem', cursor: 'pointer',
                                    fontWeight: 600, fontSize: '0.8rem',
                                }}>🗑️ Clear All Orphans</button>
                            </div>
                            <div className={styles.tableWrapper}>
                                <table className={styles.table}>
                                    <tbody>
                                        {orphanSessionIds.flatMap(sid =>
                                            playersBySession[sid].map(p => (
                                                <tr key={p.player_id}>
                                                    <td><strong>{p.name || '—'}</strong></td>
                                                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{p.player_id}</td>
                                                    <td style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{sid.slice(0, 8)}</td>
                                                    <td>
                                                        <button
                                                            onClick={() => handleDeletePlayer(p.player_id)}
                                                            style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1rem' }}
                                                        >✕</button>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </section>
    );
}
