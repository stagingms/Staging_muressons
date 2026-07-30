/**
 * Bulk Add Players has TWO variants, and the modal must render the cohort's,
 * not a generic average of both.
 *
 *   4-BU conglomerate → every player runs all four business units, so there is
 *                       no per-player company: identity columns only.
 *   Single business    → each player runs their own company, so industry and
 *                       region are per-row dropdowns from the cohort's own
 *                       formation vocabulary.
 *
 * Why this is worth a test rather than eyeballing: the two variants differ in
 * what a column MEANS, not just in whether it is displayed. A conglomerate
 * roster that carried a business unit used to be accepted, and join_session then
 * scoped each of those players to a single BU — no error, no warning, and a
 * cohort that silently was not the cohort the facilitator formed. The modal
 * promising a column the template does not ship is how an operator gets talked
 * into recreating that state by hand.
 *
 * The shape is FETCHED, so these tests assert the modal obeys the server rather
 * than re-deriving the mode locally. A local derivation is a second source of
 * truth and would drift from backend/roster_shape.py.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import BulkPlayerUpload from '../app/components/BulkPlayerUpload';

const CONGLOMERATE_SHAPE = {
  mode: 'conglomerate',
  mode_label: '4-BU Conglomerate (every player runs all four)',
  per_player_scope: false,
  columns: ['name', 'email', 'programme'],
  required: ['name'],
  choices: {},
  cohort: { cohort_name: 'MBA 2026 — Section A', industry_vertical: '', region_id: 'europe' },
  refused_columns: { assigned_bu: 'not a column on a 4-BU conglomerate roster' },
};

const SINGLE_BU_SHAPE = {
  mode: 'single_bu',
  mode_label: 'Single Business (one company per player)',
  per_player_scope: true,
  columns: ['name', 'email', 'programme', 'industry_vertical', 'region_id'],
  required: ['name'],
  choices: {
    industry_vertical: ['pharma', 'oil_gas', 'electronics', 'semiconductor'],
    region_id: ['south_asia', 'china', 'europe'],
  },
  cohort: { cohort_name: 'EMBA Energy', industry_vertical: 'oil_gas', region_id: 'south_asia' },
  refused_columns: { assigned_bu: 'never authored — derived from industry_vertical' },
};

/** Mock only the roster-shape GET; anything else 404s so a stray call is loud. */
function mockShape(shape) {
  global.fetch = jest.fn((url) => {
    if (String(url).includes('/players/roster-shape')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ ok: true, shape, max_players: 20, used: 0, remaining: 20 }),
      });
    }
    return Promise.resolve({ ok: false, status: 404, json: async () => ({}) });
  });
}

function renderModal(props = {}) {
  return render(
    <BulkPlayerUpload mode="cohort" sessionId="sid-1" cohortName="Test Cohort" {...props} />,
  );
}

afterEach(() => { jest.restoreAllMocks(); delete global.fetch; });

describe('4-BU conglomerate roster', () => {
  it('offers no per-player company column at all', async () => {
    mockShape(CONGLOMERATE_SHAPE);
    renderModal();
    await screen.findByText(/4-BU Conglomerate/i);

    // The strongest form of the fix: the column is absent, so it cannot be
    // filled in wrongly.
    expect(screen.queryByText('industry_vertical')).not.toBeInTheDocument();
    expect(screen.queryByText('region_id')).not.toBeInTheDocument();
    expect(screen.queryByText('assigned_bu')).not.toBeInTheDocument();
    for (const col of CONGLOMERATE_SHAPE.columns) {
      expect(screen.getByText(new RegExp(`^${col}`))).toBeInTheDocument();
    }
  });

  it('says WHY there is no business-unit column, not merely that there is none', async () => {
    mockShape(CONGLOMERATE_SHAPE);
    renderModal();
    // An operator who wanted per-player BUs needs to know the cohort's mode is
    // the reason, or they will go looking for a bug.
    await waitFor(() => {
      expect(screen.getByText(/all four business units/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/scope that player down to a single business/i)).toBeInTheDocument();
  });
});

describe('single-business roster', () => {
  it('offers industry and region per player, and names the inherited defaults', async () => {
    mockShape(SINGLE_BU_SHAPE);
    renderModal();
    await screen.findByText(/Single Business/i);

    expect(screen.getByText(/^industry_vertical/)).toBeInTheDocument();
    expect(screen.getByText(/^region_id/)).toBeInTheDocument();
    // Blank-inherits is the one rule an author cannot guess from the sheet.
    expect(screen.getByText(/Blank inherits/i)).toBeInTheDocument();
    expect(screen.getByText(/Oil Gas/)).toBeInTheDocument();
    expect(screen.getByText(/South Asia/)).toBeInTheDocument();
  });

  it('states that players may differ, and that the BU slot is derived', async () => {
    mockShape(SINGLE_BU_SHAPE);
    renderModal();
    await waitFor(() => {
      expect(
        screen.getByText(/different industries in different regions/i),
      ).toBeInTheDocument();
    });
    expect(screen.getByText(/derived from the industry/i)).toBeInTheDocument();
  });

  it('never invites the author to write a BU slot', async () => {
    mockShape(SINGLE_BU_SHAPE);
    renderModal();
    await screen.findByText(/Single Business/i);
    expect(screen.queryByText('assigned_bu')).not.toBeInTheDocument();
  });
});

describe('where the shape comes from', () => {
  it('is fetched from the cohort, not inferred locally', async () => {
    mockShape(SINGLE_BU_SHAPE);
    renderModal({ sessionId: 'sid-42' });
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    expect(global.fetch.mock.calls.some(
      ([url]) => String(url).includes('/api/admin/sid-42/players/roster-shape'),
    )).toBe(true);
  });

  it('downloads the COHORT-SCOPED template, not the generic one', async () => {
    mockShape(SINGLE_BU_SHAPE);
    const { container } = renderModal({ sessionId: 'sid-42' });
    await screen.findByText(/Single Business/i);

    const btn = [...container.querySelectorAll('button')]
      .find((b) => /Download template/i.test(b.textContent));
    btn.click();
    await waitFor(() => {
      expect(global.fetch.mock.calls.some(
        ([url]) => String(url) === '/api/admin/sid-42/players/bulk-template',
      )).toBe(true);
    });
    // The cohort-less route cannot know a single-business cohort's industry and
    // region vocabulary, so using it here would hand back the wrong sheet.
    expect(global.fetch.mock.calls.some(
      ([url]) => String(url) === '/api/admin/players/bulk-template',
    )).toBe(false);
  });

  it('degrades to generic copy when the shape cannot be read, without alarming', async () => {
    // The template build and the upload are both gated server-side by the same
    // shape, so a failed shape fetch costs tailored copy and nothing else.
    global.fetch = jest.fn(() => Promise.resolve({ ok: false, status: 500, json: async () => ({}) }));
    renderModal();
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    expect(screen.queryByText(/Could not/i)).not.toBeInTheDocument();
    expect(screen.getByText(/All or nothing/i)).toBeInTheDocument();
  });

  it('renders the hint immediately so the first frame is never blank', () => {
    mockShape(SINGLE_BU_SHAPE);
    renderModal({ shapeHint: SINGLE_BU_SHAPE });
    // No await: this must be true before the fetch resolves.
    expect(screen.getByText(/Single Business/i)).toBeInTheDocument();
  });
});
