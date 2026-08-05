'use client';
import React, { useState, useEffect, useMemo } from 'react';
import ConsequenceDNAVisualizer from './ConsequenceDNAVisualizer';

/**
 * DNAComparison — Facilitator tool for side-by-side
 * Consequence DNA Sankey comparison across cohorts.
 *
 * Fetches DNA data for two selected sessions and renders
 * them inline for visual comparison during debriefs.
 */

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function DNAComparison({ sessionId, leaderboard = [] }) {
  const [sessionA, setSessionA] = useState(sessionId || '');
  const [sessionB, setSessionB] = useState('');
  const [dataA, setDataA] = useState(null);
  const [dataB, setDataB] = useState(null);
  const [loadingA, setLoadingA] = useState(false);
  const [loadingB, setLoadingB] = useState(false);
  const [errorA, setErrorA] = useState(null);
  const [errorB, setErrorB] = useState(null);

  // Sessions that are R5+ (DNA ignited)
  const eligibleSessions = useMemo(() => {
    return leaderboard.filter(s => (s.round_number || 1) >= 5);
  }, [leaderboard]);

  // Fetch DNA data for a session
  const fetchDNA = async (sid, setData, setLoading, setError) => {
    if (!sid) { setData(null); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/simulations/${sid}/consequence-dna-data`);
      if (!res.ok) throw new Error(`${res.status}`);
      const d = await res.json();
      setData(d);
    } catch (e) {
      setError(`Failed to load DNA data: ${e.message}`);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDNA(sessionA, setDataA, setLoadingA, setErrorA); }, [sessionA]);
  useEffect(() => { fetchDNA(sessionB, setDataB, setLoadingB, setErrorB); }, [sessionB]);

  const getLabel = (sid) => {
    const s = leaderboard.find(l => l.session_id === sid);
    return s ? `${s.cohort_name || s.player_name || 'Team'} (R${s.round_number || '?'})` : sid?.slice(0, 12) || '—';
  };

  // Quick comparison metrics
  const renderDelta = (a, b, label, higherIsBetter = true) => {
    if (!a || !b) return null;
    const diff = a - b;
    const better = higherIsBetter ? diff > 0 : diff < 0;
    return (
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '6px 12px', borderRadius: 6,
        background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
        fontSize: '0.78rem',
      }}>
        <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{label}</span>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{typeof a === 'number' ? a.toFixed(2) : a}</span>
          <span style={{
            fontWeight: 700, fontSize: 'var(--type-caption)',
            color: diff === 0 ? 'var(--text-muted)' : better ? '#10b981' : '#ef4444',
          }}>
            {diff > 0 ? '▲' : diff < 0 ? '▼' : '='} {Math.abs(diff).toFixed(2)}
          </span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{typeof b === 'number' ? b.toFixed(2) : b}</span>
        </div>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{
        padding: '1.25rem 1.5rem', borderRadius: 12,
        background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      }}>
        <h2 style={{ color: 'var(--text-primary)', fontSize: '1.3rem', fontWeight: 700, marginBottom: 8 }}>
          🧬 Consequence DNA Comparison
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: 1.6, maxWidth: 700, marginBottom: 16 }}>
          Compare how two teams' strategic decisions cascaded through flags, stakeholder agents,
          and metric shifts to produce different M_R outcomes. Use this during debriefs to highlight
          systemic divergence points.
        </p>

        {/* Session selectors */}
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 220 }}>
            <label style={{ display: 'block', fontSize: 'var(--type-caption)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
              Team A
            </label>
            <select
              value={sessionA}
              onChange={e => setSessionA(e.target.value)}
              style={{
                width: '100%', padding: '8px 12px', borderRadius: 8,
                background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)', fontSize: '0.82rem',
              }}
            >
              <option value="">Select session…</option>
              {eligibleSessions.map(s => (
                <option key={s.session_id} value={s.session_id}>
                  {s.cohort_name || s.player_name || s.session_id.slice(0, 12)} — R{s.round_number || '?'}
                </option>
              ))}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 220 }}>
            <label style={{ display: 'block', fontSize: 'var(--type-caption)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
              Team B
            </label>
            <select
              value={sessionB}
              onChange={e => setSessionB(e.target.value)}
              style={{
                width: '100%', padding: '8px 12px', borderRadius: 8,
                background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)', fontSize: '0.82rem',
              }}
            >
              <option value="">Select session…</option>
              {eligibleSessions.filter(s => s.session_id !== sessionA).map(s => (
                <option key={s.session_id} value={s.session_id}>
                  {s.cohort_name || s.player_name || s.session_id.slice(0, 12)} — R{s.round_number || '?'}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Delta Comparison Strip */}
      {dataA && dataB && (
        <div style={{
          padding: '1rem 1.5rem', borderRadius: 12,
          background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(16,185,129,0.06))',
          border: '1px solid rgba(99,102,241,0.2)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontWeight: 700, fontSize: '0.82rem', color: 'var(--text-primary)' }}>
              📊 Quick Comparison: {getLabel(sessionA)} vs {getLabel(sessionB)}
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {renderDelta(dataA.mr_projection?.mr, dataB.mr_projection?.mr, 'M_R (Regenerative Multiple)', true)}
            {renderDelta(dataA.leverage_summary?.deep_intervention_count, dataB.leverage_summary?.deep_intervention_count, 'Deep Interventions', true)}
            {renderDelta(dataA.leverage_summary?.shallow_intervention_count, dataB.leverage_summary?.shallow_intervention_count, 'Shallow Interventions', false)}
            {renderDelta(
              (dataA.agents || []).filter(a => ['agitated', 'hostile', 'triggered'].includes(a.stage)).length,
              (dataB.agents || []).filter(a => ['agitated', 'hostile', 'triggered'].includes(a.stage)).length,
              'Active Conflicts',
              false,
            )}
            {renderDelta(dataA.leverage_summary?.effectiveness_score, dataB.leverage_summary?.effectiveness_score, 'System Effectiveness', true)}
          </div>
        </div>
      )}

      {/* Side-by-side Sankey Diagrams */}
      <div style={{ display: 'grid', gridTemplateColumns: dataB ? '1fr 1fr' : '1fr', gap: 16 }}>
        {/* Team A */}
        <div style={{ borderRadius: 12, border: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
          <div style={{
            padding: '8px 16px', background: 'var(--bg-elevated)',
            borderBottom: '1px solid var(--border-subtle)',
            fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)',
          }}>
            {sessionA ? `🅰️ ${getLabel(sessionA)}` : '🅰️ Select Team A'}
          </div>
          {loadingA && <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading…</div>}
          {errorA && <div style={{ padding: 20, color: '#ef4444', fontSize: '0.82rem' }}>{errorA}</div>}
          {dataA && (
            <ConsequenceDNAVisualizer
              isOpen={true}
              frozen={true}
              inline={true}
              snapshotData={dataA}
              onClose={() => {}}
            />
          )}
          {!sessionA && !loadingA && (
            <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 8, opacity: 0.4 }}>🧬</div>
              Select a session from the dropdown above
            </div>
          )}
        </div>

        {/* Team B */}
        {sessionB && (
          <div style={{ borderRadius: 12, border: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
            <div style={{
              padding: '8px 16px', background: 'var(--bg-elevated)',
              borderBottom: '1px solid var(--border-subtle)',
              fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)',
            }}>
              🅱️ {getLabel(sessionB)}
            </div>
            {loadingB && <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading…</div>}
            {errorB && <div style={{ padding: 20, color: '#ef4444', fontSize: '0.82rem' }}>{errorB}</div>}
            {dataB && (
              <ConsequenceDNAVisualizer
                isOpen={true}
                frozen={true}
                inline={true}
                snapshotData={dataB}
                onClose={() => {}}
              />
            )}
          </div>
        )}
      </div>

      {/* No eligible sessions message */}
      {eligibleSessions.length === 0 && (
        <div style={{
          padding: '3rem 2rem', textAlign: 'center',
          background: 'var(--bg-card)', borderRadius: 12,
          border: '1px dashed var(--border-subtle)',
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.4 }}>🔒</div>
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>No DNA Data Available Yet</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: 500, margin: '0 auto' }}>
            The Consequence DNA Visualizer activates after the Round 5 Shadow Board Audit.
            Once teams reach Round 5+, their causal chain data will appear here for comparison.
          </p>
        </div>
      )}
    </div>
  );
}
