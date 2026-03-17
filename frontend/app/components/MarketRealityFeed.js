'use client';

import styles from './ExecutiveCockpit.module.css';

/**
 * MarketRealityFeed — News ticker + event alert overlay.
 *
 * Props:
 *  - items: [{ type: 'info'|'alert', text: string }]
 *  - activeAlert: { icon, title, body } — overrides feed with stark warning
 */
export default function MarketRealityFeed({ items = [], activeAlert = null }) {
  if (activeAlert) {
    return (
      <div className={styles.feedContainer}>
        <div className={styles.feedTitle}>📰 Market Reality</div>
        <div className={styles.eventPopup}>
          <div className={styles.eventPopupIcon}>{activeAlert.icon || '⚠️'}</div>
          <div className={styles.eventPopupTitle}>{activeAlert.title}</div>
          <div className={styles.eventPopupBody}>{activeAlert.body}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.feedContainer}>
      <div className={styles.feedTitle}>📰 Market Reality Feed</div>
      {items.map((item, i) => (
        <div
          key={i}
          className={`${styles.feedItem} ${item.type === 'alert' ? styles.feedItemAlert : styles.feedItemInfo}`}
        >
          {item.text}
        </div>
      ))}
      {items.length === 0 && (
        <div className={styles.feedItem} style={{ color: '#94a3b8', textAlign: 'center' }}>
          No market events this round
        </div>
      )}
    </div>
  );
}
