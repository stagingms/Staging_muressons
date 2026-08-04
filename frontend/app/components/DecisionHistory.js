import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { money } from '../utils/format';

const fmtCurrency = (v) => {
  return money(v);
};

const DeltaBadge = ({ value, invert = false, suffix = '' }) => {
  if (value === 0 || value === undefined) return null;
  const isGood = invert ? value < 0 : value > 0;
  return (
    <span style={{
      fontSize: '0.6rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4,
      background: isGood ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
      color: isGood ? '#059669' : '#dc2626',
      whiteSpace: 'nowrap',
    }}>
      {value > 0 ? '▲' : '▼'} {typeof value === 'number' && Math.abs(value) >= 1000
        ? fmtCurrency(Math.abs(value))
        : Math.abs(value).toFixed(0)}{suffix}
    </span>
  );
};

export default function DecisionHistory({ historyData }) {
  const [openRound, setOpenRound] = useState(null);

  if (!historyData || historyData.length === 0) {
    return (
      <div style={{
        textAlign: 'center', padding: '2rem 1rem',
        color: '#94a3b8', fontSize: '0.75rem',
      }}>
        <div style={{ fontSize: '1.5rem', marginBottom: 6 }}>📜</div>
        No decisions recorded yet.<br />
        Complete your first round to see results here.
      </div>
    );
  }

  // Only show completed rounds (those that have previous data or are not the latest)
  const completedRounds = historyData.filter((h, i) => i < historyData.length - 1 || h.previous_ebitda !== undefined);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {completedRounds.slice().reverse().map((h) => {
        const isOpen = openRound === h.round;
        const dTreasury = h.treasury - (h.previous_treasury || 0);
        const dEbitda = h.ebitda - (h.previous_ebitda || 0);
        const dReputation = h.reputation - (h.previous_reputation || 50);
        const dCO2 = h.tco2e - (h.previous_tco2e || 0);

        return (
          <div key={h.round}>
            {/* Accordion Header */}
            <button
              onClick={() => setOpenRound(isOpen ? null : h.round)}
              style={{
                width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '8px 10px', cursor: 'pointer', border: 'none',
                background: isOpen ? 'rgba(99,102,241,0.08)' : '#f8fafc',
                borderLeft: `3px solid ${isOpen ? '#6366f1' : '#cbd5e1'}`,
                borderRadius: '0 6px 6px 0',
                transition: 'background 0.15s ease, color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease, transform 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#1e293b' }}>
                  Round {h.round}
                </span>
                <DeltaBadge value={dEbitda} />
              </div>
              <span style={{ fontSize: '0.6rem', color: '#94a3b8', transition: 'transform 0.2s', transform: isOpen ? 'rotate(180deg)' : 'rotate(0)' }}>▼</span>
            </button>

            {/* Accordion Content */}
            <AnimatePresence>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  style={{ overflow: 'hidden' }}
                >
                  <div style={{
                    padding: '8px 10px', background: '#f1f5f9',
                    borderLeft: '3px solid #6366f1', borderRadius: '0 0 6px 0',
                    fontSize: '0.65rem', lineHeight: 1.6,
                  }}>
                    {/* KPI Grid */}
                    <div style={{
                      display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 12px',
                      marginBottom: 8,
                    }}>
                      <div>
                        <div style={{ color: '#64748b', fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Treasury</div>
                        <div style={{ fontWeight: 700, color: '#1e293b', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.68rem' }}>
                          {fmtCurrency(h.treasury)} <DeltaBadge value={dTreasury} />
                        </div>
                      </div>
                      <div>
                        <div style={{ color: '#64748b', fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>EBITDA</div>
                        <div style={{ fontWeight: 700, color: '#1e293b', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.68rem' }}>
                          {fmtCurrency(h.ebitda)} <DeltaBadge value={dEbitda} />
                        </div>
                      </div>
                      <div>
                        <div style={{ color: '#64748b', fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Reputation</div>
                        <div style={{ fontWeight: 700, color: '#1e293b', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.68rem' }}>
                          {h.reputation.toFixed(0)}/100 <DeltaBadge value={dReputation} />
                        </div>
                      </div>
                      <div>
                        <div style={{ color: '#64748b', fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>CO₂</div>
                        <div style={{ fontWeight: 700, color: '#1e293b', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.68rem' }}>
                          {h.tco2e.toLocaleString()}t <DeltaBadge value={dCO2} invert />
                        </div>
                      </div>
                    </div>

                    {/* Synergy */}
                    {h.synergy && h.synergy !== 1.0 && (
                      <div style={{
                        padding: '4px 8px', background: 'rgba(99,102,241,0.06)', borderRadius: 4,
                        marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      }}>
                        <span style={{ color: '#475569', fontSize: '0.68rem', fontWeight: 600 }}>Synergy Multiplier</span>
                        <span style={{ color: '#6366f1', fontWeight: 800, fontSize: '0.65rem' }}>{h.synergy.toFixed(2)}×</span>
                      </div>
                    )}

                    {/* Business Units */}
                    {h.bu_count > 0 && (
                      <div style={{
                        fontSize: '0.68rem', color: '#64748b',
                        padding: '3px 0', borderTop: '1px solid #e2e8f0', marginTop: 4,
                      }}>
                        {h.bu_count} business unit{h.bu_count !== 1 ? 's' : ''} managed
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}
