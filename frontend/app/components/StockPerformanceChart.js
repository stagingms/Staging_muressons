'use client';

import { useMemo, useState, useCallback } from 'react';
import {
  ComposedChart, Area, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { buildFullStockData, IPO_PRICE } from './stockValuationEngine';
import { roundToQuarter, roundRangeLabel } from '../utils/roundToQuarter';
import styles from './StockPerformanceChart.module.css';

/**
 * StockPerformanceChart — Premium stock terminal card.
 *
 * Two-tiered system:
 *  - Macro Engine: deterministic stock price per round
 *  - Micro Engine: 20 stochastic daily interpolated points per round
 *
 * Props:
 *  - historyData:    Array of { round, ebitda, reputation, ... }
 *  - globalState:    current global state object
 *  - businessUnits:  current BU array
 *  - roundNumber:    current round
 *  - events:         current round engine events
 *  - projectedCost:  projected treasury delta (for header display)
 *  - peerStockData:  Array of { round, price } for peer comparison overlay
 *  - peerLabel:      Label for the peer line (e.g. 'AI Benchmark Avg')
 */

const RANGE_FILTERS = [
  { label: 'Y1: Q1–Q4', minRound: 1, maxRound: 4 },
  { label: 'Y2: Q1–Q4', minRound: 5, maxRound: 8 },
  { label: 'Y3: Q1–Q2', minRound: 9, maxRound: 10 },
  { label: 'ALL', minRound: 0, maxRound: 10 },
];

// Custom tooltip
function StockTooltip({ active, payload, peerLabel }) {
  if (!active || !payload?.length) return null;
  const data = payload[0].payload;
  const roundLabel = data.round === 0
    ? 'IPO'
    : roundToQuarter(data.round).label;

  const playerEntry = payload.find(p => p.dataKey === 'price');
  const peerEntry = payload.find(p => p.dataKey === 'peerPrice');

  return (
    <div className={styles.tooltipContainer}>
      <div className={styles.tooltipLabel}>{roundLabel}</div>
      {playerEntry && (
        <div className={styles.tooltipPrice}>
          Your Stock: ${playerEntry.value?.toFixed(2) || '—'}
        </div>
      )}
      {peerEntry && peerEntry.value != null && (
        <div className={styles.tooltipPeer} style={{ color: '#fb923c', fontSize: 11, marginTop: 2 }}>
          {peerLabel || 'Peer Avg'}: ${peerEntry.value?.toFixed(2) || '—'}
        </div>
      )}
    </div>
  );
}

export default function StockPerformanceChart({
  historyData = [],
  globalState,
  businessUnits = [],
  roundNumber = 1,
  events,
  projectedCost = 0,
  peerStockData = null,
  peerLabel = null,
}) {
  const [activeRange, setActiveRange] = useState('ALL');

  // Build full stochastic stock ticker data
  const fullData = useMemo(
    () => buildFullStockData(historyData, globalState, businessUnits, roundNumber, events),
    [historyData, globalState, businessUnits, roundNumber, events],
  );

  // Merge peer stock data into the full data
  // Peer data has one price per round — we place it at the last day of each round
  const fullDataWithPeer = useMemo(() => {
    if (!peerStockData || peerStockData.length === 0) return fullData;

    const peerMap = {};
    peerStockData.forEach(p => { peerMap[p.round] = p.price; });

    // Find the last data point for each round and attach peer price
    const lastDayPerRound = {};
    fullData.forEach((d, idx) => {
      lastDayPerRound[d.round] = idx;
    });

    return fullData.map((d, idx) => {
      if (lastDayPerRound[d.round] === idx && peerMap[d.round] != null) {
        return { ...d, peerPrice: peerMap[d.round] };
      }
      return d;
    });
  }, [fullData, peerStockData]);

  // Current price = last data point
  const currentPrice = fullDataWithPeer.length > 0 ? fullDataWithPeer[fullDataWithPeer.length - 1].price : IPO_PRICE;
  const prevPrice = fullDataWithPeer.length > 1 ? fullDataWithPeer[fullDataWithPeer.length - 2].price : IPO_PRICE;
  const priceDelta = currentPrice - IPO_PRICE;
  const pctChange = IPO_PRICE > 0 ? ((currentPrice - IPO_PRICE) / IPO_PRICE * 100) : 0;

  // Filter data by range
  const filteredData = useMemo(() => {
    const filter = RANGE_FILTERS.find(f => f.label === activeRange);
    if (!filter || filter.label === 'ALL') return fullDataWithPeer;
    return fullDataWithPeer.filter(d => d.round >= filter.minRound && d.round <= filter.maxRound);
  }, [fullDataWithPeer, activeRange]);

  // Y-axis domain: padded min/max with 50 baseline visible
  const yDomain = useMemo(() => {
    if (filteredData.length === 0) return [40, 60];
    const prices = filteredData.map(d => d.price);
    const peerPrices = filteredData.filter(d => d.peerPrice != null).map(d => d.peerPrice);
    const allPrices = [...prices, ...peerPrices, IPO_PRICE];
    const min = Math.min(...allPrices);
    const max = Math.max(...allPrices);
    const padding = (max - min) * 0.15 || 5;
    return [Math.max(0, Math.floor(min - padding)), Math.ceil(max + padding)];
  }, [filteredData]);

  // Format price for axis
  const fmtPrice = useCallback((v) => `$${Number(v).toFixed(0)}`, []);

  // X-axis tick formatter: show round labels
  const fmtXAxis = useCallback((val) => {
    // val is the 'day' from the dataKey
    const point = filteredData.find(d => d.day === val);
    if (!point) return '';
    if (point.round === 0) return 'IPO';
    return point.label || '';
  }, [filteredData]);

  // Build custom ticks: only the day indices that carry a year label
  const xTicks = useMemo(() => {
    const ticks = [];
    for (const d of filteredData) {
      if (d.round === 0 || d.label) ticks.push(d.day);
    }
    return ticks;
  }, [filteredData]);

  const hasPeer = peerStockData && peerStockData.length > 0;

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <span className={styles.title}>📈 Stock Performance</span>
      </div>

      {/* Price + Delta (compact) */}
      <div className={styles.priceDisplay}>
        <span className={styles.currentPrice}>${currentPrice.toFixed(2)}</span>
        <span className={`${styles.priceDelta} ${priceDelta >= 0 ? styles.deltaUp : styles.deltaDown}`}>
          {priceDelta >= 0 ? '▲' : '▼'} {pctChange >= 0 ? '+' : ''}{pctChange.toFixed(1)}%
        </span>
      </div>

      {/* Range Selectors */}
      <div className={styles.rangeBar}>
        {RANGE_FILTERS.map(f => (
          <button
            key={f.label}
            className={`${styles.rangeBtn} ${activeRange === f.label ? styles.rangeBtnActive : ''}`}
            onClick={() => setActiveRange(f.label)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className={styles.chartArea}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={filteredData}
            margin={{ top: 4, right: 4, bottom: 0, left: 0 }}
          >
            <defs>
              <linearGradient id="stockGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.45} />
                <stop offset="40%" stopColor="#2563eb" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#1e40af" stopOpacity={0.03} />
              </linearGradient>
            </defs>

            <XAxis
              dataKey="day"
              tick={{ fontSize: 8, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={fmtXAxis}
              ticks={xTicks}
            />

            <YAxis
              domain={yDomain}
              tick={{ fontSize: 8, fill: '#1e293b' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={fmtPrice}
              width={32}
            />

            <Tooltip content={<StockTooltip peerLabel={peerLabel} />} />

            {/* IPO Baseline */}
            <ReferenceLine
              y={IPO_PRICE}
              stroke="rgba(148, 163, 184, 0.3)"
              strokeDasharray="4 4"
              label={{
                value: `IPO $${IPO_PRICE}`,
                position: 'right',
                fontSize: 8,
                fill: '#64748b',
              }}
            />

            {/* Stock price area + line */}
            <Area
              type="monotone"
              dataKey="price"
              stroke="#60a5fa"
              strokeWidth={2}
              fill="url(#stockGrad)"
              dot={false}
              activeDot={{
                r: 3,
                fill: '#2563eb',
                stroke: '#0f1524',
                strokeWidth: 2,
              }}
            />

            {/* Peer stock price overlay (dashed amber line) */}
            {hasPeer && (
              <Line
                type="monotone"
                dataKey="peerPrice"
                name={peerLabel || 'Peer Avg'}
                stroke="#fb923c"
                strokeWidth={1.8}
                strokeDasharray="6 3"
                dot={{ r: 3, fill: '#fb923c', strokeWidth: 0 }}
                connectNulls={true}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
