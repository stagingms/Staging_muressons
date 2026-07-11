'use client';
import { useState, useCallback } from 'react';
import styles from './StakeholderSentimentPanel.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/* ─── Helpers ─── */
function getSalienceInfo(sh) {
    const hasUrgency = sh.urgency;
    const hasLegitimacy = sh.legitimacy;
    const hasPower = sh.power === 'high';

    const count = [hasUrgency, hasLegitimacy, hasPower].filter(Boolean).length;
    if (count >= 3) return { label: 'Definitive', color: '#a855f7', bg: 'rgba(168,85,247,0.12)' };
    if (count === 2) return { label: 'Expectant', color: '#3b82f6', bg: 'rgba(59,130,246,0.12)' };
    return { label: 'Latent', color: '#64748b', bg: 'rgba(100,116,139,0.12)' };
}

function getAttitudeColor(score) {
    if (score < -30) return { bar: '#ef4444', text: '#ef4444' };
    if (score > 30) return { bar: '#10b981', text: '#10b981' };
    return { bar: '#f59e0b', text: '#f59e0b' };
}

function AttitudeGauge({ score }) {
    const pct = Math.round(((score + 100) / 200) * 100);
    const { bar } = getAttitudeColor(score);
    return (
        <div className={styles.gauge}>
            <div className={styles.gaugeTrack}>
                <div
                    className={styles.gaugeFill}
                    style={{ width: `${pct}%`, background: bar }}
                />
                <div
                    className={styles.gaugeMarker}
                    style={{ left: '50%' }}
                    title="Neutral (0)"
                />
            </div>
            <div className={styles.gaugeLabels}>
                <span>-100</span>
                <span>0</span>
                <span>+100</span>
            </div>
        </div>
    );
}

function DeltaArrow({ delta }) {
    if (delta === undefined || delta === null) return null;
    const up = delta >= 0;
    return (
        <span style={{ color: up ? '#10b981' : '#ef4444', fontWeight: 700, fontSize: '0.78rem' }}>
            {up ? '▲' : '▼'}{Math.abs(delta)}
        </span>
    );
}

function StakeholderCard({ sh }) {
    const attitude = sh.attitude_score ?? 0;
    const delta = sh.attitude_delta ?? null;
    const { text: attColor } = getAttitudeColor(attitude);
    const salience = getSalienceInfo(sh);
    const isEarlyWarning = attitude < -50 && sh.power === 'high';

    return (
        <div className={styles.card}>
            <div className={styles.cardTop}>
                <div className={styles.stakeholderIdent}>
                    <span className={styles.stakeholderIcon}>{sh.icon || '👤'}</span>
                    <span className={styles.stakeholderName}>{sh.name || 'Unknown'}</span>
                </div>
                <div className={styles.badges}>
                    <span
                        className={styles.salienceBadge}
                        style={{ color: salience.color, background: salience.bg, borderColor: salience.color }}
                    >
                        {salience.label}
                    </span>
                    {isEarlyWarning && (
                        <span className={styles.warningBadge}>🚨 Early Warning</span>
                    )}
                </div>
            </div>

            <AttitudeGauge score={attitude} />

            <div className={styles.scoreRow}>
                <span className={styles.scoreValue} style={{ color: attColor }}>
                    {attitude > 0 ? '+' : ''}{attitude}
                </span>
                <DeltaArrow delta={delta} />
                <span className={styles.scoreLabel}>attitude score</span>
            </div>

            {sh.sentiment_narrative && (
                <p className={styles.narrative}>"{sh.sentiment_narrative}"</p>
            )}
        </div>
    );
}

function SummaryRow({ stakeholders }) {
    const hostile = stakeholders.filter(s => (s.attitude_score ?? 0) < -30).length;
    const supportive = stakeholders.filter(s => (s.attitude_score ?? 0) > 30).length;
    const neutral = stakeholders.length - hostile - supportive;

    return (
        <div className={styles.summaryRow}>
            <div className={styles.summaryItem} style={{ color: '#ef4444' }}>
                <span className={styles.summaryCount}>{hostile}</span>
                <span className={styles.summaryLabel}>Hostile</span>
            </div>
            <div className={styles.summaryDivider} />
            <div className={styles.summaryItem} style={{ color: '#f59e0b' }}>
                <span className={styles.summaryCount}>{neutral}</span>
                <span className={styles.summaryLabel}>Neutral</span>
            </div>
            <div className={styles.summaryDivider} />
            <div className={styles.summaryItem} style={{ color: '#10b981' }}>
                <span className={styles.summaryCount}>{supportive}</span>
                <span className={styles.summaryLabel}>Supportive</span>
            </div>
        </div>
    );
}

export default function StakeholderSentimentPanel({ stakeholders = [], sessionId, currentRound }) {
    const [refreshKey, setRefreshKey] = useState(0);

    const handleRefresh = useCallback(() => {
        setRefreshKey(k => k + 1);
    }, []);

    if (!stakeholders || stakeholders.length === 0) {
        return (
            <div className={styles.container}>
                <div className={styles.header}>
                    <h3 className={styles.title}>📊 Stakeholder Sentiment</h3>
                </div>
                <div className={styles.placeholder}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📊</div>
                    <p>No stakeholder data available. Stakeholder sentiment will appear once the simulation is running.</p>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div>
                    <h3 className={styles.title}>📊 Stakeholder Sentiment</h3>
                    {currentRound && (
                        <span className={styles.roundBadge}>Round {currentRound}</span>
                    )}
                </div>
                <button className={styles.refreshBtn} onClick={handleRefresh} title="Refresh">
                    🔄 Refresh
                </button>
            </div>

            <div className={styles.cardGrid}>
                {stakeholders.map((sh, idx) => (
                    <StakeholderCard key={sh.id || sh.name || idx} sh={sh} />
                ))}
            </div>

            <SummaryRow stakeholders={stakeholders} />
        </div>
    );
}
