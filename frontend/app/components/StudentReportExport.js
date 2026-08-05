'use client';
import { useCallback } from 'react';
import { currencySymbol } from '../utils/format';

const fmt$ = (v) => {
  const abs = Math.abs(v || 0);
  if (abs >= 1e6) return `${currencySymbol()}${((v || 0) / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${currencySymbol()}${((v || 0) / 1e3).toFixed(0)}K`;
  return `${currencySymbol()}${(v || 0).toFixed(0)}`;
};

export default function StudentReportExport({ data = {}, globalState = {}, history = [], businessUnits = [], sessionId = '', playerName = '' }) {
  const generateReport = useCallback(() => {
    const d = data;
    const profileTitle = d.profile_title || 'Strategic Leader';
    const tv = d.terminal_value || 0;
    const mr = d.regenerative_multiple || 0;
    const rep = globalState?.group_reputation || 50;
    const treasury = globalState?.corporate_treasury || 0;
    const bs = globalState?.balance_sheet || {};

    const roundRows = history.map((h, i) => {
      const choice = h?.choice_title || h?.choice_label || h?.choice_selected || '—';
      const treas = h?.treasury ?? h?.corporate_treasury ?? 0;
      return `<tr><td style="padding:6px 10px;border-bottom:1px solid #e2e8f0;font-weight:600">R${i+1}</td><td style="padding:6px 10px;border-bottom:1px solid #e2e8f0">${choice}</td><td style="padding:6px 10px;border-bottom:1px solid #e2e8f0;text-align:right;font-family:monospace">${fmt$(treas)}</td></tr>`;
    }).join('');

    const buRows = businessUnits.map(bu =>
      `<tr><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;font-weight:600">${bu.bu_name||bu.bu_id}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right">${fmt$(bu.revenue_base||0)}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right">${fmt$(bu.opex_base||0)}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right">${(bu.carbon_intensity||0).toFixed(1)}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right">${(bu.social_license_score||0).toFixed(1)}</td></tr>`
    ).join('');

    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Strategy Report</title>
<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}body{font-family:'DM Sans',sans-serif;color:#1e293b;background:#fff;padding:40px;max-width:900px;margin:0 auto}
h1{font-size:1.8rem;font-weight:900;color:#0f172a;margin-bottom:4px}h2{font-size:1.1rem;font-weight:800;color:#334155;margin:24px 0 10px;padding-bottom:6px;border-bottom:2px solid #e2e8f0}
.header{text-align:center;margin-bottom:32px;padding-bottom:20px;border-bottom:3px solid #6366f1}
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}
.kpi-card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;text-align:center}
.kpi-label{font-size: var(--type-caption);font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#64748b}
.kpi-value{font-size:1.2rem;font-weight:800;font-family:monospace;margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:.82rem;margin:8px 0}
th{text-align:left;padding:6px 10px;font-size: var(--type-caption);font-weight:700;color:#64748b;text-transform:uppercase;border-bottom:2px solid #e2e8f0}
.footer{margin-top:32px;padding-top:16px;border-top:2px solid #e2e8f0;text-align:center;font-size: var(--type-caption);color:#94a3b8}
@media print{body{padding:20px}.no-print{display:none!important}}</style></head>
<body>
<div class="header"><div style="font-size:.8rem;color:#64748b;letter-spacing:.15em;text-transform:uppercase;font-weight:700">Muressons Global Corporation</div>
<h1>Strategy Report</h1>
<div style="font-size:.85rem;color:#475569;margin-top:4px">${playerName?`<strong>${playerName}</strong> · `:''}${new Date().toLocaleDateString()}</div>
<div style="display:inline-block;padding:6px 20px;border-radius:20px;font-size:.75rem;font-weight:800;color:white;margin:12px 0;background:linear-gradient(135deg,#6366f1,#4f46e5)">${d.profile_icon||''} ${profileTitle}</div></div>

<h2>📊 Final Performance</h2>
<div class="kpi-grid">
<div class="kpi-card"><div class="kpi-label">Terminal Value</div><div class="kpi-value" style="color:#3b82f6">${fmt$(tv)}</div></div>
<div class="kpi-card"><div class="kpi-label">M_R Multiple</div><div class="kpi-value" style="color:${mr>=1.2?'#10b981':'#f59e0b'}">${mr.toFixed(3)}×</div></div>
<div class="kpi-card"><div class="kpi-label">Treasury</div><div class="kpi-value" style="color:${treasury>=0?'#10b981':'#ef4444'}">${fmt$(treasury)}</div></div>
<div class="kpi-card"><div class="kpi-label">Reputation</div><div class="kpi-value" style="color:${rep>60?'#10b981':'#f59e0b'}">${rep.toFixed(1)}</div></div>
</div>

<h2>📋 Decision Timeline</h2>
<table><thead><tr><th>Round</th><th>Decision</th><th style="text-align:right">Treasury</th></tr></thead>
<tbody>${roundRows||'<tr><td colspan="3" style="padding:10px;color:#94a3b8;text-align:center">No decisions recorded</td></tr>'}</tbody></table>

<h2>🏢 Business Unit Performance</h2>
<table><thead><tr><th>BU</th><th style="text-align:right">Revenue</th><th style="text-align:right">OPEX</th><th style="text-align:right">CI</th><th style="text-align:right">SLO</th></tr></thead>
<tbody>${buRows||'<tr><td colspan="5" style="padding:10px;color:#94a3b8;text-align:center">No data</td></tr>'}</tbody></table>

<div class="footer"><p><strong>Muressons Global Corporation</strong> © ${new Date().getFullYear()}</p></div>
<div class="no-print" style="text-align:center;margin-top:24px"><button onclick="window.print()" style="padding:10px 28px;background:#6366f1;color:white;border:none;border-radius:8px;font-weight:700;cursor:pointer">🖨️ Print / Save as PDF</button></div>
</body></html>`;

    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }, [data, globalState, history, businessUnits, sessionId, playerName]);

  return (
    <button onClick={generateReport} style={{
      width:'100%',padding:'0.7rem',
      background:'linear-gradient(135deg,rgba(99,102,241,0.12),rgba(168,85,247,0.08))',
      border:'1px solid rgba(99,102,241,0.3)',borderRadius:'10px',color:'#818cf8',
      fontSize:'0.85rem',fontWeight:700,cursor:'pointer',transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
      display:'flex',alignItems:'center',justifyContent:'center',gap:'0.5rem',
    }}>📄 Download My Strategy Report</button>
  );
}
