'use client';
import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { currencySymbol, setCurrencySymbol, setCurrencyRate } from '../utils/format';


const API = process.env.NEXT_PUBLIC_API_URL || '';

// ─── Currency catalogue ───────────────────────────────────────────
export const CURRENCIES = [
  { symbol: '₹',  code: 'INR', label: 'Rupee',          flag: '🇮🇳' },
  { symbol: '$',  code: 'USD', label: 'US Dollar',       flag: '🇺🇸' },
  { symbol: '£',  code: 'GBP', label: 'Pound',           flag: '🇬🇧' },
  { symbol: '€',  code: 'EUR', label: 'Euro',            flag: '🇪🇺' },
  { symbol: '¥',  code: 'JPY', label: 'Yen',             flag: '🇯🇵' },
  // CNY must NOT reuse the bare '¥' — currency is persisted and looked up BY
  // SYMBOL (CURRENCIES.find(c => c.symbol === sym)), so a shared glyph makes a
  // Chinese-Yuan cohort resolve back to the first '¥' match (JPY). 'CN¥'
  // disambiguates the renminbi while staying legible on KPIs/reports.
  { symbol: 'CN¥', code: 'CNY', label: 'Chinese Yuan',    flag: '🇨🇳' },
];

export const DEFAULT_CURRENCY = CURRENCIES[0]; // ₹ INR

// ─── Context ──────────────────────────────────────────────────────
const CurrencyContext = createContext({
  currency: DEFAULT_CURRENCY,
  setCurrency: () => {},
  loadSessionCurrency: async () => {},
  formatAmount: (n) => `${currencySymbol()}${n}`,
});

// ─── Helpers ──────────────────────────────────────────────────────
function buildFormatter(symbol) {
  return (value, { abbreviate = true, decimals } = {}) => {
    if (value === null || value === undefined || isNaN(value)) return '—';
    const abs = Math.abs(value);
    const neg = value < 0 ? '-' : '';

    if (abbreviate) {
      if (abs >= 1_000_000_000) {
        const d = decimals !== undefined ? decimals : 2;
        return `${neg}${symbol}${(abs / 1_000_000_000).toFixed(d)}B`;
      }
      if (abs >= 1_000_000) {
        const d = decimals !== undefined ? decimals : 2;
        return `${neg}${symbol}${(abs / 1_000_000).toFixed(d)}M`;
      }
      if (abs >= 1_000) {
        const d = decimals !== undefined ? decimals : 1;
        return `${neg}${symbol}${(abs / 1_000).toFixed(d)}K`;
      }
    }
    const d = decimals !== undefined ? decimals : 0;
    return `${neg}${symbol}${abs.toFixed(d)}`;
  };
}

// ─── Provider ────────────────────────────────────────────────────
export function CurrencyProvider({ children }) {
  const [currency, setCurrencyState] = useState(DEFAULT_CURRENCY);

  /* Push the active symbol down to utils/format.js. Those are plain functions —
     called from module scope and from non-React helpers — so they cannot read a
     hook. This effect is the ONLY writer, which is what makes the symbol single-
     sourced: before it, formatCurrency.js hard-coded '$' and a rupee cohort saw
     both glyphs on one screen. */
  useEffect(() => { setCurrencySymbol(currency?.symbol); }, [currency]);
  // NEW-09: Once a session-specific currency is loaded, lock it so the god-mode
  // global-settings fetch cannot silently overwrite it on re-mount between rounds.
  const sessionCurrencyLockedRef = useRef(false);

  // Load global fallback from server on mount (God Mode default)
  // Only applies when no session-specific currency has been established.
  useEffect(() => {
    if (sessionCurrencyLockedRef.current) return;
    fetch(`${API}/api/admin/global-settings`)
      .then(r => r.json())
      .then(d => {
        if (sessionCurrencyLockedRef.current) return; // race-guard
        const sym = d.currency_symbol;
        if (sym) {
          const found = CURRENCIES.find(c => c.symbol === sym);
          if (found) setCurrencyState(found);
        }
      })
      .catch(() => {});
  }, []);

  // Manually set currency + persist to global-settings (God Mode / Engine Tunables)
  const setCurrency = useCallback((curr) => {
    setCurrencyState(curr);
    fetch(`${API}/api/admin/global-settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ currency_symbol: curr.symbol }),
    }).catch(() => {});
  }, []);

  /**
   * loadSessionCurrency(sessionId)
   * Called by player-facing components after they know their session ID.
   * Fetches the cohort's currency_symbol from the session-info API and
   * overrides the in-memory currency for this browser session only —
   * does NOT change the global God Mode setting.
   */
  const loadSessionCurrency = useCallback(async (sessionId) => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${API}/api/simulations/${sessionId}/session-info`);
      if (res.ok) {
        const data = await res.json();
        // Prefer the parent cohort's currency if this is a player sub-session
        const sym = data.currency_symbol || data.parent_currency_symbol;
        if (sym) {
          const found = CURRENCIES.find(c => c.symbol === sym);
          if (found) {
            setCurrencyState(found);
            // NEW-09: Lock currency to cohort setting — prevents god-mode from overwriting
            sessionCurrencyLockedRef.current = true;
          }
        }
        /* THE RATE, from the same payload as the symbol.
           Deliberately NOT gated on the symbol being recognised: a cohort can
           set a rate for a currency that is not in the CURRENCIES list, and
           tying the two together would silently drop the conversion while
           keeping the glyph — which is the exact defect the rate exists to fix,
           reintroduced one level up.

           setCurrencyRate refuses anything non-finite or <= 0, so a missing,
           null or malformed field leaves the previous rate standing rather
           than zeroing every figure in the product. */
        const rate = data.currency_rate ?? data.parent_currency_rate;
        if (rate != null) setCurrencyRate(rate);
      }
    } catch { /* silently keep current default */ }
  }, []);

  const formatAmount = buildFormatter(currency.symbol);

  return (
    <CurrencyContext.Provider value={{ currency, setCurrency, loadSessionCurrency, formatAmount, currencies: CURRENCIES }}>
      {children}
    </CurrencyContext.Provider>
  );
}

// ─── Consumer hook ───────────────────────────────────────────────
export function useCurrency() {
  return useContext(CurrencyContext);
}

// ─── Standalone formatter (for use outside React tree) ──────────
export function formatWithSymbol(symbol, value, opts) {
  return buildFormatter(symbol)(value, opts);
}
