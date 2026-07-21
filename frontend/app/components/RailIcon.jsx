'use client';

/**
 * RailIcon — a small, consistent monochrome glyph set for the rail chrome.
 *
 * The app has no icon font, so the rail grew an emoji zoo (📰 📊 🚨 📋 🔍 …)
 * at mismatched weights and hues. These stroke icons inherit `currentColor`,
 * so a caller sets the semantic colour once (neutral info, red alert, amber
 * breaking) and the glyph matches — one visual language instead of many.
 *
 * Chrome only: state/identity emoji (persona avatars, stakeholder mood,
 * severity count badges) keep their emoji — colour there carries meaning.
 *
 * Pure presentation. No state, no logic.
 */

const ICONS = {
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5" />
      <path d="M12 8h.01" />
    </>
  ),
  alertTriangle: (
    <>
      <path d="M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.7 3.86a2 2 0 0 0-3.4 0z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </>
  ),
  zap: <path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z" />,
  list: (
    <>
      <path d="M8 6h13M8 12h13M8 18h13" />
      <path d="M3 6h.01M3 12h.01M3 18h.01" />
    </>
  ),
  barChart: <path d="M12 20V10M18 20V4M6 20v-4" />,
  rss: (
    <>
      <path d="M4 11a9 9 0 0 1 9 9" />
      <path d="M4 4a16 16 0 0 1 16 16" />
      <circle cx="5" cy="19" r="1" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
    </>
  ),
  chevronDown: <path d="M6 9l6 6 6-6" />,
  target: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="3.5" />
    </>
  ),
  rows: (
    <>
      <rect x="3" y="5" width="18" height="5" rx="1" />
      <rect x="3" y="14" width="18" height="5" rx="1" />
    </>
  ),
};

export default function RailIcon({ name, size = 13, color = 'currentColor', strokeWidth = 2, style, className }) {
  const glyph = ICONS[name];
  if (!glyph) return null;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
      style={{ flexShrink: 0, display: 'block', ...style }}
    >
      {glyph}
    </svg>
  );
}
