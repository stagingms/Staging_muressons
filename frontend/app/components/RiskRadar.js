/**
 * RiskRadar.js — 2D Materiality Scatter Plot (PHASE-3)
 * Plots all BUs on a Financial Materiality × Impact Materiality plane.
 * Bubble size = investment allocation, Color = tipping point proximity.
 * Canvas-based for performance with animated pulse effects.
 */
import React, { useRef, useEffect, useState, useCallback } from 'react';
import styles from './RiskRadar.module.css';

const RISK_COLORS = {
  safe: { fill: 'rgba(16, 185, 129, 0.6)', stroke: '#10b981', pulse: 'rgba(16, 185, 129, 0.2)' },
  warning: { fill: 'rgba(245, 158, 11, 0.6)', stroke: '#f59e0b', pulse: 'rgba(245, 158, 11, 0.2)' },
  stressed: { fill: 'rgba(239, 68, 68, 0.6)', stroke: '#ef4444', pulse: 'rgba(239, 68, 68, 0.2)' },
  tipped: { fill: 'rgba(127, 29, 29, 0.8)', stroke: '#7f1d1d', pulse: 'rgba(127, 29, 29, 0.3)' },
};

const QUADRANT_LABELS = [
  { x: 0.25, y: 0.25, label: 'Low Priority', color: 'rgba(148,163,184,0.3)' },
  { x: 0.75, y: 0.25, label: 'Financial Focus', color: 'rgba(59,130,246,0.15)' },
  { x: 0.25, y: 0.75, label: 'Impact Focus', color: 'rgba(16,185,129,0.15)' },
  { x: 0.75, y: 0.75, label: 'Critical Zone', color: 'rgba(239,68,68,0.15)' },
];

function getTippingTier(bu) {
  const ci = bu.carbon_intensity || 50;
  const slo = bu.social_license_score || 50;
  const gov = bu.governance_risk_score || 20;
  const risk = (ci * 0.3 + (100 - slo) * 0.4 + gov * 0.3);
  if (risk > 75) return 'tipped';
  if (risk > 55) return 'stressed';
  if (risk > 35) return 'warning';
  return 'safe';
}

function getFinancialMateriality(bu) {
  const revenue = bu.revenue_base || 10_000_000;
  const opex = bu.opex_base || 8_000_000;
  const margin = (revenue - opex) / Math.max(revenue, 1);
  const ncd = Math.min(bu.natural_capital_debt || 0, 500) / 500;
  const ci = Math.min(bu.carbon_intensity || 50, 100) / 100;
  // Financial materiality = how sustainability risks affect finances
  // Lower margin → more vulnerable to cost shocks; Higher NCD → more exposed
  // Carbon intensity adds transition risk (carbon tax, stranded assets)
  return Math.min(1, Math.max(0, (1 - margin) * 0.4 + ncd * 0.5 + ci * 0.1));
}

function getImpactMateriality(bu) {
  const ci = Math.min(bu.carbon_intensity || 50, 100) / 100;
  const slo = (bu.social_license_score || 50) / 100;
  const water = Math.min(bu.water_dependency || 0, 100) / 100;
  return Math.min(1, Math.max(0, ci * 0.4 + (1 - slo) * 0.3 + water * 0.3));
}

const BU_DISPLAY = {
  pharma: { label: 'Pharma', short: 'PH' },
  electronics: { label: 'Electronics', short: 'EL' },
  consumer_goods: { label: 'Consumer', short: 'CG' },
  software: { label: 'Software', short: 'SW' },
  hospitals: { label: 'Hospitals', short: 'HO' },
  diagnostics: { label: 'Diagnostics', short: 'DI' },
  medical_devices: { label: 'Med Devices', short: 'MD' },
  telehealth: { label: 'Telehealth', short: 'TH' },
};

export default function RiskRadar({ buStates = [], allocations = {}, tippingState = {} }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const [hoveredBu, setHoveredBu] = useState(null);
  const [tooltip, setTooltip] = useState(null);
  const pulsePhase = useRef(0);

  const buData = (buStates || []).map(bu => {
    const id = bu.bu_id;
    const tier = getTippingTier(bu);
    const finMat = getFinancialMateriality(bu);
    const impMat = getImpactMateriality(bu);
    const alloc = allocations[id] || 0;
    const maxAlloc = Math.max(...Object.values(allocations || {}), 1);
    const size = 16 + (alloc / Math.max(maxAlloc, 1)) * 24;
    return { id, tier, finMat, impMat, size, bu, alloc };
  });

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width;
    const H = rect.height;
    const PAD = 50;
    const plotW = W - PAD * 2;
    const plotH = H - PAD * 2;

    ctx.clearRect(0, 0, W, H);
    pulsePhase.current += 0.03;

    // Quadrant backgrounds
    QUADRANT_LABELS.forEach(q => {
      ctx.fillStyle = q.color;
      const qx = PAD + (q.x - 0.25) * plotW;
      const qy = PAD + (1 - q.y - 0.25) * plotH;
      ctx.fillRect(qx, qy, plotW * 0.5, plotH * 0.5);
      ctx.fillStyle = 'rgba(148,163,184,0.5)';
      ctx.font = '11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(q.label, qx + plotW * 0.25, qy + plotH * 0.25 + 4);
    });

    // Grid lines
    ctx.strokeStyle = 'rgba(148,163,184,0.15)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(PAD + plotW * 0.5, PAD);
    ctx.lineTo(PAD + plotW * 0.5, PAD + plotH);
    ctx.moveTo(PAD, PAD + plotH * 0.5);
    ctx.lineTo(PAD + plotW, PAD + plotH * 0.5);
    ctx.stroke();
    ctx.setLineDash([]);

    // Axes labels
    ctx.fillStyle = 'rgba(148,163,184,0.8)';
    ctx.font = '12px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Financial Materiality →', PAD + plotW / 2, H - 8);
    ctx.save();
    ctx.translate(14, PAD + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Impact Materiality →', 0, 0);
    ctx.restore();

    // BU bubbles
    buData.forEach(d => {
      const cx = PAD + d.finMat * plotW;
      const cy = PAD + (1 - d.impMat) * plotH;
      const colors = RISK_COLORS[d.tier] || RISK_COLORS.safe;
      const pulseSize = d.tier === 'tipped' ? 8 : d.tier === 'stressed' ? 5 : 2;
      const pulseR = d.size + pulseSize + Math.sin(pulsePhase.current * (d.tier === 'tipped' ? 3 : 1.5)) * pulseSize;

      // Pulse ring
      ctx.beginPath();
      ctx.arc(cx, cy, pulseR, 0, Math.PI * 2);
      ctx.fillStyle = colors.pulse;
      ctx.fill();

      // Main bubble
      ctx.beginPath();
      ctx.arc(cx, cy, d.size, 0, Math.PI * 2);
      ctx.fillStyle = colors.fill;
      ctx.fill();
      ctx.strokeStyle = colors.stroke;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Label
      const display = BU_DISPLAY[d.id] || { short: d.id.substring(0, 2).toUpperCase() };
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(display.short, cx, cy);
    });

    animRef.current = requestAnimationFrame(draw);
  }, [buData]);

  useEffect(() => {
    animRef.current = requestAnimationFrame(draw);
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
  }, [draw]);

  const handleMouseMove = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const PAD = 50;
    const plotW = rect.width - PAD * 2;
    const plotH = rect.height - PAD * 2;

    let found = null;
    buData.forEach(d => {
      const cx = PAD + d.finMat * plotW;
      const cy = PAD + (1 - d.impMat) * plotH;
      const dist = Math.sqrt((mx - cx) ** 2 + (my - cy) ** 2);
      if (dist < d.size + 5) found = d;
    });

    if (found) {
      const display = BU_DISPLAY[found.id] || { label: found.id };
      setHoveredBu(found.id);
      setTooltip({
        x: e.clientX - rect.left + 15,
        y: e.clientY - rect.top - 10,
        content: {
          name: display.label,
          tier: found.tier,
          finMat: (found.finMat * 100).toFixed(0),
          impMat: (found.impMat * 100).toFixed(0),
          ci: found.bu.carbon_intensity?.toFixed(0) || '—',
          slo: found.bu.social_license_score?.toFixed(0) || '—',
          alloc: found.alloc,
        },
      });
    } else {
      setHoveredBu(null);
      setTooltip(null);
    }
  };

  return (
    <div className={styles.radarContainer} id="risk-radar-panel">
      <div className={styles.radarHeader}>
        <h3 className={styles.radarTitle}>🎯 Risk Radar — Double Materiality</h3>
        <div className={styles.legendRow}>
          {Object.entries(RISK_COLORS).map(([tier, colors]) => (
            <span key={tier} className={styles.legendItem}>
              <span className={styles.legendDot} style={{ background: colors.fill, borderColor: colors.stroke }} />
              {tier.charAt(0).toUpperCase() + tier.slice(1)}
            </span>
          ))}
        </div>
      </div>
      <div className={styles.canvasWrapper}>
        <canvas
          ref={canvasRef}
          className={styles.radarCanvas}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => { setHoveredBu(null); setTooltip(null); }}
        />
        {tooltip && (
          <div className={styles.tooltip} style={{ left: tooltip.x, top: tooltip.y }}>
            <div className={styles.tooltipTitle}>{tooltip.content.name}</div>
            <div className={styles.tooltipRow}>
              <span>Risk Tier:</span>
              <span className={styles[`tier_${tooltip.content.tier}`]}>{tooltip.content.tier}</span>
            </div>
            <div className={styles.tooltipRow}><span>Fin. Materiality:</span><span>{tooltip.content.finMat}%</span></div>
            <div className={styles.tooltipRow}><span>Impact Materiality:</span><span>{tooltip.content.impMat}%</span></div>
            <div className={styles.tooltipRow}><span>Carbon Intensity:</span><span>{tooltip.content.ci}</span></div>
            <div className={styles.tooltipRow}><span>Social License:</span><span>{tooltip.content.slo}</span></div>
          </div>
        )}
      </div>
    </div>
  );
}
