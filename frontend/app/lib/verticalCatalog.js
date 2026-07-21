/**
 * verticalCatalog.js
 * ─────────────────────────────────────────────────────────────────
 * Single source of truth for every industry vertical in the system.
 *
 * Contract:
 *  • slot      = one of the 4 seed BU slot IDs:
 *                pharma | electronics | consumer_goods | software
 *  • id        = the vertical identifier stored as `industry_vertical`
 *  • isDefault = true  → this vertical IS the native slot
 *                false → substitute: replaces the slot's default BU
 *  • desc      = shown as tooltip / help text in the UI
 *
 * Adding one entry here automatically propagates to:
 *   1. The Single-BU picker in CreateCohortModal (grouped by slot)
 *   2. The 4-BU Substitution tab in CreateCohortModal
 *   3. The facilitator profile vertical picker in FacilitatorManager
 *   4. The CohortSummaryTooltip label lookup
 *
 * Mirror the new entry in the backend VERTICAL_SLOT_MAP dict in
 * backend/router.py so the assigned_bu derivation stays in sync.
 */

export const VERTICAL_CATALOG = [
    // ── Pharma slot ──────────────────────────────────────────────────────────
    { id: 'pharma',          slot: 'pharma',         isDefault: true,  label: 'Pharma / Healthcare',       icon: '💊', desc: 'Pharmaceuticals, biotech and hospital networks. High R&D intensity, drug-safety liability, access-to-medicine pressure, HIPAA/GDPR obligations.' },
    { id: 'oil_gas',         slot: 'pharma',         isDefault: false, label: 'Oil & Gas',                 icon: '🛢️', desc: 'Upstream E&P, midstream pipelines, downstream refining. Extreme carbon intensity and stranded-asset risk.' },
    { id: 'chemical',        slot: 'pharma',         isDefault: false, label: 'Chemical',                  icon: '⚗️', desc: 'Specialty & bulk chemicals. High process-heat emissions, toxic discharge liability, REACH/TSCA compliance.' },
    { id: 'cosmetics',       slot: 'pharma',         isDefault: false, label: 'Cosmetics & Personal Care', icon: '💄', desc: 'Beauty and personal care. Ingredient sourcing controversy, microplastics liability, animal-testing regulation.' },
    { id: 'food_beverage',   slot: 'pharma',         isDefault: false, label: 'Food & Beverage',           icon: '🍽️', desc: 'Food processing & branded beverages. Extreme water intensity, deforestation-linked sourcing, food-safety recall risk.' },
    { id: 'power_utilities', slot: 'pharma',         isDefault: false, label: 'Power & Utilities',         icon: '⚡', desc: 'Electricity generation & distribution. Highest carbon intensity of all verticals, stranded-asset exposure, energy-transition capex.' },

    // ── Electronics slot ─────────────────────────────────────────────────────
    { id: 'electronics',     slot: 'electronics',    isDefault: true,  label: 'Electronics',               icon: '🔌', desc: 'Consumer electronics hardware. Supply-chain minerals risk, e-waste obligations, rapid product-cycle obsolescence.' },
    { id: 'semiconductor',   slot: 'electronics',    isDefault: false, label: 'Semiconductor',             icon: '💎', desc: 'Wafer fab & chip design. Extreme water/energy intensity, rare-mineral supply risk, geopolitical fab concentration.' },
    { id: 'medical_devices', slot: 'electronics',    isDefault: false, label: 'Medical Devices',           icon: '🩺', desc: 'Implantables, diagnostics & surgical equipment. Heavy FDA/CE burden, IP-intensive R&D, single-use plastics exposure.' },
    { id: 'automotive',      slot: 'electronics',    isDefault: false, label: 'Automotive',                icon: '🚗', desc: 'ICE & EV manufacturing. Scope 3 tailpipe dominance, battery mineral dependency, EV transition capex.' },
    { id: 'telecom',         slot: 'electronics',    isDefault: false, label: 'Telecom',                   icon: '📶', desc: 'Mobile & fixed-line networks. Spectrum licensing risk, e-waste obligations, tower energy intensity, data privacy.' },

    // ── Consumer Goods slot ──────────────────────────────────────────────────
    { id: 'consumer_goods',  slot: 'consumer_goods', isDefault: true,  label: 'Consumer Goods',            icon: '🛍️', desc: 'Branded mass-market consumer products. Packaging waste, consumer sentiment, sustainability labelling scrutiny.' },
    { id: 'retail_fmcg',     slot: 'consumer_goods', isDefault: false, label: 'Retail / FMCG',            icon: '🛒', desc: 'Fast-moving consumer goods. Packaging waste, plastic lifecycle, sustainable supply chain, consumer sentiment.' },
    { id: 'agriculture',     slot: 'consumer_goods', isDefault: false, label: 'Agriculture',               icon: '🌾', desc: 'Industrial farming & agri-tech. Extreme water dependency, biodiversity impact, land-use emissions.' },

    // ── Software slot ─────────────────────────────────────────────────────────
    { id: 'software',        slot: 'software',       isDefault: true,  label: 'Software / Technology',     icon: '💻', desc: 'Enterprise SaaS & platform businesses. AI governance, data-privacy risk, energy-hungry data centres, talent war.' },
    { id: 'technology',      slot: 'software',       isDefault: false, label: 'Technology',                icon: '🧠', desc: 'Cloud, AI/ML platforms & data centres. Governance sensitivity, energy growth trajectory, talent risk.' },
    { id: 'banking_financial_services', slot: 'software', isDefault: false, label: 'Banking & Financial Services', icon: '🏦', desc: 'Systemic risk, prudential regulation, ESG lending, financed emissions, digital banking disruption.' },
];

/**
 * Fast lookup: vertical id → slot id.
 * Used to derive assigned_bu (always a seed slot) from industry_vertical.
 * @type {Record<string, string>}
 */
export const VERTICAL_SLOT_MAP = Object.fromEntries(
    VERTICAL_CATALOG.map(v => [v.id, v.slot])
);

/**
 * The 4 canonical BU slot positions with display metadata.
 * Used to build grouped selects and the 4-BU substitution tab.
 */
export const SLOT_META = [
    { slot: 'pharma',         label: 'Pharma',        icon: '💊' },
    { slot: 'electronics',    label: 'Electronics',   icon: '🔌' },
    { slot: 'consumer_goods', label: 'Consumer Goods', icon: '🛍️' },
    { slot: 'software',       label: 'Software',      icon: '💻' },
];

/**
 * Resolve a vertical id to its human-readable label + icon.
 * Falls back gracefully for unknown ids (e.g. old sessions).
 * @param {string} verticalId
 * @returns {{ label: string, icon: string }}
 */
export function resolveVerticalMeta(verticalId) {
    if (!verticalId) return { label: '—', icon: '🏢' };
    const entry = VERTICAL_CATALOG.find(v => v.id === verticalId);
    if (entry) return { label: entry.label, icon: entry.icon };
    // Graceful fallback for unknown ids
    return {
        label: verticalId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        icon: '🏢',
    };
}
