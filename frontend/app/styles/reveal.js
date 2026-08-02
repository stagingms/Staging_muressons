/**
 * reveal.js — the "reveal language" (Move 4) in JS form.
 *
 * Framer-motion takes easings as bezier-coefficient arrays and durations in
 * SECONDS, so it cannot read the CSS custom properties in styles/tokens.css
 * directly. These constants mirror those tokens 1:1 — the single signature
 * curve, the ceremony overshoot, and the shared durations/rhythm — so a
 * motion.div entrance feels identical to a CSS `.reveal-panel` entrance.
 *
 * Keep in sync with the `--reveal-*` block in styles/tokens.css.
 * Pure presentation: no state, no logic.
 */

// Signature "settle" curve — cubic-bezier(0.16, 1, 0.3, 1).
export const REVEAL_EASE = [0.16, 1, 0.3, 1];

// Ceremony overshoot — cubic-bezier(0.2, 1.4, 0.4, 1). Springy "stamp" pop.
export const REVEAL_POP = [0.2, 1.4, 0.4, 1];

// Durations (seconds — framer-motion's unit).
export const REVEAL_DUR = 0.52;       // panels / cards        (--reveal-dur)
export const REVEAL_DUR_SLOW = 0.72;  // headlines / hero text (--reveal-dur-slow)

// Step between sequenced items (seconds).
export const REVEAL_STAGGER = 0.09;   // (--reveal-stagger)

/** Ready-made transition presets for the two most common entrances. */
export const revealTransition = (delay = 0) => ({ duration: REVEAL_DUR, ease: REVEAL_EASE, delay });
export const revealHeadlineTransition = (delay = 0) => ({ duration: REVEAL_DUR_SLOW, ease: REVEAL_EASE, delay });
