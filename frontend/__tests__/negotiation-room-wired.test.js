/**
 * The Stakeholder Negotiation Room must have a reachable player entry point.
 *
 * Reported: "the stakeholder negotiation room is not functional."
 *
 * Every part of the feature had shipped — the endpoints, the rules engine, the
 * concession pricing, the per-cohort toggle, the facilitator transcript viewer,
 * the component itself — and NOTHING imported NegotiationRoom.js. An orphaned
 * component compiles, lints, type-checks and passes every unit test written
 * against it. The only thing it cannot do is appear.
 *
 * That is the failure mode this file exists to catch, and it is not unique to
 * negotiation rooms: the same "built but never wired" shape produced the
 * real-world case cards and the cohort-trends toggle defects in the same week.
 * A test that imports the component would have passed the whole time; the
 * assertion has to be about the CALLER.
 */
const fs = require('fs');
const path = require('path');

const COMPONENTS = path.join(__dirname, '..', 'app', 'components');
const cockpit = fs.readFileSync(path.join(COMPONENTS, 'ExecutiveCockpit.js'), 'utf8');
const panel = fs.readFileSync(path.join(COMPONENTS, 'StakeholderAgentPanel.js'), 'utf8');

describe('negotiation room is reachable from the cockpit', () => {
  test('the cockpit imports NegotiationRoom', () => {
    expect(cockpit).toMatch(/import\(['"]\.\/NegotiationRoom['"]\)/);
  });

  test('it is actually rendered, not merely imported', () => {
    expect(cockpit).toMatch(/<NegotiationRoom[\s\n]/);
  });

  test('the stakeholder panel receives an onRequestMeeting handler', () => {
    expect(cockpit).toMatch(/onRequestMeeting=\{pedToggles\.negotiation_rooms_enabled/);
  });

  test('the handler opens the room it was given', () => {
    expect(cockpit).toMatch(/setNegotiationAgentId\(agentId\)/);
  });

  test('the entry point is gated on the cohort toggle', () => {
    // Off by default; the facilitator opts a cohort in. The gate here is only
    // about showing the door — negotiation.py re-checks on every call.
    const i = cockpit.indexOf('onRequestMeeting={pedToggles.negotiation_rooms_enabled');
    expect(cockpit.slice(i, i + 200)).toMatch(/:\s*null/);
  });

  test('the panel forwards the handler down to the agent card', () => {
    expect(panel).toMatch(/onRequestMeeting=\{onRequestMeeting\}/);
    expect(panel).toMatch(/onRequestMeeting\(agent\.agent_id\)/);
  });

  test('the meeting button appears only for hostile or triggered agents', () => {
    // Assert the RULE, not its spelling. The predicate was extracted to
    // `canNegotiate` so the collapsed-card hint chip and the button itself
    // cannot drift apart — one of them showing while the other does not would
    // be worse than either alone.
    expect(panel).toMatch(/const canNegotiate\s*=\s*!!onRequestMeeting/);
    expect(panel).toMatch(/\['hostile', 'triggered'\]\.includes\(action\?\.stage \|\| agent\?\.stage\)/);
    // …and it is what actually gates the button.
    const i = panel.indexOf('🤝 Request a meeting');
    expect(i).toBeGreaterThan(-1);
    expect(panel.slice(Math.max(0, i - 900), i)).toMatch(/\{canNegotiate && \(/);
  });

  test('the collapsed card hints that a negotiation is available', () => {
    // Reported: "the negotiation room is not visible". Even with the cohort
    // toggle ON and an agent at the table, the button lived inside the
    // expanded card, so a player saw nothing until they expanded that exact
    // row. The chip is the only affordance on the collapsed card.
    expect(panel).toMatch(/Open to negotiation/);
    const i = panel.indexOf('Open to negotiation');
    // 600 chars clipped the guard mid-token once styling grew; anchor the
    // guard itself instead of hoping a fixed window reaches it.
    const guard = panel.lastIndexOf('{canNegotiate && (', i);
    expect(guard).toBeGreaterThan(-1);
    expect(i - guard).toBeLessThan(1200);
  });

  test('closing the room re-reads server state', () => {
    // A committed concession moves cash, reputation and the agent's escalation
    // stage. Trusting local state after a close would show stale numbers.
    const i = cockpit.indexOf('<NegotiationRoom');
    expect(cockpit.slice(i, i + 600)).toMatch(/fetchDashboard/);
  });

  test('it occupies the OverlayHost slot, not a permanent panel', () => {
    // CLAUDE.md V-D: new player UI takes exactly one slot, and an interrupt
    // like this one must be summoned rather than ambient.
    const i = cockpit.indexOf('<NegotiationRoom');
    expect(cockpit.slice(Math.max(0, i - 700), i)).toMatch(/createPortal/);
  });
});
