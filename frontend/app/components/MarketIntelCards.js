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

const DIR_META = {
  upgrade: { arrow: '▲', color: '#059669', label: 'UPGRADE' },
  downgrade: { arrow: '▼', color: '#dc2626', label: 'DOWNGRADE' },
  affirmed: { arrow: '►', color: '#64748b', label: 'AFFIRMED' },
  initiated: { arrow: '◆', color: '#7c3aed', label: 'INITIATED' },
};

export default function MarketIntel({ history, roundNumber }) {
  const release = useMemo(() => deriveRivalRelease(history), [history]);
  const letter = useMemo(() => deriveRatingLetter(history), [history]);
  if (!release && !letter) return null;

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{
        fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.1em',
        textTransform: 'uppercase', color: '#64748b', margin: '0 0 6px 2px',
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
            <span style={{ fontSize: '0.7rem' }}>{RIVAL.avatar}</span>
            <span style={{ fontSize: '0.68rem', fontWeight: 600, color: RIVAL.color }}>{RIVAL.name}</span>
            <span style={{
              fontSize: '0.55rem', fontWeight: 800, color: '#64748b',
              background: 'rgba(100,116,139,0.12)', padding: '1px 5px',
              borderRadius: 3, letterSpacing: '0.06em',
            }}>MARKET NEWS</span>
          </div>
          <strong style={{ fontSize: '0.68rem', color: '#0f172a' }}>{release.title}</strong>
          <p style={{ margin: '2px 0 0', fontSize: '0.65rem', color: '#334155', lineHeight: 1.5 }}>{release.body}</p>
          <div style={{ fontSize: '0.58rem', color: '#94a3b8', marginTop: 4 }}>
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
              <span style={{ fontSize: '0.7rem' }}>{AGENCY.avatar}</span>
              <span style={{ fontSize: '0.68rem', fontWeight: 600, color: AGENCY.color }}>{AGENCY.name}</span>
              <span style={{
                fontSize: '0.55rem', fontWeight: 800, color: dir.color,
                background: 'rgba(100,116,139,0.08)', padding: '1px 5px',
                borderRadius: 3, letterSpacing: '0.06em',
              }}>{dir.arrow} {dir.label}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{
                fontSize: '1.15rem', fontWeight: 900, color: dir.color,
                fontFamily: 'var(--font-numeral, monospace)', letterSpacing: '0.04em',
              }}>{letter.grade}</span>
              {letter.prevGrade && letter.prevGrade !== letter.grade && (
                <span style={{ fontSize: '0.62rem', color: '#94a3b8' }}>from {letter.prevGrade}</span>
              )}
              <span style={{ fontSize: '0.6rem', color: '#94a3b8' }}>ESG composite {letter.score}/100</span>
            </div>
            <p style={{ margin: '3px 0 0', fontSize: '0.65rem', color: '#334155', lineHeight: 1.5 }}>{letter.rationale}</p>
            <div style={{ fontSize: '0.58rem', color: '#94a3b8', marginTop: 4 }}>
              Semi-annual review · after Round {letter.round} · methodology: reputation 45% · carbon 25% · natural capital 15% · capital access 15%
            </div>
          </div>
        );
      })()}

      <div style={{ fontSize: '0.56rem', color: '#b6c2d1', margin: '2px 2px 0', fontStyle: 'italic' }}>
        Simulated market colour, derived from your session data — informational only.
      </div>
    </div>
  );
}
