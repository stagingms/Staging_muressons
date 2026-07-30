'use client';
import { useState, useEffect } from 'react';
import styles from './AnalyticsControlPanel.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// Railway audit §4.3: the card list lives in the shared analytics registry —
// one place to add a card, one tooltip wording for both surfaces. The
// FACILITATOR_ANALYTICS name is re-exported for existing importers.
import { ANALYTICS_CARDS } from '../config/analyticsRegistry';
export const FACILITATOR_ANALYTICS = ANALYTICS_CARDS;
import { PLAYER_VISIBILITY_CARDS, PLAYER_VISIBILITY_DEFAULTS, playerVisibilityGroups } from '../config/playerVisibilityRegistry';

// Player catalog from the shared registry. This array used to hold THREE keys
// while the Create-Cohort form held nineteen, and DEFAULT_VIS below was built
// from it — so a save from this panel wrote a player map missing sixteen keys.
const PLAYER_ANALYTICS = PLAYER_VISIBILITY_CARDS;

// Player-facing round surfaces. These are cohort SETTINGS (not analytics
// visibility), so they persist to the per-cohort override layer via
// /player-feature-toggles and are read back cohort-effective from
// global-settings. Each cohort is independent; with no cohort selected the
// controls set the global default.
const PLAYER_FEATURES = [
    { key: 'consequence_map_enabled', label: 'Decision Consequence Map', icon: '🗺️', desc: "Results-view timeline linking each round's decisions to their downstream effects" },
    { key: 'board_room_moments_enabled', label: 'Board Room Moment', icon: '🏢', desc: 'Guided post-round reflection (Noticing → Making Sense → Working with Meaning)' },
];

export default function AnalyticsControlPanel({ sessionId }) {
    const [visibility, setVisibility] = useState(null);
    const [saving, setSaving] = useState(false);
    const [status, setStatus] = useState(null);
    // Player-facing round surfaces — cohort-effective, persisted separately
    // from analytics visibility (see PLAYER_FEATURES).
    const [features, setFeatures] = useState({ consequence_map_enabled: true, board_room_moments_enabled: true });

    useEffect(() => {
        const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
        fetch(`${API}/api/admin/global-settings${qs}`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : {})
            .then(d => setFeatures({
                consequence_map_enabled: d.consequence_map_enabled !== false,
                board_room_moments_enabled: d.board_room_moments_enabled !== false,
            }))
            .catch(() => {});
    }, [sessionId]);

    // ── Facilitator tools (per-cohort unlocks, super-admin-owned) ──
    // Custom Black Swan Injector: OFF by default; enabling it here lets the
    // cohort's lead facilitator use the injector tab for THIS cohort only.
    // Persists to the cohort-settings override layer.
    const [swanEnabled, setSwanEnabled] = useState(false);
    // Stakeholder Negotiation Rooms — per-cohort toggle, but only offered to
    // callers whose facilitator profile carries the super-admin-granted
    // capability (admins always). The server enforces the same rule on
    // cohort-settings AND on every player call; this just avoids showing a
    // control that would 403.
    const [negoEnabled, setNegoEnabled] = useState(false);
    const [negoStatus, setNegoStatus] = useState(null);
    const [negoCapable, setNegoCapable] = useState(false);
    useEffect(() => {
        try {
            const auth = JSON.parse(localStorage.getItem('godmode_auth') || localStorage.getItem('facilitator_auth') || '{}');
            const isAdmin = auth.is_admin === true || ['super_admin', 'god_mode', 'admin'].includes(auth.role);
            setNegoCapable(isAdmin || auth.negotiation_rooms_enabled === true);
        } catch { setNegoCapable(false); }
    }, []);
    useEffect(() => {
        const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
        fetch(`${API}/api/admin/global-settings${qs}`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : {})
            .then(d => setNegoEnabled(d.negotiation_rooms_enabled === true))
            .catch(() => {});
    }, [sessionId]);
    const toggleNego = async () => {
        if (!sessionId) { setNegoStatus('❌ Select a cohort first'); setTimeout(() => setNegoStatus(null), 3000); return; }
        const next = !negoEnabled;
        setNegoEnabled(next);
        try {
            const r = await fetch(`${API}/api/admin/sessions/${sessionId}/cohort-settings`, {
                method: 'PATCH', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ negotiation_rooms_enabled: next }),
            });
            if (!r.ok) {
                const err = await r.json().catch(() => ({}));
                setNegoEnabled(!next);
                setNegoStatus(`❌ ${err.detail || 'Save failed'}`);
            } else setNegoStatus(next ? '✅ Rooms open for this cohort' : '✅ Rooms closed for this cohort');
        } catch { setNegoEnabled(!next); setNegoStatus('❌ Connection error'); }
        setTimeout(() => setNegoStatus(null), 4500);
    };
    const [swanStatus, setSwanStatus] = useState(null);
    useEffect(() => {
        const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
        fetch(`${API}/api/admin/global-settings${qs}`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : {})
            .then(d => setSwanEnabled(d.custom_black_swan_enabled === true))
            .catch(() => {});
    }, [sessionId]);
    const toggleSwan = async () => {
        if (!sessionId) { setSwanStatus('❌ Select a cohort first'); setTimeout(() => setSwanStatus(null), 3000); return; }
        const next = !swanEnabled;
        setSwanEnabled(next); // optimistic
        try {
            const r = await fetch(`${API}/api/admin/sessions/${sessionId}/cohort-settings`, {
                method: 'PATCH', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ custom_black_swan_enabled: next }),
            });
            if (!r.ok) { setSwanEnabled(!next); setSwanStatus('❌ Save failed'); }
            else setSwanStatus(next ? '✅ Injector unlocked for this cohort' : '✅ Injector locked for this cohort');
        } catch { setSwanEnabled(!next); setSwanStatus('❌ Connection error'); }
        setTimeout(() => setSwanStatus(null), 3500);
    };

    // ── Briefing videos (per-cohort): URL pattern + per-round overrides ──
    const [videoBase, setVideoBase] = useState('');
    const [videoLines, setVideoLines] = useState('');   // "1 = https://…" per line
    const [videoStatus, setVideoStatus] = useState(null);
    useEffect(() => {
        const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
        fetch(`${API}/api/admin/global-settings${qs}`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : {})
            .then(d => {
                setVideoBase(d.briefing_video_base || '');
                const map = d.briefing_videos || {};
                setVideoLines(Object.entries(map).map(([k, v]) => `${k} = ${v}`).join('\n'));
            }).catch(() => {});
    }, [sessionId]);
    const saveVideos = async () => {
        if (!sessionId) { setVideoStatus('❌ Select a cohort first'); return; }
        const map = {};
        for (const line of videoLines.split('\n')) {
            const m = line.match(/^\s*(\d{1,2})\s*[=:]\s*(\S.*)$/);
            if (m) map[m[1]] = m[2].trim();
        }
        try {
            const r = await fetch(`${API}/api/admin/sessions/${sessionId}/briefing-videos`, {
                method: 'POST', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ briefing_video_base: videoBase.trim(), briefing_videos: map }),
            });
            setVideoStatus(r.ok ? '✅ Saved — players see Watch on their next briefing' : '❌ Save failed');
        } catch { setVideoStatus('❌ Connection error'); }
        setTimeout(() => setVideoStatus(null), 4000);
    };

    const toggleFeature = async (key) => {
        const next = !features[key];
        setFeatures(f => ({ ...f, [key]: next }));   // optimistic
        setSaving(true);
        try {
            const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
            const res = await fetch(`${API}/api/admin/player-feature-toggles${qs}`, {
                method: 'POST', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [key]: next }),
            });
            if (res.ok) {
                const d = await res.json();
                setFeatures(f => ({ ...f, [key]: d[key] !== false }));
                setStatus('✅ Saved'); setTimeout(() => setStatus(null), 2000);
            } else {
                setFeatures(f => ({ ...f, [key]: !next }));   // revert
            }
        } catch { setFeatures(f => ({ ...f, [key]: !next })); }
        setSaving(false);
    };

    const DEFAULT_VIS = {
        facilitator: Object.fromEntries(FACILITATOR_ANALYTICS.map(a => [a.key, true])),
        // Every key, with each card's own default — not a hand-written
        // exception for what_if_simulator over a three-key list.
        player: PLAYER_VISIBILITY_DEFAULTS,
    };

    useEffect(() => {
        const endpoint = sessionId 
            ? `${API}/api/admin/cohort/${sessionId}/analytics-visibility` 
            : `${API}/api/admin/god/analytics-visibility`;
            
        fetch(endpoint)
            .then(r => r.json())
            .then(d => {
                const data = sessionId ? (d.cohort_overrides || {}) : d;
                setVisibility({
                    facilitator: { ...DEFAULT_VIS.facilitator, ...(data.facilitator || {}) },
                    player: { ...DEFAULT_VIS.player, ...(data.player || {}) },
                });
            })
            .catch(() => setVisibility(DEFAULT_VIS));
    }, [sessionId]);

    const toggle = async (role, key) => {
        const updated = {
            ...visibility,
            [role]: { ...visibility[role], [key]: !visibility[role][key] }
        };
        setVisibility(updated);
        setSaving(true);
        try {
            const endpoint = sessionId 
                ? `${API}/api/admin/cohort/${sessionId}/analytics-visibility` 
                : `${API}/api/admin/god/analytics-visibility`;
                
            const res = await fetch(endpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updated),
            });
            if (res.ok) {
                setStatus('✅ Saved');
                setTimeout(() => setStatus(null), 2000);
            }
        } catch {}
        setSaving(false);
    };

    if (!visibility) return <div className={styles.loading}>Loading visibility settings…</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🎛️</span>
                <div>
                    <h2 className={styles.title}>Analytics Visibility Controls {sessionId ? `(${sessionId.slice(0,12)})` : ''}</h2>
                    <p className={styles.subtitle}>
                        {sessionId ? "Override analytics visibility and player-facing round surfaces for this specific cohort." : "Choose which analytics are available to Facilitators and Players, and the default player-facing round surfaces, globally."}
                        {saving && <span className={styles.savingBadge}>Saving…</span>}
                        {status && <span className={styles.savedBadge}>{status}</span>}
                    </p>
                </div>
            </div>

            <div className={styles.rolesGrid}>
                {/* Facilitator column */}
                <div className={styles.roleColumn}>
                    <div className={styles.roleHeader}>
                        <span>🎓</span>
                        <h3>Facilitator Dashboard</h3>
                    </div>
                    {FACILITATOR_ANALYTICS.map(a => (
                        <div key={a.key} className={styles.toggleRow} data-tooltip={a.tooltip}>
                            <div className={styles.toggleInfo}>
                                <span className={styles.toggleIcon}>{a.icon}</span>
                                <div>
                                    <div className={styles.toggleLabel}>{a.label}</div>
                                    <div className={styles.toggleDesc}>{a.desc}</div>
                                </div>
                            </div>
                            <button
                                className={`${styles.toggleBtn} ${visibility.facilitator[a.key] ? styles.toggleOn : styles.toggleOff}`}
                                onClick={() => toggle('facilitator', a.key)}
                            >
                                <span className={styles.toggleKnob} />
                            </button>
                        </div>
                    ))}

                    {/* Facilitator tools — per-cohort unlocks (cohort-settings
                        override layer, super-admin-owned). */}
                    <div className={styles.roleHeader} style={{ marginTop: '0.9rem' }}>
                        <span>🦢</span>
                        <h3>Facilitator Tools</h3>
                    </div>
                    <div className={styles.toggleRow}
                         data-tooltip="Unlocks the Custom Black Swan Injector tab for THIS cohort's lead facilitator: they can compose a custom crisis (narrative + treasury/reputation/social-licence/NCD deltas) and inject it into this cohort only. Off = the tab lists nothing for them; the backend enforces the same lock.">
                        <div className={styles.toggleInfo}>
                            <span className={styles.toggleIcon}>🦢</span>
                            <div>
                                <div className={styles.toggleLabel}>Custom Black Swan Injector</div>
                                <div className={styles.toggleDesc}>
                                    {sessionId ? 'Let this cohort’s lead facilitator inject custom crises (this cohort only)' : 'Select a cohort to unlock the injector per cohort'}
                                </div>
                            </div>
                        </div>
                        <button
                            className={`${styles.toggleBtn} ${swanEnabled ? styles.toggleOn : styles.toggleOff}`}
                            onClick={toggleSwan}
                            disabled={!sessionId}
                        >
                            <span className={styles.toggleKnob} />
                        </button>
                    </div>
                    {swanStatus && <div style={{ fontSize: '0.74rem', fontWeight: 700, padding: '2px 4px' }}>{swanStatus}</div>}

                    {/* Negotiation Rooms — shown only when the caller's profile
                        carries the capability (super admin grants it in the
                        Facilitator Registry). Server enforces regardless. */}
                    {negoCapable && (
                        <>
                            <div className={styles.toggleRow}
                                 data-tooltip="Opens Stakeholder Negotiation Rooms for THIS cohort: when an autonomous stakeholder turns hostile, players may request a meeting and buy de-escalation with priced, binding concessions (broken promises make future meetings costlier). Requires the per-facilitator capability, granted by a super admin.">
                                <div className={styles.toggleInfo}>
                                    <span className={styles.toggleIcon}>🤝</span>
                                    <div>
                                        <div className={styles.toggleLabel}>Stakeholder Negotiation Rooms</div>
                                        <div className={styles.toggleDesc}>
                                            {sessionId ? 'Let this cohort’s players negotiate with hostile stakeholders' : 'Select a cohort to open rooms per cohort'}
                                        </div>
                                    </div>
                                </div>
                                <button
                                    className={`${styles.toggleBtn} ${negoEnabled ? styles.toggleOn : styles.toggleOff}`}
                                    onClick={toggleNego}
                                    disabled={!sessionId}
                                >
                                    <span className={styles.toggleKnob} />
                                </button>
                            </div>
                            {negoStatus && <div style={{ fontSize: '0.74rem', fontWeight: 700, padding: '2px 4px' }}>{negoStatus}</div>}
                        </>
                    )}
                </div>

                {/* Player column */}
                <div className={styles.roleColumn}>
                    <div className={styles.roleHeader}>
                        <span>👤</span>
                        <h3>Player Dashboard</h3>
                    </div>
                    {/* Sectioned by the registry's own groups. This list grew from 3
                        keys to 65; as one flat column it was a scroll-and-hope
                        surface, and this panel is the one a facilitator opens
                        MID-RUN to change something specific. Same grouping the
                        cohort-formation form uses, from the same helper. */}
                    {playerVisibilityGroups().map(({ group, cards }) => {
                        const on = cards.filter(c => visibility.player[c.key]).length;
                        return (
                            <div key={group}>
                                <div className={styles.groupHeader ?? ''} style={{
                                    display: 'flex', alignItems: 'center', gap: 8,
                                    margin: '14px 0 4px', fontSize: '0.64rem', fontWeight: 700,
                                    letterSpacing: '0.08em', textTransform: 'uppercase', color: '#64748b',
                                }}>
                                    <span>{group}</span>
                                    <span style={{ color: '#475569', letterSpacing: 0 }}>{on}/{cards.length}</span>
                                </div>
                                {cards.map(a => (
                                    <div key={a.key} className={styles.toggleRow} data-tooltip={a.tooltip}>
                                        <div className={styles.toggleInfo}>
                                            <span className={styles.toggleIcon}>{a.icon}</span>
                                            <div>
                                                <div className={styles.toggleLabel}>{a.label}</div>
                                                <div className={styles.toggleDesc}>{a.desc || a.tooltip}</div>
                                            </div>
                                        </div>
                                        <button
                                            className={`${styles.toggleBtn} ${visibility.player[a.key] ? styles.toggleOn : styles.toggleOff}`}
                                            onClick={() => toggle('player', a.key)}
                                        >
                                            <span className={styles.toggleKnob} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        );
                    })}

                    {/* Player-facing round surfaces — per-cohort settings (not
                        analytics visibility). Persist via /player-feature-toggles. */}
                    <div className={styles.roleHeader} style={{ marginTop: '0.9rem' }}>
                        <span>🎬</span>
                        <h3>Round Surfaces</h3>
                    </div>
                    {/* Briefing videos — URLs only; media lives on YouTube/Vimeo/CDN. */}
                    <div className={styles.roleHeader} style={{ marginTop: '0.9rem' }}>
                        <span>🎬</span>
                        <h3>Briefing Videos</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '4px 2px' }}>
                        <label style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', opacity: 0.75 }}>URL pattern (optional, {'{round}'} = round no.)</label>
                        <input type="text" value={videoBase} onChange={e => setVideoBase(e.target.value)}
                            placeholder="https://cdn.example.edu/briefing-{round}.mp4"
                            style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(148,163,184,0.3)', background: 'transparent', color: 'inherit', fontSize: '0.78rem' }} />
                        <label style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', opacity: 0.75, marginTop: 4 }}>Per-round URLs — one per line, e.g. “1 = https://youtu.be/…”</label>
                        <textarea value={videoLines} onChange={e => setVideoLines(e.target.value)} rows={3}
                            placeholder={"1 = https://youtu.be/K_6cGzU7vrI\n2 = https://youtu.be/…"}
                            style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(148,163,184,0.3)', background: 'transparent', color: 'inherit', fontSize: '0.76rem', fontFamily: 'inherit', resize: 'vertical' }} />
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <button onClick={saveVideos}
                                style={{ padding: '6px 14px', borderRadius: 8, border: '1px solid rgba(99,102,241,0.5)', background: 'rgba(99,102,241,0.18)', color: 'inherit', fontWeight: 700, fontSize: '0.74rem', cursor: 'pointer' }}>
                                💾 Save briefing videos
                            </button>
                            {videoStatus && <span style={{ fontSize: '0.74rem', fontWeight: 700 }}>{videoStatus}</span>}
                        </div>
                    </div>

                    {PLAYER_FEATURES.map(a => (
                        <div key={a.key} className={styles.toggleRow} data-tooltip={a.desc}>
                            <div className={styles.toggleInfo}>
                                <span className={styles.toggleIcon}>{a.icon}</span>
                                <div>
                                    <div className={styles.toggleLabel}>{a.label}</div>
                                    <div className={styles.toggleDesc}>{a.desc}</div>
                                </div>
                            </div>
                            <button
                                className={`${styles.toggleBtn} ${features[a.key] ? styles.toggleOn : styles.toggleOff}`}
                                onClick={() => toggleFeature(a.key)}
                            >
                                <span className={styles.toggleKnob} />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            <div className={styles.footer}>
                <p>💡 Changes take effect immediately. Disabled analytics are hidden from the respective dashboard but data is still collected.</p>
            </div>
        </div>
    );
}
