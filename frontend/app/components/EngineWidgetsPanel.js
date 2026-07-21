'use client';
/**
 * EngineWidgetsPanel — Biodiversity · Board Governance · Supply Chain ·
 * Balance Sheet widgets for the right-panel "Engines" tab.
 * Phase A (player redesign): verbatim extraction from ExecutiveCockpit.js.
 * Shares ExecutiveCockpit.module.css so rendering is pixel-identical.
 */
import { useState, useEffect } from 'react';
import BalanceSheetModal from './BalanceSheetModal';
import styles from './ExecutiveCockpit.module.css';

// ══════════════════════════════════════════════════════════════════
//  ENGINE WIDGETS PANEL — Biodiversity · Board Governance · Supply Chain
//  Renders in the right-panel "Engines" tab. Each widget fetches its
//  own endpoint, degrades silently if the engine is toggled off.
// ══════════════════════════════════════════════════════════════════
export default function EngineWidgetsPanel({ sessionId, globalState, commitResults }) {
  const API = process.env.NEXT_PUBLIC_API_URL || '';
  const [bio, setBio] = useState(null);
  const [board, setBoard] = useState(null);
  const [supply, setSupply] = useState(null);
  const [balanceSheet, setBalanceSheet] = useState(null);
  const [bsModalOpen, setBsModalOpen] = useState(false); // CL-2: Balance Sheet Modal
  const [open, setOpen] = useState({ bio: true, board: false, supply: false, bs: true });
  const [enginesLoaded, setEnginesLoaded] = useState(false); // Friction #5: track initial load

  useEffect(() => {
    if (!sessionId) return;
    // Biodiversity
    fetch(`${API}/api/simulations/${sessionId}/biodiversity`)
      .then(r => r.ok ? r.json() : null).then(d => d && setBio(d)).catch(() => {});
    // Board Governance
    fetch(`${API}/api/simulations/${sessionId}/board-governance`)
      .then(r => r.ok ? r.json() : null).then(d => d && setBoard(d)).catch(() => {});
    // Supply Chain
    fetch(`${API}/api/simulations/${sessionId}/supply-chain`)
      .then(r => r.ok ? r.json() : null).then(d => d && setSupply(d)).catch(() => {});
    // Balance Sheet
    fetch(`${API}/api/simulations/${sessionId}/balance-sheet`)
      .then(r => r.ok ? r.json() : null).then(d => d && setBalanceSheet(d.balance_sheet || d)).catch(() => {});
    // Mark engines as loaded after a short delay (covers network round-trip)
    const t = setTimeout(() => setEnginesLoaded(true), 600);
    return () => clearTimeout(t);
  }, [sessionId]);

  // Re-sync balance sheet after each commit (so sidebar panel shows latest)
  useEffect(() => {
    if (!commitResults) return;
    // Prefer inline data from commit response
    const bsFromCommit = commitResults.globalState?.balance_sheet;
    if (bsFromCommit && bsFromCommit.total_assets) {
      setBalanceSheet(bsFromCommit);
    } else if (sessionId) {
      // Fallback: re-fetch from API
      fetch(`${API}/api/simulations/${sessionId}/balance-sheet`)
        .then(r => r.ok ? r.json() : null).then(d => d && setBalanceSheet(d.balance_sheet || d)).catch(() => {});
    }
  }, [commitResults, sessionId]);

  const toggle = (key) => setOpen(prev => ({ ...prev, [key]: !prev[key] }));

  // AC-4: Migrated from inline styles to CSS module classes
  const Bar = ({ value, max = 100, color }) => (
    <div className={styles.ewBarTrack}>
      <div className={styles.ewBarFill} style={{ width: `${Math.min(100, (value / max) * 100)}%`, background: color }} />
    </div>
  );

  const Pill = ({ label, value, good }) => (
    <div className={styles.ewPill}>
      <span className={styles.ewPillLabel}>{label}</span>
      <span className={styles.ewPillValue} style={{ color: good ? '#10b981' : '#f59e0b' }}>{value}</span>
    </div>
  );

  const noEngine = (name) => (
    <div className={styles.ewNoEngine}>
      {name} engine not active this session.
    </div>
  );

  // Friction #5: Loading skeleton
  const skeleton = () => (
    <div className={styles.ewSkeleton}>
      <div className={styles.ewSkeletonBar} style={{ height: 8, width: '80%', marginBottom: 8 }} />
      <div className={styles.ewSkeletonBarNarrow} style={{ width: '100%' }} />
      <div className={styles.ewSkeletonBar} style={{ height: 8, width: '60%', marginBottom: 8 }} />
      <div className={styles.ewSkeletonBarNarrow} style={{ width: '100%' }} />
    </div>
  );

  return (
    <div style={{ paddingTop: 4 }}>
      <div style={{ fontSize: '0.68rem', color: '#475569', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
        🔬 Active System Engines
      </div>

      {/* ── Biodiversity ── */}
      <div className={styles.ewCard}>
        <div className={styles.ewHeader} style={{ background: 'rgba(16,185,129,0.08)', borderBottom: '1px solid rgba(16,185,129,0.15)' }} onClick={() => toggle('bio')}>
          <span className={styles.ewLabel} style={{ color: '#34d399' }}>🌿 Biodiversity</span>
          <span className={styles.ewChevron}>{open.bio ? '▲' : '▼'}</span>
        </div>
        {open.bio && (bio ? (
          <div className={styles.ewBody}>
            <Pill label="Ecosystem Health Index" value={`${(bio.ehi ?? bio.ecosystem_health_index ?? 0).toFixed(1)} / 100`} good={(bio.ehi ?? bio.ecosystem_health_index ?? 0) >= 60} />
            <Bar value={bio.ehi ?? bio.ecosystem_health_index ?? 0} color="#34d399" />
            <Pill label="Deforestation Risk" value={(bio.deforestation_risk ?? 'Low')} good={(bio.deforestation_risk ?? 'Low') === 'Low'} />
            <Pill label="Water Stress Index" value={`${(bio.water_stress_index ?? 0).toFixed(1)}`} good={(bio.water_stress_index ?? 0) < 50} />
            {bio.tnfd_flags?.length > 0 && (
              <div style={{ marginTop: 6 }}>
                <div style={{ fontSize: '0.6rem', color: '#64748b', marginBottom: 3 }}>TNFD Flags:</div>
                {bio.tnfd_flags.map((f, i) => (
                  <div key={i} style={{ fontSize: '0.65rem', color: '#fbbf24', marginBottom: 2 }}>⚠ {f}</div>
                ))}
              </div>
            )}
          </div>
        ) : (!enginesLoaded ? skeleton() : noEngine('Biodiversity')))}
      </div>

      {/* ── Board Governance ── */}
      <div className={styles.ewCard}>
        <div className={styles.ewHeader} style={{ background: 'rgba(99,102,241,0.08)', borderBottom: '1px solid rgba(99,102,241,0.15)' }} onClick={() => toggle('board')}>
          <span className={styles.ewLabel} style={{ color: '#818cf8' }}>🏛️ Board Governance</span>
          <span className={styles.ewChevron}>{open.board ? '▲' : '▼'}</span>
        </div>
        {open.board && (board ? (
          <div className={styles.ewBody}>
            <Pill label="ESG Alignment Score" value={`${(board.esg_alignment_score ?? board.board_esg_score ?? 0).toFixed(1)} / 100`} good={(board.esg_alignment_score ?? board.board_esg_score ?? 0) >= 60} />
            <Bar value={board.esg_alignment_score ?? board.board_esg_score ?? 0} color="#818cf8" />
            <Pill label="Board Confidence" value={`${(board.board_confidence ?? 0).toFixed(1)}%`} good={(board.board_confidence ?? 0) >= 60} />
            {board.resolution_outcome && (
              <div style={{ marginTop: 6, padding: '5px 8px', borderRadius: 5, background: 'rgba(99,102,241,0.1)', fontSize: '0.65rem', color: '#a5b4fc' }}>
                📋 Last Resolution: {board.resolution_outcome}
              </div>
            )}
          </div>
        ) : (!enginesLoaded ? skeleton() : noEngine('Board Governance')))}
      </div>

      {/* ── Supply Chain ── */}
      <div className={styles.ewCard}>
        <div className={styles.ewHeader} style={{ background: 'rgba(245,158,11,0.08)', borderBottom: '1px solid rgba(245,158,11,0.15)' }} onClick={() => toggle('supply')}>
          <span className={styles.ewLabel} style={{ color: '#fbbf24' }}>🔗 Supply Chain</span>
          <span className={styles.ewChevron}>{open.supply ? '▲' : '▼'}</span>
        </div>
        {open.supply && (supply ? (
          <div className={styles.ewBody}>
            <Pill label="Scope 3 Completeness" value={`${(supply.scope3_completeness ?? supply.data_completeness ?? 0).toFixed(0)}%`} good={(supply.scope3_completeness ?? supply.data_completeness ?? 0) >= 60} />
            <Bar value={supply.scope3_completeness ?? supply.data_completeness ?? 0} color="#fbbf24" />
            <Pill label="Tier 1 Compliance" value={`${(supply.tier1_compliance ?? 0).toFixed(0)}%`} good={(supply.tier1_compliance ?? 0) >= 70} />
            <Pill label="Risk Exposure" value={supply.risk_level ?? 'Moderate'} good={(supply.risk_level ?? '') === 'Low'} />
            {supply.disruption_events?.length > 0 && (
              <div style={{ marginTop: 6, fontSize: '0.68rem', color: '#ef4444' }}>
                ⚡ {supply.disruption_events[0]}
              </div>
            )}
          </div>
        ) : (!enginesLoaded ? skeleton() : noEngine('Supply Chain')))}
      </div>

      {/* ── Balance Sheet (CL-2: Compact summary + modal for full IFRS view) ── */}
      <div className={styles.ewCard}>
        <div className={styles.ewHeader} style={{ background: 'rgba(56,189,248,0.08)', borderBottom: '1px solid rgba(56,189,248,0.15)' }} onClick={() => toggle('bs')}>
          <span className={styles.ewLabel} style={{ color: '#38bdf8' }}>📊 Balance Sheet</span>
          <span className={styles.ewChevron}>{open.bs ? '▲' : '▼'}</span>
        </div>
        {open.bs && (balanceSheet ? (() => {
          const fmtM = (v) => `$${((v || 0) / 1_000_000).toFixed(1)}M`;
          const totalAssets = balanceSheet.total_assets || 0;
          const totalLiabilities = balanceSheet.total_liabilities || 0;
          const netAssets = balanceSheet.net_assets || 0;
          const deRatio = balanceSheet.debt_to_equity || 0;
          const covenantStatus = balanceSheet.covenant_status || 'green';
          const covenantColors = { green: '#10b981', amber: '#f59e0b', red: '#ef4444', breached: '#dc2626' };
          return (
            <div className={styles.ewBody}>
              {/* Compact 3-line summary */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-secondary, #94a3b8)' }}>Assets</span>
                  <span style={{ fontWeight: 800, fontFamily: "'JetBrains Mono', monospace", color: '#38bdf8' }}>{fmtM(totalAssets)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-secondary, #94a3b8)' }}>Liabilities</span>
                  <span style={{ fontWeight: 800, fontFamily: "'JetBrains Mono', monospace", color: '#f87171' }}>{fmtM(totalLiabilities)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', borderTop: '1px solid rgba(148,163,184,0.15)', paddingTop: 3 }}>
                  <span style={{ fontWeight: 700, color: 'var(--text-primary, #e2e8f0)' }}>Net Assets</span>
                  <span style={{ fontWeight: 800, fontFamily: "'JetBrains Mono', monospace", color: netAssets >= 0 ? '#4ade80' : '#ef4444' }}>{fmtM(netAssets)}</span>
                </div>
              </div>
              {/* Quick ratio pills */}
              <div style={{ display: 'flex', gap: 4, marginTop: 6, flexWrap: 'wrap' }}>
                <Pill label="D/E" value={`${deRatio.toFixed(1)}×`} good={deRatio < 2.0} />
                <span style={{ fontSize: '0.6rem', fontWeight: 700, color: covenantColors[covenantStatus], padding: '2px 6px', borderRadius: 4, background: `${covenantColors[covenantStatus]}15`, border: `1px solid ${covenantColors[covenantStatus]}25` }}>
                  {covenantStatus === 'green' ? '🟢' : covenantStatus === 'amber' ? '🟡' : '🔴'} Covenant
                </span>
              </div>
              {/* Open full modal button */}
              <button
                onClick={() => setBsModalOpen(true)}
                style={{
                  marginTop: 8, width: '100%', padding: '5px 0', borderRadius: 5,
                  background: 'rgba(56,189,248,0.08)', border: '1px solid rgba(56,189,248,0.2)',
                  color: '#38bdf8', fontSize: '0.65rem', fontWeight: 700, cursor: 'pointer',
                  fontFamily: "'DM Sans', sans-serif", letterSpacing: '0.04em',
                  transition: 'background 0.15s',
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(56,189,248,0.15)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'rgba(56,189,248,0.08)'}
              >
                📊 View Full Statement →
              </button>
            </div>
          );
        })() : (!enginesLoaded ? skeleton() : noEngine('Balance Sheet')))}
      </div>

      {/* CL-2: Balance Sheet Full Modal */}
      <BalanceSheetModal
        balanceSheet={balanceSheet}
        isOpen={bsModalOpen}
        onClose={() => setBsModalOpen(false)}
      />
    </div>
  );
}
