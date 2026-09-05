/**
 * Audit 2026-09-04 F-15 / WP-14 — the player-facing M_R surfaces (Mirror
 * Debrief, M_R Ladder, Rewind Ribbon, Regret Meter) read what the arbiter
 * awarded, not a client-side flag table.
 *
 * Production stores strategic flags inside `rN_flags` lists (top-level key
 * absent or null), and the finale writes its component breakdown to
 * flags.mr_breakdown. `!!flags[opp.flag]` saw none of the lists, so the
 * "biggest missed lever" was always Resilience +0.20 — told to a player
 * whose breakdown carried resilience_bonus 0.20.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { computeMrRegret, hasFlag, MR_OPPORTUNITIES } from '../app/utils/mrJourney';
import MirrorDebrief from '../app/components/MirrorDebrief';

const LIST_FLAGS = {
  r2_flags: ['materiality_aligned'],
  r6_flags: ['ethical_ai_overhaul'],
  r7_flags: ['synergy_unlock', 'waste_to_energy'],
  r9_flags: ['community_fund'],
  synergy_unlock: null,
  r5_flags: [],
};

describe('hasFlag reads flags the way the backend collects them', () => {
  test('list-held, string-valued and boolean flags', () => {
    expect(hasFlag(LIST_FLAGS, 'synergy_unlock')).toBe(true);
    expect(hasFlag(LIST_FLAGS, 'community_fund')).toBe(true);
    expect(hasFlag({ ending_pathway: 'hostile_takeover' }, 'hostile_takeover')).toBe(true);
    expect(hasFlag({ insurance_only: true }, 'insurance_only')).toBe(true);
    expect(hasFlag({ insurance_only: null }, 'insurance_only')).toBe(false);
    expect(hasFlag({ _private: ['synergy_unlock'] }, 'synergy_unlock')).toBe(false);
    expect(hasFlag(null, 'x')).toBe(false);
  });
});

describe('computeMrRegret', () => {
  test('before the finale, list-held flags count as captured', () => {
    const { captured, missed, source } = computeMrRegret(LIST_FLAGS);
    expect(source).toBe('flags');
    const names = captured.map((c) => c.flag);
    expect(names).toEqual(expect.arrayContaining(['materiality_aligned', 'ethical_ai_overhaul', 'synergy_unlock', 'community_fund', '__resilience__']));
    expect(missed).toHaveLength(0);
  });

  test('a listed insurance_only blocks resilience', () => {
    const { missed } = computeMrRegret({ r5_flags: ['insurance_only'] });
    expect(missed.map((m) => m.flag)).toContain('__resilience__');
  });

  test('after the finale, the arbiter breakdown decides and carries its values', () => {
    const flags = {
      ...LIST_FLAGS,
      mr_breakdown: { base: 1.0, materiality_governance: 0.10, resilience_bonus: 0.20, truth_premium: 0.15, community_champion_bonus: 0.27, instability_discount: -0.1 },
    };
    const { captured, missed, source, mrCaptured } = computeMrRegret(flags);
    expect(source).toBe('mr_breakdown');
    expect(missed.map((m) => m.flag)).toEqual(['synergy_unlock']); // gated by the synergy threshold — the arbiter withheld it
    const community = captured.find((c) => c.flag === 'community_fund');
    expect(community.mr).toBe(0.27);          // the JT-scaled value the finale awarded
    expect(community.nominalMr).toBe(0.18);
    expect(mrCaptured).toBeCloseTo(0.10 + 0.20 + 0.15 + 0.27, 2);
  });

  test('every opportunity names an arbiter component (no fictional levers)', () => {
    const arbiterKeys = ['materiality_governance', 'synergy_bonus', 'resilience_bonus', 'truth_premium', 'community_champion_bonus'];
    for (const op of MR_OPPORTUNITIES) expect(arbiterKeys).toContain(op.breakdownKey);
  });
});

describe('MirrorDebrief', () => {
  test('does not name Resilience as missed when the finale awarded resilience_bonus', () => {
    const flags = { ...LIST_FLAGS, mr_breakdown: { base: 1.0, resilience_bonus: 0.2, truth_premium: 0.15, community_champion_bonus: 0.18 } };
    render(<MirrorDebrief mr={1.53} flags={flags} terminalValue={300_000_000} />);
    // missed: materiality (0.10) and synergy (0.15) → biggest is synergy, R7 option C
    expect(screen.getAllByText(/Round 7/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Waste-to-Energy Partnership/)).toBeInTheDocument();
    expect(screen.queryByText(/Climate Resilience Investment/)).toBeNull();
  });

  test('renders nothing when the arbiter awarded every component', () => {
    const flags = { mr_breakdown: { base: 1.0, materiality_governance: 0.1, synergy_bonus: 0.15, resilience_bonus: 0.2, truth_premium: 0.15, community_champion_bonus: 0.18 } };
    const { container } = render(<MirrorDebrief mr={1.78} flags={flags} terminalValue={500_000_000} />);
    expect(container.firstChild).toBeNull();
  });
});
