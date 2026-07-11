'use client';

import { useState, useRef, useEffect } from 'react';
import styles from './HelpTooltip.module.css';

const HELP_CONTENT = {
    dashboard_home: 'Overview of all active cohorts, key metrics, and alerts at a glance.',
    leaderboard: 'View and manage all active simulation sessions. Create new cohorts here.',
    audit_trail: 'Chronological log of all decisions, overrides, and events.',
    session_viewer: 'Inspect the detailed state of a specific session, including BU metrics.',
    registry: 'Manage player registrations, credentials, and team assignments.',
    pacing: 'Control round advancement: free-play, manual gating, or timed intervals.',
    undo_round: 'Roll back the latest round\'s decisions and state for a session.',
    notes: 'Add private or player-visible annotations to a session.',
    impersonate: 'View a team\'s dashboard from their perspective (read-only).',
    reports: 'Export session data as CSV or JSON for offline analysis.',
    timeline: 'Visual timeline showing progress through the 10-round simulation.',
    bonuses: 'Award bonus points and achievement badges to individual players.',
    sim_manager: 'Group and compare multiple simulations by facilitator.',
    peer_eval: 'Manage peer evaluations for team contribution assessment.',
    broadcast: 'Send messages to all or selected cohorts simultaneously.',
    crises: 'Configure and trigger crisis interventions and events.',
    overrides: 'Apply real-time God Mode overrides to simulation parameters.',
    messages: 'Inject narrative messages and alerts into player sessions.',
};

export default function HelpTooltip({ helpKey, children }) {
    const [visible, setVisible] = useState(false);
    const ref = useRef(null);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (ref.current && !ref.current.contains(e.target)) setVisible(false);
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const text = HELP_CONTENT[helpKey] || 'Help information not available.';

    return (
        <span className={styles.wrapper} ref={ref}>
            {children}
            <button className={styles.helpBtn} onClick={(e) => { e.stopPropagation(); setVisible(!visible); }} aria-label="Help">
                ?
            </button>
            {visible && (
                <div className={styles.tooltip}>
                    <div className={styles.tooltipArrow} />
                    <p className={styles.tooltipText}>{text}</p>
                </div>
            )}
        </span>
    );
}
