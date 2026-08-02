'use client';

/**
 * ConnectionBanner — surfaces a stale/reconnecting state (audit #11).
 *
 * The player board polls in the background; when those polls fail, the numbers
 * on screen silently go stale. This banner makes that visible so a player under
 * time pressure knows the board may be out of date and is reconnecting, rather
 * than trusting a frozen screen.
 *
 * Drop it near the top of the player board:
 *   const { connectionState, lastSyncAt } = sim;
 *   <ConnectionBanner state={connectionState} lastSyncAt={lastSyncAt} />
 *
 * Renders nothing while the connection is healthy. Uses tokens.css semantic
 * colors (no raw hex — see CLAUDE.md).
 */

import { useEffect, useState } from 'react';

export default function ConnectionBanner({ state = 'ok', lastSyncAt = null }) {
  const [, setTick] = useState(0);

  // Re-render every 5s so the "updated Ns ago" label stays current while stale.
  useEffect(() => {
    if (state === 'ok') return undefined;
    const t = setInterval(() => setTick((n) => n + 1), 5000);
    return () => clearInterval(t);
  }, [state]);

  if (state === 'ok') return null;

  let ago = '';
  if (lastSyncAt) {
    const secs = Math.max(0, Math.round((Date.now() - lastSyncAt) / 1000));
    ago = secs < 60 ? `${secs}s ago` : `${Math.round(secs / 60)}m ago`;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.4rem 0.9rem',
        fontSize: '0.85rem',
        fontWeight: 600,
        color: 'var(--color-caution-fg, var(--color-caution, #92400e))',
        background: 'var(--color-caution-bg, rgba(245, 158, 11, 0.12))',
        borderBottom: '1px solid var(--color-caution, #f59e0b)',
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: 'var(--color-caution, #f59e0b)',
          animation: 'mur-pulse 1.4s ease-in-out infinite',
        }}
      />
      <span>Reconnecting to the server — the board may be out of date{ago ? ` (updated ${ago})` : ''}.</span>
      <style>{`@keyframes mur-pulse{0%,100%{opacity:1}50%{opacity:0.3}}`}</style>
    </div>
  );
}
