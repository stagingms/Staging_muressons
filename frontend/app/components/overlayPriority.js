/**
 * overlayPriority — the single documented z-index ladder for every
 * full-screen/floating layer on the player surface (Phase A).
 *
 * The values below are the EXACT numbers currently hard-coded across
 * page.js, ExecutiveCockpit.js and the overlay components — this module
 * names the contract; it does not change stacking. Phases D–E migrate the
 * remaining literals here one call site at a time, after which "who wins"
 * is answered by this file instead of by grep.
 *
 * Rule of thumb: gameplay chrome < guidance < takeovers < system.
 */
export const OVERLAY_PRIORITY = {
    /* gameplay chrome */
    TICKER: 7500,
    LEFT_RAIL_FLYOUT: 9000,
    TOOLTIP: 9500,
    DROPDOWN: 9999,

    /* guidance & modals */
    MODAL: 10000,
    MODAL_STACKED: 10001,
    FOCUS_OVERLAY: 12000,
    ONBOARDING_TOUR: 15000,

    /* takeovers (block the cockpit) */
    RESULTS_OVERLAY: 18000,
    CRISIS_INTERSTITIAL: 19000,
    CRISIS_INTERSTITIAL_TOP: 19100,
    SHOCKWAVE: 20000,
    BROADCAST_BANNER: 20500,
    CLIMATE_MODULE: 21000,

    /* system (nothing may cover these) */
    ERROR_BOUNDARY: 24000,
};

/**
 * OverlayLayer — thin positioning primitive for Phase D adoption.
 * Renders a fixed, full-viewport stacking context at a named priority.
 */
export function OverlayLayer({ priority, children, style = {}, ...rest }) {
    return (
        <div
            style={{ position: 'fixed', inset: 0, zIndex: priority, ...style }}
            {...rest}
        >
            {children}
        </div>
    );
}
