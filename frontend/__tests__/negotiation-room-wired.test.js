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
    expect(panel).toMatch(
      /onRequestMeeting && \['hostile', 'triggered'\]\.includes/
    );
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
