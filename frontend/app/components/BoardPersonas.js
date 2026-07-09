/**
 * BoardPersonas — AI board-member personas + message→persona resolver.
 * Phase A (player redesign): verbatim extraction from ExecutiveCockpit.js.
 */

// AI Board Member Personas (Improvement #4.2)
const BOARD_PERSONAS = {
  financial: { name: 'Sarah Chen, CFO', avatar: '👩‍💼', color: '#6366f1' },
  sustainability: { name: 'Dr. Kwame Asante, CSO', avatar: '🧑‍🔬', color: '#16a34a' },
  legal: { name: 'Marcus Wong, General Counsel', avatar: '👨‍⚖️', color: '#f59e0b' },
  crisis: { name: 'Elena Vasquez, CRO', avatar: '🧑‍💻', color: '#ef4444' },
  default: { name: 'Board of Directors', avatar: '🏛️', color: '#64748b' },
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
