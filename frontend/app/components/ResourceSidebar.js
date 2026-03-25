'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import styles from './ResourceSidebar.module.css';
import InlinePodcastPlayer from './InlinePodcastPlayer';
import InlineQuizEngine from './InlineQuizEngine';
import InlineReviewViewer from './InlineReviewViewer';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

const TYPE_ICONS = { PDF: '📄', Video: '🎬', Weblink: '🔗', Memo: '📝', NotebookLM: '🧠' };
const TYPE_CLASS = { PDF: styles.typePDF, Video: styles.typeVideo, Weblink: styles.typeWeblink, Memo: styles.typeMemo, NotebookLM: styles.typeNotebookLM };

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

function LearningHubCard({ notebook, onOpenPodcast, onOpenQuiz, onOpenReview, quizEnabled }) {
    const types = notebook.content_types || [];
    const ACTION_STYLES = {
        podcast: { bg: 'linear-gradient(135deg, #7c3aed, #6d28d9)', icon: '🎧', label: 'Listen' },
        quiz: { bg: 'linear-gradient(135deg, #4f46e5, #4338ca)', icon: '🧩', label: 'Quiz' },
        review: { bg: 'linear-gradient(135deg, #059669, #047857)', icon: '📝', label: 'Review' },
    };

    const CANONICAL_ORDER = ['podcast', 'review', 'quiz'];

    return (
        <div className={styles.nbHubCard}>
            <div className={styles.nbHubHeader}>
                <div className={styles.nbHubIcon}>📚</div>
                <div className={styles.nbHubInfo}>
                    <h4 className={styles.nbHubTitle}>{notebook.title}</h4>
                    <span className={styles.nbHubMeta}>R{notebook.target_round} · {notebook.category}</span>
                </div>
            </div>
            {notebook.description && <p className={styles.nbHubDesc}>{notebook.description}</p>}
            <div className={styles.nbHubFooter}>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {CANONICAL_ORDER.filter(ct => types.includes(ct)).map(ct => {
                        const style = ACTION_STYLES[ct];
                        if (!style) return null;
                        if (ct === 'quiz' && !quizEnabled) return null;
                        const handler = ct === 'podcast' ? onOpenPodcast
                            : ct === 'quiz' ? onOpenQuiz
                            : onOpenReview;
                        return (
                            <button
                                key={ct}
                                onClick={() => handler(notebook)}
                                style={{
                                    background: style.bg, border: 'none', borderRadius: 8,
                                    padding: '6px 14px', color: '#fff', fontSize: '0.75rem',
                                    fontWeight: 600, cursor: 'pointer', display: 'flex',
                                    alignItems: 'center', gap: 4,
                                    transition: 'transform 0.15s, box-shadow 0.15s',
                                }}
                                onMouseOver={e => { e.target.style.transform = 'scale(1.05)'; e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)'; }}
                                onMouseOut={e => { e.target.style.transform = 'scale(1)'; e.target.style.boxShadow = 'none'; }}
                            >
                                {style.icon} {style.label}
                            </button>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}


export default function ResourceSidebar({ sessionId, roundNumber, isOpen, onClose }) {
    const [resources, setResources] = useState({ new_this_round: [], archive: [], notebooklm_notebooks: [] });
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false);

    // ── Inline content modal state ───────────────────────────
    const [podcastNb, setPodcastNb] = useState(null);
    const [quizNb, setQuizNb] = useState(null);
    const [reviewNb, setReviewNb] = useState(null);

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
    const notebooks = resources.notebooklm_notebooks || [];
    const quizEnabled = resources.quiz_enabled !== false;
    const [quizQuestions, setQuizQuestions] = useState([]);
    const [quizDifficulty, setQuizDifficulty] = useState('medium');
    const [quizLoading, setQuizLoading] = useState(false);

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

                    {!loading && notebooks.length === 0 && filteredNew.length === 0 && filteredArchive.length === 0 && (
                        <div className={styles.empty}>
                            {search ? 'No resources match your search.' : 'No resources have been unlocked yet. Your facilitator will release them as the simulation progresses.'}
                        </div>
                    )}

                    {/* Learning Hub (was NotebookLM Hub) */}
                    {notebooks.length > 0 && (
                        <div className={styles.nbHubSection}>
                            <div className={styles.sectionHeader}>
                                📚 Learning Hub
                                <span className={styles.newCount}>{notebooks.length}</span>
                            </div>
                            {notebooks.map(nb => (
                                <LearningHubCard
                                    key={nb.id}
                                    notebook={nb}
                                    quizEnabled={quizEnabled}
                                    onOpenPodcast={(nb) => setPodcastNb(nb)}
                                    onOpenQuiz={async (nb) => {
                                        setQuizLoading(true);
                                        setQuizNb(nb);
                                        try {
                                            const res = await fetch(`${API_BASE}/api/simulations/quiz/${nb.id}`);
                                            if (res.ok) {
                                                const data = await res.json();
                                                setQuizQuestions(data.questions || []);
                                                setQuizDifficulty(data.difficulty || 'medium');
                                            } else {
                                                setQuizQuestions(nb.quiz_questions || []);
                                            }
                                        } catch {
                                            setQuizQuestions(nb.quiz_questions || []);
                                        }
                                        setQuizLoading(false);
                                    }}
                                    onOpenReview={(nb) => setReviewNb(nb)}
                                />
                            ))}
                        </div>
                    )}

                    {notebooks.length > 0 && (filteredNew.length > 0 || filteredArchive.length > 0) && <hr className={styles.divider} />}

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

            {/* ═══ Inline Podcast Player ═══ */}
            <InlinePodcastPlayer
                isOpen={!!podcastNb}
                onClose={() => setPodcastNb(null)}
                title={podcastNb?.title || ''}
                transcript={podcastNb?.podcast_transcript || []}
                sessionId={sessionId}
                notebookId={podcastNb?.id || ''}
            />

            {/* ═══ Inline Quiz Engine ═══ */}
            <InlineQuizEngine
                isOpen={!!quizNb}
                onClose={() => { setQuizNb(null); setQuizQuestions([]); }}
                title={quizNb?.title || ''}
                questions={quizQuestions}
                difficulty={quizDifficulty}
                loading={quizLoading}
                sessionId={sessionId}
                notebookId={quizNb?.id || ''}
            />

            {/* ═══ Inline Review Viewer ═══ */}
            <InlineReviewViewer
                isOpen={!!reviewNb}
                onClose={() => setReviewNb(null)}
                title={reviewNb?.title || ''}
                content={reviewNb?.review_content || ''}
            />
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
