/**
 * UX audit #21 — "Complete the consequence chain".
 *
 * ConsequenceReplay used to explain a round from a hardcoded list of three or
 * four event keys and then fall back to "the first 3 truthy flags". Anything
 * else the engine produced disappeared from the player's explanation, and the
 * gap was invisible — a dropped node looks exactly like an effect that never
 * fired.
 *
 * These tests pin the two properties that fix is made of:
 *   1. every catalog entry is complete enough to actually teach something, and
 *   2. NOTHING is silently dropped — an unrecognised flag key still renders.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import ConsequenceReplay, { buildChain } from '../app/components/ConsequenceReplay';
import {
  CONSEQUENCE_CATALOG,
  IGNORED_KEYS,
  isIgnoredKey,
  humaniseKey,
  lookupConsequence,
} from '../app/components/consequenceCatalog';

const CATALOG_KEYS = Object.keys(CONSEQUENCE_CATALOG);
const SEVERITIES = ['good', 'bad', 'neutral'];

// The facilitator toggle fetch must never decide the outcome of a unit test.
beforeEach(() => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: false, json: () => Promise.resolve({}) }));
});
afterEach(() => {
  jest.restoreAllMocks();
});

describe('(a) every catalog entry is complete', () => {
  test('the catalog is substantial (sanity)', () => {
    expect(CATALOG_KEYS.length).toBeGreaterThanOrEqual(40);
  });

  test.each(CATALOG_KEYS)('%s has label / mechanism / severity / explain', (key) => {
    const entry = CONSEQUENCE_CATALOG[key];

    expect(typeof entry.label).toBe('string');
    expect(entry.label.trim().length).toBeGreaterThan(0);

    expect(typeof entry.mechanism).toBe('string');
    expect(entry.mechanism.trim().length).toBeGreaterThan(0);

    expect(SEVERITIES).toContain(entry.severity);

    expect(typeof entry.explain).toBe('function');
  });

  test.each(CATALOG_KEYS)('%s explain() returns a sentence for any payload shape', (key) => {
    const entry = CONSEQUENCE_CATALOG[key];
    // The engine writes booleans, numbers, strings, arrays and dicts into
    // active_event_flags. explain() must survive all of them.
    const payloads = [true, 1, 0.42, 2_500_000, 'stabilise', ['hospitals'], {}, undefined];
    for (const payload of payloads) {
      const sentence = entry.explain(payload, {});
      expect(typeof sentence).toBe('string');
      expect(sentence.trim().length).toBeGreaterThan(0);
      expect(sentence).not.toMatch(/undefined|NaN|\[object Object\]/);
    }
  });
});

describe('(b) no flag is silently dropped', () => {
  const commitFor = (flags) => ({
    choiceLabel: 'Option B — Retrofit the plant',
    events: {},
    globalState: { active_event_flags: flags },
  });

  test('an UNKNOWN flag key still produces a rendered step', () => {
    const unknownKey = 'totally_invented_engine_effect_active';
    expect(lookupConsequence(unknownKey)).toBeNull();

    const chain = buildChain(commitFor({ [unknownKey]: true }), 4);
    const node = chain.find((n) => n.key === unknownKey);

    expect(node).toBeDefined();
    expect(node.label).toBe('Totally Invented Engine Effect Active');
    expect(node.uncatalogued).toBe(true);
  });

  test('the unknown key reaches the DOM, not just the chain array', () => {
    render(
      <ConsequenceReplay
        commitResults={commitFor({ cfo_austerity_active: true, some_brand_new_flag: true })}
        roundNumber={4}
      />
    );
    // Humanised, not dropped, and not raw snake_case.
    expect(screen.getByText('Some Brand New Flag')).toBeInTheDocument();
    expect(screen.queryByText('some_brand_new_flag')).not.toBeInTheDocument();
    // The known key renders from its catalog entry alongside it.
    expect(screen.getByText(CONSEQUENCE_CATALOG.cfo_austerity_active.label)).toBeInTheDocument();
  });

  test('every truthy non-ignored flag becomes exactly one node — no slicing', () => {
    const flags = {
      talent_penalty_applied: 1.18,      // catalogued
      loan_interest_payment: 2_400_000,  // catalogued
      tipping_point_reached: true,       // catalogued
      greenwashing_scandal: true,        // catalogued
      supplier_defection: { active: true },
      brand_new_effect_one: true,        // uncatalogued
      brand_new_effect_two: 7,           // uncatalogued
      quiet_failure_mode: 'it happened quietly',
      greenwashing_checked: false,       // falsy → did not fire
      stochastic_seed: 'cohort-a-42',    // documented exclusion
      ending_pathway: 'hostile_takeover',// documented exclusion
      _base_treasury_internal: 5,        // engine-internal prefix
    };

    const chain = buildChain(commitFor(flags), 6);
    const rendered = new Set(chain.map((n) => n.key));

    const expected = Object.entries(flags)
      .filter(([k, v]) => v && !isIgnoredKey(k))
      .map(([k]) => k);

    for (const key of expected) {
      expect(rendered.has(key)).toBe(true);
    }
    // Falsy and deliberately-ignored keys stay out.
    expect(rendered.has('greenwashing_checked')).toBe(false);
    expect(rendered.has('stochastic_seed')).toBe(false);
    expect(rendered.has('ending_pathway')).toBe(false);
    expect(rendered.has('_base_treasury_internal')).toBe(false);
  });

  test('round-suffixed families resolve to their base catalog entry', () => {
    // engine.py stamps the round onto some keys (reputation_applied_r4, …).
    const chain = buildChain(commitFor({ midgame_carbon_cost_r7: 1_800_000 }), 7);
    const node = chain.find((n) => n.key === 'midgame_carbon_cost_r7');
    expect(node).toBeDefined();
    expect(node.uncatalogued).toBeUndefined();
    expect(node.label).toBe(CONSEQUENCE_CATALOG.midgame_carbon_cost.label);
  });

  test('an uncatalogued key borrows the engine\'s own message string', () => {
    const chain = buildChain(
      commitFor({
        weird_new_levy_applied: 900_000,
        weird_new_levy_applied_message: 'The regulator invented a new levy and charged you for it.',
      }),
      8
    );
    const node = chain.find((n) => n.key === 'weird_new_levy_applied');
    expect(node.explain).toBe('The regulator invented a new levy and charged you for it.');
  });

  test('humaniseKey never returns raw snake_case', () => {
    expect(humaniseKey('cfo_austerity_active')).toBe('CFO Austerity Active');
    expect(humaniseKey('esg_adjusted_wacc')).toBe('ESG Adjusted WACC');
    expect(humaniseKey('_loan_principal_internal')).toBe('Loan Principal Internal');
    expect(humaniseKey('anything_at_all')).not.toContain('_');
  });
});

describe('(c) exclusion is documented, not accidental', () => {
  test('IGNORED_KEYS and CONSEQUENCE_CATALOG do not overlap', () => {
    const overlap = CATALOG_KEYS.filter((k) => IGNORED_KEYS.has(k));
    expect(overlap).toEqual([]);
  });

  test('no catalog entry is unreachable via the ignore rules (prefix/pattern too)', () => {
    const unreachable = CATALOG_KEYS.filter((k) => isIgnoredKey(k));
    expect(unreachable).toEqual([]);
  });

  test('IGNORED_KEYS is a real, non-trivial set', () => {
    expect(IGNORED_KEYS.size).toBeGreaterThanOrEqual(20);
    for (const key of IGNORED_KEYS) {
      expect(typeof key).toBe('string');
      expect(key.trim().length).toBeGreaterThan(0);
    }
  });
});

describe('the existing component contract still holds', () => {
  test('renders nothing without commit results', () => {
    const { container } = render(<ConsequenceReplay commitResults={null} roundNumber={3} />);
    expect(container).toBeEmptyDOMElement();
  });

  test('the decision is still the first node, ahead of any consequence', () => {
    const chain = buildChain(
      {
        choiceLabel: 'Option A — Close the plant',
        events: { treasury_delta: -3_000_000, reputation_delta: -4.2 },
        globalState: { active_event_flags: { insolvency_active: true } },
      },
      5
    );
    expect(chain[0].type).toBe('decision');
    expect(chain[0].label).toBe('Option A — Close the plant');
    expect(chain.map((n) => n.key)).toContain('__treasury__');
    expect(chain.map((n) => n.key)).toContain('__reputation__');
  });

  test('skip button is present and reveals the whole chain', () => {
    render(
      <ConsequenceReplay
        commitResults={{
          choiceLabel: 'Option C',
          events: {},
          globalState: { active_event_flags: { fog_of_war_active: true } },
        }}
        roundNumber={2}
      />
    );
    expect(screen.getByRole('button', { name: /Skip/ })).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  PER-ENTITY FAMILIES (UX audit #21 follow-through)
//  Engines stamp the BU/NPC onto the KEY (`talent_penalty_applied_pharma`),
//  and the set is unbounded because verticals and NPC ids are configurable.
//  These used to fall through to the generic humaniser and read like variable
//  names. Pin the matcher so the copy survives refactors.
// ═══════════════════════════════════════════════════════════════════════════
describe('per-entity flag families', () => {
    const { PER_ENTITY_FAMILIES, matchPerEntity, lookupConsequence } = require('../app/components/consequenceCatalog');

    test('every family entry is complete', () => {
        for (const [prefix, fam] of Object.entries(PER_ENTITY_FAMILIES)) {
            expect(typeof fam.label).toBe('string');
            expect(fam.label.length).toBeGreaterThan(0);
            expect(typeof fam.mechanism).toBe('string');
            expect(['good', 'bad', 'neutral']).toContain(fam.severity);
            expect(typeof fam.explain).toBe('function');
            // explain() must survive any payload shape the engine might write.
            for (const v of [true, 1.25, 0, 'x', [], {}, { opex_delta: 1e6 }, undefined, null]) {
                expect(typeof fam.explain('Pharma', v)).toBe('string');
            }
            expect(prefix).toMatch(/^[a-z0-9_]+$/);
        }
    });

    test('resolves a per-BU key to family copy naming the business unit', () => {
        const hit = matchPerEntity('talent_penalty_applied_consumer_goods');
        expect(hit).not.toBeNull();
        expect(hit.subject).toBe('Consumer Goods');
        expect(hit.entry.label).toContain('Consumer Goods');
        expect(hit.entry.explain(1.4)).toContain('Consumer Goods');
        // and it is NOT the raw humanised key
        expect(hit.entry.label).not.toBe('Talent Penalty Applied Consumer Goods');
    });

    test('longest prefix wins — streak never resolves against penalty', () => {
        expect(matchPerEntity('technical_debt_streak_pharma').family).toBe('technical_debt_streak');
        expect(matchPerEntity('technical_debt_penalty_pharma').family).toBe('technical_debt_penalty');
    });

    test('a bare family prefix with no entity does not match', () => {
        expect(matchPerEntity('talent_penalty_applied')).toBeNull();
        expect(matchPerEntity('talent_penalty_applied_')).toBeNull();
    });

    test('lookupConsequence routes per-entity keys through the family', () => {
        const entry = lookupConsequence('npc_cascade_treasury_activist_fund');
        expect(entry).not.toBeNull();
        expect(entry.explain(2_500_000)).toContain('Activist Fund');
    });

    test('unknown keys still return null so the humanised fallback runs', () => {
        expect(lookupConsequence('totally_made_up_flag_xyz')).toBeNull();
    });
});
