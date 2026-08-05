'use client';
import { useMemo } from 'react';
import { RIVAL, AGENCY, deriveRivalRelease, deriveRatingLetter } from './rivalIntel';

/**
 * MarketIntelCards — W-B (W2b + W6)
 *
 * "Market Intelligence" section rendered inside the mailbox tab, BELOW the
 * real board messages. These cards are client-derived colour (see
 * rivalIntel.js): they are NOT messages — they never enter the `messages`
 * array, carry no read state, and cannot affect unread counts by
 * construction. Display-only.
 */

/* A11Y-M2 (WCAG 1.4.3) — real-browser pass, 2026-08-02.
   These cards render inside the mailbox rail, which is dark in dark mode, and
   every colour below was a 600/700-weight hue chosen for a light card. On the
   signed-in cockpit in Chromium:
     headline  #0f172a on #131828 = 1.01:1
     body      #334155 on #131828 = 1.71:1
     agency    #7c3aed on #14142c = 3.16:1   (and the CCC grade with it)
   `textColor` is the same identity in the semantic text tier (tokens.css),
   which is defined per theme; `color` stays for the glyph and the border. */
const DIR_META = {
  upgrade: { arrow: '▲', color: '#059669', textColor: 'var(--positive-text)', label: 'UPGRADE' },
  downgrade: { arrow: '▼', color: '#dc2626', textColor: 'var(--danger-text)', label: 'DOWNGRADE' },
  affirmed: { arrow: '►', color: '#64748b', textColor: 'var(--text-muted)', label: 'AFFIRMED' },
  initiated: { arrow: '◆', color: '#7c3aed', textColor: 'var(--accent-text)', label: 'INITIATED' },
};

export default function MarketIntel({ history, roundNumber }) {
  const release = useMemo(() => deriveRivalRelease(history), [history]);
  const letter = useMemo(() => deriveRatingLetter(history), [history]);
  if (!release && !letter) return null;

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{
        fontSize: 'var(--type-caption)', fontWeight: 800, letterSpacing: '0.1em',
        textTransform: 'uppercase', color: 'var(--text-muted)', margin: '0 0 6px 2px',
        display: 'flex', alignItems: 'center', gap: 5,
      }}>
        <span>🛰️</span> Market Intelligence
      </div>

      {/* W2b: rival press release — latest committed round */}
      {release && (
        <div style={{
          padding: '8px 10px', marginBottom: 6, borderRadius: 8,
          background: 'rgba(100, 116, 139, 0.06)',
          borderLeft: `3px solid ${RIVAL.color}`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
            <span style={{ fontSize: 'var(--type-caption)' }}>{RIVAL.avatar}</span>
            <span style={{ fontSize: 'var(--type-caption)', fontWeight: 600, color: RIVAL.textColor || RIVAL.color }}>{RIVAL.name}</span>
            {/* A11Y-M2: this chip was #64748b text on rgba(100,116,139,0.12) —
                the SAME hue as its own background. It measured 1:1 in BOTH
                themes: a label rendered in its own backdrop. Not a theme bug,
                an authoring one. */}
            <span style={{
              fontSize: 'var(--type-caption)', fontWeight: 800, color: 'var(--text-secondary)',
              background: 'rgba(100,116,139,0.12)', padding: '1px 5px',
              borderRadius: 3, letterSpacing: '0.06em',
            }}>MARKET NEWS</span>
          </div>
          <strong style={{ fontSize: 'var(--type-caption)', color: 'var(--text-primary)' }}>{release.title}</strong>
          <p style={{ margin: '2px 0 0', fontSize: 'var(--type-caption)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{release.body}</p>
          <div style={{ fontSize: 'var(--type-caption)', color: 'var(--neutral)', marginTop: 4 }}>
            Wire report · Round {release.round} results · derived from market data
          </div>
        </div>
      )}

      {/* W6: Meridian ESG rating letter — latest even committed round */}
      {letter && (() => {
        const dir = DIR_META[letter.direction] || DIR_META.affirmed;
        return (
          <div style={{
            padding: '8px 10px', marginBottom: 6, borderRadius: 8,
            background: 'rgba(124, 58, 237, 0.05)',
            borderLeft: `3px solid ${AGENCY.color}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
              <span style={{ fontSize: 'var(--type-caption)' }}>{AGENCY.avatar}</span>
              <span style={{ fontSize: 'var(--type-caption)', fontWeight: 600, color: AGENCY.textColor || AGENCY.color }}>{AGENCY.name}</span>
              <span style={{
                fontSize: 'var(--type-caption)', fontWeight: 800, color: dir.textColor || dir.color,
                background: 'rgba(100,116,139,0.08)', padding: '1px 5px',
                borderRadius: 3, letterSpacing: '0.06em',
              }}>{dir.arrow} {dir.label}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{
                fontSize: '1.15rem', fontWeight: 900, color: dir.textColor || dir.color,
                fontFamily: 'var(--font-numeral, monospace)', letterSpacing: '0.04em',
              }}>{letter.grade}</span>
              {letter.prevGrade && letter.prevGrade !== letter.grade && (
                <span style={{ fontSize: 'var(--type-caption)', color: 'var(--neutral)' }}>from {letter.prevGrade}</span>
              )}
              <span style={{ fontSize: 'var(--type-caption)', color: 'var(--neutral)' }}>ESG composite {letter.score}/100</span>
            </div>
            <p style={{ margin: '3px 0 0', fontSize: 'var(--type-caption)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{letter.rationale}</p>
            <div style={{ fontSize: 'var(--type-caption)', color: 'var(--neutral)', marginTop: 4 }}>
              Semi-annual review · after Round {letter.round} · methodology: reputation 45% · carbon 25% · natural capital 15% · capital access 15%
            </div>
          </div>
        );
      })()}

      {/* A11Y-M2: #b6c2d1 is a DARK-theme neutral; on the light card it was
          1.65:1. This is the disclaimer that says the numbers are simulated —
          the one line here a reader must not miss. */}
      <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)', margin: '2px 2px 0', fontStyle: 'italic' }}>
        Simulated market colour, derived from your session data — informational only.
      </div>
    </div>
  );
}
