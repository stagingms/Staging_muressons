'use client';
import Dialog from './Dialog';
import { useState, useMemo } from 'react';

/**
 * AchievementBadges — Achievement/badge system that unlocks based on game state.
 * Improvement #5.1: Achievement System
 */

const ACHIEVEMENTS = [
  { id: 'esg_pioneer', icon: '🏆', title: 'ESG Pioneer', desc: 'Score above 60 in reputation', check: (gs) => (gs?.group_reputation || 0) >= 60 },
  { id: 'treasury_guard', icon: '💎', title: 'Treasury Guardian', desc: 'Maintain treasury above $40M', check: (gs) => (gs?.corporate_treasury || 0) >= 40_000_000 },
  { id: 'carbon_champ', icon: '🌱', title: 'Carbon Champion', desc: 'Emissions below 2,000t', check: (gs) => (gs?.tco2e_emissions || 9999) < 2000 },
  { id: 'stakeholder_pro', icon: '🤝', title: 'Stakeholder Pro', desc: 'Complete stakeholder map with 70%+ accuracy', check: (gs) => (gs?.stakeholder_map_accuracy || 0) >= 70 },
  { id: 'multi_round', icon: '🎮', title: 'Persistent Leader', desc: 'Reach Round 5', check: (gs, rn) => rn >= 5 },
  { id: 'veteran', icon: '⭐', title: 'Simulation Veteran', desc: 'Reach Round 8', check: (gs, rn) => rn >= 8 },
  { id: 'balanced', icon: '⚖️', title: 'Balanced Strategist', desc: 'Treasury > $30M AND Reputation > 50', check: (gs) => (gs?.corporate_treasury || 0) > 30_000_000 && (gs?.group_reputation || 0) > 50 },
  { id: 'survivor', icon: '🛡️', title: 'Crisis Survivor', desc: 'Navigate through 3+ crises', check: (gs, rn) => rn >= 4 },
];

export default function AchievementBadges({ globalState, roundNumber, isOpen, onClose }) {
  const unlocked = useMemo(() =>
    ACHIEVEMENTS.filter(a => a.check(globalState, roundNumber)),
    [globalState, roundNumber]
  );

  const locked = useMemo(() =>
    ACHIEVEMENTS.filter(a => !a.check(globalState, roundNumber)),
    [globalState, roundNumber]
  );

  if (!isOpen) return null;

  return (
    /* PHASE 8: a scrim div + a stopPropagation panel div = two click targets
       no keyboard could reach, on a modal with no role, no trap and no focus
       restore. Dialog owns all of it; the panel's stopPropagation is redundant
       because Dialog's backdrop handler tests target === currentTarget. */
    <Dialog
      onClose={onClose}
      label="Achievements"
      style={{
        position: 'fixed', inset: 0, zIndex: 12000,
        background: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: 'Inter, sans-serif',
      }}
    >
      <div style={{
        background: '#fff', borderRadius: 16, width: '90%', maxWidth: 500,
        maxHeight: '80vh', overflow: 'auto',
        boxShadow: '0 25px 60px rgba(0,0,0,0.2)', padding: '1.5rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: '#0f172a' }}>
            🏅 Achievements
            <span style={{
              fontSize: 'var(--type-caption)', fontWeight: 700, background: '#f0fdf4',
              color: '#16a34a', padding: '2px 8px', borderRadius: 10, marginLeft: 8,
            }}>{unlocked.length}/{ACHIEVEMENTS.length}</span>
          </h2>
          <button onClick={onClose} style={{
            background: '#f1f5f9', border: 'none', borderRadius: '50%',
            width: 28, height: 28, cursor: 'pointer', fontSize: '0.85rem',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#64748b', fontWeight: 700,
          }}>✕</button>
        </div>

        {/* Unlocked */}
        {unlocked.length > 0 && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: '#16a34a', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              🎉 Unlocked
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {unlocked.map(a => (
                <div key={a.id} style={{
                  padding: '0.6rem', borderRadius: 10,
                  background: 'linear-gradient(135deg, #f0fdf4, #ecfdf5)',
                  border: '1px solid #bbf7d0',
                }}>
                  <div style={{ fontSize: '1.5rem', marginBottom: 4 }}>{a.icon}</div>
                  <div style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: '#0f172a' }}>{a.title}</div>
                  <div style={{ fontSize: 'var(--type-caption)', color: '#16a34a' }}>{a.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Locked */}
        {locked.length > 0 && (
          <div>
            <div style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              🔒 Locked
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {locked.map(a => (
                <div key={a.id} style={{
                  padding: '0.6rem', borderRadius: 10,
                  background: '#f8fafc', border: '1px solid #e2e8f0',
                  opacity: 0.6,
                }}>
                  <div style={{ fontSize: '1.5rem', marginBottom: 4, filter: 'grayscale(1)' }}>{a.icon}</div>
                  <div style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: '#64748b' }}>{a.title}</div>
                  <div style={{ fontSize: 'var(--type-caption)', color: '#94a3b8' }}>{a.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Dialog>
  );
}
