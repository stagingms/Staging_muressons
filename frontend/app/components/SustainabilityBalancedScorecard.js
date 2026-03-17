'use client';

import { useMemo, useState, useRef } from 'react';
import {
    LineChart, Line, AreaChart, Area, ComposedChart,
    XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import styles from './SustainabilityBalancedScorecard.module.css';

// ═══════════════════════════════════════════════════════════════
//  DYNAMIC DIAGNOSTIC FEEDBACK
// ═══════════════════════════════════════════════════════════════

function diagnoseEBITDA(ebitda) {
    if (ebitda > 20_000_000) return "Exceptional earnings. Carbon tax was absorbed without material impact.";
    if (ebitda > 10_000_000) return "Solid EBITDA despite carbon liabilities. Group-level efficiencies are evident.";
    if (ebitda > 0) return "Marginal profitability. Carbon tax and OPEX bloat ate into operating margins.";
    return "Negative EBITDA. The business is loss-making — carbon costs exceeded operating income.";
}

function diagnoseGreenDebt(nrrs) {
    if (nrrs < 0.05) return "Minimal natural capital debt. Green bond rates remain favourable.";
    if (nrrs < 0.10) return "Moderate environmental liabilities. Cost of debt is trending upward.";
    if (nrrs < 0.20) return "Significant natural capital exposure. Lenders demand risk premiums.";
    return "Extreme environmental debt. Capital markets may refuse refinancing.";
}

function diagnoseReputation(rep) {
    if (rep >= 85) return "Best-in-class reputation. Stakeholders view Muressons as a sustainability leader.";
    if (rep >= 65) return "Above-average reputation. Room for improvement in community engagement.";
    if (rep >= 45) return "Below-average reputation. Media scrutiny and talent flight are increasing.";
    return "Severely damaged brand. Consumer boycotts and regulatory investigations imminent.";
}

function diagnoseSLO(slo) {
    if (slo >= 85) return "Strong social mandate. Communities actively support continued operations.";
    if (slo >= 75) return "Acceptable social licence. Avoided the -0.4 Instability Discount.";
    if (slo >= 50) return "Alienated stakeholders and triggered the -0.4 Instability Discount on M_R.";
    return "Social licence collapsed. Operations face legal challenges and protest blockades.";
}

function diagnoseSynergy(sy) {
    if (sy > 1.2) return "Excellent systems integration. Cross-BU circularity slashed internal OPEX.";
    if (sy > 1.0) return "Moderate synergy. Some cross-BU benefits, but full circularity not achieved.";
    if (sy >= 0.8) return "Weak synergy. Business units operate largely in silos.";
    return "Synergy destroyed. Divestiture or breakup has severed all cross-BU value chains.";
}

function diagnoseCarbon(tonnage) {
    if (tonnage < 50) return "Low-carbon portfolio. Well-positioned for net-zero regulatory environment.";
    if (tonnage < 150) return "Moderate carbon exposure. Some BUs still require decarbonisation investment.";
    if (tonnage < 300) return "High carbon footprint. Stranded asset risk is material.";
    return "Extreme carbon liability. Regulatory fines and carbon border adjustments are unavoidable.";
}

function diagnoseTalent(pTalent) {
    if (pTalent > 1.0) return "Toxic culture caused massive developer flight and OPEX bleed in the Software BU.";
    if (pTalent > 0.5) return "Moderate talent strain. Retention programs needed to stabilise the workforce.";
    return "Strong talent retention. The employer brand attracts top-tier sustainability professionals.";
}

function diagnoseJustTransition(passed) {
    if (passed) return "Just Transition commitments honoured. Communities and workers retained trust in leadership.";
    return "Just Transition failed. Displaced workers and communities have no safety net — reputational fallout severe.";
}

function diagnoseVRIO(active) {
    if (active) return "VRIO advantage sustained. Proprietary capabilities remain difficult to imitate.";
    return "VRIO advantage decayed. Competitors have replicated key capabilities — differentiation lost.";
}

// ═══════════════════════════════════════════════════════════════
//  CRITICAL ANALYSIS GENERATOR
// ═══════════════════════════════════════════════════════════════

function generateCriticalAnalysis(kpis, d, bus) {
    const strengths = [];
    const weaknesses = [];
    const missed = [];

    // Financial
    if (kpis.ebitda > 10_000_000) strengths.push("Maintained operating profitability despite carbon tax headwinds — a signal of cost discipline.");
    else weaknesses.push("Failed to achieve baseline profitability. Carbon costs overwhelmed operating income, suggesting insufficient decarbonisation earlier in the simulation.");

    if (kpis.greenDebt < 0.10) strengths.push("Natural capital debt remained manageable, keeping green bond rates competitive.");
    else weaknesses.push("Accumulated excessive natural capital debt, raising the cost of capital and limiting future investment capacity.");

    // Stakeholder
    if (kpis.groupRep >= 65) strengths.push("Group reputation remained strong, providing a buffer against regulatory and market scrutiny.");
    else weaknesses.push("Reputation collapsed below viability thresholds. This would trigger talent flight, consumer boycotts, and regulatory intervention in a real scenario.");

    if (kpis.avgSL >= 75) strengths.push("Social License to Operate held firm — communities support continued operations.");
    else {
        weaknesses.push("Social License fell below 75, triggering the -0.4 Instability Discount on the Regenerative Multiple.");
        missed.push("Earlier investment in community engagement and stakeholder relations could have prevented the SLO penalty.");
    }

    // Internal
    if (kpis.synergy > 1.1) strengths.push("Achieved meaningful industrial synergy through cross-BU circular economy integration.");
    else {
        weaknesses.push("Synergy multiplier remained near baseline — the four BUs operated as silos rather than an integrated system.");
        missed.push("Allocating CSF to OPEX Circularity and collaborative R&D across BUs would have unlocked cross-divisional symbiosis.");
    }

    if (kpis.carbonTonnage < 150) strengths.push("Carbon footprint reduced to manageable levels, minimising the 2050 carbon tax liability.");
    else weaknesses.push("Carbon tonnage remained dangerously high, resulting in a heavy tax burden that eroded terminal value.");

    // Learning
    if (kpis.pTalent <= 0.5) strengths.push("Talent retention remained stable — the employer brand attracted top sustainability professionals.");
    else weaknesses.push("Software BU experienced significant brain drain. The talent penalty multiplied OPEX costs and reduced innovation capacity.");

    if (kpis.vrioActive) strengths.push("VRIO competitive advantage sustained — proprietary capabilities remain a source of differentiation.");
    else {
        weaknesses.push("VRIO advantage decayed as competitors replicated key capabilities.");
        missed.push("Sustained R&D investment was needed to maintain the innovation moat against industry imitators.");
    }

    // Overall verdict
    const score = strengths.length;
    const total = strengths.length + weaknesses.length;
    let verdict;
    if (score >= total * 0.75) verdict = "The CSO demonstrated strong strategic acumen, balancing financial performance with sustainability commitments. The group emerges well-positioned for the next decade.";
    else if (score >= total * 0.5) verdict = "A mixed performance. While some metrics show promise, critical weaknesses remain unaddressed. The group faces an uncertain future requiring immediate strategic intervention.";
    else verdict = "The portfolio deteriorated significantly over the simulation period. Multiple KPIs fell below viability thresholds. Without radical restructuring, the group faces existential risk.";

    return { strengths, weaknesses, missed, verdict };
}

// ═══════════════════════════════════════════════════════════════
//  CONSTANTS
// ═══════════════════════════════════════════════════════════════

const PROFILES = {
    regenerative_titan: { icon: '🌱', gradient: 'linear-gradient(135deg, #10b981, #059669)', rank: 'APEX' },
    derisked_safe_haven: { icon: '🛡️', gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)', rank: 'SOLID' },
    fragile_giant: { icon: '⚠️', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', rank: 'AT RISK' },
    stranded_relic: { icon: '💀', gradient: 'linear-gradient(135deg, #ef4444, #b91c1c)', rank: 'TERMINAL' },
};

const PERSPECTIVE_ICONS = {
    financial: '💰',
    stakeholder: '🤝',
    internal: '⚙️',
    learning: '🎓',
};

const PERSPECTIVE_COLORS = {
    financial: '#3b82f6',
    stakeholder: '#10b981',
    internal: '#f59e0b',
    learning: '#8b5cf6',
};

/**
 * SustainabilityBalancedScorecard — Enhanced with Critical Analysis,
 * Round Review, and Download capability.
 *
 * New props:
 *  - history: array of round snapshots for review
 *  - onProceed: () => void — proceed to Boardroom Showdown
 */
export default function SustainabilityBalancedScorecard({ data, businessUnits = [], globalState = {}, history = [], onProceed, onClose }) {
    const d = data || {};
    const bus = businessUnits;
    const theme = PROFILES[d.profile] || PROFILES.fragile_giant;

    // Debug: log what data the scorecard receives
    console.log('[SCORECARD] data:', d);
    console.log('[SCORECARD] profile:', d.profile, '| ebitda_2050:', d.ebitda_2050, '| terminal_value:', d.terminal_value);
    console.log('[SCORECARD] bus:', bus.length, '| globalState keys:', Object.keys(globalState));
    console.log('[SCORECARD] history:', history.length, 'rounds');
    const [activeTab, setActiveTab] = useState('scorecard'); // 'scorecard' | 'analysis' | 'rounds'
    const printRef = useRef(null);

    // Compute derived KPIs
    const kpis = useMemo(() => {
        const sy = (globalState.synergy_multiplier || 1.0);
        const avgSL = d.avg_social_license || (bus.length > 0
            ? bus.reduce((s, b) => s + (b.social_license_score || 0), 0) / bus.length
            : 0);
        const groupRep = globalState.group_reputation || 0;
        const totalNCD = bus.reduce((s, b) => s + (b.natural_capital_debt || 0), 0);
        const greenDebtRate = totalNCD > 0 ? totalNCD * 0.0005 : 0;

        const softwareBU = bus.find(b => b.bu_id === 'software');
        const pTalent = softwareBU ? (softwareBU.talent_penalty || 0) : 0;

        const flags = globalState.active_event_flags || {};
        const allFlags = Object.values(flags).flat().filter(v => typeof v === 'string');

        const justTransitionPassed = allFlags.includes('just_transition_fund')
            || allFlags.includes('worker_retraining')
            || (d.r9_choice === 'option_a' || d.r9_choice === 'option_c');

        const vrioActive = (globalState.vrio_advantage || 0) > 0.3;

        return {
            ebitda: d.ebitda_2050 || 0,
            greenDebt: greenDebtRate,
            groupRep,
            avgSL,
            synergy: sy,
            carbonTonnage: d.carbon_tonnage_group || 0,
            pTalent,
            justTransitionPassed,
            vrioActive,
        };
    }, [d, bus, globalState]);

    // Critical analysis
    const analysis = useMemo(() => generateCriticalAnalysis(kpis, d, bus), [kpis, d, bus]);

    // MR Breakdown
    const mrBreakdown = d.mr_breakdown || {};
    const mrItems = Object.entries(mrBreakdown)
        .filter(([, val]) => val !== 0)
        .map(([key, val]) => ({ key, value: val }));

    const PERSPECTIVES = [
        {
            id: 'financial',
            title: 'Financial Perspective',
            metrics: [
                {
                    label: 'Adjusted EBITDA (2050)',
                    value: `$${(kpis.ebitda / 1_000_000).toFixed(2)}M`,
                    note: `After $${(d.carbon_tax_per_ton || 250)}/ton carbon tax`,
                    diagnostic: diagnoseEBITDA(kpis.ebitda),
                    health: kpis.ebitda > 10_000_000 ? 'good' : kpis.ebitda > 0 ? 'warn' : 'bad',
                },
                {
                    label: 'Green Cost of Debt (NRRS)',
                    value: `${(kpis.greenDebt * 100).toFixed(2)}%`,
                    note: 'Tied to Natural Capital Debt across BUs',
                    diagnostic: diagnoseGreenDebt(kpis.greenDebt),
                    health: kpis.greenDebt < 0.05 ? 'good' : kpis.greenDebt < 0.15 ? 'warn' : 'bad',
                },
            ],
        },
        {
            id: 'stakeholder',
            title: 'Customer & Stakeholder Perspective',
            metrics: [
                {
                    label: 'Group Reputation',
                    value: `${kpis.groupRep.toFixed(1)} / 100`,
                    note: 'Avg. across all business units & contagion',
                    diagnostic: diagnoseReputation(kpis.groupRep),
                    health: kpis.groupRep >= 65 ? 'good' : kpis.groupRep >= 45 ? 'warn' : 'bad',
                },
                {
                    label: 'Social License to Operate (SLO)',
                    value: `${kpis.avgSL.toFixed(1)} / 100`,
                    note: 'Avg. across all BUs; < 75 triggers -0.4 M_R',
                    diagnostic: diagnoseSLO(kpis.avgSL),
                    health: kpis.avgSL >= 75 ? 'good' : kpis.avgSL >= 50 ? 'warn' : 'bad',
                },
            ],
        },
        {
            id: 'internal',
            title: 'Internal Business Processes',
            metrics: [
                {
                    label: 'Industrial Synergy (S_y)',
                    value: `${kpis.synergy.toFixed(2)}×`,
                    note: 'Cross-BU circular economy multiplier',
                    diagnostic: diagnoseSynergy(kpis.synergy),
                    health: kpis.synergy > 1.2 ? 'good' : kpis.synergy >= 1.0 ? 'warn' : 'bad',
                },
                {
                    label: 'Carbon Liability',
                    value: `${kpis.carbonTonnage.toFixed(0)} tonnes`,
                    note: `Taxed at $${d.carbon_tax_per_ton || 250}/ton = $${((kpis.carbonTonnage * (d.carbon_tax_per_ton || 250)) / 1_000).toFixed(1)}K`,
                    diagnostic: diagnoseCarbon(kpis.carbonTonnage),
                    health: kpis.carbonTonnage < 100 ? 'good' : kpis.carbonTonnage < 250 ? 'warn' : 'bad',
                },
            ],
        },
        {
            id: 'learning',
            title: 'Learning, Growth & Innovation',
            metrics: [
                {
                    label: 'Talent Retention Index (P_Talent)',
                    value: kpis.pTalent > 0 ? kpis.pTalent.toFixed(2) : 'Stable',
                    note: 'Software BU brain-drain penalty multiplier',
                    diagnostic: diagnoseTalent(kpis.pTalent),
                    health: kpis.pTalent <= 0.5 ? 'good' : kpis.pTalent <= 1.0 ? 'warn' : 'bad',
                },
                {
                    label: 'Just Transition Metric',
                    value: kpis.justTransitionPassed ? '✅ Pass' : '❌ Fail',
                    note: 'Based on R9 strategic choice',
                    diagnostic: diagnoseJustTransition(kpis.justTransitionPassed),
                    health: kpis.justTransitionPassed ? 'good' : 'bad',
                },
                {
                    label: 'VRIO Competitive Advantage',
                    value: kpis.vrioActive ? '🟢 Active' : '🔴 Decayed',
                    note: 'Proprietary capabilities vs imitation decay',
                    diagnostic: diagnoseVRIO(kpis.vrioActive),
                    health: kpis.vrioActive ? 'good' : 'bad',
                },
            ],
        },
    ];

    // Download handler — generates a self-contained HTML report with all sections
    const handleDownload = () => {
        const fmt = (v) => `$${(v / 1_000_000).toFixed(2)}M`;
        const healthEmoji = (h) => h === 'good' ? '✅' : h === 'warn' ? '⚠️' : '❌';

        // ── Build Scorecard Section ──
        const scorecardHTML = PERSPECTIVES.map(persp => {
            const metricsHTML = persp.metrics.map(m => `
                <div class="kpi-card ${m.health}">
                    <div class="kpi-header">
                        <span class="kpi-label">${m.label}</span>
                        <span class="kpi-value">${m.value}</span>
                    </div>
                    <div class="kpi-note">${m.note}</div>
                    <div class="kpi-diagnostic">${healthEmoji(m.health)} ${m.diagnostic}</div>
                </div>
            `).join('');
            return `
                <div class="perspective">
                    <h3>${PERSPECTIVE_ICONS[persp.id]} ${persp.title}</h3>
                    ${metricsHTML}
                </div>
            `;
        }).join('');

        // ── Build M_R Breakdown Section ──
        const mrHTML = mrItems.length > 0 ? `
            <div class="mr-section">
                <h3>M<sub>R</sub> Breakdown</h3>
                <table class="data-table">
                    <thead><tr><th>Component</th><th>Value</th></tr></thead>
                    <tbody>
                        ${mrItems.map(item => `
                            <tr>
                                <td>${item.key.replace(/_/g, ' ')}</td>
                                <td class="${item.value >= 0 ? 'positive' : 'negative'}">${item.value > 0 ? '+' : ''}${item.value.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                        <tr class="total-row">
                            <td><strong>Total M<sub>R</sub></strong></td>
                            <td><strong>${(d.regenerative_multiple || 0).toFixed(2)}×</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        ` : '';

        // ── Build Critical Analysis Section ──
        const strengthsHTML = analysis.strengths.length > 0
            ? `<ul>${analysis.strengths.map(s => `<li class="strength">${s}</li>`).join('')}</ul>`
            : '<p class="no-items">No significant strengths identified — a critical concern.</p>';
        const weaknessesHTML = analysis.weaknesses.length > 0
            ? `<ul>${analysis.weaknesses.map(w => `<li class="weakness">${w}</li>`).join('')}</ul>`
            : '<p class="no-items">No critical weaknesses — an exceptional result.</p>';
        const missedHTML = analysis.missed.length > 0
            ? `<div class="analysis-block"><h3>💡 Missed Opportunities</h3><ul>${analysis.missed.map(m => `<li class="missed">${m}</li>`).join('')}</ul></div>`
            : '';

        // ── Build Trends Table Section ──
        const trendsRows = history
            .filter(snap => (snap.round || snap.round_number || 0) <= 10)
            .map((snap, i) => {
                const gs = snap.global_state || snap || {};
                const buArr = snap.business_units || snap.bu_states || [];
                const roundNum = snap.round || snap.round_number || i + 1;
                const year = 2040 + roundNum;
                const avgCI = buArr.length > 0
                    ? buArr.reduce((s, b) => s + (b.carbon_intensity || 0), 0) / buArr.length
                    : 0;
                const tco2e = gs.tco2e_emissions || gs.carbon_tonnage || buArr.reduce((s, b) => {
                    return s + ((b.carbon_intensity || 0) * (b.revenue_base || 0) / 1_000_000);
                }, 0);
                const ebitda = gs.historical_ebitda || 0;
                const rep = gs.group_reputation || 0;
                return `<tr>
                    <td>R${roundNum} (${year})</td>
                    <td>${avgCI.toFixed(1)}</td>
                    <td>${tco2e.toFixed(0)}</td>
                    <td>${fmt(ebitda)}</td>
                    <td>${rep.toFixed(1)}</td>
                </tr>`;
            }).join('');

        // ── Build Round Review Table Section ──
        const roundRows = history
            .filter(snap => (snap.round || snap.round_number || 0) <= 10)
            .map((snap, i) => {
                const gs = snap.global_state || snap || {};
                const buArr = snap.business_units || snap.bu_states || [];
                const roundNum = snap.round || snap.round_number || i + 1;
                const cash = gs.corporate_treasury || gs.total_cash || 0;
                const rep = gs.group_reputation || 0;
                const avgSL = buArr.length > 0
                    ? buArr.reduce((s, b) => s + (b.social_license_score || 0), 0) / buArr.length
                    : (gs.avg_social_license || 0);
                const sy = gs.synergy_multiplier || 1.0;
                const carbon = gs.tco2e_emissions || gs.carbon_tonnage || buArr.reduce((s, b) => {
                    return s + ((b.carbon_intensity || 0) * (b.revenue_base || 0) / 1_000_000);
                }, 0);
                return `<tr>
                    <td><strong>R${roundNum}</strong></td>
                    <td>${fmt(cash)}</td>
                    <td style="color:${rep >= 65 ? '#10b981' : rep >= 45 ? '#f59e0b' : '#ef4444'}">${rep.toFixed(1)}</td>
                    <td style="color:${avgSL >= 75 ? '#10b981' : avgSL >= 50 ? '#f59e0b' : '#ef4444'}">${avgSL.toFixed(1)}</td>
                    <td>${sy.toFixed(2)}×</td>
                    <td>${carbon.toFixed(0)}</td>
                </tr>`;
            }).join('');

        // ── Build BU Performance Table ──
        const buRows = bus.map(b => `
            <tr>
                <td><strong>${(b.bu_id || '').replace(/_/g, ' ').toUpperCase()}</strong></td>
                <td>${fmt(b.revenue_base || 0)}</td>
                <td>${fmt(b.opex_base || 0)}</td>
                <td>${fmt((b.revenue_base || 0) - (b.opex_base || 0))}</td>
                <td>${(b.carbon_intensity || 0).toFixed(1)}</td>
                <td>${(b.social_license_score || 0).toFixed(1)}</td>
                <td>${(b.natural_capital_debt || 0).toFixed(1)}</td>
            </tr>
        `).join('');

        // ── Assemble Full HTML ──
        const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Muressons Global Command — Sustainability Report 2050</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; padding: 0; }
        .report { max-width: 900px; margin: 0 auto; padding: 40px 32px; }
        .header { text-align: center; padding: 40px 24px; border-radius: 16px; margin-bottom: 32px; background: ${theme.gradient}; }
        .header .badge { font-size: 11px; letter-spacing: 3px; text-transform: uppercase; opacity: 0.85; margin-bottom: 8px; }
        .header h1 { font-size: 28px; font-weight: 700; margin: 8px 0; }
        .header p { font-size: 14px; opacity: 0.9; max-width: 600px; margin: 0 auto; }
        .top-metrics { display: flex; gap: 16px; margin-bottom: 32px; }
        .top-card { flex: 1; background: rgba(30,41,59,0.8); border: 1px solid rgba(99,102,241,0.2); border-radius: 12px; padding: 20px; text-align: center; }
        .top-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; display: block; margin-bottom: 6px; }
        .top-value { font-size: 24px; font-weight: 700; color: #f1f5f9; }
        h2 { font-size: 18px; font-weight: 700; color: #f1f5f9; margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 1px solid rgba(99,102,241,0.2); }
        h3 { font-size: 15px; font-weight: 600; color: #cbd5e1; margin: 16px 0 10px; }
        .perspective { background: rgba(30,41,59,0.6); border: 1px solid rgba(99,102,241,0.15); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
        .kpi-card { background: rgba(15,23,42,0.5); border-radius: 8px; padding: 14px; margin-bottom: 10px; border-left: 3px solid #475569; }
        .kpi-card.good { border-left-color: #10b981; }
        .kpi-card.warn { border-left-color: #f59e0b; }
        .kpi-card.bad { border-left-color: #ef4444; }
        .kpi-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
        .kpi-label { font-size: 13px; font-weight: 600; color: #cbd5e1; }
        .kpi-value { font-size: 16px; font-weight: 700; color: #f1f5f9; }
        .kpi-note { font-size: 11px; color: #64748b; margin-bottom: 6px; }
        .kpi-diagnostic { font-size: 12px; color: #94a3b8; line-height: 1.5; }
        .data-table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }
        .data-table th { text-align: left; padding: 10px 12px; background: rgba(30,41,59,0.8); color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid rgba(99,102,241,0.2); }
        .data-table td { padding: 10px 12px; border-bottom: 1px solid rgba(51,65,85,0.5); color: #cbd5e1; }
        .data-table tr:hover { background: rgba(30,41,59,0.4); }
        .total-row { background: rgba(99,102,241,0.1); font-weight: 600; }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        .analysis-block { background: rgba(30,41,59,0.6); border: 1px solid rgba(99,102,241,0.15); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
        .verdict-card { background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1)); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 24px; margin-bottom: 20px; }
        .verdict-card p { font-size: 14px; color: #e2e8f0; line-height: 1.7; }
        ul { list-style: none; padding: 0; }
        li { padding: 8px 0 8px 20px; position: relative; font-size: 13px; color: #cbd5e1; border-bottom: 1px solid rgba(51,65,85,0.3); }
        li:before { position: absolute; left: 0; }
        li.strength:before { content: '✅'; }
        li.weakness:before { content: '❌'; }
        li.missed:before { content: '💡'; }
        .no-items { font-style: italic; color: #64748b; font-size: 13px; }
        .footer { text-align: center; margin-top: 48px; padding-top: 24px; border-top: 1px solid rgba(99,102,241,0.2); color: #475569; font-size: 12px; }
        .page-break { page-break-before: always; }
        @media print {
            body { background: #0f172a; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .report { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="report">
        <!-- Header -->
        <div class="header">
            <div class="badge">MURESSONS GLOBAL — SUSTAINABILITY BALANCED SCORECARD 2050</div>
            <h1>${theme.icon} ${d.profile_title || 'Final Assessment'}</h1>
            <p>${d.profile_description || ''}</p>
        </div>

        <!-- Top KPIs -->
        <div class="top-metrics">
            <div class="top-card">
                <span class="top-label">Terminal Value</span>
                <span class="top-value">${fmt(d.terminal_value || 0)}</span>
            </div>
            <div class="top-card">
                <span class="top-label">Regenerative Multiple (M꜀)</span>
                <span class="top-value">${(d.regenerative_multiple || 0).toFixed(2)}×</span>
            </div>
            <div class="top-card">
                <span class="top-label">Final Treasury</span>
                <span class="top-value">${fmt(d.final_treasury || globalState.corporate_treasury || 0)}</span>
            </div>
        </div>

        ${mrHTML}

        <!-- ═══ SECTION 1: SCORECARD ═══ -->
        <h2>📊 Sustainability Balanced Scorecard</h2>
        ${scorecardHTML}

        <!-- ═══ SECTION 2: CRITICAL ANALYSIS ═══ -->
        <div class="page-break"></div>
        <h2>🔍 Strategic Critical Analysis</h2>
        <div class="verdict-card">
            <h3>Executive Summary</h3>
            <p>${analysis.verdict}</p>
        </div>
        <div class="analysis-block">
            <h3>✅ Key Strengths Identified</h3>
            ${strengthsHTML}
        </div>
        <div class="analysis-block">
            <h3>❌ Critical Weaknesses Exposed</h3>
            ${weaknessesHTML}
        </div>
        ${missedHTML}

        <!-- ═══ SECTION 3: BU PERFORMANCE ═══ -->
        <h2>🏢 Business Unit Performance (Final State)</h2>
        <table class="data-table">
            <thead><tr><th>Business Unit</th><th>Revenue</th><th>OPEX</th><th>Margin</th><th>Carbon Intensity</th><th>Social License</th><th>NCD</th></tr></thead>
            <tbody>${buRows}</tbody>
        </table>

        <!-- ═══ SECTION 4: TRENDS ═══ -->
        <div class="page-break"></div>
        <h2>📉 Performance Trends Across Simulation</h2>
        ${trendsRows ? `
        <table class="data-table">
            <thead><tr><th>Round</th><th>Avg Carbon Intensity</th><th>tCO₂e Emissions</th><th>EBITDA</th><th>Group Reputation</th></tr></thead>
            <tbody>${trendsRows}</tbody>
        </table>
        ` : '<p class="no-items">Trend data not available for this session.</p>'}

        <!-- ═══ SECTION 5: ROUND REVIEW ═══ -->
        <h2>📈 Round-by-Round Performance</h2>
        ${roundRows ? `
        <table class="data-table">
            <thead><tr><th>Round</th><th>Cash</th><th>Group Rep</th><th>Avg SLO</th><th>Synergy</th><th>Carbon (t)</th></tr></thead>
            <tbody>${roundRows}</tbody>
        </table>
        ` : '<p class="no-items">Round history data not available for this session.</p>'}

        <!-- Footer -->
        <div class="footer">
            <p>Muressons Global Command — Sustainability Strategy Simulation</p>
            <p>Report generated ${new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
        </div>
    </div>
</body>
</html>`;

        // Trigger download
        const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Muressons_Report.html';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const proceedAction = onProceed || onClose;

    return (
        <div className={styles.overlay}>
            <div className={styles.scorecard} ref={printRef}>
                {/* ── Hero Header ── */}
                <header className={styles.hero} style={{ background: theme.gradient }}>
                    <div className={styles.heroContent}>
                        <div className={styles.heroBadge}>SUSTAINABILITY BALANCED SCORECARD</div>
                        <h1 className={styles.heroTitle}>
                            {theme.icon} {d.profile_title || 'Final Assessment'}
                        </h1>
                        <p className={styles.heroDesc}>{d.profile_description || ''}</p>
                    </div>
                </header>

                {/* ── Tab Navigation ── */}
                <nav className={styles.tabNav}>
                    <button
                        className={`${styles.tab} ${activeTab === 'scorecard' ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab('scorecard')}
                    >
                        📊 Scorecard
                    </button>
                    <button
                        className={`${styles.tab} ${activeTab === 'analysis' ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab('analysis')}
                    >
                        🔍 Critical Analysis
                    </button>
                    <button
                        className={`${styles.tab} ${activeTab === 'trends' ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab('trends')}
                    >
                        📉 Trends
                    </button>
                    <button
                        className={`${styles.tab} ${activeTab === 'rounds' ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab('rounds')}
                    >
                        📈 Round Review
                    </button>
                    <button className={styles.downloadBtn} onClick={handleDownload}>
                        📥 Download Report
                    </button>
                </nav>

                {/* ──────── TAB: Scorecard ──────── */}
                {activeTab === 'scorecard' && (
                    <>
                        {/* Top KPI Cards */}
                        <section className={styles.topMetrics}>
                            <div className={styles.topCard}>
                                <span className={styles.topLabel}>Terminal Value</span>
                                <span className={styles.topValue}>
                                    ${((d.terminal_value || 0) / 1_000_000).toFixed(2)}M
                                </span>
                            </div>
                            <div className={styles.topCard}>
                                <span className={styles.topLabel}>Regenerative Multiple (M<sub>R</sub>)</span>
                                <span className={styles.topValue}>
                                    {(d.regenerative_multiple || 0).toFixed(2)}×
                                </span>
                            </div>
                            <div className={styles.topCard}>
                                <span className={styles.topLabel}>Market Headline</span>
                                <span className={styles.topValue} style={{ fontSize: '1rem' }}>
                                    {d.profile_title || '—'}
                                </span>
                            </div>
                        </section>

                        {/* M_R Breakdown */}
                        <section className={styles.mrSection}>
                            <h2 className={styles.sectionTitle}>M<sub>R</sub> Breakdown</h2>
                            <div className={styles.mrBar}>
                                {mrItems.map(item => (
                                    <div
                                        key={item.key}
                                        className={`${styles.mrSegment} ${item.value >= 0 ? styles.mrPositive : styles.mrNegative}`}
                                        style={{ flex: Math.abs(item.value) }}
                                        title={`${item.key}: ${item.value > 0 ? '+' : ''}${item.value.toFixed(2)}`}
                                    >
                                        <span>{item.value > 0 ? '+' : ''}{item.value.toFixed(2)}</span>
                                    </div>
                                ))}
                            </div>
                            <div className={styles.mrLegend}>
                                {mrItems.map(item => (
                                    <span key={item.key} className={item.value >= 0 ? styles.legendPositive : styles.legendNegative}>
                                        {item.key.replace(/_/g, ' ')}: {item.value > 0 ? '+' : ''}{item.value.toFixed(2)}
                                    </span>
                                ))}
                            </div>
                        </section>

                        {/* 4-Perspective Matrix */}
                        <section className={styles.matrix}>
                            {PERSPECTIVES.map(persp => (
                                <div key={persp.id} className={styles.perspective} style={{ '--persp-color': PERSPECTIVE_COLORS[persp.id] }}>
                                    <div className={styles.perspHeader}>
                                        <span className={styles.perspIcon}>{PERSPECTIVE_ICONS[persp.id]}</span>
                                        <h3>{persp.title}</h3>
                                    </div>
                                    <div className={styles.perspMetrics}>
                                        {persp.metrics.map((m, i) => (
                                            <div key={i} className={`${styles.kpiCard} ${styles[m.health]}`}>
                                                <div className={styles.kpiHeader}>
                                                    <span className={styles.kpiLabel}>{m.label}</span>
                                                    <span className={styles.kpiValue}>{m.value}</span>
                                                </div>
                                                <div className={styles.kpiNote}>{m.note}</div>
                                                <div className={styles.kpiDiagnostic}>
                                                    <span className={styles.diagIcon}>
                                                        {m.health === 'good' ? '✅' : m.health === 'warn' ? '⚠️' : '❌'}
                                                    </span>
                                                    <span>{m.diagnostic}</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </section>
                    </>
                )}

                {/* ──────── TAB: Critical Analysis ──────── */}
                {activeTab === 'analysis' && (
                    <section className={styles.analysisSection}>
                        <h2 className={styles.sectionTitle}>🔍 Strategic Critical Analysis</h2>

                        {/* Verdict */}
                        <div className={styles.verdictCard}>
                            <h3>Executive Summary</h3>
                            <p>{analysis.verdict}</p>
                        </div>

                        {/* Strengths */}
                        <div className={styles.analysisBlock}>
                            <h3 className={styles.analysisHeading}>
                                <span className={styles.analysisIcon}>✅</span> Key Strengths Identified
                            </h3>
                            {analysis.strengths.length > 0 ? (
                                <ul className={styles.analysisList}>
                                    {analysis.strengths.map((s, i) => (
                                        <li key={i} className={styles.strengthItem}>{s}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p className={styles.noItems}>No significant strengths identified — a critical concern.</p>
                            )}
                        </div>

                        {/* Weaknesses */}
                        <div className={styles.analysisBlock}>
                            <h3 className={styles.analysisHeading}>
                                <span className={styles.analysisIcon}>❌</span> Critical Weaknesses Exposed
                            </h3>
                            {analysis.weaknesses.length > 0 ? (
                                <ul className={styles.analysisList}>
                                    {analysis.weaknesses.map((w, i) => (
                                        <li key={i} className={styles.weaknessItem}>{w}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p className={styles.noItems}>No critical weaknesses — an exceptional result.</p>
                            )}
                        </div>

                        {/* Missed Opportunities */}
                        {analysis.missed.length > 0 && (
                            <div className={styles.analysisBlock}>
                                <h3 className={styles.analysisHeading}>
                                    <span className={styles.analysisIcon}>💡</span> Missed Opportunities
                                </h3>
                                <ul className={styles.analysisList}>
                                    {analysis.missed.map((m, i) => (
                                        <li key={i} className={styles.missedItem}>{m}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </section>
                )}

                {/* ──────── TAB: Trends ──────── */}
                {activeTab === 'trends' && (() => {
                    // Build chart data from history
                    const chartData = history
                        .filter(snap => (snap.round || snap.round_number || 0) <= 10)
                        .map((snap, i) => {
                            const gs = snap.global_state || snap || {};
                            const buArr = snap.business_units || snap.bu_states || [];
                            const roundNum = snap.round || snap.round_number || i + 1;
                            const year = 2040 + roundNum;

                            // Carbon intensity: weighted average across BUs
                            const avgCI = buArr.length > 0
                                ? buArr.reduce((s, b) => s + (b.carbon_intensity || 0), 0) / buArr.length
                                : 0;

                            // Carbon tonnage (per-year emissions)
                            const tco2e = gs.tco2e_emissions || gs.carbon_tonnage || buArr.reduce((s, b) => {
                                const ci = b.carbon_intensity || 0;
                                const rev = b.revenue_base || 0;
                                return s + (ci * rev / 1_000_000);
                            }, 0);

                            const ebitda = gs.historical_ebitda || 0;
                            const rep = gs.group_reputation || 0;

                            return { round: year, year, avgCI, tco2e, ebitda, rep };
                        });

                    // Cumulative carbon
                    let cumCarbon = 0;
                    const chartDataWithCum = chartData.map(d => {
                        cumCarbon += d.tco2e;
                        return { ...d, cumulativeCarbon: cumCarbon };
                    });

                    const fmtM = (v) => `$${(v / 1_000_000).toFixed(1)}M`;
                    const chartTooltipStyle = { fontSize: 11, borderRadius: 8, background: 'rgba(22,33,62,0.95)', border: '1px solid #2a2a4a', color: '#e2e8f0' };

                    return (
                        <section className={styles.trendsSection}>
                            <h2 className={styles.sectionTitle}>📉 Performance Trends Across Simulation</h2>
                            <div className={styles.trendsGrid}>

                                {/* 1. Carbon Intensity */}
                                <div className={styles.trendCard}>
                                    <div className={styles.trendHeader}>
                                        <span className={styles.trendIcon}>🏭</span>
                                        <h3>Carbon Intensity (Avg Across BUs)</h3>
                                    </div>
                                    <div className={styles.trendChart}>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <LineChart data={chartDataWithCum} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                                <XAxis dataKey="round" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`${v.toFixed(1)} tCO₂e/$M`, 'Carbon Intensity']} />
                                                <Line type="monotone" dataKey="avgCI" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 4, fill: '#f59e0b' }} activeDot={{ r: 6 }} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* 2. Cumulative Carbon */}
                                <div className={styles.trendCard}>
                                    <div className={styles.trendHeader}>
                                        <span className={styles.trendIcon}>📊</span>
                                        <h3>Cumulative Carbon Emissions</h3>
                                    </div>
                                    <div className={styles.trendChart}>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <ComposedChart data={chartDataWithCum} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                                <XAxis dataKey="round" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <YAxis yAxisId="left" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <Tooltip contentStyle={chartTooltipStyle} formatter={(v, name) => [
                                                    `${v.toFixed(0)} t`, name === 'cumulativeCarbon' ? 'Cumulative tCO₂e' : 'Per-Year tCO₂e'
                                                ]} />
                                                <Area yAxisId="left" type="monotone" dataKey="cumulativeCarbon" stroke="#ef4444" fill="rgba(239,68,68,0.15)" strokeWidth={2} dot={{ r: 3 }} />
                                                <Line yAxisId="right" type="monotone" dataKey="tco2e" stroke="#3b82f6" strokeWidth={2} strokeDasharray="4 3" dot={{ r: 3, fill: '#3b82f6' }} />
                                            </ComposedChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* 3. EBITDA */}
                                <div className={styles.trendCard}>
                                    <div className={styles.trendHeader}>
                                        <span className={styles.trendIcon}>💰</span>
                                        <h3>EBITDA Over Simulation</h3>
                                    </div>
                                    <div className={styles.trendChart}>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <AreaChart data={chartDataWithCum} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                                <XAxis dataKey="round" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={(v) => `$${(v / 1_000_000).toFixed(0)}M`} />
                                                <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [fmtM(v), 'EBITDA']} />
                                                <Area type="monotone" dataKey="ebitda" stroke="#10b981" fill="rgba(16,185,129,0.12)" strokeWidth={2.5} dot={{ r: 4, fill: '#10b981' }} activeDot={{ r: 6 }} />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* 4. Reputation */}
                                <div className={styles.trendCard}>
                                    <div className={styles.trendHeader}>
                                        <span className={styles.trendIcon}>🤝</span>
                                        <h3>Group Reputation</h3>
                                    </div>
                                    <div className={styles.trendChart}>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <LineChart data={chartDataWithCum} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                                <XAxis dataKey="round" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`${v.toFixed(1)} / 100`, 'Reputation']} />
                                                <Line type="monotone" dataKey="rep" stroke="#8b5cf6" strokeWidth={2.5} dot={{ r: 4, fill: '#8b5cf6' }} activeDot={{ r: 6 }} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                            </div>

                            {history.length === 0 && (
                                <div className={styles.noRoundData}>
                                    <p>📭 Trend data is not available. Round history was not recorded for this session.</p>
                                </div>
                            )}
                        </section>
                    );
                })()}

                {/* ──────── TAB: Round Review ──────── */}
                {activeTab === 'rounds' && (
                    <section className={styles.roundsSection}>
                        <h2 className={styles.sectionTitle}>📈 Round-by-Round Performance</h2>
                        {history.length > 0 ? (
                            <div className={styles.roundTableWrap}>
                                <table className={styles.roundTable}>
                                    <thead>
                                        <tr>
                                            <th>Round</th>
                                            <th>Cash ($M)</th>
                                            <th>Group Rep</th>
                                            <th>Avg SLO</th>
                                            <th>Synergy</th>
                                            <th>Carbon (t)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {history.filter(snap => (snap.round || snap.round_number || 0) <= 10).map((snap, i) => {
                                            const gs = snap.global_state || snap || {};
                                            const buArr = snap.business_units || snap.bu_states || [];
                                            const cash = gs.corporate_treasury || gs.total_cash || 0;
                                            const rep = gs.group_reputation || 0;
                                            const avgSL = buArr.length > 0
                                                ? buArr.reduce((s, b) => s + (b.social_license_score || 0), 0) / buArr.length
                                                : (gs.avg_social_license || 0);
                                            const sy = gs.synergy_multiplier || 1.0;
                                            const carbon = gs.tco2e_emissions || gs.carbon_tonnage || buArr.reduce((s, b) => {
                                                const ci = b.carbon_intensity || 0;
                                                const rev = b.revenue_base || 0;
                                                return s + (ci * rev / 1_000_000);
                                            }, 0);
                                            const roundNum = snap.round || snap.round_number || i + 1;
                                            return (
                                                <tr key={i} className={i % 2 === 0 ? styles.evenRow : ''}>
                                                    <td className={styles.roundNum}>R{roundNum}</td>
                                                    <td>${(cash / 1_000_000).toFixed(2)}</td>
                                                    <td style={{ color: rep >= 65 ? '#10b981' : rep >= 45 ? '#f59e0b' : '#ef4444' }}>
                                                        {rep.toFixed(1)}
                                                    </td>
                                                    <td style={{ color: avgSL >= 75 ? '#10b981' : avgSL >= 50 ? '#f59e0b' : '#ef4444' }}>
                                                        {avgSL.toFixed(1)}
                                                    </td>
                                                    <td>{sy.toFixed(2)}×</td>
                                                    <td>{carbon.toFixed(0)}</td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className={styles.noRoundData}>
                                <p>📭 Round history data is not available for this session.</p>
                                <p>In multiplayer mode, round history is tracked on the server and may not be available in solo sessions.</p>
                            </div>
                        )}
                    </section>
                )}

                {/* ── Footer ── */}
                <div className={styles.closeRow}>
                    <button className={styles.closeBtn} onClick={proceedAction} style={{ background: theme.gradient }}>
                        {onProceed ? '⚖️ Proceed to Boardroom Showdown →' : 'Close Balanced Scorecard'}
                    </button>
                </div>
            </div>
        </div>
    );
}
