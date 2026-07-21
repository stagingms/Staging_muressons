// Pure helper — removes academic framing tagged with <span class="ped-academic">…</span>
// from player briefing narrative when the briefing_theory toggle is OFF (default for
// players). Facilitators keep the full pedagogy in the teleprompter and can re-enable
// it on the player briefing via the god-mode global setting. Kept dependency-free so it
// is trivially unit-testable and safe to import anywhere.
export function stripPedagogy(html) {
  if (!html || typeof html !== 'string') return html || '';
  // Fast path: untagged narratives (e.g. the healthcare & SDG editions, which have no
  // textbook asides) are returned byte-for-byte unchanged — no whitespace touching.
  if (!html.includes('ped-academic')) return html;
  return html
    .replace(/<span class="ped-academic">[\s\S]*?<\/span>/g, '')
    .replace(/\(\s*\)/g, '')            // empty parens left by a removed citation
    .replace(/\s+([.,;:!?])/g, '$1')    // tidy space-before-punctuation
    .replace(/\s{2,}/g, ' ')
    .replace(/\s+<\/(p|li|strong|em)>/g, '</$1>')
    .trim();
}
