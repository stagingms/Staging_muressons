'use client';

/**
 * RoundChecklist — where you are in the round.
 *
 * HISTORY, because the shape keeps being the problem rather than the content:
 *   v1 was position:fixed and dismissible, so a flow indicator could cover the
 *   option cards and then be closed. V-C docked it in flow and removed the ✕.
 *   That fixed the behaviour and left the appearance: a rgba(255,255,255,0.98)
 *   slab with rounded corners and a drop shadow, floating in a dark cockpit.
 *   It was the loudest object on the screen, and it is the one object on the
 *   screen that asks for nothing. A status readout should not out-shout the
 *   decision it is describing, nor the button that commits it.
 *
 * It is now a row of words inside the action bar: done steps in the positive
 * token, the current step in the accent with a dot, the rest muted. No card,
 * no shadow, no white. It sits to the left of the commit control so "where am
 * I" and "what do I press" read as one object.
 *
 * The ARROWS are gone too. Order already conveys order; they were a second
 * row of chevrons carrying nothing, and at five steps they cost about 60px of
 * horizontal room the labels needed.
 */
export default function RoundChecklist({
  roundNumber,
  hasReadBriefing,
  hasCompletedStakeholderMap,
  hasSubmittedMatrix,
  hasDecision,
  hasAllocated,
  hasCommitted,
}) {
  const steps = [];

  steps.push({ id: 'briefing', label: 'Briefing', done: hasReadBriefing !== false });
  if (roundNumber === 1) {
    steps.push({ id: 'stakeholder', label: 'Stakeholder map', done: hasCompletedStakeholderMap });
  }
  if (roundNumber === 2) {
    steps.push({ id: 'csrd', label: 'Materiality assessment', done: hasSubmittedMatrix });
  }
  steps.push({ id: 'decision', label: 'Decision', done: hasDecision });
  steps.push({ id: 'allocation', label: 'Capital', done: hasAllocated });
  steps.push({ id: 'commit', label: 'Commit', done: hasCommitted });

  const completed = steps.filter((s) => s.done).length;
  // The first not-done step is where the player actually is.
  const currentIdx = steps.findIndex((s) => !s.done);

  return (
    <>
      <style>{`
        .rc-steps {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 4px 18px;
          font-size: 13px;
          line-height: 1.4;
          min-width: 0;
        }
        .rc-step { display: flex; align-items: center; gap: 6px; white-space: nowrap; }
        .rc-done    { color: var(--positive-text); }
        .rc-now     { color: var(--accent); font-weight: 600; }
        .rc-todo    { color: var(--text-muted); }
        /* A mark, not an emoji: a tick for done and a filled dot for the step
           you are on. Both are aria-hidden — the state is in the visually
           hidden text beside each label, so a screen reader hears "Decision,
           current step" rather than a checkmark character. */
        .rc-mark { font-size: 11px; line-height: 1; }
        .rc-count {
          margin-left: auto;
          font-size: 13px;
          color: var(--text-muted);
          font-variant-numeric: tabular-nums;
          white-space: nowrap;
        }
        .rc-sr {
          position: absolute; width: 1px; height: 1px;
          overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
        }
        @media (max-width: 1100px) {
          .rc-steps { gap: 4px 12px; font-size: 12px; }
        }
      `}</style>
      <nav className="rc-steps" aria-label="Round progress">
        {steps.map((step, i) => (
          <span
            key={step.id}
            className={`rc-step ${step.done ? 'rc-done' : i === currentIdx ? 'rc-now' : 'rc-todo'}`}
            aria-current={i === currentIdx ? 'step' : undefined}
          >
            <span className="rc-mark" aria-hidden="true">
              {step.done ? '✓' : i === currentIdx ? '●' : '○'}
            </span>
            {step.label}
            <span className="rc-sr">
              {step.done ? ' — done' : i === currentIdx ? ' — current step' : ' — not started'}
            </span>
          </span>
        ))}
        <span className="rc-count">{completed} of {steps.length}</span>
      </nav>
    </>
  );
}
