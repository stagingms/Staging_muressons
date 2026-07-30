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

  // BUG-2026-07-30: these three panels showed 0 for every metric, forever.
  //
  //   a) EVERY endpoint wraps its payload — /biodiversity returns
  //      {biodiversity:{...}}, /board-governance returns {board_governance:{...}},
  //      /supply-chain returns {supply_chain:{...}} — but we stored the wrapper
  //      and then read fields off IT, so every lookup was undefined and the
  //      `?? 0` fallbacks rendered 0.0 / 0%. (balance-sheet already unwrapped
  //      correctly, which is why that panel worked and these did not.)
  //   b) The deps were [sessionId] only, so this ran ONCE on mount and never
  //      again. Even correct values would have frozen at the round the player
  //      happened to load on — which is what "not changing after round 2"
  //      looked like from the outside.
  //
  // Unwrap here, once, so every reader below sees the real engine object.
  const roundNumber = globalState?.round_number;
  useEffect(() => {
    if (!sessionId) return;
    const pick = (d, key) => (d && typeof d === 'object' && d[key]) ? d[key] : d;
    fetch(`${API}/api/simulations/${sessionId}/biodiversity`)
      .then(r => r.ok ? r.json() : null).then(d => d && setBio(pick(d, 'biodiversity'))).catch(() => {});
    fetch(`${API}/api/simulations/${sessionId}/board-governance`)
      .then(r => r.ok ? r.json() : null).then(d => d && setBoard(pick(d, 'board_governance'))).catch(() => {});
    fetch(`${API}/api/simulations/${sessionId}/supply-chain`)
      .then(r => r.ok ? r.json() : null).then(d => d && setSupply(pick(d, 'supply_chain'))).catch(() => {});
    fetch(`${API}/api/simulations/${sessionId}/balance-sheet`)
      .then(r => r.ok ? r.json() : null).then(d => d && setBalanceSheet(d.balance_sheet || d)).catch(() => {});
    const t = setTimeout(() => setEnginesLoaded(true), 600);
    return () => clearTimeout(t);
    // roundNumber in the deps is what makes these panels advance with the game.
  }, [sessionId, roundNumber]);

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
            {/* Real emitted fields (see the unwrap note above): ehi/deforestation_risk
                never existed. water_stress_index and habitat_integrity are 0-1 ratios,
                so they are scaled here rather than printed raw as "0.4". */}
            <Pill label="Ecosystem Health Index" value={`${(bio.ecosystem_health_index ?? 0).toFixed(1)} / 100`} good={(bio.ecosystem_health_index ?? 0) >= 60} />
            <Bar value={bio.ecosystem_health_index ?? 0} color="#34d399" />
            <Pill label="Habitat Integrity" value={`${((bio.habitat_integrity ?? 0) * 100).toFixed(0)}%`} good={(bio.habitat_integrity ?? 0) >= 0.6} />
            <Pill label="Deforestation Rate" value={`${(bio.deforestation_rate ?? 0).toFixed(1)}%`} good={(bio.deforestation_rate ?? 0) < 2} />
            <Pill label="Water Stress" value={`${((bio.water_stress_index ?? 0) * 100).toFixed(0)}%`} good={(bio.water_stress_index ?? 0) < 0.5} />
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
            {/* esg_alignment_score / board_confidence are not emitted by the
                engine. These are the real computed fields: avg_esg_alignment is
                the mean over the director roster (0-1), board_effectiveness_score
                is already 0-100. Labels match what is actually measured. */}
            <Pill label="Board Effectiveness" value={`${(board.board_effectiveness_score ?? 0).toFixed(1)} / 100`} good={(board.board_effectiveness_score ?? 0) >= 60} />
            <Bar value={board.board_effectiveness_score ?? 0} color="#818cf8" />
            <Pill label="Board ESG Alignment" value={`${((board.avg_esg_alignment ?? 0) * 100).toFixed(0)}%`} good={(board.avg_esg_alignment ?? 0) >= 0.6} />
            <Pill label="Independent Directors" value={`${((board.independence_ratio ?? 0) * 100).toFixed(0)}%`} good={(board.independence_ratio ?? 0) >= 0.5} />
            <Pill label="Say-on-Pay Approval" value={`${(board.say_on_pay_approval ?? 0).toFixed(0)}%`} good={(board.say_on_pay_approval ?? 0) >= 70} />
            {/* The board only shifts when its COMPOSITION shifts, so a static
                reading is the engine working, not a stuck panel. Say so. */}
            <div style={{ marginTop: 6, fontSize: '0.6rem', color: '#64748b', lineHeight: 1.4 }}>
              Board ESG alignment moves when board composition changes — activist
              nominees seated, or directors replaced.
            </div>
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
            {/* scope3_completeness / tier1_compliance / risk_level are not
                emitted. overall_visibility is a 0-1 mean across all tiers and is
                the honest proxy for how much of the chain the company can SEE;
                Tier-1 compliance is derived from the per-supplier
                compliance_status the engine really maintains. */}
            <Pill label="Supply Chain Visibility" value={`${((supply.overall_visibility ?? 0) * 100).toFixed(0)}%`} good={(supply.overall_visibility ?? 0) >= 0.6} />
            <Bar value={(supply.overall_visibility ?? 0) * 100} color="#fbbf24" />
            {(() => {
              const t1 = supply.tier_1_suppliers || [];
              const audited = t1.filter(x => x?.compliance_status === 'audited').length;
              const pct = t1.length ? (audited / t1.length) * 100 : 0;
              return (
                <Pill label="Tier 1 Audited"
                      value={t1.length ? `${pct.toFixed(0)}% (${audited}/${t1.length})` : '—'}
                      good={pct >= 70} />
              );
            })()}
            <Pill label="Supply Chain Risk" value={`${(supply.overall_risk ?? 0).toFixed(1)} / 100`} good={(supply.overall_risk ?? 100) < 40} />
            <Pill label="Scope 3 Estimate" value={`${((supply.scope_3_estimate ?? 0) / 1000).toFixed(1)}k tCO₂e`} good={false} />
            {/* Visibility only rises when the player pays for an audit — the
                intended lesson (disclosure costs money). A static reading here
                means nobody has audited yet, not that the panel is broken. */}
            <div style={{ marginTop: 6, fontSize: '0.6rem', color: '#64748b', lineHeight: 1.4 }}>
              Visibility rises only when you commission a supply-chain audit —
              deeper tiers cost more.
            </div>
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
