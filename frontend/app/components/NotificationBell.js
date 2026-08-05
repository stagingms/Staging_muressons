'use client';
import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * NotificationBell — Real-time notification bell for admin dashboards.
 * Shows God Mode events (settings changes, pacing overrides, freeze events)
 * as a dropdown notification panel. Badge shows unread count.
 *
 * Props:
 *   activityLog: Array of log entries from WebSocket handler
 *   
 * God Mode events are identified by log.type === 'god_mode'.
 */
export default function NotificationBell({ activityLog = [] }) {
    const [isOpen, setIsOpen] = useState(false);
    const [lastSeenCount, setLastSeenCount] = useState(0);
    const ref = useRef(null);

    // Filter only god_mode and important system events
    const notifications = activityLog.filter(
        e => e.type === 'god_mode' || e.severity === 'critical' || e.severity === 'warning'
    );

    const unreadCount = Math.max(0, notifications.length - lastSeenCount);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handler = (e) => {
            if (ref.current && !ref.current.contains(e.target)) setIsOpen(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const handleOpen = useCallback(() => {
        setIsOpen(prev => !prev);
        if (!isOpen) setLastSeenCount(notifications.length);
    }, [isOpen, notifications.length]);

    const severityColors = {
        critical: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6',
    };

    return (
        <div ref={ref} style={{ position: 'relative' }}>
            <button
                onClick={handleOpen}
                title={`${unreadCount} new notifications`}
                style={{
                    background: 'none',
                    border: `1px solid ${unreadCount > 0 ? 'rgba(245,158,11,0.4)' : 'rgba(148,163,184,0.2)'}`,
                    color: unreadCount > 0 ? '#f59e0b' : 'var(--text-muted)',
                    fontSize: '1rem',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    position: 'relative',
                    transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                    animation: unreadCount > 0 ? 'bellShake 0.6s ease-in-out' : 'none',
                }}
            >
                🔔
                {unreadCount > 0 && (
                    <span style={{
                        position: 'absolute', top: '-4px', right: '-4px',
                        background: '#ef4444', color: '#fff',
                        fontSize: 'var(--type-caption)', fontWeight: 800,
                        width: '16px', height: '16px',
                        borderRadius: '50%',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        border: '2px solid var(--bg-card)',
                    }}>
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            {/* Shake animation */}
            <style dangerouslySetInnerHTML={{ __html: `
                @keyframes bellShake {
                    0%, 100% { transform: rotate(0); }
                    20% { transform: rotate(12deg); }
                    40% { transform: rotate(-12deg); }
                    60% { transform: rotate(6deg); }
                    80% { transform: rotate(-6deg); }
                }
            `}} />

            {/* Dropdown panel */}
            {isOpen && (
                <div style={{
                    position: 'absolute', top: 'calc(100% + 8px)', right: 0,
                    width: '340px', maxHeight: '400px', overflowY: 'auto',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '12px',
                    boxShadow: '0 12px 40px rgba(0,0,0,0.25)',
                    zIndex: 9000,
                    padding: '0',
                }}>
                    <div style={{
                        padding: '0.75rem 1rem',
                        borderBottom: '1px solid var(--border-subtle)',
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    }}>
                        <span style={{ fontWeight: 700, fontSize: '0.82rem', color: 'var(--text-primary)' }}>
                            🔔 Notifications
                        </span>
                        <span style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)' }}>
                            {notifications.length} events
                        </span>
                    </div>

                    {notifications.length === 0 ? (
                        <div style={{
                            padding: '2rem', textAlign: 'center',
                            color: 'var(--text-muted)', fontSize: '0.8rem',
                        }}>
                            No notifications yet.<br/>
                            <span style={{ fontSize: 'var(--type-caption)' }}>God Mode changes will appear here in real-time.</span>
                        </div>
                    ) : (
                        <div style={{ padding: '0.4rem' }}>
                            {notifications.slice(0, 20).map((n, i) => (
                                <div key={i} style={{
                                    padding: '0.6rem 0.8rem',
                                    borderRadius: '8px',
                                    marginBottom: '2px',
                                    background: i < unreadCount ? 'rgba(245,158,11,0.04)' : 'transparent',
                                    borderLeft: `3px solid ${severityColors[n.severity] || '#64748b'}`,
                                    transition: 'background 0.15s',
                                }}>
                                    <div style={{
                                        fontSize: '0.78rem', color: 'var(--text-primary)',
                                        fontWeight: i < unreadCount ? 600 : 400,
                                        lineHeight: 1.4,
                                    }}>
                                        {n.message}
                                    </div>
                                    <div style={{
                                        fontSize: 'var(--type-caption)', color: 'var(--text-muted)',
                                        marginTop: '0.2rem',
                                    }}>
                                        {n.timestamp}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
