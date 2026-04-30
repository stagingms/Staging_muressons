import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

export default function CompetitorIntelligence({ globalState, ebitda, roundNumber }) {
  const competitorEbitda = globalState?.competitor_ebitda || ebitda;
  const isTrailing = ebitda < competitorEbitda;

  const data = [
    { name: 'You', value: ebitda, fill: '#6366f1' },
    { name: 'Competitor', value: competitorEbitda, fill: '#f43f5e' }
  ];

  const fmtM = (v) => `$${(v / 1_000_000).toFixed(1)}M`;
  const ratio = (ebitda / (competitorEbitda || 1)).toFixed(2);
  const isTied = ratio === '1.00';

  // DV-03: Don't show misleading data before first commit
  const hasData = ebitda > 0;

  return (
    <div style={{
      padding: '10px 14px',
      borderBottom: '1px solid rgba(0, 229, 195, 0.06)',
      display: 'flex', flexDirection: 'column', gap: 6,
      background: '#f8fafc'
    }}>
      <div style={{
        fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase',
        letterSpacing: '0.08em', color: '#1e293b',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <span>👁️‍🗨️</span> Competitor Intel
        </div>
        {hasData && (
          <span style={{
            fontSize: '0.65rem', padding: '2px 6px', borderRadius: 4,
            background: isTied ? 'rgba(148, 163, 184, 0.1)' : isTrailing ? 'rgba(244, 63, 94, 0.1)' : 'rgba(16, 185, 129, 0.1)',
            color: isTied ? '#64748b' : isTrailing ? '#e11d48' : '#059669'
          }}>
            {isTied ? 'Tied' : isTrailing ? 'Trailing' : 'Leading'} ({ratio}x)
          </span>
        )}
      </div>

      {!hasData ? (
        <div style={{ padding: '8px 0', fontSize: '0.7rem', color: '#94a3b8', fontStyle: 'italic', textAlign: 'center' }}>
          📊 Competitor data available from Round 2
        </div>
      ) : (
        <div style={{ height: 60, width: '100%', marginTop: 4 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 0, right: 10, bottom: 0, left: 0 }}>
              <XAxis type="number" hide domain={[0, 'dataMax']} />
              <YAxis type="category" dataKey="name" width={65} tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip
                cursor={{ fill: 'rgba(0,0,0,0.02)' }}
                formatter={(v) => fmtM(v)}
                contentStyle={{ fontSize: 10, borderRadius: 4, padding: '4px 8px' }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={12}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
