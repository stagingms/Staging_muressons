'use client';

import { useState, useCallback, useEffect } from 'react';
import styles from './SwipeFile.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * SwipeFile — Preset + custom message inject into player's ExecutiveMailbox.
 *
 * Props:
 *  - sessionId: target session
 *  - onMessageSent: (result) => void
 */
export default function SwipeFile({ sessionId, onMessageSent }) {
    const [sending, setSending] = useState(null);
    // Phase R1 (V2-4): the old handlers never checked res.ok — an error
    // response still flashed the ✓ sent state. False success is worse than
    // silence in a live room.
    const [sendError, setSendError] = useState('');
    const [sent, setSent] = useState({});
    const [customOpen, setCustomOpen] = useState(false);
    const [customTitle, setCustomTitle] = useState('');
    const [customBody, setCustomBody] = useState('');

    // New preset creation
    const [createOpen, setCreateOpen] = useState(false);
    const [userPresets, setUserPresets] = useState([]);
    const [fetchedSwipes, setFetchedSwipes] = useState([]);
    const [newPreset, setNewPreset] = useState({
        icon: '📢',
        label: '',
        trigger: '',
        title: '',
        body: '',
        color: '#6366f1',
    });

    useEffect(() => {
        if (!sessionId) {
            setFetchedSwipes([]);
            return;
        }
        fetch(`${API}/api/admin/${sessionId}/interventions`)
            .then(r => r.ok ? r.json() : { swipes: [] })
            .then(d => setFetchedSwipes(d.swipes || []))
            .catch(() => setFetchedSwipes([]));
    }, [sessionId]);

    const allPresets = [...fetchedSwipes, ...userPresets];

    const sendPreset = useCallback(
        async (presetId) => {
            if (!sessionId) return;
            setSending(presetId);
            try {
                // Check if it's a user-created preset
                const userP = userPresets.find((p) => p.id === presetId);
                const payload = userP
                    ? {
                        session_id: sessionId,
                        message_type: 'admin',
                        title: userP.title,
                        body: userP.body,
                    }
                    : {
                        session_id: sessionId,
                        message_type: 'admin',
                        title: '',
                        body: '',
                        preset_id: presetId,
                    };

                setSendError('');
                const res = await fetch(`${API}/api/admin/${sessionId}/inject-message`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!res.ok) {
                    const eb = await res.json().catch(() => ({}));
                    throw new Error(eb.detail || `HTTP ${res.status}`);
                }
                const data = await res.json();
                setSent((prev) => ({ ...prev, [presetId]: true }));
                onMessageSent?.(data);
                setTimeout(() => setSent((prev) => ({ ...prev, [presetId]: false })), 3000);
            } catch (err) {
                console.error('Inject failed:', err);
                setSendError(`❌ Message NOT delivered — ${err.message}. Nothing reached the team; retry when ready.`);
            } finally {
                setSending(null);
            }
        },
        [sessionId, userPresets, onMessageSent]
    );

    const sendCustom = useCallback(async () => {
        if (!sessionId || !customTitle.trim()) return;
        setSending('custom');
        setSendError('');
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/inject-message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    message_type: 'admin',
                    title: customTitle,
                    body: customBody,
                }),
            });
            if (!res.ok) {
                const eb = await res.json().catch(() => ({}));
                throw new Error(eb.detail || `HTTP ${res.status}`);
            }
            const data = await res.json();
            onMessageSent?.(data);
            setCustomTitle('');
            setCustomBody('');
            setCustomOpen(false);
        } catch (err) {
            console.error('Custom inject failed:', err);
            setSendError(`❌ Custom message NOT delivered — ${err.message}. Your draft is preserved; retry when ready.`);
        } finally {
            setSending(null);
        }
    }, [sessionId, customTitle, customBody, onMessageSent]);

    const handleCreatePreset = useCallback(() => {
        if (!newPreset.label.trim() || !newPreset.title.trim()) return;
        const preset = {
            id: `custom_${Date.now()}`,
            label: `${newPreset.icon} ${newPreset.label}`,
            trigger: newPreset.trigger || 'Custom',
            color: newPreset.color,
            title: newPreset.title,
            body: newPreset.body,
            isCustom: true,
        };
        setUserPresets((prev) => [...prev, preset]);
        setNewPreset({ icon: '📢', label: '', trigger: '', title: '', body: '', color: '#6366f1' });
        setCreateOpen(false);
    }, [newPreset]);

    const handleDeletePreset = useCallback((presetId) => {
        if (!confirm('Remove this custom preset?')) return;
        setUserPresets((prev) => prev.filter((p) => p.id !== presetId));
    }, []);

    return (
        <section className={styles.panel}>
            <div className={styles.header}>
                <span>📨</span>
                <h2>Swipe File — Message Inject</h2>
                <button
                    className={styles.addPresetBtn}
                    onClick={() => setCreateOpen(!createOpen)}
                >
                    {createOpen ? '✕ Close' : '＋ New Preset'}
                </button>
            </div>

            {sendError && (
                <div style={{
                    margin: '0.5rem 0', padding: '8px 12px', borderRadius: '6px',
                    background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                    color: '#ef4444', fontSize: '0.82rem', fontWeight: 600,
                }}>{sendError}</div>
            )}

            {/* Create New Preset Form */}
            {createOpen && (
                <div className={styles.createPresetForm}>
                    <div className={styles.createRow}>
                        <div className={styles.createField} style={{ flex: '0 0 60px' }}>
                            <label>Icon</label>
                            <input
                                type="text"
                                value={newPreset.icon}
                                onChange={(e) => setNewPreset({ ...newPreset, icon: e.target.value })}
                                className={styles.customInput}
                                style={{ textAlign: 'center', fontSize: '1.2rem' }}
                                maxLength={2}
                            />
                        </div>
                        <div className={styles.createField} style={{ flex: 1 }}>
                            <label>Preset Label</label>
                            <input
                                type="text"
                                placeholder="e.g. Supply Chain Shock"
                                value={newPreset.label}
                                onChange={(e) => setNewPreset({ ...newPreset, label: e.target.value })}
                                className={styles.customInput}
                            />
                        </div>
                        <div className={styles.createField} style={{ flex: '0 0 140px' }}>
                            <label>Trigger Tag</label>
                            <input
                                type="text"
                                placeholder="e.g. High Risk"
                                value={newPreset.trigger}
                                onChange={(e) => setNewPreset({ ...newPreset, trigger: e.target.value })}
                                className={styles.customInput}
                            />
                        </div>
                        <div className={styles.createField} style={{ flex: '0 0 50px' }}>
                            <label>Color</label>
                            <input
                                type="color"
                                value={newPreset.color}
                                onChange={(e) => setNewPreset({ ...newPreset, color: e.target.value })}
                                className={styles.colorPicker}
                            />
                        </div>
                    </div>
                    <div className={styles.createRow}>
                        <div className={styles.createField} style={{ flex: 1 }}>
                            <label>Message Title (shown to players)</label>
                            <input
                                type="text"
                                placeholder="e.g. ⚠️ Supply Chain Alert"
                                value={newPreset.title}
                                onChange={(e) => setNewPreset({ ...newPreset, title: e.target.value })}
                                className={styles.customInput}
                            />
                        </div>
                    </div>
                    <div className={styles.createRow}>
                        <div className={styles.createField} style={{ flex: 1 }}>
                            <label>Message Body</label>
                            <textarea
                                placeholder="The message body players will see in their Executive Mailbox..."
                                value={newPreset.body}
                                onChange={(e) => setNewPreset({ ...newPreset, body: e.target.value })}
                                className={styles.customTextarea}
                                rows={3}
                            />
                        </div>
                    </div>
                    <button
                        className={styles.createSaveBtn}
                        onClick={handleCreatePreset}
                        disabled={!newPreset.label.trim() || !newPreset.title.trim()}
                    >
                        ✓ Save as Preset
                    </button>
                </div>
            )}

            <div className={styles.grid}>
                {allPresets.map((p) => {
                    // Build a rich tooltip: label + trigger tag + message preview
                    const tooltipParts = [p.label];
                    if (p.trigger) tooltipParts.push(`Tag: ${p.trigger}`);
                    if (p.title) tooltipParts.push(`📨 ${p.title}`);
                    if (p.body) tooltipParts.push(p.body.length > 120 ? p.body.slice(0, 120) + '…' : p.body);
                    const tooltipText = tooltipParts.join('\n\n');

                    return (
                    <button
                        key={p.id}
                        className={`${styles.preset} ${sent[p.id] ? styles.sent : ''} ${p.isCustom ? styles.customPresetCard : ''}`}
                        style={{ '--preset-color': p.color }}
                        onClick={() => sendPreset(p.id)}
                        disabled={!sessionId || sending === p.id}
                        data-tooltip={tooltipText}
                        data-tooltip-pos="above"
                    >
                        <span className={styles.presetLabel}>{p.label}</span>
                        <span className={styles.trigger}>{p.trigger}</span>
                        {sending === p.id && <span className={styles.spinner}>⏳</span>}
                        {sent[p.id] && <span className={styles.sentBadge}>✓ Sent</span>}
                        {p.isCustom && (
                            <span
                                className={styles.deletePresetBtn}
                                onClick={(e) => { e.stopPropagation(); handleDeletePreset(p.id); }}
                                data-tooltip="Remove this custom preset"
                            >
                                ✕
                            </span>
                        )}
                    </button>
                    );
                })}
            </div>

            {/* Custom one-off message */}
            <div className={styles.customSection}>
                <button
                    className={styles.customToggle}
                    onClick={() => setCustomOpen(!customOpen)}
                >
                    {customOpen ? '▾' : '▸'} Send One-Off Message
                </button>
                {customOpen && (
                    <div className={styles.customForm}>
                        <input
                            className={styles.customInput}
                            type="text"
                            placeholder="Message title..."
                            value={customTitle}
                            onChange={(e) => setCustomTitle(e.target.value)}
                        />
                        <textarea
                            className={styles.customTextarea}
                            placeholder="Message body..."
                            value={customBody}
                            onChange={(e) => setCustomBody(e.target.value)}
                            rows={3}
                        />
                        <button
                            className={styles.customSend}
                            onClick={sendCustom}
                            disabled={!sessionId || !customTitle.trim() || sending === 'custom'}
                        >
                            {sending === 'custom' ? '⏳ Sending...' : '📤 Send Custom Message'}
                        </button>
                    </div>
                )}
            </div>
        </section>
    );
}
