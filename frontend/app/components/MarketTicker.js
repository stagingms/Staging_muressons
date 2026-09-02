'use client';
import { useState, useEffect, useMemo, useRef } from 'react';
import { calculateRoundStockPrice, IPO_PRICE } from './stockValuationEngine';

/**
 * MarketTicker — Enhanced scrolling stock ticker bar.
 *
 * A11Y-F15 (WCAG 1.4.3) — real-browser pass, 2026-08-02.
 * This strip is PERMANENTLY BLACK: `bg` below is '#000000' with no theme
 * branch, in both themes, by design — it is the trading-terminal ribbon.
 * Its text was nevertheless drawn from theme-dependent sources, so in light
 * mode the whole ticker went black-on-black:
 *   symbol  var(--neutral)      -> #334155 on #000000 = 2.03:1
 *   price   '#e2e8f0' inline    -> caught by the globals.css light shim,
 *                                  rewritten to var(--text-primary) = 1:1
 *   delta   var(--positive-text)-> #15803d on the pale-green chip = 3.70:1
 * 16 nodes, every number on the bar, invisible. The old header claimed the
 * component "supports dark and light themes"; it does not, and should not —
 * a surface that never changes needs a palette that never changes.
 *
 * The palette therefore lives in the component's own <style> block as
 * classes, not as inline colours: inline is exactly what the light-mode shim
 * pattern-matches on, and a class it cannot see cannot be rewritten.
 *
 * W-A (W1): the ticker is now LIVE. Every symbol is derived from real engine
 * state already on the client (globalState / history / businessUnits props) —
 * no Math.random, no static symbols, no new fetches. Deltas are true
 * round-over-round moves: current derived state vs the last committed round
 * in `history` (MURS anchors to the IPO price before the first commit).
 * Display-only: reads props, never writes game state.
 */

// Derive per-round core metrics from a global_state + business_units pair.
// Fallback definitions are IDENTICAL to ExecutiveCockpit / stock chart:
//   ebitda  = historical_ebitda            || Σ(revenue − opex)
//   tco2e   = max(0, tco2e_emissions > 0 ? it : Σ(CI × revenue / 1e6))
function deriveMetrics(gs, bus) {
  const g = gs || {};
  const list = bus || [];
  if (!gs && list.length === 0) return null;
  const ebitda = g.historical_ebitda ||
    (list.reduce((acc, bu) => acc + (bu.revenue_base || 0) - (bu.opex_base || 0), 0) || 0);
  const rawT = g.tco2e_emissions;
  const tco2e = Math.max(
    0,
    (rawT != null && rawT > 0)
      ? rawT
      : (list.reduce((acc, bu) => acc + ((bu.carbon_intensity || 0) * (bu.revenue_base || 0)) / 1_000_000, 0) || 0)
  );
  const avgNCD = list.length
    ? list.reduce((s, bu) => s + (bu.natural_capital_debt || 0), 0) / list.length
    : 0;
  const reputation = g.group_reputation || 50;
  const wacc = g.cost_of_capital || 0.05;
  const inflation = g.inflation_index || 0;
  const carbonFee = g.carbon_fee_per_ton ?? g.internal_carbon_fee_rate ?? 15;
  const greenFund = g.green_transition_fund || 0;
  const price = calculateRoundStockPrice({
    ebitda,
    synergy_multiplier: g.synergy_multiplier || 1.0,
    natural_capital_debt: avgNCD,
    group_reputation: reputation,
    cost_of_capital: wacc,
    exit_multiple: g.active_event_flags?.valuation_preview?.exit_multiple ?? null,  // F-17
  });
  return { ebitda, tco2e, reputation, wacc, inflation, carbonFee, greenFund, price };
}

export default function MarketTicker({ roundNumber = 1, globalState, history, businessUnits }) {
  const scrollRef = useRef(null);
  // Phase B (F-P7): ambient theatrics yield to concentration — the ticker
  // dims while the allocation/commit stage is open. The cockpit flags the
  // stage on <html data-allocation-open>; observed here with the same
  // MutationObserver pattern this file already uses for theming.
  const [dimmed, setDimmed] = useState(false);

  // W1: build the symbol list from real engine state. Recomputes only when
  // committed state changes (globalState updates after round advance), so the
  // ticker visibly "prints" the consequences of the previous commit.
  const items = useMemo(() => {
    const cur = deriveMetrics(globalState, businessUnits);
    if (!cur) return [];
    const prevH = (history || []).length ? history[history.length - 1] : null;
    const prev = prevH ? deriveMetrics(prevH.global_state, prevH.business_units) : null;

    const pct = (now, before) =>
      (before == null || before === 0) ? null : ((now - before) / Math.abs(before)) * 100;
    const fmtPct = (v) => (v == null ? null : `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`);

    const out = [];
    // MURS — real share price (macro valuation engine) vs last committed round
    const prevPrice = prev ? prev.price : IPO_PRICE;
    const dPrice = pct(cur.price, prevPrice);
    out.push({ symbol: 'MURS', price: `$${cur.price.toFixed(2)}`, change: fmtPct(dPrice), rising: (dPrice ?? 0) >= 0, good: (dPrice ?? 0) >= 0 });
    // ESG Sentiment Index — reputation-scaled composite (rep 50 = 1,000)
    const dEsg = prev ? pct(cur.reputation, prev.reputation) : null;
    out.push({ symbol: 'ESG Index', price: Math.round(cur.reputation * 20).toLocaleString(), change: fmtPct(dEsg), rising: (dEsg ?? 0) >= 0, good: (dEsg ?? 0) >= 0 });
    // Internal carbon fee actually charged by the engine each round
    const dFee = prev ? pct(cur.carbonFee, prev.carbonFee) : null;
    out.push({ symbol: 'Carbon $/t', price: `$${Number(cur.carbonFee).toFixed(2)}`, change: fmtPct(dFee), rising: (dFee ?? 0) >= 0, good: (dFee ?? 0) <= 0 });
    // WACC print — falling is good (rating-linked cost of capital)
    const dWacc = prev ? (cur.wacc - prev.wacc) * 10000 : null;
    out.push({ symbol: 'WACC', price: `${(cur.wacc * 100).toFixed(1)}%`, change: dWacc == null ? null : `${dWacc >= 0 ? '+' : ''}${Math.round(dWacc)}bps`, rising: (dWacc ?? 0) >= 0, good: (dWacc ?? 0) <= 0 });
    // CPI — engine inflation print (fractional index → %); falling is good
    const dCpi = prev ? (cur.inflation - prev.inflation) * 100 : null;
    out.push({ symbol: 'CPI', price: `${(cur.inflation * 100).toFixed(1)}%`, change: dCpi == null ? null : `${dCpi >= 0 ? '+' : ''}${dCpi.toFixed(1)}pp`, rising: (dCpi ?? 0) >= 0, good: (dCpi ?? 0) <= 0 });
    // Green Transition Fund balance (accrues from internal carbon taxation)
    const dGf = prev ? pct(cur.greenFund, prev.greenFund) : null;
    out.push({ symbol: 'Green Fund', price: `$${(cur.greenFund / 1_000_000).toFixed(1)}M`, change: fmtPct(dGf), rising: (dGf ?? 0) >= 0, good: (dGf ?? 0) >= 0 });
    // Group emissions — falling is good (pill colour inverts)
    const dCo2 = prev ? pct(cur.tco2e, prev.tco2e) : null;
    out.push({ symbol: 'tCO₂e', price: Math.round(cur.tco2e).toLocaleString(), change: fmtPct(dCo2), rising: (dCo2 ?? 0) >= 0, good: (dCo2 ?? 0) <= 0 });
    // Group EBITDA print
    const dEb = prev ? pct(cur.ebitda, prev.ebitda) : null;
    out.push({ symbol: 'EBITDA', price: `$${(cur.ebitda / 1_000_000).toFixed(1)}M`, change: fmtPct(dEb), rising: (dEb ?? 0) >= 0, good: (dEb ?? 0) >= 0 });

    return [...out, ...out]; // duplicate for seamless scroll
  }, [globalState, businessUnits, history]);

  // A11Y-F15: the theme observer that used to live here is gone with the
  // theme-dependent colours it fed. `isDark` had already stopped being read
  // by anything that renders — keeping an observer that re-renders the bar on
  // every theme flip, for a bar that is black in both themes, would only
  // reintroduce the belief that this surface follows the theme.

  // Phase B: observe the allocation flag set by ExecutiveCockpit
  useEffect(() => {
    const check = () => setDimmed(document.documentElement.hasAttribute('data-allocation-open'));
    check();
    const obs = new MutationObserver(check);
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-allocation-open'] });
    return () => obs.disconnect();
  }, []);

  const bg = '#000000';
  const border = '1px solid rgba(255, 255, 255, 0.08)';
  const fadeL = 'linear-gradient(90deg, #000000, transparent)';
  const fadeR = 'linear-gradient(270deg, #000000, transparent)';
  /* Contrast against the fixed #000 strip, measured in Chromium:
       .tkSym   #cbd5e1 -> 13.6:1
       .tkPrice #e2e8f0 -> 16.0:1
       .tkUp    #4ade80 on rgba(74,222,128,0.1) over #000  -> 10.8:1
       .tkDown  #f87171 on rgba(248,113,113,0.1) over #000 ->  7.6:1 */

  if (items.length === 0) return null;

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, height: 32,
      background: bg,
      borderTop: border,
      overflow: 'hidden', zIndex: 7000,
      fontFamily: 'var(--font-numeral)',
      display: 'flex', alignItems: 'center',
      opacity: dimmed ? 0.35 : 1,
      transition: 'background 0.3s ease, border-color 0.3s ease, opacity 0.4s ease',
    }}>
      {/* Left fade edge */}
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0, width: 60,
        background: fadeL,
        zIndex: 2, pointerEvents: 'none',
      }} />
      {/* Right fade edge */}
      <div style={{
        position: 'absolute', right: 0, top: 0, bottom: 0, width: 60,
        background: fadeR,
        zIndex: 2, pointerEvents: 'none',
      }} />

      <div
        ref={scrollRef}
        className="tickerScrollRow"
        style={{
          display: 'flex', gap: 8,
          animation: 'tickerScroll 45s linear infinite',
          whiteSpace: 'nowrap',
          paddingLeft: 60,
        }}
      >
        {items.map((item, i) => (
          <span key={i} style={{
            fontSize: 'var(--type-caption)', fontWeight: 600,
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}>
            <span className="tkSym" style={{ fontWeight: 700, letterSpacing: '0.02em' }}>
              {item.symbol}
            </span>
            <span className="tkPrice" style={{ fontVariantNumeric: 'tabular-nums' }}>
              {item.price}
            </span>
            {/* Pill badge for change — colour = good/bad, arrow = direction.
                (For emissions/WACC/CPI a falling print renders green.) */}
            {item.change != null && (
              <span className={item.good ? 'tkUp' : 'tkDown'} style={{
                fontSize: 'var(--type-caption)',
                fontWeight: 700,
                borderRadius: 3,
                padding: '1px 5px',
              }}>
                {item.rising ? '▲' : '▼'} {item.change}
              </span>
            )}
            {/* Separator dot. Pure decoration — it carries no information a
                sighted user gets either, so it is hidden from assistive tech
                rather than recoloured. WCAG 1.4.3 exempts pure decoration;
                lifting its hue would be a restyle of the strip's rhythm. */}
            {i < items.length - 1 && (
              <span aria-hidden="true" className="tkDot" style={{
                fontSize: 'var(--type-caption)', margin: '0 4px',
              }}>●</span>
            )}
          </span>
        ))}
      </div>
      <style>{`
        @keyframes tickerScroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        @media (prefers-reduced-motion: reduce) {
          .tickerScrollRow { animation: none !important; }
        }
        /* A11Y-F15: theme-invariant, because the strip is theme-invariant.
           Deliberately NOT tokens and NOT inline — a token follows the theme
           this surface does not have, and an inline colour is what the
           light-mode shim in globals.css rewrites. */
        .tkSym   { color: #cbd5e1; }
        .tkPrice { color: #e2e8f0; }
        .tkDot   { color: rgba(148, 163, 184, 0.3); }
        .tkUp    { color: #4ade80; background: rgba(74, 222, 128, 0.1); border: 1px solid rgba(74, 222, 128, 0.25); }
        .tkDown  { color: #f87171; background: rgba(248, 113, 113, 0.1); border: 1px solid rgba(248, 113, 113, 0.25); }
      `}</style>
    </div>
  );
}
