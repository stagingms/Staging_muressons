/**
 * Geometry for the player's always-visible Logout control.
 *
 * The control is `position: fixed` in the top-right corner (ArchetypeReveal,
 * BoardroomShowdown, CrisisAlerts, RoundBriefing) so it stays reachable while
 * those screens scroll. Being fixed, it takes part in NO host layout — which
 * means any host that puts content at its own right edge will have that
 * content painted UNDER the button.
 *
 * That is exactly what happened on the Year-5 reveal: the status bar's
 * "BANKRUPT · Grade F" pill sits flush right, and the Logout button landed on
 * top of it, clipping the grade the whole screen exists to deliver.
 *
 * So a host with right-edge content must reserve `LOGOUT_GUTTER` on its right.
 * Keeping the numbers here — rather than as a literal in a CSS module — means
 * the button's footprint and the space reserved for it come from one place and
 * cannot drift apart. Hosts whose header content is centred (Boardroom,
 * RoundBriefing) need no gutter; the corner is empty for them.
 *
 * Widths were measured in the browser at the button's real font
 * (700 11.52px 'DM Sans'), padding 6px 14px:
 *     "🚪 Logout"           →  86px
 *     "⚠️ Confirm Logout?"  → 140px   ← the state that must fit
 * MIN_WIDTH pins the button to the wider of the two so it does not resize
 * when it flips to the confirm state, and gives the emoji fallback fonts a
 * few pixels of slack.
 */

export const LOGOUT_TOP = 12;
export const LOGOUT_RIGHT = 16;

/** Pinned to the widest label state (140px measured) + emoji slack. */
export const LOGOUT_MIN_WIDTH = 152;

/** Breathing room between the button and whatever the host renders next to it. */
export const LOGOUT_CLEARANCE = 12;

/** What a host with right-edge content must reserve on its right side. */
export const LOGOUT_GUTTER = LOGOUT_RIGHT + LOGOUT_MIN_WIDTH + LOGOUT_CLEARANCE;

/**
 * The fixed-position part of the button's style. Hosts keep their own colours
 * (each screen tints it for its theme); this pins only the geometry that the
 * gutter is calculated from.
 */
export const logoutAnchorStyle = (zIndex) => ({
  position: 'fixed',
  top: LOGOUT_TOP,
  right: LOGOUT_RIGHT,
  zIndex,
  minWidth: LOGOUT_MIN_WIDTH,
  justifyContent: 'center',
  whiteSpace: 'nowrap',
});
