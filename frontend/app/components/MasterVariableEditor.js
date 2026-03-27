'use client';
import { useState, useEffect } from 'react';
import styles from './MasterVariableEditor.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function MasterVariableEditor() {
    const [settings, setSettings] = useState(null);
    const [status, setStatus] = useState('');
    const [error, setError] = useState('');
    const [saving, setSaving] = useState(false);

    // Editable Local State
    const [form, setForm] = useState({
        corporate_treasury_start: 25000000,
        cost_of_capital_start: 0.05,
        loan_interest_rate_start: 0.12,
        group_reputation_start: 50.0,
        synergy_multiplier_start: 1.0,
        imitation_decay_rate_start: 0.05,
        market_hostility_index: 5,
        global_carbon_fee: 40,
        green_transition_fund_start: 0,
    });

    const load = async () => {
        try {
            const res = await fetch(`${API}/api/admin/god/settings`);
            if (res.ok) {
                const data = await res.json();
                setSettings(data);
                setForm(prev => ({
                    corporate_treasury_start: data.corporate_treasury_start ?? prev.corporate_treasury_start,
                    cost_of_capital_start: data.cost_of_capital_start ?? prev.cost_of_capital_start,
                    loan_interest_rate_start: data.loan_interest_rate_start ?? prev.loan_interest_rate_start,
                    group_reputation_start: data.group_reputation_start ?? prev.group_reputation_start,
                    synergy_multiplier_start: data.synergy_multiplier_start ?? prev.synergy_multiplier_start,
                    imitation_decay_rate_start: data.imitation_decay_rate_start ?? prev.imitation_decay_rate_start,
                    market_hostility_index: data.market_hostility_index ?? prev.market_hostility_index,
                    global_carbon_fee: data.global_carbon_fee ?? prev.global_carbon_fee,
                    green_transition_fund_start: data.green_transition_fund_start ?? prev.green_transition_fund_start,
                }));
            }
        } catch (e) {
            setError('Failed to load global settings from server.');
        }
    };

    useEffect(() => { load(); }, []);

    const handleChange = (key, val) => {
        setForm(prev => ({ ...prev, [key]: Number(val) }));
    };

    const handleSave = async () => {
        setSaving(true);
        setStatus('');
        setError('');
        try {
            const res = await fetch(`${API}/api/admin/god/settings`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            });
            if (res.ok) {
                setStatus('✅ Master variables successfully overwritten for all future instances.');
                load();
            } else {
                setError('Failed to update master variables.');
            }
        } catch {
            setError('Network error occurred.');
        } finally {
            setSaving(false);
        }
    };

    if (!settings) return <div className={styles.loading}>Loading exhaustive master tables…</div>;

    const hasChanges = Object.keys(form).some(k => form[k] !== (settings[k] ?? form[k]));

    const CB = ({children, math}) => (
        <span className={`${styles.codeBadge} ${math ? styles.mathBadge : ''}`}>{children}</span>
    );

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.titleArea}>
                    <span className={styles.icon}>🎛️</span>
                    <div>
                        <h2>Master Variables</h2>
                        <p className={styles.subtitle}>Exhaustive global dataset. Overrides defaults applied to newly created pristine simulation cohorts.</p>
                    </div>
                </div>
                <button 
                    className={styles.saveBtn} 
                    onClick={handleSave}
                    disabled={saving || !hasChanges}
                >
                    {saving ? 'Saving Constants...' : 'Publish Globals'}
                </button>
            </div>

            {status && <div className={styles.statusMsg}>{status}</div>}
            {error && <div className={`${styles.statusMsg} ${styles.errorMsg}`}>{error}</div>}

            {/* 1. Global Economic Vectors */}
            <h3 className={styles.sectionTitle}>1. Global Economic & Capital Vectors</h3>
            <div className={styles.tableWrapper}>
                <table className={styles.masterTable}>
                    <thead>
                        <tr>
                            <th style={{width: '15%'}}>Variable</th>
                            <th style={{width: '10%'}}>Scope</th>
                            <th style={{width: '15%'}}>Default Start</th>
                            <th style={{width: '15%'}}>Clamped Boundary</th>
                            <th style={{width: '45%'}}>Math / Trigger Logic</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><CB>corporate_treasury</CB></td>
                            <td>Global</td>
                            <td><input type="number" className={styles.numberInput} value={form.corporate_treasury_start} onChange={e => handleChange('corporate_treasury_start', e.target.value)} /></td>
                            <td><CB>[-$500M, +∞]</CB></td>
                            <td>Master cash pool. If <code>&lt; 0</code>, mathematically attracts <CB math>abs(treasury) * cost_of_capital</CB> interest. Clamped rigidly at <CB>-$500,000,000</CB> to halt infinite Javascript insolvency limits.</td>
                        </tr>
                        <tr>
                            <td><CB>cost_of_capital</CB></td>
                            <td>Global</td>
                            <td><input type="number" step="0.01" className={styles.numberInput} value={form.cost_of_capital_start} onChange={e => handleChange('cost_of_capital_start', e.target.value)} /></td>
                            <td><CB>[0.05, 1.0]</CB></td>
                            <td>Interest rate applied dynamically to negative treasury balances. Spikes permanently by <CB>+0.015</CB> (1.5%) round-over-round if any single BU holds a <CB>carbon_intensity &gt; 120</CB>.</td>
                        </tr>
                        <tr>
                            <td><CB>loan_interest_rate</CB></td>
                            <td>Global</td>
                            <td><input type="number" step="0.01" className={styles.numberInput} value={form.loan_interest_rate_start} onChange={e => handleChange('loan_interest_rate_start', e.target.value)} /></td>
                            <td><CB>[0.0, 1.0]</CB></td>
                            <td>Instantaneous loan rate charged if <CB>total_capex_requested</CB> across all 4 BUs exceeds <CB>base_treasury * 0.20</CB> within a single round.</td>
                        </tr>
                        <tr>
                            <td><CB>dividends_paid</CB></td>
                            <td>Global</td>
                            <td><span className={styles.readOnlyText}>0.0</span></td>
                            <td><CB>[0.0, treasury]</CB></td>
                            <td>Selected explicitly by the player. Mathematically capped by the UI to never physically exceed the <CB>base_treasury</CB> balance.</td>
                        </tr>
                        <tr>
                            <td><CB>historical_ebitda</CB></td>
                            <td>Global</td>
                            <td><span className={styles.readOnlyText}>Derived</span></td>
                            <td><CB>[0.0, +∞]</CB></td>
                            <td>Group-level gross profit proxy calculated each tick: <CB math>Σ(revenue_base - opex_base)</CB> across all BUs.</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            {/* 2. Global Reputational Vectors */}
            <h3 className={styles.sectionTitle}>2. Global Reputational & Contagion Vectors</h3>
            <div className={styles.tableWrapper}>
                <table className={styles.masterTable}>
                    <thead>
                        <tr>
                            <th style={{width: '15%'}}>Variable</th>
                            <th style={{width: '10%'}}>Scope</th>
                            <th style={{width: '15%'}}>Default Start</th>
                            <th style={{width: '15%'}}>Clamped Boundary</th>
                            <th style={{width: '45%'}}>Math / Trigger Logic</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><CB>group_reputation</CB></td>
                            <td>Global</td>
                            <td><input type="number" className={styles.numberInput} value={form.group_reputation_start} onChange={e => handleChange('group_reputation_start', e.target.value)} /></td>
                            <td><CB>[0.0, 100.0]</CB></td>
                            <td>Master resilience stat. Suppresses structural damage inside <CB math>calc_contagion()</CB> when <CB>crisis_severity</CB> initiates. Hard-drops <CB>-20</CB> If AI Bias (R6) is exploited.</td>
                        </tr>
                        <tr>
                            <td><CB>crisis_severity</CB></td>
                            <td>Global (Tick)</td>
                            <td><span className={styles.readOnlyText}>0.0 - 50.0</span></td>
                            <td><CB>[0.0, 100.0]</CB></td>
                            <td>Base reputational or structural damage incoming from a round's narrative event. <CB math>Contagion Damage = severity * (1.0 - group_reputation/100)</CB>.</td>
                        </tr>
                        <tr>
                            <td><CB>synergy_multiplier</CB></td>
                            <td>Global</td>
                            <td><input type="number" step="0.1" className={styles.numberInput} value={form.synergy_multiplier_start} onChange={e => handleChange('synergy_multiplier_start', e.target.value)} /></td>
                            <td><CB>[1.0, 1.35x]</CB></td>
                            <td>Lowers global OPEX through the <CB math>calc_synergy_opex</CB> formula. Option C in R7 unlocks a massive <CB>+0.35</CB> multiplier, heavily boosting profitability.</td>
                        </tr>
                        <tr>
                            <td><CB>imitation_decay_rate</CB></td>
                            <td>Universal</td>
                            <td><input type="number" step="0.01" className={styles.numberInput} value={form.imitation_decay_rate_start} onChange={e => handleChange('imitation_decay_rate_start', e.target.value)} /></td>
                            <td><CB>[0.0, 1.0]</CB></td>
                            <td>The "VRIO Advantage Bleed." Mathematically decays the <CB>synergy_multiplier</CB> passively by 5% every turn to simulate competitors catching up.</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            {/* 3. Advanced Climate Engine Mechanics */}
            <h3 className={styles.sectionTitle}>3. Advanced Climate Engine Mechanics</h3>
            <div className={styles.tableWrapper}>
                <table className={styles.masterTable}>
                    <thead>
                        <tr>
                            <th style={{width: '15%'}}>Variable</th>
                            <th style={{width: '10%'}}>Scope</th>
                            <th style={{width: '15%'}}>Default Start</th>
                            <th style={{width: '15%'}}>Clamped Boundary</th>
                            <th style={{width: '45%'}}>Math / Trigger Logic</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><CB>market_hostility_index</CB></td>
                            <td>Global</td>
                            <td><input type="number" className={styles.numberInput} value={form.market_hostility_index} onChange={e => handleChange('market_hostility_index', e.target.value)} /></td>
                            <td><CB>[1.0, 5.0]</CB></td>
                            <td>Abstract scalar. In Advanced Climate mode, determines Toxic NCD OPEX penalties: <CB math>NCD * 50,000 * hostility</CB>. Multiplies by 2 if Tipping Point triggers.</td>
                        </tr>
                        <tr>
                            <td><CB>tipping_point_active</CB></td>
                            <td>Global Toggle</td>
                            <td><span className={styles.readOnlyText}>False</span></td>
                            <td><CB>True/False</CB></td>
                            <td>Triggered irreversibly in <CB>Round &gt;= 5</CB> if the group's <CB math>avg(carbon_intensity) &gt; 100</CB>. Permanently doubles the <CB>market_hostility_index</CB>.</td>
                        </tr>
                        <tr>
                            <td><CB>green_transition_fund</CB></td>
                            <td>Global</td>
                            <td><input type="number" className={styles.numberInput} value={form.green_transition_fund_start} onChange={e => handleChange('green_transition_fund_start', e.target.value)} /></td>
                            <td><CB>[0, +∞]</CB></td>
                            <td>Accrues via internal taxation. Every round: <CB math>green_fund += tco2e_emissions * carbon_fee_per_ton</CB>. Can explicitly offset R7, R8, R9 systemic CapEx requirements automatically.</td>
                        </tr>
                        <tr>
                            <td><CB>carbon_fee_per_ton</CB></td>
                            <td>Global</td>
                            <td><input type="number" className={styles.numberInput} value={form.global_carbon_fee} onChange={e => handleChange('global_carbon_fee', e.target.value)} /></td>
                            <td><CB>[0, 1000]</CB></td>
                            <td>Internal tax rate parameter. Spikes to <CB>$250</CB> automatically at R10 (Year 3) Terminal Valuation calculation.</td>
                        </tr>
                        <tr>
                            <td><CB>resilience_factor</CB></td>
                            <td>Event Toggle</td>
                            <td><span className={styles.readOnlyText}>0.0</span></td>
                            <td><CB>[0.0, 1.0]</CB></td>
                            <td>Stored in the <CB>pending_capex_projects</CB> array. When R5 Hard-Engineering completes after a 2-round delay, it is extracted as <CB>active_resilience_factor</CB> (usually <CB>0.85</CB>) mitigating stochastic cyclone damage.</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            {/* 4. Business Unit (BU) Sub-Level Metrics */}
            <h3 className={styles.sectionTitle}>4. Business Unit (BU) Sub-Level Metrics</h3>
            <div className={styles.tableWrapper}>
                <table className={styles.masterTable}>
                    <thead>
                        <tr>
                            <th style={{width: '15%'}}>Variable</th>
                            <th style={{width: '10%'}}>Scope</th>
                            <th style={{width: '15%'}}>Default Start</th>
                            <th style={{width: '15%'}}>Clamped Boundary</th>
                            <th style={{width: '45%'}}>Math / Trigger Logic</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><CB>natural_capital_debt</CB></td>
                            <td>BU Level</td>
                            <td><span className={styles.readOnlyText}>Phar: 10, Elec: 25, Other: 0</span></td>
                            <td><CB>[0, 1,000,000]</CB></td>
                            <td>Accrues <CB>cost_of_capital</CB> simple interest. Penalizes OPEX in Advanced Climate mathematically: <CB math>bu_opex += (NCD * 50_000 * hostility) / 1,000,000</CB>.</td>
                        </tr>
                        <tr>
                            <td><CB>carbon_intensity</CB></td>
                            <td>BU Level</td>
                            <td><span className={styles.readOnlyText}>Phar: 45, Elec: 72, Cons: 38, Soft: 28</span></td>
                            <td><CB>[0, +∞]</CB></td>
                            <td>Tracks fossil fuel reliance. Trigger array: <CB>&gt; 120</CB> = Stranded Asset (+1.5% CoC debt multiplier). <CB>Avg &gt; 100</CB> = Tipping Point.</td>
                        </tr>
                        <tr>
                            <td><CB>social_license_score</CB></td>
                            <td>BU Level</td>
                            <td><span className={styles.readOnlyText}>Soft: 60, Phar: 55, Other: ~50</span></td>
                            <td><CB>[0.0, 100.0]</CB></td>
                            <td>Local community trust. Determines Strike Probability in R9: <CB math>p = calc_strike_probability(base_risk, social_license)</CB>. If <CB>avg(SL) &lt; 50</CB> in R9, probability overrides to 75% for catastrophic Revenue zeroization.</td>
                        </tr>
                        <tr>
                            <td><CB>governance_risk_score</CB></td>
                            <td>BU Level</td>
                            <td><span className={styles.readOnlyText}>Elec: 20, Phar: 15, Other: &lt;=10</span></td>
                            <td><CB>[0.0, 100.0]</CB></td>
                            <td>Spikes heavily (+10) via Supply Chain disruptions in R3. Acts as the <CB>base_risk</CB> multiplier for strikes, and informs the VRIO <CB>organization</CB> vector.</td>
                        </tr>
                        <tr>
                            <td><CB>revenue_base</CB></td>
                            <td>BU Level</td>
                            <td><span className={styles.readOnlyText}>$8M - $18M</span></td>
                            <td><CB>[0, +∞]</CB></td>
                            <td>Top-line revenue per BU unit. Mathematically zeroed out ($0) entirely dynamically by labor union strikes executing in R9.</td>
                        </tr>
                        <tr>
                            <td><CB>opex_base</CB></td>
                            <td>BU Level</td>
                            <td><span className={styles.readOnlyText}>$4M - $11M</span></td>
                            <td><CB>[0, +∞]</CB></td>
                            <td>Operating expenses per BU. Capped at a hard boundary of <CB>0.0</CB>. Drops geometrically through <CB>synergy_multiplier</CB> and spikes via NCD penalties.</td>
                        </tr>
                        <tr>
                            <td><CB>water_dependency</CB></td>
                            <td>BU Level</td>
                            <td><span className={styles.readOnlyText}>Phar: 82, Elec: 58, Cons: 65, Soft: 12</span></td>
                            <td><CB>[0, 100]</CB></td>
                            <td>Mostly narrative impact, but dynamically modified (delta) based on the structural decisions surrounding Desalination Plants in Round 8.</td>
                        </tr>
                        <tr>
                            <td><CB>talent_penalty</CB></td>
                            <td>BU (Software)</td>
                            <td><span className={styles.readOnlyText}>$0</span></td>
                            <td><CB>[0, opex]</CB></td>
                            <td>Exclusive to the Software BU. Emulates Brain-Drain by adding overhead. Derived exponentially against dropping <CB>group_reputation</CB>.</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div style={{height: '2rem'}}></div>
        </div>
    );
}
