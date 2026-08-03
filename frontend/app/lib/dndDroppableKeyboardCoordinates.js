/**
 * dndDroppableKeyboardCoordinates — a dnd-kit KeyboardCoordinateGetter that
 * SNAPS between droppable zones instead of nudging the dragged item by pixels.
 *
 * ── A11Y-F20 (WCAG 2.1.1) — real-browser pass, 2026-08-02 ──────────────────
 *
 * WHAT WAS WRONG, AND WHY THE LAST PASS MISSED IT
 *
 * Both mandatory gates — StakeholderMapModal (round 1) and
 * DoubleMaterialityMatrix (round 2) — registered `useSensor(KeyboardSensor)`
 * with no coordinate getter, so they inherited dnd-kit's default: translate
 * the dragged item by a fixed 25 px per arrow press. The previous
 * accessibility pass lifted a chip, pressed an arrow, saw dnd-kit's live
 * region announce a move, and recorded the gate as conformant. It is —
 * literally. Counted in a real browser, at 1600 x 1000:
 *
 *     lift                              -> over droppable "bank"
 *     6 x ArrowRight                    -> over "keep_satisfied"
 *     23 x ArrowRight                   -> over "manage_closely"
 *     bottom row needs the ArrowDowns too
 *
 * Ten stakeholders is on the order of two hundred key presses to complete a
 * gate a mouse user completes in ten drags — and the modal offers a five
 * minute timer while you do it. "Operable by keyboard" was true and useless,
 * which is exactly the failure mode a pass/fail check cannot see. It is not
 * reported as a 2.1.1 violation here; it is reported as the reason a 2.1.1
 * pass was not worth much.
 *
 * WHAT THIS DOES
 *
 * On an arrow key, take the droppables whose centres lie in that direction
 * from the dragged item's current centre, rank them by distance along the
 * pressed axis first (perpendicular drift breaks ties), and return the
 * coordinates that put the item over the winner. One press, one zone.
 *
 * Pointer dragging is untouched: this getter is only consulted by
 * KeyboardSensor. It is UI-layer only — no simulation state, no scoring, no
 * request shape changes. The two gates keep their existing collision
 * detection, their existing droppable ids, and their existing drop handlers;
 * all that changes is where an arrow press puts the item before the drop.
 */

import { KeyboardCode } from '@dnd-kit/core';

const DIRECTIONS = {
  [KeyboardCode.Right]: { axis: 'x', sign: 1 },
  [KeyboardCode.Left]: { axis: 'x', sign: -1 },
  [KeyboardCode.Down]: { axis: 'y', sign: 1 },
  [KeyboardCode.Up]: { axis: 'y', sign: -1 },
};

const centreOf = (rect) => ({
  x: rect.left + rect.width / 2,
  y: rect.top + rect.height / 2,
});

export function droppableKeyboardCoordinates(
  event,
  { currentCoordinates, context: { active, droppableRects, droppableContainers, collisionRect } },
) {
  const direction = DIRECTIONS[event.code];
  if (!direction) return undefined;

  // collisionRect is where the item is RIGHT NOW mid-drag; falling back to the
  // active node's rect covers the first press after the lift.
  const from = collisionRect
    ? centreOf(collisionRect)
    : active?.rect?.current?.translated
      ? centreOf(active.rect.current.translated)
      : null;
  if (!from) return undefined;

  const { axis, sign } = direction;
  const cross = axis === 'x' ? 'y' : 'x';

  let best = null;
  droppableContainers.forEach((container) => {
    if (!container || container.disabled) return;
    const rect = droppableRects.get(container.id);
    if (!rect) return;

    const to = centreOf(rect);
    const along = (to[axis] - from[axis]) * sign;
    // A zone must actually lie ahead. The 1px floor keeps a zone the item is
    // already centred on from being re-selected forever.
    if (along <= 1) return;

    const drift = Math.abs(to[cross] - from[cross]);
    // Along-axis distance dominates; drift only separates equals. Without
    // this a diagonal neighbour can beat the zone directly ahead.
    const score = along + drift * 2;
    if (!best || score < best.score) best = { score, to };
  });

  if (!best) return undefined;

  event.preventDefault();
  return {
    x: currentCoordinates.x + (best.to.x - from.x),
    y: currentCoordinates.y + (best.to.y - from.y),
  };
}

export default droppableKeyboardCoordinates;
