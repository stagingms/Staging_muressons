'use client';
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import Dialog from './Dialog';
import { deriveKeyInsights, fmtDeltaM, roundLedger } from '../lib/keyInsights';
import { currencySymbol, atRate } from '../utils/format';

/**
 * FrontPageReveal (Feature 5) — the Year-5 terminal edition of THE MURESSONS
 * TIMES: a full-screen four-column broadsheet debrief generated from the
 * team's own run.
 *
 * Slot: OverlayHost (interrupt, summoned). The results stage carries only the
 * one-line masthead trigger — a launcher, not a panel — and the paper itself
 * takes the whole screen, so this feature still occupies exactly ONE slot
 * (CLAUDE.md, V-D). It was previously an inline results-stage panel; a
 * four-column broadsheet cannot be read inside a column of the scorecard.
 *
 * NO INVENTED FACTS. Every figure below traces to a real payload:
 *   data          round-10 commit `events` (terminal valuation, P&L, carbon,
 *                 M_R breakdown, competitor EBITDA, ceo_diary, decision_regret)
 *   history       per-round dashboard rows (closing treasury + choice)
 *   peers         /peer-leaderboard (the cohort's other teams)
 *   series        /balance-sheet history (year-end net assets, EBITDA)
 * Anything absent renders as "—" or its whole section is omitted. The editorial
 * templates are the only prose, and they only ever interpolate real numbers.
 *
 * Props: sessionId, data, cohortName, history, peers.
 */

// Band selection. A newspaper reports the SHARE PRICE, so the headline must
// reflect the equity bridge (EV − net debt), not the Regenerative Multiple in
// isolation. The backend's archetype solvency-gate keys off DMAV (treasury ×
// M_R − NCD), which can stay positive while net debt has already wiped out
// equity — that is exactly how a $35.6M "de-risked" splash ended up sitting on
// top of a −$4.99 share price. Here we trust the equity truth first, then the
// backend archetype, then fall back to the raw M_R ladder.
const PROFILE_BAND = {
  regenerative_titan:  'titan',
  derisked_safe_haven: 'safe',
  fragile_giant:       'fragile',
  hollow_idealist:     'insolvent',
  stranded_relic:      'relic',
};

function mrBand(mr) {
  if (mr >= 1.8) return 'titan';
  if (mr >= 1.2) return 'safe';
  if (mr >= 0.8) return 'fragile';
  return 'relic';
}

export function bandFor(mr, d = {}) {
  const ev    = Number(d.terminal_value) || 0;
  const price = d.price_per_share;
  const eq    = d.equity_value;
  const equityWiped = (price != null && price < 0) || (eq != null && eq <= 0);

  // Start from the backend's real archetype where we have it.
  let band = PROFILE_BAND[d.profile] || mrBand(mr);

  // Equity-truth overrides — the front page cannot flatter an outcome the
  // share price contradicts.
  if (ev <= 0) return 'relic';                       // enterprise value itself gone
  if (equityWiped && band !== 'relic') return 'insolvent'; // EV positive, owners wiped out
  return band;
}

/**
 * Derive one major achievement and one major misstep from the terminal state,
 * highest-signal first. Everything is read from the final-report payload the
 * scorecard already holds — no new data plumbing, nothing invented.
 */
function deriveLedger(d = {}) {
  const mr      = Number(d.regenerative_multiple) || 0;
  const price   = d.price_per_share;
  const eq      = d.equity_value;
  const ev      = Number(d.terminal_value) || 0;
  const netDebt = d.net_debt;
  const rep     = Number(d.group_reputation);
  const jt      = d.just_transition_passed;
  const bd      = d.mr_breakdown || {};
  const has     = (k) => Math.abs(Number(bd[k]) || 0) > 0.0001;
  const equityWiped = (price != null && price < 0) || (eq != null && eq <= 0);

  let achievement = null;
  if (mr >= 1.8)                      achievement = `A ${mr.toFixed(2)}× Regenerative Multiple — ESG performance compounded straight into enterprise value.`;
  else if (has('climate_leader'))    achievement = `Decisive decarbonisation earned a climate-leadership premium at valuation.`;
  else if (has('social_regeneration')) achievement = `A workforce-first strategy earned a social-regeneration premium on the multiple.`;
  else if (has('resilience_bonus'))  achievement = `Early resilience investments carried the group through the crisis rounds intact.`;
  else if (has('truth_premium'))     achievement = `Radical transparency earned a "truth premium" with the market.`;
  else if (jt === true || has('just_transition_bonus') || has('community_champion_bonus'))
                                     achievement = `Delivered a credible just transition, keeping workforce and community onside.`;
  else if (price != null && price >= 50) achievement = `Shareholders rewarded with a ${currencySymbol()}${atRate(price).toFixed(2)} share price on a well-capitalised balance sheet.`;
  else if (Number.isFinite(rep) && rep >= 65) achievement = `Group reputation closed strong at ${rep.toFixed(0)}/100.`;
  else if (mr >= 1.2)                achievement = `Held a de-risked balance sheet with limited residual climate exposure.`;

  let misstep = null;
  if (ev <= 0)                       misstep = `Natural Capital Debt consumed enterprise value entirely — the group ended value-destroyed.`;
  else if (equityWiped)              misstep = `Net debt overwhelmed equity: shareholders were effectively wiped out despite a positive enterprise value.`;
  else if (has('social_collapse'))   misstep = `A collapse in social licence triggered a punitive valuation discount.`;
  else if (has('instability_discount')) misstep = `Governance and social instability forced a 40% instability discount on the multiple.`;
  else if (has('stranded_asset_penalty')) misstep = `High-carbon assets stranded, dragging the multiple toward breakeven.`;
  else if (netDebt != null && ev > 0 && netDebt > ev) misstep = `The group leaned heavily on debt — net debt now exceeds enterprise value.`;
  else if (Number.isFinite(rep) && rep < 40) misstep = `Reputation ended weak at ${rep.toFixed(0)}/100, capping pricing power.`;
  else if (mr < 1.2)                misstep = `Deferred green investment left upside on the table — the multiple never reached leadership territory.`;
  else if (jt === false)            misstep = `The transition left parts of the workforce behind, capping the social multiplier.`;

  return { achievement, misstep };
}

/* ── Newsprint charts ────────────────────────────────────────────────────────
   Pure SVG-string builders so the same figure renders in the on-screen page
   (dangerouslySetInnerHTML) AND in the downloadable PNG (nested <svg x y>). */

/* The rate lands HERE, on the raw value, not on the three formatted branches
   below. Multiplication is linear, so one wrap converts all of them and cannot
   move a decimal place. */
const fmtM = (v) => {
  const m = atRate(v) / 1_000_000;
  const a = Math.abs(m);
  return `${m < 0 ? '−' : ''}${currencySymbol()}${a >= 100 ? a.toFixed(0) : a.toFixed(1)}M`;
};

/** Null-safe money for table cells: never prints a number we do not have. */
const money = (v) => (Number.isFinite(Number(v)) ? fmtM(Number(v)) : '—');
const num = (v, dp = 2) => (Number.isFinite(Number(v)) ? Number(v).toFixed(dp) : '—');

function yearSeries(hist) {
  const rows = (hist || []).filter((h) => h && Number.isFinite(Number(h.round)));
  const ends = rows.filter((h) => Number(h.round) % 2 === 0).sort((a, b) => a.round - b.round);
  const src = ends.length >= 2 ? ends : rows.sort((a, b) => a.round - b.round);
  return src.map((h) => ({
    year: Math.ceil(Number(h.round) / 2),
    netAssets: Number(h.net_assets),
    ebitda: Number(h.ebitda),
  }));
}

/** Vertical bar chart in newsprint style. Negative bars hang below the zero
    line in newspaper red; positives print in ink. */
function barChartSVG(series, key, { w = 460, h = 200, title = '', x = 0, y = 0 } = {}) {
  const pts = series.filter((s) => Number.isFinite(s[key]));
  if (pts.length < 2) return '';
  const padL = 8, padR = 8, padT = 30, padB = 26;
  const iw = w - padL - padR, ih = h - padT - padB;
  const vals = pts.map((p) => p[key]);
  const max = Math.max(0, ...vals), min = Math.min(0, ...vals);
  const span = (max - min) || 1;
  const yOf = (v) => padT + ((max - v) / span) * ih;
  const zero = yOf(0);
  const bw = Math.min(56, (iw / pts.length) * 0.55);
  const step = iw / pts.length;
  const bars = pts.map((p, i) => {
    const cx = padL + step * i + step / 2;
    const v = p[key];
    const yTop = Math.min(yOf(v), zero), bh = Math.max(2, Math.abs(yOf(v) - zero));
    const neg = v < 0;
    const valY = neg ? yTop + bh + 13 : yTop - 5;
    return `
      <rect x="${(cx - bw / 2).toFixed(1)}" y="${yTop.toFixed(1)}" width="${bw.toFixed(1)}" height="${bh.toFixed(1)}"
            fill="${neg ? '#b42318' : '#1a1a1a'}" fill-opacity="${neg ? 0.85 : 0.9}"/>
      <text x="${cx.toFixed(1)}" y="${valY.toFixed(1)}" text-anchor="middle" font-family="Georgia,serif" font-size="11" fill="${neg ? '#b42318' : '#333'}">${fmtM(v)}</text>
      <text x="${cx.toFixed(1)}" y="${h - 8}" text-anchor="middle" font-family="Georgia,serif" font-size="12" fill="#555">Y${p.year}</text>`;
  }).join('');
  return `
  <svg x="${x}" y="${y}" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">
    <text x="0" y="14" font-family="Georgia,serif" font-size="13" font-weight="700" letter-spacing="0.08em" fill="#1a1a1a">${title}</text>
    <line x1="0" y1="19" x2="${w}" y2="19" stroke="#1a1a1a" stroke-width="1.5"/>
    <line x1="${padL}" y1="${zero.toFixed(1)}" x2="${w - padR}" y2="${zero.toFixed(1)}" stroke="#999" stroke-width="1"/>
    ${bars}
  </svg>`;
}

/** Line chart in newsprint style — single ink line with point markers. */
function lineChartSVG(series, key, { w = 460, h = 190, title = '', x = 0, y = 0 } = {}) {
  const pts = series.filter((s) => Number.isFinite(s[key]));
  if (pts.length < 2) return '';
  const padL = 8, padR = 30, padT = 30, padB = 26;
  const iw = w - padL - padR, ih = h - padT - padB;
  const vals = pts.map((p) => p[key]);
  const max = Math.max(0, ...vals), min = Math.min(0, ...vals);
  const span = (max - min) || 1;
  const xOf = (i) => padL + (pts.length === 1 ? iw / 2 : (i / (pts.length - 1)) * iw);
  const yOf = (v) => padT + ((max - v) / span) * ih;
  const zero = yOf(0);
  const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${xOf(i).toFixed(1)},${yOf(p[key]).toFixed(1)}`).join(' ');
  const marks = pts.map((p, i) => {
    const neg = p[key] < 0;
    return `
      <circle cx="${xOf(i).toFixed(1)}" cy="${yOf(p[key]).toFixed(1)}" r="3.5" fill="${neg ? '#b42318' : '#1a1a1a'}"/>
      <text x="${xOf(i).toFixed(1)}" y="${(yOf(p[key]) + (neg ? 18 : -9)).toFixed(1)}" text-anchor="middle" font-family="Georgia,serif" font-size="11" fill="${neg ? '#b42318' : '#333'}">${fmtM(p[key])}</text>
      <text x="${xOf(i).toFixed(1)}" y="${h - 8}" text-anchor="middle" font-family="Georgia,serif" font-size="12" fill="#555">Y${p.year}</text>`;
  }).join('');
  return `
  <svg x="${x}" y="${y}" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">
    <text x="0" y="14" font-family="Georgia,serif" font-size="13" font-weight="700" letter-spacing="0.08em" fill="#1a1a1a">${title}</text>
    <line x1="0" y1="19" x2="${w}" y2="19" stroke="#1a1a1a" stroke-width="1.5"/>
    <line x1="${padL}" y1="${zero.toFixed(1)}" x2="${w - padR}" y2="${zero.toFixed(1)}" stroke="#999" stroke-width="1" stroke-dasharray="3 3"/>
    <path d="${path}" fill="none" stroke="#1a1a1a" stroke-width="2"/>
    ${marks}
  </svg>`;
}

/* ── Editorial templates ─────────────────────────────────────────────────────
   Realistic broadsheet copy: title-case headline, dateline lede, reported
   paragraphs. `paras(t)` returns the article body; the achievement/misstep
   ledger and the "By the Numbers" box render as sidebars. */

export const TEMPLATES = {
  titan: {
    tone: '#10b981',
    byline: 'A. Renard, Markets Correspondent',
    headline: (t) => `Muressons' Regenerative Bet Pays Off as Valuation Reaches ${t.tv}`,
    subhead: (t) => `Five years after the board tied executive pay to natural-capital targets, the conglomerate's ${t.mr}× multiple is the sector benchmark`,
    quote: `"They proved the thesis: decarbonisation and value creation were the same project all along."`,
    paras: (t) => [
      `MURESSONS CITY — The Muressons Group closed the books on its five-year transformation programme with a terminal enterprise value of ${t.tv}, capping a period in which the conglomerate turned aggressive sustainability spending into the strongest valuation multiple among its peers.`,
      `The group's ${t.mr}× regenerative multiple — a measure investors now use to price resilience as much as earnings — reflects early, sustained capital allocation into decarbonisation, supply-chain hardening and workforce transition. Shares ended the period at ${currencySymbol()}${t.price}.`,
      `Rivals that deferred the same investments spent the back half of the plan absorbing crisis costs Muressons had already engineered out. Fund managers described the result as "compounding by another name."`,
      `The board is expected to extend the programme into a second five-year horizon, with analysts pressing for detail on how the group protects its lead as the premium it earned becomes the market's baseline.`,
    ],
  },
  safe: {
    tone: '#3b82f6',
    byline: 'S. Okafor, Corporate Affairs Desk',
    headline: (t) => `Muressons Closes Five-Year Plan With Steady Returns, Thinner Green Pipeline`,
    subhead: (t) => `A ${t.tv} valuation on a ${t.mr}× multiple rewards caution — and prices in the investments the group chose not to make`,
    quote: `"Solid, defensible, unspectacular. The question is what they compound from here."`,
    paras: (t) => [
      `MURESSONS CITY — The Muressons Group reported a terminal enterprise value of ${t.tv} on Friday, ending its five-year plan with the de-risked balance sheet management promised — and with questions about the growth it traded away to get there.`,
      `The group's ${t.mr}× regenerative multiple places it comfortably above distressed peers but short of the sector's leaders, a gap analysts attribute to green-infrastructure investments that were studied, budgeted and then deferred. Shares closed the period at ${currencySymbol()}${t.price}.`,
      `Executives defend the record: crisis rounds that forced write-downs elsewhere passed with limited damage, and the group enters the next cycle with headroom rather than obligations. "We kept our options open," one senior manager said.`,
      `The counter-argument is already circulating in investor notes: options have expiry dates, and the premium for early movers has widened every year of the plan.`,
    ],
  },
  insolvent: {
    tone: '#a855f7',
    byline: 'D. Vasquez, Markets Desk',
    headline: (t) => `Debt Overhang Wipes Out Muressons Shareholders Despite ${t.tv} Valuation`,
    subhead: (t) => `The headline enterprise value survives; the equity beneath it does not, once ${'netDebtM' in t && t.netDebtM !== '—' ? `${t.netDebtMoney} of net debt` : 'the debt stack'} is settled`,
    quote: `"Impressive at the top line, hollow underneath — the equity was gone before the valuation printed."`,
    paras: (t) => [
      `MURESSONS CITY — On paper, the Muressons Group ends its five-year plan valued at ${t.tv}. For its shareholders, the arithmetic is crueller: after the group's accumulated borrowings are netted off, the equity is worth effectively nothing, and the shares closed the period at ${currencySymbol()}${t.price}.`,
      `The pattern will be familiar to restructuring specialists. Operating ambitions — some of them genuinely regenerative, reflected in a ${t.mr}× multiple — were funded with debt rather than earnings, and the balance sheet quietly inverted while the strategy narrative held the spotlight.`,
      `Creditors, not owners, now hold the economics of the enterprise. Bondholders are expected to drive any recapitalisation, with existing equity heavily diluted or extinguished in most scenarios bankers describe.`,
      `The lesson traders drew was blunt: a sustainability premium on the multiple cannot outrun a funding model that mortgages the equity to pay for it.`,
    ],
  },
  fragile: {
    tone: '#f59e0b',
    byline: 'R. Whitfield, Risk & Regulation',
    headline: (t) => `Muressons' Five-Year Report Leaves Analysts Asking What Holds in the Next Storm`,
    subhead: (t) => `A ${t.tv} valuation rests on a thin ${t.mr}× multiple as deferred transition costs begin to come due`,
    quote: `"The bill for short-termism arrives late, larger, and with fewer options attached."`,
    paras: (t) => [
      `MURESSONS CITY — The Muressons Group ended its five-year programme with a terminal enterprise value of ${t.tv}, a result the group presented as stability and the market read as fragility. Shares closed the period at ${currencySymbol()}${t.price}.`,
      `The concern is concentrated in the group's ${t.mr}× regenerative multiple, which sits close enough to breakeven that a single stranded-asset ruling, remediation order or reputational shock could tip the valuation into discount territory.`,
      `Institutional holders spent the final quarters pressing for a credible transition plan with dates and capital attached, rather than the sequence of pilots and reviews that characterised the middle years of the plan.`,
      `The group has runway, analysts concede — but it is measured in quarters now, not years, and the next crisis window will not negotiate.`,
    ],
  },
  relic: {
    tone: '#ef4444',
    byline: 'M. Adeyemi, Investigations',
    headline: (t) => `Stranded Assets, Shrinking Options: Muressons Ends the Era Under Pressure`,
    subhead: (t) => `Five years of extraction leave a ${t.mr}× multiple, a ${t.tv} valuation under sustained pressure, and a narrowing path back`,
    quote: `"A cautionary tale of value destroyed one deferred decision at a time."`,
    paras: (t) => [
      `MURESSONS CITY — The Muressons Group closed its five-year plan in the position its critics predicted at the outset: carbon-heavy assets written down, social licence eroded, and a valuation — ${t.tv} at the terminal reading — that reflects a ${t.mr}× multiple deep in distressed territory. Shares ended the period at ${currencySymbol()}${t.price}.`,
      `Internal documents reviewed across the period show a consistent pattern: transition investments scoped, costed and shelved, with the savings booked to earnings that the market has since clawed back several times over.`,
      `Regulators are circling the remediation ledger, activist holders are demanding board changes, and the insurers who once priced the group as an industrial stalwart now price it as a liability book.`,
      `Whatever emerges from the coming restructuring will be smaller, greener by necessity, and — in the phrase one adviser used — "a company that pays for the decade it declined to fund."`,
    ],
  },
};

/* ── M_R breakdown: engine key → reader-facing label ───────────────────────── */
const MR_LABELS = {
  base: 'Base multiple',
  materiality_governance: 'Materiality governance',
  synergy_bonus: 'Cross-unit synergy',
  resilience_bonus: 'Resilience investment',
  truth_premium: 'Transparency premium',
  community_champion_bonus: 'Community standing',
  just_transition_bonus: 'Just transition',
  workforce_bonus: 'Workforce capability',
  wellbeing_bonus: 'Employee wellbeing',
  climate_leader: 'Climate leadership',
  social_regeneration: 'Social regeneration',
  instability_discount: 'Instability discount',
  social_collapse: 'Social-licence collapse',
  stranded_asset_penalty: 'Stranded assets',
  greenwashing_penalty: 'Greenwashing penalty',
};

/* Structural keys that are not themselves credits or debits. */
const MR_NON_LINE = new Set(['base', 'max_achievable_mr', 'jt_scaling_factor', 'final_mr']);

const CSS = `
.fpr-paper { background:#f4f1ea; color:#111; font-family:Georgia,'Times New Roman',serif;
  /* PHASE 10: this used to arrive at full #f4f1ea in one frame — a
     full-viewport near-white surface in a darkened room, at the end of a
     ninety-minute session run on a dark cockpit. The paper colour is
     deliberate and stays; what changes is that it is REACHED rather than
     switched to. 400ms is long enough for an iris to follow and short enough
     that nobody waits for a newspaper. */
  animation: fpr-dawn 400ms cubic-bezier(0.4, 0, 0.2, 1) both; }
@keyframes fpr-dawn {
  from { background-color:#12161f; color:#12161f; }
  to   { background-color:#f4f1ea; color:#111; }
}
/* Reduced motion means "do not move me", not "flash me". Shorten the ramp
   rather than removing it: a cross-fade with no translation is not the class
   of motion that causes trouble, and the instant version is the harsher one. */
@media (prefers-reduced-motion: reduce) {
  .fpr-paper { animation-duration:120ms; }
}
.fpr-body { column-count:4; column-gap:26px; column-rule:1px solid #d8d2c4;
            font-size:0.90rem; line-height:1.60; text-align:justify; }
@media (max-width:1500px){ .fpr-body{ column-count:3; } }
@media (max-width:1080px){ .fpr-body{ column-count:2; } }
@media (max-width:720px) { .fpr-body{ column-count:1; } }
.fpr-sec { break-inside:avoid; page-break-inside:avoid; margin:0 0 16px;
           padding:11px 12px; background:#ece7dc; border:1px solid #1a1a1a; }
.fpr-sec h4 { margin:0 0 8px; font-size:0.70rem; font-weight:700; letter-spacing:0.11em;
              text-transform:uppercase; border-bottom:1px solid #1a1a1a; padding-bottom:5px; }
.fpr-fig { break-inside:avoid; margin:0 0 16px; padding:10px 10px 6px;
           background:#efeade; border:1px solid #d8d2c4; }
.fpr-cap { font-size:0.66rem; color:#6b6b6b; margin-top:4px; font-style:italic; line-height:1.4; }
.fpr-row { display:flex; justify-content:space-between; gap:8px; font-size:0.80rem;
           padding:2px 0; border-bottom:1px dotted #cfc8b8; }
.fpr-row span:first-child { color:#444; }
.fpr-row strong { white-space:nowrap; }
.fpr-tbl { width:100%; border-collapse:collapse; font-size:0.76rem; }
.fpr-tbl th { text-align:left; font-size:0.62rem; letter-spacing:0.06em; text-transform:uppercase;
              color:#555; border-bottom:1px solid #1a1a1a; padding:3px 2px; font-weight:700; }
.fpr-tbl td { padding:3px 2px; border-bottom:1px dotted #cfc8b8; }
.fpr-tbl td.n { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }
.fpr-p { margin:0 0 11px; }
.fpr-drop::first-letter { float:left; font-size:3.1rem; line-height:0.82; padding:3px 7px 0 0; font-weight:700; }
`;

export default function FrontPageReveal({
  sessionId,
  data = {},
  cohortName = '',
  history = [],
  peers = [],
}) {
  const [enabled, setEnabled] = useState(true); // default show; disable only if facilitator turned it off
  const [open, setOpen] = useState(false);
  // WOW-5E: LLM-enhanced copy (falls back to deterministic)
  const [llmCopy, setLlmCopy] = useState(null);
  // Year-by-year figures for the pictorial charts (balance-sheet history).
  const [series, setSeries] = useState([]);
  // The cohort's other teams. Passed in when the scorecard already fetched it;
  // fetched here otherwise so the paper works standalone.
  const [peerRows, setPeerRows] = useState(peers || []);

  useEffect(() => { if (peers && peers.length) setPeerRows(peers); }, [peers]);

  useEffect(() => {
    // Respect the facilitator toggle (public settings endpoint). Fail-open so a
    // hiccup never hides the reveal.
    const q = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    fetch(`/api/admin/global-settings${q}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((s) => { if (s && s.front_page_enabled === false) setEnabled(false); })
      .catch(() => {});
  }, [sessionId]);

  // WOW-5E: Try fetching LLM-enhanced copy (fire-and-forget, deterministic fallback)
  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    fetch(`${API}/api/simulations/${sessionId}/front-page`)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!cancelled && d && d.source === 'llm') {
          setLlmCopy(d);
        }
      })
      .catch(() => {}); // Silent — deterministic fallback always works
    return () => { cancelled = true; };
  }, [sessionId]);

  // Charts: year-end net assets + EBITDA from the balance-sheet history
  // (the endpoint stitches the full period, so legacy sessions chart too).
  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    fetch(`${API}/api/simulations/${sessionId}/balance-sheet`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (cancelled || !d) return;
        setSeries(yearSeries(d.balance_sheet?.balance_sheet_history));
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [sessionId]);

  // Competitor desk: only fetch if the parent did not already hand us the rows.
  useEffect(() => {
    if (!sessionId || (peers && peers.length)) return;
    let cancelled = false;
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    fetch(`${API}/api/simulations/${sessionId}/peer-leaderboard`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (!cancelled && Array.isArray(d?.leaderboard)) setPeerRows(d.leaderboard); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [sessionId, peers]);

  /* PHASE 8. Escape lived here and nothing else did: no focus trap, so Tab
     walked out of a full-viewport overlay into the scorecard underneath it,
     and no focus restore, so closing the edition dropped focus on <body>
     instead of returning it to the button that opened it. Dialog owns all
     three now. The close button still says "(Esc)" and that is still true. */

  const t = useMemo(() => {
    const mr = Number(data.regenerative_multiple) || 0;
    const ledger = deriveLedger(data);
    return {
      mr: mr.toFixed(2),
      // `tv` is the printable money string ("−$56.2M"); the templates use it so
      // a negative valuation no longer reads "$-56.2M" with the sign stranded
      // inside the currency. `tvM` stays as the bare magnitude for callers that
      // want to compose their own units.
      tv: money(data.terminal_value),
      netDebtMoney: money(data.net_debt),
      tvM: ((Number(data.terminal_value) || 0) / 1_000_000).toFixed(1),
      price: data.price_per_share != null ? atRate(data.price_per_share).toFixed(2) : '—',
      eqM: data.equity_value != null ? (Number(data.equity_value) / 1_000_000).toFixed(1) : '—',
      netDebtM: data.net_debt != null ? (Number(data.net_debt) / 1_000_000).toFixed(1) : '—',
      rep: Number.isFinite(Number(data.group_reputation)) ? Number(data.group_reputation).toFixed(0) : '—',
      achievement: ledger.achievement,
      misstep: ledger.misstep,
    };
  }, [data]);

  const band = bandFor(Number(data.regenerative_multiple) || 0, data);
  const baseTpl = TEMPLATES[band];

  // WOW-5E: Merge LLM copy into template (override headline/subhead/quote only)
  const tpl = useMemo(() => {
    if (llmCopy) {
      return {
        ...baseTpl,
        headline: () => llmCopy.headline,
        subhead: () => llmCopy.subhead,
        quote: llmCopy.quote,
      };
    }
    return baseTpl;
  }, [baseTpl, llmCopy]);

  /* ── Derived sections. Each is null when its source data is absent. ────── */

  // `money()` rather than `${t.netDebtMoney}`: the latter printed "$-62.1M",
  // with the sign stranded inside the currency. The headline templates keep
  // their own interpolation, unchanged.
  const numbersRows = useMemo(() => ([
    ['Enterprise value', money(data.terminal_value)],
    ['Regenerative multiple', `${t.mr}×`],
    ['Share price', t.price === '—' ? '—' : `${currencySymbol()}${t.price}`],
    ['Equity value', money(data.equity_value)],
    ['Net debt', money(data.net_debt)],
    ['Group reputation', t.rep === '—' ? '—' : `${t.rep}/100`],
  ]), [t, data]);

  // Terminal-year P&L, straight off the engine's own totals.
  const pnlRows = useMemo(() => {
    const rows = [
      ['Group revenue', money(data.total_revenue)],
      ['Operating costs', money(data.total_opex)],
      ['Terminal EBITDA', money(data.terminal_ebitda)],
      ['Closing treasury', money(data.final_treasury)],
      ['Exit multiple', Number.isFinite(Number(data.exit_multiple)) ? `${num(data.exit_multiple, 1)}×` : '—'],
      ['Shares outstanding', Number.isFinite(Number(data.shares_outstanding))
        ? `${(Number(data.shares_outstanding) / 1_000_000).toFixed(0)}M` : '—'],
    ];
    return rows.filter(([, v]) => v !== '—');
  }, [data]);

  // M_R attribution — only the lines the engine actually scored.
  const mrLines = useMemo(() => {
    const bd = data.mr_breakdown;
    if (!bd || typeof bd !== 'object') return null;
    const lines = Object.entries(bd)
      .filter(([k, v]) => !MR_NON_LINE.has(k) && Number.isFinite(Number(v)) && Math.abs(Number(v)) > 0.0001)
      .map(([k, v]) => [MR_LABELS[k] || k.replace(/_/g, ' '), Number(v)]);
    if (!lines.length) return null;
    return {
      base: Number.isFinite(Number(bd.base)) ? Number(bd.base) : null,
      lines,
      max: Number.isFinite(Number(bd.max_achievable_mr)) ? Number(bd.max_achievable_mr) : null,
    };
  }, [data]);

  // The five-year decision ledger and the three key insights share one
  // derivation (../lib/keyInsights) with the scorecard.
  const ledgerRows = useMemo(() => roundLedger(history), [history]);
  const insights = useMemo(() => deriveKeyInsights(history), [history]);

  // Competitor desk.
  const competitor = useMemo(() => {
    const cEbitda = Number(data.competitor_ebitda);
    const rma = Number(data.relative_market_advantage);
    const ours = Number(data.terminal_ebitda);
    if (!Number.isFinite(cEbitda) && !peerRows.length) return null;
    return {
      cEbitda: Number.isFinite(cEbitda) ? cEbitda : null,
      ours: Number.isFinite(ours) ? ours : null,
      rma: Number.isFinite(rma) ? rma : null,
      warning: typeof data.competitor_warning === 'string' ? data.competitor_warning : null,
      rows: peerRows.filter((p) => p && Number.isFinite(Number(p.treasury))),
    };
  }, [data, peerRows]);

  // The chief executive's own closing entry — engine-authored, printed verbatim.
  const ceo = useMemo(() => {
    const d = data.ceo_diary;
    const entry = typeof d === 'string' ? d : d?.entry;
    if (typeof entry !== 'string' || !entry.trim()) return null;
    return { entry: entry.trim(), mood: d?.mood || null, label: d?.round_label || null };
  }, [data]);

  // The counterfactual the engine actually computed for the final decision.
  const regret = useMemo(() => {
    const r = data.decision_regret;
    const alts = r?.alternatives;
    if (!alts || typeof alts !== 'object') return null;
    const rows = Object.entries(alts)
      .map(([k, v]) => ({
        label: /^option_([a-z])$/i.test(k) ? `Option ${k.slice(-1).toUpperCase()}` : k,
        treasury: Number(v?.treasury_delta),
        rep: Number(v?.reputation_delta),
      }))
      .filter((x) => Number.isFinite(x.treasury) || Number.isFinite(x.rep));
    if (!rows.length) return null;
    const yours = typeof r.your_choice === 'string' && /^option_[a-z]$/i.test(r.your_choice)
      ? `Option ${r.your_choice.slice(-1).toUpperCase()}` : null;
    return { yours, rows };
  }, [data]);

  // Sustainability desk — real terminal indicators only.
  const esgRows = useMemo(() => {
    const rows = [];
    const push = (label, value) => { if (value !== null && value !== undefined) rows.push([label, value]); };
    if (Number.isFinite(Number(data.carbon_tonnage_group)))
      push('Group emissions', `${Number(data.carbon_tonnage_group).toFixed(0)} tCO₂e`);
    if (Number.isFinite(Number(data.carbon_cost)))
      push('Carbon cost borne', money(data.carbon_cost));
    if (Number.isFinite(Number(data.workforce_readiness)))
      push('Workforce readiness', `${Number(data.workforce_readiness).toFixed(0)}/100`);
    if (Number.isFinite(Number(data.avg_social_license)))
      push('Social licence', `${Number(data.avg_social_license).toFixed(0)}/100`);
    if (Number.isFinite(Number(data.synergy_score)))
      push('Cross-unit synergy', `${Number(data.synergy_score).toFixed(0)}/100`);
    if (Number.isFinite(Number(data.crisis_count_lifetime)))
      push('Crises weathered', `${Number(data.crisis_count_lifetime)}`);
    if (data.just_transition_passed === true || data.just_transition_passed === false)
      push('Just transition', data.just_transition_passed ? 'Passed' : 'Failed');
    if (data.greenwashing_risk_active === true) push('Greenwashing exposure', 'Flagged');
    if (data.equity_wiped_out === true) push('Shareholder equity', 'Wiped out');
    return rows;
  }, [data]);

  const chartNetAssets = useMemo(
    () => barChartSVG(series, 'netAssets', { title: 'NET ASSETS AT YEAR-END' }),
    [series],
  );
  const chartEbitda = useMemo(
    () => lineChartSVG(series, 'ebitda', { title: 'EBITDA BY YEAR' }),
    [series],
  );

  const download = useCallback(() => {
    const W = 1200;
    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const wrap = (s, n) => {
      const words = String(s).split(' '); const lines = []; let cur = '';
      for (const w of words) { if ((cur + ' ' + w).trim().length > n) { lines.push(cur.trim()); cur = w; } else cur += ' ' + w; }
      if (cur.trim()) lines.push(cur.trim()); return lines;
    };

    const headLines = wrap(tpl.headline(t), 34);
    const subLines = wrap(tpl.subhead(t), 82);
    const headBottom = 150 + headLines.length * 52 + subLines.length * 28 + 46;

    // ── Two newspaper columns ──
    const colL = 60, colR = 620, colW = 500;
    const paras = tpl.paras ? tpl.paras(t) : [];

    // Left column: article prose.
    let lyL = headBottom;
    const leftSvg = [];
    paras.forEach((p) => {
      wrap(p, 54).forEach((l) => {
        leftSvg.push(`<text x="${colL}" y="${lyL}" font-family="Georgia,serif" font-size="18" fill="#1a1a1a">${esc(l)}</text>`);
        lyL += 25;
      });
      lyL += 12;
    });
    // Ledger under the prose.
    const pushLedger = (label, text, color) => {
      wrap(`${label}  ${text}`, 56).forEach((l) => {
        leftSvg.push(`<text x="${colL}" y="${lyL}" font-family="Georgia,serif" font-size="16" fill="${color}">${esc(l)}</text>`);
        lyL += 22;
      });
      lyL += 6;
    };
    if (t.achievement || t.misstep) {
      leftSvg.push(`<line x1="${colL}" y1="${lyL - 14}" x2="${colL + colW}" y2="${lyL - 14}" stroke="#d8d2c4" stroke-width="1"/>`);
      if (t.achievement) pushLedger('▲ Major achievement:', t.achievement, '#0a7d3c');
      if (t.misstep)     pushLedger('▼ Major misstep:', t.misstep, '#b42318');
    }
    // The three key insights print on the keepsake too, when the run supports
    // them (same suppression rule as on screen — no data, no claim).
    if (insights) {
      lyL += 8;
      pushLedger('▲ Best round:',
        `R${insights.best.round}${insights.best.name ? ` ${insights.best.name}` : ''} — ${insights.best.choice || 'decision'} moved treasury ${fmtDeltaM(insights.best.delta)}.`,
        '#0a7d3c');
      pushLedger('▼ Costliest round:',
        `R${insights.worst.round}${insights.worst.name ? ` ${insights.worst.name}` : ''} — ${insights.worst.choice || 'decision'} moved treasury ${fmtDeltaM(insights.worst.delta)}.`,
        '#b42318');
    }

    // Right column: charts, numbers box, pull-quote.
    let lyR = headBottom - 18;
    const rightSvg = [];
    const chart1 = barChartSVG(series, 'netAssets', { w: 500, h: 220, title: 'NET ASSETS AT YEAR-END', x: colR, y: lyR });
    if (chart1) { rightSvg.push(chart1); lyR += 240; }
    const chart2 = lineChartSVG(series, 'ebitda', { w: 500, h: 200, title: 'EBITDA BY YEAR', x: colR, y: lyR });
    if (chart2) { rightSvg.push(chart2); lyR += 226; }

    rightSvg.push(`<rect x="${colR}" y="${lyR}" width="500" height="${numbersRows.length * 26 + 42}" fill="#ece7dc" stroke="#1a1a1a" stroke-width="1"/>`);
    rightSvg.push(`<text x="${colR + 16}" y="${lyR + 26}" font-family="Georgia,serif" font-size="14" font-weight="700" letter-spacing="0.08em" fill="#1a1a1a">BY THE NUMBERS</text>`);
    numbersRows.forEach(([k, v], i) => {
      rightSvg.push(`<text x="${colR + 16}" y="${lyR + 50 + i * 26}" font-family="Georgia,serif" font-size="16" fill="#444">${esc(k)}</text>`);
      rightSvg.push(`<text x="${colR + 484}" y="${lyR + 50 + i * 26}" text-anchor="end" font-family="Georgia,serif" font-size="16" font-weight="700" fill="#1a1a1a">${esc(v)}</text>`);
    });
    lyR += numbersRows.length * 26 + 58;

    const quoteLines = wrap(tpl.quote, 52);
    rightSvg.push(`<rect x="${colR}" y="${lyR}" width="500" height="${quoteLines.length * 26 + 44}" fill="#ece7dc" stroke="${esc(tpl.tone)}" stroke-width="2"/>`);
    quoteLines.forEach((l, i) => {
      rightSvg.push(`<text x="${colR + 16}" y="${lyR + 30 + i * 26}" font-family="Georgia,serif" font-size="18" font-style="italic" fill="#333">${esc(l)}</text>`);
    });
    rightSvg.push(`<text x="${colR + 16}" y="${lyR + 30 + quoteLines.length * 26 + 4}" font-family="Georgia,serif" font-size="14" fill="#777">— Independent market analyst</text>`);
    lyR += quoteLines.length * 26 + 66;

    const H = Math.max(920, lyL + 40, lyR + 40);

    const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#f4f1ea"/>
  <rect x="0" y="0" width="${W}" height="10" fill="${esc(tpl.tone)}"/>
  <text x="${W / 2}" y="70" text-anchor="middle" font-family="Georgia,serif" font-size="46" font-weight="800" fill="#1a1a1a">THE MURESSONS TIMES</text>
  <line x1="60" y1="92" x2="${W - 60}" y2="92" stroke="#1a1a1a" stroke-width="2"/>
  <text x="60" y="118" font-family="Georgia,serif" font-size="18" fill="#555">YEAR 5 · TERMINAL EDITION${cohortName ? ' · ' + esc(cohortName) : ''}</text>
  <text x="${W - 60}" y="118" text-anchor="end" font-family="Georgia,serif" font-size="18" fill="#555">Business · Front Page</text>
  <line x1="60" y1="132" x2="${W - 60}" y2="132" stroke="#ccc" stroke-width="1"/>
  ${headLines.map((l, i) => `<text x="60" y="${196 + i * 52}" font-family="Georgia,serif" font-size="44" font-weight="900" fill="#111">${esc(l)}</text>`).join('')}
  <text x="60" y="${186 + headLines.length * 52 + 24}" font-family="Georgia,serif" font-size="22" font-style="italic" fill="#333">${subLines.map((l, i) => `<tspan x="60" dy="${i === 0 ? 0 : 28}">${esc(l)}</tspan>`).join('')}</text>
  <text x="60" y="${headBottom - 22}" font-family="Georgia,serif" font-size="15" fill="#888">By ${esc(tpl.byline)}</text>
  <line x1="${(colL + colW + colR) / 2}" y1="${headBottom - 14}" x2="${(colL + colW + colR) / 2}" y2="${H - 40}" stroke="#d8d2c4" stroke-width="1"/>
  ${leftSvg.join('')}
  ${rightSvg.join('')}
</svg>`.trim();
    const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = W; c.height = H;
      c.getContext('2d').drawImage(img, 0, 0); URL.revokeObjectURL(url);
      c.toBlob((png) => {
        if (!png) return;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(png);
        a.download = `muressons-year5-frontpage.png`;
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      }, 'image/png');
    };
    img.onerror = () => URL.revokeObjectURL(url);
    img.src = url;
  }, [tpl, t, cohortName, series, numbersRows, insights]);

  if (!enabled) return null;

  const paras = tpl.paras ? tpl.paras(t) : [];
  const dateline = `YEAR 5 · TERMINAL EDITION${cohortName ? ` · ${cohortName}` : ''}`;

  /* ── The launcher. One line in the results stage; the paper itself lives in
        the overlay slot, so this feature takes no permanent screen space. ── */
  if (!open) {
    return (
      <div
        className="reveal-panel"
        style={{
          marginTop: 16, borderRadius: 12, overflow: 'hidden',
          border: '1px solid rgba(148,163,184,0.2)', background: '#f4f1ea',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 16, padding: '14px 20px', flexWrap: 'wrap',
        }}
      >
        <div style={{ fontFamily: 'Georgia, serif', color: '#111', minWidth: 240, flex: 1 }}>
          <div style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '0.02em' }}>
            THE MURESSONS TIMES
          </div>
          <div style={{ fontSize: '0.72rem', color: '#555', marginTop: 2 }}>
            {dateline} — your five-year debrief, in full
          </div>
        </div>
        <button
          type="button"
          onClick={() => setOpen(true)}
          style={{
            padding: '10px 20px', borderRadius: 8, cursor: 'pointer', fontWeight: 700,
            fontSize: '0.85rem', border: `2px solid ${tpl.tone}`, background: tpl.tone,
            color: '#0b1220', fontFamily: 'Georgia, serif', letterSpacing: '0.04em',
          }}
        >
          📰 Read the full edition
        </button>
      </div>
    );
  }

  return (
    <Dialog
      onClose={() => setOpen(false)}
      label="The Muressons Times — Year 5 terminal edition"
      className="fpr-paper"
      /* The paper IS the dialog surface, not a scrim over one — a backdrop
         click would be a click on the newspaper itself. */
      closeOnBackdrop={false}
      style={{
        position: 'fixed', inset: 0, zIndex: 9000, overflowY: 'auto',
        padding: '0 0 48px',
      }}
    >
      <style>{CSS}</style>

      {/* Close control — stays put while the paper scrolls */}
      <button
        type="button"
        onClick={() => setOpen(false)}
        aria-label="Close the edition"
        style={{
          position: 'fixed', top: 14, right: 18, zIndex: 2,
          padding: '8px 16px', borderRadius: 6, cursor: 'pointer', fontWeight: 700,
          fontSize: '0.8rem', fontFamily: 'Georgia, serif',
          border: '1px solid #1a1a1a', background: '#ece7dc', color: '#111',
        }}
      >
        ✕ Close  <span style={{ color: '#777', fontWeight: 400 }}>(Esc)</span>
      </button>

      <div style={{ maxWidth: 1680, margin: '0 auto', padding: '0 32px' }}>
        <div style={{ height: 8, background: tpl.tone, margin: '0 -32px 18px' }} />

        {/* ── Masthead ── */}
        <div style={{ textAlign: 'center', fontSize: '3rem', fontWeight: 800, letterSpacing: '0.02em', lineHeight: 1.05 }}>
          THE MURESSONS TIMES
        </div>
        <div style={{
          display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
          borderTop: '2px solid #111', borderBottom: '1px solid #ccc',
          padding: '6px 0', fontSize: '0.74rem', color: '#555', margin: '10px 0 18px',
        }}>
          <span>{dateline}</span>
          <span>Business · Special Report · Front Page</span>
        </div>

        {/* ── Splash headline, full width ── */}
        <h1 style={{ fontSize: '2.6rem', fontWeight: 900, lineHeight: 1.1, margin: '0 0 10px' }}>
          {tpl.headline(t)}
        </h1>
        <div style={{
          fontSize: '1.06rem', fontStyle: 'italic', color: '#333',
          borderBottom: '1px solid #d8d2c4', paddingBottom: 10, marginBottom: 6,
        }}>
          {tpl.subhead(t)}
        </div>
        <div style={{ fontSize: '0.74rem', color: '#888', margin: '8px 0 18px' }}>
          By {tpl.byline}
        </div>

        {/* ── Four-column broadsheet body ── */}
        <div className="fpr-body">
          {paras[0] && <p className="fpr-p fpr-drop">{paras[0]}</p>}
          {paras[1] && <p className="fpr-p">{paras[1]}</p>}

          {/* By the numbers */}
          <section className="fpr-sec">
            <h4>By the numbers</h4>
            {numbersRows.map(([k, v]) => (
              <div className="fpr-row" key={k}><span>{k}</span><strong>{v}</strong></div>
            ))}
          </section>

          {paras[2] && <p className="fpr-p">{paras[2]}</p>}

          {/* Terminal-year P&L */}
          {pnlRows.length > 0 && (
            <section className="fpr-sec">
              <h4>The terminal year</h4>
              {pnlRows.map(([k, v]) => (
                <div className="fpr-row" key={k}><span>{k}</span><strong>{v}</strong></div>
              ))}
              <div className="fpr-cap">Group totals as filed at the close of Year 5.</div>
            </section>
          )}

          {chartNetAssets && (
            <figure className="fpr-fig">
              <div dangerouslySetInnerHTML={{ __html: chartNetAssets.replace('<svg x="0" y="0"', '<svg style="width:100%;height:auto"') }} />
              <figcaption className="fpr-cap">Net assets at each year-end, Years 1–5. Source: group statement of financial position.</figcaption>
            </figure>
          )}

          {paras[3] && <p className="fpr-p">{paras[3]}</p>}

          {/* ── THE DEBRIEF: ten rounds, as decided ── */}
          {ledgerRows.length > 0 && (
            <section className="fpr-sec">
              <h4>The five-year decision ledger</h4>
              <table className="fpr-tbl">
                <thead>
                  <tr><th>Rd</th><th>Agenda</th><th>Call</th><th className="n">Treasury</th><th className="n">Change</th></tr>
                </thead>
                <tbody>
                  {ledgerRows.map((r) => (
                    <tr key={r.round}>
                      <td>{r.round}</td>
                      <td>{r.name || '—'}</td>
                      <td>{r.choice || '—'}</td>
                      <td className="n">{money(r.treasury)}</td>
                      <td className="n" style={{ color: Number.isFinite(r.delta) ? (r.delta < 0 ? '#b42318' : '#0a7d3c') : '#888' }}>
                        {Number.isFinite(r.delta) ? fmtDeltaM(r.delta) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="fpr-cap">
                Closing treasury after each round, as recorded by the group. Round 1 shows no
                change because the period opens at that close.
              </div>
            </section>
          )}

          {/* ── THREE KEY INSIGHTS ── */}
          {insights && (
            <section className="fpr-sec" style={{ borderWidth: 2 }}>
              <h4>Inside the numbers: three key insights</h4>

              <div style={{ marginBottom: 9 }}>
                <div style={{ fontWeight: 700, color: '#0a7d3c', fontSize: '0.78rem' }}>
                  ▲ Best round — Round {insights.best.round}
                  {insights.best.name ? `: ${insights.best.name}` : ''}
                </div>
                <div style={{ fontSize: '0.80rem' }}>
                  {insights.best.choice ? `${insights.best.choice} ` : 'The board’s call '}
                  moved the treasury {fmtDeltaM(insights.best.delta)}, the strongest single-round
                  swing of the plan.
                </div>
              </div>

              <div style={{ marginBottom: 9 }}>
                <div style={{ fontWeight: 700, color: '#b42318', fontSize: '0.78rem' }}>
                  ▼ Costliest round — Round {insights.worst.round}
                  {insights.worst.name ? `: ${insights.worst.name}` : ''}
                </div>
                <div style={{ fontSize: '0.80rem' }}>
                  {insights.worst.choice ? `${insights.worst.choice} ` : 'The board’s call '}
                  moved the treasury {fmtDeltaM(insights.worst.delta)} — the deepest drawdown on
                  the ledger.
                </div>
              </div>

              {insights.swing && (
                <div>
                  <div style={{ fontWeight: 700, color: '#7c4dff', fontSize: '0.78rem' }}>
                    ◆ Sharpest reputation swing — Round {insights.swing.round}
                    {insights.swing.name ? `: ${insights.swing.name}` : ''}
                  </div>
                  <div style={{ fontSize: '0.80rem' }}>
                    Group reputation moved from {insights.swing.from.toFixed(0)} to{' '}
                    {insights.swing.reputation.toFixed(0)} out of 100
                    {' '}({insights.swing.change >= 0 ? '+' : '−'}{Math.abs(insights.swing.change).toFixed(0)} points).
                  </div>
                </div>
              )}

              <div className="fpr-cap">
                Computed from the round-by-round treasury and reputation record of this run.
              </div>
            </section>
          )}

          {chartEbitda && (
            <figure className="fpr-fig">
              <div dangerouslySetInnerHTML={{ __html: chartEbitda.replace('<svg x="0" y="0"', '<svg style="width:100%;height:auto"') }} />
              <figcaption className="fpr-cap">Group EBITDA by year. Source: company reports.</figcaption>
            </figure>
          )}

          {/* ── MARKET DESK: the competition ── */}
          {competitor && (
            <section className="fpr-sec">
              <h4>Market desk: how rivals fared</h4>

              {competitor.rows.length > 0 && (
                <>
                  <table className="fpr-tbl">
                    <thead>
                      <tr><th>#</th><th>Group</th><th className="n">Treasury</th><th className="n">Rep.</th><th className="n">tCO₂e</th></tr>
                    </thead>
                    <tbody>
                      {competitor.rows.map((p, i) => (
                        <tr key={`${p.name}-${i}`} style={p.isYou ? { fontWeight: 700, background: '#e2dccd' } : undefined}>
                          <td>{p.rank ?? i + 1}</td>
                          <td>{p.name}{p.isYou ? ' ◂' : ''}</td>
                          <td className="n">{money(p.treasury)}</td>
                          <td className="n">{Number.isFinite(Number(p.reputation)) ? Number(p.reputation).toFixed(0) : '—'}</td>
                          <td className="n">{Number.isFinite(Number(p.co2)) ? Number(p.co2).toFixed(0) : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className="fpr-cap">Cohort standings at the terminal reading.</div>
                </>
              )}

              {competitor.cEbitda !== null && (
                <div style={{ marginTop: 9, borderTop: '1px solid #cfc8b8', paddingTop: 7 }}>
                  <div className="fpr-row">
                    <span>Market competitor EBITDA</span><strong>{money(competitor.cEbitda)}</strong>
                  </div>
                  {competitor.ours !== null && (
                    <div className="fpr-row"><span>Muressons EBITDA</span><strong>{money(competitor.ours)}</strong></div>
                  )}
                  {competitor.rma !== null && (
                    <div className="fpr-row">
                      <span>Relative advantage</span>
                      <strong style={{ color: competitor.rma < 0 ? '#b42318' : '#0a7d3c' }}>
                        {competitor.rma >= 0 ? '+' : '−'}{Math.abs(competitor.rma).toFixed(2)}×
                      </strong>
                    </div>
                  )}
                </div>
              )}

              {competitor.warning && (
                <div className="fpr-cap" style={{ marginTop: 6 }}>{competitor.warning}</div>
              )}
            </section>
          )}

          {/* ── FROM THE CHIEF EXECUTIVE ── */}
          {ceo && (
            <section className="fpr-sec" style={{ borderLeft: `4px solid ${tpl.tone}` }}>
              <h4>From the chief executive</h4>
              <p style={{ margin: 0, fontStyle: 'italic', fontSize: '0.86rem', lineHeight: 1.6 }}>
                “{ceo.entry}”
              </p>
              <div className="fpr-cap" style={{ marginTop: 6 }}>
                — Chief Executive, Muressons Group
                {ceo.label ? `, on the ${ceo.label}` : ''}
                {ceo.mood ? ` · tone recorded as ${ceo.mood}` : ''}. Reproduced from the
                executive diary.
              </div>
            </section>
          )}

          {/* ── VALUATION LEDGER (M_R attribution) ── */}
          {mrLines && (
            <section className="fpr-sec">
              <h4>How the multiple was built</h4>
              {mrLines.base !== null && (
                <div className="fpr-row"><span>Base</span><strong>{mrLines.base.toFixed(2)}×</strong></div>
              )}
              {mrLines.lines.map(([label, v]) => (
                <div className="fpr-row" key={label}>
                  <span>{label}</span>
                  <strong style={{ color: v < 0 ? '#b42318' : '#0a7d3c' }}>
                    {v >= 0 ? '+' : '−'}{Math.abs(v).toFixed(2)}
                  </strong>
                </div>
              ))}
              <div className="fpr-row" style={{ borderBottom: 'none', marginTop: 4 }}>
                <span style={{ fontWeight: 700, color: '#111' }}>Final multiple</span>
                <strong>{t.mr}×</strong>
              </div>
              {mrLines.max !== null && (
                <div className="fpr-cap">
                  Maximum achievable on this run: {mrLines.max.toFixed(2)}×.
                </div>
              )}
            </section>
          )}

          {/* ── SUSTAINABILITY DESK ── */}
          {esgRows.length > 0 && (
            <section className="fpr-sec">
              <h4>Sustainability desk</h4>
              {esgRows.map(([k, v]) => (
                <div className="fpr-row" key={k}><span>{k}</span><strong>{v}</strong></div>
              ))}
              <div className="fpr-cap">Terminal indicators as reported by the group.</div>
            </section>
          )}

          {/* ── THE ROAD NOT TAKEN (engine-computed counterfactual) ── */}
          {regret && (
            <section className="fpr-sec">
              <h4>The road not taken</h4>
              <div style={{ fontSize: '0.78rem', marginBottom: 6 }}>
                {regret.yours
                  ? `The board went with ${regret.yours} in the final round. The alternatives modelled:`
                  : 'The alternatives modelled for the final round:'}
              </div>
              <table className="fpr-tbl">
                <thead>
                  <tr><th>Path</th><th className="n">Treasury</th><th className="n">Reputation</th></tr>
                </thead>
                <tbody>
                  {regret.rows.map((r) => (
                    <tr key={r.label}>
                      <td>{r.label}</td>
                      <td className="n">{Number.isFinite(r.treasury) ? fmtDeltaM(r.treasury) : '—'}</td>
                      <td className="n">
                        {Number.isFinite(r.rep) ? `${r.rep >= 0 ? '+' : '−'}${Math.abs(r.rep).toFixed(0)}` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="fpr-cap">Counterfactual outcomes computed by the group’s own planning model.</div>
            </section>
          )}

          {/* ── Pull-quote ── */}
          <div className="fpr-sec" style={{ borderLeft: `4px solid ${tpl.tone}`, fontStyle: 'italic', fontSize: '0.92rem', color: '#333' }}>
            {tpl.quote}
            <div className="fpr-cap" style={{ fontStyle: 'normal' }}>— Independent market analyst</div>
          </div>
        </div>

        {/* ── Five-year ledger footer, full width ── */}
        {(t.achievement || t.misstep) && (
          <div style={{
            marginTop: 18, paddingTop: 14, borderTop: '2px solid #111',
            display: 'flex', flexWrap: 'wrap', gap: 18, fontSize: '0.92rem', lineHeight: 1.55,
          }}>
            {t.achievement && (
              <div style={{ flex: '1 1 380px' }}>
                <strong style={{ color: '#0a7d3c' }}>▲ Major achievement:</strong> {t.achievement}
              </div>
            )}
            {t.misstep && (
              <div style={{ flex: '1 1 380px' }}>
                <strong style={{ color: '#b42318' }}>▼ Major misstep:</strong> {t.misstep}
              </div>
            )}
          </div>
        )}

        <div style={{
          marginTop: 22, paddingTop: 14, borderTop: '1px solid #d8d2c4',
          display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap',
        }}>
          <button onClick={download} style={{
            padding: '10px 20px', borderRadius: 6, cursor: 'pointer', fontWeight: 700,
            fontSize: '0.85rem', fontFamily: 'Georgia, serif',
            border: '1px solid #1a1a1a', background: '#ece7dc', color: '#111',
          }}>📰 Download the front page (PNG)</button>
          <button onClick={() => setOpen(false)} style={{
            padding: '10px 20px', borderRadius: 6, cursor: 'pointer', fontWeight: 700,
            fontSize: '0.85rem', fontFamily: 'Georgia, serif',
            border: `1px solid ${tpl.tone}`, background: tpl.tone, color: '#0b1220',
          }}>Back to the scorecard</button>
        </div>

        <div style={{ textAlign: 'center', fontSize: '0.66rem', color: '#8a8a8a', marginTop: 16 }}>
          Every figure in this edition is taken from your own run. Where a measure was not
          recorded, it is shown as “—” rather than estimated.
        </div>
      </div>
    </Dialog>
  );
}
