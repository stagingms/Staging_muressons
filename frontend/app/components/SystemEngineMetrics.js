import React from 'react';
import { useCurrency } from '../contexts/CurrencyContext';
import styles from './ExecutiveCockpit.module.css';

export default function SystemEngineMetrics({ globalState, pedToggles, isHealthcare }) {
  const { currency } = useCurrency();
  const sym = currency?.symbol || '$';

  const fmtCurrency = (v) => {
    if (v === undefined || v === null || isNaN(v)) return `${sym}0`;
    if (v === 0) return `${sym}0`;
    const abs = Math.abs(v);
    if (abs >= 1_000_000) return `${v < 0 ? '-' : ''}${sym}${(abs / 1_000_000).toFixed(1)}M`;
    if (abs >= 1_000) return `${v < 0 ? '-' : ''}${sym}${(abs / 1_000).toFixed(0)}K`;
    return `${v < 0 ? '-' : ''}${sym}${abs.toFixed(0)}`;
  };

  const widgets = [];

  // 1. Biodiversity Engine (SE-4)
  if (pedToggles?.biodiversity_engine_enabled && globalState?.biodiversity_state) {
    const bio = globalState.biodiversity_state;
    widgets.push(
      <div key="biodiversity" style={{ padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: `1px solid ${bio.ecosystem_health_index < 40 ? 'rgba(239,68,68,0.4)' : bio.ecosystem_health_index < 60 ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.2)'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <span style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>🌿 Ecosystem Health</span>
          <span style={{ fontSize: '0.75rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: bio.ecosystem_health_index < 40 ? '#f87171' : bio.ecosystem_health_index < 60 ? '#fbbf24' : '#4ade80' }}>
            {bio.ecosystem_health_index.toFixed(1)}
          </span>
        </div>
        <div style={{ height: 3, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden', marginBottom: 4 }}>
          <div style={{ height: '100%', width: `${bio.ecosystem_health_index}%`, background: bio.ecosystem_health_index < 40 ? '#ef4444' : bio.ecosystem_health_index < 60 ? '#f59e0b' : '#10b981', borderRadius: 2, transition: 'width 0.5s' }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#64748b' }}>
          <span>Risk: {bio.species_risk_score} Spp</span>
          <span>ESV: {fmtCurrency(bio.ecosystem_services_value)}/yr</span>
        </div>
      </div>
    );
  }

  // 2. Supply Chain Network (SE-2)
  if (pedToggles?.supply_chain_network_enabled && globalState?.supply_chain_state) {
    const sc = globalState.supply_chain_state;
    widgets.push(
      <div key="supply_chain" style={{ padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: `1px solid ${sc.network_resilience_score < 40 ? 'rgba(239,68,68,0.4)' : sc.network_resilience_score < 70 ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.2)'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <span style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>🔗 Supply Chain Resilience</span>
          <span style={{ fontSize: '0.75rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: sc.network_resilience_score < 40 ? '#f87171' : sc.network_resilience_score < 70 ? '#fbbf24' : '#4ade80' }}>
            {sc.network_resilience_score.toFixed(1)}
          </span>
        </div>
        <div style={{ height: 3, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden', marginBottom: 4 }}>
          <div style={{ height: '100%', width: `${sc.network_resilience_score}%`, background: sc.network_resilience_score < 40 ? '#ef4444' : sc.network_resilience_score < 70 ? '#f59e0b' : '#10b981', borderRadius: 2, transition: 'width 0.5s' }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#64748b' }}>
          <span>Risk Exp: {sc.csddd_risk_exposure.toFixed(1)}</span>
          <span>Vis: {sc.tier_visibility_depth.toFixed(1)} Tiers</span>
        </div>
      </div>
    );
  }

  // 3. Board Governance (SE-1)
  if (pedToggles?.board_governance_enabled && globalState?.board_governance_state) {
    const bg = globalState.board_governance_state;
    widgets.push(
      <div key="board_governance" style={{ padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: `1px solid ${bg.board_confidence_score < 40 ? 'rgba(239,68,68,0.4)' : bg.board_confidence_score < 70 ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.2)'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <span style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>🏛️ Board Confidence</span>
          <span style={{ fontSize: '0.75rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: bg.board_confidence_score < 40 ? '#f87171' : bg.board_confidence_score < 70 ? '#fbbf24' : '#4ade80' }}>
            {bg.board_confidence_score.toFixed(1)}
          </span>
        </div>
        <div style={{ height: 3, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden', marginBottom: 4 }}>
          <div style={{ height: '100%', width: `${bg.board_confidence_score}%`, background: bg.board_confidence_score < 40 ? '#ef4444' : bg.board_confidence_score < 70 ? '#f59e0b' : '#10b981', borderRadius: 2, transition: 'width 0.5s' }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#64748b' }}>
          <span>ESG Focus: {(bg.esg_competency_index * 100).toFixed(0)}%</span>
          <span>Revolt Risk: {(bg.activist_pressure_level * 100).toFixed(0)}%</span>
        </div>
      </div>
    );
  }

  if (widgets.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {widgets}
    </div>
  );
}
