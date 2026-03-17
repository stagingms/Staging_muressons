'use client';

import styles from './GameOverSummary.module.css';

const PROFILES = {
    regenerative_titan: { icon: '🌱', gradient: 'linear-gradient(135deg, #10b981, #059669)', title: 'Regenerative Titan' },
    derisked_safe_haven: { icon: '🛡️', gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)', title: 'De-risked Safe Haven' },
    fragile_giant: { icon: '⚠️', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', title: 'Fragile Giant' },
    stranded_relic: { icon: '💀', gradient: 'linear-gradient(135deg, #ef4444, #b91c1c)', title: 'Stranded Relic' },
};

/**
 * GameOverSummary — Final screen after Boardroom Showdown.
 * Simulation is definitively over. Player can download report or review scorecard.
 */
export default function GameOverSummary({ data, businessUnits, globalState, history, onReviewScorecard }) {
    const d = data || {};
    const theme = PROFILES[d.profile] || PROFILES.fragile_giant;

    const handleDownload = () => {
        // Open the scorecard which has the full report download capability
        if (onReviewScorecard) {
            onReviewScorecard();
        }
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.container}>
                {/* Completion Badge */}
                <div className={styles.badge}>SIMULATION COMPLETE</div>

                {/* Hero */}
                <div className={styles.hero} style={{ background: theme.gradient }}>
                    <span className={styles.heroEmoji}>{theme.icon}</span>
                    <h1 className={styles.heroTitle}>{d.profile_title || theme.title}</h1>
                    <p className={styles.heroDesc}>{d.profile_description || 'Your strategic journey has concluded.'}</p>
                </div>

                {/* Final Stats */}
                <div className={styles.statsGrid}>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Terminal Value</span>
                        <span className={styles.statValue}>${((d.terminal_value || 0) / 1_000_000).toFixed(2)}M</span>
                    </div>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Regenerative Multiple</span>
                        <span className={styles.statValue}>{(d.regenerative_multiple || 0).toFixed(2)}×</span>
                    </div>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Rounds Played</span>
                        <span className={styles.statValue}>10</span>
                    </div>
                </div>

                {/* Message */}
                <div className={styles.message}>
                    <h2>📋 Your Board Presentation Is Complete</h2>
                    <p>
                        You have presented your strategic recommendation to the Board of Directors.
                        The simulation is now concluded. You may download your Balanced Scorecard report
                        or review your performance across all 10 rounds.
                    </p>
                </div>

                {/* Actions */}
                <div className={styles.actions}>
                    <button className={styles.primaryBtn} onClick={onReviewScorecard}>
                        📊 Review Balanced Scorecard
                    </button>
                    <button className={styles.secondaryBtn} onClick={handleDownload}>
                        📥 Download Report (PDF)
                    </button>
                    <button className={styles.outlineBtn} onClick={() => window.location.reload()}>
                        🔄 Start New Simulation
                    </button>
                </div>

                {/* Footer */}
                <div className={styles.footer}>
                    <p>Muressons Global Command — Sustainability Strategy Simulation</p>
                    <p>© 2050 Board of Directors Meeting</p>
                </div>
            </div>
        </div>
    );
}
