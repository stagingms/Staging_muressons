'use client';
import React, { useState, useEffect, useMemo, useCallback } from 'react';

/**
 * FrontPageReveal (Feature 5) — a Year-5 "front page" for the team, generated
 * from their real result, laid out like a real broadsheet: title-case
 * headline, dateline prose flowing in two columns, a "By the Numbers"
 * sidebar, and two newsprint charts (net assets by year, EBITDA trend)
 * drawn from the session's balance-sheet history. Deterministic
 * per-archetype templates (works with no LLM key); LLM copy, when
 * available, overrides headline/subhead/quote only. Exportable as a
 * branded PNG (SVG→canvas). Gated by `front_page_enabled`.
 *
 * Slot: results stage (game-over view) — retrospective content (V-A).
 *
 * Props: sessionId, data (the game-over data object), cohortName.
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

function bandFor(mr, d = {}) {
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
  else if (price != null && price >= 50) achievement = `Shareholders rewarded with a $${Number(price).toFixed(2)} share price on a well-capitalised balance sheet.`;
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

const fmtM = (v) => {
  const m = v / 1_000_000;
  const a = Math.abs(m);
  return `${m < 0 ? '−' : ''}$${a >= 100 ? a.toFixed(0) : a.toFixed(1)}M`;
};

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

const TEMPLATES = {
  titan: {
    tone: '#10b981',
    byline: 'A. Renard, Markets Correspondent',
    headline: (t) => `Muressons' Regenerative Bet Pays Off as Valuation Reaches $${t.tvM}M`,
    subhead: (t) => `Five years after the board tied executive pay to natural-capital targets, the conglomerate's ${t.mr}× multiple is the sector benchmark`,
    quote: `"They proved the thesis: decarbonisation and value creation were the same project all along."`,
    paras: (t) => [
      `MURESSONS CITY — The Muressons Group closed the books on its five-year transformation programme with a terminal enterprise value of $${t.tvM}M, capping a period in which the conglomerate turned aggressive sustainability spending into the strongest valuation multiple among its peers.`,
      `The group's ${t.mr}× regenerative multiple — a measure investors now use to price resilience as much as earnings — reflects early, sustained capital allocation into decarbonisation, supply-chain hardening and workforce transition. Shares ended the period at $${t.price}.`,
      `Rivals that deferred the same investments spent the back half of the plan absorbing crisis costs Muressons had already engineered out. Fund managers described the result as "compounding by another name."`,
      `The board is expected to extend the programme into a second five-year horizon, with analysts pressing for detail on how the group protects its lead as the premium it earned becomes the market's baseline.`,
    ],
  },
  safe: {
    tone: '#3b82f6',
    byline: 'S. Okafor, Corporate Affairs Desk',
    headline: (t) => `Muressons Closes Five-Year Plan With Steady Returns, Thinner Green Pipeline`,
    subhead: (t) => `A $${t.tvM}M valuation on a ${t.mr}× multiple rewards caution — and prices in the investments the group chose not to make`,
    quote: `"Solid, defensible, unspectacular. The question is what they compound from here."`,
    paras: (t) => [
      `MURESSONS CITY — The Muressons Group reported a terminal enterprise value of $${t.tvM}M on Friday, ending its five-year plan with the de-risked balance sheet management promised — and with questions about the growth it traded away to get there.`,
      `The group's ${t.mr}× regenerative multiple places it comfortably above distressed peers but short of the sector's leaders, a gap analysts attribute to green-infrastructure investments that were studied, budgeted and then deferred. Shares closed the period at $${t.price}.`,
      `Executives defend the record: crisis rounds that forced write-downs elsewhere passed with limited damage, and the group enters the next cycle with headroom rather than obligations. "We kept our options open," one senior manager said.`,
      `The counter-argument is already circulating in investor notes: options have expiry dates, and the premium for early movers has widened every year of the plan.`,
    ],
  },
  insolvent: {
    tone: '#a855f7',
    byline: 'D. Vasquez, Markets Desk',
    headline: (t) => `Debt Overhang Wipes Out Muressons Shareholders Despite $${t.tvM}M Valuation`,
    subhead: (t) => `The headline enterprise value survives; the equity beneath it does not, once ${'netDebtM' in t && t.netDebtM !== '—' ? `$${t.netDebtM}M of net debt` : 'the debt stack'} is settled`,
    quote: `"Impressive at the top line, hollow underneath — the equity was gone before the valuation printed."`,
    paras: (t) => [
      `MURESSONS CITY — On paper, the Muressons Group ends its five-year plan valued at $${t.tvM}M. For its shareholders, the arithmetic is crueller: after the group's accumulated borrowings are netted off, the equity is worth effectively nothing, and the shares closed the period at $${t.price}.`,
      `The pattern will be familiar to restructuring specialists. Operating ambitions — some of them genuinely regenerative, reflected in a ${t.mr}× multiple — were funded with debt rather than earnings, and the balance sheet quietly inverted while the strategy narrative held the spotlight.`,
      `Creditors, not owners, now hold the economics of the enterprise. Bondholders are expected to drive any recapitalisation, with existing equity heavily diluted or extinguished in most scenarios bankers describe.`,
      `The lesson traders drew was blunt: a sustainability premium on the multiple cannot outrun a funding model that mortgages the equity to pay for it.`,
    ],
  },
  fragile: {
    tone: '#f59e0b',
    byline: 'R. Whitfield, Risk & Regulation',
    headline: (t) => `Muressons' Five-Year Report Leaves Analysts Asking What Holds in the Next Storm`,
    subhead: (t) => `A $${t.tvM}M valuation rests on a thin ${t.mr}× multiple as deferred transition costs begin to come due`,
    quote: `"The bill for short-termism arrives late, larger, and with fewer options attached."`,
    paras: (t) => [
      `MURESSONS CITY — The Muressons Group ended its five-year programme with a terminal enterprise value of $${t.tvM}M, a result the group presented as stability and the market read as fragility. Shares closed the period at $${t.price}.`,
      `The concern is concentrated in the group's ${t.mr}× regenerative multiple, which sits close enough to breakeven that a single stranded-asset ruling, remediation order or reputational shock could tip the valuation into discount territory.`,
      `Institutional holders spent the final quarters pressing for a credible transition plan with dates and capital attached, rather than the sequence of pilots and reviews that characterised the middle years of the plan.`,
      `The group has runway, analysts concede — but it is measured in quarters now, not years, and the next crisis window will not negotiate.`,
    ],
  },
  relic: {
    tone: '#ef4444',
    byline: 'M. Adeyemi, Investigations',
    headline: (t) => `Stranded Assets, Shrinking Options: Muressons Ends the Era Under Pressure`,
    subhead: (t) => `Five years of extraction leave a ${t.mr}× multiple, a $${t.tvM}M valuation under sustained pressure, and a narrowing path back`,
    quote: `"A cautionary tale of value destroyed one deferred decision at a time."`,
    paras: (t) => [
      `MURESSONS CITY — The Muressons Group closed its five-year plan in the position its critics predicted at the outset: carbon-heavy assets written down, social licence eroded, and a valuation — $${t.tvM}M at the terminal reading — that reflects a ${t.mr}× multiple deep in distressed territory. Shares ended the period at $${t.price}.`,
      `Internal documents reviewed across the period show a consistent pattern: transition investments scoped, costed and shelved, with the savings booked to earnings that the market has since clawed back several times over.`,
      `Regulators are circling the remediation ledger, activist holders are demanding board changes, and the insurers who once priced the group as an industrial stalwart now price it as a liability book.`,
      `Whatever emerges from the coming restructuring will be smaller, greener by necessity, and — in the phrase one adviser used — "a company that pays for the decade it declined to fund."`,
    ],
  },
};

export default function FrontPageReveal({ sessionId, data = {}, cohortName = '' }) {
  const [enabled, setEnabled] = useState(true); // default show; disable only if facilitator turned it off
  // WOW-5E: LLM-enhanced copy (falls back to deterministic)
  const [llmCopy, setLlmCopy] = useState(null);
  // Year-by-year figures for the pictorial charts (balance-sheet history).
  const [series, setSeries] = useState([]);

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

  const t = useMemo(() => {
    const mr = Number(data.regenerative_multiple) || 0;
    const ledger = deriveLedger(data);
    return {
      mr: mr.toFixed(2),
      tvM: ((Number(data.terminal_value) || 0) / 1_000_000).toFixed(1),
      price: data.price_per_share != null ? Number(data.price_per_share).toFixed(2) : '—',
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

  const numbersRows = useMemo(() => ([
    ['Enterprise value', `$${t.tvM}M`],
    ['Regenerative multiple', `${t.mr}×`],
    ['Share price', t.price === '—' ? '—' : `$${t.price}`],
    ['Equity value', t.eqM === '—' ? '—' : `$${t.eqM}M`],
    ['Net debt', t.netDebtM === '—' ? '—' : `$${t.netDebtM}M`],
    ['Group reputation', t.rep === '—' ? '—' : `${t.rep}/100`],
  ]), [t]);

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
  }, [tpl, t, cohortName, series, numbersRows]);

  if (!enabled) return null;

  const paras = tpl.paras ? tpl.paras(t) : [];
  const figStyle = { breakInside: 'avoid', margin: '4px 0 14px', padding: '10px 10px 6px', background: '#efeade', border: '1px solid #d8d2c4' };
  const capStyle = { fontSize: '0.68rem', color: '#777', marginTop: 4, fontStyle: 'italic' };

  return (
    /* Move 4: shares the reveal language — the newsprint settles in on the
       same signature ease as every other wow moment. */
    <div className="reveal-panel" style={{ marginTop: 16, borderRadius: 12, overflow: 'hidden', border: '1px solid rgba(148,163,184,0.2)' }}>
      <div style={{ background: '#f4f1ea', color: '#111', padding: '20px 24px', fontFamily: 'Georgia, serif' }}>
        <div style={{ height: 6, background: tpl.tone, margin: '-20px -24px 14px' }} />
        <div className="reveal-headline" style={{ textAlign: 'center', fontSize: '1.9rem', fontWeight: 800, letterSpacing: '0.02em' }}>THE MURESSONS TIMES</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '2px solid #111', borderBottom: '1px solid #ccc', padding: '6px 0', fontSize: '0.75rem', color: '#555', margin: '8px 0 16px' }}>
          <span>YEAR 5 · TERMINAL EDITION{cohortName ? ` · ${cohortName}` : ''}</span>
          <span>Business · Front Page</span>
        </div>

        {/* Headline block spans both columns, like a real splash */}
        <div style={{ fontSize: '2rem', fontWeight: 900, lineHeight: 1.12, marginBottom: 10 }}>{tpl.headline(t)}</div>
        <div style={{ fontSize: '1.02rem', fontStyle: 'italic', color: '#333', marginBottom: 6, borderBottom: '1px solid #d8d2c4', paddingBottom: 10 }}>{tpl.subhead(t)}</div>
        <div style={{ fontSize: '0.75rem', color: '#888', margin: '8px 0 14px' }}>By {tpl.byline}</div>

        {/* Two-column newspaper body: prose flows around inset figures */}
        <div style={{ columnCount: 2, columnGap: 28, columnRule: '1px solid #d8d2c4', fontSize: '0.93rem', lineHeight: 1.62, color: '#1a1a1a', textAlign: 'justify' }}>
          {paras[0] && <p style={{ margin: '0 0 12px' }}>{paras[0]}</p>}
          {paras[1] && <p style={{ margin: '0 0 12px' }}>{paras[1]}</p>}

          {chartNetAssets && (
            <figure style={figStyle}>
              <div dangerouslySetInnerHTML={{ __html: chartNetAssets.replace('<svg x="0" y="0"', '<svg style="width:100%;height:auto"') }} />
              <figcaption style={capStyle}>Net assets at each year-end, Years 1–5. Source: group statement of financial position.</figcaption>
            </figure>
          )}

          {paras[2] && <p style={{ margin: '0 0 12px' }}>{paras[2]}</p>}

          {chartEbitda && (
            <figure style={figStyle}>
              <div dangerouslySetInnerHTML={{ __html: chartEbitda.replace('<svg x="0" y="0"', '<svg style="width:100%;height:auto"') }} />
              <figcaption style={capStyle}>Group EBITDA by year. Source: company reports.</figcaption>
            </figure>
          )}

          {paras[3] && <p style={{ margin: '0 0 12px' }}>{paras[3]}</p>}

          {/* By the Numbers box */}
          <div style={{ breakInside: 'avoid', margin: '4px 0 14px', padding: '12px 14px', background: '#ece7dc', border: '1px solid #1a1a1a' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.1em', marginBottom: 8 }}>BY THE NUMBERS</div>
            {numbersRows.map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '2px 0', borderBottom: '1px dotted #cfc8b8' }}>
                <span style={{ color: '#444' }}>{k}</span>
                <strong>{v}</strong>
              </div>
            ))}
          </div>

          {/* Pull-quote */}
          <div style={{ breakInside: 'avoid', margin: '4px 0 12px', padding: '12px 16px', background: '#ece7dc', borderLeft: `3px solid ${tpl.tone}`, fontStyle: 'italic', fontSize: '0.95rem', color: '#333' }}>
            {tpl.quote}
            <div style={{ fontSize: '0.72rem', color: '#777', marginTop: 4 }}>— Independent market analyst</div>
          </div>
        </div>

        {/* Five-year ledger footer, full width */}
        {(t.achievement || t.misstep) && (
          <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid #d8d2c4', display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.9rem', color: '#1a1a1a', lineHeight: 1.5 }}>
            {t.achievement && <div><strong style={{ color: '#0a7d3c' }}>▲ Major achievement:</strong> {t.achievement}</div>}
            {t.misstep && <div><strong style={{ color: '#b42318' }}>▼ Major misstep:</strong> {t.misstep}</div>}
          </div>
        )}
      </div>
      <div style={{ textAlign: 'center', padding: '10px', background: 'var(--bg-card, #161e2e)' }}>
        <button onClick={download} style={{
          padding: '8px 18px', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: '0.85rem',
          border: `1px solid ${tpl.tone}`, background: `${tpl.tone}22`, color: 'var(--text-primary, #f1f5f9)',
        }}>📰 Download your Year-5 front page</button>
      </div>
    </div>
  );
}
