/**
 * BoardroomDebate — WOW-9
 *
 * Enhanced version of the Round 5 Shadow Board experience. Instead of static
 * text cards, renders three director "portraits" as animated character cards
 * with gradient avatars, dramatic entry animations, and a slide-out exit
 * animation when a director is rejected.
 *
 * SAFETY: Pure presentation enhancement. Uses the SAME data from the existing
 * shadow-board-audit API. Does NOT modify any backend logic, flag setting,
 * or game state. The existing ShadowBoardAudit component handles all logic —
 * this component is mounted INSIDE it as an enhanced UI layer.
 *
 * Props:
 *   personas     — array of persona objects from GET /shadow-board-audit
 *   selectedTarget — currently selected rejection target (persona_id)
 *   onSelect     — callback(persona_id) when a director is selected for rejection
 *   rejectedId   — the persona_id that was confirmed rejected (null until confirmed)
 *   globalState  — for contextual detail in arguments
 */
'use client';
import React, { useState, useEffect, useMemo } from 'react';
import styles from './BoardroomDebate.module.css';

/** Director avatar gradients and character styling */
const DIRECTOR_THEME = {
  shareholder: {
    gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
    bgGlow: 'rgba(245, 158, 11, 0.08)',
    borderColor: 'rgba(245, 158, 11, 0.3)',
    icon: '📈',
    stance: 'Protect shareholder returns',
  },
  activist: {
    gradient: 'linear-gradient(135deg, #10b981, #059669)',
    bgGlow: 'rgba(16, 185, 129, 0.08)',
    borderColor: 'rgba(16, 185, 129, 0.3)',
    icon: '🌿',
    stance: 'Prioritize planet and community',
  },
  auditor: {
    gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)',
    bgGlow: 'rgba(99, 102, 241, 0.08)',
    borderColor: 'rgba(99, 102, 241, 0.3)',
    icon: '🏛️',
    stance: 'Maximize physical risk protection',
  },
};

const FALLBACK_THEME = {
  gradient: 'linear-gradient(135deg, #64748b, #475569)',
  bgGlow: 'rgba(100, 116, 139, 0.08)',
  borderColor: 'rgba(100, 116, 139, 0.3)',
  icon: '👤',
  stance: 'Advisory position',
};

/** Staggered entry delay per card */
const ENTRY_DELAY_MS = 300;

export default function BoardroomDebate({
  personas = [],
  selectedTarget,
  onSelect,
  rejectedId,
  globalState,
}) {
  // Track which cards have entered (for staggered animation)
  const [enteredCards, setEnteredCards] = useState(new Set());

  useEffect(() => {
    if (!personas.length) return;
    const timers = personas.map((p, i) =>
      setTimeout(() => {
        setEnteredCards(prev => new Set([...prev, p.persona_id]));
      }, ENTRY_DELAY_MS * (i + 1))
    );
    return () => timers.forEach(clearTimeout);
  }, [personas]);

  if (!personas.length) return null;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerIcon}>🏛️</div>
        <div className={styles.headerTitle}>The Boardroom</div>
        <div className={styles.headerSubtitle}>
          Three directors have conflicting recommendations. You must reject one to proceed.
        </div>
      </div>

      <div className={styles.directorGrid}>
        {personas.map((persona, i) => {
          const theme = DIRECTOR_THEME[persona.persona_id] || FALLBACK_THEME;
          const isEntered = enteredCards.has(persona.persona_id);
          const isRejected = rejectedId === persona.persona_id;
          const isSelected = selectedTarget === persona.persona_id;
          const isOther = rejectedId && !isRejected;

          return (
            <div
              key={persona.persona_id}
              className={`
                ${styles.directorCard}
                ${isEntered ? styles.cardEntered : styles.cardHidden}
                ${isRejected ? styles.cardRejected : ''}
                ${isSelected ? styles.cardSelected : ''}
                ${isOther ? styles.cardDimmed : ''}
              `}
              style={{
                '--card-glow': theme.bgGlow,
                '--card-border': theme.borderColor,
                '--card-gradient': theme.gradient,
                transitionDelay: `${i * 80}ms`,
              }}
            >
              {/* Avatar */}
              <div className={styles.avatar} style={{ background: theme.gradient }}>
                <span className={styles.avatarIcon}>{persona.avatar_emoji || theme.icon}</span>
              </div>

              {/* Name & Title */}
              <div className={styles.directorName}>{persona.name}</div>
              <div className={styles.directorTitle}>{persona.title}</div>

              {/* Archetype badge */}
              <div className={styles.archetypeBadge} style={{ borderColor: theme.borderColor, background: theme.bgGlow }}>
                {persona.icon} {persona.archetype}
              </div>

              {/* Stance */}
              <div className={styles.stance}>{theme.stance}</div>

              {/* Script (the argument) */}
              <div className={styles.script}>
                <div className={styles.scriptQuote}>"</div>
                <div className={styles.scriptText}>{persona.script}</div>
              </div>

              {/* Recommendation */}
              <div className={styles.recommendation}>
                Recommends: <strong>Option {persona.recommended_option}</strong> — {persona.recommended_label}
              </div>

              {/* Reject button */}
              {!rejectedId && (
                <button
                  className={`${styles.rejectBtn} ${isSelected ? styles.rejectBtnActive : ''}`}
                  onClick={() => onSelect?.(persona.persona_id)}
                >
                  {isSelected ? '✓ Selected for Rejection' : `Reject ${persona.name.split(' ')[0]}'s Advice`}
                </button>
              )}

              {/* Rejected overlay */}
              {isRejected && (
                <div className={styles.rejectedOverlay}>
                  <div className={styles.rejectedIcon}>🚪</div>
                  <div className={styles.rejectedText}>
                    {persona.name.split(' ')[0]} left the boardroom
                  </div>
                  <div className={styles.rejectedConsequence}>
                    This will affect your terminal valuation
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
