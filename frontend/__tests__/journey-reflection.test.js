/**
 * IMP-04 (audit 2026-09-04, WP-22): the R6/R7/R8 journey panels promised
 * effects no engine applied ("impacts will apply at round resolution",
 * "consequences will unfold"). They are reflection exercises: every panel
 * says so, and the confirmation badge no longer promises an engine effect.
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { R6RevelationPanel, BudgetAllocationPanel } from '../app/components/PedagogicalScaffolding';

const NOTE = "Reflection exercise — your answer is recorded for the facilitator's debrief. It does not change the simulation's numbers.";

function mockFetch(routes) {
  global.fetch = jest.fn((url) => {
    for (const [frag, body] of routes) {
      if (String(url).includes(frag)) return Promise.resolve({ ok: true, status: 200, json: async () => body });
    }
    return Promise.resolve({ ok: false, status: 404, json: async () => ({}) });
  });
}
afterEach(() => jest.resetAllMocks());

test('the R7 budget panel is labelled a reflection exercise and the lock badge promises no engine effect', async () => {
  mockFetch([['/journey/mechanic-variant/7', { round: 7, variant: {
    enabled: true, engine_impact: false, note: NOTE, title: 'Circular Economy Budget Allocation',
    instruction: 'Distribute the budget.', total_budget: 15_000_000,
    initiatives: {
      product_redesign: { label: 'Product Redesign', icon: '🔄', description: 'x', synergy_threshold: 8_000_000 },
      take_back_program: { label: 'Take-Back Program', icon: '📦', description: 'y', synergy_threshold: 5_000_000 },
    },
  } }]]);
  const onAllocate = jest.fn();
  render(<BudgetAllocationPanel onAllocate={onAllocate} />);
  await waitFor(() => expect(screen.getByTestId('journey-reflection-note')).toHaveTextContent(NOTE));
  fireEvent.click(screen.getByText(/Lock Allocation/));
  expect(onAllocate).toHaveBeenCalledTimes(1);
  expect(screen.getByText(/recorded for the debrief/)).toBeInTheDocument();
  expect(screen.queryByText(/impacts will apply/)).toBeNull();
});

test('the R6 revelation panel carries the note and its confirmation promises no consequences', async () => {
  mockFetch([['/journey/r6-revelation', { revelation: {
    enabled: true, engine_impact: false, note: NOTE, title: 'Breaking', narrative: 'A leak.',
    pedagogical_purpose: 'Reflective observation.',
    micro_decisions: { accept: { label: 'Accept Full Accountability', icon: '🙋', description: 'd' } },
  } }]]);
  const onMicroDecision = jest.fn();
  render(<R6RevelationPanel onMicroDecision={onMicroDecision} />);
  await waitFor(() => expect(screen.getByTestId('journey-reflection-note')).toHaveTextContent(NOTE));
  fireEvent.click(screen.getByText(/Accept Full Accountability/));
  fireEvent.click(screen.getByText(/Confirm Response/));
  expect(onMicroDecision).toHaveBeenCalledTimes(1);
  expect(screen.getByText(/no engine impact/)).toBeInTheDocument();
  expect(screen.queryByText(/consequences will unfold/)).toBeNull();
});
