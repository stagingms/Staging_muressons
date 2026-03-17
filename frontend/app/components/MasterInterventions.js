import React, { useState, useEffect, useRef } from 'react';
import styles from './MasterInterventions.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const MEDIA_TYPES = [
    { value: 'text', label: '📝 Text Only' },
    { value: 'audio', label: '🎵 Audio' },
    { value: 'video', label: '🎬 Video' },
];

const MEDIA_BADGE = { text: '📝', audio: '🎵', video: '🎬' };

export default function MasterInterventions() {
    const [overrides, setOverrides] = useState([]);
    const [swipes, setSwipes] = useState([]);
    const [loading, setLoading] = useState(true);

    const [editingType, setEditingType] = useState(null); // 'override' or 'swipe'
    const [formData, setFormData] = useState(null);
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef(null);
    const [showDatabase, setShowDatabase] = useState(false);

    useEffect(() => {
        fetchMasterData();
    }, []);

    const fetchMasterData = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/interventions/master`);
            if (res.ok) {
                const data = await res.json();
                setOverrides(data.overrides || []);
                setSwipes(data.swipes || []);
            }
        } catch (err) {
            console.error("Failed to fetch master interventions", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (type, id) => {
        if (!confirm(`Are you sure you want to delete this ${type}?`)) return;
        try {
            const res = await fetch(`${API}/api/admin/interventions/master/${type}/${id}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                fetchMasterData();
            }
        } catch (err) {
            console.error("Delete failed", err);
        }
    };

    const uploadMedia = async (file) => {
        const fd = new FormData();
        fd.append('file', file);
        const res = await fetch(`${API}/api/admin/interventions/upload-media`, {
            method: 'POST',
            body: fd,
        });
        if (!res.ok) throw new Error('Upload failed');
        return await res.json();
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setUploading(true);
        try {
            let mediaUrl = formData.media_url || '';
            let mediaType = formData.media_type || 'text';

            // If a file was selected, upload it first
            if (selectedFile && (mediaType === 'audio' || mediaType === 'video')) {
                const uploadResult = await uploadMedia(selectedFile);
                mediaUrl = uploadResult.url;
            }

            const payload = { ...formData, media_url: mediaUrl, media_type: mediaType };

            const res = await fetch(`${API}/api/admin/interventions/master/${editingType}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                setEditingType(null);
                setFormData(null);
                setSelectedFile(null);
                fetchMasterData();
            }
        } catch (err) {
            console.error("Save failed", err);
        } finally {
            setUploading(false);
        }
    };

    const openForm = (type, existingItem = null) => {
        setEditingType(type);
        setSelectedFile(null);
        if (type === 'override') {
            setFormData(existingItem || {
                id: `ov_${Date.now()}`,
                icon: '⚡',
                title: '',
                description: '',
                color: '#3b82f6',
                dangerLevel: 'HIGH',
                params: {},
                scheduled_round: null,
                media_type: 'text',
                media_url: '',
            });
        } else {
            setFormData(existingItem || {
                id: `sw_${Date.now()}`,
                icon: '📢',
                label: '',
                trigger: 'Manual',
                title: '',
                body: '',
                color: '#6366f1',
                scheduled_round: null,
                media_type: 'text',
                media_url: '',
            });
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files?.[0];
        if (file) setSelectedFile(file);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        const file = e.dataTransfer?.files?.[0];
        if (file) setSelectedFile(file);
    };

    if (loading && !overrides.length) return <div className={styles.loading}>Loading interventions...</div>;

    return (
        <div className={styles.container}>
            <div className={styles.topHeader}>
                <h2>Master Interventions Database</h2>
                <p>Global repository of overrides and swipe files. Upload text, audio, or video attachments for each intervention.</p>
            </div>

            {!showDatabase && (
                <div className={styles.gatePrompt}>
                    <div className={styles.gateIcon}>
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                    </div>
                    <p className={styles.gateText}>
                        The Master Interventions Database contains global overrides and swipe files used across <strong>all cohorts</strong>. Modifying these entries will affect <strong>all future simulation runs</strong>.
                    </p>
                    <button
                        className={styles.gateBtn}
                        onClick={() => setShowDatabase(true)}
                    >Edit Interventions Database</button>
                </div>
            )}

            {showDatabase && (<>

            {editingType && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modal}>
                        <h3>{formData?.id?.startsWith('ov_') || formData?.id?.startsWith('sw_') ? 'Create New' : 'Edit'} {editingType === 'override' ? 'Override' : 'Swipe File'}</h3>
                        <form onSubmit={handleSave} className={styles.form}>
                            {/* Shared Fields */}
                            <div className={styles.formRow}>
                                <div className={styles.formGroup}>
                                    <label>Internal ID (immutable tracking)</label>
                                    <input type="text" value={formData.id} disabled />
                                </div>
                                <div className={styles.formGroup}>
                                    <label>Icon Details (Emoji)</label>
                                    <input type="text" value={formData.icon} onChange={(e) => setFormData({ ...formData, icon: e.target.value })} required maxLength={2} />
                                </div>
                                <div className={styles.formGroup}>
                                    <label>Theme Color (Hex)</label>
                                    <input type="color" value={formData.color} onChange={(e) => setFormData({ ...formData, color: e.target.value })} />
                                </div>
                            </div>

                            {/* Override Specific Fields */}
                            {editingType === 'override' && (
                                <>
                                    <div className={styles.formGroup}>
                                        <label>Display Title</label>
                                        <input type="text" value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>Description Tooltip</label>
                                        <input type="text" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} required />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>Danger Level</label>
                                        <select value={formData.dangerLevel} onChange={(e) => setFormData({ ...formData, dangerLevel: e.target.value })}>
                                            <option value="LOW">LOW</option>
                                            <option value="MEDIUM">MEDIUM</option>
                                            <option value="HIGH">HIGH</option>
                                            <option value="CRITICAL">CRITICAL</option>
                                        </select>
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>JSON Parameters Payload (Advanced)</label>
                                        <textarea
                                            value={JSON.stringify(formData.params, null, 2)}
                                            onChange={(e) => {
                                                try {
                                                    setFormData({ ...formData, params: JSON.parse(e.target.value) });
                                                } catch (err) { /* ignore parse errors while typing */ }
                                            }}
                                            rows={4}
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>Scheduled Round</label>
                                        <select value={formData.scheduled_round ?? ''} onChange={(e) => setFormData({ ...formData, scheduled_round: e.target.value ? parseInt(e.target.value) : null })}>
                                            <option value="">Any Round</option>
                                            {Array.from({ length: 10 }, (_, i) => (
                                                <option key={i + 1} value={i + 1}>Round {i + 1}</option>
                                            ))}
                                        </select>
                                        <small style={{ color: 'var(--text-muted)' }}>If set, this intervention is only available in the specified round.</small>
                                    </div>
                                </>
                            )}

                            {/* Swipe File Specific Fields */}
                            {editingType === 'swipe' && (
                                <>
                                    <div className={styles.formGroup}>
                                        <label>Dashboard Label (Short Name)</label>
                                        <input type="text" value={formData.label} onChange={(e) => setFormData({ ...formData, label: e.target.value })} required />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>Trigger Condition (For sorting)</label>
                                        <input type="text" value={formData.trigger} onChange={(e) => setFormData({ ...formData, trigger: e.target.value })} required />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>Injected Message Title</label>
                                        <input type="text" value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>Injected Message Body</label>
                                        <textarea value={formData.body} onChange={(e) => setFormData({ ...formData, body: e.target.value })} required rows={5} />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>Scheduled Round</label>
                                        <select value={formData.scheduled_round ?? ''} onChange={(e) => setFormData({ ...formData, scheduled_round: e.target.value ? parseInt(e.target.value) : null })}>
                                            <option value="">Any Round</option>
                                            {Array.from({ length: 10 }, (_, i) => (
                                                <option key={i + 1} value={i + 1}>Round {i + 1}</option>
                                            ))}
                                        </select>
                                        <small style={{ color: 'var(--text-muted)' }}>If set, this swipe file is only injected in the specified round.</small>
                                    </div>
                                </>
                            )}

                            {/* ─── Media Attachment Section ─── */}
                            <div className={styles.mediaSection}>
                                <div className={styles.mediaSectionHeader}>
                                    <span>📎 Media Attachment</span>
                                </div>
                                <div className={styles.formGroup}>
                                    <label>Content Type</label>
                                    <div className={styles.mediaTypeSelector}>
                                        {MEDIA_TYPES.map(mt => (
                                            <button
                                                key={mt.value}
                                                type="button"
                                                className={`${styles.mediaTypeBtn} ${formData.media_type === mt.value ? styles.mediaTypeBtnActive : ''}`}
                                                onClick={() => {
                                                    setFormData({ ...formData, media_type: mt.value, media_url: mt.value === 'text' ? '' : formData.media_url });
                                                    if (mt.value === 'text') setSelectedFile(null);
                                                }}
                                            >
                                                {mt.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {(formData.media_type === 'audio' || formData.media_type === 'video') && (
                                    <div className={styles.formGroup}>
                                        <label>Upload {formData.media_type === 'audio' ? 'Audio' : 'Video'} File</label>
                                        <div
                                            className={styles.dropZone}
                                            onDragOver={(e) => e.preventDefault()}
                                            onDrop={handleDrop}
                                            onClick={() => fileInputRef.current?.click()}
                                        >
                                            <input
                                                ref={fileInputRef}
                                                type="file"
                                                accept={formData.media_type === 'audio' ? 'audio/*' : 'video/*'}
                                                onChange={handleFileSelect}
                                                style={{ display: 'none' }}
                                            />
                                            {selectedFile ? (
                                                <div className={styles.fileSelected}>
                                                    <span className={styles.fileIcon}>{formData.media_type === 'audio' ? '🎵' : '🎬'}</span>
                                                    <span className={styles.fileName}>{selectedFile.name}</span>
                                                    <span className={styles.fileSize}>({(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)</span>
                                                    <button type="button" className={styles.removeFile} onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}>✕</button>
                                                </div>
                                            ) : formData.media_url ? (
                                                <div className={styles.fileSelected}>
                                                    <span className={styles.fileIcon}>{formData.media_type === 'audio' ? '🎵' : '🎬'}</span>
                                                    <span className={styles.fileName}>Existing: {formData.media_url.split('/').pop()}</span>
                                                    <span className={styles.fileSize}>(click to replace)</span>
                                                </div>
                                            ) : (
                                                <div className={styles.dropZoneEmpty}>
                                                    <span className={styles.dropIcon}>☁️</span>
                                                    <span>Drop {formData.media_type} file here or <strong>click to browse</strong></span>
                                                    <small>{formData.media_type === 'audio' ? 'MP3, WAV, OGG, M4A' : 'MP4, WebM, MOV, AVI'}</small>
                                                </div>
                                            )}
                                        </div>

                                        {/* Preview for existing media */}
                                        {formData.media_url && !selectedFile && (
                                            <div className={styles.mediaPreview}>
                                                {formData.media_type === 'audio' ? (
                                                    <audio controls src={formData.media_url} className={styles.audioPlayer} />
                                                ) : (
                                                    <video controls src={formData.media_url} className={styles.videoPlayer} />
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            <div className={styles.modalActions}>
                                <button type="button" className={styles.cancelBtn} onClick={() => { setEditingType(null); setSelectedFile(null); }}>Cancel</button>
                                <button type="submit" className={styles.saveBtn} disabled={uploading}>
                                    {uploading ? '⏳ Uploading…' : 'Save Interventions'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <div className={styles.grid}>
                {/* Overrides Table */}
                <div className={styles.panel}>
                    <div className={styles.panelHeader}>
                        <h3>⚡ Manual Overrides</h3>
                        <button className={styles.addBtn} onClick={() => openForm('override')}>+ Add Override</button>
                    </div>
                    <div className={styles.list}>
                        {overrides.map(ov => (
                            <div key={ov.id} className={styles.listItem} style={{ borderLeftColor: ov.color }}>
                                <span className={styles.itemIcon}>{ov.icon}</span>
                                <div className={styles.itemDetails}>
                                    <h4>{ov.title} <span className={styles.dangerBadge}>{ov.dangerLevel}</span>
                                        {ov.scheduled_round ? <span className={styles.roundBadge}>R{ov.scheduled_round}</span> : <span className={styles.anyBadge}>Any</span>}
                                        {ov.media_type && ov.media_type !== 'text' && (
                                            <span className={styles.mediaBadge} title={`${ov.media_type} attached`}>
                                                {MEDIA_BADGE[ov.media_type]}
                                            </span>
                                        )}
                                    </h4>
                                    <p>{ov.description}</p>
                                    {ov.media_url && ov.media_type === 'audio' && (
                                        <audio controls src={ov.media_url} className={styles.inlineAudio} />
                                    )}
                                    {ov.media_url && ov.media_type === 'video' && (
                                        <video controls src={ov.media_url} className={styles.inlineVideo} />
                                    )}
                                </div>
                                <div className={styles.itemActions}>
                                    <button onClick={() => openForm('override', ov)}>✎</button>
                                    <button onClick={() => handleDelete('override', ov.id)} className={styles.deleteIcon}>🗑️</button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Swipes Table */}
                <div className={styles.panel}>
                    <div className={styles.panelHeader}>
                        <h3>✉️ Swipe Files</h3>
                        <button className={styles.addBtn} onClick={() => openForm('swipe')}>+ Add Swipe File</button>
                    </div>
                    <div className={styles.list}>
                        {swipes.map(sw => (
                            <div key={sw.id} className={styles.listItem} style={{ borderLeftColor: sw.color }}>
                                <span className={styles.itemIcon}>{sw.icon}</span>
                                <div className={styles.itemDetails}>
                                    <h4>{sw.label} <span className={styles.triggerBadge}>{sw.trigger}</span>
                                        {sw.scheduled_round ? <span className={styles.roundBadge}>R{sw.scheduled_round}</span> : <span className={styles.anyBadge}>Any</span>}
                                        {sw.media_type && sw.media_type !== 'text' && (
                                            <span className={styles.mediaBadge} title={`${sw.media_type} attached`}>
                                                {MEDIA_BADGE[sw.media_type]}
                                            </span>
                                        )}
                                    </h4>
                                    <p><strong>{sw.title}</strong>: {sw.body?.substring(0, 50)}{sw.body?.length > 50 ? '...' : ''}</p>
                                    {sw.media_url && sw.media_type === 'audio' && (
                                        <audio controls src={sw.media_url} className={styles.inlineAudio} />
                                    )}
                                    {sw.media_url && sw.media_type === 'video' && (
                                        <video controls src={sw.media_url} className={styles.inlineVideo} />
                                    )}
                                </div>
                                <div className={styles.itemActions}>
                                    <button onClick={() => openForm('swipe', sw)}>✎</button>
                                    <button onClick={() => handleDelete('swipe', sw.id)} className={styles.deleteIcon}>🗑️</button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
            </>)}
        </div>
    );
}
