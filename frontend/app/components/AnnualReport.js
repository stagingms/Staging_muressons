'use client';
import { useMemo, useCallback } from 'react';
import Dialog from './Dialog';
import { calculateRoundStockPrice } from './stockValuationEngine';
import { deriveRatingLetter, AGENCY } from './rivalIntel';
import { roundToQuarter } from '../utils/roundToQuarter';
import { currencySymbol, atRate } from '../utils/format';

/**
 * AnnualReport — W-C (W3): Year-End Integrated Annual Report.
 *
 * A one-page, print-styled integrated report offered in the results step
 * after each even round (year boundary). Everything renders from the
 * commit snapshot + history already on the client:
 *   - financial highlights (per-round EBITDA, treasury, share price, reputation)
 *   - emissions trajectory (SVG bars from history tco2e)
 *   - Meridian ESG rating (same deterministic derivation as the mailbox letter)
 *   - THE TEAM'S OWN double-materiality assessment — top material issues from
 *     the per-industry materiality library, scored by how the team placed them
 *     (globalState.materiality_issue_scores, persisted by the R2 CSRD gate)
 *
 * Flow-safety: optional overlay opened from a button in the results step;
 * closing returns to results; the advance path is untouched. Zero fetches;
 * PNG export is offline (SVG → canvas, same pattern as FrontPageReveal).
 */

const M = (v) => `${currencySymbol()}${atRate((v || 0) / 1_000_000).toFixed(1)}M`;
const BASE_YEAR = new Date().getFullYear();

// Build the report model from snapshot data only. Pure + deterministic.
export function buildReportModel({ roundNumber, commitResults, history, businessUnits }) {
  const gs = commitResults?.globalState || {};
  const bus = commitResults?.businessUnits || businessUnits || [];
  const year = Math.ceil(roundNumber / 2);
  const fy = roundToQuarter(roundNumber, BASE_YEAR).year;

  // Per-round EBITDA — same definition as everywhere else in the cockpit
  const ebitda = gs.historical_ebitda ||
    (bus.reduce((a, b) => a + (b.revenue_base || 0) - (b.opex_base || 0), 0) || 0);
  const treasury = gs.corporate_treasury || 0;
  const reputation = gs.group_reputation ?? 50;
  const avgNCD = bus.length ? bus.reduce((s, b) => s + (b.natural_capital_debt || 0), 0) / bus.length : 0;
  const sharePrice = calculateRoundStockPrice({
    ebitda,
    synergy_multiplier: gs.synergy_multiplier || 1.0,
    natural_capital_debt: avgNCD,
    group_reputation: reputation,
    cost_of_capital: gs.cost_of_capital || 0.05,
    exit_multiple: gs.active_event_flags?.valuation_preview?.exit_multiple ?? null,  // F-17
  });

  // Year-ago comparison: the snapshot two rounds earlier
  const yearAgo = (history || []).find(h => h.round_number === roundNumber - 2);
  const yaGs = yearAgo?.global_state || null;

  // Emissions trajectory: committed rounds + this year-end snapshot
  const emissions = [
    ...(history || [])
      .filter(h => (h.round_number || 0) < roundNumber)
      .map(h => ({ round: h.round_number, tco2e: h.global_state?.tco2e_emissions || 0 })),
    { round: roundNumber, tco2e: gs.tco2e_emissions || 0 },
  ];

  // Rating: reuse the W-B derivation on history + this snapshot
  const ratingHistory = [
    ...(history || []).filter(h => (h.round_number || 0) < roundNumber),
    { round_number: roundNumber, global_state: gs, business_units: bus },
  ];
  const rating = deriveRatingLetter(ratingHistory);

  // Materiality: the team's own scored assessment (per-industry library)
  const issueScores = gs.materiality_issue_scores || null;
  const materiality = issueScores
    ? {
        accuracy: gs.materiality_full_accuracy ?? null,
        status: gs.materiality_status || null,
        buId: gs.materiality_bu_id || null,
        issues: Object.entries(issueScores)
          .map(([id, s]) => ({ id, ...s }))
          .sort((a, b) => (b.materiality_product || 0) - (a.materiality_product || 0) || (b.credit || 0) - (a.credit || 0))
          .slice(0, 6),
      }
    : null;

  return { year, fy, roundNumber, ebitda, treasury, reputation, sharePrice, yaGs, emissions, rating, materiality };
}

const kpiDelta = (cur, prev, fmt, invert = false) => {
  if (prev == null) return null;
  const d = cur - prev;
  if (d === 0) return { text: 'unchanged', color: '#94a3b8' };
  const good = invert ? d < 0 : d > 0;
  return { text: `${d > 0 ? '+' : ''}${fmt(d)} YoY`, color: good ? '#059669' : '#dc2626' };
};

export default function AnnualReport({ open, onClose, roundNumber, commitResults, history, businessUnits, teamName = '' }) {
  const model = useMemo(
    () => buildReportModel({ roundNumber, commitResults, history, businessUnits }),
    [roundNumber, commitResults, history, businessUnits]
  );

  /* PHASE 8. Escape used to be handled here, unconditionally, on window — so
     this modal closed on Escape even when something was stacked on top of it.
     Dialog owns Escape now (topmost-only, via a module-level stack) along with
     the focus trap and focus restore this never had. */

  const download = useCallback(() => {
    const W = 1200, H = 1560;
    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const m = model;
    const maxE = Math.max(1, ...m.emissions.map(e => e.tco2e));
    const barW = Math.min(70, 700 / Math.max(1, m.emissions.length));
    const bars = m.emissions.map((e, i) => {
      const h = Math.max(4, (e.tco2e / maxE) * 160);
      const x = 90 + i * (barW + 18);
      return `<rect x="${x}" y="${560 - h}" width="${barW}" height="${h}" fill="#0d9488" opacity="0.75"/>
        <text x="${x + barW / 2}" y="${578}" text-anchor="middle" font-family="Georgia,serif" font-size="14" fill="#666">R${e.round}</text>
        <text x="${x + barW / 2}" y="${548 - h}" text-anchor="middle" font-family="Georgia,serif" font-size="13" fill="#333">${Math.round(e.tco2e).toLocaleString()}</text>`;
    }).join('');
    const kpis = [
      ['EBITDA', M(m.ebitda)], ['TREASURY', M(m.treasury)],
      ['SHARE PRICE', `${currencySymbol()}${atRate(m.sharePrice).toFixed(2)}`], ['REPUTATION', `${m.reputation.toFixed(0)}/100`],
    ].map(([label, val], i) => {
      const x = 70 + i * 270;
      return `<rect x="${x}" y="230" width="250" height="110" fill="#faf8f3" stroke="#d9d2c4"/>
        <text x="${x + 125}" y="268" text-anchor="middle" font-family="Georgia,serif" font-size="15" letter-spacing="2" fill="#777">${label}</text>
        <text x="${x + 125}" y="315" text-anchor="middle" font-family="Georgia,serif" font-size="34" font-weight="800" fill="#111">${esc(val)}</text>`;
    }).join('');
    const matRows = (m.materiality?.issues || []).map((iss, i) => {
      const y = 780 + i * 44;
      const ok = (iss.credit || 0) >= 1;
      const half = (iss.credit || 0) === 0.5;
      const mark = ok ? '✓ addressed' : half ? '◐ partially assessed' : '✗ mis-assessed';
      const color = ok ? '#059669' : half ? '#d97706' : '#dc2626';
      return `<text x="90" y="${y}" font-family="Georgia,serif" font-size="20" fill="#222">${esc(iss.title || iss.id)}</text>
        <text x="${W - 90}" y="${y}" text-anchor="end" font-family="Georgia,serif" font-size="18" fill="${color}">${mark}</text>`;
    }).join('');
    const ratingBlock = m.rating ? `
      <rect x="850" y="440" width="260" height="140" fill="#faf8f3" stroke="#d9d2c4"/>
      <text x="980" y="472" text-anchor="middle" font-family="Georgia,serif" font-size="15" letter-spacing="2" fill="#777">MERIDIAN ESG RATING</text>
      <text x="980" y="535" text-anchor="middle" font-family="Georgia,serif" font-size="52" font-weight="900" fill="#5b21b6">${esc(m.rating.grade)}</text>
      <text x="980" y="565" text-anchor="middle" font-family="Georgia,serif" font-size="14" fill="#666">${esc(m.rating.direction.toUpperCase())} · ${m.rating.score}/100</text>` : '';
    const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#f4f1ea"/>
  <rect x="0" y="0" width="${W}" height="12" fill="#0d9488"/>
  <text x="${W / 2}" y="80" text-anchor="middle" font-family="Georgia,serif" font-size="44" font-weight="800" fill="#111">MURESSONS GLOBAL CORPORATION</text>
  <text x="${W / 2}" y="125" text-anchor="middle" font-family="Georgia,serif" font-size="24" letter-spacing="4" fill="#0d9488">INTEGRATED ANNUAL REPORT · YEAR ${m.year} (FY${m.fy})</text>
  ${teamName ? `<text x="${W / 2}" y="155" text-anchor="middle" font-family="Georgia,serif" font-size="17" fill="#777">${esc(teamName)}</text>` : ''}
  <line x1="70" y1="180" x2="${W - 70}" y2="180" stroke="#1a1a1a" stroke-width="2"/>
  ${kpis}
  <text x="70" y="415" font-family="Georgia,serif" font-size="22" font-weight="800" fill="#111">EMISSIONS TRAJECTORY (tCO₂e)</text>
  ${bars}
  ${ratingBlock}
  <line x1="70" y1="640" x2="${W - 70}" y2="640" stroke="#ccc" stroke-width="1"/>
  <text x="70" y="690" font-family="Georgia,serif" font-size="22" font-weight="800" fill="#111">MATERIAL SUSTAINABILITY MATTERS${m.materiality?.buId ? ` · ${esc(String(m.materiality.buId).replace(/_/g, ' ').toUpperCase())} SECTOR LIBRARY` : ''}</text>
  ${m.materiality
    ? `<text x="70" y="726" font-family="Georgia,serif" font-size="17" fill="#555">Double-materiality assessment accuracy: ${m.materiality.accuracy}% · Board stance: ${esc(m.materiality.status || 'n/a')}</text>${matRows}`
    : `<text x="70" y="726" font-family="Georgia,serif" font-size="17" fill="#777" font-style="italic">Double-materiality assessment not yet performed this cycle.</text>`}
  <line x1="70" y1="${H - 120}" x2="${W - 70}" y2="${H - 120}" stroke="#ccc" stroke-width="1"/>
  <text x="70" y="${H - 84}" font-family="Georgia,serif" font-size="15" fill="#888">Prepared from live simulation data at the close of Round ${m.roundNumber}. Deterministic derivation — figures match the boardroom cockpit.</text>
  <text x="70" y="${H - 58}" font-family="Georgia,serif" font-size="15" fill="#888">Muressons Global Corporation · Sustainability Strategy Simulation · Integrated Reporting (IFRS S1/S2 + ESRS style)</text>
</svg>`.trim();
    const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = W; c.height = H;
      c.getContext('2d').drawImage(img, 0, 0); URL.revokeObjectURL(url);
      c.toBlob((png) => {
        if (!png) return;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(png);
        a.download = `muressons-year${model.year}-annual-report.png`;
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      }, 'image/png');
    };
    img.onerror = () => URL.revokeObjectURL(url);
    img.src = url;
  }, [model, teamName]);

  if (!open) return null;
  const m = model;
  const maxE = Math.max(1, ...m.emissions.map(e => e.tco2e));

  return (
    <Dialog
      onClose={onClose}
      label={`Year ${m.year} Integrated Annual Report`}
      style={{
        position: 'fixed', inset: 0, zIndex: 10500,
        background: 'rgba(10, 14, 26, 0.72)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem',
      }}
    >
      {/* PHASE 8: stopPropagation removed - Dialog's backdrop handler
          already tests target === currentTarget, so this guard was a click
          target with no purpose and no keyboard equivalent. */}
      <div
        style={{
          width: '100%', maxWidth: 760, maxHeight: '88vh', overflowY: 'auto',
          background: '#f4f1ea', color: '#1a1a1a', borderRadius: 4,
          fontFamily: 'Georgia, "Times New Roman", serif',
          boxShadow: '0 24px 80px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{ height: 8, background: '#0d9488' }} />
        <div style={{ padding: '22px 30px 26px' }}>
          {/* Masthead */}
          <div style={{ textAlign: 'center', borderBottom: '2px solid #1a1a1a', paddingBottom: 12 }}>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, letterSpacing: '0.02em' }}>MURESSONS GLOBAL CORPORATION</div>
            <div style={{ fontSize: '0.8rem', letterSpacing: '0.28em', color: '#0d9488', fontWeight: 700, marginTop: 4 }}>
              INTEGRATED ANNUAL REPORT · YEAR {m.year} (FY{m.fy})
            </div>
            {teamName && <div style={{ fontSize: 'var(--type-caption)', color: '#777', marginTop: 3 }}>{teamName}</div>}
          </div>

          {/* KPI row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, margin: '16px 0' }}>
            {[
              { label: 'EBITDA', val: M(m.ebitda), delta: kpiDelta(m.ebitda, m.yaGs?.historical_ebitda, (d) => M(d)) },
              { label: 'Treasury', val: M(m.treasury), delta: kpiDelta(m.treasury, m.yaGs?.corporate_treasury, (d) => M(d)) },
              { label: 'Share Price', val: `${currencySymbol()}${atRate(m.sharePrice).toFixed(2)}`, delta: null },
              { label: 'Reputation', val: `${m.reputation.toFixed(0)}/100`, delta: kpiDelta(m.reputation, m.yaGs?.group_reputation, (d) => d.toFixed(1)) },
            ].map(({ label, val, delta }) => (
              <div key={label} style={{ background: '#faf8f3', border: '1px solid #d9d2c4', padding: '8px 10px', textAlign: 'center' }}>
                <div style={{ fontSize: 'var(--type-caption)', letterSpacing: '0.14em', color: '#777', textTransform: 'uppercase' }}>{label}</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 800, marginTop: 2 }}>{val}</div>
                {delta && <div style={{ fontSize: 'var(--type-caption)', color: delta.color, marginTop: 1 }}>{delta.text}</div>}
              </div>
            ))}
          </div>

          {/* Emissions + rating side by side */}
          <div style={{ display: 'flex', gap: 14, alignItems: 'stretch' }}>
            <div style={{ flex: 2 }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 800, marginBottom: 6 }}>EMISSIONS TRAJECTORY (tCO₂e)</div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 90, borderBottom: '1px solid #d9d2c4', padding: '0 4px' }}>
                {m.emissions.map((e) => (
                  <div key={e.round} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                    <div style={{ fontSize: 'var(--type-caption)', color: '#555' }}>{Math.round(e.tco2e).toLocaleString()}</div>
                    <div style={{ width: '70%', height: Math.max(3, (e.tco2e / maxE) * 62), background: '#0d9488', opacity: 0.75 }} />
                    <div style={{ fontSize: 'var(--type-caption)', color: '#888' }}>R{e.round}</div>
                  </div>
                ))}
              </div>
            </div>
            {m.rating && (
              <div style={{ flex: 1, background: '#faf8f3', border: '1px solid #d9d2c4', padding: '10px 12px', textAlign: 'center', alignSelf: 'flex-start' }}>
                <div style={{ fontSize: 'var(--type-caption)', letterSpacing: '0.12em', color: '#777' }}>{AGENCY.name.toUpperCase()}</div>
                <div style={{ fontSize: '1.9rem', fontWeight: 900, color: '#5b21b6', lineHeight: 1.2 }}>{m.rating.grade}</div>
                <div style={{ fontSize: 'var(--type-caption)', color: '#666' }}>{m.rating.direction.toUpperCase()} · {m.rating.score}/100</div>
              </div>
            )}
          </div>

          {/* Materiality — the industry library, on the player's page */}
          <div style={{ marginTop: 16, borderTop: '1px solid #d9d2c4', paddingTop: 10 }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 800 }}>
              MATERIAL SUSTAINABILITY MATTERS
              {m.materiality?.buId && (
                <span style={{ fontWeight: 600, color: '#0d9488' }}> · {String(m.materiality.buId).replace(/_/g, ' ').toUpperCase()} SECTOR LIBRARY</span>
              )}
            </div>
            {m.materiality ? (
              <>
                <div style={{ fontSize: 'var(--type-caption)', color: '#555', margin: '3px 0 8px' }}>
                  Double-materiality assessment accuracy: <strong>{m.materiality.accuracy}%</strong>
                  {m.materiality.status && <> · Board stance: <strong>{m.materiality.status}</strong></>}
                </div>
                {m.materiality.issues.map((iss) => {
                  const ok = (iss.credit || 0) >= 1;
                  const half = (iss.credit || 0) === 0.5;
                  return (
                    <div key={iss.id} style={{ display: 'flex', justifyContent: 'space-between', gap: 10, padding: '4px 0', borderBottom: '1px dotted #e2dccd', fontSize: 'var(--type-caption)' }}>
                      <span>{iss.title || iss.id}</span>
                      <span style={{ whiteSpace: 'nowrap', color: ok ? '#059669' : half ? '#d97706' : '#dc2626', fontWeight: 700 }}>
                        {ok ? '✓ addressed' : half ? '◐ partially assessed' : '✗ mis-assessed'}
                      </span>
                    </div>
                  );
                })}
              </>
            ) : (
              <div style={{ fontSize: 'var(--type-caption)', color: '#777', fontStyle: 'italic', marginTop: 4 }}>
                Double-materiality assessment not yet performed this cycle.
              </div>
            )}
          </div>

          <div style={{ fontSize: 'var(--type-caption)', color: '#888', marginTop: 14, borderTop: '1px solid #d9d2c4', paddingTop: 8 }}>
            Prepared from live simulation data at the close of Round {m.roundNumber}. Deterministic — figures match the boardroom cockpit.
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', padding: '10px 0 16px', background: 'rgba(13,148,136,0.06)' }}>
          <button onClick={download} style={{
            padding: '8px 18px', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: '0.85rem',
            border: '1px solid #0d9488', background: 'rgba(13,148,136,0.12)', color: '#0f172a',
          }}>📄 Download PNG</button>
          <button onClick={onClose} style={{
            padding: '8px 18px', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: '0.85rem',
            border: '1px solid #94a3b8', background: 'transparent', color: '#334155',
          }}>Back to results</button>
        </div>
      </div>
    </Dialog>
  );
}
