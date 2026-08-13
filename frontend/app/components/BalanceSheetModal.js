'use client';
import React from 'react';
import styles from './ExecutiveCockpit.module.css';
import Dialog from './Dialog';
import { currencySymbol, atRate } from '../utils/format';

/**
 * BalanceSheetModal — Full IFRS Statement of Financial Position
 * CL-2: Moved from sidebar (0.58rem) to modal with readable font sizes.
 *
 * Scholarly ESG Toggle:
 * When balanceSheet.esg_bs_mode.active === true (set by facilitator/god-mode),
 * Social Licence Capital and Reputation Capital are shown as GAAP Intangible
 * Assets with a prominent amber "Scholarly View" banner and † markers.
 * Per IAS 38, these are excluded by default.
 * Reference: IIRC <IR> Framework; Barker & Eccles (2011); Gleeson-White (2014).
 */
export default function BalanceSheetModal({ balanceSheet, isOpen, onClose, fmtCurrency }) {
  if (!isOpen || !balanceSheet) return null;

  const fmtM = (v) => `${currencySymbol()}${atRate((v || 0) / 1_000_000).toFixed(1)}M`;
  const fmtK = (v) => Math.abs(v || 0) >= 1_000_000 ? fmtM(v) : `${currencySymbol()}${atRate((v || 0) / 1_000).toFixed(0)}K`;

  // ── Scholarly mode detection ──────────────────────────────────────────────
  const esgBsMode    = balanceSheet.esg_bs_mode || {};
  const isScholarly  = esgBsMode.active === true;
  const scholarlySLC = esgBsMode.social_licence_on_bs || 0;
  const scholarlyRep = esgBsMode.reputation_on_bs || 0;
  const scholarlyTotal = esgBsMode.total_esg_on_bs || 0;

  const totalAssets      = balanceSheet.total_assets || 0;
  const totalLiabilities = balanceSheet.total_liabilities || 0;
  const netAssets        = balanceSheet.net_assets || 0;
  const deRatio          = balanceSheet.debt_to_equity || 0;
  const covenantStatus   = balanceSheet.covenant_status || 'green';
  const ndEbitda         = balanceSheet.net_debt_to_ebitda || 0;
  const strandedExposure = balanceSheet.stranded_asset_exposure || 0;

  const covenantColors = { green: '#10b981', amber: '#f59e0b', red: '#ef4444', breached: '#dc2626' };
  const covenantLabels = { green: '🟢 Comfortable', amber: '🟡 Watch List', red: '🔴 Breach (Cure Period)', breached: '🚨 Acceleration' };

  const ta  = balanceSheet.tangible_assets || {};
  const ia  = balanceSheet.intangible_assets || {};
  const ca  = balanceSheet.current_assets || {};
  const ncl = balanceSheet.non_current_liabilities || {};
  const cl  = balanceSheet.current_liabilities || {};
  // FIX-C: ESG capitals moved from intangible_assets to esg_capitals (IAS 38 / FIX-8)
  const esgCap = balanceSheet.esg_capitals || {};

  // In scholarly mode, ia already contains esg_social_licence_capital and
  // esg_reputation_capital — we EXCLUDE them from the per-line display and use
  // the dedicated scholarly rows instead, so we strip them from totalIntangible
  // to avoid double-counting if the engine ever includes them in the dict sum.
  const totalTangible   = Object.values(ta).reduce((s, v) => s + (v || 0), 0);
  const totalIntangible = Object.values(ia).reduce((s, v) => s + (v || 0), 0);
  const totalCurrent    = Object.values(ca).reduce((s, v) => s + (v || 0), 0);
  const totalNCL        = Object.values(ncl).reduce((s, v) => s + (v || 0), 0);
  const totalCL         = Object.values(cl).reduce((s, v) => s + (v || 0), 0);
  const totalEquity     = (balanceSheet.share_capital || 0) + (balanceSheet.retained_earnings || 0) + (balanceSheet.other_reserves || 0);

  const lineRow = (label, value, opts = {}) => (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: opts.bold ? '5px 0' : '3px 0',
      borderTop: opts.topBorder ? '1px solid rgba(148,163,184,0.15)' : 'none',
      borderBottom: opts.bottomBorder ? '1px double rgba(148,163,184,0.2)' : 'none',
    }}>
      <span style={{
        fontSize: opts.bold ? '0.78rem' : '0.72rem',
        fontWeight: opts.bold ? 800 : 500,
        color: opts.color || (opts.bold ? '#e2e8f0' : '#94a3b8'),
        paddingLeft: opts.indent ? 16 : 0,
      }}>{label}</span>
      <span style={{
        fontSize: opts.bold ? '0.8rem' : '0.72rem',
        fontWeight: opts.bold ? 800 : 600,
        fontFamily: "'JetBrains Mono', monospace",
        color: opts.color || (opts.bold ? '#e2e8f0' : '#cbd5e1'),
      }}>{typeof value === 'number' ? fmtK(value) : value}</span>
    </div>
  );

  const sectionHeader = (label, icon) => (
    <div style={{
      fontSize: '0.78rem', fontWeight: 800, textTransform: 'uppercase',
      letterSpacing: '0.08em', color: '#64748b', marginTop: 14, marginBottom: 4,
      display: 'flex', alignItems: 'center', gap: 6,
    }}>{icon} {label}</div>
  );

  // ── Scholarly ESG line row (amber, †-marked) ──────────────────────────────
  const scholarlyRow = (label, value) => (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '3px 0',
      borderLeft: '2px solid rgba(245,158,11,0.5)',
      paddingLeft: 12,
      marginLeft: 4,
    }}>
      <span style={{ fontSize: 'var(--type-caption)', fontWeight: 500, color: '#f59e0b' }}>{label}</span>
      <span style={{
        fontSize: 'var(--type-caption)', fontWeight: 700,
        fontFamily: "'JetBrains Mono', monospace", color: '#fbbf24',
      }}>{fmtK(value)}</span>
    </div>
  );

  return (
    /* A11Y-3 (UX audit #18): was a bare div with a backdrop onClick — no
       dialog role, no Escape, no focus management. Dialog supplies all of it
       and keeps the existing backdrop-click-to-close behaviour. */
    <Dialog className={styles.bsModalOverlay} onClose={onClose} labelledBy="bs-modal-title">
      {/* PHASE 8: stopPropagation removed - Dialog already tests
          target === currentTarget on the backdrop. */}
        <div className={styles.bsModalPanel}>
        <div className={styles.bsModalHeader}>
          <div>
            <div id="bs-modal-title" style={{ fontSize: '0.88rem', fontWeight: 800, color: '#38bdf8' }}>
              📊 Statement of Financial Position
            </div>
            <div style={{ fontSize: 'var(--type-caption)', color: '#64748b', marginTop: 2 }}>
              {isScholarly
                ? 'IFRS Balance Sheet — Scholarly View (ESG Capitals On-Balance-Sheet)'
                : 'IFRS-Compliant Balance Sheet'}
            </div>
          </div>
          <button onClick={onClose} style={{
            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 6, color: '#94a3b8', fontSize: 'var(--type-caption)', fontWeight: 700,
            padding: '4px 12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif",
          }}>ESC · Close</button>
        </div>

        {/* ── Scholarly View Banner ─────────────────────────────────────────── */}
        {isScholarly && (
          <div style={{
            margin: '0 0 14px 0',
            padding: '10px 14px',
            borderRadius: 8,
            background: 'rgba(245,158,11,0.08)',
            border: '1px solid rgba(245,158,11,0.35)',
            borderLeft: '4px solid #f59e0b',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={{ fontSize: '0.8rem' }}>📚</span>
              <span style={{ fontSize: '0.76rem', fontWeight: 800, color: '#fbbf24', letterSpacing: '0.04em' }}>
                SCHOLARLY VIEW ACTIVE
              </span>
              <span style={{
                fontSize: 'var(--type-caption)', fontWeight: 700, color: '#f59e0b',
                background: 'rgba(245,158,11,0.15)', borderRadius: 4, padding: '1px 6px',
                border: '1px solid rgba(245,158,11,0.3)',
              }}>WHAT-IF MODE</span>
            </div>
            <div style={{ fontSize: 'var(--type-caption)', color: '#94a3b8', lineHeight: 1.5 }}>
              Social Licence Capital <strong style={{ color: '#fbbf24' }}>{fmtM(scholarlySLC)}</strong> and
              Reputation Capital <strong style={{ color: '#fbbf24' }}>{fmtM(scholarlyRep)}</strong> are
              recognised as Intangible Assets (+{fmtM(scholarlyTotal)} to Total Assets &amp; Equity).{' '}
              <span style={{ color: '#64748b' }}>
                IAS 38 prohibits this in standard IFRS (internally generated intangibles).
                This view explores the academic debate:
                IIRC &lt;IR&gt; Framework (2021) · Barker &amp; Eccles (2011) · Gleeson-White (2014).
              </span>
            </div>
          </div>
        )}

        <div className={styles.bsModalBody}>
          {/* Two-column layout for Assets / Liabilities+Equity */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            {/* LEFT: Assets */}
            <div>
              {sectionHeader('Non-Current Assets', '🏭')}
              {lineRow('Property, Plant & Equipment', ta.property_plant_equipment, { indent: true })}
              {lineRow('Right-of-Use Assets (IFRS 16)', ta.right_of_use_assets, { indent: true })}
              {lineRow('Inventory', ta.inventory, { indent: true })}
              {lineRow('Total Tangible Assets', totalTangible, { bold: true, topBorder: true })}

              {sectionHeader('Intangible Assets', '💎')}
              {lineRow('Brand Value', ia.brand_value, { indent: true })}
              {lineRow('Intellectual Property', ia.intellectual_property, { indent: true })}
              {lineRow('Goodwill', ia.goodwill, { indent: true })}

              {/* ── Scholarly: ESG capitals as on-GAAP intangibles ──────────── */}
              {isScholarly && (
                <div style={{ marginTop: 4 }}>
                  <div style={{ fontSize: 'var(--type-caption)', color: '#92400e', fontStyle: 'italic', marginBottom: 3, paddingLeft: 16 }}>
                    † Scholarly recognition (IAS 38 debate — see banner above)
                  </div>
                  {scholarlyRow('† Social Licence Capital [Scholarly]', scholarlySLC)}
                  {scholarlyRow('† Reputation Capital [Scholarly]', scholarlyRep)}
                </div>
              )}

              {/* FIX-C: When NOT in scholarly mode, Social Licence & Reputation are
                  non-GAAP <IR> Framework capitals, excluded from Total Assets (IAS 38). */}
              {!isScholarly && (esgCap.social_licence_capital || esgCap.reputation_capital) ? (
                <div style={{ marginTop: 6, paddingTop: 6, borderTop: '1px dashed rgba(148,163,184,0.1)' }}>
                  <div style={{ fontSize: 'var(--type-caption)', color: '#475569', fontStyle: 'italic', marginBottom: 3 }}>
                    † Non-GAAP ESG Capitals (IAS 38 / &#60;IR&#62; Framework — excluded from total assets)
                  </div>
                  {lineRow('† Social Licence Capital', esgCap.social_licence_capital, { indent: true, color: '#64748b' })}
                  {lineRow('† Reputation Capital', esgCap.reputation_capital, { indent: true, color: '#64748b' })}
                </div>
              ) : null}

              {lineRow('Total Intangible Assets', totalIntangible, { bold: true, topBorder: true })}

              {sectionHeader('Current Assets', '💵')}
              {lineRow('Cash & Equivalents', ca.cash_and_equivalents, { indent: true, color: (ca.cash_and_equivalents || 0) < 0 ? '#f87171' : '#4ade80' })}
              {lineRow('Trade Receivables', ca.trade_receivables, { indent: true })}
              {lineRow('Prepayments', ca.prepayments, { indent: true })}
              {lineRow('Total Current Assets', totalCurrent, { bold: true, topBorder: true })}

              {lineRow('TOTAL ASSETS', totalAssets, { bold: true, topBorder: true, bottomBorder: true, color: isScholarly ? '#fbbf24' : '#38bdf8' })}

              {/* Scholarly delta chip */}
              {isScholarly && (
                <div style={{
                  marginTop: 4, padding: '3px 8px', borderRadius: 4,
                  background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)',
                  fontSize: 'var(--type-caption)', color: '#f59e0b', textAlign: 'right',
                }}>
                  📚 +{fmtM(scholarlyTotal)} vs. standard IFRS view
                </div>
              )}
            </div>

            {/* RIGHT: Liabilities + Equity */}
            <div>
              {sectionHeader('Non-Current Liabilities', '🏦')}
              {lineRow('Revolving Credit Facility', ncl.revolving_credit_facility, { indent: true })}
              {lineRow('Green Bonds Outstanding', ncl.green_bonds_outstanding, { indent: true, color: (ncl.green_bonds_outstanding || 0) > 0 ? '#10b981' : undefined })}
              {lineRow('Environmental Provisions', ncl.environmental_provisions, { indent: true })}
              {lineRow('Decommissioning Obligations', ncl.decommissioning_obligations, { indent: true })}
              {lineRow('Lease Liabilities (IFRS 16)', ncl.lease_liabilities, { indent: true })}
              {lineRow('Total Non-Current Liabilities', totalNCL, { bold: true, topBorder: true })}

              {sectionHeader('Current Liabilities', '📋')}
              {lineRow('Trade Payables', cl.trade_payables, { indent: true })}
              {lineRow('Tax Provisions', cl.tax_provisions, { indent: true })}
              {lineRow('Accrued Remediation', cl.accrued_remediation, { indent: true })}
              {lineRow('Short-Term Debt', cl.short_term_debt, { indent: true })}
              {lineRow('Total Current Liabilities', totalCL, { bold: true, topBorder: true })}

              {lineRow('TOTAL LIABILITIES', totalLiabilities, { bold: true, topBorder: true, bottomBorder: true, color: '#f87171' })}

              {sectionHeader("Shareholders' Equity", '🏛️')}
              {lineRow('Share Capital', balanceSheet.share_capital, { indent: true })}
              {lineRow('Retained Earnings', balanceSheet.retained_earnings, {
                indent: true,
                color: (balanceSheet.retained_earnings || 0) < 0 ? '#f87171' : (isScholarly ? '#fbbf24' : undefined),
              })}
              {isScholarly && (
                <div style={{ fontSize: 'var(--type-caption)', color: '#92400e', fontStyle: 'italic', paddingLeft: 16, marginTop: -2, marginBottom: 2 }}>
                  ↑ Retained Earnings includes {fmtM(scholarlyTotal)} from ESG capital recognition
                </div>
              )}
              {lineRow('Other Reserves', balanceSheet.other_reserves, { indent: true })}
              {lineRow('TOTAL EQUITY', totalEquity, { bold: true, topBorder: true, bottomBorder: true, color: isScholarly ? '#fbbf24' : '#a78bfa' })}

              {lineRow('NET ASSETS (= Equity)', netAssets, { bold: true, topBorder: true, color: netAssets >= 0 ? '#4ade80' : '#ef4444' })}
            </div>
          </div>

          {/* Bottom: Key Ratios + Covenant + Trend */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginTop: 16, paddingTop: 12, borderTop: '1px solid rgba(148,163,184,0.1)' }}>
            {/* Ratios */}
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(56,189,248,0.05)', border: '1px solid rgba(56,189,248,0.1)' }}>
              <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>📐 Key Ratios</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--type-caption)' }}>
                  <span style={{ color: '#94a3b8' }}>Debt / Equity</span>
                  <span style={{ fontWeight: 800, color: deRatio < 2.0 ? '#4ade80' : '#ef4444', fontFamily: "'JetBrains Mono', monospace" }}>{deRatio.toFixed(2)}×</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--type-caption)' }}>
                  <span style={{ color: '#94a3b8' }}>ND / EBITDA</span>
                  <span style={{ fontWeight: 800, color: ndEbitda <= 2.5 ? '#4ade80' : '#ef4444', fontFamily: "'JetBrains Mono', monospace" }}>{ndEbitda.toFixed(2)}×</span>
                </div>
                {strandedExposure > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--type-caption)' }}>
                    <span style={{ color: '#f59e0b' }}>Stranded Exposure</span>
                    <span style={{ fontWeight: 800, color: '#f59e0b', fontFamily: "'JetBrains Mono', monospace" }}>{fmtM(strandedExposure)}</span>
                  </div>
                )}
                {isScholarly && (
                  <div style={{
                    marginTop: 4, paddingTop: 4, borderTop: '1px dashed rgba(245,158,11,0.2)',
                    fontSize: 'var(--type-caption)', color: '#f59e0b',
                  }}>
                    📚 D/E improved by ESG capitalisation
                  </div>
                )}
              </div>
            </div>

            {/* Covenant */}
            <div style={{ padding: '10px 14px', borderRadius: 8, background: `${covenantColors[covenantStatus]}08`, border: `1px solid ${covenantColors[covenantStatus]}20` }}>
              <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>🏛️ Covenant Status</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 800, color: covenantColors[covenantStatus] }}>
                {covenantLabels[covenantStatus] || covenantStatus}
              </div>
            </div>

            {/* Trend */}
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(56,189,248,0.03)', border: '1px solid rgba(56,189,248,0.08)' }}>
              <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>📈 Net Assets Trend</div>
              {balanceSheet.balance_sheet_history?.length > 1 ? (
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 36 }}>
                  {balanceSheet.balance_sheet_history.map((h, i) => {
                    const maxNA = Math.max(...balanceSheet.balance_sheet_history.map(x => Math.abs(x.net_assets || 1)));
                    const pct = Math.max(6, Math.abs(h.net_assets || 0) / maxNA * 100);
                    const isNeg = (h.net_assets || 0) < 0;
                    return (
                      <div key={i} title={`R${h.round}: ${fmtM(h.net_assets)}`} style={{
                        flex: 1, height: `${pct}%`, borderRadius: 2, minHeight: 4,
                        background: isNeg ? '#ef4444' : '#38bdf8',
                        opacity: 0.5 + (i / balanceSheet.balance_sheet_history.length) * 0.5,
                      }} />
                    );
                  })}
                </div>
              ) : (
                <div style={{ fontSize: 'var(--type-caption)', color: '#475569' }}>Not enough data yet</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
