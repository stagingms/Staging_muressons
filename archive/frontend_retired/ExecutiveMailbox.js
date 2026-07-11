'use client';

import { useState, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import styles from './ExecutiveMailbox.module.css';
import { sanitizeHtml } from '@/app/utils/sanitize';

/**
 * ExecutiveMailbox — Fixed right-hand accordion panel.
 *
 * Active round: shows incoming narratives, reports, admin "God Mode" messages.
 * Previous rounds: collapse into read-only historical archive tabs.
 *
 * Props:
 *  - roundNumber:  current round (1–10)
 *  - events:       dict of current-round engine events
 *  - history:      array of past round snapshots
 *  - messages:     array of { id, round, type, title, body, read }
 *  - onMarkRead:   (messageId) => void
 */

const SAMPLE_ROUND_MESSAGES = {
    1: [
        { id: 'm1-1', type: 'narrative', title: 'Board Briefing', body: 'Welcome to Muressons Corporation. The board expects a sustainable growth trajectory over the next 10 semesters (5 years). Initial capital position is strong — deploy wisely.', read: false },
        { id: 'm1-2', type: 'report', title: 'ESG Baseline Report', body: 'All four business units are operational. Pharma and Electronics drive majority revenue. Note: Electronics carbon intensity is the highest across the group (72).', read: false },
        { id: 'm1-3', type: 'admin', title: '⚡ Facilitator Note', body: 'This is a learning simulation. Discuss trade-offs as a team before committing each round.', read: false },
    ],
};

// ── Crisis briefings per round (auto-injected into mailbox) ──
const ROUND_CRISES = {
    1: {
        title: '📋 Round 1 Crisis: ESG Foundation Audit',
        body: 'The board demands an initial ESG materiality assessment across all business units.\n\n'
            + '🅰 Option A — Full Supply-Chain Audit: Comprehensive investigation of all Scope 1–3 risks. High upfront cost but maximum visibility.\n'
            + '🅱 Option B — Materiality Screening: Targeted assessment of top-priority ESG risks. Balanced cost-benefit approach.\n'
            + '🅲 Option C — Desk Review Only: Minimal-cost paper review. Saves budget now but defers risk discovery.',
    },
    2: {
        title: '⚖️ Round 2 Crisis: Double Materiality Gate',
        body: 'The CFO requires all sustainability investments to pass a double materiality test.\n\n'
            + '🅰 Option A — Embed Double Materiality: Integrate full financial + impact materiality into all capital allocation. High governance cost.\n'
            + '🅱 Option B — Pilot Program: Test double materiality in two BUs before company-wide rollout.\n'
            + '🅲 Option C — Financial Materiality Only: Stick to traditional financial risk assessment. Low cost, but ESG blind spots remain.',
    },
    3: {
        title: '🏭 Round 3 Crisis: Scope 3 Supply Chain Disruption',
        body: 'Major Scope 3 emissions discovered in Electronics and Pharma supply chains. Regulators are watching.\n\n'
            + '🅰 Option A — Full Supply-Chain Decarbonisation: Overhaul supplier contracts with emissions targets. Expensive but comprehensive.\n'
            + '🅱 Option B — Tier-1 Supplier Engagement: Work with direct suppliers only. Moderate cost and partial coverage.\n'
            + '🅲 Option C — Reporting Compliance Only: Meet minimum disclosure requirements without operational changes.',
    },
    4: {
        title: '⚡ Round 4 Crisis: ESG Contagion Crisis',
        body: 'Negative ESG headlines from a competitor have triggered sector-wide scrutiny. Your reputation is under pressure.\n\n'
            + '🅰 Option A — Proactive Transparency Campaign: Release full ESG data publicly and launch stakeholder engagement. High cost, reputation boost.\n'
            + '🅱 Option B — Targeted Media Response: Issue press statements and engage key analysts. Moderate defence.\n'
            + '🅲 Option C — Wait and See: Monitor the situation without public action. Risk of further reputation erosion.',
    },
    5: {
        title: '🌪️ Round 5 Crisis: Climate Physical Risk Event',
        body: 'A severe climate event threatens your coastal manufacturing facilities.\n\n'
            + '🅰 Option A — Relocate & Fortify: Move critical operations inland and invest in climate-resilient infrastructure. Major CAPEX.\n'
            + '🅱 Option B — Insurance Upgrade: Strengthen insurance coverage and implement basic flood defences.\n'
            + '🅲 Option C — Accept Risk: Maintain current facilities with minimal adaptation. Low cost, high exposure.',
    },
    6: {
        title: '🤖 Round 6 Crisis: AI Ethics & Bias Scandal',
        body: 'Your Software division\'s AI hiring tool has been found to exhibit racial bias. Media attention is escalating.\n\n'
            + '🅰 Option A — Full AI Ethics Overhaul: Hire external auditors, rebuild algorithms, establish an AI Ethics Board. High cost, strong governance.\n'
            + '🅱 Option B — Patch & Retrain: Fix the specific bias, retrain the model, and issue a public apology.\n'
            + '🅲 Option C — Quietly Discontinue: Pull the tool without public acknowledgment. Low cost, reputation risk if exposed.',
    },
    7: {
        title: '♻️ Round 7 Crisis: Circular Economy Pivot',
        body: 'New EU regulations require circular economy compliance by 2035. First-mover advantage is available.\n\n'
            + '🅰 Option A — Full Circular Transformation: Redesign products for recyclability across all BUs. Cross-BU synergy potential. Major investment.\n'
            + '🅱 Option B — Pilot in Consumer Goods: Launch circularity in one BU as a proof of concept.\n'
            + '🅲 Option C — Lobby for Extension: Advocate for regulatory delays. Saves near-term cost but risks falling behind competitors.',
    },
    8: {
        title: '💧 Round 8 Crisis: Blue Water Stress',
        body: 'Your primary watershed has been reclassified as critically stressed. Water-dependent BUs face operational disruption.\n\n'
            + '🅰 Option A — Water Stewardship Program: Invest in watershed restoration and alternative water sources. Long-term resilience.\n'
            + '🅱 Option B — Efficiency Upgrades: Install water recycling systems in most-affected facilities.\n'
            + '🅲 Option C — Secure Rights: Purchase additional water extraction rights. Quick fix, potential community backlash.',
    },
    9: {
        title: '✊ Round 9 Crisis: Just Transition & Labor',
        body: 'Automation and green-transition layoffs have triggered labor unrest. Social license is eroding.\n\n'
            + '🅰 Option A — Just Transition Fund: Create a comprehensive reskilling program and transition support for affected workers. High cost, strong SL recovery.\n'
            + '🅱 Option B — Negotiate with Unions: Enter collective bargaining with enhanced severance packages.\n'
            + '🅲 Option C — Proceed with Automation: Continue planned automation without additional support. Cost-efficient, high social risk.',
    },
    10: {
        title: '📢 Round 10 Crisis: Activist Ultimatum — Grand Finale',
        body: 'A major activist fund has acquired 8% of Muressons shares and demands structural change. This is your final decision.\n\n'
            + '🅰 Option A — Embrace Transformation: Accept activist demands and commit to radical ESG restructuring. Signal long-term vision.\n'
            + '🅱 Option B — Negotiate Compromise: Offer partial concessions with a 3-year transition plan.\n'
            + '🅲 Option C — Defend the Status Quo: Reject demands and fight the proxy battle. Short-term cost, governance battle ahead.',
    },
};

export default function ExecutiveMailbox({
    roundNumber = 1,
    events = {},
    history = [],
    messages: externalMessages,
    onMarkRead,
}) {
    // Internal message state (uses external if provided, else sample)
    const [messages, setMessages] = useState(
        externalMessages || SAMPLE_ROUND_MESSAGES[1] || []
    );

    useEffect(() => {
        if (externalMessages) setMessages(externalMessages);
    }, [externalMessages]);

    // Auto-inject crisis briefing mail when round changes
    useEffect(() => {
        const crisis = ROUND_CRISES[roundNumber];
        if (!crisis) return;
        const crisisMailId = `crisis-briefing-r${roundNumber}`;
        setMessages((prev) => {
            // Don't add if already exists
            if (prev.some((m) => m.id === crisisMailId)) return prev;
            return [
                ...prev,
                {
                    id: crisisMailId,
                    round: roundNumber,
                    type: 'narrative',
                    title: crisis.title,
                    body: crisis.body,
                    read: false,
                },
            ];
        });
    }, [roundNumber]);

    // Split messages by round
    const currentMessages = useMemo(
        () => messages.filter((m) => (m.round || 1) === roundNumber),
        [messages, roundNumber]
    );

    const archivedRounds = useMemo(() => {
        const rounds = {};
        messages
            .filter((m) => (m.round || 1) < roundNumber)
            .forEach((m) => {
                const r = m.round || 1;
                if (!rounds[r]) rounds[r] = [];
                rounds[r].push(m);
            });
        return rounds;
    }, [messages, roundNumber]);

    // Add engine events as system messages for current round
    const eventMessages = useMemo(() => {
        const msgs = [];
        if (events.talent_penalty_applied && events.talent_penalty_applied > 1) {
            msgs.push({
                id: `evt-talent-${roundNumber}`,
                type: 'warning',
                title: '🧠 Brain-Drain Alert',
                body: `Software BU OPEX inflated by ${((events.talent_penalty_applied - 1) * 100).toFixed(1)}% due to low group reputation.`,
                read: false,
                round: roundNumber,
            });
        }
        if (events.strike_probabilities) {
            const highs = Object.entries(events.strike_probabilities)
                .filter(([, p]) => p > 0.3)
                .map(([bu, p]) => `${bu}: ${(p * 100).toFixed(0)}%`);
            if (highs.length) {
                msgs.push({
                    id: `evt-strike-${roundNumber}`,
                    type: 'warning',
                    title: '⚠️ Strike Risk Elevated',
                    body: `High strike probability: ${highs.join(', ')}`,
                    read: false,
                    round: roundNumber,
                });
            }
        }
        return msgs;
    }, [events, roundNumber]);

    const allCurrent = [...currentMessages, ...eventMessages];
    const unreadCount = allCurrent.filter((m) => !m.read).length;

    const [expandedArchive, setExpandedArchive] = useState(null);
    const [expandedMessage, setExpandedMessage] = useState(null);

    const stripHtml = (html) => {
        if (!html) return '';
        return html.replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    };

    const truncate = (text, max = 100, isHtml = false) => {
        const plain = isHtml ? stripHtml(text) : text;
        if (!plain || plain.length <= max) return plain;
        return plain.slice(0, max).trimEnd() + '…';
    };

    const handleMarkRead = (id) => {
        setMessages((prev) =>
            prev.map((m) => (m.id === id ? { ...m, read: true } : m))
        );
        onMarkRead?.(id);
    };

    const typeStyles = {
        narrative: styles.typeNarrative,
        report: styles.typeReport,
        admin: styles.typeAdmin,
        warning: styles.typeWarning,
    };

    const typeLabels = {
        narrative: 'NARRATIVE',
        report: 'REPORT',
        admin: 'FACILITATOR',
        warning: 'SYSTEM',
    };

    return (
        <aside className={styles.mailbox}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.headerTitle}>
                    <span>📬</span>
                    <h2>Executive Mailbox</h2>
                </div>
                {unreadCount > 0 && (
                    <span className={styles.badge}>{unreadCount}</span>
                )}
            </div>

            <div className={styles.content}>
                {/* Active round messages */}
                <div className={styles.section}>
                    <div className={styles.sectionLabel}>
                        <span className={styles.liveDot} />
                        Round {roundNumber} — Live
                    </div>

                    {allCurrent.length === 0 && (
                        <div className={styles.empty}>No messages this round</div>
                    )}

                    {allCurrent.map((msg, i) => (
                        <div
                            key={msg.id}
                            className={`${styles.message} ${!msg.read ? styles.unread : ''}`}
                            onClick={() => {
                                handleMarkRead(msg.id);
                                setExpandedMessage(msg);
                            }}
                            style={{ animationDelay: `${i * 60}ms` }}
                        >
                            <div className={styles.msgHeader}>
                                <span className={`${styles.typeBadge} ${typeStyles[msg.type] || ''}`}>
                                    {typeLabels[msg.type] || msg.type.toUpperCase()}
                                </span>
                                {!msg.read && <span className={styles.unreadDot} />}
                            </div>
                            <h3 className={styles.msgTitle}>{msg.title}</h3>
                            <p className={styles.msgBody}>{truncate(msg.body, 100, msg.html)}</p>
                            {msg.body && (msg.html ? stripHtml(msg.body).length > 100 : msg.body.length > 100) && (
                                <span className={styles.readMore}>Click to read full message ›</span>
                            )}
                        </div>
                    ))}
                </div>

                {/* Archived rounds */}
                {Object.keys(archivedRounds)
                    .sort((a, b) => Number(b) - Number(a))
                    .map((round) => {
                        const r = Number(round);
                        const isOpen = expandedArchive === r;
                        const items = archivedRounds[r];
                        return (
                            <div key={r} className={styles.archiveSection}>
                                <button
                                    className={styles.archiveToggle}
                                    onClick={() => setExpandedArchive(isOpen ? null : r)}
                                >
                                    <span className={styles.archiveIcon}>{isOpen ? '▾' : '▸'}</span>
                                    <span>Round {r}: Historical Record</span>
                                    <span className={styles.archiveCount}>{items.length}</span>
                                </button>
                                {isOpen && (
                                    <div className={styles.archiveBody}>
                                        {items.map((msg) => (
                                            <div
                                                key={msg.id}
                                                className={styles.archivedMessage}
                                                onClick={() => setExpandedMessage(msg)}
                                                style={{ cursor: 'pointer' }}
                                            >
                                                <span className={`${styles.typeBadge} ${styles.archived} ${typeStyles[msg.type] || ''}`}>
                                                    {typeLabels[msg.type] || msg.type.toUpperCase()}
                                                </span>
                                                <h4 className={styles.archivedTitle}>{msg.title}</h4>
                                                <p className={styles.archivedBody}>{truncate(msg.body, 80)}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
            </div>
            {/* ── Full Message Modal (portaled to body) ── */}
            {expandedMessage && typeof document !== 'undefined' && createPortal(
                <div className={styles.modalOverlay} onClick={() => setExpandedMessage(null)}>
                    <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                        <div className={styles.modalHeader}>
                            <span className={`${styles.typeBadge} ${typeStyles[expandedMessage.type] || ''}`}>
                                {typeLabels[expandedMessage.type] || expandedMessage.type?.toUpperCase()}
                            </span>
                            {expandedMessage.round && (
                                <span className={styles.modalRound}>Round {expandedMessage.round}</span>
                            )}
                            <button
                                className={styles.modalClose}
                                onClick={() => setExpandedMessage(null)}
                            >✕</button>
                        </div>
                        <h3 className={styles.modalTitle}>{expandedMessage.title}</h3>
                        {expandedMessage.html ? (
                            <div
                                className={`${styles.modalBody} ${styles.htmlArtifact}`}
                                dangerouslySetInnerHTML={{ __html: sanitizeHtml(expandedMessage.body) }}
                            />
                        ) : (
                            <div className={styles.modalBody}>{expandedMessage.body}</div>
                        )}
                    </div>
                </div>,
                document.body
            )}
        </aside>
    );
}
