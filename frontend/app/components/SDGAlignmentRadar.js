'use client';
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import styles from './SDGAlignmentRadar.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * SDG Alignment Radar — Chief Strategic Orchestrator Frontend
 *
 * Visualizes:
 *  - SVG Polar Radar Chart of per-BU SDG alignment scores
 *  - SDG Heatmap (color-coded SDG tiles with group scores)
 *  - Material Gap Alerts
 *  - M_SDG terminal valuation projection
 *  - SDG Side Track progress (if active)
 *
 * Props:
 *  - sessionId: current session ID
 *  - globalState: live global state from cockpit
 *  - buStates: live BU states from cockpit
 *  - isOpen: visibility toggle
 *  - onClose: callback
 */

const SDG_ICONS = {
  3: '💊', 6: '💧', 8: '⚡', 9: '💻', 10: '⚖️', 12: '♻️', 15: '🌿',
};

const SDG_LABELS = {
  3: 'Good Health', 6: 'Clean Water', 8: 'Decent Work',
  9: 'Innovation', 10: 'Reduced Inequalities', 12: 'Responsible Production', 15: 'Life on Land',
};

const BU_ICONS = {
  pharma: '💊', electronics: '⚡', consumer_goods: '🛒', software: '💻',
};

const BU_LABELS = {
  pharma: 'Pharma', electronics: 'Electronics', consumer_goods: 'Consumer Goods', software: 'Software',
};

// UN SDG Official Colors
const SDG_COLORS = {
  3: '#4C9F38', 6: '#26BDE2', 8: '#A21942', 9: '#FD6925',
  10: '#DD1367', 12: '#BF8B2E', 15: '#56C02B',
};


export default function SDGAlignmentRadar({ sessionId, globalState, buStates, isOpen, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('radar'); // 'radar' | 'heatmap' | 'track'

  // Fetch SDG dashboard data
  const fetchData = useCallback(async () => {
    if (!sessionId || sessionId === 'demo') return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/simulations/${sessionId}/sdg-dashboard`);
      if (res.ok) {
        const d = await res.json();
        setData(d);
      }
    } catch { /* silent */ }
    setLoading(false);
  }, [sessionId]);

  useEffect(() => {
    if (isOpen) fetchData();
  }, [isOpen, fetchData]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => { if (e.key === 'Escape') onClose?.(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  // Derived computations
  const groupScore = data?.group_sdg_score ?? 0;
  const buScores = data?.bu_scores ?? {};
  const sdgHeatmap = data?.sdg_heatmap ?? {};
  const alerts = data?.alerts ?? [];
  const gapCount = data?.gap_count ?? 0;

  // SDG track state (if in flags)
  const sdgTrackScore = globalState?.active_event_flags?.sdg_impact_score ?? null;
  const sdgTrackCompleted = globalState?.active_event_flags?.sdg_track_completed ?? false;
  const mSdg = sdgTrackScore !== null ? (1.0 + (sdgTrackScore / 100.0) * 0.25) : null;

  // Radar polygon data (SVG polar chart)
  const radarData = useMemo(() => {
    const buIds = Object.keys(buScores);
    if (!buIds.length) return [];
    return buIds.map((buId, i) => {
      const result = buScores[buId];
      const score = result?.sdg_score ?? 50;
      const details = result?.sdg_details ?? [];
      return { buId, score, details, angle: (i / buIds.length) * 2 * Math.PI - Math.PI / 2 };
    });
  }, [buScores]);

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}>
      <div className={styles.panel}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <span className={styles.headerIcon}>🌐</span>
            <div>
              <div className={styles.headerTitle}>SDG ALIGNMENT RADAR</div>
              <div className={styles.headerSub}>Chief Strategic Orchestrator — Principled Prioritization</div>
            </div>
          </div>
          <div className={styles.headerRight}>
            {['radar', 'heatmap', 'track'].map(t => (
              <button key={t} className={`${styles.tabBtn} ${activeTab === t ? styles.tabBtnActive : ''}`}
                onClick={() => setActiveTab(t)}>
                {{ radar: '📡 Radar', heatmap: '🗺️ Heatmap', track: '🛤️ SDG Track' }[t]}
              </button>
            ))}
            <button className={styles.closeBtn} onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Score Banner */}
        <div className={styles.scoreBanner}>
          <div className={styles.scoreCard}>
            <span className={styles.scoreLabel}>Group SDG Score</span>
            <span className={styles.scoreValue} style={{
              color: groupScore >= 70 ? '#10b981' : groupScore >= 45 ? '#f59e0b' : '#ef4444'
            }}>{groupScore.toFixed(1)}</span>
            <span className={styles.scoreUnit}>/100</span>
          </div>
          {mSdg !== null && (
            <div className={styles.scoreCard}>
              <span className={styles.scoreLabel}>M<sub>SDG</sub> Projection</span>
              <span className={styles.scoreValue} style={{
                color: mSdg >= 1.15 ? '#10b981' : mSdg >= 1.0 ? '#3b82f6' : '#ef4444'
              }}>{mSdg.toFixed(4)}×</span>
              <span className={styles.scoreUnit}>Terminal Multiplier</span>
            </div>
          )}
          <div className={styles.scoreCard}>
            <span className={styles.scoreLabel}>Material Gaps</span>
            <span className={styles.scoreValue} style={{
              color: gapCount === 0 ? '#10b981' : gapCount <= 2 ? '#f59e0b' : '#ef4444'
            }}>{gapCount}</span>
            <span className={styles.scoreUnit}>SDGs below threshold</span>
          </div>
          {sdgTrackCompleted && (
            <div className={styles.scoreCard}>
              <span className={styles.scoreLabel}>SDG Track Score</span>
              <span className={styles.scoreValue} style={{ color: '#818cf8' }}>
                {sdgTrackScore ?? '—'}
              </span>
              <span className={styles.scoreUnit}>/105 impact points</span>
            </div>
          )}
        </div>

        {/* Content Area */}
        <div className={styles.content}>
          {loading && !data && (
            <div className={styles.loadingState}>
              <div className={styles.spinner} />
              <div>Loading SDG alignment data…</div>
            </div>
          )}

          {/* ═══ RADAR TAB ═══ */}
          {activeTab === 'radar' && data && (
            <div className={styles.radarLayout}>
              {/* SVG Radar */}
              <div className={styles.radarSvgWrap}>
                <svg viewBox="0 0 300 300" className={styles.radarSvg}>
                  {/* Background rings */}
                  {[20, 40, 60, 80, 100].map(r => (
                    <circle key={r} cx={150} cy={150} r={r * 1.2}
                      className={styles.radarRing} />
                  ))}
                  {/* Ring labels */}
                  {[20, 40, 60, 80, 100].map(r => (
                    <text key={`l-${r}`} x={152} y={150 - r * 1.2 + 4}
                      className={styles.ringLabel}>{r}</text>
                  ))}

                  {/* Axis lines */}
                  {radarData.map(d => {
                    const x2 = 150 + Math.cos(d.angle) * 120;
                    const y2 = 150 + Math.sin(d.angle) * 120;
                    return (
                      <line key={d.buId} x1={150} y1={150} x2={x2} y2={y2}
                        className={styles.radarAxis} />
                    );
                  })}

                  {/* Score polygon */}
                  {radarData.length > 0 && (
                    <polygon
                      points={radarData.map(d => {
                        const r = (d.score / 100) * 120;
                        return `${150 + Math.cos(d.angle) * r},${150 + Math.sin(d.angle) * r}`;
                      }).join(' ')}
                      className={styles.radarPolygon}
                    />
                  )}

                  {/* Score dots + labels */}
                  {radarData.map(d => {
                    const r = (d.score / 100) * 120;
                    const x = 150 + Math.cos(d.angle) * r;
                    const y = 150 + Math.sin(d.angle) * r;
                    const lx = 150 + Math.cos(d.angle) * 135;
                    const ly = 150 + Math.sin(d.angle) * 135;
                    const color = d.score >= 60 ? '#10b981' : d.score >= 40 ? '#f59e0b' : '#ef4444';
                    return (
                      <g key={d.buId}>
                        <circle cx={x} cy={y} r={5} fill={color} className={styles.radarDot} />
                        <text x={lx} y={ly + 4} textAnchor="middle" className={styles.radarLabel}>
                          {BU_ICONS[d.buId]} {d.score.toFixed(0)}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>

              {/* BU Detail Cards */}
              <div className={styles.buCards}>
                {Object.entries(buScores).map(([buId, result]) => {
                  const score = result?.sdg_score ?? 0;
                  const color = result?.color ?? '#888';
                  const gaps = result?.gaps ?? [];
                  return (
                    <div key={buId} className={styles.buCard}>
                      <div className={styles.buCardHeader}>
                        <span className={styles.buIcon}>{BU_ICONS[buId]}</span>
                        <span className={styles.buName}>{BU_LABELS[buId] || buId}</span>
                        <span className={styles.buScore} style={{
                          color: score >= 60 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444'
                        }}>{score.toFixed(1)}</span>
                      </div>
                      <div className={styles.buSDGs}>
                        {(result?.sdg_details ?? []).map(sd => (
                          <div key={sd.sdg} className={styles.sdgRow}>
                            <span className={styles.sdgIcon} style={{ color: sd.color }}>{sd.icon}</span>
                            <span className={styles.sdgName}>SDG {sd.sdg}</span>
                            <div className={styles.sdgBar}>
                              <div className={styles.sdgBarFill} style={{
                                width: `${sd.normalized_score}%`,
                                background: sd.normalized_score >= 60 ? '#10b981' : sd.normalized_score >= 40 ? '#f59e0b' : '#ef4444',
                              }} />
                            </div>
                            <span className={styles.sdgScore}>{sd.normalized_score.toFixed(0)}</span>
                          </div>
                        ))}
                      </div>
                      {gaps.length > 0 && (
                        <div className={styles.buGap}>
                          ⚠️ {gaps.map(g => `SDG ${g.sdg}: −${g.gap_magnitude.toFixed(0)}pt`).join(', ')}
                        </div>
                      )}
                      <div className={styles.buLinkage}>{result?.linkage_rule}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ═══ HEATMAP TAB ═══ */}
          {activeTab === 'heatmap' && data && (
            <div className={styles.heatmapLayout}>
              <div className={styles.heatmapGrid}>
                {Object.entries(sdgHeatmap).sort(([a], [b]) => Number(a) - Number(b)).map(([sdgNum, score]) => {
                  const num = Number(sdgNum);
                  const color = SDG_COLORS[num] || '#888';
                  const pct = Math.max(0, Math.min(100, score));
                  return (
                    <div key={num} className={styles.heatmapTile}>
                      <div className={styles.heatmapTileHeader} style={{ borderBottomColor: color }}>
                        <span className={styles.heatmapIcon}>{SDG_ICONS[num]}</span>
                        <span className={styles.heatmapNum}>SDG {num}</span>
                      </div>
                      <div className={styles.heatmapLabel}>{SDG_LABELS[num]}</div>
                      <div className={styles.heatmapScoreWrap}>
                        <div className={styles.heatmapRing} style={{
                          background: `conic-gradient(${color} ${pct * 3.6}deg, rgba(255,255,255,0.06) 0deg)`,
                        }}>
                          <span className={styles.heatmapScore}>{score.toFixed(0)}</span>
                        </div>
                      </div>
                      {/* BU linkage indicators */}
                      <div className={styles.heatmapBUs}>
                        {Object.entries(data.materiality_map || {}).map(([buId, mat]) => {
                          if (!mat.sdgs.includes(num)) return null;
                          return <span key={buId} className={styles.heatmapBUBadge}>{BU_ICONS[buId]}</span>;
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Materiality Alerts */}
              {alerts.length > 0 && (
                <div className={styles.alertSection}>
                  <div className={styles.alertTitle}>⚠️ Critical SDG Gaps</div>
                  {alerts.map((a, i) => (
                    <div key={i} className={styles.alertCard}>
                      <span className={styles.alertSeverity}>{a.severity === 'critical' ? '🔴' : '🟡'}</span>
                      <span className={styles.alertMsg}>{a.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ═══ SDG TRACK TAB ═══ */}
          {activeTab === 'track' && (
            <div className={styles.trackLayout}>
              {sdgTrackCompleted ? (
                <div className={styles.trackCompleted}>
                  <div className={styles.trackCompletedIcon}>🏆</div>
                  <div className={styles.trackCompletedTitle}>SDG Deep Track Complete</div>
                  <div className={styles.trackScoreRow}>
                    <div className={styles.trackScoreCard}>
                      <span className={styles.trackScoreLabel}>Impact Score</span>
                      <span className={styles.trackScoreVal}>{sdgTrackScore ?? 0}/105</span>
                    </div>
                    <div className={styles.trackScoreCard}>
                      <span className={styles.trackScoreLabel}>M<sub>SDG</sub></span>
                      <span className={styles.trackScoreVal} style={{ color: '#10b981' }}>{mSdg?.toFixed(4)}×</span>
                    </div>
                    <div className={styles.trackScoreCard}>
                      <span className={styles.trackScoreLabel}>Terminal Formula</span>
                      <span className={styles.trackScoreVal} style={{ fontSize: '0.72rem' }}>
                        V<sub>T</sub> = EBITDA × Exit × M<sub>R</sub> × M<sub>SDG</sub>
                      </span>
                    </div>
                  </div>

                  {/* ── Fix 8: Round-by-round sparkline trend ── */}
                  {(() => {
                    const history = globalState?.active_event_flags?.sdg_score_history || [];
                    if (history.length === 0) return null;

                    const CHOICE_LABELS = { option_a: 'A', option_b: 'B', option_c: 'C' };
                    const CHOICE_COLORS = {
                      option_a: '#10b981', option_b: '#f59e0b', option_c: '#ef4444',
                    };
                    const ROUND_NAMES = {
                      1: 'PAI Audit', 2: 'Living Wage', 3: 'Circular Proc.',
                      4: 'Biodiversity', 5: 'Int. Reporting',
                    };
                    const maxScore = 105;

                    // Build SVG polyline for M_SDG trend
                    const svgW = 320, svgH = 48;
                    const xStep = history.length > 1 ? svgW / (history.length - 1) : svgW;
                    const mSdgMin = 1.0, mSdgMax = 1.2625;
                    const toY = (val) => svgH - ((val - mSdgMin) / (mSdgMax - mSdgMin)) * svgH;
                    const points = history.map((h, i) =>
                      `${history.length === 1 ? svgW / 2 : i * xStep},${toY(h.m_sdg || 1.0)}`
                    ).join(' ');

                    return (
                      <div style={{
                        background: 'rgba(0,0,0,0.15)', borderRadius: '10px',
                        padding: '0.9rem', margin: '0.75rem 0',
                        border: '1px solid rgba(255,255,255,0.05)',
                      }}>
                        <div style={{ fontSize: '0.6rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.65rem' }}>
                          Round-by-Round SDG Progression
                        </div>

                        {/* Bar chart */}
                        <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'flex-end', height: '52px', marginBottom: '0.4rem' }}>
                          {history.map((h, i) => {
                            const pct = Math.max(6, (h.score / maxScore) * 100);
                            const col = CHOICE_COLORS[h.choice] || '#818cf8';
                            return (
                              <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
                                <div style={{ fontSize: '0.5rem', color: col, fontWeight: 800 }}>
                                  {h.points >= 0 ? `+${h.points}` : h.points}
                                </div>
                                <div style={{ position: 'relative', width: '100%', flex: 1, display: 'flex', alignItems: 'flex-end' }}>
                                  <div style={{
                                    width: '100%', height: `${pct}%`, minHeight: '5px',
                                    borderRadius: '3px 3px 0 0', background: col,
                                    opacity: 0.85, transition: 'height 0.5s ease',
                                  }} title={`ST-R${h.sdg_track_round} (${ROUND_NAMES[h.sdg_track_round]}): ${h.choice?.replace('option_', 'Option ')} | +${h.points}pts → Total: ${h.score}`} />
                                </div>
                                <div style={{
                                  fontSize: '0.48rem', fontWeight: 800, color: '#fff',
                                  background: col, padding: '1px 4px', borderRadius: '3px',
                                }}>{CHOICE_LABELS[h.choice] || '?'}</div>
                              </div>
                            );
                          })}
                        </div>

                        {/* Round labels */}
                        <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '0.6rem' }}>
                          {history.map((h, i) => (
                            <div key={i} style={{ flex: 1, textAlign: 'center', fontSize: '0.45rem', color: '#475569', lineHeight: 1.2 }}>
                              {ROUND_NAMES[h.sdg_track_round] || `R${h.sdg_track_round}`}
                            </div>
                          ))}
                        </div>

                        {/* M_SDG SVG trend line */}
                        <div style={{ marginBottom: '0.4rem' }}>
                          <div style={{ fontSize: '0.52rem', color: '#64748b', fontWeight: 700, marginBottom: '3px' }}>M<sub>SDG</sub> trajectory</div>
                          <svg width="100%" viewBox={`0 0 ${svgW} ${svgH}`} style={{ overflow: 'visible', display: 'block' }}>
                            {/* Grid lines */}
                            {[1.0, 1.0625, 1.125, 1.1875, 1.2625].map((v, i) => (
                              <line key={i} x1={0} y1={toY(v)} x2={svgW} y2={toY(v)}
                                stroke="rgba(255,255,255,0.04)" strokeWidth={1} />
                            ))}
                            {/* Trend polyline */}
                            {history.length > 1 && (
                              <polyline points={points} fill="none" stroke="#818cf8" strokeWidth={1.5}
                                strokeLinecap="round" strokeLinejoin="round" opacity={0.9} />
                            )}
                            {/* Dots */}
                            {history.map((h, i) => {
                              const cx = history.length === 1 ? svgW / 2 : i * xStep;
                              const cy = toY(h.m_sdg || 1.0);
                              const col = CHOICE_COLORS[h.choice] || '#818cf8';
                              return (
                                <g key={i}>
                                  <circle cx={cx} cy={cy} r={4} fill={col} stroke="rgba(0,0,0,0.3)" strokeWidth={1} />
                                  <text x={cx} y={cy - 7} textAnchor="middle"
                                    fill={col} fontSize={7} fontFamily="JetBrains Mono, monospace" fontWeight={700}>
                                    {h.m_sdg?.toFixed(3)}
                                  </text>
                                </g>
                              );
                            })}
                          </svg>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.45rem', color: '#334155', marginTop: '2px' }}>
                            <span>1.000× (baseline)</span><span>1.2625× (max)</span>
                          </div>
                        </div>

                        {/* Cumulative score callout */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.4rem 0.6rem', borderRadius: '6px', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
                          <span style={{ fontSize: '0.62rem', color: '#94a3b8' }}>Final cumulative SDG Impact Score</span>
                          <span style={{ fontSize: '0.82rem', fontWeight: 900, color: '#818cf8', fontFamily: "'JetBrains Mono', monospace" }}>
                            {history[history.length - 1]?.score ?? 0} / 105
                          </span>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Flag Summary */}
                  <div className={styles.trackFlagsSection}>
                    <div className={styles.trackFlagsTitle}>Earned Flags</div>
                    <div className={styles.trackFlags}>
                      {['sdg_integrity_unlocked', 'community_fund', 'circular_leader', 'nature_positive',
                        'sdg_integrated_reporting', 'sdg_living_wage', 'managed_transition'].map(flag => {
                        const active = globalState?.active_event_flags?.[flag];
                        return (
                          <span key={flag} className={`${styles.trackFlag} ${active ? styles.trackFlagActive : ''}`}>
                            {active ? '✅' : '○'} {flag.replace(/_/g, ' ')}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div className={styles.trackNotStarted}>
                  <div className={styles.trackNotStartedIcon}>🌐</div>
                  <div className={styles.trackNotStartedTitle}>Corporate SDG Deep Track</div>
                  <div className={styles.trackNotStartedDesc}>
                    The SDG Deep Track is a facilitator-gated, 5-round side simulation covering:
                  </div>
                  <div className={styles.trackRoundsList}>
                    {[
                      { r: 1, icon: '🔍', label: 'PAI Audit', desc: 'Map all BU harm pathways to material SDGs' },
                      { r: 2, icon: '✊', label: 'Living Wage Strike', desc: 'Supply chain labor justice across Tier-1 suppliers' },
                      { r: 3, icon: '♻️', label: 'Circular Procurement', desc: 'Closed-loop material flow transformation' },
                      { r: 4, icon: '🌿', label: 'Biodiversity Net-Gain', desc: 'SBTN/TNFD alignment for nature-positive status' },
                      { r: 5, icon: '📊', label: 'Integrated Reporting', desc: 'Codify the Universal Care Mandate into corporate DNA' },
                    ].map(({ r, icon, label, desc }) => (
                      <div key={r} className={styles.trackRoundItem}>
                        <span className={styles.trackRoundIcon}>{icon}</span>
                        <div>
                          <div className={styles.trackRoundLabel}>ST-R{r}: {label}</div>
                          <div className={styles.trackRoundDesc}>{desc}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className={styles.trackNotStartedNote}>
                    💡 Access this track via the Side Tracks panel. Assignment is controlled by your facilitator.
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Trigger button for the Executive Cockpit
 */
export function SDGRadarTrigger({ onClick, sdgScore, gapCount }) {
  return (
    <button className={styles.triggerBtn} onClick={onClick}
      title="Open SDG Alignment Radar">
      <span className={styles.triggerPulse} style={{
        background: (gapCount || 0) > 0 ? 'rgba(239,68,68,0.4)' : 'rgba(16,185,129,0.4)',
      }} />
      <span>🌐</span>
      <span>SDG Radar</span>
      {sdgScore != null && <span className={styles.triggerScore}>{sdgScore.toFixed(0)}</span>}
    </button>
  );
}
