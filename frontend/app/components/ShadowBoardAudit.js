'use client';
import React, { useState, useEffect, useCallback } from 'react';
import styles from './ShadowBoardAudit.module.css';
import { playerIdHeader } from '../hooks/useSimulation';
import { moneyM } from '../utils/format';

/* The headline damage figure for the R5 cyclone. */
const CYCLONE_BASE_DAMAGE = 12_000_000;

/**
 * ShadowBoardAudit — Round 5 Reflective Middleware
 *
 * A mandatory "Board Room Moment" that intercepts the player after the
 * Round 5 Physical Climate Risk briefing. Three AI personas present
 * conflicting arguments about the impending Category 4 cyclone.
 * The player must publicly reject one argument to proceed.
 *
 * Theory base:
 *   - Mitchell et al. (1997): Stakeholder Salience
 *   - Schön (1983): Reflection-in-Action
 *
 * Props:
 *   - sessionId:    current session UUID
 *   - onComplete:   callback({rejection_target, archetype, consequence_dna_chain}) when audit finishes
 *   - globalState:  current game state (for pre-check)
 */
export default function ShadowBoardAudit({ sessionId, onComplete, globalState }) {
  // ── SDG Tension: live M_SDG projection for the intercept panel ──
  const flags = globalState?.active_event_flags || {};
  const sdgTrackScore = flags.sdg_impact_score ?? null;
  const sdgTrackActive = sdgTrackScore !== null;
  const sdgHistoricalScore = sdgTrackScore ?? 0;
  const mSdgCurrent = 1.0 + (sdgHistoricalScore / 100.0) * 0.25;
  const mSdgWithPerfectR5 = 1.0 + ((sdgHistoricalScore + 20) / 100.0) * 0.25; // +20 from option_a
  const mSdgUplift = Math.round((mSdgWithPerfectR5 - mSdgCurrent) * 10000) / 10000;
  const API = process.env.NEXT_PUBLIC_API_URL || '';

  const [phase, setPhase] = useState('loading'); // 'loading' | 'personas' | 'confirming' | 'result'
  const [personas, setPersonas] = useState([]);
  const [auditState, setAuditState] = useState(null);
  const [confirmTarget, setConfirmTarget] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // ── Fetch audit data on mount ──────────────────────────────
  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;

    const fetchAudit = async () => {
      try {
        const res = await fetch(`${API}/api/simulations/${sessionId}/shadow-board-audit`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (cancelled) return;

        if (!data.audit_required) {
          // Already completed or wrong round — skip
          onComplete?.({
            skipped: true,
            rejection_target: data.audit_state?.rejection_target,
            archetype: data.audit_state?.archetype,
          });
          return;
        }

        setPersonas(data.personas || []);
        setAuditState(data.audit_state);
        setPhase('personas');
      } catch (err) {
        console.error('[ShadowBoardAudit] Fetch failed:', err);
        if (!cancelled) {
          setError(err.message);
          // Don't block the player on network error — let them proceed
          setTimeout(() => onComplete?.({ skipped: true, error: err.message }), 3000);
        }
      }
    };

    fetchAudit();
    return () => { cancelled = true; };
  }, [sessionId]);

  // ── Initiate rejection ─────────────────────────────────────
  const handleRejectClick = useCallback((personaId) => {
    setConfirmTarget(personaId);
  }, []);

  const handleCancelConfirm = useCallback(() => {
    setConfirmTarget(null);
  }, []);

  // ── Submit rejection to backend ────────────────────────────
  const handleConfirmReject = useCallback(async () => {
    if (!confirmTarget || submitting) return;
    setSubmitting(true);

    try {
      const res = await fetch(
        `${API}/api/simulations/${sessionId}/shadow-board-audit/reject`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...playerIdHeader() },
          body: JSON.stringify({ rejection_target: confirmTarget }),
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setResult(data);
      setPhase('result');
    } catch (err) {
      console.error('[ShadowBoardAudit] Rejection submit failed:', err);
      setError(err.message);
      // Fallback: proceed anyway after a brief delay
      setTimeout(() => onComplete?.({ skipped: true, error: err.message }), 2000);
    } finally {
      setSubmitting(false);
    }
  }, [confirmTarget, submitting, sessionId]);

  // ── Proceed to Investment Matrix ───────────────────────────
  const handleProceed = useCallback(() => {
    if (result) {
      onComplete?.({
        rejection_target: result.rejection_target,
        archetype: result.strategic_archetype?.archetype,
        consequence_dna_chain: result.consequence_dna_chain,
        hidden_flag: result.hidden_flag,
      });
    }
  }, [result, onComplete]);

  // ── Find persona by ID ────────────────────────────────────
  const getPersona = (id) => personas.find(p => p.persona_id === id);
  const confirmedPersona = confirmTarget ? getPersona(confirmTarget) : null;

  // ═══════════════════════════════════════════════════════════
  //  RENDER — Loading
  // ═══════════════════════════════════════════════════════════
  if (phase === 'loading') {
    return (
      <div className={styles.overlay}>
        <div className={styles.modal}>
          <div className={styles.loading}>
            <div className={styles.spinner} />
            <div className={styles.loadingText}>Convening the Shadow Board…</div>
          </div>
        </div>
      </div>
    );
  }

  // ═══════════════════════════════════════════════════════════
  //  RENDER — Error (brief flash then auto-dismiss)
  // ═══════════════════════════════════════════════════════════
  if (error && phase === 'loading') {
    return (
      <div className={styles.overlay}>
        <div className={styles.modal}>
          <div className={styles.loading}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚠️</div>
            <div className={styles.loadingText}>
              Shadow Board unavailable: {error}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ═══════════════════════════════════════════════════════════
  //  RENDER — Result Phase
  // ═══════════════════════════════════════════════════════════
  if (phase === 'result' && result) {
    const chain = result.consequence_dna_chain;
    const archetype = result.strategic_archetype;
    const rejected = result.rejected_persona;
    const stake = result.stakeholder_impact;
    const accentColor = getPersona(result.rejection_target)?.color || '#ef4444';

    return (
      <div className={styles.overlay}>
        <div className={styles.modal}>
          <div className={styles.header}>
            <div className={styles.headerBadge}>AUDIT COMPLETE</div>
            <h1 className={styles.title}>Value Judgment Recorded</h1>
          </div>

          <div className={styles.resultPhase}>
            <div className={styles.resultIcon}>🔍</div>

            <h2 className={styles.resultTitle} style={{ color: accentColor }}>
              You Publicly Rejected: {rejected?.name}
            </h2>

            <div
              className={styles.resultArchetype}
              style={{
                background: `${accentColor}18`,
                border: `1px solid ${accentColor}50`,
                color: accentColor,
              }}
            >
              Strategic Archetype: {archetype?.archetype}
            </div>

            <p className={styles.resultDescription}>
              {archetype?.description}
            </p>

            {/* Consequence DNA Preview */}
            {chain && (
              <div className={styles.consequencePreview}>
                <div className={styles.consequencePreviewLabel}>
                  🧬 CONSEQUENCE DNA — Causal Chain Activated
                </div>
                <div className={styles.consequenceChain}>
                  <span className={`${styles.consequenceNode} ${styles.nodeDecision}`}>
                    {chain.source?.label}
                  </span>
                  <span className={styles.consequenceArrow}>→</span>
                  <span className={`${styles.consequenceNode} ${styles.nodeEffect}`}>
                    {chain.effect?.label}
                  </span>
                  <span className={styles.consequenceArrow}>→</span>
                  <span className={`${styles.consequenceNode} ${styles.nodeFuture}`}>
                    {chain.future?.label}
                  </span>
                </div>
              </div>
            )}

            {/* Stakeholder Tolerance Impact */}
            {stake?.tolerance_applied && (
              <div className={styles.stakeholderImpact}>
                <span className={styles.stakeholderImpactIcon}>📉</span>
                <span>
                  <strong>{stake.agent_name}</strong>&apos;s tolerance dropped by{' '}
                  <strong>{stake.tolerance_penalty}</strong> points.
                  {' '}Every dollar saved today creates a specific type of systemic liability tomorrow.
                </span>
              </div>
            )}

            <button
              className={styles.proceedBtn}
              onClick={handleProceed}
              id="shadow-board-proceed"
            >
              Proceed to Investment Matrix →
            </button>
          </div>

          <div className={styles.footerNote}>
            <p className={styles.footerNoteText}>
              This value judgment will be evaluated at Round 10. The hidden flag &ldquo;{result.hidden_flag?.name}&rdquo;
              is now active in your Consequence DNA. Mitchell Stakeholder Salience framework applied.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ═══════════════════════════════════════════════════════════
  //  RENDER — Personas Phase (main audit)
  // ═══════════════════════════════════════════════════════════
  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerBadge}>⚠ MANDATORY AUDIT — ROUND 5</div>
          <h1 className={styles.title}>Shadow Board Audit</h1>
          <p className={styles.subtitle}>
            Before proceeding to the Investment Matrix, you must evaluate three
            conflicting perspectives on the impending Category 4 cyclone and
            <strong> publicly reject</strong> one argument. This is a &ldquo;Board Room
            Moment&rdquo; — your choice reveals your firm&apos;s strategic values.
          </p>
        </div>

        {/* Crisis Context */}
        <div className={styles.contextSection}>
          <div className={styles.contextCard}>
            <div className={styles.contextIcon}>🌪️</div>
            <div className={styles.contextText}>
              <h3>IMMINENT THREAT: Category 4 Cyclone — {moneyM(CYCLONE_BASE_DAMAGE, { dp: 0 })} Base Damage</h3>
              <p>
                A Category 4 cyclone is projected to hit your primary manufacturing corridor.
                Three advisors from your Shadow Board have presented conflicting recommendations.
                You must decide whose logic you reject — this reveals which stakeholder group
                your firm considers least legitimate.
              </p>
            </div>
          </div>
        </div>

        {/* ── SDG Tension Panel (Fix 6) — shown if SDG track is active ── */}
        {sdgTrackActive && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(0,229,195,0.05))',
            border: '1px solid rgba(99,102,241,0.25)',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            marginBottom: '1.2rem',
            borderLeft: '4px solid #6366f1',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.1rem' }}>🌐</span>
                <div>
                  <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.1em' }}>SDG Deep Track — Intercept Alert</div>
                  <div style={{ fontSize: 'var(--type-caption)', color: '#64748b', marginTop: '1px' }}>Your SDG trajectory is visible to institutional investors. One round remains.</div>
                </div>
              </div>
            </div>

            {/* M_SDG trajectory cards */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <div style={{ textAlign: 'center', padding: '0.6rem', borderRadius: '8px', background: 'rgba(0,0,0,0.15)', border: '1px solid rgba(99,102,241,0.15)' }}>
                <div style={{ fontSize: 'var(--type-caption)', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', marginBottom: '2px' }}>SDG Score (R1–R4)</div>
                <div style={{ fontSize: '1rem', fontWeight: 900, color: sdgHistoricalScore >= 60 ? '#10b981' : sdgHistoricalScore >= 35 ? '#f59e0b' : '#ef4444', fontFamily: "'JetBrains Mono', monospace" }}>{sdgHistoricalScore}/85</div>
              </div>
              <div style={{ textAlign: 'center', padding: '0.6rem', borderRadius: '8px', background: 'rgba(0,0,0,0.15)', border: '1px solid rgba(16,185,129,0.15)' }}>
                <div style={{ fontSize: 'var(--type-caption)', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', marginBottom: '2px' }}>Current M<sub>SDG</sub></div>
                <div style={{ fontSize: '1rem', fontWeight: 900, color: '#3b82f6', fontFamily: "'JetBrains Mono', monospace" }}>{mSdgCurrent.toFixed(4)}×</div>
              </div>
              <div style={{ textAlign: 'center', padding: '0.6rem', borderRadius: '8px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)' }}>
                <div style={{ fontSize: 'var(--type-caption)', color: '#10b981', fontWeight: 700, textTransform: 'uppercase', marginBottom: '2px' }}>Max M<sub>SDG</sub> (ST-R5 A)</div>
                <div style={{ fontSize: '1rem', fontWeight: 900, color: '#10b981', fontFamily: "'JetBrains Mono', monospace" }}>{mSdgWithPerfectR5.toFixed(4)}×</div>
              </div>
            </div>

            {/* Progress bar */}
            <div style={{ marginBottom: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: 'var(--type-caption)', color: '#64748b' }}>SDG Alignment Progress</span>
                <span style={{ fontSize: 'var(--type-caption)', color: '#818cf8', fontWeight: 700 }}>{Math.round((sdgHistoricalScore / 85) * 100)}% of R1–R4 max</span>
              </div>
              <div style={{ height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${Math.min(100, (sdgHistoricalScore / 85) * 100)}%`, background: 'linear-gradient(90deg, #6366f1, #00e5c3)', borderRadius: '3px', transition: 'width 0.8s ease' }} />
              </div>
            </div>

            <div style={{ fontSize: 'var(--type-caption)', color: '#a78bfa', fontStyle: 'italic', borderLeft: '2px solid rgba(99,102,241,0.3)', paddingLeft: '0.6rem' }}>
              🎯 <strong>Integrated Reporting (ST-R5)</strong> is your final SDG decision. Choosing <em>Integrated Value Creation</em> (Option A) can lift M<sub>SDG</sub> by <strong style={{ color: '#10b981' }}>+{mSdgUplift.toFixed(4)}×</strong> — stacking multiplicatively with M<sub>R</sub> at terminal valuation.
            </div>
          </div>
        )}

        {/* Director cards — the sole boardroom set. (The duplicate animated
            "Enhanced Boardroom Debate" render was removed to avoid showing the
            same three advisors twice; these cards drive the full reject flow:
            select → confirm → submit, self-contained in this component.) */}
        <div className={styles.personasSection}>
          <div className={styles.sectionLabel}>
            Three Conflicting Arguments — Read All Before Rejecting
          </div>

          <div className={styles.personasGrid}>
            {personas.map((persona) => (
              <div
                key={persona.persona_id}
                className={styles.personaCard}
                style={{ '--persona-color': persona.color }}
              >
                {/* Confirmation overlay */}
                {confirmTarget === persona.persona_id && (
                  <div className={styles.confirmOverlay}>
                    <div className={styles.confirmTitle}>
                      Publicly Reject {persona.name}?
                    </div>
                    <div className={styles.confirmText}>
                      This action cannot be undone. It will lower {persona.name}&apos;s
                      stakeholder tolerance by 10 points and set a hidden flag
                      evaluated at Round 10.
                    </div>
                    <div className={styles.confirmActions}>
                      <button
                        className={styles.confirmYes}
                        onClick={handleConfirmReject}
                        disabled={submitting}
                        id={`shadow-board-confirm-${persona.persona_id}`}
                      >
                        {submitting ? 'Processing…' : 'Confirm Rejection'}
                      </button>
                      <button
                        className={styles.confirmNo}
                        onClick={handleCancelConfirm}
                        disabled={submitting}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Persona Header */}
                <div className={styles.personaHeader}>
                  <div
                    className={styles.personaAvatar}
                    style={{ background: persona.accent_gradient }}
                  >
                    {persona.avatar_emoji}
                  </div>
                  <div className={styles.personaInfo}>
                    <div className={styles.personaName}>{persona.name}</div>
                    <div className={styles.personaTitle}>{persona.title}</div>
                    <span
                      className={styles.personaArchetype}
                      style={{ color: persona.color, borderColor: `${persona.color}40` }}
                    >
                      {persona.archetype}
                    </span>
                  </div>
                </div>

                {/* Monitored Metric */}
                <div className={styles.personaBody}>
                  <div className={styles.personaMetric}>
                    <span className={styles.personaMetricLabel}>Prioritises</span>
                    <span
                      className={styles.personaMetricValue}
                      style={{ color: persona.color }}
                    >
                      {persona.monitored_metric}
                    </span>
                  </div>

                  {/* Recommendation Badge */}
                  <div className={styles.personaMetric}>
                    <span className={styles.personaMetricLabel}>Recommends</span>
                    <span
                      className={styles.personaMetricValue}
                      style={{ color: persona.color }}
                    >
                      Option {persona.recommended_option}: {persona.recommended_label}
                    </span>
                  </div>

                  {/* Script */}
                  <div
                    className={styles.personaScript}
                    style={{ borderColor: persona.color }}
                  >
                    &ldquo;{persona.script}&rdquo;
                  </div>
                </div>

                {/* Theory Citation Removed for Facilitator Teleprompter */}

                {/* Reject Button */}
                <div className={styles.personaFooter}>
                  <button
                    className={styles.rejectBtn}
                    onClick={() => handleRejectClick(persona.persona_id)}
                    disabled={confirmTarget !== null}
                    id={`shadow-board-reject-${persona.persona_id}`}
                  >
                    ✕ Publicly Reject This Argument
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className={styles.footerNote}>
          <p className={styles.footerNoteText}>
            Mitchell Stakeholder Salience Framework (1997): Your rejection directly
            lowers the &ldquo;Legitimacy&rdquo; of a specific stakeholder group,
            accelerating their &ldquo;Tolerance Decay&rdquo; in the Autonomous
            Stakeholder Agents module. This is a reflective-in-action exercise
            designed to surface your underlying strategic mental models.
          </p>
        </div>
      </div>
    </div>
  );
}
