'use client';

import styles from './ExecutiveCockpit.module.css';

/**
 * MarketRealityFeed — News ticker + event alert overlay.
 *
 * Props:
 *  - items: [{ type: 'info'|'alert', text: string }]
 *  - activeAlert: { icon, title, body, isBlackSwan? } — overrides feed with stark warning
 */

const SEVERITY_META = {
  alert: { icon: '🚨', badge: 'ALERT', badgeColor: '#ef4444', badgeBg: 'rgba(239,68,68,0.1)' },
  info: { icon: '📊', badge: 'INFO', badgeColor: '#3b82f6', badgeBg: 'rgba(59,130,246,0.08)' },
};

export default function MarketRealityFeed({ items = [], activeAlert = null }) {
  if (activeAlert) {
    const isBlackSwan = activeAlert.isBlackSwan;
    return (
      <div className={styles.feedContainer}>
        <div className={styles.feedTitle}>
          {isBlackSwan ? '🦢 BLACK SWAN EVENT' : '📰 Market Reality'}
        </div>
        <div
          className={`${styles.eventPopup} ${isBlackSwan ? styles.eventPopupBlackSwan : ''}`}
          style={isBlackSwan ? {
            background: 'linear-gradient(135deg, #1a0000, #2d0000)',
            border: '2px solid #ef4444',
            boxShadow: '0 0 30px rgba(239, 68, 68, 0.3)',
            animation: 'none',
          } : undefined}
        >
          <div className={styles.eventPopupIcon}>
            {activeAlert.icon || '⚠️'}
          </div>
          <div
            className={styles.eventPopupTitle}
            style={isBlackSwan ? { color: '#ef4444', fontWeight: 800, fontSize: '1rem' } : undefined}
          >
            {activeAlert.title}
          </div>
          <div
            className={styles.eventPopupBody}
            style={isBlackSwan ? { color: '#fecaca', fontSize: '0.82rem', lineHeight: 1.5 } : undefined}
          >
            {activeAlert.body}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.feedContainer}>
      <div className={styles.feedTitle}>📰 Market Reality Feed</div>
      {items.map((item, i) => {
        const meta = SEVERITY_META[item.type] || SEVERITY_META.info;
        return (
          <div
            key={i}
            className={`${styles.feedItem} ${item.type === 'alert' ? styles.feedItemAlert : styles.feedItemInfo}`}
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <div style={{
              display: 'flex', alignItems: 'flex-start', gap: 6,
            }}>
              <span style={{ fontSize: '0.82rem', flexShrink: 0, lineHeight: 1.5 }}>{meta.icon}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 5, marginBottom: 2,
                }}>
                  <span style={{
                    fontSize: '0.48rem', fontWeight: 800,
                    padding: '1px 4px', borderRadius: 3,
                    background: meta.badgeBg, color: meta.badgeColor,
                    letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                  }}>
                    {meta.badge}
                  </span>
                </div>
                <div style={{ fontSize: '0.7rem', lineHeight: 1.5 }}>
                  {item.text}
                </div>
              </div>
            </div>
          </div>
        );
      })}
      {items.length === 0 && (
        <div className={styles.feedItem} style={{ color: '#94a3b8', textAlign: 'center' }}>
          <span style={{ fontSize: '1.2rem', display: 'block', marginBottom: 4 }}>📭</span>
          No market events this round
        </div>
      )}
    </div>
  );
}
