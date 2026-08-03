/**
 * BoardPersonas — AI board-member personas + message→persona resolver.
 * Phase A (player redesign): verbatim extraction from ExecutiveCockpit.js.
 */

// AI Board Member Personas (Improvement #4.2)
/* A11Y-M1 (WCAG 1.4.3) — real-browser pass, 2026-08-02.
   `color` is a 500/600-weight hue picked for a light card. Used as TEXT on the
   mailbox item, which is dark in dark mode, every persona failed:
     default  #64748b on #151929 = 3.67:1   (and 4.16:1 on the light card)
   `textColor` is the same identity in the semantic text tier, which flips per
   theme by design (bright pastels on dark, 700-weights on light) — see
   styles/tokens.css. Measured on the mailbox card: 5.6:1 to 10.6:1 in dark,
   4.9:1 to 8.9:1 in light.

   `color` is deliberately KEPT and unchanged: ShadowBoardAudit.js builds a
   border out of it with `${persona.color}40`, and a var() cannot be
   concatenated with an alpha suffix. Consumers that need text pick
   `textColor`; consumers that need a colour value keep `color`. */
const BOARD_PERSONAS = {
  financial: { name: 'Sarah Chen, CFO', avatar: '👩‍💼', color: '#6366f1', textColor: 'var(--accent-text)' },
  sustainability: { name: 'Dr. Kwame Asante, CSO', avatar: '🧑‍🔬', color: '#16a34a', textColor: 'var(--positive-text)' },
  legal: { name: 'Marcus Wong, General Counsel', avatar: '👨‍⚖️', color: '#f59e0b', textColor: 'var(--caution-text)' },
  crisis: { name: 'Elena Vasquez, CRO', avatar: '🧑‍💻', color: '#ef4444', textColor: 'var(--danger-text)' },
  default: { name: 'Board of Directors', avatar: '🏛️', color: '#64748b', textColor: 'var(--text-muted)' },
};

function getPersona(msg) {
  const t = (msg.type || '').toLowerCase();
  const title = (msg.title || '').toLowerCase();
  if (t === 'crisis' || title.includes('crisis') || title.includes('alert')) return BOARD_PERSONAS.crisis;
  if (t === 'facilitator') return BOARD_PERSONAS.sustainability;
  if (title.includes('financial') || title.includes('treasury') || title.includes('ebitda')) return BOARD_PERSONAS.financial;
  if (title.includes('legal') || title.includes('regulation') || title.includes('compliance')) return BOARD_PERSONAS.legal;
  return BOARD_PERSONAS.default;
}

export { BOARD_PERSONAS, getPersona };
