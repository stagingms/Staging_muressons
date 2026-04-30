'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * StochasticDiceRoll — Phase 3.5
 * Animated dice roll visualization for R5 climate damage.
 * Shows the probability threshold visually so students SEE the
 * randomness they are exposed to.
 *
 * Props:
 *   - probability:   number (0-1), e.g. 0.75 for 75% chance
 *   - outcome:       boolean — did the damage happen?
 *   - damageAmount:  number — dollar damage dealt
 *   - fmtCurrency:   formatter function
 *   - onDismiss:     callback when animation completes
 */

export default function StochasticDiceRoll({
  probability = 0.75,
  outcome = true,
  damageAmount = 12000000,
  fmtCurrency = (v) => `$${(v / 1e6).toFixed(1)}M`,
  onDismiss,
}) {
  const [phase, setPhase] = useState('rolling'); // rolling → revealing → done
  const [displayNumber, setDisplayNumber] = useState(0);

  // Animate dice rolling
  useEffect(() => {
    if (phase !== 'rolling') return;
    const rollDuration = 2000;
    const interval = 50;
    const startTime = Date.now();

    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      if (elapsed >= rollDuration) {
        clearInterval(timer);
        // Final number: outcome determines if it lands in the danger zone
        const finalNum = outcome
          ? Math.floor(Math.random() * (probability * 100)) + 1  // 1 to threshold
          : Math.floor(Math.random() * ((1 - probability) * 100)) + Math.floor(probability * 100) + 1; // above threshold
        setDisplayNumber(Math.min(100, Math.max(1, finalNum)));
        setPhase('revealing');
        setTimeout(() => setPhase('done'), 2500);
        return;
      }
      // Random flicker during roll
      setDisplayNumber(Math.floor(Math.random() * 100) + 1);
    }, interval);

    return () => clearInterval(timer);
  }, [phase, outcome, probability]);

  const thresholdPct = probability * 100;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(14, 20, 36, 0.95), rgba(30, 41, 59, 0.95))',
          border: outcome
            ? '2px solid rgba(239, 68, 68, 0.4)'
            : '2px solid rgba(16, 185, 129, 0.4)',
          borderRadius: 16,
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Title */}
        <div style={{
          fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase',
          letterSpacing: '0.12em', color: '#94a3b8', marginBottom: 12,
        }}>
          🎲 STOCHASTIC CLIMATE EVENT
        </div>

        {/* Dice Display */}
        <motion.div
          key={displayNumber}
          initial={phase === 'rolling' ? { rotateX: 0 } : { scale: 1.2 }}
          animate={phase === 'rolling' ? { rotateX: 360 } : { scale: 1 }}
          transition={{ duration: phase === 'rolling' ? 0.05 : 0.3 }}
          style={{
            fontSize: '3rem',
            fontWeight: 900,
            fontFamily: "'JetBrains Mono', monospace",
            color: phase === 'revealing' || phase === 'done'
              ? (outcome ? '#ef4444' : '#10b981')
              : '#e2e8f0',
            margin: '8px 0',
          }}
        >
          {displayNumber}
        </motion.div>

        {/* Probability Bar */}
        <div style={{ margin: '16px 0', position: 'relative' }}>
          <div style={{
            height: 24, borderRadius: 12,
            background: '#1e293b', overflow: 'hidden',
            position: 'relative',
          }}>
            {/* Danger Zone */}
            <div style={{
              position: 'absolute', left: 0, top: 0, bottom: 0,
              width: `${thresholdPct}%`,
              background: 'linear-gradient(90deg, rgba(239, 68, 68, 0.3), rgba(239, 68, 68, 0.15))',
              borderRight: '2px solid rgba(239, 68, 68, 0.6)',
            }} />
            {/* Safe Zone */}
            <div style={{
              position: 'absolute', right: 0, top: 0, bottom: 0,
              width: `${100 - thresholdPct}%`,
              background: 'linear-gradient(90deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.3))',
            }} />
            {/* Marker for result */}
            {(phase === 'revealing' || phase === 'done') && (
              <motion.div
                initial={{ left: '50%', opacity: 0 }}
                animate={{ left: `${displayNumber}%`, opacity: 1 }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                style={{
                  position: 'absolute', top: -4, bottom: -4,
                  width: 4, borderRadius: 2,
                  background: outcome ? '#ef4444' : '#10b981',
                  boxShadow: `0 0 12px ${outcome ? 'rgba(239,68,68,0.6)' : 'rgba(16,185,129,0.6)'}`,
                }}
              />
            )}
          </div>
          {/* Labels */}
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            marginTop: 4, fontSize: '0.7rem', fontWeight: 600,
          }}>
            <span style={{ color: '#f87171' }}>⚠️ Damage ({thresholdPct.toFixed(0)}%)</span>
            <span style={{ color: '#4ade80' }}>✓ Safe ({(100 - thresholdPct).toFixed(0)}%)</span>
          </div>
        </div>

        {/* Outcome */}
        {(phase === 'revealing' || phase === 'done') && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            style={{
              padding: '12px 16px', borderRadius: 10, marginTop: 8,
              background: outcome
                ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
              border: `1px solid ${outcome
                ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.25)'}`,
            }}
          >
            <div style={{
              fontSize: '1rem', fontWeight: 800,
              color: outcome ? '#f87171' : '#4ade80',
              marginBottom: 4,
            }}>
              {outcome ? '🌪️ CYCLONE HITS' : '🌤️ CYCLONE MISSES'}
            </div>
            <div style={{
              fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.5,
            }}>
              {outcome
                ? `Your roll of ${displayNumber} fell within the ${thresholdPct.toFixed(0)}% danger zone. Infrastructure damage: ${fmtCurrency(damageAmount)}`
                : `Your roll of ${displayNumber} fell in the safe ${(100 - thresholdPct).toFixed(0)}% zone. No damage this round.`
              }
            </div>
            <div style={{
              fontSize: '0.72rem', color: '#64748b', marginTop: 6, fontStyle: 'italic',
            }}>
              Your infrastructure investment protects against FUTURE events, not this one (2-round construction delay).
            </div>
          </motion.div>
        )}

        {/* Dismiss */}
        {phase === 'done' && onDismiss && (
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            onClick={onDismiss}
            style={{
              marginTop: 12, padding: '8px 20px',
              background: 'rgba(99, 102, 241, 0.15)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: 8, color: '#a5b4fc',
              fontSize: '0.78rem', fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Continue →
          </motion.button>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
