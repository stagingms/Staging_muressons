'use client';
import { useState, useEffect, useRef } from 'react';

/**
 * MarketTicker — Enhanced scrolling stock ticker bar.
 * Supports dark (default) and light themes.
 */

const BASE_ITEMS = [
  { symbol: 'MURS', price: '42.50', change: '+2.3%', up: true },
  { symbol: 'ESG Index', price: '1,247', change: '-0.8%', up: false },
  { symbol: 'Carbon Credit', price: '€45.20', change: '+1.2%', up: true },
  { symbol: 'EU Taxonomy', price: '72%', change: '+0.5%', up: true },
  { symbol: 'Water Futures', price: '$128', change: '-2.1%', up: false },
  { symbol: 'Green Bond', price: '$98.40', change: '+0.3%', up: true },
  { symbol: 'S&P Clean', price: '3,891', change: '+1.8%', up: true },
  { symbol: 'Pharma ETF', price: '$62.30', change: '-0.4%', up: false },
];

export default function MarketTicker({ roundNumber = 1 }) {
  const scrollRef = useRef(null);
  const [items, setItems] = useState([]);
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    // Randomize prices slightly based on round
    const randomized = BASE_ITEMS.map(item => {
      const delta = (Math.random() - 0.5) * 4;
      const isUp = delta > 0;
      return {
        ...item,
        change: `${isUp ? '+' : ''}${delta.toFixed(1)}%`,
        up: isUp,
      };
    });
    setItems([...randomized, ...randomized]); // duplicate for seamless scroll
  }, [roundNumber]);

  // Listen for theme changes
  useEffect(() => {
    const checkTheme = () => {
      const theme = document.documentElement.getAttribute('data-theme');
      setIsDark(theme !== 'light');
    };
    checkTheme();
    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  const bg = '#000000';
  const border = '1px solid rgba(255, 255, 255, 0.08)';
  const fadeL = 'linear-gradient(90deg, #000000, transparent)';
  const fadeR = 'linear-gradient(270deg, #000000, transparent)';
  const symColor = '#94a3b8';
  const priceColor = '#e2e8f0';
  const dotColor = 'rgba(148, 163, 184, 0.3)';

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, height: 32,
      background: bg,
      borderTop: border,
      overflow: 'hidden', zIndex: 7000,
      fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
      display: 'flex', alignItems: 'center',
      transition: 'background 0.3s ease, border-color 0.3s ease',
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
        style={{
          display: 'flex', gap: 8,
          animation: 'tickerScroll 45s linear infinite',
          whiteSpace: 'nowrap',
          paddingLeft: 60,
        }}
      >
        {items.map((item, i) => (
          <span key={i} style={{
            fontSize: '0.66rem', fontWeight: 600,
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}>
            <span style={{ color: symColor, fontWeight: 700, letterSpacing: '0.02em' }}>
              {item.symbol}
            </span>
            <span style={{ color: priceColor, fontVariantNumeric: 'tabular-nums' }}>
              {item.price}
            </span>
            {/* Pill badge for change */}
            <span style={{
              color: item.up ? '#4ade80' : '#f87171',
              fontSize: '0.68rem',
              fontWeight: 700,
              background: item.up ? 'rgba(74, 222, 128, 0.1)' : 'rgba(248, 113, 113, 0.1)',
              border: `1px solid ${item.up ? 'rgba(74, 222, 128, 0.25)' : 'rgba(248, 113, 113, 0.25)'}`,
              borderRadius: 3,
              padding: '1px 5px',
            }}>
              {item.up ? '▲' : '▼'} {item.change}
            </span>
            {/* Separator dot */}
            {i < items.length - 1 && (
              <span style={{
                color: dotColor, fontSize: '0.5rem', margin: '0 4px',
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
      `}</style>
    </div>
  );
}
