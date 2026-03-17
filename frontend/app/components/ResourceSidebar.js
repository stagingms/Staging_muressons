'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import styles from './ResourceSidebar.module.css';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

const TYPE_ICONS = { PDF: '📄', Video: '🎬', Weblink: '🔗', Memo: '📝' };
const TYPE_CLASS = { PDF: styles.typePDF, Video: styles.typeVideo, Weblink: styles.typeWeblink, Memo: styles.typeMemo };

function ResourceCard({ resource, isNew }) {
    const href = resource.url || '#';
    const isExternal = href.startsWith('http');

    return (
        <a
            className={`${styles.resourceCard} ${resource.is_strategic_drop ? styles.strategicDrop : ''}`}
            href={isExternal ? href : undefined}
            target={isExternal ? '_blank' : undefined}
            rel={isExternal ? 'noopener noreferrer' : undefined}
            onClick={!isExternal ? (e) => e.preventDefault() : undefined}
        >
            <div className={styles.cardHeader}>
                <h4 className={styles.cardTitle}>{resource.title}</h4>
                {isNew && <span className={styles.newTag}>NEW</span>}
            </div>
            <div className={styles.cardMeta}>
                <span className={`${styles.typeBadge} ${TYPE_CLASS[resource.type] || ''}`}>
                    {TYPE_ICONS[resource.type] || '📌'} {resource.type}
                </span>
                <span className={styles.categoryBadge}>{resource.category}</span>
                {resource.trigger === 'auto_condition' && (
                    <span className={styles.hiddenUnlockTag}>🏆 Achievement Unlock</span>
                )}
                {resource.impact_link && (
                    <span className={styles.unlockBadge}>→ {resource.impact_link}</span>
                )}
            </div>
            {resource.effect && (
                <div className={styles.effectBanner}>
                    ⚡ Competitive Advantage: {resource.effect.target} {resource.effect.modifier > 0 ? '+' : ''}
                    {Math.abs(resource.effect.modifier) < 1
                        ? `${(resource.effect.modifier * 100).toFixed(0)}%`
                        : `$${resource.effect.modifier.toLocaleString()}`}
                </div>
            )}
        </a>
    );
}

export default function ResourceSidebar({ sessionId, roundNumber, isOpen, onClose }) {
    const [resources, setResources] = useState({ new_this_round: [], archive: [] });
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false);

    // ── Fetch resources ─────────────────────────────────────
    const fetchResources = useCallback(async () => {
        if (!sessionId || sessionId === 'demo') return;
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/simulations/${sessionId}/resources`);
            if (res.ok) {
                const data = await res.json();
                setResources(data);
            }
        } catch (e) { console.error('Failed to fetch resources', e); }
        setLoading(false);
    }, [sessionId]);

    useEffect(() => {
        if (isOpen) fetchResources();
    }, [isOpen, fetchResources, roundNumber]);

    // ── Search filter ───────────────────────────────────────
    const filterFn = useCallback((r) => {
        if (!search) return true;
        const q = search.toLowerCase();
        return r.title.toLowerCase().includes(q) ||
            r.category.toLowerCase().includes(q) ||
            r.type.toLowerCase().includes(q) ||
            (r.tags || []).some(t => t.toLowerCase().includes(q)) ||
            (r.impact_link || '').toLowerCase().includes(q);
    }, [search]);

    const filteredNew = useMemo(() => (resources.new_this_round || []).filter(filterFn), [resources.new_this_round, filterFn]);
    const filteredArchive = useMemo(() => (resources.archive || []).filter(filterFn), [resources.archive, filterFn]);

    const hasNew = (resources.new_this_round || []).length > 0;

    if (!isOpen) return null;

    return (
        <>
            <div className={styles.sidebarOverlay} onClick={onClose} />
            <div className={styles.sidebar}>
                <div className={styles.header}>
                    <h2>📚 Resources</h2>
                    <button className={styles.closeBtn} onClick={onClose}>✕</button>
                </div>

                <div className={styles.content}>
                    {/* Search */}
                    <div className={styles.searchBar}>
                        <span className={styles.searchIcon}>🔍</span>
                        <input
                            type="text"
                            placeholder="Search by title, category, tag..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>

                    {loading && <p className={styles.empty}>Loading resources...</p>}

                    {!loading && filteredNew.length === 0 && filteredArchive.length === 0 && (
                        <div className={styles.empty}>
                            {search ? 'No resources match your search.' : 'No resources have been unlocked yet. Your facilitator will release them as the simulation progresses.'}
                        </div>
                    )}

                    {/* New This Round */}
                    {filteredNew.length > 0 && (
                        <div className={styles.sectionNew}>
                            <div className={styles.sectionHeader}>
                                ✨ New This Round
                                <span className={styles.newCount}>{filteredNew.length}</span>
                            </div>
                            {filteredNew.map(r => <ResourceCard key={r.id} resource={r} isNew />)}
                        </div>
                    )}

                    {filteredNew.length > 0 && filteredArchive.length > 0 && <hr className={styles.divider} />}

                    {/* Archive */}
                    {filteredArchive.length > 0 && (
                        <div>
                            <div className={styles.sectionHeader}>📂 Reference Library</div>
                            {filteredArchive.map(r => <ResourceCard key={r.id} resource={r} isNew={false} />)}
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}

/**
 * Trigger button to open the sidebar. Renders a glowing dot when new resources exist.
 */
export function ResourceTriggerButton({ hasNew, onClick }) {
    return (
        <button className={styles.triggerBtn} onClick={onClick} title="Open Resources">
            📚
            {hasNew && <span className={styles.glowDot} />}
        </button>
    );
}
