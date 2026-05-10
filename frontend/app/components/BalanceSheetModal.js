'use client';
import React from 'react';
import styles from './ExecutiveCockpit.module.css';

/**
 * BalanceSheetModal — Full IFRS Statement of Financial Position
 * CL-2: Moved from sidebar (0.58rem) to modal with readable font sizes.
 */
export default function BalanceSheetModal({ balanceSheet, isOpen, onClose, fmtCurrency }) {
  if (!isOpen || !balanceSheet) return null;

  const fmtM = (v) => `$${((v || 0) / 1_000_000).toFixed(1)}M`;
  const fmtK = (v) => Math.abs(v || 0) >= 1_000_000 ? fmtM(v) : `$${((v || 0) / 1_000).toFixed(0)}K`;

  const totalAssets = balanceSheet.total_assets || 0;
  const totalLiabilities = balanceSheet.total_liabilities || 0;
  const netAssets = balanceSheet.net_assets || 0;
  const deRatio = balanceSheet.debt_to_equity || 0;
  const covenantStatus = balanceSheet.covenant_status || 'green';
  const ndEbitda = balanceSheet.net_debt_to_ebitda || 0;
  const strandedExposure = balanceSheet.stranded_asset_exposure || 0;

  const covenantColors = { green: '#10b981', amber: '#f59e0b', red: '#ef4444', breached: '#dc2626' };
  const covenantLabels = { green: '🟢 Comfortable', amber: '🟡 Watch List', red: '🔴 Breach (Cure Period)', breached: '🚨 Acceleration' };

  const ta = balanceSheet.tangible_assets || {};
  const ia = balanceSheet.intangible_assets || {};
  const ca = balanceSheet.current_assets || {};
  const ncl = balanceSheet.non_current_liabilities || {};
  const cl = balanceSheet.current_liabilities || {};

  const totalTangible = Object.values(ta).reduce((s, v) => s + (v || 0), 0);
  const totalIntangible = Object.values(ia).reduce((s, v) => s + (v || 0), 0);
  const totalCurrent = Object.values(ca).reduce((s, v) => s + (v || 0), 0);
  const totalNCL = Object.values(ncl).reduce((s, v) => s + (v || 0), 0);
  const totalCL = Object.values(cl).reduce((s, v) => s + (v || 0), 0);
  const totalEquity = (balanceSheet.share_capital || 0) + (balanceSheet.retained_earnings || 0) + (balanceSheet.other_reserves || 0);

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

  return (
    <div className={styles.bsModalOverlay} onClick={onClose}>
      <div className={styles.bsModalPanel} onClick={(e) => e.stopPropagation()}>
        <div className={styles.bsModalHeader}>
          <div>
            <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#38bdf8' }}>📊 Statement of Financial Position</div>
            <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: 2 }}>IFRS-Compliant Balance Sheet</div>
          </div>
          <button onClick={onClose} style={{
            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 6, color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700,
            padding: '4px 12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif",
          }}>ESC · Close</button>
        </div>

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
              {lineRow('Social Licence (IAS 38)', ia.social_licence_asset, { indent: true })}
              {lineRow('Reputation Capital', ia.reputation_asset, { indent: true })}
              {lineRow('Total Intangible Assets', totalIntangible, { bold: true, topBorder: true })}

              {sectionHeader('Current Assets', '💵')}
              {lineRow('Cash & Equivalents', ca.cash_and_equivalents, { indent: true, color: (ca.cash_and_equivalents || 0) < 0 ? '#f87171' : '#4ade80' })}
              {lineRow('Trade Receivables', ca.trade_receivables, { indent: true })}
              {lineRow('Prepayments', ca.prepayments, { indent: true })}
              {lineRow('Total Current Assets', totalCurrent, { bold: true, topBorder: true })}

              {lineRow('TOTAL ASSETS', totalAssets, { bold: true, topBorder: true, bottomBorder: true, color: '#38bdf8' })}
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

              {sectionHeader('Shareholders\' Equity', '🏛️')}
              {lineRow('Share Capital', balanceSheet.share_capital, { indent: true })}
              {lineRow('Retained Earnings', balanceSheet.retained_earnings, { indent: true, color: (balanceSheet.retained_earnings || 0) < 0 ? '#f87171' : undefined })}
              {lineRow('Other Reserves', balanceSheet.other_reserves, { indent: true })}
              {lineRow('TOTAL EQUITY', totalEquity, { bold: true, topBorder: true, bottomBorder: true, color: '#a78bfa' })}

              {lineRow('NET ASSETS (= Equity)', netAssets, { bold: true, topBorder: true, color: netAssets >= 0 ? '#4ade80' : '#ef4444' })}
            </div>
          </div>

          {/* Bottom: Key Ratios + Covenant + Trend */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginTop: 16, paddingTop: 12, borderTop: '1px solid rgba(148,163,184,0.1)' }}>
            {/* Ratios */}
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(56,189,248,0.05)', border: '1px solid rgba(56,189,248,0.1)' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>📐 Key Ratios</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                  <span style={{ color: '#94a3b8' }}>Debt / Equity</span>
                  <span style={{ fontWeight: 800, color: deRatio < 2.0 ? '#4ade80' : '#ef4444', fontFamily: "'JetBrains Mono', monospace" }}>{deRatio.toFixed(2)}×</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                  <span style={{ color: '#94a3b8' }}>ND / EBITDA</span>
                  <span style={{ fontWeight: 800, color: ndEbitda <= 2.5 ? '#4ade80' : '#ef4444', fontFamily: "'JetBrains Mono', monospace" }}>{ndEbitda.toFixed(2)}×</span>
                </div>
                {strandedExposure > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                    <span style={{ color: '#f59e0b' }}>Stranded Exposure</span>
                    <span style={{ fontWeight: 800, color: '#f59e0b', fontFamily: "'JetBrains Mono', monospace" }}>{fmtM(strandedExposure)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Covenant */}
            <div style={{ padding: '10px 14px', borderRadius: 8, background: `${covenantColors[covenantStatus]}08`, border: `1px solid ${covenantColors[covenantStatus]}20` }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>🏛️ Covenant Status</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 800, color: covenantColors[covenantStatus] }}>
                {covenantLabels[covenantStatus] || covenantStatus}
              </div>
            </div>

            {/* Trend */}
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(56,189,248,0.03)', border: '1px solid rgba(56,189,248,0.08)' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>📈 Net Assets Trend</div>
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
                <div style={{ fontSize: '0.7rem', color: '#475569' }}>Not enough data yet</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
