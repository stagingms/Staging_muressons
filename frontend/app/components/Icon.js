'use client';

/**
 * Icon — the player surface's icon vocabulary, as SVG.
 *
 * WHY THIS EXISTS
 *   The player tree carries 644 pictographic glyphs. Three things are wrong
 *   with using emoji for them, and only the first is cosmetic:
 *
 *   1. They render differently on every platform. ⚖ is a line drawing on
 *      Windows, a full-colour object on macOS, and a different full-colour
 *      object on Android. A facilitator's projected screen and a player's
 *      laptop do not agree on what the materiality gate looks like.
 *
 *   2. A screen reader announces the CLDR name. "⚖" is read as "balance
 *      scale", inside a heading that already says "Double Materiality Gate" —
 *      so the decoration is announced and the meaning is duplicated. Several
 *      of these sit next to their own label.
 *
 *   3. They cannot take a colour. An emoji ignores `color`, so a state change
 *      that should tint an icon has to swap the glyph instead — which is how
 *      ✅/❌/⚠ ended up encoding state in a way no token can reach.
 *
 * currentColor, DELIBERATELY
 *   Every path here is stroke="currentColor" with no fill. That makes the set
 *   independent of the palette work in 6.3: an icon takes the colour of the
 *   text around it, so whatever --danger, --positive and --caution settle on,
 *   these follow without being touched again. It is also why this could ship
 *   before the palette was finished rather than after it.
 *
 * ACCESSIBILITY
 *   Decorative by default: aria-hidden, focusable={false}, no title. An icon
 *   beside its own label is decoration, and that is the majority case here.
 *   Pass `label` only where the icon is the ONLY carrier of meaning; it then
 *   becomes role="img" with an accessible name. There is no third mode,
 *   because "sometimes announced" is how you get a label read twice.
 *
 * SIZE
 *   A 24px grid, rendered at 1em by default so it tracks the type scale
 *   rather than fighting it. Pass a number for a fixed pixel size.
 */

/* 24x24, 2px stroke, round caps. Geometric rather than illustrative: these
   sit at 12-17px most of the time, where detail becomes noise. */
const PATHS = {
  warning:    <><path d="M12 3.5 2.5 20h19L12 3.5Z" /><path d="M12 10v4" /><path d="M12 17.2v.1" /></>,
  check:      <path d="m4 12.5 5.5 5.5L20 6.5" />,
  cross:      <><path d="M5.5 5.5 18.5 18.5" /><path d="M18.5 5.5 5.5 18.5" /></>,
  chart:      <><path d="M4 20V10" /><path d="M10 20V4" /><path d="M16 20v-7" /><path d="M22 20H2" /></>,
  trendUp:    <><path d="m3 16 5.5-5.5 4 4L21 6" /><path d="M15 6h6v6" /></>,
  trendDown:  <><path d="m3 8 5.5 5.5 4-4L21 18" /><path d="M15 18h6v-6" /></>,
  globe:      <><circle cx="12" cy="12" r="9" /><path d="M3 12h18" /><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18Z" /></>,
  clipboard:  <><path d="M9 4h6v3H9z" /><path d="M15 5.5h2.5v15h-11v-15H9" /><path d="M9 12h6" /><path d="M9 16h4" /></>,
  scales:     <><path d="M12 4v16" /><path d="M6 8h12" /><path d="M3 15 6 8l3 7a3 3 0 0 1-6 0Z" /><path d="M15 15l3-7 3 7a3 3 0 0 1-6 0Z" /></>,
  money:      <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v10" /><path d="M14.5 9.5a2.5 2.5 0 0 0-5 .3c0 2.7 5 1.4 5 4.2a2.5 2.5 0 0 1-5 .3" /></>,
  leaf:       <><path d="M4 20C4 11 10 5 20 5c0 10-6 15-13 15H4Z" /><path d="M4 20C8 16 12 13 17 11" /></>,
  bolt:       <path d="M13.5 3 5 13.5h5.5L10 21l8.5-10.5H13L13.5 3Z" />,
  factory:    <><path d="M3 20V11l5 3V11l5 3V7l8 4v9H3Z" /><path d="M7 20v-3" /><path d="M12 20v-3" /><path d="M17 20v-3" /></>,
  thermometer:<><path d="M14 14.8V5a2 2 0 1 0-4 0v9.8a4.5 4.5 0 1 0 4 0Z" /><path d="M12 9v7" /></>,
  bank:       <><path d="M3 9.5 12 4l9 5.5" /><path d="M5 10v8" /><path d="M10 10v8" /><path d="M14 10v8" /><path d="M19 10v8" /><path d="M3 20.5h18" /></>,
  lock:       <><rect x="4.5" y="10.5" width="15" height="10" rx="2" /><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" /></>,
  people:     <><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0" /><path d="M16 5.2a3.5 3.5 0 0 1 0 5.6" /><path d="M17.5 14.2A6.5 6.5 0 0 1 21.5 20" /></>,
  shield:     <path d="M12 3 4.5 6v6c0 4.5 3 7.7 7.5 9 4.5-1.3 7.5-4.5 7.5-9V6L12 3Z" />,
  clock:      <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5.2l3.4 2" /></>,
  target:     <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="4" /><circle cx="12" cy="12" r="0.6" /></>,
};

export const ICON_NAMES = Object.keys(PATHS);

export default function Icon({ name, size, label, className, style, strokeWidth = 2 }) {
  const d = PATHS[name];
  /* An unknown name renders NOTHING rather than a placeholder box. A missing
     icon is a small hole; a placeholder is a small hole that looks deliberate,
     and it ships. */
  if (!d) return null;

  const px = typeof size === 'number' ? `${size}px` : '1em';

  return (
    <svg
      viewBox="0 0 24 24"
      width={px}
      height={px}
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={{ flexShrink: 0, verticalAlign: '-0.125em', ...style }}
      {...(label
        ? { role: 'img', 'aria-label': label }
        : { 'aria-hidden': 'true', focusable: 'false' })}
    >
      {d}
    </svg>
  );
}
