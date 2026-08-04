'use client';
import React, { useCallback } from 'react';
import { currencySymbol } from '../utils/format';

/**
 * ArchetypeCard (wow feature) — one-click branded PNG the team keeps.
 * Builds a 1200×630 social-share card (archetype, M_R, enterprise value, share
 * price) entirely client-side (SVG → canvas → PNG), so it needs no backend and
 * no libraries. Extends the sim's life past the room.
 *
 * Props: title, icon, mr, terminalValueM (in $M), sharePrice, accent (hex),
 *        cohortName (optional).
 */
export default function ArchetypeCard({
  title = 'Corporate Archetype',
  icon = '🏢',
  mr = 0,
  terminalValueM = 0,
  sharePrice = null,
  equityWiped = null,   // explicit backend signal (equity_wiped_out); preferred
  accent = '#10b981',
  cohortName = '',
}) {
  // ── Equity-truth override ────────────────────────────────────────────────
  // A shareable card must never headline a flattering archetype over an
  // insolvent outcome. The backend archetype can stay "De-risked" on a positive
  // DMAV while net debt has already wiped out equity. The honest signal is the
  // backend's `equity_wiped_out` flag (equity value < 0). NOTE: the reported
  // share price is now FLOORED at $1 (a stock can't quote negative), so we no
  // longer infer insolvency from the price sign — we rely on the flag, falling
  // back to `sharePrice < 0` only for older payloads that predate the flag.
  const priceNum   = sharePrice != null ? Number(sharePrice) : null;
  const isEquityWiped = equityWiped != null
    ? !!equityWiped
    : (priceNum != null && priceNum < 0);
  const evM         = Number(terminalValueM) || 0;

  let dTitle = title, dIcon = icon, dAccent = accent;
  if (isEquityWiped) {
    if (evM > 0) { dTitle = 'Hollow Idealist'; dIcon = '🕯️'; dAccent = '#a855f7'; }
    else         { dTitle = 'Stranded Relic';  dIcon = '💀'; dAccent = '#ef4444'; }
  }
  // Share-price stat colour, consistent with the scorecard's thresholds.
  const priceColor = priceNum == null ? '#f1f5f9'
    : priceNum >= 50 ? '#10b981'
    : priceNum >= 30 ? '#f59e0b'
    : '#ef4444';

  const download = useCallback(() => {
    const W = 1200, H = 630;
    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const price = priceNum != null ? `${currencySymbol()}${priceNum.toFixed(2)}` : '—';
    const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0a0e1a"/>
      <stop offset="1" stop-color="#161e2e"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="28%" r="60%">
      <stop offset="0" stop-color="${esc(accent)}" stop-opacity="0.22"/>
      <stop offset="1" stop-color="${esc(accent)}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="${W}" height="${H}" fill="url(#bg)"/>
  <rect width="${W}" height="${H}" fill="url(#glow)"/>
  <rect x="8" y="8" width="${W - 16}" height="${H - 16}" rx="24" fill="none" stroke="${esc(dAccent)}" stroke-opacity="0.35" stroke-width="2"/>
  <text x="60" y="86" font-family="'DM Sans',Arial,sans-serif" font-size="26" letter-spacing="4" fill="#8899a6">MURESSONS GLOBAL · YEAR 5 TERMINAL VALUATION</text>
  <text x="600" y="250" text-anchor="middle" font-size="120">${esc(dIcon)}</text>
  <text x="600" y="340" text-anchor="middle" font-family="'DM Sans',Arial,sans-serif" font-weight="800" font-size="64" fill="#f1f5f9">${esc(dTitle)}</text>
  ${isEquityWiped ? `<text x="600" y="384" text-anchor="middle" font-family="'DM Sans',Arial,sans-serif" font-weight="700" font-size="24" letter-spacing="2" fill="#ef4444">EQUITY WIPED OUT · SHARE PRICE COLLAPSED</text>` : ''}
  ${cohortName ? `<text x="600" y="${isEquityWiped ? 416 : 384}" text-anchor="middle" font-family="'DM Sans',Arial,sans-serif" font-size="26" fill="#b0bec5">${esc(cohortName)}</text>` : ''}
  <g font-family="'DM Sans',Arial,sans-serif" text-anchor="middle">
    <text x="300" y="500" font-size="52" font-weight="800" fill="${esc(dAccent)}">${Number(mr).toFixed(2)}×</text>
    <text x="300" y="536" font-size="22" fill="#8899a6">Regenerative Multiple</text>
    <text x="600" y="500" font-size="52" font-weight="800" fill="#f1f5f9">${currencySymbol()}${Number(terminalValueM).toFixed(1)}M</text>
    <text x="600" y="536" font-size="22" fill="#8899a6">Enterprise Value</text>
    <text x="900" y="500" font-size="52" font-weight="800" fill="${esc(priceColor)}">${esc(price)}</text>
    <text x="900" y="536" font-size="22" fill="#8899a6">Share Price</text>
  </g>
</svg>`.trim();

    const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = W; canvas.height = H;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      canvas.toBlob((png) => {
        if (!png) return;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(png);
        a.download = `muressons-${dTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.png`;
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      }, 'image/png');
    };
    img.onerror = () => URL.revokeObjectURL(url);
    img.src = url;
  }, [dTitle, dIcon, mr, terminalValueM, priceNum, priceColor, dAccent, isEquityWiped, cohortName]);

  return (
    <button
      onClick={download}
      style={{
        marginTop: 14, padding: '10px 20px', borderRadius: 10, cursor: 'pointer',
        border: `1px solid ${dAccent}`, background: `${dAccent}22`, color: 'var(--text-primary, #f1f5f9)',
        fontWeight: 700, fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', gap: 8,
      }}
      title="Download a shareable PNG of your final archetype"
    >
      🖼️ Download your archetype card
    </button>
  );
}
