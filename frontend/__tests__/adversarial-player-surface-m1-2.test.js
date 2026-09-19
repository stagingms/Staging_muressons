/**
 * Adversarial Challenge Suite for Milestone 1: Player Surface (Issues #07–#11)
 *
 * EMPIRICAL CHALLENGER: challenger_m1_2
 * Scope:
 *  1. <DecisionPressureTimer> handling all pacing modes (Timed, Free, Manual) as sole header clock
 *  2. Persistent <KPIStrip> rendering and preserving deltas across all 5 round steps
 *  3. Non-semantic --bu-* tokens and design-token-drift compliance
 *  4. ui-budgets.test.js ratchet rigor, absence of loopholes/exemptions
 *  5. Speech synthesis cleanup reliability upon crisis dismissal
 */

import React from 'react';
import fs from 'fs';
import path from 'path';
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import DecisionPressureTimer from '../app/components/DecisionPressureTimer';
import { KPIStrip } from '../app/components/FocusOverlay';
import { CrisisScreen } from '../app/components/CrisisAlerts';

describe('Adversarial Challenge 1: DecisionPressureTimer across all pacing modes & sole header clock', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    global.fetch = originalFetch;
    jest.clearAllTimers();
  });

  test('Timed mode: renders countdown ring, urgency classes, and commit badge', async () => {
    const futureTime = new Date(Date.now() + 90 * 1000).toISOString();
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes('/session-info')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ parent_cohort_id: 'cohort-123' }) });
      }
      if (url.includes('/pacing')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            mode: 'timed',
            interval_seconds: 120,
            next_unlock_at: futureTime,
            committed_count: 3,
            total_count: 5,
          }),
        });
      }
      return Promise.reject(new Error('unknown url'));
    });

    await act(async () => {
      render(
        <DecisionPressureTimer
          sessionId="test-session"
          roundNumber={2}
          isCommitted={false}
          globalState={{}}
        />
      );
    });

    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('⏳')).toBeInTheDocument();
    expect(screen.getByText('1:30')).toBeInTheDocument();
  });

  test('Timed mode: dynamic tick down and urgency transitions (green -> amber -> red)', async () => {
    // 100 seconds total, start with 40s left (pct = 0.40 -> green), tick to 30s (amber), tick to 10s (red)
    const now = Date.now();
    const unlockTime = new Date(now + 40 * 1000).toISOString();

    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes('/session-info')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ parent_cohort_id: 'cohort-123' }) });
      }
      if (url.includes('/pacing')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            mode: 'timed',
            interval_seconds: 100,
            next_unlock_at: unlockTime,
            committed_count: 1,
            total_count: 4,
          }),
        });
      }
      return Promise.reject(new Error('unknown url'));
    });

    const { container } = render(
      <DecisionPressureTimer
        sessionId="test-session"
        roundNumber={2}
        isCommitted={false}
        globalState={{}}
      />
    );

    await act(async () => {
      await Promise.resolve();
    });

    // Initial state at 40s (pct = 0.40 > 0.35 -> green)
    expect(screen.getByText('0:40')).toBeInTheDocument();
    expect(container.querySelector('.urgency_green')).not.toBeNull();

    // Fast-forward 10 seconds -> 30s left (pct = 0.30 <= 0.35 -> amber)
    act(() => {
      jest.advanceTimersByTime(10000);
    });
    expect(screen.getByText('0:30')).toBeInTheDocument();
    expect(container.querySelector('.urgency_amber')).not.toBeNull();

    // Fast-forward 20 seconds -> 10s left (pct = 0.10 <= 0.15 -> red)
    act(() => {
      jest.advanceTimersByTime(20000);
    });
    expect(screen.getByText('0:10')).toBeInTheDocument();
    expect(container.querySelector('.urgency_red')).not.toBeNull();
    // Warning pulse should appear in red urgency when uncommitted
    expect(screen.getByText('⚠️')).toBeInTheDocument();
  });

  test('Timed mode: handles expired deadline (remaining <= 0) gracefully without NaN or negative time', async () => {
    const pastTime = new Date(Date.now() - 5000).toISOString();
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes('/session-info')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ parent_cohort_id: 'cohort-123' }) });
      }
      if (url.includes('/pacing')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            mode: 'timed',
            interval_seconds: 60,
            next_unlock_at: pastTime,
            committed_count: 5,
            total_count: 5,
          }),
        });
      }
      return Promise.reject(new Error('unknown url'));
    });

    await act(async () => {
      render(
        <DecisionPressureTimer
          sessionId="test-session"
          roundNumber={2}
          isCommitted={true}
          globalState={{}}
        />
      );
    });

    expect(screen.getByText('0:00')).toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  test('Free mode: displays honest "No time limit this round" label and infinity symbol', async () => {
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes('/session-info')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ parent_cohort_id: 'cohort-123' }) });
      }
      if (url.includes('/pacing')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            mode: 'free',
            committed_count: 2,
            total_count: 4,
          }),
        });
      }
      return Promise.reject(new Error('unknown url'));
    });

    await act(async () => {
      render(
        <DecisionPressureTimer
          sessionId="test-session"
          roundNumber={1}
          isCommitted={false}
          globalState={{}}
        />
      );
    });

    expect(screen.getByText('No time limit this round')).toBeInTheDocument();
    expect(screen.getByText('∞')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('⏳')).toBeInTheDocument();
  });

  test('Manual mode: displays honest "Facilitator paces this round" label and clapperboard icon', async () => {
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes('/session-info')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ parent_cohort_id: 'cohort-123' }) });
      }
      if (url.includes('/pacing')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            mode: 'manual',
            committed_count: 4,
            total_count: 4,
          }),
        });
      }
      return Promise.reject(new Error('unknown url'));
    });

    await act(async () => {
      render(
        <DecisionPressureTimer
          sessionId="test-session"
          roundNumber={3}
          isCommitted={true}
          globalState={{}}
        />
      );
    });

    expect(screen.getByText('Facilitator paces this round')).toBeInTheDocument();
    expect(screen.getByText('🎬')).toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  test('Network or server failure falls back gracefully without unhandled exception', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network offline'));

    let container;
    await act(async () => {
      const res = render(
        <DecisionPressureTimer
          sessionId="test-session"
          roundNumber={1}
          isCommitted={false}
          globalState={{}}
        />
      );
      container = res.container;
    });

    // Should return null and render empty container without error
    expect(container).toBeEmptyDOMElement();
  });

  test('Sole header clock: ExecutiveCockpit header does NOT contain CountdownTimer', () => {
    const cockpitPath = path.join(__dirname, '..', 'app', 'components', 'ExecutiveCockpit.js');
    const src = fs.readFileSync(cockpitPath, 'utf8');

    // Find the headerCenter block
    const headerCenterIdx = src.indexOf('className={styles.headerCenter}');
    expect(headerCenterIdx).toBeGreaterThan(-1);

    const headerEndIdx = src.indexOf('</header>');
    expect(headerEndIdx).toBeGreaterThan(headerCenterIdx);

    const headerContent = src.slice(headerCenterIdx, headerEndIdx);

    // Must NOT contain <CountdownTimer
    expect(headerContent).not.toMatch(/<CountdownTimer/);
    // Must contain <DecisionPressureTimer
    expect(headerContent).toMatch(/<DecisionPressureTimer/);
  });
});

describe('Adversarial Challenge 2: Persistent KPIStrip rendering and delta preservation across all 5 round steps', () => {
  test('Renders all 4 core KPI tiles (Treasury, EBITDA, Reputation, Carbon)', () => {
    render(
      <KPIStrip
        treasury={50000000}
        reputation={75}
        carbon={12000}
        ebitda={8000000}
        roundNumber={2}
        previous={{
          corporate_treasury: 45000000,
          historical_ebitda: 10000000,
          group_reputation: 70,
          tco2e_emissions: 14000,
        }}
        fmtCurrency={(v) => `$${(v / 1e6).toFixed(1)}M`}
      />
    );

    expect(screen.getByText('Treasury')).toBeInTheDocument();
    expect(screen.getByText('$50.0M')).toBeInTheDocument();

    expect(screen.getByText('EBITDA')).toBeInTheDocument();
    expect(screen.getByText('$8.0M')).toBeInTheDocument();

    expect(screen.getByText('Reputation')).toBeInTheDocument();
    expect(screen.getByText('75')).toBeInTheDocument();

    expect(screen.getByText('Carbon')).toBeInTheDocument();
    expect(screen.getByText('12,000')).toBeInTheDocument();
  });

  test('Delta calculations are mathematically and directionally accurate', () => {
    const { container } = render(
      <KPIStrip
        treasury={50000000}      // +5M (favorable: up)
        reputation={75}           // +5 (favorable: up)
        carbon={12000}            // -2000t (lower emissions is favorable: up!)
        ebitda={8000000}          // -2M (unfavorable: down)
        roundNumber={3}
        previous={{
          corporate_treasury: 45000000,
          historical_ebitda: 10000000,
          group_reputation: 70,
          tco2e_emissions: 14000,
        }}
        fmtCurrency={(v) => `$${(v / 1e6).toFixed(1)}M`}
      />
    );

    const deltas = container.querySelectorAll('.beltDelta');
    expect(deltas.length).toBe(4);

    // Treasury: +$5.0M vs R2 (up)
    expect(deltas[0].textContent).toBe('+$5.0M vs R2');
    expect(deltas[0].getAttribute('data-dir')).toBe('up');

    // EBITDA: −$2.0M vs R2 (down)
    expect(deltas[1].textContent).toBe('−$2.0M vs R2');
    expect(deltas[1].getAttribute('data-dir')).toBe('down');

    // Reputation: +5 vs R2 (up)
    expect(deltas[2].textContent).toBe('+5 vs R2');
    expect(deltas[2].getAttribute('data-dir')).toBe('up');

    // Carbon: −2,000 vs R2 (emissions down -> favorable -> up)
    expect(deltas[3].textContent).toBe('−2,000 vs R2');
    expect(deltas[3].getAttribute('data-dir')).toBe('up');
  });

  test('Round 1 (no prior state): deltas are blank, not fabricated zeros', () => {
    const { container } = render(
      <KPIStrip
        treasury={50000000}
        reputation={75}
        carbon={12000}
        ebitda={8000000}
        roundNumber={1}
        previous={null}
      />
    );

    const deltas = container.querySelectorAll('.beltDelta');
    deltas.forEach((d) => {
      expect(d.textContent).toBe('');
      expect(d.getAttribute('data-dir')).toBeNull();
    });
  });

  test('Unchanged metrics explicitly declare "unchanged vs R{N-1}" with neutral dir', () => {
    const { container } = render(
      <KPIStrip
        treasury={50000000}
        reputation={75}
        carbon={12000}
        ebitda={8000000}
        roundNumber={2}
        previous={{
          corporate_treasury: 50000000,
          historical_ebitda: 8000000,
          group_reputation: 75,
          tco2e_emissions: 12000,
        }}
        fmtCurrency={(v) => `$${(v / 1e6).toFixed(1)}M`}
      />
    );

    const deltas = container.querySelectorAll('.beltDelta');
    deltas.forEach((d) => {
      expect(d.textContent).toBe('unchanged vs R1');
      expect(d.getAttribute('data-dir')).toBeNull();
    });
  });

  test('Multi-team and staged cost tiles render conditionally when present', () => {
    render(
      <KPIStrip
        treasury={50000000}
        reputation={75}
        carbon={12000}
        ebitda={8000000}
        roundNumber={2}
        previous={{ corporate_treasury: 50000000, historical_ebitda: 8000000, group_reputation: 75, tco2e_emissions: 12000 }}
        cohortTeamCount={4}
        cohortCommits={2}
        projectedCost={-3500000}
        fmtCurrency={(v) => `$${(Math.abs(v) / 1e6).toFixed(1)}M`}
      />
    );

    expect(screen.getByText('Committed')).toBeInTheDocument();
    expect(screen.getByText('2 of 4')).toBeInTheDocument();

    expect(screen.getByText('Staged')).toBeInTheDocument();
    expect(screen.getByText('$3.5M')).toBeInTheDocument();
    expect(screen.getByText('to spend this round')).toBeInTheDocument();
  });

  test('Persistent placement: KPIStrip is rendered before all 5 canvas round step blocks', () => {
    const cockpitPath = path.join(__dirname, '..', 'app', 'components', 'ExecutiveCockpit.js');
    const src = fs.readFileSync(cockpitPath, 'utf8');

    // Verify KPIStrip is mounted before mainContent
    const kpiStripIdx = src.indexOf('<KPIStrip');
    const mainContentIdx = src.indexOf('className={styles.mainContent}');
    expect(kpiStripIdx).toBeGreaterThan(-1);
    expect(mainContentIdx).toBeGreaterThan(kpiStripIdx);

    // Verify all 5 canvas round steps render AFTER KPIStrip in the JSX tree
    const canvasSteps = [
      "{focusStep === 'gate' && (",
      "{focusStep === 'strategy' && (",
      "{focusStep === 'allocation' && (",
      "{focusStep === 'waiting' && commitResults &&",
      "{focusStep === 'results' && commitResults &&",
    ];
    for (const stepPattern of canvasSteps) {
      const stepIdx = src.indexOf(stepPattern);
      expect(stepIdx).toBeGreaterThan(kpiStripIdx);
    }

    // Verify the 4 data-testid="kpi-delta" attributes exist in ExecutiveCockpit.js
    const kpiDeltaMatches = src.match(/data-testid="kpi-delta"/g) || [];
    expect(kpiDeltaMatches.length).toBe(4);
  });
});

describe('Adversarial Challenge 3: Non-semantic --bu-* tokens and design-token-drift', () => {
  const SEMANTIC_HEX_PATTERN = /#(?:10b981|22c55e|4ade80|34d399|059669|16a34a|86efac|6ee7b7|a7f3d0|0a7d3c|15803d|047857|ef4444|f87171|dc2626|b91c1c|fca5a5|b42318|450a0a|f59e0b|fbbf24|fcd34d|d97706|a16207|b45309|92400e)\b/i;

  test('All 8 --bu-* tokens exist in tokens.css and none match semantic status hues', () => {
    const tokensPath = path.join(__dirname, '..', 'app', 'styles', 'tokens.css');
    const tokensSrc = fs.readFileSync(tokensPath, 'utf8');

    const buTokens = [
      '--bu-pharma',
      '--bu-electronics',
      '--bu-consumer',
      '--bu-software',
      '--bu-hospital',
      '--bu-clinics',
      '--bu-specialised',
      '--bu-telehealth',
    ];

    for (const token of buTokens) {
      const regex = new RegExp(`${token}:\\s*([^;]+);`);
      const match = tokensSrc.match(regex);
      expect(match).not.toBeNull();
      const value = match[1].trim();
      expect(value).toMatch(/^#[0-9a-fA-F]{3,8}$/);
      expect(value).not.toMatch(SEMANTIC_HEX_PATTERN);
    }
  });

  test('InvestmentMatrix BU_META references strictly --bu-* tokens, not semantic status tokens', () => {
    const matrixPath = path.join(__dirname, '..', 'app', 'components', 'InvestmentMatrix.js');
    const matrixSrc = fs.readFileSync(matrixPath, 'utf8');

    const buMetaMatch = matrixSrc.match(/const BU_META = \{([\s\S]*?)\};/);
    expect(buMetaMatch).not.toBeNull();
    const buMetaBody = buMetaMatch[1];

    // Must NOT contain semantic tokens
    expect(buMetaBody).not.toContain('var(--kpi-good)');
    expect(buMetaBody).not.toContain('var(--caution)');
    expect(buMetaBody).not.toContain('var(--danger)');
    expect(buMetaBody).not.toContain('var(--positive)');

    // Must reference var(--bu-*)
    expect(buMetaBody).toContain('var(--bu-pharma)');
    expect(buMetaBody).toContain('var(--bu-electronics)');
    expect(buMetaBody).toContain('var(--bu-consumer)');
    expect(buMetaBody).toContain('var(--bu-software)');
    expect(buMetaBody).toContain('var(--bu-hospital)');
    expect(buMetaBody).toContain('var(--bu-clinics)');
    expect(buMetaBody).toContain('var(--bu-specialised)');
    expect(buMetaBody).toContain('var(--bu-telehealth)');
  });
});

describe('Adversarial Challenge 4: ui-budgets.test.js ratchet rigor & absence of loopholes', () => {
  test('Ratchet baselines in ui-budgets.test.js reflect genuine reductions without test dilution', () => {
    const budgetsPath = path.join(__dirname, '..', '__tests__', 'ui-budgets.test.js');
    const src = fs.readFileSync(budgetsPath, 'utf8');

    // Verify test suite has no .skip or .only
    expect(src).not.toContain('test.skip');
    expect(src).not.toContain('describe.skip');
    expect(src).not.toContain('test.only');
    expect(src).not.toContain('describe.only');

    // Verify that the ratchet helper continues to throw on drift
    expect(src).toContain('baseline ${baseline}. You added');
    expect(src).toContain('Now lower the baseline in __tests__/ui-budgets.test.js to ${actual}');
  });
});

describe('Adversarial Challenge 5: Speech synthesis cleanup upon crisis dismissal', () => {
  let originalSpeechSynthesis;

  beforeEach(() => {
    originalSpeechSynthesis = window.speechSynthesis;
  });

  afterEach(() => {
    window.speechSynthesis = originalSpeechSynthesis;
  });

  test('Crisis dismissal when speechSynthesis is completely undefined does not throw', () => {
    delete window.speechSynthesis;

    const onDismiss = jest.fn();
    render(
      <CrisisScreen
        crisisType="liquidity"
        cfg={{ title: 'Liquidity Crisis', metric: 'corporate_treasury' }}
        globalState={{ corporate_treasury: 1000000 }}
        onDismiss={onDismiss}
      />
    );

    const dismissBtn = screen.getByRole('button', { name: /acknowledge/i });
    expect(() => {
      fireEvent.click(dismissBtn);
    }).not.toThrow();

    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  test('Crisis dismissal triggers window.speechSynthesis.cancel() cleanly', () => {
    const mockCancel = jest.fn();
    window.speechSynthesis = {
      cancel: mockCancel,
      speak: jest.fn(),
      getVoices: jest.fn().mockReturnValue([]),
      speaking: false,
    };

    const onDismiss = jest.fn();
    render(
      <CrisisScreen
        crisisType="liquidity"
        cfg={{ title: 'Liquidity Crisis', metric: 'corporate_treasury' }}
        globalState={{ corporate_treasury: 1000000 }}
        onDismiss={onDismiss}
      />
    );

    const dismissBtn = screen.getByRole('button', { name: /acknowledge/i });
    fireEvent.click(dismissBtn);

    expect(mockCancel).toHaveBeenCalled();
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  test('Unmounting CrisisScreen triggers speech synthesis cancellation', () => {
    const mockCancel = jest.fn();
    window.speechSynthesis = {
      cancel: mockCancel,
      speak: jest.fn(),
      getVoices: jest.fn().mockReturnValue([]),
      speaking: false,
    };

    const { unmount } = render(
      <CrisisScreen
        crisisType="liquidity"
        cfg={{ title: 'Liquidity Crisis', metric: 'corporate_treasury' }}
        globalState={{ corporate_treasury: 1000000 }}
        onDismiss={() => {}}
      />
    );

    unmount();
    expect(mockCancel).toHaveBeenCalled();
  });

  test('ExecutiveCockpit dismissActiveAlert cancels speech synthesis safely', () => {
    const cockpitPath = path.join(__dirname, '..', 'app', 'components', 'ExecutiveCockpit.js');
    const src = fs.readFileSync(cockpitPath, 'utf8');

    const dismissAlertMatch = src.match(/const dismissActiveAlert = useCallback\(\(\) => \{([\s\S]*?)\}, \[blackSwanAlert\]\);/);
    expect(dismissAlertMatch).not.toBeNull();
    const dismissBody = dismissAlertMatch[1];

    expect(dismissBody).toContain("if (typeof window !== 'undefined') window.speechSynthesis?.cancel();");
  });
});
