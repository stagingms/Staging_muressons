/**
 * TCFDScenarioDashboard.js — Climate Scenario Analysis Panel
 * Fetches TCFD-aligned scenario data (1.5°C, 2°C, 4°C) and renders
 * an interactive comparison dashboard with animated risk gauges,
 * revenue projections, and strategic implications.
 *
 * Architecture:
 *   Self-contained component. Fetches from /api/simulations/{id}/tcfd-scenarios.
 *   Designed for the ExecutiveCockpit right-panel "Climate" tab and also
 *   available for the Facilitator Teleprompter.
 *
 * Theory: TCFD (2017), NGFS (2022), IEA (2023)
 */
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import styles from './TCFDScenarioDashboard.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const SCENARIO_META = {
  orderly_1_5: {
    icon: '🌱',
    gradient: 'linear-gradient(135deg, #059669, #10b981)',
    accentHsl: '160, 84%, 39%',
    ringColor: '#10b981',
    tagLabel: 'ORDERLY',
    tagBg: 'rgba(16, 185, 129, 0.12)',
    tagColor: '#10b981',
    temp: '1.5°C',
  },
  disorderly_2: {
    icon: '⚡',
    gradient: 'linear-gradient(135deg, #d97706, #f59e0b)',
    accentHsl: '38, 92%, 50%',
    ringColor: '#f59e0b',
    tagLabel: 'DISORDERLY',
    tagBg: 'rgba(245, 158, 11, 0.12)',
    tagColor: '#f59e0b',
    temp: '2°C',
  },
  hothouse_4: {
    icon: '🔥',
    gradient: 'linear-gradient(135deg, #dc2626, #ef4444)',
    accentHsl: '0, 84%, 60%',
    ringColor: '#ef4444',
    tagLabel: 'HOTHOUSE',
    tagBg: 'rgba(239, 68, 68, 0.12)',
    tagColor: '#ef4444',
    temp: '4°C',
  },
};

/* ── Animated SVG Arc Gauge ── */
function ArcGauge({ value, max, color, label, size = 72 }) {
  const radius = (size - 10) / 2;
  const circumference = Math.PI * radius;
  const pct = Math.min(Math.max(value / max, 0), 1);
  const dashOffset = circumference * (1 - pct);

  return (
    <div className={styles.gaugeWrap}>
      <svg width={size} height={size / 2 + 8} viewBox={`0 0 ${size} ${size / 2 + 8}`}>
        {/* Background arc */}
        <path
          d={`M 5 ${size / 2 + 3} A ${radius} ${radius} 0 0 1 ${size - 5} ${size / 2 + 3}`}
          fill="none"
          stroke="rgba(148,163,184,0.12)"
          strokeWidth="5"
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d={`M 5 ${size / 2 + 3} A ${radius} ${radius} 0 0 1 ${size - 5} ${size / 2 + 3}`}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className={styles.gaugeArc}
        />
      </svg>
      <div className={styles.gaugeValue} style={{ color }}>{typeof value === 'number' ? value.toFixed(1) : value}</div>
      <div className={styles.gaugeLabel}>{label}</div>
    </div>
  );
}

/* ── Horizontal Impact Bar ── */
function ImpactBar({ label, value, maxAbs, positive }) {
  const pct = Math.min(Math.abs(value) / (maxAbs || 1), 1) * 100;
  const barColor = positive ? '#10b981' : '#ef4444';
  return (
    <div className={styles.impactRow}>
      <span className={styles.impactLabel}>{label}</span>
      <div className={styles.impactTrack}>
        <div
          className={styles.impactFill}
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
      <span className={styles.impactVal} style={{ color: barColor }}>
        {positive ? '+' : ''}{typeof value === 'number' ? value.toFixed(1) : value}%
      </span>
    </div>
  );
}

/* ── Main Component ── */
export default function TCFDScenarioDashboard({
  sessionId,
  globalState = {},
  compact = false,
  onClose,
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeScenario, setActiveScenario] = useState('orderly_1_5');
  const [compareMode, setCompareMode] = useState(false);
  const fetchRef = useRef(false);

  // Fetch TCFD data
  useEffect(() => {
    if (!sessionId || fetchRef.current) return;
    fetchRef.current = true;
    setLoading(true);
    fetch(`${API}/api/simulations/${sessionId}/tcfd-scenarios`)
      .then(r => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); })
      .finally(() => { fetchRef.current = false; });
  }, [sessionId]);

  const scenarios = useMemo(() => data?.scenarios || {}, [data]);
  const summary = useMemo(() => data?.summary || {}, [data]);
  const active = scenarios[activeScenario] || {};

  const maxRisk = useMemo(() => {
    if (!summary.overall_risk) return 100;
    return Math.max(...Object.values(summary.overall_risk), 100);
  }, [summary]);

  const maxCarbon = useMemo(() => {
    if (!summary.carbon_cost) return 1;
    return Math.max(...Object.values(summary.carbon_cost));
  }, [summary]);

  const fmtM = useCallback((v) => {
    if (Math.abs(v) >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
    if (Math.abs(v) >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
    return `$${v.toFixed(0)}`;
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingWrap}>
          <div className={styles.loadingOrb} />
          <span className={styles.loadingText}>Loading TCFD scenarios…</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={styles.container}>
        <div className={styles.errorWrap}>
          <span className={styles.errorIcon}>⚠️</span>
          <span className={styles.errorText}>
            {error === '404' ? 'Session not found' : 'Climate scenarios unavailable'}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${compact ? styles.compact : ''}`} id="tcfd-scenario-dashboard">
      {/* ── Header ── */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerIcon}>🌍</span>
          <div>
            <h3 className={styles.title}>Climate Scenario Analysis</h3>
            <span className={styles.subtitle}>TCFD · NGFS-aligned · {active.time_horizon_years || 10}yr horizon</span>
          </div>
        </div>
        <div className={styles.headerActions}>
          <button
            className={`${styles.modeToggle} ${compareMode ? styles.modeActive : ''}`}
            onClick={() => setCompareMode(!compareMode)}
          >
            {compareMode ? '◻ Single' : '◫ Compare'}
          </button>
          {onClose && <button className={styles.closeBtn} onClick={onClose}>✕</button>}
        </div>
      </div>

      {/* ── Scenario Selector Tabs ── */}
      <div className={styles.scenarioTabs}>
        {Object.entries(SCENARIO_META).map(([sid, meta]) => {
          const sc = scenarios[sid] || {};
          const risk = summary.overall_risk?.[sid] || 0;
          return (
            <button
              key={sid}
              className={`${styles.scenarioTab} ${activeScenario === sid ? styles.scenarioTabActive : ''}`}
              onClick={() => setActiveScenario(sid)}
              style={{
                '--accent': meta.ringColor,
                '--accent-bg': meta.tagBg,
              }}
            >
              <div className={styles.tabIcon}>{meta.icon}</div>
              <div className={styles.tabInfo}>
                <span className={styles.tabTemp}>{meta.temp}</span>
                <span className={styles.tabTag} style={{ background: meta.tagBg, color: meta.tagColor }}>
                  {meta.tagLabel}
                </span>
              </div>
              <div className={styles.tabRisk} style={{ color: meta.ringColor }}>
                {risk.toFixed(0)}
              </div>
            </button>
          );
        })}
      </div>

      {compareMode ? (
        /* ══ COMPARE MODE ══ */
        <div className={styles.compareGrid}>
          {/* Revenue Impact */}
          <div className={styles.compareCard}>
            <div className={styles.ccHeader}>📊 Revenue Impact</div>
            {Object.entries(summary.revenue_impact || {}).map(([sid, val]) => {
              const meta = SCENARIO_META[sid];
              return (
                <ImpactBar
                  key={sid}
                  label={meta.temp}
                  value={val}
                  maxAbs={Math.max(...Object.values(summary.revenue_impact || {}).map(Math.abs))}
                  positive={val > 0}
                />
              );
            })}
          </div>

          {/* Carbon Cost */}
          <div className={styles.compareCard}>
            <div className={styles.ccHeader}>🏭 Annual Carbon Cost</div>
            {Object.entries(summary.carbon_cost || {}).map(([sid, val]) => {
              const meta = SCENARIO_META[sid];
              const pct = (val / maxCarbon) * 100;
              return (
                <div key={sid} className={styles.compareRow}>
                  <span className={styles.compareLabel}>{meta.icon} {meta.temp}</span>
                  <div className={styles.compareTrack}>
                    <div
                      className={styles.compareFill}
                      style={{ width: `${pct}%`, background: meta.ringColor }}
                    />
                  </div>
                  <span className={styles.compareVal}>{fmtM(val)}</span>
                </div>
              );
            })}
          </div>

          {/* Physical Loss */}
          <div className={styles.compareCard}>
            <div className={styles.ccHeader}>🌊 Physical Loss / yr</div>
            {Object.entries(summary.physical_loss || {}).map(([sid, val]) => {
              const meta = SCENARIO_META[sid];
              const maxPhys = Math.max(...Object.values(summary.physical_loss || {}));
              const pct = (val / maxPhys) * 100;
              return (
                <div key={sid} className={styles.compareRow}>
                  <span className={styles.compareLabel}>{meta.icon} {meta.temp}</span>
                  <div className={styles.compareTrack}>
                    <div
                      className={styles.compareFill}
                      style={{ width: `${pct}%`, background: meta.ringColor }}
                    />
                  </div>
                  <span className={styles.compareVal}>{fmtM(val)}</span>
                </div>
              );
            })}
          </div>

          {/* Risk Gauges */}
          <div className={styles.compareCard}>
            <div className={styles.ccHeader}>⚖️ Overall Risk Score</div>
            <div className={styles.gaugeRow}>
              {Object.entries(summary.overall_risk || {}).map(([sid, val]) => {
                const meta = SCENARIO_META[sid];
                return (
                  <ArcGauge key={sid} value={val} max={maxRisk} color={meta.ringColor} label={meta.temp} />
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* ══ SINGLE SCENARIO VIEW ══ */
        <div className={styles.singleView}>
          {(() => {
            const meta = SCENARIO_META[activeScenario] || {};
            const sc = active;
            const phys = sc.physical_risk || {};
            const trans = sc.transition_opportunity || {};
            const stranded = sc.stranded_assets || {};
            const carbon = sc.carbon_exposure || {};

            return (
              <>
                {/* Scenario Header Banner */}
                <div className={styles.scenarioBanner} style={{ '--sc-gradient': meta.gradient }}>
                  <div className={styles.bannerIcon}>{meta.icon}</div>
                  <div className={styles.bannerText}>
                    <h4 className={styles.bannerTitle}>{sc.scenario || 'Scenario'}</h4>
                    <p className={styles.bannerDesc}>{sc.description}</p>
                  </div>
                  <span className={styles.bannerTag} style={{ background: meta.tagBg, color: meta.tagColor }}>
                    {sc.ngfs_category}
                  </span>
                </div>

                {/* KPI Row */}
                <div className={styles.kpiRow}>
                  <div className={styles.kpiCard}>
                    <div className={styles.kpiLabel}>Revenue Impact</div>
                    <div className={styles.kpiValue} style={{ color: (sc.total_revenue_change_pct || 0) < 0 ? '#ef4444' : '#10b981' }}>
                      {(sc.total_revenue_change_pct || 0) > 0 ? '+' : ''}{(sc.total_revenue_change_pct || 0).toFixed(1)}%
                    </div>
                  </div>
                  <div className={styles.kpiCard}>
                    <div className={styles.kpiLabel}>Carbon Cost / yr</div>
                    <div className={styles.kpiValue} style={{ color: '#f59e0b' }}>
                      {fmtM(carbon.annual_carbon_cost || 0)}
                    </div>
                  </div>
                  <div className={styles.kpiCard}>
                    <div className={styles.kpiLabel}>Stranded Assets</div>
                    <div className={styles.kpiValue} style={{ color: '#ef4444' }}>
                      {fmtM(stranded.write_down_impact || 0)}
                    </div>
                  </div>
                  <div className={styles.kpiCard}>
                    <div className={styles.kpiLabel}>Opportunity</div>
                    <div className={styles.kpiValue} style={{ color: '#3b82f6' }}>
                      {(trans.opportunity_score || 0).toFixed(0)}/100
                    </div>
                  </div>
                </div>

                {/* Gauges: Physical Risk + Carbon Exposure */}
                <div className={styles.gaugeSection}>
                  <ArcGauge
                    value={summary.overall_risk?.[activeScenario] || 0}
                    max={maxRisk}
                    color={meta.ringColor}
                    label="Risk Score"
                    size={90}
                  />
                  <div className={styles.riskDetail}>
                    <div className={styles.riskRow}>
                      <span>Physical Risk</span>
                      <span className={styles.riskBadge} style={{
                        background: phys.risk_level === 'catastrophic' ? 'rgba(239,68,68,0.15)' :
                          phys.risk_level === 'severe' ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)',
                        color: phys.risk_level === 'catastrophic' ? '#ef4444' :
                          phys.risk_level === 'severe' ? '#f59e0b' : '#10b981',
                      }}>
                        {(phys.risk_level || 'unknown').toUpperCase()}
                      </span>
                    </div>
                    <div className={styles.riskRow}>
                      <span>Transition Readiness</span>
                      <span className={styles.riskBadge} style={{
                        background: trans.readiness_assessment === 'well_positioned' ? 'rgba(16,185,129,0.15)' :
                          trans.readiness_assessment === 'high_vulnerability' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                        color: trans.readiness_assessment === 'well_positioned' ? '#10b981' :
                          trans.readiness_assessment === 'high_vulnerability' ? '#ef4444' : '#f59e0b',
                      }}>
                        {(trans.readiness_assessment || 'unknown').replace(/_/g, ' ').toUpperCase()}
                      </span>
                    </div>
                    <div className={styles.riskRow}>
                      <span>Carbon Intensity</span>
                      <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{(carbon.avg_carbon_intensity || 0).toFixed(0)}</span>
                    </div>
                    <div className={styles.riskRow}>
                      <span>Carbon as % Rev</span>
                      <span style={{ color: '#f59e0b', fontWeight: 600 }}>{(carbon.carbon_cost_as_pct_revenue || 0).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                {/* BU Revenue Projections */}
                {sc.bu_projections && sc.bu_projections.length > 0 && (
                  <div className={styles.buSection}>
                    <div className={styles.buHeader}>📈 BU Revenue Projections</div>
                    {sc.bu_projections.map(bp => (
                      <div key={bp.bu_id} className={styles.buRow}>
                        <span className={styles.buName}>{bp.bu_id.replace(/_/g, ' ')}</span>
                        <div className={styles.buBarWrap}>
                          <div
                            className={styles.buBar}
                            style={{
                              width: `${Math.min(Math.abs(bp.revenue_change_pct) * 5, 100)}%`,
                              background: bp.revenue_change_pct >= 0 ? '#10b981' : '#ef4444',
                            }}
                          />
                        </div>
                        <span className={styles.buPct} style={{ color: bp.revenue_change_pct >= 0 ? '#10b981' : '#ef4444' }}>
                          {bp.revenue_change_pct >= 0 ? '+' : ''}{bp.revenue_change_pct}%
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Strategic Implications */}
                {trans.strategic_implications && trans.strategic_implications.length > 0 && (
                  <div className={styles.implicationsSection}>
                    <div className={styles.implHeader}>🧭 Strategic Implications</div>
                    {trans.strategic_implications.map((imp, i) => (
                      <div key={i} className={styles.implItem}>{imp}</div>
                    ))}
                  </div>
                )}

                {/* Nature Risk (if available) */}
                {sc.nature_risk && (
                  <div className={styles.natureRisk}>
                    <div className={styles.natureHeader}>🌿 Nature Risk (TNFD)</div>
                    <div className={styles.natureRow}>
                      <span>Ecosystem Health</span>
                      <span style={{ color: '#10b981' }}>{sc.nature_risk.ecosystem_health}</span>
                    </div>
                    <div className={styles.natureRow}>
                      <span>Nature Risk Score</span>
                      <span style={{ color: '#f59e0b' }}>{sc.nature_risk.nature_risk_score}</span>
                    </div>
                    <div className={styles.natureReco}>{sc.nature_risk.tnfd_recommendation}</div>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {/* ── Footer: Strategic Insight ── */}
      {summary.strategic_insight && (
        <div className={styles.insightFooter}>
          <span className={styles.insightIcon}>💡</span>
          <p className={styles.insightText}>{summary.strategic_insight}</p>
        </div>
      )}
    </div>
  );
}
