'use client';

import React, { useMemo, useState, useRef, useEffect, useCallback } from 'react';
import {

    LineChart, Line, AreaChart, Area, ComposedChart,
    XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import styles from './SustainabilityBalancedScorecard.module.css';
import StockPerformanceChart from './StockPerformanceChart';
import ConsequenceDNAVisualizer from './ConsequenceDNAVisualizer';
import { roundToQuarter } from '../utils/roundToQuarter';
import { useCurrency } from '../contexts/CurrencyContext';
import { currencySymbol } from '../utils/format';

/**
 * Merge peer-trend rounds into the player's per-round chart rows.
 *
 * Exported for tests, and pure on purpose — this merge carried a data-integrity
 * bug that survived every visual check: /peer-trend-history returns each round's
 * cohort AGGREGATES under the SAME key names the player's own rows use (avgCI,
 * tco2e, ebitda, rep), and the old code spread the whole round object into the
 * row. Flipping "Show Cohort Trends" therefore silently REPLACED the player's
 * solid lines with the cohort average — a player who finished at −$375M EBITDA
 * saw +$26M the moment the toggle went on. Only the namespaced per-peer series
 * (peer_<id>_*) may enter a row; the one aggregate the UI does use
 * (peerStockPrice) is read from peerRounds directly, never from these rows.
 */
export function mergePeerTrendRows(chartRows, peerRounds, peerColors) {
    const peerCum = {};
    const peerIds = [];
    const peerMap = {};

    if (peerRounds.length > 0 && peerRounds[0].peers) {
        peerRounds[0].peers.forEach((p, idx) => {
            peerIds.push({
                id: p.id,
                name: p.name || p.id,
                color: peerColors[idx % peerColors.length],
            });
            peerCum[p.id] = 0;
        });
    }

    peerRounds.forEach(pr => {
        const peersInfo = {};
        (pr.peers || []).forEach(p => {
            if (peerCum[p.id] === undefined) peerCum[p.id] = 0;
            peerCum[p.id] += (p.tco2e || 0);
            peersInfo[`peer_${p.id}_ci`] = p.ci;
            peersInfo[`peer_${p.id}_tco2e`] = p.tco2e;
            peersInfo[`peer_${p.id}_ebitda`] = p.ebitda;
            peersInfo[`peer_${p.id}_rep`] = p.rep;
            peersInfo[`peer_${p.id}_stock`] = p.stock;
            peersInfo[`peer_${p.id}_cum`] = peerCum[p.id];
        });
        peerMap[pr.round] = peersInfo;   // namespaced keys ONLY — never ...pr
    });

    return {
        peerIds,
        rows: chartRows.map(d => (peerMap[d.round] ? { ...d, ...peerMap[d.round] } : d)),
    };
}

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

    if (kpis.carbonTonnage < 150) strengths.push("Carbon footprint reduced to manageable levels, minimising the Year 5 carbon tax liability.");
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
//  BOARD MEMO GENERATOR (Task 4 — Dynamic Diagnostic Feedback)
// ═══════════════════════════════════════════════════════════════

function generateBoardMemo(kpis, d) {
    const sentences = [];
    const sy = kpis.synergy;
    const slo = kpis.avgSL;
    const ebitda = kpis.ebitda;
    const pTalent = kpis.pTalent;
    const rep = kpis.groupRep;
    const carbon = kpis.carbonTonnage;

    // Rule 1: Decoupled growth
    if (sy > 1.2 && slo > 75) {
        sentences.push(
            "You have successfully decoupled financial growth from ecological extraction while maintaining strong labor equity."
        );
    }
    // Rule 2: Toxic culture
    if (ebitda > 10_000_000 && pTalent > 1.0) {
        sentences.push(
            "Your profits are high, but a toxic culture is driving severe talent flight, threatening future software viability."
        );
    }
    // Rule 3: Carbon liability
    if (carbon > 200 && ebitda > 0) {
        sentences.push(
            "Despite positive operating margins, the carbon tonnage exposes the group to material regulatory risk under Year 5 carbon border adjustments."
        );
    }
    // Rule 4: SLO collapse
    if (slo < 50) {
        sentences.push(
            "Social License has collapsed below viability thresholds — communities have withdrawn consent, making continued operations legally and ethically untenable."
        );
    }
    // Rule 5: Reputation resilience
    if (rep >= 80 && sy >= 1.0) {
        sentences.push(
            "Strong reputation combined with operational synergy positions the group as a preferred partner for green supply chain alliances."
        );
    }
    // Rule 6: Financial distress
    if (ebitda <= 0) {
        sentences.push(
            "The group is in financial distress — operating losses after carbon tax indicate the business model is fundamentally unviable without radical restructuring."
        );
    }
    // Fallback if nothing triggered
    if (sentences.length === 0) {
        sentences.push(
            "Performance is mixed. The Board should conduct a deeper review of each business unit's sustainability trajectory before committing to a long-term strategy."
        );
    }

    return sentences.slice(0, 3);
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

const MR_TOOLTIPS = {
    base: 'Starting multiplier of 1.00 — the baseline before any bonuses or penalties are applied.',
    synergy_bonus: 'Earned +0.30 by achieving a Synergy Score ≥ 80 through circular economy integration in R7 (waste-to-energy pipeline).',
    resilience_bonus: 'Earned +0.20 by surviving R5 Cyclone and R8 Water Crisis without choosing bailout/insurance-only options.',
    truth_premium: 'Earned +0.15 by choosing the Ethical AI Overhaul (Option B) in R6, demonstrating governance transparency.',
    community_champion_bonus: 'Earned +0.18 by investing $20M into the community resilience fund in R9.',
    just_transition_bonus: 'Earned +0.12 by choosing managed workforce transition (Option A or C) in R9 instead of mass layoffs.',
    workforce_bonus: 'Earned +0.08 by maintaining Workforce Readiness ≥ 75 at terminal — reflects sustained HR investment.',
    wellbeing_bonus: 'Earned +0.05 by keeping average Burnout Index < 20 across all BUs at terminal.',
    instability_discount: 'Penalty of −0.40 triggered when average Social License across all BUs falls below 75 — reflects stakeholder destabilisation.',
    max_achievable_mr: 'Theoretical ceiling — the maximum M_R attainable if every bonus is earned and no penalties apply.',
    csrd_governance_premium: 'Earned +0.10 by choosing CSRD-aligned governance in R2 (Option A).',
    green_bond_premium: 'Earned via green bond issuance — lower cost of capital from verified ESG credentials.',
    climate_resilience_bonus: 'Earned by maintaining high climate resilience factor through proactive infrastructure investments.',
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
export default function SustainabilityBalancedScorecard({ data, businessUnits = [], globalState = {}, history = [], onProceed, onClose, onLogout, sessionId, decisionParadigm }) {
    const d = data || {};
    const bus = businessUnits;
    const theme = PROFILES[d.profile] || PROFILES.fragile_giant;
    const maxRounds = 10;
    const { currency: scorecardCurrency } = useCurrency();
    const sym = scorecardCurrency?.symbol || '$';

    // Debug: log what data the scorecard receives
    console.log('[SCORECARD] data:', d);
    console.log('[SCORECARD] profile:', d.profile, '| terminal_ebitda:', d.terminal_ebitda, '| terminal_value:', d.terminal_value);
    console.log('[SCORECARD] bus:', bus.length, '| globalState keys:', Object.keys(globalState));
    console.log('[SCORECARD] history:', history.length, 'rounds');
    const [activeTab, setActiveTab] = useState('scorecard'); // 'scorecard' | 'financial_statement' | 'analysis' | 'trends' | 'tbl_matrix' | 'rounds' | 'stock' | 'leaderboard' | 'report' | 'dna_map'
    const printRef = useRef(null);
    const [leaderboard, setLeaderboard] = useState([]);

    // Peer trend comparison state
    const [showPeerTrends, setShowPeerTrends] = useState(false);
    const [peerTrendData, setPeerTrendData] = useState(null); // { available, ai_benchmark, peerCount, rounds: [] }
    const [peerLoading, setPeerLoading] = useState(false);

    // Fetch peer trend history when toggle is activated
    useEffect(() => {
        if (!showPeerTrends || !sessionId || peerTrendData) return;
        setPeerLoading(true);
        fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sessionId}/peer-trend-history`)
            .then(r => r.json())
            .then(data => {
                setPeerTrendData(data);
                setPeerLoading(false);
            })
            .catch(() => setPeerLoading(false));
    }, [showPeerTrends, sessionId, peerTrendData]);

    // Balance Sheet data for the Financial Statement tab
    const [balanceSheet, setBalanceSheet] = useState(null);
    useEffect(() => {
        if (!sessionId) return;
        fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sessionId}/balance-sheet`)
            .then(r => r.ok ? r.json() : null)
            .then(d => d && setBalanceSheet(d.balance_sheet || d))
            .catch(() => {});
    }, [sessionId]);

    // Fallback state for older sessions that didn't capture the snapshot at R10
    const [fetchedDnaSnapshot, setFetchedDnaSnapshot] = useState(null);

    // Consequence DNA snapshot from live fetch (prioritized during dev/updates) or fallback to frozen state
    const dnaSnapshot = useMemo(() => {
        return fetchedDnaSnapshot || globalState?.active_event_flags?.consequence_dna_snapshot || null;
    }, [globalState, fetchedDnaSnapshot]);

    useEffect(() => {
        if (sessionId) {
            fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sessionId}/consequence-dna-data`)
                .then(r => r.json())
                .then(data => {
                    if (data && !data.error) setFetchedDnaSnapshot(data);
                })
                .catch(err => console.error("Failed to fetch DNA snapshot fallback:", err));
        }
    }, [sessionId]);

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
            ebitda: d.terminal_ebitda || 0,
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
        .filter(([, val]) => val != null && val !== 0)
        .map(([key, val]) => ({
            key,
            value: Number(val) || 0,
            tooltip: MR_TOOLTIPS[key] || `${key.replace(/_/g, ' ')} component of the Regenerative Multiple.`,
        }));


    const PERSPECTIVES = [
        {
            id: 'financial',
            title: 'Financial Perspective',
            metrics: [
                {
                    label: 'Adjusted EBITDA (Year 5)',
                    value: `${currencySymbol()}${(kpis.ebitda / 1_000_000).toFixed(2)}M`,
                    note: `After ${currencySymbol()}${(d.carbon_tax_per_ton || 250)}/ton carbon tax`,
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
                    note: `Taxed at ${currencySymbol()}${d.carbon_tax_per_ton || 250}/ton = ${currencySymbol()}${((kpis.carbonTonnage * (d.carbon_tax_per_ton || 250)) / 1_000).toFixed(1)}K`,
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
        const fmt = (v) => `${currencySymbol()}${(v / 1_000_000).toFixed(2)}M`;
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
            .filter(snap => (snap.round || snap.round_number || 0) <= maxRounds)
            .map((snap, i) => {
                const gs = snap.global_state || snap || {};
                const buArr = snap.business_units || snap.bu_states || [];
                const roundNum = snap.round || snap.round_number || i + 1;
                const quarterLabel = roundToQuarter(roundNum).label;
                const avgCI = buArr.length > 0
                    ? buArr.reduce((s, b) => s + (b.carbon_intensity || 0), 0) / buArr.length
                    : 0;
                const tco2e = gs.tco2e_emissions || gs.carbon_tonnage || buArr.reduce((s, b) => {
                    return s + ((b.carbon_intensity || 0) * (b.revenue_base || 0) / 1_000_000);
                }, 0);
                const ebitda = gs.historical_ebitda || 0;
                const rep = gs.group_reputation || 0;
                return `<tr>
                    <td>R${roundNum} (${quarterLabel})</td>
                    <td>${avgCI.toFixed(1)}</td>
                    <td>${tco2e.toFixed(0)}</td>
                    <td>${fmt(ebitda)}</td>
                    <td>${rep.toFixed(1)}</td>
                </tr>`;
            }).join('');

        // ── Build Round Review Table Section ──
        const roundRows = history
            .filter(snap => (snap.round || snap.round_number || 0) <= maxRounds)
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
    <title>Muressons Global Corporation — Sustainability Report (Year 5)</title>
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
            <div class="badge">MURESSONS GLOBAL — SUSTAINABILITY BALANCED SCORECARD (YEAR 5)</div>
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
            <p>Muressons Global Corporation — Sustainability Strategy Simulation</p>
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
                        className={`${styles.tab} ${activeTab === 'financial_statement' ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab('financial_statement')}
                    >
                        💰 Financial Statement
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
                        className={`${styles.tab} ${activeTab === 'tbl_matrix' ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab('tbl_matrix')}
                    >
                        🧮 TBL Matrix
                    </button>
                    <button
                        className={`${styles.tab} ${activeTab === 'rounds' ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab('rounds')}
                    >
                        📈 Round Review
                    </button>

                    <button
                        className={`${styles.tab} ${activeTab === 'report' ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab('report')}
                    >
                        📋 Final Report
                    </button>
                    {dnaSnapshot && (
                      <button
                          className={`${styles.tab} ${activeTab === 'dna_map' ? styles.tabActive : ''}`}
                          onClick={() => setActiveTab('dna_map')}
                      >
                          🧬 DNA Map
                      </button>
                    )}
                    {d.pathway_discovery && (
                        <button
                            className={`${styles.tab} ${activeTab === 'pathway' ? styles.tabActive : ''}`}
                            onClick={() => setActiveTab('pathway')}
                        >
                            🗺️ Pathway
                        </button>
                    )}
                    {history && history.length > 0 && (
                        <button
                            className={`${styles.tab} ${activeTab === 'journey' ? styles.tabActive : ''}`}
                            onClick={() => setActiveTab('journey')}
                        >
                            📜 Journey
                        </button>
                    )}
                    <button className={styles.downloadBtn} onClick={handleDownload}>
                        📥 Download Report
                    </button>
                    {onLogout && (
                        <button
                            className={styles.downloadBtn}
                            onClick={() => { if (window.confirm('Log out? Your progress is saved and you can return anytime.')) onLogout(); }}
                            style={{ background: 'rgba(239,68,68,0.1)', borderColor: '#fca5a5', color: '#fca5a5' }}
                        >
                            🚪 Logout
                        </button>
                    )}
                </nav>

                {/* ──────── TAB: Scorecard ──────── */}
                {activeTab === 'scorecard' && (
                    <>
                        {/* Top KPI Cards */}
                        <section className={styles.topMetrics}>
                            <div className={styles.topCard}>
                                <span className={styles.topLabel}>Terminal Value</span>
                                <span className={styles.topValue}>
                                    {currencySymbol()}{((d.terminal_value || 0) / 1_000_000).toFixed(2)}M
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
                                        title={`${item.key.replace(/_/g, ' ')}: ${item.value > 0 ? '+' : ''}${item.value.toFixed(2)} — ${item.tooltip}`}
                                    >
                                        <span>{item.value > 0 ? '+' : ''}{item.value.toFixed(2)}</span>
                                    </div>
                                ))}
                            </div>
                            <div className={styles.mrLegend}>
                                {mrItems.map(item => (
                                    <span key={item.key} className={`${item.value >= 0 ? styles.legendPositive : styles.legendNegative} ${styles.mrTooltipWrap}`}>
                                        {item.key.replace(/_/g, ' ')}: {item.value > 0 ? '+' : ''}{item.value.toFixed(2)}
                                        <span className={styles.mrTooltip}>{item.tooltip}</span>
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

                {/* ──────── TAB: Financial Statement ──────── */}
                {activeTab === 'financial_statement' && (() => {
                    if (!balanceSheet) return (
                        <section style={{ padding: '3rem 2rem', textAlign: 'center' }}>
                            <div style={{ fontSize: '2.5rem', marginBottom: '1rem', opacity: 0.4 }}>💰</div>
                            <h3 style={{ color: 'var(--text-primary, #e2e8f0)', marginBottom: '0.5rem' }}>Loading Financial Statement...</h3>
                            <p style={{ color: 'var(--text-muted, #64748b)', fontSize: '0.85rem' }}>The balance sheet data is being retrieved.</p>
                        </section>
                    );

                    const fmtM = (v) => `${currencySymbol()}${((v || 0) / 1_000_000).toFixed(1)}M`;
                    const fmtK = (v) => Math.abs(v || 0) >= 1_000_000 ? fmtM(v) : `${currencySymbol()}${((v || 0) / 1_000).toFixed(0)}K`;

                    const totalAssets = balanceSheet.total_assets || 0;
                    const totalLiabilities = balanceSheet.total_liabilities || 0;
                    const netAssets = balanceSheet.net_assets || 0;
                    const deRatio = balanceSheet.debt_to_equity || 0;
                    const covenantStatus = balanceSheet.covenant_status || 'green';
                    const ndEbitda = balanceSheet.net_debt_to_ebitda || 0;
                    const strandedExposure = balanceSheet.stranded_asset_exposure || 0;
                    const brandValue = (balanceSheet.intangible_assets || {}).brand_value || 0;

                    const covenantColors = { green: '#10b981', amber: '#f59e0b', red: '#ef4444', breached: '#dc2626' };
                    const covenantLabels = { green: '🟢 Comfortable', amber: '🟡 Watch List', red: '🔴 Breach (Cure Period)', breached: '🚨 Acceleration' };

                    const ta = balanceSheet.tangible_assets || {};
                    const ia = balanceSheet.intangible_assets || {};
                    const ca = balanceSheet.current_assets || {};
                    const ncl = balanceSheet.non_current_liabilities || {};
                    const cl = balanceSheet.current_liabilities || {};

                    const totalTangible = Object.values(ta).reduce((s, v) => s + (v || 0), 0);
                    const totalIntangible = Object.values(ia).reduce((s, v) => s + (v || 0), 0);
                    const totalCurrent = Object.values(ca).reduce((s, v) => s + (v || 0), 0);
                    const totalNCL = Object.values(ncl).reduce((s, v) => s + (v || 0), 0);
                    const totalCL = Object.values(cl).reduce((s, v) => s + (v || 0), 0);
                    const totalEquity = (balanceSheet.share_capital || 0) + (balanceSheet.retained_earnings || 0) + (balanceSheet.other_reserves || 0);

                    const lineRow = (label, value, opts = {}) => (
                        <div style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            padding: opts.bold ? '6px 0' : '4px 0',
                            borderTop: opts.topBorder ? '1px solid rgba(148,163,184,0.15)' : 'none',
                            borderBottom: opts.bottomBorder ? '1px double rgba(148,163,184,0.2)' : 'none',
                        }}>
                            <span style={{
                                fontSize: opts.bold ? '0.82rem' : '0.78rem',
                                fontWeight: opts.bold ? 800 : 500,
                                color: opts.color || (opts.bold ? '#e2e8f0' : '#94a3b8'),
                                paddingLeft: opts.indent ? 16 : 0,
                            }}>{label}</span>
                            <span style={{
                                fontSize: opts.bold ? '0.85rem' : '0.78rem',
                                fontWeight: opts.bold ? 800 : 600,
                                fontFamily: "'JetBrains Mono', monospace",
                                color: opts.color || (opts.bold ? '#e2e8f0' : '#cbd5e1'),
                            }}>{typeof value === 'number' ? fmtK(value) : value}</span>
                        </div>
                    );

                    const sectionHeader = (label, icon) => (
                        <div style={{
                            fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase',
                            letterSpacing: '0.08em', color: '#64748b', marginTop: 18, marginBottom: 6,
                            display: 'flex', alignItems: 'center', gap: 6,
                        }}>{icon} {label}</div>
                    );

                    return (
                        <section style={{ padding: '1.5rem 0' }}>
                            <h2 className={styles.sectionTitle}>📊 Statement of Financial Position</h2>
                            <p style={{ color: '#64748b', fontSize: '0.78rem', marginBottom: '1.25rem' }}>IFRS-Compliant Balance Sheet — Year 5 Terminal State</p>

                            {/* Summary header cards */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 20 }}>
                                <div style={{
                                    padding: '14px 16px', borderRadius: 10, textAlign: 'center',
                                    background: 'rgba(56,189,248,0.06)', border: '1px solid rgba(56,189,248,0.15)',
                                }}>
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Total Assets</div>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: totalAssets >= 0 ? '#38bdf8' : '#f87171', fontFamily: "'JetBrains Mono', monospace", marginTop: 4 }}>{fmtM(totalAssets)}</div>
                                </div>
                                <div style={{
                                    padding: '14px 16px', borderRadius: 10, textAlign: 'center',
                                    background: 'rgba(248,113,113,0.06)', border: '1px solid rgba(248,113,113,0.15)',
                                }}>
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Total Liabilities</div>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f87171', fontFamily: "'JetBrains Mono', monospace", marginTop: 4 }}>{fmtM(totalLiabilities)}</div>
                                </div>
                                <div style={{
                                    padding: '14px 16px', borderRadius: 10, textAlign: 'center',
                                    background: netAssets >= 0 ? 'rgba(74,222,128,0.06)' : 'rgba(239,68,68,0.06)',
                                    border: `1px solid ${netAssets >= 0 ? 'rgba(74,222,128,0.15)' : 'rgba(239,68,68,0.15)'}`,
                                }}>
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Net Assets</div>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: netAssets >= 0 ? '#4ade80' : '#ef4444', fontFamily: "'JetBrains Mono', monospace", marginTop: 4 }}>{fmtM(netAssets)}</div>
                                </div>
                            </div>

                            {/* Two-column layout: Assets / Liabilities+Equity */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 28, background: 'rgba(15,23,42,0.4)', borderRadius: 12, padding: '1.5rem', border: '1px solid rgba(99,102,241,0.1)' }}>
                                {/* LEFT: Assets */}
                                <div>
                                    {sectionHeader('Non-Current Assets', '🏭')}
                                    {lineRow('Property, Plant & Equipment', ta.property_plant_equipment, { indent: true })}
                                    {lineRow('Right-of-Use Assets (IFRS 16)', ta.right_of_use_assets, { indent: true })}
                                    {lineRow('Inventory', ta.inventory, { indent: true })}
                                    {lineRow('Total Tangible', totalTangible, { bold: true, topBorder: true })}

                                    {sectionHeader('Intangible Assets', '💎')}
                                    {lineRow('Brand Value', ia.brand_value, { indent: true })}
                                    {lineRow('Intellectual Property', ia.intellectual_property, { indent: true })}
                                    {lineRow('Goodwill', ia.goodwill, { indent: true })}
                                    {lineRow('Social Licence (IAS 38)', ia.social_licence_asset, { indent: true })}
                                    {lineRow('Reputation Capital', ia.reputation_asset, { indent: true })}
                                    {lineRow('Total Intangible', totalIntangible, { bold: true, topBorder: true })}

                                    {sectionHeader('Current Assets', '💵')}
                                    {lineRow('Cash & Equivalents', ca.cash_and_equivalents, { indent: true, color: (ca.cash_and_equivalents || 0) < 0 ? '#f87171' : '#4ade80' })}
                                    {lineRow('Trade Receivables', ca.trade_receivables, { indent: true })}
                                    {lineRow('Prepayments', ca.prepayments, { indent: true })}
                                    {lineRow('Total Current', totalCurrent, { bold: true, topBorder: true })}

                                    {lineRow('TOTAL ASSETS', totalAssets, { bold: true, topBorder: true, bottomBorder: true, color: '#38bdf8' })}
                                </div>

                                {/* RIGHT: Liabilities + Equity */}
                                <div>
                                    {sectionHeader('Non-Current Liabilities', '🏦')}
                                    {lineRow('Revolving Credit Facility', ncl.revolving_credit_facility, { indent: true })}
                                    {lineRow('Green Bonds', ncl.green_bonds_outstanding, { indent: true })}
                                    {lineRow('Environmental Provisions', ncl.environmental_provisions, { indent: true })}
                                    {lineRow('Decommissioning', ncl.decommissioning_obligations, { indent: true })}
                                    {lineRow('Lease Liabilities (IFRS 16)', ncl.lease_liabilities, { indent: true })}
                                    {lineRow('Total Non-Current', totalNCL, { bold: true, topBorder: true })}

                                    {sectionHeader('Current Liabilities', '📋')}
                                    {lineRow('Trade Payables', cl.trade_payables, { indent: true })}
                                    {lineRow('Tax Provisions', cl.tax_provisions, { indent: true })}
                                    {lineRow('Accrued Remediation', cl.accrued_remediation, { indent: true })}
                                    {lineRow('Short-Term Debt', cl.short_term_debt, { indent: true })}
                                    {lineRow('Total Current', totalCL, { bold: true, topBorder: true })}

                                    {sectionHeader("Shareholders' Equity", '🏛️')}
                                    {lineRow('Share Capital', balanceSheet.share_capital, { indent: true })}
                                    {lineRow('Retained Earnings', balanceSheet.retained_earnings, { indent: true, color: (balanceSheet.retained_earnings || 0) < 0 ? '#f87171' : undefined })}
                                    {lineRow('Other Reserves', balanceSheet.other_reserves, { indent: true })}
                                    {lineRow('TOTAL EQUITY', totalEquity, { bold: true, topBorder: true, bottomBorder: true, color: '#a78bfa' })}
                                </div>
                            </div>

                            {/* Bottom: Key Ratios */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 20 }}>
                                <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(56,189,248,0.04)', border: '1px solid rgba(56,189,248,0.1)', textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.3rem', marginBottom: 4 }}>⚖️</div>
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>D/E Ratio</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 800, color: deRatio < 2.0 ? '#4ade80' : '#ef4444', fontFamily: "'JetBrains Mono', monospace", marginTop: 4 }}>{deRatio.toFixed(2)}×</div>
                                </div>
                                <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(56,189,248,0.04)', border: '1px solid rgba(56,189,248,0.1)', textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.3rem', marginBottom: 4 }}>📄</div>
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>ND/EBITDA</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 800, color: ndEbitda <= 2.5 ? '#4ade80' : '#ef4444', fontFamily: "'JetBrains Mono', monospace", marginTop: 4 }}>{ndEbitda.toFixed(2)}×</div>
                                </div>
                                <div style={{ padding: '14px', borderRadius: 10, background: strandedExposure > 0 ? 'rgba(245,158,11,0.06)' : 'rgba(56,189,248,0.04)', border: `1px solid ${strandedExposure > 0 ? 'rgba(245,158,11,0.15)' : 'rgba(56,189,248,0.1)'}`, textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.3rem', marginBottom: 4 }}>⚠️</div>
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Stranded Exposure</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 800, color: strandedExposure > 0 ? '#f59e0b' : '#4ade80', fontFamily: "'JetBrains Mono', monospace", marginTop: 4 }}>{fmtM(strandedExposure)}</div>
                                </div>
                                <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(167,139,250,0.04)', border: '1px solid rgba(167,139,250,0.1)', textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.3rem', marginBottom: 4 }}>💎</div>
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Brand Value</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 800, color: '#a78bfa', fontFamily: "'JetBrains Mono', monospace", marginTop: 4 }}>{fmtM(brandValue)}</div>
                                </div>
                            </div>

                            {/* Debt Covenant Status */}
                            <div style={{
                                marginTop: 16, padding: '12px 20px', borderRadius: 10, textAlign: 'center',
                                background: `${covenantColors[covenantStatus]}08`,
                                border: `1px solid ${covenantColors[covenantStatus]}25`,
                            }}>
                                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', marginRight: 12 }}>Debt Covenant Status:</span>
                                <span style={{ fontSize: '0.88rem', fontWeight: 800, color: covenantColors[covenantStatus] }}>
                                    {covenantLabels[covenantStatus] || covenantStatus}
                                </span>
                            </div>

                            {/* ──────── Year-by-Year (full-period) Statement ──────── */}
                            {(() => {
                                const history = (balanceSheet.balance_sheet_history || []).filter(Boolean);
                                if (history.length === 0) return null;
                                const sumVals = (o) => Object.values(o || {}).reduce((a, b) => a + (Number(b) || 0), 0);
                                const anyFull = history.some(h => h.full_statement);

                                // Columns are YEARS, not rounds. Two rounds make a year (each round is
                                // a half-year: H1 = odd round, H2 = even round). A balance sheet is a
                                // point-in-time position, so each year column shows that year's CLOSING
                                // position — the latest round in the year (H2 where present, else H1).
                                const byYear = new Map();
                                for (const h of history) {
                                    const yr = Math.max(1, Math.ceil((Number(h.round) || 1) / 2));
                                    const prev = byYear.get(yr);
                                    if (!prev || (Number(h.round) || 0) > (Number(prev.round) || 0)) byYear.set(yr, h);
                                }
                                const yearCols = [...byYear.entries()]
                                    .sort((a, b) => a[0] - b[0])
                                    .map(([year, snap]) => ({
                                        year,
                                        round: snap.round,
                                        half: (Number(snap.round) % 2 === 1) ? 'H1' : 'H2',
                                        snap,
                                    }));

                                // Shared row spec — drives both the on-screen table and the CSV export.
                                const ROWS = [
                                    { section: 'Non-Current Assets' },
                                    { label: 'Property, Plant & Equipment', get: s => s.tangible_assets?.property_plant_equipment },
                                    { label: 'Right-of-Use Assets (IFRS 16)', get: s => s.tangible_assets?.right_of_use_assets },
                                    { label: 'Inventory', get: s => s.tangible_assets?.inventory },
                                    { label: 'Total Tangible', total: true, get: s => s.tangible_assets ? sumVals(s.tangible_assets) : null },
                                    { section: 'Intangible Assets' },
                                    { label: 'Brand Value', get: s => s.intangible_assets?.brand_value },
                                    { label: 'Intellectual Property', get: s => s.intangible_assets?.intellectual_property },
                                    { label: 'Goodwill', get: s => s.intangible_assets?.goodwill },
                                    { label: 'Total Intangible', total: true, get: s => s.intangible_assets ? sumVals(s.intangible_assets) : null },
                                    { section: 'Current Assets' },
                                    { label: 'Cash & Equivalents', get: s => s.current_assets?.cash_and_equivalents },
                                    { label: 'Trade Receivables', get: s => s.current_assets?.trade_receivables },
                                    { label: 'Prepayments', get: s => s.current_assets?.prepayments },
                                    { label: 'Total Current', total: true, get: s => s.current_assets ? sumVals(s.current_assets) : null },
                                    { label: 'TOTAL ASSETS', grand: true, get: s => s.total_assets },
                                    { section: 'Non-Current Liabilities' },
                                    { label: 'Revolving Credit Facility', get: s => s.non_current_liabilities?.revolving_credit_facility },
                                    { label: 'Green Bonds', get: s => s.non_current_liabilities?.green_bonds_outstanding },
                                    { label: 'Environmental Provisions', get: s => s.non_current_liabilities?.environmental_provisions },
                                    { label: 'Decommissioning', get: s => s.non_current_liabilities?.decommissioning_obligations },
                                    { label: 'Lease Liabilities (IFRS 16)', get: s => s.non_current_liabilities?.lease_liabilities },
                                    { label: 'Total Non-Current', total: true, get: s => s.non_current_liabilities ? sumVals(s.non_current_liabilities) : null },
                                    { section: 'Current Liabilities' },
                                    { label: 'Trade Payables', get: s => s.current_liabilities?.trade_payables },
                                    { label: 'Tax Provisions', get: s => s.current_liabilities?.tax_provisions },
                                    { label: 'Accrued Remediation', get: s => s.current_liabilities?.accrued_remediation },
                                    { label: 'Short-Term Debt', get: s => s.current_liabilities?.short_term_debt },
                                    { label: 'Total Current', total: true, get: s => s.current_liabilities ? sumVals(s.current_liabilities) : null },
                                    { label: 'TOTAL LIABILITIES', grand: true, get: s => s.total_liabilities },
                                    { section: "Shareholders' Equity" },
                                    { label: 'Share Capital', get: s => s.share_capital },
                                    { label: 'Retained Earnings', get: s => s.retained_earnings },
                                    { label: 'Other Reserves', get: s => s.other_reserves },
                                    { label: 'TOTAL EQUITY', grand: true, get: s => (Number(s.share_capital) || 0) + (Number(s.retained_earnings) || 0) + (Number(s.other_reserves) || 0) },
                                    { section: 'Key Figures & Ratios' },
                                    { label: 'Net Assets', get: s => s.net_assets },
                                    { label: 'EBITDA', get: s => s.ebitda },
                                    { label: 'Net Income', get: s => s.net_income },
                                    { label: 'D/E Ratio', kind: 'ratio', get: s => s.d_e_ratio },
                                    { label: 'ND/EBITDA', kind: 'ratio', get: s => s.net_debt_to_ebitda },
                                    { label: 'Covenant', kind: 'text', get: s => s.covenant_status },
                                ];

                                const cellText = (row, s) => {
                                    const v = row.get(s);
                                    if (v == null || (typeof v === 'number' && Number.isNaN(v))) return '—';
                                    if (row.kind === 'ratio') return `${Number(v).toFixed(2)}×`;
                                    if (row.kind === 'text') return covenantLabels[v] || String(v);
                                    return fmtK(v);
                                };

                                const downloadCSV = () => {
                                    const periods = yearCols.map(c => `Year ${c.year} (year-end, R${c.round})`);
                                    const esc = (x) => `"${String(x).replace(/"/g, '""')}"`;
                                    const lines = [];
                                    lines.push(esc('Muressons — Statement of Financial Position (Year-by-Year, full period)'));
                                    lines.push(esc('Each year = 2 rounds (each round a half-year); columns show the year-end closing position.'));
                                    lines.push(['', ...periods].map(esc).join(','));
                                    for (const row of ROWS) {
                                        if (row.section) { lines.push(esc(row.section)); continue; }
                                        const cells = yearCols.map(c => {
                                            const v = row.get(c.snap);
                                            if (v == null) return '';
                                            if (row.kind === 'text') return esc(v);
                                            return Number(v);
                                        });
                                        lines.push([esc(row.label), ...cells].join(','));
                                    }
                                    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
                                    const url = URL.createObjectURL(blob);
                                    const a = document.createElement('a');
                                    a.href = url; a.download = 'muressons-financial-position-by-year.csv';
                                    document.body.appendChild(a); a.click(); a.remove();
                                    setTimeout(() => URL.revokeObjectURL(url), 1000);
                                };

                                return (
                                    <div style={{ marginTop: 28 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 6 }}>
                                            <h2 className={styles.sectionTitle} style={{ margin: 0 }}>🗓️ Year-by-Year Statement — Full Period</h2>
                                            <button
                                                onClick={downloadCSV}
                                                style={{
                                                    padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: '0.78rem',
                                                    border: '1px solid rgba(56,189,248,0.4)', background: 'rgba(56,189,248,0.12)', color: '#7dd3fc',
                                                }}
                                            >⬇️ Download (.csv)</button>
                                        </div>
                                        <p style={{ color: '#64748b', fontSize: '0.78rem', marginBottom: '1rem' }}>
                                            Statement of Financial Position year by year — each year is 2 rounds (each round a half-year); every column shows that year’s year-end closing position.
                                            {!anyFull && ' (This run predates full line-item history, so only the summary rows are available per year.)'}
                                        </p>
                                        <div style={{ overflowX: 'auto', border: '1px solid rgba(148,163,184,0.12)', borderRadius: 10 }}>
                                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.74rem', minWidth: 520 }}>
                                                <thead>
                                                    <tr>
                                                        <th style={{ textAlign: 'left', padding: '8px 12px', position: 'sticky', left: 0, background: '#0f172a', color: '#94a3b8', fontWeight: 700, fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Line Item</th>
                                                        {yearCols.map((c, i) => (
                                                            <th key={i} title={`Year-end position (Round ${c.round}${c.half === 'H1' ? ', H1 — year still in progress' : ''})`} style={{ textAlign: 'right', padding: '8px 12px', color: i === yearCols.length - 1 ? '#7dd3fc' : '#94a3b8', fontWeight: 700, fontSize: '0.7rem', fontFamily: "'JetBrains Mono', monospace" }}>
                                                                Year {c.year}{i === yearCols.length - 1 ? ' ·terminal' : ''}
                                                            </th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {ROWS.map((row, ri) => row.section ? (
                                                        <tr key={ri}>
                                                            <td colSpan={yearCols.length + 1} style={{ padding: '10px 12px 4px', color: '#64748b', fontWeight: 800, fontSize: '0.64rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{row.section}</td>
                                                        </tr>
                                                    ) : (
                                                        <tr key={ri} style={{ borderTop: (row.total || row.grand) ? '1px solid rgba(148,163,184,0.15)' : 'none' }}>
                                                            <td style={{ padding: '4px 12px', position: 'sticky', left: 0, background: '#0f172a', color: row.grand ? '#38bdf8' : row.total ? '#e2e8f0' : '#94a3b8', fontWeight: (row.total || row.grand) ? 800 : 500, paddingLeft: (row.total || row.grand) ? 12 : 22 }}>{row.label}</td>
                                                            {yearCols.map((c, ci) => {
                                                                const raw = row.get(c.snap);
                                                                const neg = typeof raw === 'number' && raw < 0;
                                                                return (
                                                                    <td key={ci} style={{ textAlign: 'right', padding: '4px 12px', fontFamily: "'JetBrains Mono', monospace", fontWeight: (row.total || row.grand) ? 800 : 600, color: neg ? '#f87171' : row.grand ? '#38bdf8' : '#cbd5e1' }}>
                                                                        {cellText(row, c.snap)}
                                                                    </td>
                                                                );
                                                            })}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                );
                            })()}
                        </section>
                    );
                })()}

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
                        .filter(snap => (snap.round || snap.round_number || 0) <= maxRounds)
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

                            return { round: roundNum, label: roundToQuarter(roundNum).label, avgCI, tco2e, ebitda, rep };
                        });

                    // Cumulative carbon
                    let cumCarbon = 0;
                    const chartDataWithCum = chartData.map(d => {
                        cumCarbon += d.tco2e;
                        return { ...d, cumulativeCarbon: cumCarbon };
                    });

                    // ── Merge peer data into chart data (if toggle is on) ──
                    // See mergePeerTrendRows for why this must never spread the
                    // raw round objects: their aggregate keys shadow the
                    // player's own series.
                    const peerRounds = (showPeerTrends && peerTrendData?.available) ? peerTrendData.rounds : [];
                    const peerColors = ['#fb923c', '#c084fc', '#f472b6', '#34d399', '#60a5fa', '#fcd34d', '#2dd4bf'];
                    const { peerIds, rows: chartDataMerged } =
                        mergePeerTrendRows(chartDataWithCum, peerRounds, peerColors);

                    const isPeerActive = showPeerTrends && peerTrendData?.available;
                    const peerCountLabel = peerTrendData?.ai_benchmark
                        ? '3 AI profiles'
                        : `${peerTrendData?.peerCount || 0} peer${(peerTrendData?.peerCount || 0) !== 1 ? 's' : ''}`;

                    const fmtM = (v) => `${currencySymbol()}${((v || 0) / 1_000_000).toFixed(1)}M`;
                    const chartTooltipStyle = { fontSize: 11, borderRadius: 8, background: 'rgba(22,33,62,0.95)', border: '1px solid #2a2a4a', color: '#e2e8f0' };

                    return (
                        <section className={styles.trendsSection}>
                            <h2 className={styles.sectionTitle}>📉 Performance Trends Across Simulation</h2>

                            {/* ── Peer Comparison Toggle ── */}
                            <div className={styles.peerToggleRow}>
                                <div
                                    className={`${styles.peerToggleLabel} ${showPeerTrends ? styles.peerToggleActive : ''}`}
                                    onClick={() => setShowPeerTrends(prev => !prev)}
                                    role="switch"
                                    aria-checked={showPeerTrends}
                                    tabIndex={0}
                                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setShowPeerTrends(prev => !prev); } }}
                                >
                                    <div className={styles.peerToggleSwitch} />
                                    <span className={styles.peerToggleText}>
                                        {peerLoading ? '⏳ Loading...' : showPeerTrends ? `👥 Cohort Trends` : '👥 Show Cohort Trends'}
                                    </span>
                                </div>
                                {isPeerActive && (
                                    <span className={styles.peerToggleBadge}>
                                        {peerTrendData?.ai_benchmark ? '🤖' : '👥'} {peerCountLabel}
                                    </span>
                                )}
                            </div>

                            <div className={styles.trendsGrid}>

                                {/* 1. Carbon Intensity */}
                                <div className={styles.trendCard}>
                                    <div className={styles.trendHeader}>
                                        <span className={styles.trendIcon}>🏭</span>
                                        <h3>Carbon Intensity (Avg Across BUs)</h3>
                                    </div>
                                    <div className={styles.trendChart}>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <LineChart data={chartDataMerged} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                                <XAxis dataKey="label" tick={{ fontSize: 9, fill: '#94a3b8' }} />
                                                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <Tooltip contentStyle={chartTooltipStyle} formatter={(v, name) => {
                                                    const isPeer = name.startsWith('peer_');
                                                    if (isPeer) {
                                                        const pId = name.split('_')[1];
                                                        const peer = peerIds.find(p => p.id === pId);
                                                        return [`${Number(v).toFixed(1)} tCO₂e/$M`, peer ? peer.name : 'Peer'];
                                                    }
                                                    return [`${Number(v).toFixed(1)} tCO₂e/$M`, 'Your Team'];
                                                }} />
                                                <Line type="monotone" dataKey="avgCI" name="Your Team" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 4, fill: '#f59e0b' }} activeDot={{ r: 6 }} />
                                                {isPeerActive && peerIds.map(p => (
                                                    <Line key={p.id} type="monotone" dataKey={`peer_${p.id}_ci`} name={`peer_${p.id}`} stroke={p.color} strokeWidth={1.5} strokeDasharray="5 3" dot={false} />
                                                ))}
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
                                            <ComposedChart data={chartDataMerged} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                                <XAxis dataKey="label" tick={{ fontSize: 9, fill: '#94a3b8' }} />
                                                <YAxis yAxisId="left" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <Tooltip contentStyle={chartTooltipStyle} formatter={(v, name) => {
                                                    if (name.startsWith('peer_') && name.endsWith('_cum')) {
                                                        const pId = name.split('_')[1];
                                                        const peer = peerIds.find(p => p.id === pId);
                                                        return [`${Number(v).toFixed(0)} t`, `${peer ? peer.name : 'Peer'} (Cum)`];
                                                    }
                                                    return [`${Number(v).toFixed(0)} t`, name === 'cumulativeCarbon' ? 'Cumulative tCO₂e' : 'Per-Year tCO₂e'];
                                                }} />
                                                <Area yAxisId="left" type="monotone" dataKey="cumulativeCarbon" name="Cumulative Carbon" stroke="#ef4444" fill="rgba(239,68,68,0.15)" strokeWidth={2} dot={{ r: 3 }} />
                                                <Line yAxisId="right" type="monotone" dataKey="tco2e" name="Per-Year tCO₂e" stroke="#3b82f6" strokeWidth={2} strokeDasharray="4 3" dot={{ r: 3, fill: '#3b82f6' }} />
                                                {isPeerActive && peerIds.map(p => (
                                                    <Line key={p.id} yAxisId="left" type="monotone" dataKey={`peer_${p.id}_cum`} name={`peer_${p.id}_cum`} stroke={p.color} strokeWidth={1.5} strokeDasharray="5 3" dot={false} />
                                                ))}
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
                                            <ComposedChart data={chartDataMerged} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                                <XAxis dataKey="label" tick={{ fontSize: 9, fill: '#94a3b8' }} />
                                                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={(v) => `${currencySymbol()}${(v / 1_000_000).toFixed(0)}M`} />
                                                <Tooltip contentStyle={chartTooltipStyle} formatter={(v, name) => {
                                                    const isPeer = name.startsWith('peer_');
                                                    if (isPeer) {
                                                        const pId = name.split('_')[1];
                                                        const peer = peerIds.find(p => p.id === pId);
                                                        return [fmtM(v), peer ? peer.name : 'Peer'];
                                                    }
                                                    return [fmtM(v), 'Your EBITDA'];
                                                }} />
                                                <Area type="monotone" dataKey="ebitda" name="Your EBITDA" stroke="#10b981" fill="rgba(16,185,129,0.12)" strokeWidth={2.5} dot={{ r: 4, fill: '#10b981' }} activeDot={{ r: 6 }} />
                                                {isPeerActive && peerIds.map(p => (
                                                    <Line key={p.id} type="monotone" dataKey={`peer_${p.id}_ebitda`} name={`peer_${p.id}`} stroke={p.color} strokeWidth={1.5} strokeDasharray="5 3" dot={false} />
                                                ))}
                                            </ComposedChart>
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
                                            <LineChart data={chartDataMerged} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                                <XAxis dataKey="label" tick={{ fontSize: 9, fill: '#94a3b8' }} />
                                                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                                <Tooltip contentStyle={chartTooltipStyle} formatter={(v, name) => {
                                                    const isPeer = name.startsWith('peer_');
                                                    if (isPeer) {
                                                        const pId = name.split('_')[1];
                                                        const peer = peerIds.find(p => p.id === pId);
                                                        return [`${Number(v).toFixed(1)} / 100`, peer ? peer.name : 'Peer'];
                                                    }
                                                    return [`${Number(v).toFixed(1)} / 100`, 'Your Reputation'];
                                                }} />
                                                <Line type="monotone" dataKey="rep" name="Your Reputation" stroke="#8b5cf6" strokeWidth={2.5} dot={{ r: 4, fill: '#8b5cf6' }} activeDot={{ r: 6 }} />
                                                {isPeerActive && peerIds.map(p => (
                                                    <Line key={p.id} type="monotone" dataKey={`peer_${p.id}_rep`} name={`peer_${p.id}`} stroke={p.color} strokeWidth={1.5} strokeDasharray="5 3" dot={false} />
                                                ))}
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                            </div>

                            <div className={styles.trendCard} style={{ gridColumn: '1 / -1', marginTop: '1rem' }}>
                                <div className={styles.trendHeader}>
                                    <span className={styles.trendIcon}>📉</span>
                                    <h3>Muressons Stock Performance (2027–2036)</h3>
                                </div>
                                <div className={styles.trendChart}>
                                    <StockPerformanceChart
                                        historyData={history}
                                        globalState={globalState}
                                        businessUnits={bus}
                                        roundNumber={10}
                                        events={globalState.active_event_flags || {}}
                                        peerStockData={isPeerActive ? peerRounds.map(pr => ({ round: pr.round, price: pr.peerStockPrice })).filter(p => p.price) : null}
                                        peerLabel={isPeerActive ? (peerTrendData?.ai_benchmark ? 'AI Benchmark Avg' : 'Cohort Average') : null}
                                    />
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

                {/* ──────── TAB: TBL Matrix ──────── */}
                {activeTab === 'tbl_matrix' && (() => {
                    const fmtCurr = (v) => `${currencySymbol()}${(v / 1_000_000).toFixed(2)}M`;
                    const memo = generateBoardMemo(kpis, d);

                    const TBL_GRID = [
                        {
                            perspective: 'Financial',
                            icon: '💰',
                            color: '#3b82f6',
                            cells: [
                                { col: 'Profit', label: 'Adjusted EBITDA', value: fmtCurr(kpis.ebitda), health: kpis.ebitda > 10_000_000 ? 'good' : kpis.ebitda > 0 ? 'warn' : 'bad' },
                                { col: 'People', label: 'Instability Discount', value: d.instability_discount_applied ? '⚠️ Applied (−0.4)' : '✅ Not Applied', health: d.instability_discount_applied ? 'bad' : 'good' },
                                { col: 'Planet', label: 'Green Cost of Debt', value: `${(d.green_cost_of_debt_pct || kpis.greenDebt * 100).toFixed(2)}%`, health: (d.green_cost_of_debt_pct || 0) < 5 ? 'good' : 'warn' },
                            ],
                        },
                        {
                            perspective: 'Stakeholder',
                            icon: '🤝',
                            color: '#10b981',
                            cells: [
                                { col: 'Profit', label: 'VRIO Advantage', value: kpis.vrioActive ? '🟢 Active' : '🔴 Decayed', health: kpis.vrioActive ? 'good' : 'bad' },
                                { col: 'People', label: 'Social License (SLO)', value: `${kpis.avgSL.toFixed(1)} / 100`, health: kpis.avgSL >= 75 ? 'good' : kpis.avgSL >= 50 ? 'warn' : 'bad' },
                                { col: 'Planet', label: 'Group Reputation', value: `${kpis.groupRep.toFixed(1)} / 100`, health: kpis.groupRep >= 65 ? 'good' : kpis.groupRep >= 45 ? 'warn' : 'bad' },
                            ],
                        },
                        {
                            perspective: 'Internal Process',
                            icon: '⚙️',
                            color: '#f59e0b',
                            cells: [
                                { col: 'Profit', label: 'Final Group OPEX', value: fmtCurr(d.total_opex || 0), health: 'neutral' },
                                { col: 'People', label: 'Just Transition', value: (d.just_transition_passed || kpis.justTransitionPassed) ? '✅ Pass' : '❌ Fail', health: (d.just_transition_passed || kpis.justTransitionPassed) ? 'good' : 'bad' },
                                { col: 'Planet', label: 'Synergy (S_y) & Carbon', value: `${kpis.synergy.toFixed(2)}× · ${kpis.carbonTonnage.toFixed(0)}t`, health: kpis.synergy > 1.1 && kpis.carbonTonnage < 150 ? 'good' : 'warn' },
                            ],
                        },
                        {
                            perspective: 'Learning & Growth',
                            icon: '🎓',
                            color: '#8b5cf6',
                            cells: [
                                { col: 'Profit', label: 'R&D Allocation', value: `${(d.rd_allocation_pct || 0).toFixed(1)}%`, health: (d.rd_allocation_pct || 0) > 5 ? 'good' : 'warn' },
                                { col: 'People', label: 'Talent Retention (P_Talent)', value: kpis.pTalent > 0 ? kpis.pTalent.toFixed(2) : 'Stable', health: kpis.pTalent <= 0.5 ? 'good' : kpis.pTalent <= 1.0 ? 'warn' : 'bad' },
                                { col: 'Planet', label: 'Climate Resilience Factor', value: `${(d.climate_resilience_factor ?? 0.5).toFixed(2)}`, health: (d.climate_resilience_factor ?? 0.5) >= 0.7 ? 'good' : (d.climate_resilience_factor ?? 0.5) >= 0.4 ? 'warn' : 'bad' },
                            ],
                        },
                    ];

                    return (
                        <section className={styles.tblSection}>
                            <h2 className={styles.sectionTitle}>🧮 Integrated TBL × Balanced Scorecard Matrix</h2>
                            <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginBottom: '1.25rem' }}>
                                Kaplan & Norton Perspectives (rows) × Triple Bottom Line (columns)
                            </p>

                            {/* Grid Header */}
                            <div className={styles.tblGrid}>
                                <div className={styles.tblCorner}></div>
                                <div className={styles.tblColHeader}>💰 Profit</div>
                                <div className={styles.tblColHeader}>👥 People</div>
                                <div className={styles.tblColHeader}>🌍 Planet</div>

                                {TBL_GRID.map((row) => (
                                    <React.Fragment key={row.perspective}>
                                        <div className={styles.tblRowHeader} style={{ borderLeftColor: row.color }}>
                                            <span>{row.icon}</span> {row.perspective}
                                        </div>
                                        {row.cells.map((cell, ci) => (
                                            <div
                                                key={`${row.perspective}-${ci}`}
                                                className={`${styles.tblCell} ${styles[`tblCell${cell.health === 'good' ? 'Good' : cell.health === 'bad' ? 'Bad' : cell.health === 'warn' ? 'Warn' : 'Neutral'}`]}`}
                                            >
                                                <div className={styles.tblCellLabel}>{cell.label}</div>
                                                <div className={styles.tblCellValue}>{cell.value}</div>
                                            </div>
                                        ))}
                                    </React.Fragment>
                                ))}
                            </div>

                            {/* Board Memo */}
                            <div className={styles.boardMemo}>
                                <h3 className={styles.boardMemoTitle}>📋 Board Memo — Diagnostic Synthesis</h3>
                                {memo.map((sentence, i) => (
                                    <p key={i} className={styles.boardMemoSentence}>{sentence}</p>
                                ))}
                            </div>
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
                                        {history.filter(snap => (snap.round || snap.round_number || 0) <= maxRounds).map((snap, i) => {
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
                                            const qLabel = roundToQuarter(roundNum).label;
                                            return (
                                                <tr key={i} className={i % 2 === 0 ? styles.evenRow : ''}>
                                                    <td className={styles.roundNum}>R{roundNum}<br/><span style={{ fontSize: '0.7em', opacity: 0.7 }}>{qLabel}</span></td>
                                                    <td>{currencySymbol()}{(cash / 1_000_000).toFixed(2)}</td>
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


                {/* ──────── TAB: Final Report ──────── */}
                {activeTab === 'report' && (() => {
                    const fmtM = (v) => `${currencySymbol()}${(v / 1_000_000).toFixed(2)}M`;
                    const memo = generateBoardMemo(kpis, d);
                    return (
                        <section className={styles.reportSection}>
                            <h2 className={styles.sectionTitle}>📋 Muressons Global Corporation — Final Report (Year 5)</h2>

                            {/* Top KPIs */}
                            <div className={styles.reportKpis}>
                                <div className={styles.reportKpiCard}>
                                    <span className={styles.reportKpiLabel}>🏆 Terminal Value</span>
                                    <span className={styles.reportKpiValue}>{fmtM(d.terminal_value || 0)}</span>
                                </div>
                                <div className={styles.reportKpiCard}>
                                    <span className={styles.reportKpiLabel}>🔄 Regenerative Multiple</span>
                                    <span className={styles.reportKpiValue}>{(d.regenerative_multiple || 0).toFixed(2)}×</span>
                                </div>
                                <div className={styles.reportKpiCard}>
                                    <span className={styles.reportKpiLabel}>📈 Adjusted EBITDA</span>
                                    <span className={styles.reportKpiValue}>{fmtM(kpis.ebitda)}</span>
                                </div>
                                <div className={styles.reportKpiCard}>
                                    <span className={styles.reportKpiLabel}>🌐 Market Headline</span>
                                    <span className={styles.reportKpiValue} style={{ fontSize: '0.9rem' }}>{d.profile_title || '—'}</span>
                                </div>
                            </div>

                            {/* BU Breakdown */}
                            <h3 style={{ color: '#818cf8', fontSize: '0.85rem', fontWeight: 700, margin: '1.5rem 0 0.8rem' }}>
                                🏢 Business Unit Performance (Final State)
                            </h3>
                            <div className={styles.roundTableWrap}>
                                <table className={styles.roundTable}>
                                    <thead>
                                        <tr>
                                            <th style={{ textAlign: 'left' }}>Business Unit</th>
                                            <th>Revenue</th>
                                            <th>OPEX</th>
                                            <th>Margin</th>
                                            <th>Carbon Intensity</th>
                                            <th>Social License</th>
                                            <th>NCD</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {bus.map((b, i) => (
                                            <tr key={b.bu_id || i} className={i % 2 === 0 ? styles.evenRow : ''}>
                                                <td style={{ textAlign: 'left', fontWeight: 700, color: '#818cf8' }}>
                                                    {(b.bu_id || '').replace(/_/g, ' ').toUpperCase()}
                                                </td>
                                                <td className={styles.mono}>{fmtM(b.revenue_base || 0)}</td>
                                                <td className={styles.mono}>{fmtM(b.opex_base || 0)}</td>
                                                <td className={styles.mono} style={{ color: (b.revenue_base || 0) - (b.opex_base || 0) > 0 ? '#10b981' : '#ef4444' }}>
                                                    {fmtM((b.revenue_base || 0) - (b.opex_base || 0))}
                                                </td>
                                                <td className={styles.mono}>{(b.carbon_intensity || 0).toFixed(1)}</td>
                                                <td className={styles.mono} style={{ color: (b.social_license_score || 0) >= 75 ? '#10b981' : '#f59e0b' }}>
                                                    {(b.social_license_score || 0).toFixed(1)}
                                                </td>
                                                <td className={styles.mono}>{(b.natural_capital_debt || 0).toFixed(1)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* M_R Breakdown */}
                            {mrItems.length > 0 && (
                                <>
                                    <h3 style={{ color: '#818cf8', fontSize: '0.85rem', fontWeight: 700, margin: '1.5rem 0 0.8rem' }}>
                                        🧬 M<sub>R</sub> Regenerative Multiple Breakdown
                                    </h3>
                                    <div className={styles.roundTableWrap}>
                                        <table className={styles.roundTable}>
                                            <thead>
                                                <tr>
                                                    <th style={{ textAlign: 'left' }}>Component</th>
                                                    <th>Value</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {mrItems.map((item, i) => (
                                                    <tr key={item.key} className={i % 2 === 0 ? styles.evenRow : ''}>
                                                        <td style={{ textAlign: 'left' }}>
                                                            <span className={styles.mrTooltipWrap}>
                                                                {item.key.replace(/_/g, ' ')}
                                                                <span className={styles.mrTooltip}>{item.tooltip}</span>
                                                            </span>
                                                        </td>
                                                        <td className={styles.mono} style={{ color: item.value >= 0 ? '#10b981' : '#ef4444' }}>
                                                            {item.value > 0 ? '+' : ''}{item.value.toFixed(2)}
                                                        </td>
                                                    </tr>
                                                ))}
                                                <tr className={styles.evenRow} style={{ borderTop: '2px solid #6366f1' }}>
                                                    <td style={{ textAlign: 'left', fontWeight: 700 }}>Total M<sub>R</sub></td>
                                                    <td className={styles.mono} style={{ fontWeight: 700 }}>{(d.regenerative_multiple || 0).toFixed(2)}×</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </>
                            )}

                            {/* Board Memo */}
                            <div className={styles.boardMemo}>
                                <h3 className={styles.boardMemoTitle}>📋 Board Memo — Executive Synthesis</h3>
                                {memo.map((sentence, i) => (
                                    <p key={i} className={styles.boardMemoSentence}>{sentence}</p>
                                ))}
                            </div>

                            {/* Download Button */}
                            <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
                                <button className={styles.downloadBtn} onClick={handleDownload} style={{ marginLeft: 0, padding: '0.8rem 2rem', fontSize: '0.9rem' }}>
                                    📥 Download Full Report (HTML)
                                </button>
                            </div>
                        </section>
                    );
                })()}

                {/* ── Footer ── */}
                <div className={styles.closeRow} style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', alignItems: 'center' }}>


                    {/* ──────── TAB: DNA Map (frozen Sankey) ──────── */}
                    {activeTab === 'dna_map' && dnaSnapshot && (
                      <section style={{ padding: '20px 0' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                          <h2 className={styles.sectionTitle} style={{ marginBottom: 0 }}>🧬 Consequence DNA Map — System Freeze</h2>
                          <button
                            onClick={() => {
                              const svgEl = document.querySelector('[class*="sankeySvg"]');
                              if (!svgEl) return;
                              const svgData = new XMLSerializer().serializeToString(svgEl);
                              const canvas = document.createElement('canvas');
                              const bbox = svgEl.getBoundingClientRect();
                              canvas.width = bbox.width * 2;
                              canvas.height = bbox.height * 2;
                              const ctx = canvas.getContext('2d');
                              ctx.scale(2, 2);
                              const img = new Image();
                              img.onload = () => {
                                ctx.fillStyle = '#0f172a';
                                ctx.fillRect(0, 0, canvas.width, canvas.height);
                                ctx.drawImage(img, 0, 0, bbox.width, bbox.height);
                                const link = document.createElement('a');
                                link.download = `consequence-dna-${new Date().toISOString().slice(0,10)}.png`;
                                link.href = canvas.toDataURL('image/png');
                                link.click();
                              };
                              img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
                            }}
                            style={{
                              background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)',
                              borderRadius: 8, color: '#818cf8', cursor: 'pointer', padding: '6px 14px',
                              fontSize: '0.72rem', fontWeight: 600, transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                            }}
                          >
                            📸 Export PNG
                          </button>
                        </div>
                        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 16, lineHeight: 1.6 }}>
                          This frozen Sankey diagram captures the complete causal chain of your decisions from Round 1 through Round 10.
                          Each path traces how a strategic choice propagated through flags, stakeholder conflicts, and metric shifts
                          to impact your final Regenerative Multiple. Hover over paths to see impact scores.
                        </p>
                        <div style={{ border: '1px solid rgba(99,102,241,0.2)', borderRadius: 12, overflow: 'hidden' }}>
                          <ConsequenceDNAVisualizer
                            isOpen={true}
                            frozen={true}
                            inline={true}
                            snapshotData={dnaSnapshot}
                            onClose={() => setActiveTab('scorecard')}
                          />
                        </div>
                      </section>
                    )}

                    {/* ──────── TAB: Pathway Discovery ──────── */}
                    {activeTab === 'pathway' && d.pathway_discovery && (() => {
                        const pd = d.pathway_discovery;
                        const chain = pd.foreshadowing_chain || [];

                        const ROUND_DECISION_THEMES = {
                            1: { icon: '📋', theme: 'ESG Baseline Assessment', desc: 'Board mandated ESG materiality audit depth' },
                            2: { icon: '📊', theme: 'Double Materiality Gate', desc: 'CSRD framework alignment decision' },
                            3: { icon: '🏭', theme: 'Scope 3 Supply Chain', desc: 'Supply chain decarbonisation strategy' },
                            4: { icon: '🔥', theme: 'Contagion Crisis', desc: 'Reputational crisis response strategy' },
                            5: { icon: '🌪️', theme: 'Climate Physical Risk', desc: 'Climate resilience investment choice' },
                            6: { icon: '🤖', theme: 'AI Ethics & Bias', desc: 'Algorithmic ethics governance decision' },
                            7: { icon: '♻️', theme: 'Circular Economy Pivot', desc: 'EU circular compliance strategy' },
                            8: { icon: '💧', theme: 'Blue Water Stress', desc: 'Watershed scarcity response' },
                            9: { icon: '✊', theme: 'Just Transition', desc: 'Workforce & community transition plan' },
                            10: { icon: '🏛️', theme: 'Grand Finale', desc: 'Activist ultimatum / final strategic choice' },
                        };

                        return (
                            <section style={{ padding: '20px 0' }}>
                                <h2 className={styles.sectionTitle}>🗺️ Pathway Discovery — How Your Ending Was Shaped</h2>

                                {/* Pathway Name + Description */}
                                <div style={{
                                    background: '#0f172a',
                                    border: '1px solid #334155',
                                    borderRadius: '8px',
                                    padding: '1rem',
                                    marginBottom: '0.8rem',
                                }}>
                                    <div style={{ fontSize: '0.92rem', fontWeight: 800, color: '#c4b5fd', marginBottom: '0.3rem' }}>
                                        {pd.pathway_name || 'Unknown Pathway'}
                                    </div>
                                    <div style={{ fontSize: '0.82rem', color: '#e2e8f0', lineHeight: 1.55 }}>
                                        {pd.pathway_description || 'Your decisions shaped a unique ending pathway.'}
                                    </div>
                                </div>

                                {/* Foreshadowing Chain */}
                                {chain.length > 0 && (
                                    <>
                                        <div style={{
                                            fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
                                            color: '#94a3b8', letterSpacing: '0.08em', marginBottom: '0.5rem',
                                        }}>
                                            Foreshadowing Signals — Rounds {chain[0]?.round || '?'} to {chain[chain.length - 1]?.round || '?'}
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                            {chain.map((step, i) => {
                                                const rt = ROUND_DECISION_THEMES[step.round] || {};
                                                const headline = step.headline || step.event || null;
                                                const detail = step.detail || step.hint || null;
                                                return (
                                                    <div key={i} style={{
                                                        display: 'flex', alignItems: 'flex-start', gap: '0.6rem',
                                                        padding: '0.6rem 0.75rem', borderRadius: '6px',
                                                        background: '#0f172a',
                                                        borderLeft: `3px solid ${i === chain.length - 1 ? '#a78bfa' : '#475569'}`,
                                                    }}>
                                                        <span style={{
                                                            flexShrink: 0, width: 26, height: 26, borderRadius: '50%',
                                                            background: i === chain.length - 1 ? 'rgba(167,139,250,0.2)' : 'rgba(255,255,255,0.05)',
                                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                            fontSize: '0.65rem', fontWeight: 800, color: i === chain.length - 1 ? '#a78bfa' : '#64748b',
                                                            border: i === chain.length - 1 ? '1px solid rgba(167,139,250,0.4)' : '1px solid rgba(255,255,255,0.1)',
                                                        }}>R{step.round}</span>
                                                        <div style={{ flex: 1 }}>
                                                            <div style={{ fontSize: '0.74rem', fontWeight: 700, color: '#e2e8f0' }}>
                                                                {headline || `${rt.icon || '📌'} ${rt.theme || `Round ${step.round}`}`}
                                                            </div>
                                                            {detail && (
                                                                <div style={{ fontSize: '0.66rem', color: '#94a3b8', marginTop: '0.15rem', lineHeight: 1.45 }}>
                                                                    {detail}
                                                                </div>
                                                            )}
                                                            {!detail && rt.desc && (
                                                                <div style={{ fontSize: '0.66rem', color: '#64748b', marginTop: '0.15rem', fontStyle: 'italic' }}>
                                                                    {rt.desc}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </>
                                )}

                                {/* Pedagogical Note */}
                                {pd.pedagogical_note && (
                                    <div style={{
                                        marginTop: '0.8rem', padding: '0.6rem 0.8rem', borderRadius: '6px',
                                        background: 'rgba(168,85,247,0.06)',
                                        border: '1px solid rgba(168,85,247,0.2)',
                                        fontSize: '0.72rem', color: '#c4b5fd', lineHeight: 1.5,
                                        fontStyle: 'italic',
                                    }}>
                                        <strong>💡 Facilitator Note:</strong> {pd.pedagogical_note}
                                    </div>
                                )}
                            </section>
                        );
                    })()}

                    {/* ──────── TAB: Decision Journey ──────── */}
                    {activeTab === 'journey' && history && history.length > 0 && (() => {
                        const ROUND_DEEP = {
                            1: { icon: '📋', theme: 'ESG Baseline Assessment', crisis: 'The Board mandated a comprehensive ESG materiality audit to identify the group\'s exposure to sustainability risks across all four business units.',
                                options: {
                                    option_a: { label: 'Surface-Level Scan', cost: '$0', impacts: ['Reputation −2: Stakeholders perceive the audit as performative — NGOs flag "greenwashing" risk.', 'No hidden liabilities uncovered — blind spots in Electronics BU supply chain remain undetected.', 'Sets a weak baseline for future CSRD reporting in Round 2, making Double Materiality harder.'] },
                                    option_b: { label: 'Deep Forensic Audit', cost: '−$3M', impacts: ['Reputation +5: Transparent disclosure earns analyst upgrades and media credibility.', 'Uncovers hidden natural capital debt in Mining BU — enables proactive remediation before regulators intervene.', 'Creates robust data foundation for Scope 3 calculations in Round 3 and CSRD compliance in Round 2.', 'The $3M cost reduces short-term treasury but unlocks the "Deep Audit Completed" causal flag — a prerequisite for M_R bonuses later.'] },
                                    option_c: { label: 'Phased Audit Rollout', cost: '−$1.5M', impacts: ['Reputation +2: Moderate credibility — seen as "trying" but not fully committed.', 'Partial discovery of risks — Electronics supply chain gaps may surface later in Round 4 Contagion Crisis.', 'Cost-efficient but delays full baseline by one quarter, creating a data gap in trend reporting.'] },
                                },
                            },
                            2: { icon: '📊', theme: 'Double Materiality Gate', crisis: 'The EU Corporate Sustainability Reporting Directive (CSRD) requires Double Materiality assessment — evaluating both how sustainability issues affect the company AND how the company affects society.',
                                options: {
                                    option_a: { label: 'Full CSRD Alignment', cost: 'Rep+5, Gov−5', impacts: ['Full alignment with EFRS standards — positions Muressons as an EU regulatory leader.', 'Governance score drops as internal processes are restructured to meet disclosure requirements.', 'Unlocks the "CSRD Governance Premium" (+0.10 M_R) — a direct multiplier on terminal value.', 'Creates defensible audit trail that protects against regulatory fines in later rounds.'] },
                                    option_b: { label: 'Strategic Exceptions', cost: 'Rep+2, Gov−2', impacts: ['Cherry-picks favorable metrics for disclosure — regulators may challenge completeness later.', 'Modest reputation gain but leaves gaps that could be exploited in Round 4 media crisis.', 'Governance impact is manageable but the incomplete framework may hinder Scope 3 reporting.'] },
                                    option_c: { label: 'Ignore Framework', cost: 'Rep−5, Gov+10', impacts: ['Reputation suffers significantly — ESG-focused investors begin divesting.', 'Governance score soars as management retains full operational control without external constraints.', 'Triggers the "Governance Fragility" causal flag — creates compounding vulnerability in Rounds 5-8.', 'Short-term efficiency gains are overwhelmed by medium-term regulatory and reputational costs.'] },
                                },
                            },
                            3: { icon: '🏭', theme: 'Scope 3 Supply Chain', crisis: 'Mandatory Scope 3 GHG disclosures are imminent. The Electronics and Mining BUs have extensive upstream supply chains with significant embedded carbon.',
                                options: {
                                    option_a: { label: 'Rapid Supplier Switch', cost: '−$4M', impacts: ['Carbon Intensity −15: Immediate and dramatic decarbonisation of supply chain.', 'Treasury hit of $4M reflects supplier transition costs — contract terminations, new onboarding.', 'Triggers "Broz Pioneer" causal flag — unlocks Green Bond Premium and Resilience Bonus pathways.', 'Reduces Year 5 carbon tax liability significantly, potentially saving more than the upfront cost.'] },
                                    option_b: { label: 'Green Bond Investment', cost: '−$2M', impacts: ['Carbon Intensity −8: Moderate reduction funded through ESG-labelled debt instruments.', 'Green bond issuance signals market credibility — cost of debt decreases for future rounds.', 'Builds a bridge to Net Zero but may not be aggressive enough to avoid tipping point in Round 5.'] },
                                    option_c: { label: 'Offset & Defer', cost: '−$1M', impacts: ['Reputation −3: Carbon offsets are increasingly viewed as "climate delay" by stakeholders.', 'Minimal actual emission reduction — kicks the carbon liability to future rounds.', 'Round 5 Climate Event and Round 7 Circular Economy will compound the deferred carbon debt.', 'Cheapest short-term option but creates the highest long-term carbon tax exposure at terminal.'] },
                                },
                            },
                            4: { icon: '🔥', theme: 'Contagion Crisis', crisis: 'An investigative journalist exposes child labour and toxic waste dumping in a tier-2 supplier to the Electronics BU. The story goes viral, triggering regulatory investigations across all business units.',
                                options: {
                                    option_a: { label: 'Full Transparency', cost: '−$6M', impacts: ['Reputation +10: Radical transparency earns grudging respect from media and regulators.', '$6M covers immediate remediation, victim compensation, and independent supply chain audit.', 'Triggers "Broz Net Positive Disclosure" flag — strengthens the Truth Premium M_R component.', 'The reputational recovery creates a buffer for future crises in Rounds 5-8.'] },
                                    option_b: { label: 'Damage Control PR', cost: '−$2M', impacts: ['Reputation +2: Professional crisis management contains the story but doesn\'t resolve root causes.', 'Media cycle moves on but the underlying supply chain vulnerability remains exploitable.', 'If Round 1 chose Surface-Level Scan, the blind spots compound — "Electronics Blindspot" flag activates.'] },
                                    option_c: { label: 'Deny & Deflect', cost: '$0', impacts: ['Reputation −15: Catastrophic brand damage as whistleblowers provide contradicting evidence.', 'Triggers "Broz Greenwash Risk" flag — permanently damages credibility with ESG investors.', 'Compounds in Rounds 6-9: stakeholder trust deficit makes every future crisis more expensive.', 'The $0 upfront "saving" typically costs $20M+ in compounded reputational and regulatory penalties.'] },
                                },
                            },
                            5: { icon: '🌪️', theme: 'Climate Physical Risk', crisis: 'A Category 4 cyclone makes landfall near key Mining and Agriculture facilities. Infrastructure damage is immediate. Insurance premiums are repricing globally.',
                                options: {
                                    option_a: { label: 'Hard Engineering', cost: '−$8M', impacts: ['Maximum physical resilience — seawalls, reinforced structures, backup power systems.', 'Unlocks "Resilience Bonus" (+0.20 M_R) — the most valuable climate-linked multiplier.', 'Protects revenue base from future climate events — facilities operate through disruptions.', 'The $8M investment reduces insurance costs and protects asset book value at terminal.'] },
                                    option_b: { label: 'Nature-Based Solutions', cost: '−$5M', impacts: ['Mangrove restoration, wetland buffers, and green infrastructure provide moderate protection.', 'Natural Capital Debt decreases — the ecosystem services create ongoing value beyond storm protection.', 'Partial resilience — another severe event could still cause damage, but at reduced severity.', 'Signals climate leadership to stakeholders — reputation and SLO both benefit modestly.'] },
                                    option_c: { label: 'Insurance Only', cost: '−$2M', impacts: ['Minimum capital outlay — relies entirely on insurance markets to absorb future losses.', 'No Resilience Bonus earned — misses +0.20 M_R that directly multiplies terminal value.', 'Insurance premiums will escalate in subsequent rounds as climate risk reprices.', 'Facilities remain vulnerable — any Round 8 Water Scarcity event hits unprotected assets.'] },
                                },
                            },
                            6: { icon: '🤖', theme: 'AI Ethics & Bias', crisis: 'An internal audit reveals the Software BU\'s AI recruitment algorithm systematically discriminates against certain demographic groups. Regulators and civil rights organisations are notified.',
                                options: {
                                    option_a: { label: 'Monetise Algorithm', cost: '+$5M', impacts: ['Revenue +$5M from licensing the biased algorithm to third parties — immediate treasury gain.', 'Reputation −20: Catastrophic stakeholder backlash when the monetisation becomes public.', 'Triggers severe "AI Reputational Risk" flag — talent flight accelerates from Software BU.', 'P_Talent penalty multiplier increases, inflating Software BU OPEX in all subsequent rounds.', 'The +$5M gain is dwarfed by the terminal value destruction from talent and reputation collapse.'] },
                                    option_b: { label: 'Ethical Overhaul', cost: '−$8M', impacts: ['SLO +15: Communities and workforce see genuine commitment to ethical technology governance.', 'Earns "Truth Premium" (+0.15 M_R) — one of the highest-value multiplier components.', '$8M funds algorithmic retraining, third-party bias audits, and a public transparency report.', 'Software BU talent retention stabilises — P_Talent penalty is avoided or reversed.', 'Creates defensive moat against Round 9 Just Transition labour scrutiny.'] },
                                    option_c: { label: 'Quiet Patch', cost: '−$1M', impacts: ['Reputation −5: The patch fixes symptoms but the systemic bias architecture remains.', 'If discovered later (probable in media-rich environment), the cover-up compounds damage.', 'No Truth Premium earned — misses +0.15 M_R on terminal value.', 'Moderate cost but creates ongoing governance fragility that regulators may exploit.'] },
                                },
                            },
                            7: { icon: '♻️', theme: 'Circular Economy', crisis: 'The EU Circular Economy Action Plan mandates 60% waste diversion across all industrial operations. Non-compliance triggers escalating fines and market access restrictions.',
                                options: {
                                    option_a: { label: 'Circular Redesign', cost: '−$10M', impacts: ['NCD −12: Dramatic reduction in Natural Capital Debt as products are redesigned for full lifecycle.', 'Transforms Mining and Agriculture BUs into closed-loop systems — waste becomes feedstock.', 'Unlocks cross-BU synergy pathways — materials flow between divisions creating internal value.', 'The $10M investment pays back through reduced raw material costs and EU compliance positioning.'] },
                                    option_b: { label: 'Producer Responsibility', cost: '−$5M', impacts: ['Meets minimum EU Extended Producer Responsibility requirements — avoids fines.', 'Moderate circularity gains but the business model remains fundamentally linear.', 'Does not unlock the Synergy Bonus — BUs continue operating as disconnected silos.', 'Sufficient for compliance but misses the strategic upside of systemic redesign.'] },
                                    option_c: { label: 'Waste-to-Energy', cost: '−$7M', impacts: ['Synergy +0.35: Creates an internal energy ecosystem — waste from one BU powers another.', 'The waste-to-energy pathway is the primary unlock for the Industrial Synergy multiplier.', 'Reduces external energy costs and creates revenue from excess energy sales.', 'Important: doesn\'t reduce NCD as much as Circular Redesign — the waste is burned, not eliminated.'] },
                                },
                            },
                            8: { icon: '💧', theme: 'Blue Water Stress', crisis: 'The watershed serving Mining and Agriculture operations is reclassified from "stressed" to "critically stressed." Water allocation permits are being revoked. Communities demand priority access.',
                                options: {
                                    option_a: { label: 'Water Efficiency All BUs', cost: '−$12M', impacts: ['Comprehensive water recycling and efficiency across all four business units.', 'Eliminates water scarcity risk as a terminal value threat — operational continuity assured.', 'SLO benefit: communities see Muressons as a responsible water steward rather than a competitor.', '$12M is the most expensive option but creates the broadest resilience across the portfolio.'] },
                                    option_b: { label: 'Prioritise Electronics', cost: '−$4M', impacts: ['Focuses water efficiency investment on the highest-value BU — protects Software and Electronics.', 'Mining and Agriculture BUs remain exposed — if water permits are revoked, those BUs face shutdown.', 'Cost-efficient but creates asymmetric risk — the portfolio is only partially protected.', 'May trigger community backlash if Mining BU operations degrade local water access.'] },
                                    option_c: { label: 'Desalination Mega-Project', cost: '−$30M', impacts: ['Creates an independent water supply — complete decoupling from watershed dependency.', 'The $30M cost is the single largest capital allocation in the simulation — massive treasury impact.', 'Eliminates water risk permanently but the capital could have been deployed across multiple initiatives.', 'Energy-intensive desalination increases carbon footprint — potential conflict with decarbonisation goals.'] },
                                },
                            },
                            9: { icon: '✊', theme: 'Just Transition', crisis: 'Three legacy factories must close as Muressons pivots to sustainable operations. 2,400 workers face displacement. Community protests are escalating. The ILO and trade unions are watching.',
                                options: {
                                    option_a: { label: 'Immediate Closure', cost: '+$5M', impacts: ['Treasury +$5M from immediate OPEX savings — factories close within 90 days.', 'SLO −20: Communities and displaced workers have no safety net — protests intensify.', 'Triggers the "Instability Discount" (−0.40 M_R) if average SLO falls below 75 — devastating to terminal value.', 'Media coverage of displaced families creates lasting reputational damage heading into the Grand Finale.', 'The +$5M saving can easily destroy $50M+ in terminal value through the M_R penalty.'] },
                                    option_b: { label: 'Managed Transition', cost: '−$12M', impacts: ['SLO +10: Workers receive retraining programs and 18-month transition support.', 'Earns "Just Transition Bonus" (+0.12 M_R) — rewards responsible workforce management.', '$12M covers retraining centres, income bridges, and community liaison officers.', 'Maintains SLO above 75 threshold — avoids the catastrophic Instability Discount.'] },
                                    option_c: { label: 'Community Fund', cost: '−$20M', impacts: ['SLO +18: The most generous community investment — establishes a permanent transition fund.', 'Earns both "Just Transition Bonus" (+0.12) AND "Community Champion Bonus" (+0.18 M_R).', '$20M creates a self-sustaining community development corporation — legacy beyond the simulation.', 'Combined +0.30 M_R bonus is the single highest M_R contribution available from any single round.'] },
                                },
                            },
                            10: { icon: '🏛️', theme: 'Grand Finale', crisis: 'An activist consortium has acquired a blocking stake in Muressons Global. They demand a strategic review: integrate and reform, spin off underperformers, or divest entirely. The Board must decide.',
                                options: {
                                    option_a: { label: 'Resist & Integrate', cost: '−$5M', impacts: ['Maintains portfolio integrity — all four BUs continue operating as an integrated group.', '$5M funds legal defence, shareholder communications, and operational restructuring.', 'Preserves cross-BU synergy multiplier — if Synergy was built in R7, this protects that investment.', 'The activist consortium may launch a proxy fight — governance strength from R2 decisions determines outcome.'] },
                                    option_b: { label: 'Spin-off', cost: '+$10M', impacts: ['Treasury +$10M from spinning off one or more underperforming BUs.', 'Synergy multiplier is partially reduced as cross-BU value chains are severed.', 'Allows remaining BUs to focus capital on their strongest sustainability positions.', 'Market generally rewards focused portfolios — valuation multiple may increase for retained BUs.'] },
                                    option_c: { label: 'Divest', cost: '+$25M', impacts: ['Treasury +$25M from full divestiture of non-core assets — maximum immediate cash generation.', 'Synergy multiplier drops significantly — the integrated industrial ecosystem is dismantled.', 'Eliminates carbon and water liabilities from divested BUs — improves per-unit sustainability metrics.', 'Highest short-term cash but destroys the long-term strategic optionality built over 9 rounds.'] },
                                },
                            },
                        };

                        const choiceColors = { option_a: '#38bdf8', option_b: '#f59e0b', option_c: '#f87171' };
                        const choiceLetters = { option_a: 'A', option_b: 'B', option_c: 'C' };

                        // Hover state managed via a wrapper component
                        const JourneyRow = ({ roundNum, h, prevH }) => {
                            const [hovered, setHovered] = React.useState(false);
                            const rd = ROUND_DEEP[roundNum] || {};
                            const choice = h?.choice_selected || h?.choice || h?.global_state?.active_event_flags?.[`r${roundNum}_choice`] || null;
                            const choiceLetter = choiceLetters[choice] || '?';
                            const choiceLabel = h?.choice_title || h?.choice_label || (rd.options?.[choice]?.label) || null;
                            const choiceColor = choiceColors[choice] || '#94a3b8';
                            const optionData = rd.options?.[choice];

                            let delta = h?.treasury_delta ?? null;
                            if (delta === null) {
                                const curr = h?.treasury ?? h?.corporate_treasury ?? h?.global_state?.corporate_treasury ?? 0;
                                const prev = prevH ? (prevH?.treasury ?? prevH?.corporate_treasury ?? prevH?.global_state?.corporate_treasury ?? curr) : curr;
                                delta = curr - prev;
                            }
                            const deltaStr = delta !== 0 ? `${delta >= 0 ? '+' : ''}${currencySymbol()}${(Math.abs(delta) / 1_000_000).toFixed(1)}M` : null;

                            return (
                                <div
                                    onMouseEnter={() => setHovered(true)}
                                    onMouseLeave={() => setHovered(false)}
                                    style={{ position: 'relative', cursor: 'pointer' }}
                                >
                                    {/* Row */}
                                    <div style={{
                                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                                        padding: '0.45rem 0.65rem', borderRadius: '6px',
                                        background: hovered ? 'rgba(99,102,241,0.1)' : 'rgba(0,0,0,0.15)',
                                        borderLeft: `3px solid ${choiceColor}`,
                                        transition: 'background 0.15s',
                                    }}>
                                        <span style={{
                                            flexShrink: 0, width: 22, height: 22, borderRadius: '50%',
                                            background: `${choiceColor}18`,
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            fontSize: '0.6rem', fontWeight: 800, color: choiceColor,
                                            border: `1px solid ${choiceColor}40`,
                                        }}>{roundNum}</span>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.7rem', fontWeight: 700, color: '#e2e8f0' }}>
                                                <span>{rd.icon || '📌'}</span>
                                                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{rd.theme || `Round ${roundNum}`}</span>
                                            </div>
                                            {choiceLabel && (
                                                <div style={{ fontSize: '0.62rem', color: '#94a3b8', marginTop: '0.1rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                    {choiceLabel}
                                                </div>
                                            )}
                                        </div>
                                        <span style={{
                                            flexShrink: 0, padding: '2px 8px', borderRadius: '4px',
                                            fontSize: '0.65rem', fontWeight: 800,
                                            background: `${choiceColor}18`, color: choiceColor,
                                            border: `1px solid ${choiceColor}30`,
                                            fontFamily: "'JetBrains Mono', monospace",
                                        }}>{choiceLetter}</span>
                                        {deltaStr && (
                                            <span style={{
                                                flexShrink: 0, fontSize: '0.62rem', fontWeight: 700,
                                                color: delta >= 0 ? '#4ade80' : '#f87171',
                                                fontFamily: "'JetBrains Mono', monospace",
                                                minWidth: '48px', textAlign: 'right',
                                            }}>{deltaStr}</span>
                                        )}
                                    </div>

                                    {/* Hover Popup */}
                                    {hovered && optionData && (
                                        <div style={{
                                            position: 'absolute', left: 0, right: 0, top: '100%', zIndex: 50,
                                            marginTop: '4px',
                                            background: 'linear-gradient(135deg, #1e293b, #0f172a)',
                                            border: `1px solid ${choiceColor}50`,
                                            borderRadius: '10px',
                                            padding: '1rem 1.1rem',
                                            boxShadow: `0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px ${choiceColor}20`,
                                            animation: 'fadeIn 0.15s ease-out',
                                        }}>
                                            {/* Crisis Context */}
                                            <div style={{ fontSize: '0.68rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, marginBottom: '0.4rem' }}>
                                                Round {roundNum} — Crisis Context
                                            </div>
                                            <div style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.55, marginBottom: '0.7rem', fontStyle: 'italic', borderLeft: '2px solid #475569', paddingLeft: '0.6rem' }}>
                                                {rd.crisis}
                                            </div>

                                            {/* Your Decision */}
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.6rem' }}>
                                                <span style={{
                                                    padding: '3px 10px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 800,
                                                    background: `${choiceColor}20`, color: choiceColor,
                                                    border: `1px solid ${choiceColor}40`,
                                                }}>
                                                    Option {choiceLetter}: {optionData.label}
                                                </span>
                                                {optionData.cost && (
                                                    <span style={{ fontSize: '0.68rem', color: '#94a3b8', fontFamily: "'JetBrains Mono', monospace" }}>
                                                        ({optionData.cost})
                                                    </span>
                                                )}
                                            </div>

                                            {/* Impact Chain */}
                                            <div style={{ fontSize: '0.65rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, marginBottom: '0.35rem' }}>
                                                ⛓️ Impact Chain & Consequences
                                            </div>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                                                {optionData.impacts.map((impact, idx) => (
                                                    <div key={idx} style={{
                                                        display: 'flex', alignItems: 'flex-start', gap: '0.4rem',
                                                        padding: '0.35rem 0.5rem', borderRadius: '5px',
                                                        background: 'rgba(255,255,255,0.02)',
                                                        borderLeft: `2px solid ${idx === 0 ? choiceColor : idx === optionData.impacts.length - 1 ? '#a78bfa' : '#334155'}`,
                                                    }}>
                                                        <span style={{ flexShrink: 0, fontSize: '0.65rem', color: idx === 0 ? choiceColor : '#64748b', marginTop: '1px' }}>
                                                            {idx === 0 ? '▸' : idx === optionData.impacts.length - 1 ? '◆' : '│'}
                                                        </span>
                                                        <span style={{ fontSize: '0.72rem', color: '#e2e8f0', lineHeight: 1.5 }}>
                                                            {impact}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        };

                        return (
                            <section style={{ padding: '20px 0' }}>
                                <h2 className={styles.sectionTitle}>📜 Full Decision Journey — 10 Rounds</h2>
                                <p style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: '0.8rem', lineHeight: 1.5 }}>
                                    Hover over each round to reveal the full impact chain — how your strategic choice cascaded through financial, reputational, and systemic consequences.
                                </p>

                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                                    {history.slice(0, 10).map((h, i) => (
                                        <JourneyRow key={i + 1} roundNum={i + 1} h={h} prevH={i > 0 ? history[i - 1] : null} />
                                    ))}
                                </div>

                                {/* Summary footer */}
                                {history.length >= 10 && (() => {
                                    const totalDelta = history.slice(0, 10).reduce((sum, h, i) => {
                                        let delta = h?.treasury_delta ?? 0;
                                        if (delta === 0) {
                                            const curr = h?.treasury ?? h?.corporate_treasury ?? h?.global_state?.corporate_treasury ?? 0;
                                            const prev = i > 0 ? (history[i - 1]?.treasury ?? history[i - 1]?.corporate_treasury ?? history[i - 1]?.global_state?.corporate_treasury ?? curr) : curr;
                                            delta = curr - prev;
                                        }
                                        return sum + delta;
                                    }, 0);
                                    return (
                                        <div style={{
                                            marginTop: '0.6rem', padding: '0.5rem 0.75rem', borderRadius: '6px',
                                            background: 'rgba(99,102,241,0.06)',
                                            border: '1px solid rgba(99,102,241,0.15)',
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                        }}>
                                            <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                                                Net Treasury Impact (10 Rounds)
                                            </span>
                                            <span style={{
                                                fontSize: '0.82rem', fontWeight: 900,
                                                color: totalDelta >= 0 ? '#4ade80' : '#f87171',
                                                fontFamily: "'JetBrains Mono', monospace",
                                            }}>
                                                {totalDelta >= 0 ? '+' : ''}{currencySymbol()}{(Math.abs(totalDelta) / 1_000_000).toFixed(1)}M
                                            </span>
                                        </div>
                                    );
                                })()}
                            </section>
                        );
                    })()}

                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                        <button className={styles.closeBtn} onClick={proceedAction} style={{ background: theme.gradient }}>
                            {onProceed ? '⚖️ Proceed to Boardroom Showdown →' : 'Close Balanced Scorecard'}
                        </button>
                        {onLogout && (
                            <button className={styles.closeBtn} onClick={() => { if (window.confirm('Log out? Your progress is saved and you can return anytime.')) onLogout(); }} style={{ background: '#f8fafc', color: '#475569', border: '1px solid #cbd5e1' }}>
                                👋 Logout & Exit
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
