'use client';
import React, { useState, useEffect, useMemo, useCallback } from 'react';

/**
 * FrontPageReveal (Feature 5) — a Year-5 "front page" for the team, generated
 * from their real result. Deterministic per-archetype templates (works with no
 * LLM key), rendered as newsprint and exportable as a branded PNG (SVG→canvas,
 * same pattern as ArchetypeCard). Gated by the facilitator's `front_page_enabled`
 * setting; renders nothing when disabled.
 *
 * Props: sessionId, data (the game-over data object), cohortName.
 */

// Bands keyed to the M_R archetype thresholds in terminal_valuation.py.
function bandFor(mr) {
  if (mr >= 1.8) return 'titan';
  if (mr >= 1.2) return 'safe';
  if (mr >= 0.8) return 'fragile';
  return 'relic';
}

const TEMPLATES = {
  titan: {
    tone: '#10b981',
    headline: (t) => `MURESSONS CROWNED SUSTAINABILITY LEADER OF THE DECADE`,
    subhead: (t) => `Regenerative strategy compounds into a $${t.tvM}M valuation as the board's five-year bet pays off`,
    quote: `"A textbook case that decarbonisation and value creation are the same story."`,
    byline: 'Markets Desk',
    bullets: (t) => [
      `Enterprise value closes at $${t.tvM}M on a ${t.mr}× Regenerative Multiple`,
      `Share price of $${t.price} rewards a decade of disciplined ESG capital allocation`,
      `Analysts cite resilience investments and stakeholder trust as the durable moat`,
    ],
  },
  safe: {
    tone: '#3b82f6',
    headline: (t) => `MURESSONS DELIVERS STEADY, DE-RISKED RETURNS`,
    subhead: (t) => `A pragmatic five years leaves the group well-capitalised at $${t.tvM}M with room to push further`,
    quote: `"Solid, defensible, and unspectacular — exactly what nervous boards asked for."`,
    byline: 'Corporate Affairs',
    bullets: (t) => [
      `Enterprise value of $${t.tvM}M on a ${t.mr}× Regenerative Multiple`,
      `Share price steadies at $${t.price}; balance sheet carries limited climate risk`,
      `Commentators note upside left on the table from deferred green investment`,
    ],
  },
  fragile: {
    tone: '#f59e0b',
    headline: (t) => `QUESTIONS MOUNT OVER MURESSONS' RESILIENCE`,
    subhead: (t) => `A $${t.tvM}M valuation masks a fragile ${t.mr}× multiple as deferred costs come due`,
    quote: `"The bill for short-termism arrives late, larger, and with fewer options."`,
    byline: 'Risk & Regulation',
    bullets: (t) => [
      `Enterprise value of $${t.tvM}M sits on a thin ${t.mr}× Regenerative Multiple`,
      `Share price of $${t.price} prices in elevated transition and reputational risk`,
      `Investors press for a credible plan before the next crisis window`,
    ],
  },
  relic: {
    tone: '#ef4444',
    headline: (t) => `MURESSONS FACES STRANDED-ASSET RECKONING`,
    subhead: (t) => `Five years of extraction leave a ${t.mr}× multiple and a valuation under pressure at $${t.tvM}M`,
    quote: `"A cautionary tale of value destroyed one deferred decision at a time."`,
    byline: 'Investigations',
    bullets: (t) => [
      `Enterprise value of $${t.tvM}M reflects a distressed ${t.mr}× Regenerative Multiple`,
      `Share price of $${t.price} signals eroded social licence and governance risk`,
      `Regulators and activists circle as the transition runway narrows`,
    ],
  },
};

export default function FrontPageReveal({ sessionId, data = {}, cohortName = '' }) {
  const [enabled, setEnabled] = useState(true); // default show; disable only if facilitator turned it off
  // WOW-5E: LLM-enhanced copy (falls back to deterministic)
  const [llmCopy, setLlmCopy] = useState(null);

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

  const t = useMemo(() => {
    const mr = Number(data.regenerative_multiple) || 0;
    return {
      mr: mr.toFixed(2),
      tvM: ((Number(data.terminal_value) || 0) / 1_000_000).toFixed(1),
      price: data.price_per_share != null ? Number(data.price_per_share).toFixed(2) : '—',
    };
  }, [data]);

  const band = bandFor(Number(data.regenerative_multiple) || 0);
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

  const download = useCallback(() => {
    const W = 1200, H = 900;
    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const bullets = tpl.bullets(t);
    const wrap = (s, n) => {
      const words = String(s).split(' '); const lines = []; let cur = '';
      for (const w of words) { if ((cur + ' ' + w).trim().length > n) { lines.push(cur.trim()); cur = w; } else cur += ' ' + w; }
      if (cur.trim()) lines.push(cur.trim()); return lines;
    };
    const headLines = wrap(tpl.headline(t), 26);
    const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#f4f1ea"/>
  <rect x="0" y="0" width="${W}" height="10" fill="${esc(tpl.tone)}"/>
  <text x="${W / 2}" y="70" text-anchor="middle" font-family="Georgia,serif" font-size="46" font-weight="800" fill="#1a1a1a">THE MURESSONS TIMES</text>
  <line x1="60" y1="92" x2="${W - 60}" y2="92" stroke="#1a1a1a" stroke-width="2"/>
  <text x="60" y="118" font-family="Georgia,serif" font-size="18" fill="#555">YEAR 5 · TERMINAL EDITION${cohortName ? ' · ' + esc(cohortName) : ''}</text>
  <text x="${W - 60}" y="118" text-anchor="end" font-family="Georgia,serif" font-size="18" fill="#555">Business · Front Page</text>
  <line x1="60" y1="132" x2="${W - 60}" y2="132" stroke="#ccc" stroke-width="1"/>
  ${headLines.map((l, i) => `<text x="60" y="${200 + i * 60}" font-family="Georgia,serif" font-size="52" font-weight="900" fill="#111">${esc(l)}</text>`).join('')}
  <text x="60" y="${210 + headLines.length * 60}" font-family="Georgia,serif" font-size="24" font-style="italic" fill="#333">${wrap(tpl.subhead(t), 78).map((l, i) => `<tspan x="60" dy="${i === 0 ? 0 : 30}">${esc(l)}</tspan>`).join('')}</text>
  <text x="60" y="${300 + headLines.length * 60}" font-family="Georgia,serif" font-size="16" fill="#888">By the ${esc(tpl.byline)}</text>
  ${bullets.map((b, i) => `<text x="60" y="${360 + headLines.length * 60 + i * 40}" font-family="Georgia,serif" font-size="21" fill="#222">• ${esc(b)}</text>`).join('')}
  <rect x="60" y="${500 + headLines.length * 60}" width="${W - 120}" height="90" fill="#ece7dc" stroke="${esc(tpl.tone)}" stroke-width="2"/>
  <text x="80" y="${540 + headLines.length * 60}" font-family="Georgia,serif" font-size="24" font-style="italic" fill="#333">${esc(tpl.quote)}</text>
  <text x="80" y="${572 + headLines.length * 60}" font-family="Georgia,serif" font-size="16" fill="#777">— Independent market analyst</text>
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
  }, [tpl, t, cohortName]);

  if (!enabled) return null;

  return (
    <div style={{ marginTop: 16, borderRadius: 12, overflow: 'hidden', border: '1px solid rgba(148,163,184,0.2)' }}>
      <div style={{ background: '#f4f1ea', color: '#111', padding: '20px 24px', fontFamily: 'Georgia, serif' }}>
        <div style={{ height: 6, background: tpl.tone, margin: '-20px -24px 14px' }} />
        <div style={{ textAlign: 'center', fontSize: '1.9rem', fontWeight: 800, letterSpacing: '0.02em' }}>THE MURESSONS TIMES</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '2px solid #111', borderBottom: '1px solid #ccc', padding: '6px 0', fontSize: '0.75rem', color: '#555', margin: '8px 0 16px' }}>
          <span>YEAR 5 · TERMINAL EDITION{cohortName ? ` · ${cohortName}` : ''}</span>
          <span>Business · Front Page</span>
        </div>
        <div style={{ fontSize: '1.9rem', fontWeight: 900, lineHeight: 1.1, marginBottom: 10 }}>{tpl.headline(t)}</div>
        <div style={{ fontSize: '1.05rem', fontStyle: 'italic', color: '#333', marginBottom: 6 }}>{tpl.subhead(t)}</div>
        <div style={{ fontSize: '0.75rem', color: '#888', marginBottom: 12 }}>By the {tpl.byline}</div>
        <ul style={{ margin: 0, paddingLeft: 20, fontSize: '0.95rem', color: '#222', lineHeight: 1.6 }}>
          {tpl.bullets(t).map((b, i) => <li key={i}>{b}</li>)}
        </ul>
        <div style={{ marginTop: 14, padding: '12px 16px', background: '#ece7dc', borderLeft: `3px solid ${tpl.tone}`, fontStyle: 'italic', fontSize: '0.95rem', color: '#333' }}>
          {tpl.quote}<div style={{ fontSize: '0.75rem', color: '#777', marginTop: 4 }}>— Independent market analyst</div>
        </div>
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
