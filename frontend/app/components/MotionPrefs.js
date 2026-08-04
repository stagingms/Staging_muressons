'use client';

/**
 * MotionPrefs — Slot: none (an invisible provider).
 *
 * tokens.css claims its blanket `prefers-reduced-motion` block "collapses every
 * animation/transition (framer-motion springs, heartbeat pulses, the ticker
 * marquee)". It cannot. That block overrides animation-duration,
 * animation-iteration-count, transition-duration and scroll-behavior — and
 * framer-motion uses none of them. It writes computed transform/opacity to
 * element.style on every frame, so a reduced-motion user still got the header's
 * infinite TIPPING POINT pulse, every whileHover/whileTap scale, and the 40px
 * modal slide.
 *
 * MotionConfig reducedMotion="user" is framer-motion's own switch: it reads the
 * media query and reduces transform-based animation to opacity-only for every
 * descendant motion component. One wrapper, whole tree.
 */
import { MotionConfig } from 'framer-motion';

export default function MotionPrefs({ children }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
