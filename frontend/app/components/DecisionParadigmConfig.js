'use client';
import { useState, useEffect } from 'react';
import styles from './DecisionParadigmConfig.module.css';

export default function DecisionParadigmConfig({ sessions: propSessions, apiBase }) {
  const API = apiBase || process.env.NEXT_PUBLIC_API_URL || '';
  const [selectedSession, setSelectedSession] = useState('');
  const [currentParadigm, setCurrentParadigm] = useState('legacy_abc');
  const [locked, setLocked] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [sessions, setSessions] = useState(propSessions || []);

  // Climate Engine parameters (only relevant when advanced_climate is chosen)
  const [carbonFee, setCarbonFee] = useState(40);
  const [hostility, setHostility] = useState(5);
  const [scope3, setScope3] = useState(2.5);
  const [climateApplying, setClimateApplying] = useState(false);
  const [climateMsg, setClimateMsg] = useState('');

  // -- Matrix Editor State --
  const [matrixData, setMatrixData] = useState(null);
  const [matrixLoading, setMatrixLoading] = useState(true);
  const [activeEditorTab, setActiveEditorTab] = useState('legacy_abc'); // legacy_abc | multi_toggles | climate_engine
  const [localEdits, setLocalEdits] = useState({});
  const [showEditor, setShowEditor] = useState(false);

  // Advanced Climate Engine local overrides
  const [climateOverrides, setClimateOverrides] = useState({
    global_carbon_fee: 40,
    market_hostility_index: 5,
    scope_3_threshold: 2.5,
    r5_base_damage: 12000000,
    r5_stochastic_threshold: 0.75,
    r10_carbon_tax_per_ton: 250,
    r10_exit_multiple: 12.0,
    mr_synergy_bonus: 0.30,
    mr_resilience_bonus: 0.20,
    mr_truth_premium: 0.15,
    mr_instability_discount: -0.40,
    profile_regenerative_titan: 1.8,
    profile_derisked_safe_haven: 1.2,
    profile_fragile_giant: 0.8,
    loan_interest_rate: 0.12,
    cost_of_capital: 0.05,
    synergy_gate_threshold: 80,
    strike_probability: 0.75,
  });
  const [climateOverrideSaving, setClimateOverrideSaving] = useState(false);
  const [climateOverrideMsg, setClimateOverrideMsg] = useState('');

  // Auto-fetch sessions from admin API
  useEffect(() => {
    if (propSessions && propSessions.length > 0) return;
    fetch(`${API}/api/admin/sessions`)
      .then((r) => r.json())
      .then((data) => setSessions(data.sessions || data || []))
      .catch(() => {});
  }, [API, propSessions]);

  // Fetch paradigm when session changes
  useEffect(() => {
    if (!selectedSession) { setMessage(''); return; }
    fetch(`${API}/api/simulations/${selectedSession}/paradigm`)
      .then((r) => r.json())
      .then((data) => {
        setCurrentParadigm(data.decision_paradigm || 'legacy_abc');
        setLocked(!!data.paradigm_locked);
        setMessage('');
      })
      .catch(() => { setCurrentParadigm('legacy_abc'); setLocked(false); });
  }, [selectedSession, API]);

  // Fetch Matrix God Mode data
  useEffect(() => {
    fetchMatrix();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [API]);

  const fetchMatrix = () => {
    setMatrixLoading(true);
    fetch(`${API}/api/admin/decision_configs`)
      .then(r => r.json())
      .then(d => {
        setMatrixData(d);
        setLocalEdits({});
        setMatrixLoading(false);
      })
      .catch(e => {
        console.error("Failed to load decision configs", e);
        setMatrixLoading(false);
      });
  };

  const PARADIGM_LABELS = {
    legacy_abc: 'Narrative Crises (A/B/C)',
    multi_toggles: 'Strategic Pillars (4-Area)',
    advanced_climate: 'Advanced Climate Engine',
  };

  const handleToggle = async (paradigm) => {
    if (!selectedSession) {
      setMessage('⚠️ Select a session first.');
      return;
    }
    if (locked) {
      setMessage('🔒 Paradigm is locked for this cohort and cannot be changed.');
      return;
    }
    const label = PARADIGM_LABELS[paradigm] || paradigm;
    if (!confirm(`⚠️ Permanent Change\n\nYou are about to lock the decision framework to "${label}" for this cohort.\n\nThis cannot be undone — the paradigm will be locked for the entire simulation.\n\nProceed?`)) return;
    setSaving(true);
    setMessage('');
    try {
      const res = await fetch(`${API}/api/simulations/${selectedSession}/paradigm`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision_paradigm: paradigm }),
      });
      if (res.ok) {
        setCurrentParadigm(paradigm);
        setLocked(true);
        setMessage(`✅ Paradigm locked to "${label}" — this cannot be changed.`);
      } else {
        const err = await res.json();
        setMessage(`❌ ${err.detail || 'Failed to update'}`);
      }
    } catch (e) {
      setMessage('❌ Network error');
    }
    setSaving(false);
  };

  // Matrix Edit Change Handler
  const handleEditChange = (paradigm, roundStr, optionKey, areaKey, fieldName, rawValue) => {
    let finalValue = rawValue;
    // Attempt parse to number
    if (rawValue.trim() !== '') {
      const num = parseFloat(rawValue);
      if (!isNaN(num)) finalValue = num;
    }
    
    // Construct a composite key to track local changes
    const pathKey = [paradigm, roundStr, areaKey || 'none', optionKey, fieldName].join('|');
    setLocalEdits(prev => ({ ...prev, [pathKey]: finalValue }));
  };
  
  // Matrix Save — batched per row
  const handleSaveRow = async (paradigm, roundStr, optionKey, areaKey, fieldNames) => {
    // Collect all modified fields for this row
    const modifiedFields = fieldNames.filter(f => isFieldModified(paradigm, roundStr, optionKey, areaKey, f));
    if (modifiedFields.length === 0) return;

    const label = paradigm === 'legacy_abc' ? 'Narrative Crises' : 'Strategic Pillars';
    const changes = modifiedFields.map(f => {
      const pathKey = [paradigm, roundStr, areaKey || 'none', optionKey, f].join('|');
      return `  • ${f}: ${localEdits[pathKey]}`;
    }).join('\n');

    if (!confirm(`🔒 Reconfirm Override\n\nYou are about to update:\n\n${label} — Round ${roundStr}, ${optionKey}\n\n${changes}\n\nThese changes apply globally for ALL cohorts and ALL players.\n\nAre you sure you want to commit these overrides?`)) {
      return;
    }

    let allOk = true;
    for (const fieldName of modifiedFields) {
      const pathKey = [paradigm, roundStr, areaKey || 'none', optionKey, fieldName].join('|');
      try {
        const res = await fetch(`${API}/api/admin/decision_configs`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            paradigm,
            round_number: roundStr,
            area_key: areaKey,
            option_key: optionKey,
            field_name: fieldName,
            new_value: localEdits[pathKey]
          }),
        });
        if (!res.ok) allOk = false;
      } catch {
        allOk = false;
      }
    }

    if (allOk) {
      alert(`✅ ${modifiedFields.length} override(s) saved successfully.`);
      fetchMatrix();
    } else {
      alert('⚠️ Some overrides failed to save. Please retry.');
    }
  };

  const getResolvedValue = (paradigm, roundStr, optionKey, areaKey, fieldName) => {
    const pathKey = [paradigm, roundStr, areaKey || 'none', optionKey, fieldName].join('|');
    if (localEdits[pathKey] !== undefined) return localEdits[pathKey];
    return getServerDefault(paradigm, roundStr, optionKey, areaKey, fieldName);
  };

  // Returns the raw backend value, ignoring any local edits
  const getServerDefault = (paradigm, roundStr, optionKey, areaKey, fieldName) => {
    if (!matrixData) return '';
    try {
      let target = null;
      if (paradigm === 'legacy_abc') {
        target = matrixData.merged_narrative[roundStr]?.options?.[optionKey];
      } else {
        target = matrixData.merged_pillars[roundStr]?.areas?.[areaKey]?.options?.[optionKey];
      }
      const impactFields = ['treasury', 'revenue_delta', 'carbon_intensity_delta', 'reputation', 'resilience_factor', 'natural_capital_debt_delta', 'social_license_delta', 'social_license_score'];
      if (impactFields.includes(fieldName)) return target?.impacts?.[fieldName] ?? '';
      return target?.[fieldName] ?? '';
    } catch {
      return '';
    }
  };

  const isFieldModified = (paradigm, roundStr, optionKey, areaKey, fieldName) => {
    const pathKey = [paradigm, roundStr, areaKey || 'none', optionKey, fieldName].join('|');
    return localEdits[pathKey] !== undefined;
  };


  // Apply Climate Engine Parameters globally (not per-session, like the old Switchboard)
  const handleApplyClimateParams = async () => {
    setClimateApplying(true);
    setClimateMsg('');
    try {
      const res = await fetch(`${API}/api/admin/global-settings`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          simulation_mode: 'advanced_climate',
          global_carbon_fee: carbonFee,
          market_hostility_index: hostility,
          scope_3_threshold: scope3,
        }),
      });
      setClimateMsg(res.ok ? '✅ Climate parameters applied to engine.' : `⚠️ Backend returned ${res.status} — saved locally.`);
    } catch {
      setClimateMsg('⚠️ Backend offline — parameters saved in UI state only.');
    } finally {
      setClimateApplying(false);
      setTimeout(() => setClimateMsg(''), 4000);
    }
  };

  const PARADIGMS = [
    {
      key: 'legacy_abc',
      icon: (
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <rect x="2" y="4" width="24" height="5" rx="2" fill="currentColor" opacity="0.9"/>
          <rect x="2" y="12" width="24" height="5" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="2" y="20" width="24" height="5" rx="2" fill="currentColor" opacity="0.35"/>
        </svg>
      ),
      title: 'Narrative Crises',
      subtitle: 'A / B / C Options',
      description: 'Each round presents a curated crisis scenario with three strategic response options.',
      features: ['Story-driven decision making', 'Three options per round', 'Pre-defined impact paths'],
      color: '#6366f1',
    },
    {
      key: 'multi_toggles',
      icon: (
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <rect x="2" y="3" width="10" height="10" rx="3" fill="currentColor" opacity="0.9"/>
          <rect x="16" y="3" width="10" height="10" rx="3" fill="currentColor" opacity="0.7"/>
          <rect x="2" y="16" width="10" height="10" rx="3" fill="currentColor" opacity="0.55"/>
          <rect x="16" y="16" width="10" height="10" rx="3" fill="currentColor" opacity="0.4"/>
        </svg>
      ),
      title: 'Strategic Pillars',
      subtitle: '4-Area Toggles',
      description: 'Independent decisions across Energy, Operations, Supply Chain, and Offsetting.',
      features: ['Four strategic dimensions', 'Live cost aggregation', 'Granular control per area'],
      color: '#8b5cf6',
    },
    {
      key: 'advanced_climate',
      icon: (
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <circle cx="14" cy="14" r="10" stroke="currentColor" strokeWidth="2" opacity="0.6"/>
          <path d="M14 6 C14 6, 8 11, 8 16 C8 19.3 10.7 22 14 22 C17.3 22 20 19.3 20 16 C20 11 14 6 14 6Z"
            fill="currentColor" opacity="0.8"/>
          <path d="M11 15 L13 13 L15 16 L17 12" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        </svg>
      ),
      title: 'Advanced Climate Engine',
      subtitle: 'Physics-Based Scenario',
      description: 'Rounds 1 & 2 are identical to other paradigms. From Round 3, hard carbon taxation, regulatory hostility, and Scope 3 volatility engage — branching the simulation into an advanced physics track.',
      features: ['Rounds 1–2 shared with all paradigms', 'Configurable carbon fee ($/tonne)', 'Regulatory & NGO Hostility Index', 'Scope 3 threshold from Round 3'],
      color: '#10b981',
    },
  ];

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerIcon}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </div>
        <div>
          <h3 className={styles.headerTitle}>Decision Paradigm</h3>
          <p className={styles.headerSubtitle}>
            Select the decision-making framework for this cohort. This is a <strong>permanent</strong> choice.
          </p>
        </div>
      </div>

      {/* Session Selector */}
      <div className={styles.sessionSelect}>
        <label className={styles.sessionLabel}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          Cohort
        </label>
        <div className={styles.selectWrapper}>
          <select
            value={selectedSession}
            onChange={(e) => setSelectedSession(e.target.value)}
            className={styles.select}
          >
            <option value="">— Select a cohort session —</option>
            {(sessions || []).map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.cohort_name} ({s.short_code || s.session_id.slice(0, 8)})
              </option>
            ))}
          </select>
          <svg className={styles.selectChevron} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>

      {/* Lock Banner */}
      {locked && selectedSession && (
        <div className={styles.lockBanner}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          <span>Paradigm is permanently locked for this cohort</span>
        </div>
      )}

      {/* Toggle Cards */}
      <div className={styles.toggleGrid}>
        {PARADIGMS.map((p) => {
          const isActive = currentParadigm === p.key;
          const isDisabled = locked && !isActive;
          return (
            <div
              key={p.key}
              className={`${styles.card} ${isActive ? styles.cardActive : ''} ${isDisabled ? styles.cardDisabled : ''}`}
              onClick={() => !isDisabled && handleToggle(p.key)}
              style={{ '--accent': p.color }}
            >
              {/* Status Badge */}
              {isActive && (
                <div className={styles.badge}>
                  {locked ? (
                    <>
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                      </svg>
                      LOCKED
                    </>
                  ) : (
                    <>
                      <span className={styles.badgeDot} />
                      ACTIVE
                    </>
                  )}
                </div>
              )}

              {/* Card Icon */}
              <div className={styles.cardIconWrap} style={{ color: p.color }}>
                {p.icon}
              </div>

              {/* Card Content */}
              <div className={styles.cardBody}>
                <h4 className={styles.cardTitle}>{p.title}</h4>
                <span className={styles.cardSubtitle}>{p.subtitle}</span>
                <p className={styles.cardDesc}>{p.description}</p>
              </div>

              {/* Feature List */}
              <ul className={styles.featureList}>
                {p.features.map((f, i) => (
                  <li key={i}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      {/* ── Advanced Climate Engine Parameters (visible when that paradigm is active) ── */}
      {currentParadigm === 'advanced_climate' && (
        <div className={styles.climatePanel}>
          <div className={styles.climatePanelHeader}>
            <span className={styles.climatePanelIcon}>⚡</span>
            <div>
              <h4 className={styles.climatePanelTitle}>Climate Engine Parameters</h4>
              <p className={styles.climatePanelSub}>Configure the physics parameters for the Advanced Climate Engine. These apply globally to all cohorts using this path.</p>
            </div>
          </div>

          <div className={styles.climateSliders}>
            {/* Carbon Fee */}
            <div className={styles.sliderBlock}>
              <div className={styles.sliderMeta}>
                <span className={styles.sliderLabel}>Internal Carbon Fee</span>
                <span className={styles.sliderValue}><strong>${carbonFee}</strong> <span className={styles.sliderUnit}>/tonne</span></span>
              </div>
              <input type="range" className={styles.slider} min={20} max={150} step={1}
                value={carbonFee} onChange={(e) => setCarbonFee(Number(e.target.value))} />
              <div className={styles.sliderRange}><span>$20</span><span>$150</span></div>
            </div>

            {/* Hostility */}
            <div className={styles.sliderBlock}>
              <div className={styles.sliderMeta}>
                <span className={styles.sliderLabel}>Reg &amp; NGO Hostility</span>
                <span className={styles.sliderValue}><strong>{hostility}</strong> <span className={styles.sliderUnit}>/10</span></span>
              </div>
              <input type="range" className={styles.slider} min={1} max={10} step={1}
                value={hostility} onChange={(e) => setHostility(Number(e.target.value))} />
              <div className={styles.sliderRange}><span>Low</span><span>Critical</span></div>
            </div>

            {/* Scope 3 */}
            <div className={styles.sliderBlock}>
              <div className={styles.sliderMeta}>
                <span className={styles.sliderLabel}>Scope 3 Client Threshold</span>
                <span className={styles.sliderValue}><strong>{scope3.toFixed(1)}</strong> <span className={styles.sliderUnit}>kg CO₂e/unit</span></span>
              </div>
              <input type="range" className={styles.slider} min={1.0} max={5.0} step={0.1}
                value={scope3} onChange={(e) => setScope3(Number(e.target.value))} />
              <div className={styles.sliderRange}><span>1.0</span><span>5.0</span></div>
            </div>
          </div>

          {climateMsg && (
            <div className={`${styles.message} ${climateMsg.startsWith('✅') ? styles.messageSuccess : styles.messageWarn}`}>
              {climateMsg}
            </div>
          )}

          <button
            className={styles.climateApplyBtn}
            onClick={handleApplyClimateParams}
            disabled={climateApplying}
          >
            {climateApplying ? (
              <><span className={styles.spinner} /> Applying…</>
            ) : (
              <>⚡ Apply Parameters to Live Engine</>
            )}
          </button>
        </div>
      )}

      {saving && (
        <div className={styles.saving}>
          <span className={styles.spinner} />
          Saving…
        </div>
      )}
      {message && <div className={styles.message}>{message}</div>}

      {/* God Mode Matrix Editor Section */}
      <div className={styles.editorSection}>
        <div className={styles.editorHeader}>
          <h3>Global Default Overrides</h3>
          <p className={styles.headerSubtitle}>Edit base costs, emissions, and EBITDA impacts for every round.</p>
        </div>

        {!showEditor && (
          <div className={styles.gatePrompt}>
            <div className={styles.gateIcon}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
            <p className={styles.gateText}>The base simulation parameters are currently locked. Modifying these values will affect <strong>all cohorts</strong> and <strong>all future rounds</strong>.</p>
            <button
              className={styles.gateBtn}
              onClick={() => {
                if (confirm('⚠️ You are about to open the Global Default Overrides editor.\n\nChanges made here will affect ALL cohorts and ALL players.\n\nWould you like to proceed?')) {
                  setShowEditor(true);
                }
              }}
            >Change Base Parameters</button>
          </div>
        )}

        {showEditor && (<>

        {/* Dynamic Editor Tabs */}
        <div className={styles.editorTabs}>
          <button 
            className={`${styles.editorTab} ${activeEditorTab === 'legacy_abc' ? styles.editorTabActive : ''}`}
            onClick={() => setActiveEditorTab('legacy_abc')}
          >
            Narrative Crises Editor
          </button>
          <button 
            className={`${styles.editorTab} ${activeEditorTab === 'multi_toggles' ? styles.editorTabActive : ''}`}
            onClick={() => setActiveEditorTab('multi_toggles')}
          >
            Strategic Pillars Editor
          </button>
          <button 
            className={`${styles.editorTab} ${activeEditorTab === 'climate_engine' ? styles.editorTabActive : ''}`}
            onClick={() => setActiveEditorTab('climate_engine')}
            style={{ '--editorTabAccent': '#10b981' }}
          >
            ⚡ Climate Engine Editor
          </button>
        </div>

        {matrixLoading && <div style={{ padding: '2rem', textAlign: 'center' }}>Loading Game Matrices...</div>}
        
        {!matrixLoading && matrixData && matrixData.merged_narrative && activeEditorTab === 'legacy_abc' && (
          <div className={styles.tableWrapper}>
            <table className={styles.matrixTable}>
              <thead>
                <tr>
                  <th>Round</th>
                  <th>Option</th>
                  <th>Cost (Treasury)</th>
                  <th>EBITDA (Revenue Δ)</th>
                  <th>Carbon Δ</th>
                  <th>Reputation Δ</th>
                  <th>Resilience</th>
                  <th>Actions</th>
                </tr>
                <tr className={styles.defaultHeaderRow}>
                  <th colSpan={2} />
                  {['Cost','EBITDA','Carbon','Reputation','Resilience'].map(f => (
                    <th key={f} className={styles.defaultHeaderCell}>Default → Override</th>
                  ))}
                  <th />
                </tr>
              </thead>
              <tbody>
                {Object.keys(matrixData.merged_narrative).map(roundStr => {
                  const options = matrixData.merged_narrative[roundStr].options || {};
                  return Object.keys(options).map((optKey, idx) => (
                    <tr key={`${roundStr}-${optKey}`}>
                      {idx === 0 && (
                        <td rowSpan={Object.keys(options).length} className={styles.roundCell}>
                          Round {roundStr}
                        </td>
                      )}
                      <td className={styles.optionCell}>
                        <span className={styles.optionTitle}>{options[optKey].title || optKey}</span>
                        <span className={styles.optionId}>{optKey}</span>
                      </td>

                      {[['treasury','legacy_abc'],['revenue_delta','legacy_abc'],['carbon_intensity_delta','legacy_abc'],['reputation','legacy_abc'],['resilience_factor','legacy_abc']].map(([field]) => {
                        const serverVal = getServerDefault('legacy_abc', roundStr, optKey, null, field);
                        const modified = isFieldModified('legacy_abc', roundStr, optKey, null, field);
                        return (
                          <td key={field}>
                            <div className={styles.defaultValueLabel}>{serverVal !== '' ? serverVal : '—'}</div>
                            <input type="number"
                              className={`${styles.inputField} ${modified ? styles.modified : ''}`}
                              value={getResolvedValue('legacy_abc', roundStr, optKey, null, field)}
                              onChange={(e) => handleEditChange('legacy_abc', roundStr, optKey, null, field, e.target.value)}
                            />
                          </td>
                        );
                      })}

                      <td className={styles.actionCell}>
                        <button 
                          className={styles.saveBtn}
                          disabled={!isFieldModified('legacy_abc', roundStr, optKey, null, 'treasury') && 
                                    !isFieldModified('legacy_abc', roundStr, optKey, null, 'revenue_delta') &&
                                    !isFieldModified('legacy_abc', roundStr, optKey, null, 'carbon_intensity_delta') &&
                                    !isFieldModified('legacy_abc', roundStr, optKey, null, 'reputation') &&
                                    !isFieldModified('legacy_abc', roundStr, optKey, null, 'resilience_factor')}
                          onClick={() => handleSaveRow('legacy_abc', roundStr, optKey, null, ['treasury', 'revenue_delta', 'carbon_intensity_delta', 'reputation', 'resilience_factor'])}
                        >Save Edits</button>
                      </td>
                    </tr>
                  ));
                })}
              </tbody>
            </table>
          </div>
        )}

        {!matrixLoading && matrixData && matrixData.merged_pillars && activeEditorTab === 'multi_toggles' && (
          <div className={styles.tableWrapper}>
            <table className={styles.matrixTable}>
              <thead>
                <tr>
                  <th>Round</th>
                  <th>Area</th>
                  <th>Option</th>
                  <th>Cost (Treasury)</th>
                  <th>EBITDA</th>
                  <th>Carbon Δ</th>
                  <th>Reputation Δ</th>
                  <th>Resilience</th>
                  <th>Actions</th>
                </tr>
                <tr className={styles.defaultHeaderRow}>
                  <th colSpan={3} />
                  {['Cost','EBITDA','Carbon','Reputation','Resilience'].map(f => (
                    <th key={f} className={styles.defaultHeaderCell}>Default → Override</th>
                  ))}
                  <th />
                </tr>
              </thead>
              <tbody>
                {Object.keys(matrixData.merged_pillars).map(roundStr => {
                  const areasDict = matrixData.merged_pillars[roundStr].areas || {};

                  return Object.keys(areasDict).map((areaKey, areaIdx) => {
                    const options = areasDict[areaKey].options || {};
                    return Object.keys(options).map((optKey, optIdx) => (
                      <tr key={`${roundStr}-${areaKey}-${optKey}`}>
                        {areaIdx === 0 && optIdx === 0 && (
                          <td
                            rowSpan={Object.values(areasDict).reduce((acc, a) => acc + Object.keys(a.options || {}).length, 0)}
                            className={styles.roundCell}
                          >
                            Round {roundStr}
                          </td>
                        )}
                        {optIdx === 0 && (
                          <td rowSpan={Object.keys(options).length} style={{ fontWeight: '500', color: '#64748b' }}>
                            {areasDict[areaKey].label || areaKey}
                          </td>
                        )}

                        <td className={styles.optionCell}>
                          <span className={styles.optionTitle}>{options[optKey].title || optKey}</span>
                          <span className={styles.optionId}>{optKey}</span>
                        </td>

                        {[['cost','multi_toggles'],['revenue_delta','multi_toggles'],['carbon_intensity_delta','multi_toggles'],['reputation','multi_toggles'],['resilience_factor','multi_toggles']].map(([field]) => {
                          const serverVal = getServerDefault('multi_toggles', roundStr, optKey, areaKey, field);
                          const modified = isFieldModified('multi_toggles', roundStr, optKey, areaKey, field);
                          return (
                            <td key={field}>
                              <div className={styles.defaultValueLabel}>{serverVal !== '' ? serverVal : '—'}</div>
                              <input type="number"
                                className={`${styles.inputField} ${modified ? styles.modified : ''}`}
                                value={getResolvedValue('multi_toggles', roundStr, optKey, areaKey, field)}
                                onChange={(e) => handleEditChange('multi_toggles', roundStr, optKey, areaKey, field, e.target.value)}
                              />
                            </td>
                          );
                        })}

                        <td className={styles.actionCell}>
                          <button 
                            className={styles.saveBtn}
                            disabled={!isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'cost') && 
                                      !isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'revenue_delta') &&
                                      !isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'carbon_intensity_delta') &&
                                      !isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'reputation') &&
                                      !isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'resilience_factor')}
                            onClick={() => handleSaveRow('multi_toggles', roundStr, optKey, areaKey, ['cost', 'revenue_delta', 'carbon_intensity_delta', 'reputation', 'resilience_factor'])}
                          >Save Edits</button>
                        </td>
                      </tr>
                    ));
                  });
                })}
              </tbody>
            </table>
          </div>
        )}

        {!matrixLoading && matrixData && !matrixData.merged_narrative && activeEditorTab === 'legacy_abc' && (
          <div className={styles.message}>⚠️ Narrative Crises data is unavailable. The backend may need to be restarted.</div>
        )}

        {!matrixLoading && matrixData && !matrixData.merged_pillars && activeEditorTab === 'multi_toggles' && (
          <div className={styles.message}>⚠️ Strategic Pillars data is unavailable. The backend may need to be restarted.</div>
        )}

        {/* ─── Advanced Climate Engine Editor ─── */}
        {activeEditorTab === 'climate_engine' && (() => {
          const groups = [
            {
              label: '🌡️ Global Physics Parameters',
              desc: 'Applied from Round 3 via /api/admin/global-settings',
              rows: [
                { key: 'global_carbon_fee', label: 'Internal Carbon Fee', unit: '$/tonne', min: 20, max: 150, step: 1, default: 40, hint: 'Per-tonne carbon price applied to all BU decisions from R3' },
                { key: 'market_hostility_index', label: 'Reg & NGO Hostility Index', unit: '/10', min: 1, max: 10, step: 1, default: 5, hint: 'Modulates reputational penalty on high-carbon choices' },
                { key: 'scope_3_threshold', label: 'Scope 3 Client Threshold', unit: 'kg CO₂e/unit', min: 1.0, max: 5.0, step: 0.1, default: 2.5, hint: 'Supply chain clients above this intensity trigger disruption events' },
              ],
            },
            {
              label: '🌪️ R5 — Stochastic Climate Event',
              desc: 'Controls the cyclone / flood probability event at Round 5',
              rows: [
                { key: 'r5_base_damage', label: 'Base Physical Damage', unit: '$', min: 0, max: 50000000, step: 1000000, default: 12000000, hint: 'Treasury loss when stochastic roll < threshold. Mitigated by resilience_factor.' },
                { key: 'r5_stochastic_threshold', label: 'Event Strike Probability', unit: 'roll < threshold', min: 0.1, max: 1.0, step: 0.05, default: 0.75, hint: 'Probability (0–1) that the physical climate event actually strikes' },
              ],
            },
            {
              label: '🏁 R10 — Grand Finale Terminal EBITDA',
              desc: 'Terminal valuation engine parameters',
              rows: [
                { key: 'r10_carbon_tax_per_ton', label: 'Carbon Tax per Tonne (Year 3)', unit: '$/tonne', min: 50, max: 1000, step: 10, default: 250, hint: 'Terminal_EBITDA = Σ(Rev−OPEX) − (CarbonTonnage × this rate)' },
                { key: 'r10_exit_multiple', label: 'Exit Multiple', unit: '×', min: 5, max: 25, step: 0.5, default: 12.0, hint: 'Terminal Value = Terminal_EBITDA × Exit Multiple × M_R' },
              ],
            },
            {
              label: '♻️ Regenerative Multiple (M_R) Bonuses',
              desc: 'Adjustments to the M_R multiplier based on strategic choices',
              rows: [
                { key: 'mr_synergy_bonus', label: 'R7 Synergy Achieved (Circular)', unit: '+', min: 0, max: 1, step: 0.05, default: 0.30, hint: '+bonus if synergy_unlock or waste_to_energy flag is set from R7' },
                { key: 'mr_resilience_bonus', label: 'Survived R5/R8 Without Bailout', unit: '+', min: 0, max: 1, step: 0.05, default: 0.20, hint: '+bonus if no insurance_only or electronics_water_priority flags' },
                { key: 'mr_truth_premium', label: 'R6 Truth Premium (Ethical AI)', unit: '+', min: 0, max: 1, step: 0.05, default: 0.15, hint: '+bonus if ethical_ai_overhaul flag is set from R6' },
                { key: 'mr_instability_discount', label: 'Instability Discount (SLO < 75)', unit: '−', min: -1, max: 0, step: 0.05, default: -0.40, hint: 'Penalty deducted if avg Social License < 75 at R10' },
              ],
            },
            {
              label: '📊 Profile Archetype Thresholds',
              desc: 'M_R score boundaries for the four Year 3 outcome profiles',
              rows: [
                { key: 'profile_regenerative_titan', label: 'Regenerative Titan (M_R ≥)', unit: '', min: 1.0, max: 3.0, step: 0.05, default: 1.8, hint: 'Players at or above this M_R score earn "The Regenerative Titan"' },
                { key: 'profile_derisked_safe_haven', label: 'De-risked Safe-Haven (M_R ≥)', unit: '', min: 0.5, max: 2.0, step: 0.05, default: 1.2, hint: 'Players between this and the Titan threshold' },
                { key: 'profile_fragile_giant', label: 'Fragile Giant (M_R ≥)', unit: '', min: 0.0, max: 1.5, step: 0.05, default: 0.8, hint: 'Players between this and the Safe-Haven threshold' },
              ],
            },
            {
              label: '⚙️ Engine Constants',
              desc: 'Core simulation mechanics constants applied each round',
              rows: [
                { key: 'loan_interest_rate', label: 'Short-Term Loan Interest Rate', unit: '%', min: 0.01, max: 0.5, step: 0.01, default: 0.12, hint: 'Applied when CAPEX exceeds 20% of starting treasury' },
                { key: 'cost_of_capital', label: 'Base Cost of Capital', unit: '%', min: 0.01, max: 0.2, step: 0.005, default: 0.05, hint: 'Base rate for Natural Capital Cost of Debt calculation per BU' },
                { key: 'synergy_gate_threshold', label: 'R10 Synergy Gate (Option A)', unit: 'Synergy Score', min: 50, max: 100, step: 5, default: 80, hint: 'Minimum synergy score required to choose "Resist & Integrate" in R10' },
                { key: 'strike_probability', label: 'R9 Strike Probability', unit: 'roll < threshold', min: 0.1, max: 1.0, step: 0.05, default: 0.75, hint: 'Probability of worker strike when avg Social License < 50' },
              ],
            },
          ];

          const handleSaveClimateParam = async (key, value) => {
            setClimateOverrideSaving(true);
            setClimateOverrideMsg('');
            try {
              const res = await fetch(`${API}/api/admin/global-settings`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [key]: value }),
              });
              setClimateOverrideMsg(res.ok ? `✅ ${key} saved.` : `⚠️ Backend returned ${res.status} — saved locally.`);
            } catch {
              setClimateOverrideMsg('⚠️ Backend offline — changes stored in UI state only.');
            } finally {
              setClimateOverrideSaving(false);
              setTimeout(() => setClimateOverrideMsg(''), 3500);
            }
          };

          return (
            <div>
              {climateOverrideMsg && (
                <div className={`${styles.message} ${climateOverrideMsg.startsWith('✅') ? styles.messageSuccess : styles.messageWarn}`} style={{ marginBottom: '0.75rem' }}>
                  {climateOverrideMsg}
                </div>
              )}
              {groups.map((group) => (
                <div key={group.label} style={{ marginBottom: '1.5rem' }}>
                  <div style={{ marginBottom: '0.5rem' }}>
                    <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#065f46', marginBottom: '0.1rem' }}>{group.label}</div>
                    <div style={{ fontSize: '0.7rem', color: '#6b7280' }}>{group.desc}</div>
                  </div>
                  <div className={styles.tableWrapper}>
                    <table className={styles.matrixTable}>
                      <thead>
                        <tr>
                          <th>Parameter</th>
                          <th style={{ textAlign: 'center' }}>Default</th>
                          <th style={{ textAlign: 'center' }}>Override Value</th>
                          <th>Notes</th>
                          <th style={{ textAlign: 'center' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {group.rows.map((row) => {
                          const current = climateOverrides[row.key];
                          const isDirty = current !== row.default;
                          return (
                            <tr key={row.key}>
                              <td>
                                <div style={{ fontWeight: 600, fontSize: '0.78rem', color: '#1e293b' }}>{row.label}</div>
                                <div style={{ fontSize: '0.62rem', color: '#94a3b8', fontFamily: 'monospace' }}>{row.key}</div>
                              </td>
                              <td style={{ textAlign: 'center' }}>
                                <span style={{ fontSize: '0.75rem', color: '#64748b', fontVariantNumeric: 'tabular-nums' }}>
                                  {row.default}{row.unit}
                                </span>
                              </td>
                              <td style={{ textAlign: 'center' }}>
                                <input
                                  type="number"
                                  className={`${styles.inputField} ${isDirty ? styles.modified : ''}`}
                                  value={current}
                                  min={row.min}
                                  max={row.max}
                                  step={row.step}
                                  onChange={(e) => {
                                    const v = parseFloat(e.target.value);
                                    if (!isNaN(v)) setClimateOverrides(prev => ({ ...prev, [row.key]: v }));
                                  }}
                                  style={{ width: 110 }}
                                />
                                {row.unit && <span style={{ marginLeft: 4, fontSize: '0.66rem', color: '#94a3b8' }}>{row.unit}</span>}
                              </td>
                              <td style={{ fontSize: '0.7rem', color: '#64748b', lineHeight: 1.4, maxWidth: 260 }}>{row.hint}</td>
                              <td className={styles.actionCell}>
                                <button
                                  className={styles.saveBtn}
                                  disabled={!isDirty || climateOverrideSaving}
                                  onClick={() => handleSaveClimateParam(row.key, current)}
                                  style={isDirty ? { background: 'linear-gradient(135deg, #10b981, #059669)' } : {}}
                                >Save</button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          );
        })()}

        {!matrixLoading && !matrixData && (
          <div className={styles.message}>❌ Failed to load decision configurations. Check that the backend is running.</div>
        )}
        </>)}
      </div>

    </div>
  );
}
