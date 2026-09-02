'use client';
import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './SideTrackPanel.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function SideTrackPanel({ sessionId, onClose }) {
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTrack, setActiveTrack] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [committing, setCommitting] = useState(false);
  const [commitResult, setCommitResult] = useState(null);
  const [mainBlocked, setMainBlocked] = useState(false);
  const [blockingTrackId, setBlockingTrackId] = useState(null);
  const [history, setHistory] = useState([]);
  const [viewMode, setViewMode] = useState('play'); // 'play' | 'history' | 'leaderboard'
  const [leaderboard, setLeaderboard] = useState([]);
  const [aggregateData, setAggregateData] = useState(null);
  const [showAggregate, setShowAggregate] = useState(false);

  // Fetch side tracks
  const fetchTracks = useCallback(async () => {
    if (!sessionId || sessionId === 'demo') { setLoading(false); return; }
    try {
      const res = await fetch(`${API}/api/simulations/${sessionId}/side-tracks`);
      if (!res.ok) { setLoading(false); return; }
      const data = await res.json();
      setTracks(data.side_tracks || []);
      setMainBlocked(data.main_sim_blocked);
      setBlockingTrackId(data.blocking_track_id);
      // Auto-select blocking track
      if (data.blocking_track_id && !activeTrack) {
        const bt = (data.side_tracks || []).find(t => t.track_id === data.blocking_track_id);
        if (bt) setActiveTrack(bt);
      }
    } catch { /* silent */ }
    setLoading(false);
  }, [sessionId, activeTrack]);

  useEffect(() => { fetchTracks(); }, [fetchTracks]);

  // Fetch history for active track
  useEffect(() => {
    if (!activeTrack || !sessionId) return;
    fetch(`${API}/api/simulations/${sessionId}/side-tracks/${activeTrack.track_id}/history`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setHistory(d.round_history || []); })
      .catch(() => {});
  }, [activeTrack, sessionId, commitResult]);

  // Fetch leaderboard (per-track or aggregate)
  useEffect(() => {
    if (viewMode !== 'leaderboard' || !sessionId) return;
    if (showAggregate || !activeTrack) {
      // Aggregate cross-track leaderboard
      fetch(`${API}/api/simulations/${sessionId}/side-tracks/aggregate-leaderboard`)
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d) setAggregateData(d); })
        .catch(() => {});
    } else if (activeTrack) {
      // Per-track leaderboard
      fetch(`${API}/api/simulations/${sessionId}/side-tracks/${activeTrack.track_id}/leaderboard`)
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d) setLeaderboard(d.leaderboard || []); })
        .catch(() => {});
    }
  }, [activeTrack, viewMode, sessionId, showAggregate]);

  const handleCommit = useCallback(async () => {
    if (!activeTrack || !selectedOption || committing) return;
    setCommitting(true);
    try {
      const res = await fetch(`${API}/api/simulations/${sessionId}/side-tracks/${activeTrack.track_id}/commit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decisions: [{ bu_id: 'all', choice_selected: selectedOption, investment_ratio: 0.2, capex_allocated: 1000000 }],
          dividends_paid: 0,  // F-07: crisis severity / decay are server-derived
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setCommitResult(data);
      setSelectedOption(null);
      // Refresh track state
      const updated = { ...activeTrack, current_round: data.next_round || activeTrack.current_round, completed: data.is_final, round_config: data.next_round_config, track_state: data.track_state, accumulated_flags: data.accumulated_flags };
      setActiveTrack(updated);
      await fetchTracks();
    } catch (e) { console.error('Side track commit failed:', e); }
    setCommitting(false);
  }, [activeTrack, selectedOption, committing, sessionId, fetchTracks]);

  const dismissResult = () => setCommitResult(null);

  const fmtCurrency = (v) => {
    if (!v || isNaN(v)) return `${currencySymbol()}0`;
    const abs = Math.abs(v);
    return money(v);
  };

  if (loading) {
    return (
      <div className={styles.overlay}>
        <div className={styles.loading}><div className={styles.spinner} /><div className={styles.loadingText}>Loading Side Tracks...</div></div>
      </div>
    );
  }

  if (!tracks.length) {
    return (
      <div className={styles.overlay}>
        <header className={styles.header}>
          <div className={styles.headerLeft}><div className={styles.headerIcon}>🛤️</div><div className={styles.headerTitle}><span className={styles.headerLabel}>Side Simulations</span><span className={styles.headerName}>No Tracks Assigned</span></div></div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={onClose} style={{
              padding: '7px 16px', borderRadius: 8, cursor: 'pointer',
              background: 'linear-gradient(135deg, rgba(0,229,195,0.15), rgba(99,102,241,0.15))',
              border: '1px solid rgba(0,229,195,0.35)', color: '#00e5c3',
              fontSize: 'var(--type-caption)', fontWeight: 700, letterSpacing: '0.04em',
              fontFamily: "'DM Sans', system-ui, sans-serif",
              display: 'flex', alignItems: 'center', gap: 6,
            }}>← Return to Main Session</button>
            <button className={styles.closeBtn} onClick={onClose}>✕</button>
          </div>
        </header>
        <div className={styles.notStartedState}>
          <div className={styles.notStartedIcon}>📭</div>
          <div className={styles.notStartedTitle}>No Side Tracks Available</div>
          <div className={styles.notStartedDesc}>Your facilitator hasn&apos;t assigned any side simulations yet. Check back later or ask your facilitator to enable side tracks for your cohort.</div>
          <button onClick={onClose} style={{
            marginTop: 20, padding: '10px 24px', borderRadius: 8, cursor: 'pointer',
            background: 'linear-gradient(135deg, #00e5c3, #0dd9b0)', color: '#0a0e1a',
            border: 'none', fontSize: '0.78rem', fontWeight: 800, letterSpacing: '0.04em',
            fontFamily: "'DM Sans', system-ui, sans-serif",
            boxShadow: '0 4px 16px rgba(0,229,195,0.25)',
          }}>← Return to Main Simulation</button>
        </div>
      </div>
    );
  }

  // Track selector view (no active track chosen yet)
  if (!activeTrack) {
    return (
      <div className={styles.overlay}>
        <header className={styles.header}>
          <div className={styles.headerLeft}><div className={styles.headerIcon}>🛤️</div><div className={styles.headerTitle}><span className={styles.headerLabel}>Side Simulations</span><span className={styles.headerName}>Select a Track</span></div></div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={onClose} style={{
              padding: '7px 16px', borderRadius: 8, cursor: 'pointer',
              background: 'linear-gradient(135deg, rgba(0,229,195,0.15), rgba(99,102,241,0.15))',
              border: '1px solid rgba(0,229,195,0.35)', color: '#00e5c3',
              fontSize: 'var(--type-caption)', fontWeight: 700, letterSpacing: '0.04em',
              fontFamily: "'DM Sans', system-ui, sans-serif",
              display: 'flex', alignItems: 'center', gap: 6,
            }}>← Return to Main Session</button>
            <button className={styles.closeBtn} onClick={onClose}>✕</button>
          </div>
        </header>
        <div className={styles.trackSelector}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
            <div className={styles.trackSelectorTitle}>Choose Your Track</div>
            <button onClick={() => { setShowAggregate(true); setViewMode('leaderboard'); }} style={{
              padding: '6px 14px', borderRadius: 7, border: '1px solid rgba(99,102,241,0.3)',
              background: 'rgba(99,102,241,0.08)', color: '#a5b4fc', fontSize: 'var(--type-caption)',
              fontWeight: 700, cursor: 'pointer', letterSpacing: '0.05em',
            }}>🏆 All Tracks Leaderboard</button>
          </div>
          <div className={styles.trackSelectorSub}>Side simulations run independently from your main simulation. Complete all rounds to earn a separate leaderboard score and unlock bonuses for the main sim.</div>
          <div className={styles.trackCards}>
            {tracks.map(t => (
              <div key={t.track_id} className={`${styles.trackCard} ${t.completed ? styles.trackCardCompleted : ''} ${!t.is_unlocked ? styles.trackCardLocked : ''}`} onClick={() => t.is_unlocked && setActiveTrack(t)}>
                <div className={styles.trackCardIcon}>{t.icon || '📦'}</div>
                <div className={styles.trackCardName}>{t.display_name}</div>
                <div className={styles.trackCardDesc}>{t.description || 'A focused mini-simulation pathway.'}</div>
                <div className={styles.trackCardMeta}>
                  <span className={styles.trackCardMetaItem}>{t.num_rounds} rounds</span>
                  {t.completed ? <span className={styles.completeBadge}>✓ Complete</span> : t.current_round > 0 ? <span className={styles.trackCardMetaItem}>Round {t.current_round}/{t.num_rounds}</span> : <span className={styles.trackCardMetaItem}>Not Started</span>}
                  {!t.is_unlocked && <span className={styles.trackCardMetaItem}>🔒 After R{t.unlock_after_round}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ═══ AGGREGATE LEADERBOARD (overlay on selector) ═══ */}
        {showAggregate && viewMode === 'leaderboard' && (
          <div style={{ position: 'absolute', inset: 0, zIndex: 5, background: 'rgba(10,15,30,0.97)', backdropFilter: 'blur(12px)', display: 'flex', flexDirection: 'column', padding: 28, overflowY: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <div>
                <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.12em', color: '#818cf8' }}>🏆 Cross-Track Leaderboard</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f1f5f9', marginTop: 2 }}>Aggregate Side Track Performance</div>
              </div>
              <button onClick={() => { setShowAggregate(false); setViewMode('play'); }} style={{
                padding: '6px 14px', borderRadius: 7, border: '1px solid rgba(255,255,255,0.1)',
                background: 'transparent', color: '#94a3b8', fontSize: 'var(--type-caption)', fontWeight: 700, cursor: 'pointer',
              }}>← Back to Tracks</button>
            </div>
            {aggregateData?.aggregate_leaderboard?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {aggregateData.aggregate_leaderboard.map((e, i) => {
                  const gc = {'A+': '#10b981', 'A': '#34d399', 'B': '#3b82f6', 'C': '#f59e0b', 'D': '#f97316', 'F': '#ef4444'};
                  const color = gc[e.composite_grade] || '#94a3b8';
                  return (
                    <div key={i} style={{
                      padding: '12px 16px', borderRadius: 10,
                      background: e.is_you ? 'rgba(0,229,195,0.04)' : 'rgba(255,255,255,0.02)',
                      border: e.is_you ? '1px solid rgba(0,229,195,0.25)' : '1px solid rgba(255,255,255,0.05)',
                      display: 'flex', alignItems: 'center', gap: 14,
                    }}>
                      <div style={{
                        width: 36, height: 36, borderRadius: 8,
                        background: i === 0 ? 'linear-gradient(135deg, #c9a84c, #a78a3a)' : i === 1 ? 'linear-gradient(135deg, #94a3b8, #64748b)' : i === 2 ? 'linear-gradient(135deg, #b45309, #92400e)' : 'rgba(255,255,255,0.05)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.85rem', fontWeight: 900, color: i < 3 ? '#0f172a' : '#64748b',
                        fontFamily: "'JetBrains Mono', monospace",
                      }}>{e.rank}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '0.78rem', fontWeight: 700, color: e.is_you ? '#00e5c3' : '#e2e8f0' }}>
                          {e.player_name || 'Team'} {e.is_you ? '(You)' : ''}
                        </div>
                        <div style={{ fontSize: 'var(--type-caption)', color: '#64748b', marginTop: 2 }}>
                          {e.tracks_completed}/{e.tracks_available} tracks complete · {e.tracks_started} started
                        </div>
                        {/* Per-track mini badges */}
                        <div style={{ display: 'flex', gap: 4, marginTop: 4, flexWrap: 'wrap' }}>
                          {Object.entries(e.track_details || {}).map(([tid, td]) => {
                            const tColor = gc[td.grade] || '#94a3b8';
                            const trackInfo = aggregateData.available_tracks?.find(t => t.track_id === tid);
                            return (
                              <span key={tid} style={{
                                padding: '2px 6px', borderRadius: 4, fontSize: 'var(--type-caption)', fontWeight: 700,
                                background: `${tColor}15`, border: `1px solid ${tColor}30`, color: tColor,
                                fontFamily: "'JetBrains Mono', monospace",
                              }}>{trackInfo?.icon || '📦'} {td.grade} {td.total_score.toFixed(0)}</span>
                            );
                          })}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '1.1rem', fontWeight: 900, color, fontFamily: "'JetBrains Mono', monospace" }}>{e.composite_grade}</div>
                        <div style={{ fontSize: 'var(--type-caption)', color: '#64748b' }}>{e.composite_score}/100</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ color: '#64748b', textAlign: 'center', padding: 40 }}>No side track data available yet.</div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Active track view
  const rc = activeTrack.round_config;
  const trackRound = activeTrack.current_round || 0;
  const isCompleted = activeTrack.completed;
  const options = rc?.options || {};
  const flags = activeTrack.accumulated_flags || activeTrack.track_state?.accumulated_flags || [];

  return (
    <div className={styles.overlay}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerIcon}>{activeTrack.icon || '📦'}</div>
          <div className={styles.headerTitle}>
            <span className={styles.headerLabel}>Side Track</span>
            <span className={styles.headerName}>{activeTrack.display_name}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {/* View mode tabs */}
          {['play', 'history', 'leaderboard'].map(m => (
            <button key={m} onClick={() => setViewMode(m)} style={{
              padding: '5px 12px', borderRadius: 6, border: viewMode === m ? '1px solid rgba(0,229,195,0.4)' : '1px solid rgba(255,255,255,0.08)',
              background: viewMode === m ? 'rgba(0,229,195,0.1)' : 'transparent', color: viewMode === m ? '#00e5c3' : '#64748b',
              fontSize: 'var(--type-caption)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', cursor: 'pointer',
            }}>{{ play: '▶ Play', history: '📜 History', leaderboard: '🏆 Board' }[m]}</button>
          ))}
          <button onClick={() => setActiveTrack(null)} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)', background: 'transparent', color: '#64748b', fontSize: 'var(--type-caption)', fontWeight: 700, cursor: 'pointer' }}>← Tracks</button>
          <button onClick={onClose} style={{
            padding: '5px 14px', borderRadius: 6, cursor: 'pointer',
            background: 'rgba(0,229,195,0.1)', border: '1px solid rgba(0,229,195,0.3)',
            color: '#00e5c3', fontSize: 'var(--type-caption)', fontWeight: 700, letterSpacing: '0.04em',
          }}>← Main Sim</button>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>
      </header>

      {/* Progress Bar */}
      <div className={styles.progressBar}>
        {Array.from({ length: activeTrack.num_rounds }, (_, i) => {
          const r = i + 1;
          const done = r < trackRound || isCompleted;
          const active = r === trackRound && !isCompleted;
          return (
            <React.Fragment key={r}>
              {i > 0 && <div className={`${styles.progressLine} ${done ? styles.progressLineDone : ''}`} />}
              <div className={`${styles.progressDot} ${done ? styles.progressDotDone : active ? styles.progressDotActive : styles.progressDotLocked}`}>
                {done ? '✓' : r}
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {/* ═══ PLAY VIEW ═══ */}
      {viewMode === 'play' && (
        <>
          {/* Not started yet */}
          {trackRound === 0 && !isCompleted && (
            <div className={styles.notStartedState}>
              <div className={styles.notStartedIcon}>{activeTrack.icon}</div>
              <div className={styles.notStartedTitle}>Ready to Begin</div>
              <div className={styles.notStartedDesc}>This side track will seed from your main simulation state. Your decisions here will influence your terminal valuation.</div>
              <button className={styles.startBtn} onClick={() => {
                setSelectedOption(null);
                // round_config is already available from the server (preview of round 1),
                // so we just advance the local round counter to show the play view
                setActiveTrack({ ...activeTrack, current_round: 1 });
              }}>▶ Start Track</button>
            </div>
          )}

          {/* Completed state */}
          {isCompleted && (
            <div className={styles.notStartedState}>
              <div className={styles.notStartedIcon}>🏆</div>
              <div className={styles.notStartedTitle}>Track Complete!</div>
              {activeTrack.track_state && (
                <div className={styles.scorePanel}>
                  <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, textTransform: 'uppercase', color: '#00e5c3', letterSpacing: '0.1em' }}>Final Score</div>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f1f5f9', fontFamily: "'JetBrains Mono', monospace" }}>
                    {activeTrack.track_state.total_score || '—'}
                  </div>
                  {flags.length > 0 && (
                    <div className={styles.flagsStrip}>
                      {flags.map(f => <span key={f} className={styles.flagBadge}>{f.replace(/_/g, ' ')}</span>)}
                    </div>
                  )}
                </div>
              )}

              {/* Tyler TED Talk — Consumer Trust Index & Learning Resource */}
              {activeTrack.track_id === 'supply_chain' && (
                <div className={styles.tylerDebrief}>
                  <div className={styles.tylerHeader}>
                    <span className={styles.tylerIcon}>📺</span>
                    <span className={styles.tylerLabel}>Tyler Framework — Consumer Trust Index</span>
                  </div>
                  {activeTrack.track_state?.tyler_insight && (
                    <div className={styles.tylerInsight}>
                      <div className={styles.tylerCTI}>
                        <span className={styles.tylerCTILabel}>Consumer Trust Index</span>
                        <span className={styles.tylerCTIValue}>
                          {activeTrack.track_state.tyler_insight.consumer_trust_index?.toFixed(0) || '—'}/100
                        </span>
                      </div>
                      <p className={styles.tylerInterpretation}>
                        {activeTrack.track_state.tyler_insight.interpretation}
                      </p>
                    </div>
                  )}
                  <a
                    href="https://www.ted.com/talks/olivia_tyler_the_complex_path_to_sustainability"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.tylerLink}
                  >
                    ▶ Watch: The Complex Path to Sustainability — Olivia Tyler, TED Talk
                  </a>
                </div>
              )}

              {/* Mitchell/Agle/Wood Stakeholder Salience Map (Hardening Phase) */}
              {activeTrack.track_id === 'stakeholder' && activeTrack.track_state?.stakeholder_salience && (() => {
                const salience = activeTrack.track_state.stakeholder_salience;
                const stakeholders = salience.stakeholders || {};
                const classColors = {
                  'Dormant': '#64748b', 'Discretionary': '#94a3b8', 'Demanding': '#f59e0b',
                  'Dominant': '#3b82f6', 'Dangerous': '#ef4444', 'Dependent': '#8b5cf6',
                  'Definitive': '#10b981',
                };
                const attrIcons = { power: '⚡', legitimacy: '⚖️', urgency: '⏰' };
                return (
                  <div style={{
                    marginTop: 16, padding: '16px 18px', borderRadius: 12,
                    background: 'linear-gradient(135deg, rgba(99,102,241,0.06), rgba(16,185,129,0.04))',
                    border: '1px solid rgba(99,102,241,0.2)',
                  }}>
                    <div style={{
                      fontSize: 'var(--type-caption)', fontWeight: 800, textTransform: 'uppercase',
                      letterSpacing: '0.12em', color: '#818cf8', marginBottom: 12,
                      display: 'flex', alignItems: 'center', gap: 6,
                    }}>
                      <span>🎯</span> Stakeholder Salience Map (Mitchell/Agle/Wood)
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                      {Object.entries(stakeholders).map(([name, s]) => {
                        const cls = s.classification || 'Unknown';
                        const color = classColors[cls] || '#94a3b8';
                        return (
                          <div key={name} style={{
                            background: 'rgba(15,23,42,0.5)',
                            border: `1px solid ${color}40`,
                            borderRadius: 8, padding: '10px 12px',
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                              <span style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: '#e2e8f0' }}>
                                {(s.icon || '👤')} {name.replace(/_/g, ' ')}
                              </span>
                              <span style={{
                                padding: '2px 7px', borderRadius: 4, fontSize: 'var(--type-caption)',
                                fontWeight: 800, background: `${color}20`, border: `1px solid ${color}50`,
                                color, textTransform: 'uppercase', letterSpacing: '0.04em',
                              }}>{cls}</span>
                            </div>
                            <div style={{ display: 'flex', gap: 6 }}>
                              {['power', 'legitimacy', 'urgency'].map(attr => (
                                <div key={attr} style={{
                                  flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
                                  padding: '4px 0', borderRadius: 4,
                                  background: s[attr] ? `${color}10` : 'rgba(255,255,255,0.02)',
                                  border: s[attr] ? `1px solid ${color}30` : '1px solid rgba(255,255,255,0.05)',
                                }}>
                                  <span style={{ fontSize: 'var(--type-caption)' }}>{attrIcons[attr]}</span>
                                  <span style={{
                                    fontSize: 'var(--type-caption)', fontWeight: 700, marginTop: 2,
                                    color: s[attr] ? color : '#475569', textTransform: 'uppercase',
                                  }}>{attr.slice(0, 3)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div style={{
                      marginTop: 10, fontSize: 'var(--type-caption)', color: '#94a3b8', lineHeight: 1.5,
                      fontStyle: 'italic', padding: '6px 8px', borderRadius: 6,
                      background: 'rgba(255,255,255,0.02)',
                    }}>
                      💡 <strong>Mitchell, Agle & Wood (1997):</strong> Stakeholders gain salience when they accumulate Power, Legitimacy, and Urgency. 
                      Definitive stakeholders (all three attributes) demand immediate management attention.
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* Active round */}
          {trackRound > 0 && !isCompleted && rc && (
            <div className={styles.content}>
              {/* Left: Narrative */}
              <div className={styles.narrativePane}>
                <span className={styles.roundBadge}>⚡ Round {trackRound} of {activeTrack.num_rounds}</span>
                <h2 className={styles.crisisTitle}>{rc.crisis_title || rc.title || `Round ${trackRound}`}</h2>
                <p className={styles.crisisNarrative}>{rc.crisis_narrative || rc.narrative || rc.description || 'Review the situation and select your response.'}</p>
                
                {/* KPI Preview */}
                <div className={styles.kpiPreview}>
                  <div className={styles.kpiCard}>
                    <span className={styles.kpiLabel}>💰 Treasury</span>
                    <span className={styles.kpiValue}>{fmtCurrency(activeTrack.track_state?.current_treasury || activeTrack.track_state?.inherited_treasury)}</span>
                  </div>
                  <div className={styles.kpiCard}>
                    <span className={styles.kpiLabel}>🌍 Reputation</span>
                    <span className={styles.kpiValue}>{(activeTrack.track_state?.current_reputation || activeTrack.track_state?.inherited_reputation || 50).toFixed(0)}</span>
                  </div>
                  <div className={styles.kpiCard}>
                    <span className={styles.kpiLabel}>📊 Round</span>
                    <span className={styles.kpiValue}>{trackRound}/{activeTrack.num_rounds}</span>
                  </div>
                </div>

                {/* Accumulated flags */}
                {flags.length > 0 && (
                  <div>
                    <div className={styles.sectionLabel}>Active Effects</div>
                    <div className={styles.flagsStrip}>
                      {flags.map(f => <span key={f} className={styles.flagBadge}>{f.replace(/_/g, ' ')}</span>)}
                    </div>
                  </div>
                )}

                {/* Dependency warnings */}
                {rc.required_flag && !flags.includes(rc.required_flag) && (
                  <div className={styles.dependencyWarning}>
                    ⚠️ This round&apos;s options are affected by prior choices. Some paths may be locked.
                  </div>
                )}

                {/* Tyler TED Talk Reference (visible to players) */}
                {rc.tyler_reference && (
                  <div className={styles.tylerReference}>
                    <div className={styles.tylerHeader}>
                      <span className={styles.tylerIcon}>📺</span>
                      <span className={styles.tylerLabel}>Perspective — {rc.tyler_reference.speaker}</span>
                    </div>
                    <blockquote className={styles.tylerQuote}>
                      {rc.tyler_reference.quote}
                    </blockquote>
                    <div className={styles.tylerPrompt}>
                      <strong>💬 Discussion:</strong> {rc.tyler_reference.discussion_prompt}
                    </div>
                    <a
                      href={rc.tyler_reference.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.tylerLink}
                    >
                      ▶ Watch: {rc.tyler_reference.talk_title} — TED Talk
                    </a>
                  </div>
                )}
              </div>

              {/* Right: Decision */}
              <div className={styles.decisionPane}>
                <div className={styles.sectionLabel}>Choose Your Response</div>
                {Object.entries(options).map(([key, opt]) => {
                  const isSelected = selectedOption === key;
                  const isLocked = opt.requires_flag && !flags.includes(opt.requires_flag);
                  return (
                    <div key={key} className={`${styles.optionCard} ${isSelected ? styles.optionCardSelected : ''}`} onClick={() => !isLocked && setSelectedOption(key)} style={isLocked ? { opacity: 0.4, cursor: 'not-allowed' } : {}}>
                      {isSelected && <div className={styles.checkMark}>✓</div>}
                      <div className={styles.optionLabel}>
                        <span className={styles.optionKey}>{key.toUpperCase()}</span>
                        <span className={styles.optionTitle}>{opt.title}</span>
                      </div>
                      <p className={styles.optionDesc}>{opt.description}</p>
                      {opt.impacts && (
                        <div className={styles.optionImpacts}>
                          {opt.impacts.treasury != null && <span className={`${styles.impactBadge} ${opt.impacts.treasury >= 0 ? styles.impactPositive : styles.impactNegative}`}>💰 {fmtCurrency(opt.impacts.treasury)}</span>}
                          {opt.impacts.reputation != null && <span className={`${styles.impactBadge} ${opt.impacts.reputation >= 0 ? styles.impactPositive : styles.impactNegative}`}>🌍 {opt.impacts.reputation > 0 ? '+' : ''}{opt.impacts.reputation}</span>}
                          {opt.impacts.carbon != null && <span className={`${styles.impactBadge} ${opt.impacts.carbon <= 0 ? styles.impactPositive : styles.impactNegative}`}>🏭 {opt.impacts.carbon > 0 ? '+' : ''}{opt.impacts.carbon}t</span>}
                        </div>
                      )}
                      {isLocked && <div style={{ marginTop: 8, fontSize: 'var(--type-caption)', color: '#f59e0b' }}>🔒 Requires: {opt.requires_flag?.replace(/_/g, ' ')}</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Footer with commit */}
          {trackRound > 0 && !isCompleted && (
            <div className={styles.footer}>
              <div className={styles.footerInfo}>
                <span className={styles.footerLabel}>Selected</span>
                <span className={styles.footerValue}>{selectedOption ? options[selectedOption]?.title || selectedOption : 'None'}</span>
              </div>
              <button className={`${styles.commitBtn} ${selectedOption ? styles.commitBtnReady : styles.commitBtnDisabled}`} onClick={handleCommit} disabled={!selectedOption || committing}>
                {committing ? '⏳ Processing...' : `▶ Commit Round ${trackRound}`}
              </button>
            </div>
          )}
        </>
      )}

      {/* ═══ HISTORY VIEW ═══ */}
      {viewMode === 'history' && (
        <div style={{ flex: 1, overflowY: 'auto', padding: 28 }}>
          <div className={styles.sectionLabel}>Decision History</div>
          {history.length === 0 ? (
            <div style={{ color: '#64748b', textAlign: 'center', padding: 40 }}>No rounds completed yet.</div>
          ) : (
            <div className={styles.historyList}>
              {history.map((h, i) => (
                <div key={i} className={styles.historyItem}>
                  <div className={styles.historyRound}>{h.round_number}</div>
                  <div className={styles.historyMeta}>
                    <div className={styles.historyChoice}>{h.choice || 'Unknown'}</div>
                    <div style={{ fontSize: 'var(--type-caption)', color: '#64748b' }}>
                      Treasury: {fmtCurrency(h.treasury_after)} · Rep: {(h.reputation_after || 50).toFixed(0)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═══ LEADERBOARD VIEW ═══ */}
      {viewMode === 'leaderboard' && (
        <div style={{ flex: 1, overflowY: 'auto', padding: 28 }}>
          <div className={styles.sectionLabel}>Track Leaderboard</div>
          {leaderboard.length === 0 ? (
            <div style={{ color: '#64748b', textAlign: 'center', padding: 40 }}>No players have started this track yet.</div>
          ) : (
            <div className={styles.historyList}>
              {leaderboard.map((e, i) => (
                <div key={i} className={styles.historyItem} style={e.is_you ? { borderColor: 'rgba(0,229,195,0.3)', background: 'rgba(0,229,195,0.04)' } : {}}>
                  <div className={styles.historyRound} style={e.is_you ? { background: 'rgba(0,229,195,0.2)', color: '#00e5c3' } : {}}>#{e.rank}</div>
                  <div className={styles.historyMeta}>
                    <div className={styles.historyChoice}>{e.player_name || 'Team'} {e.is_you ? '(You)' : ''}</div>
                    <div style={{ fontSize: 'var(--type-caption)', color: '#64748b' }}>
                      Score: {e.total_score} · {e.grade} · {e.completed ? '✅ Done' : `R${e.rounds_done}/${e.num_rounds}`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Commit Result Toast */}
      <AnimatePresence>
        {commitResult && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} onClick={dismissResult}
            style={{ position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)', zIndex: 20000, padding: '14px 24px', borderRadius: 12, background: commitResult.is_final ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #3b82f6, #2563eb)', color: '#fff', fontSize: '0.82rem', fontWeight: 700, boxShadow: '0 8px 32px rgba(0,0,0,0.4)', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" }}>
            {commitResult.is_final ? '🏆 Track Complete! Results saved to main sim.' : `✅ Round ${commitResult.round_completed} committed. Advancing to Round ${commitResult.next_round}.`}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Need React import for Fragment
import React from 'react';
import { currencySymbol, money } from '../utils/format';
