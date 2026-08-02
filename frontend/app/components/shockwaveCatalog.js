/**
 * G-3 (v3): the SINGLE frontend copy of the Shockwave crisis catalog.
 *
 * ⚠ These numbers MUST mirror backend/admin_router.py::_SHOCKWAVE_EVENTS.
 * The engine detonates with the BACKEND values regardless of what this file
 * claims — a mismatch means the console lies about impact on a destructive
 * control. The drift-tripwire test (frontend/__tests__/shockwave-catalog.test.js)
 * parses the backend source and fails when the two diverge: update BOTH files
 * in the same commit. (Proper fix — a catalog GET endpoint — is Phase S5.)
 */
export const SHOCKWAVE_EVENTS = [
  { id: 'pandemic',        label: '🦠 Global Pandemic',          financial_impact: -6000000, reputation_impact: -6 },
  { id: 'carbon_tax',      label: '🏭 Emergency Carbon Tax',     financial_impact: -5000000, reputation_impact: -3 },
  { id: 'supply_collapse', label: '🚢 Supply-Chain Collapse',    financial_impact: -4500000, reputation_impact: -4 },
  { id: 'cyber_attack',    label: '💻 Coordinated Cyber Attack', financial_impact: -4000000, reputation_impact: -7 },
];

/** Display string derived from the numbers — never hand-write impact copy. */
export const fmtHit = (ev) =>
  `-$${Math.abs(ev.financial_impact / 1_000_000).toFixed(1)}M · ${ev.reputation_impact} rep`;
