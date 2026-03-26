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

  // -- Matrix Editor State --
  const [matrixData, setMatrixData] = useState(null);
  const [matrixLoading, setMatrixLoading] = useState(true);
  const [activeEditorTab, setActiveEditorTab] = useState('legacy_abc'); // legacy_abc | multi_toggles
  const [localEdits, setLocalEdits] = useState({});
  const [showEditor, setShowEditor] = useState(false);

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

  const handleToggle = async (paradigm) => {
    if (!selectedSession) {
      setMessage('⚠️ Select a session first.');
      return;
    }
    if (locked) {
      setMessage('🔒 Paradigm is locked for this cohort and cannot be changed.');
      return;
    }
    const label = paradigm === 'legacy_abc' ? 'Narrative Crises (A/B/C)' : 'Strategic Pillars (4-Area)';
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
        setMessage(`✅ Paradigm locked to "${paradigm === 'legacy_abc' ? 'Narrative Crises' : 'Strategic Pillars'}" — this cannot be changed.`);
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
    
    // Drill into merged config
    if (!matrixData) return '';
    try {
      let target = null;
      if (paradigm === 'legacy_abc') {
        target = matrixData.merged_narrative[roundStr]?.options?.[optionKey];
      } else {
        target = matrixData.merged_pillars[roundStr]?.areas?.[areaKey]?.options?.[optionKey];
      }
      
      const impactFields = ['treasury', 'revenue_delta', 'carbon_intensity_delta', 'reputation', 'resilience_factor', 'natural_capital_debt_delta', 'social_license_delta', 'social_license_score'];
      
      if (impactFields.includes(fieldName)) {
        return target?.impacts?.[fieldName] ?? '';
      }
      return target?.[fieldName] ?? '';
    } catch {
      return '';
    }
  };

  const isFieldModified = (paradigm, roundStr, optionKey, areaKey, fieldName) => {
    const pathKey = [paradigm, roundStr, areaKey || 'none', optionKey, fieldName].join('|');
    return localEdits[pathKey] !== undefined;
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
        </div>

        {matrixLoading && <div style={{ padding: '2rem', textAlign: 'center' }}>Loading Game Matrices...</div>}
        
        {!matrixLoading && matrixData && matrixData.merged_narrative && activeEditorTab === 'legacy_abc' && (
          <div className={styles.tableWrapper}>
            <table className={styles.matrixTable}>
              <thead>
                <tr>
                  <th>Round</th>
                  <th>Option Key</th>
                  <th>Cost (Treasury)</th>
                  <th>EBITDA (Revenue Delta)</th>
                  <th>Carbon Emission</th>
                  <th>Reputation</th>
                  <th>Resilience</th>
                  <th>Actions</th>
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
                      
                      {/* Cost */}
                      <td>
                        <input type="number" 
                          className={`${styles.inputField} ${isFieldModified('legacy_abc', roundStr, optKey, null, 'treasury') ? styles.modified : ''}`}
                          value={getResolvedValue('legacy_abc', roundStr, optKey, null, 'treasury')}
                          onChange={(e) => handleEditChange('legacy_abc', roundStr, optKey, null, 'treasury', e.target.value)}
                        />
                      </td>
                      
                      {/* EBITDA */}
                      <td>
                        <input type="number" 
                          className={`${styles.inputField} ${isFieldModified('legacy_abc', roundStr, optKey, null, 'revenue_delta') ? styles.modified : ''}`}
                          value={getResolvedValue('legacy_abc', roundStr, optKey, null, 'revenue_delta')}
                          onChange={(e) => handleEditChange('legacy_abc', roundStr, optKey, null, 'revenue_delta', e.target.value)}
                        />
                      </td>

                      {/* Carbon Emission */}
                      <td>
                        <input type="number" 
                          className={`${styles.inputField} ${isFieldModified('legacy_abc', roundStr, optKey, null, 'carbon_intensity_delta') ? styles.modified : ''}`}
                          value={getResolvedValue('legacy_abc', roundStr, optKey, null, 'carbon_intensity_delta')}
                          onChange={(e) => handleEditChange('legacy_abc', roundStr, optKey, null, 'carbon_intensity_delta', e.target.value)}
                        />
                      </td>

                      {/* Reputation */}
                      <td>
                        <input type="number" 
                          className={`${styles.inputField} ${isFieldModified('legacy_abc', roundStr, optKey, null, 'reputation') ? styles.modified : ''}`}
                          value={getResolvedValue('legacy_abc', roundStr, optKey, null, 'reputation')}
                          onChange={(e) => handleEditChange('legacy_abc', roundStr, optKey, null, 'reputation', e.target.value)}
                        />
                      </td>

                      {/* Resilience */}
                      <td>
                        <input type="number" 
                          className={`${styles.inputField} ${isFieldModified('legacy_abc', roundStr, optKey, null, 'resilience_factor') ? styles.modified : ''}`}
                          value={getResolvedValue('legacy_abc', roundStr, optKey, null, 'resilience_factor')}
                          onChange={(e) => handleEditChange('legacy_abc', roundStr, optKey, null, 'resilience_factor', e.target.value)}
                        />
                      </td>

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
                  <th>Option Key</th>
                  <th>Cost (Treasury)</th>
                  <th>EBITDA</th>
                  <th>Carbon Emission</th>
                  <th>Reputation</th>
                  <th>Resilience</th>
                  <th>Actions</th>
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

                        {/* Cost */}
                        <td>
                          <input type="number" 
                            className={`${styles.inputField} ${isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'cost') ? styles.modified : ''}`}
                            value={getResolvedValue('multi_toggles', roundStr, optKey, areaKey, 'cost')}
                            onChange={(e) => handleEditChange('multi_toggles', roundStr, optKey, areaKey, 'cost', e.target.value)}
                          />
                        </td>
                        
                         {/* EBITDA */}
                        <td>
                          <input type="number" 
                            className={`${styles.inputField} ${isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'revenue_delta') ? styles.modified : ''}`}
                            value={getResolvedValue('multi_toggles', roundStr, optKey, areaKey, 'revenue_delta')}
                            onChange={(e) => handleEditChange('multi_toggles', roundStr, optKey, areaKey, 'revenue_delta', e.target.value)}
                          />
                        </td>

                        {/* Carbon */}
                        <td>
                          <input type="number" 
                            className={`${styles.inputField} ${isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'carbon_intensity_delta') ? styles.modified : ''}`}
                            value={getResolvedValue('multi_toggles', roundStr, optKey, areaKey, 'carbon_intensity_delta')}
                            onChange={(e) => handleEditChange('multi_toggles', roundStr, optKey, areaKey, 'carbon_intensity_delta', e.target.value)}
                          />
                        </td>

                        {/* Reputation */}
                        <td>
                          <input type="number" 
                            className={`${styles.inputField} ${isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'reputation') ? styles.modified : ''}`}
                            value={getResolvedValue('multi_toggles', roundStr, optKey, areaKey, 'reputation')}
                            onChange={(e) => handleEditChange('multi_toggles', roundStr, optKey, areaKey, 'reputation', e.target.value)}
                          />
                        </td>

                        {/* Resilience */}
                        <td>
                          <input type="number" 
                            className={`${styles.inputField} ${isFieldModified('multi_toggles', roundStr, optKey, areaKey, 'resilience_factor') ? styles.modified : ''}`}
                            value={getResolvedValue('multi_toggles', roundStr, optKey, areaKey, 'resilience_factor')}
                            onChange={(e) => handleEditChange('multi_toggles', roundStr, optKey, areaKey, 'resilience_factor', e.target.value)}
                          />
                        </td>

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

        {!matrixLoading && !matrixData && (
          <div className={styles.message}>❌ Failed to load decision configurations. Check that the backend is running.</div>
        )}
        </>)}
      </div>

    </div>
  );
}
