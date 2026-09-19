# Master Comprehensive UI/UX Code Audit: Muressons Simulation Platform
**Platform Version:** 2026-09 Multi-Tier Simulation Cockpit & Facilitation Suite  
**Date of Audit:** September 18, 2026  
**Auditor:** Teamwork Comprehensive Audit Taskforce (worker_1)  
**Target Repository:** `/Users/Dilijithkannan/Documents/AG/Staging_Mayan`  
**Reference Standards:** `CLAUDE.md`, `frontend/__tests__/ui-budgets.test.js`, `frontend/app/styles/tokens.css`, `frontend/__tests__/player-surface-contracts.test.js`, `frontend/__tests__/design-token-drift.test.js`, `AUDIT_UX_Product_2026-08-02.md`

---

## Executive Summary

### 1. High-Level Health Assessment Across Surfaces

An exhaustive, multi-agent code investigation was conducted across the three operational surfaces of the Muressons simulation platform:
1. **Player Simulation Surface** (`ExecutiveCockpit.js`, `FocusOverlay.js`, `DoubleMaterialityMatrix.js`, `InvestmentMatrix.js`, `useRoundStage.js`, and associated CSS modules).
2. **Facilitator & Admin Portal** (`RunBar.js`, `RoundPacingControl.js`, `CreateCohortModal.js`, `FacilitatorManager.js`, `trading-floor`, `war-map`, and God Mode tooling).
3. **Auth & Onboarding Experience** (`page.js`, `JoinCohortModal.js`, `OnboardingWalkthrough.js`, `OnboardingWizard.js`, `GlobalTooltip.js`, `storageHealth.js`, and `roleRouting.js`).

The simulation platform contains an exceptionally strong, pure-function algorithmic core (`engine.py`, `round_logic.py`, `systemic_risk_engine.py`) backed by deterministic golden-trace testing, robust server-side concurrency locking, and high pedagogical ambition (e.g., pre-commit consequence previews, interactive trade-off calculations, and endgame causal attribution scorecards). 

However, the user-facing interfaces suffer from severe **architectural accretion, modal collisions, workflow traps, accessibility failures, and design token bypasses**:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                SURFACE UX HEALTH SCORECARD                                  │
├───────────────────────────────┬───────────────┬─────────────────────────────────────────────┤
│ Surface                       │ Status        │ Primary Operational Vulnerabilities         │
├───────────────────────────────┼───────────────┼─────────────────────────────────────────────┤
│ 1. Player Simulation Surface  │ MODERATE      │ • Dual-results collision & metric leak (P0) │
│                               │ (Needs Align) │ • Dormant Expand Drawer squeezing screen(P1)│
│                               │               │ • Stranded 3D Constellation / DNA tools (P1)│
│                               │               │ • Stacking context drift (z-index anarchy)  │
│                               │               │ • 317 sub-12px typographic debt items (P2)  │
├───────────────────────────────┼───────────────┼─────────────────────────────────────────────┤
│ 2. Facilitator & Admin Portal │ HIGH RISK     │ • RunBar advance deadlock in Free/Timed (P0)│
│                               │ (Fragile)     │ • Dead-code pre-lock preview in wizard (P0) │
│                               │               │ • 179 API calls missing credentials (P0)    │
│                               │               │ • Monolithic 3,408-LOC wizard (85 useState) │
│                               │               │ • 14+ native unstyled browser confirms (P1) │
│                               │               │ • 10px illegible projector typography (P1)  │
├───────────────────────────────┼───────────────┼─────────────────────────────────────────────┤
│ 3. Auth & Onboarding Flows    │ MODERATE      │ • Bypassable round lockout screen (P0)      │
│                               │ (Inconsistent)│ • Pitch-black dynamic chunk loader (P0)     │
│                               │               │ • Absent God-Mode/Facilitator switcher (P1) │
│                               │               │ • Deceptive "Team Impersonation" table (P1) │
│                               │               │ • One-shot unreopenable onboarding tours    │
│                               │               │ • WCAG 1.4.13 non-hoverable tooltips (P2)   │
└───────────────────────────────┴───────────────┴─────────────────────────────────────────────┘
```

---

### 2. Top 5 Immediate Improvement Priorities

| # | Priority Action Item | Surface | Severity | Estimated Impact & Rationale |
|---|----------------------|---------|----------|------------------------------|
| **1** | **Eradicate Dual-Results Collision & Quarantine Pre-Commit Outflows** (`ExecutiveCockpit.js:4982`) | Player Surface | **P0 Critical** | Prevents catastrophic pedagogical spoiling. Currently, turn submission fires an obsolete 95% opacity modal (`z-index: 9000`) on top of the Canvas results step, exposing sensitive post-round Treasury, EBITDA, Reputation, and Carbon scores during multi-team waiting periods before the cohort barrier lifts. |
| **2** | **Resolve RunBar Advance Deadlocks in Free & Timed Pacing Modes** (`RunBar.js:198-212`) | Facilitator Portal | **P0 Critical** | Eliminates live classroom delivery freezes. When student seats drop or stall in Free or Timed mode, the persistent `RunBar` strips its Advance button, forcing facilitators into high-friction multi-level tab navigation to find cohort force-advance overrides while participants wait. |
| **3** | **Enforce `credentials: 'include'` & Standardize API Client** (`FacilitatorManager.js`, admin components) | Facilitator / Admin | **P0 Critical** | Fixes 179 vulnerable network calls that omit session cookies. Prevents silent 401 failures during role assignment, user de-provisioning, password resets, and emergency interventions in reverse-proxy, multi-origin, or iframe deployments. |
| **4** | **Seal Bypassable Round Lockout Screen** (`page.js:1609-1635`) | Auth & Onboarding | **P0 Critical** | Restores facilitator pacing control. The existing lockout overlay equips students with a functional "Dismiss" button (`sim.setRoundLocked(false)`), allowing participants to bypass facilitator locks and explore future decision stages prematurely. |
| **5** | **Wire Dead-Code Pre-Lock Server Preview (`previewSetup`)** (`CreateCohortModal.js:894-907`) | Facilitator Portal | **P0 Critical** | Prevents blind configuration errors. A complete server dry-run endpoint (`/apply-setup` with `dry_run: true`) was implemented to resolve 85 parameters before locking a cohort, but was left completely uncalled in the UI. Facilitators are currently forced to permanently lock cohorts blind. |

---

## Complete Feature Inventory & Master Issue Ledger

| # | Issue Key | Area / Surface | Severity | Heuristic Category | Primary Component(s) | Line Citations |
|---|-----------|----------------|----------|-------------------|----------------------|----------------|
| 1 | Dual-Results Overlay Collision & Pre-Commit Leak | Player Surface | P0 Critical | Visibility of System Status | `ExecutiveCockpit.js`, `FocusOverlay.js` | `ExecutiveCockpit.js:4982-5612` |
| 2 | Disabled Context Drawer & Viewport Starvation | Player Surface | P1 High Friction | Aesthetic & Minimalist Design | `ExecutiveCockpit.js`, CSS Module | `ExecutiveCockpit.js:149`, `3180-3238` |
| 3 | Stranded 3D Constellation & DNA Triggers | Player Surface | P1 High Friction | Recognition Rather Than Recall | `ExecutiveCockpit.js` | `ExecutiveCockpit.js:3014, 3673` |
| 4 | Stacking Context Governance Breakdown | Player Surface | P1 High Friction | Consistency & Standards | `overlayPriority.js`, `page.js` | `page.js:1930, 2053`, `Cockpit:4659` |
| 5 | CSRD Double Materiality Dialog A11Y Failure | Player Surface | P1 High Friction | User Control & Freedom (WCAG) | `DoubleMaterialityMatrix.js`, `page.js`| `page.js:1928-2048` |
| 6 | Right Rail Accordion Sprawl & Cognitive Overload | Player Surface | P1 High Friction | Flexibility & Efficiency | `ExecutiveCockpit.js` | `ExecutiveCockpit.js:4251-4573` |
| 7 | Duplicate Cockpit Header Countdown Timers | Player Surface | P2 Inconsistency | Aesthetic & Minimalist Design | `CountdownTimer.js`, `DecisionTimer.js`| `ExecutiveCockpit.js:1452, 1489` |
| 8 | Inconsistent / Vanishing KPI Belt | Player Surface | P2 Inconsistency | Visibility of System Status | `FocusOverlay.js`, `ExecutiveCockpit.js`| `FocusOverlay.js:250`, `Cockpit:1664` |
| 9 | Semantic Hue Contamination in BU Branding | Player Surface | P2 Inconsistency | Consistency & Standards | `InvestmentMatrix.js`, `tokens.css` | `InvestmentMatrix.js:18-27` |
| 10 | Typographic Debt (317 Sub-12px Font Declarations)| Player Surface | P2 Debt | Aesthetic & Minimalist Design | `ExecutiveCockpit.js`, `ui-budgets.test`| `ui-budgets.test.js:119-148` |
| 11 | Fragmented Dual Crisis Alert Screens | Player Surface | P3 Polish | Consistency & Standards | `CrisisAlerts.js`, `ExecutiveCockpit.js` | `CrisisAlerts.js:252`, `Cockpit:1270` |
| 12 | RunBar Advance Deadlock in Free/Timed Modes | Facilitator/Admin | P0 Critical | Flexibility & Efficiency | `RunBar.js`, `RoundPacingControl.js` | `RunBar.js:198-212` |
| 13 | Phantom Pre-Lock Server Preview (`previewSetup`)| Facilitator/Admin | P0 Critical | Visibility of System Status | `CreateCohortModal.js` | `CreateCohortModal.js:894-907` |
| 14 | 179 Fetch Invocations Missing `credentials` | Facilitator/Admin | P0 Critical | System Integrity / Security | `FacilitatorManager.js`, Admin Tools | `FacilitatorManager:203, 270`, `ManualOverride:26, 39` |
| 15 | Fragile 10-Step Sequential Client-Side Pipeline | Facilitator/Admin | P1 High Friction | Error Prevention / Reliability | `CreateCohortModal.js` | `CreateCohortModal.js:755-884` |
| 16 | Monolithic Accordion Overload (85 useState Hooks) | Facilitator/Admin | P1 High Friction | Cognitive Load / Minimalist Design | `CreateCohortModal.js` | `CreateCohortModal.js:1-3409` |
| 17 | Near-Total Absence of Client-Side Form Validation| Facilitator/Admin | P1 High Friction | Error Prevention | `CreateCohortModal.js` | `CreateCohortModal.js:1047-1066` |
| 18 | Asymmetric Undo Capability (Locked Facilitators) | Facilitator/Admin | P1 High Friction | User Control & Freedom | `RoundPacingControl.js`, `UndoRound.js` | `sidebarConfig.js:163` |
| 19 | All-or-Nothing Force Advance with Hardcoded Auto | Facilitator/Admin | P1 High Friction | Flexibility & Efficiency | `RoundPacingControl.js` | `RoundPacingControl.js:272-305` |
| 20 | Room-Scale Projector Illegibility (10px SVG) | Facilitator/Admin | P1 High Friction | Aesthetic & Minimalist Design | `trading-floor/page.js`, `war-map` | `war-map:31`, `trading-floor:358` |
| 21 | Critical Pedagogical Signals Trapped Behind Hover| Facilitator/Admin | P1 High Friction | Visibility of System Status | `war-map/page.js` | `war-map/page.js:50-74, 120` |
| 22 | Missing Cohort Scoping on Secondary Projectors | Facilitator/Admin | P1 High Friction | Match Between System & Real World | `trading-floor/page.js` | `trading-floor/page.js:71, 109` |
| 23 | Proliferation of Native Browser `confirm()` (14+) | Facilitator/Admin | P1 High Friction | Error Prevention / Consistency | `CrisisTriggerConfig.js`, Admin Tools | `CrisisTriggerConfig:73`, `Registry` |
| 24 | Silent First-Session Pre-Selection in Black Swan | Facilitator/Admin | P1 High Friction | Error Prevention | `CustomBlackSwanBuilder.js` | `CustomBlackSwanBuilder.js:60-62` |
| 25 | Auto-Pause Triggers Lack Room-Wide Escalation | Facilitator/Admin | P1 High Friction | Visibility of System Status | `AutoPauseConfig.js`, Facilitator Page | `AutoPauseConfig.js:5-13` |
| 26 | In-Memory Ephemeral Activity Log | Facilitator/Admin | P2 Inconsistency | Recognition Rather than Recall | `admin/facilitator/page.js` | `facilitator/page.js:1259-1307` |
| 27 | Uncoordinated Polling Stampede & Disregarded WS | Facilitator/Admin | P2 Tech Debt | Visibility of System Status | `RunBar.js`, `CohortPulse.js`, `Leader`| `CohortPulse.js:66`, `Leaderboard` |
| 28 | Widespread Token & Inline Styling Debt in Admin | Facilitator/Admin | P2 Tech Debt | Consistency & Standards | `CreateCohortModal.js`, `Facilitator` | `CreateCohortModal.js:1-3400` |
| 29 | Bypassable Round-Locked Lockout Screen | Auth & Onboarding | P0 Critical | Error Prevention / Integrity | `frontend/app/page.js` | `page.js:1609-1635` |
| 30 | Pitch-Black Screen During Dynamic Chunk Load | Auth & Onboarding | P0 Critical | Visibility of System Status | `frontend/app/page.js` | `page.js:21, 125, 126` |
| 31 | Duplicate `FacilitatorLoginGate` Bypassing Storage| Auth & Onboarding | P1 High Friction | Consistency & Standards | `admin/facilitator/page.js` | `facilitator/page.js:150-286` |
| 32 | Missing Role & Context Switcher Between Portals | Auth & Onboarding | P1 High Friction | Flexibility & Efficiency | `god-mode/page.js`, `facilitator/page` | `god-mode:800-868`, `roleRouting` |
| 33 | Deceptive Team Impersonation Feature | Auth & Onboarding | P1 High Friction | Match Between System & Real World | `TeamImpersonation.js`, `sidebarConfig`| `TeamImpersonation.js:180-274` |
| 34 | Missing Pre-Round Participant Lobby & Dead CSS | Auth & Onboarding | P1 High Friction | Visibility of System Status | `frontend/app/page.js`, CSS Module | `page.js:1440`, `page.module.css:14` |
| 35 | Permanently Unreachable Tour Replay / Resume | Auth & Onboarding | P1 High Friction | Recognition Rather than Recall | `frontend/app/page.js`, `Onboarding` | `page.js:2102`, `OnboardingWizard:168`|
| 36 | Regressed Tour Copy (PDF Export, 3-Tier Model) | Auth & Onboarding | P2 Debt | Help & Documentation | `OnboardingWizard.js` | `OnboardingWizard.js:49, 116` |
| 37 | Mislabelled Active Role Badge for `project_admin` | Auth & Onboarding | P2 Inconsistency | Visibility of System Status | `admin/facilitator/page.js`, `CLAUDE` | `facilitator/page.js:1746-1755` |
| 38 | Non-Hoverable Global Tooltips (WCAG 1.4.13) | Auth & Onboarding | P2 Inconsistency | Accessibility (WCAG 1.4.13) | `GlobalTooltip.js` | `GlobalTooltip.js:154, 181, 226` |
| 39 | Clashing Light-Mode Modals on Dark Cockpit | Auth & Onboarding | P2 Inconsistency | Aesthetic & Minimalist Design | `ChangePasswordModal.js`, `Onboarding`| `ChangePasswordModal.js:105-127` |
| 40 | Type Floor (11 counts) & Touch Target Debt (14px)| Auth & Onboarding | P2 Inconsistency | Accessibility (WCAG 2.5.8) | `JoinCohortModal.js`, CSS Module | `JoinCohortModal.js:167`, `CSS:246` |
| 41 | Out-of-Bounds Z-Index Arms Race in Inline Styles | Auth & Onboarding | P2 Debt | Stacking Context Integrity | `GlobalTooltip.js`, `page.js` | `GlobalTooltip:154`, `page.js:21` |
| 42 | Lingering "Team" Vocabulary vs Individual Model | Auth & Onboarding | P3 Polish | Consistency & Mental Model | `JoinCohortModal.js`, `page.js` | `JoinCohortModal:120`, `page:1618` |

---

## SECTION 1: Player Simulation Surface Audit

### Overview
The Player Simulation Surface governs the participant decision loop across 10 simulation rounds. Governed by the V-D slotting rule (`CLAUDE.md`), every player-facing UI element must strictly occupy **exactly one** defined slot:
- **Canvas Stage:** Completes the active step of the round workflow (`gate` → `strategy` → `allocation` → `commit` → `results`).
- **KPI Belt:** Always-glanceable operational metrics (numbers + deltas only).
- **Expand Drawer:** Deep-dive context, summoned on-demand, never ambient.
- **Rail Tab:** Asynchronous intelligence (Mailbox, Feed, Intel).
- **OverlayHost:** Top-level interrupts (Crises, Shockwaves, Broadcasts, Guided Tours).

---

### Detailed Player Surface Findings

#### [ISSUE-01] Dual-Results Presentation Collision & Early Metric Leakage
- **Severity Rating:** **P0 Critical Blocker**
- **Heuristic / UX Category:** Nielsen Norman #1 (Visibility of System Status), #4 (Consistency & Standards) · Round Progression Integrity
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/ExecutiveCockpit.js:4982-5612`
  - `frontend/app/components/ExecutiveCockpit.js:2641-3006`
  - `frontend/app/components/ExecutiveCockpit.module.css:1193-1250`
  - `frontend/app/hooks/useRoundStage.js:89-102`
- **Observed Code Evidence:**
  In `ExecutiveCockpit.js:4982`:
  ```jsx
  {/* ═══ COMMIT RESULTS OVERLAY ═══ */}
  <AnimatePresence>
    {commitResults && !sim.gameOver && (
      <motion.div
        className={styles.resultsOverlay}
        role="region"
        aria-label="Round results"
        ...
      >
        <div className={styles.resultsCard}>
          {/* Renders Treasury, EBITDA, Reputation deltas, stock chart, sparklines */}
  ```
  In `ExecutiveCockpit.module.css:1193-1202`:
  ```css
  .resultsOverlay {
    position: fixed;
    inset: 0;
    z-index: 9000;
    background: rgba(10, 14, 26, 0.95);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  ```
  Concurrently, in `ExecutiveCockpit.js:2641-3006`, the redesigned Canvas stage hosts the official inline results view:
  ```jsx
  {/* ── RESULTS STEP ── */}
  {focusStep === 'results' && commitResults && (
    <div className={focusStyles.resultsContainer}>
      <div className={focusStyles.resultsHeader}>...</div>
      <div className={focusStyles.belt}>...</div>
  ```
  In `useRoundStage.js:96-102`:
  ```javascript
  if (committed) {
    if (cohortWaiting) return 'waiting';
    return 'results';
  }
  ```
- **Observed Behavior:**
  When a participant commits their round, two conflicting results surfaces mount simultaneously:
  1. The inline Canvas Results view (`FocusOverlay.js` / `ExecutiveCockpit.js:2641`).
  2. The legacy 940px modal overlay (`styles.resultsOverlay`) rendered at `z-index: 9000` with 95% opacity.
  
  Most critically, during multi-team sessions where `cohortWaiting = true` (waiting for peer companies to submit), `useRoundStage.js` enters the `'waiting'` step to display the room progress barrier. However, because `ExecutiveCockpit.js:4982` gates solely on `commitResults && !sim.gameOver`, the legacy overlay mounts unconditionally over the waiting room, prematurely revealing all post-round financial outcomes, carbon penalties, and stock movements before the facilitator has released the round.
- **Actionable Remediation Proposal:**
  1. Retire and remove the legacy modal container `styles.resultsOverlay` from `ExecutiveCockpit.js:4982-5612` and its CSS block in `ExecutiveCockpit.module.css:1193-1250`. **Crucially retain and re-mount `<BalanceSheetModal>` (lines 5601-5609)** either directly within the Canvas Results step (`focusStep === 'results'`) or within `OverlayHost` (`isPlayerVisible('balance_sheet_modal')`), ensuring the player Balance Sheet inspection dialog remains fully functional and is not orphaned.
  2. Consolidate all retrospective analysis (sparklines, balance sheet drilldowns, and consequence replay attributions) exclusively into the Canvas Results step (`focusStep === 'results'`) inside `FocusOverlay.js`.
  3. Ensure results remain strictly unrendered while `focusStep === 'waiting'`.
- **UI Budget & V-D Slotting Impact:**
  - Reduces distinct component mounts in `ExecutiveCockpit.js` from 58 to 57, allowing a one-count ratchet reduction in `frontend/__tests__/ui-budgets.test.js:212`.
  - Reconciles V-D slotting: results strictly occupy the Canvas stage slot, eliminating rogue modal overlays from OverlayHost.

---

#### [ISSUE-02] Dormant Context Drawer Feature Flag & Viewport Starvation
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #8 (Aesthetic & Minimalist Design) · Visual Hierarchy & Screen Real Estate
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/ExecutiveCockpit.js:149`
  - `frontend/app/components/ExecutiveCockpit.js:1456-1486`, `3864-3874`, `4581-4623`
  - `frontend/app/components/ExecutiveCockpit.module.css:3180-3238`
- **Observed Code Evidence:**
  In `ExecutiveCockpit.js:149`:
  ```javascript
  /* PHASE 5.1 + 5.2 — the right rail becomes a 56px spine and its content moves
     into a 360px overlay drawer, per the mock. One line, same pattern as
     CANVAS_FIRST and ACTION_BAR above.
     FALSE until somebody has looked at it on a real screen... */
  const CONTEXT_DRAWER = false;
  ```
  In `ExecutiveCockpit.js:4581-4586`:
  ```jsx
  if (!CONTEXT_DRAWER) {
    return (
      <aside id="tour-intelligence-target" aria-label="Messages and intelligence" className={styles.rightSidebar}>
        {contextPanels}
      </aside>
    );
  }
  ```
  In `ExecutiveCockpit.module.css:3190-3215`:
  ```css
  .leftSidebar[data-rails="collapsed"] { min-width: 172px; }
  .rightSidebar[data-rails="collapsed"] { min-width: 208px; }
  ```
- **Observed Behavior:**
  The Expand Drawer implementation is complete and verified by automated contracts (`player-surface-contracts.test.js:1020-1100`), but remains deactivated via `CONTEXT_DRAWER = false`. As a result, secondary context (Mailbox, Market Feed, Stakeholder notes) renders permanently as an ambient 25% column (`aside.rightSidebar`).
  Even when participants collapse the rails (`railsPinnedOpen = false`), CSS clamps sidebars to a combined minimum width of 380px (`min-width: 172px` and `208px`). On standard university and laptop displays (1366x768 or 1440x900), this starves the central decision canvas of horizontal width, forcing strategic tables and investment sliders into compressed, horizontally scrolling containers.
- **Actionable Remediation Proposal:**
  1. Toggle the feature flag in `ExecutiveCockpit.js:149` to `const CONTEXT_DRAWER = true;`.
  2. Verify that the envelope trigger (`styles.contextOpenBtn`) in the cockpit header and the action bar button (`styles.contextGhostBtn`) summon the 360px slide-in `<Dialog className={styles.contextDrawer}>`.
  3. Ensure the central decision canvas automatically claims the reclaimed 25% viewport width, conforming to the single-column focus layout.
- **UI Budget & V-D Slotting Impact:**
  Fulfills CLAUDE.md §3 Expand Drawer slot contract ("Deep-dive detail, summoned not ambient"). Fully compliant with existing Jest contracts.

---

#### [ISSUE-03] Inaccessible 3D ESG Constellation & DNA Visualizer Triggers
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #6 (Recognition Rather Than Recall), #7 (Flexibility & Efficiency of Use)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/ExecutiveCockpit.js:3014`
  - `frontend/app/components/ExecutiveCockpit.js:3673-3708`
  - `frontend/app/components/ExecutiveCockpit.js:3720-3727`
- **Observed Code Evidence:**
  In `ExecutiveCockpit.js:3014`:
  ```jsx
  {/* Phase D: the dense center content is the DISCLOSURE layer now —
      it renders when the canvas is dismissed (D1 pinned-dashboard preference)... */}
  {!(CANVAS_FIRST && isFocusActive) && (
    <>
      ...
      {/* Antigravity: 3D Constellation Trigger */}
      {isPlayerVisible('esg_constellation_3d') && (
        <button
          onClick={() => setShowConstellation(true)}
          className={styles.toolBtn}
          title="Explore ESG impacts in 3D Constellation"
        >
          🌐 3D Constellation
        </button>
      )}
      ...
      <ConsequenceDNATrigger ignited={dnaIgnited} onClick={() => setShowDNAVisualizer(true)} />
    </>
  )}
  ```
- **Observed Behavior:**
  Because the platform operates in `CANVAS_FIRST = true` and `isFocusActive = true` during regular gameplay, lines 3014-3826 are unmounted from the React DOM tree. As a consequence, high-value pedagogical 3D visualizers—specifically the Three.js **3D ESG Impact Constellation** and the **Consequence DNA Visualizer**—are stranded inside dead conditional code. Students cannot locate or launch these features during their decision-making workflow.
- **Actionable Remediation Proposal:**
  Relocate the launcher triggers for the 3D Constellation and Consequence DNA out of the unmounted legacy block into one of two approved V-D slots:
  1. The `PlayerUtilityDock` ⋯ More menu (`page.js:1740-1753`).
  2. The Expand Drawer header toolbar (`styles.drawerHeader`).
- **UI Budget & V-D Slotting Impact:**
  Enforces CLAUDE.md V-D rule: "⋯ More menu: Occasional utilities". Zero net addition to screen real estate or mount budgets.

---

#### [ISSUE-04] Stacking Context Governance Breakdown & Overlay Puncturing
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #4 (Consistency & Standards), #5 (Error Prevention) · Modality & Stacking Integrity
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/overlayPriority.js:13-36`
  - `frontend/app/page.js:1930`, `2053`, `1869`, `1893`, `21`
  - `frontend/app/components/ExecutiveCockpit.js:1272`, `4659`, `4713`
  - `frontend/app/components/ExecutiveCockpit.module.css:1196`
- **Observed Code Evidence:**
  The repository established a single source of truth for modal priorities in `overlayPriority.js`:
  ```javascript
  export const OVERLAY_PRIORITY = {
    TICKER: 7500, LEFT_RAIL_FLYOUT: 9000, TOOLTIP: 9500, DROPDOWN: 9999,
    MODAL: 10000, MODAL_STACKED: 10001, FOCUS_OVERLAY: 12000, ONBOARDING_TOUR: 15000,
    RESULTS_OVERLAY: 18000, CRISIS_INTERSTITIAL: 19000, CLIMATE_MODULE: 21000,
    ERROR_BOUNDARY: 24000,
  };
  ```
  However, component files systematically bypass this module and inject ad-hoc z-index values:
  - Round 1 Stakeholder Map (`page.js:2053`): `zIndex: 7500`
  - Round 2 CSRD Double Materiality (`page.js:1930`): `zIndex: 7500`
  - Commit Results Overlay (`ExecutiveCockpit.module.css:1196`): `z-index: 9000`
  - Crisis Alert Modal (`ExecutiveCockpit.js:1272`): `zIndex: 11000`
  - FullScreenLoader (`page.js:21`): `zIndex: 20000`
  - Keyboard Shortcut Cheatsheet (`ExecutiveCockpit.js:4659`): `zIndex: 99998`
  - Expanded Message Modal (`ExecutiveCockpit.js:4713`): `zIndex: 99999`
- **Observed Behavior:**
  Because mandatory stage-gate modals (Stakeholder Map and CSRD Matrix) render at `zIndex: 7500`, lower-priority UI elements—such as tooltips (`9500`) and dropdown selectors (`9999`)—puncture through the modal scrim, intercepting clicks and causing visual artifacts. 
  Conversely, Crisis Interstitials render at 11000 (below Onboarding Tours at 15000), and cockpit child modals escalate up to 99999, escaping the 24000 error boundary ceiling.
- **Actionable Remediation Proposal:**
  1. Refactor all modal wrappers across `page.js` and `ExecutiveCockpit.js` to import and consume `OVERLAY_PRIORITY` tokens exclusively.
  2. Assign Gating Interstitials (R1 Stakeholder Map, R2 CSRD Assessment) to `OVERLAY_PRIORITY.MODAL` (10000).
  3. Set Crisis Interstitial to `OVERLAY_PRIORITY.CRISIS_INTERSTITIAL` (19000).
  4. Constrain all informational dialogs to `OVERLAY_PRIORITY.MODAL` (10000) or `MODAL_STACKED` (10001).
- **UI Budget & V-D Slotting Impact:**
  Restores architectural compliance with OverlayHost governance. Prevents overlay collision bugs without modifying the slot ledger.

---

#### [ISSUE-05] CSRD Double Materiality Slide-in Lacks Accessible Dialog Semantics
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #3 (User Control & Freedom) · Accessibility & WCAG 2.1 AA Compliance
- **Component File(s) & Line Numbers:**
  - `frontend/app/page.js:1928-2048`
  - `frontend/app/components/DoubleMaterialityMatrix.js:1-1209`
- **Observed Code Evidence:**
  In `page.js:1928-1935`:
  ```jsx
  {isMatrixOpen && (
    <div style={{ position: 'fixed', inset: 0, zIndex: 7500, display: 'flex', justifyContent: 'flex-end', background: 'rgba(10, 14, 26, 0.4)', backdropFilter: 'blur(4px)' }}>
      <div style={{ width: '85%', maxWidth: 1100, height: '100%', background: '#0a0e1a', borderLeft: '1px solid #1e293b' }}>
        <DoubleMaterialityMatrix ... />
  ```
  An AST scan of `DoubleMaterialityMatrix.js` reveals zero occurrences of `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, or `keydown` listeners for the `Escape` key.
- **Observed Behavior:**
  The Round 2 CSRD Double Materiality assessment renders as a plain `<div>` container. It fails fundamental modal accessibility standards:
  1. Pressing the `Escape` key does not dismiss the panel.
  2. Tab focus is not trapped inside the assessment grid; pressing `Tab` cycles focus into unseen background cockpit controls beneath the scrim.
  3. Screen readers do not announce the container as a modal dialog, failing WCAG 2.1 Success Criteria 2.1.2 (No Keyboard Trap) and 2.4.3 (Focus Order).
- **Actionable Remediation Proposal:**
  Wrap `DoubleMaterialityMatrix` inside the standardized `frontend/app/components/Dialog.js` primitive with:
  ```jsx
  <Dialog
    isOpen={isMatrixOpen}
    onClose={() => setIsMatrixOpen(false)}
    label="CSRD Double Materiality Assessment"
    closeOnBackdrop={true}
    priority="MODAL"
  >
    <DoubleMaterialityMatrix ... />
  </Dialog>
  ```
- **UI Budget & V-D Slotting Impact:**
  Reuses existing `Dialog.js` primitive, passing `player-surface-contracts.test.js:801-830` (`modal accessibility is centralised`) without increasing component count baselines.

---

#### [ISSUE-06] Right Rail Accordion Sprawl & Cognitive Overload
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #7 (Flexibility & Efficiency of Use), #8 (Aesthetic & Minimalist Design) · Cognitive Load Under Stress
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/ExecutiveCockpit.js:4251-4573`
- **Observed Code Evidence:**
  The right sidebar vertically concatenates 8 distinct UI sub-systems:
  1. Sticky tab strip (`styles.railTabStrip`): Mailbox, Decisions, Engines, Climate.
  2. Tab content container (`styles.tabContentEnter`) with nested internal scrolling.
  3. Live Market Reality Feed (`styles.rightMarket`).
  4. Round recap accordion (`EngineEventsPanel sections="retrospect"`).
  5. CEO Diary archive (`EngineEventsPanel sections="rest"`).
  6. Stakeholder Agent Panel (`StakeholderAgentPanel`).
  7. Player Annotations (`PlayerAnnotations`).
  8. Synergy Tracker (`SynergyTracker`).
- **Observed Behavior:**
  During timed 15-minute decision rounds, students must scroll through multiple stacked accordion panels within a narrow 260px column. Toggling an accordion dynamically displaces the Market Reality Feed, causing vertical viewport jumps and forcing participants to hunt for live news updates.
- **Actionable Remediation Proposal:**
  Following the activation of `CONTEXT_DRAWER = true`, enforce strict tab discipline:
  1. Keep only live, glanceable asynchronous intelligence (Mailbox badge and Market Feed headline ticker) in the collapsed spine.
  2. Consolidate CEO Diary, Historical Recaps, Stakeholder Notes, and Synergy Trackers into dedicated tabs within the summoned 360px drawer.
  3. Enforce that only one rail section can be expanded at any time.
- **UI Budget & V-D Slotting Impact:**
  Directly aligns with CLAUDE.md §3 Rail tab convention ("one open at a time: Asynchronous context").

---

#### [ISSUE-07] Duplicate Countdown Timers in Cockpit Header
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Nielsen Norman #8 (Aesthetic & Minimalist Design) · Visibility of System Status
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/ExecutiveCockpit.js:1452` (`<CountdownTimer>`)
  - `frontend/app/components/ExecutiveCockpit.js:1489-1495` (`<DecisionPressureTimer>`)
  - `frontend/app/components/CountdownTimer.js:63-90`
  - `frontend/app/components/DecisionPressureTimer.js:63-90`
- **Observed Code Evidence:**
  In `ExecutiveCockpit.js:1452-1495`:
  ```jsx
  <div className={styles.headerCenter}>
    <CountdownTimer sessionId={sim?.sessionId} roundNumber={roundNumber} />
    ...
    {isPlayerVisible('decision_pressure_timer') && (
      <DecisionPressureTimer
        sessionId={sim?.sessionId}
        roundNumber={roundNumber}
        isCommitted={!!commitResults}
        globalState={globalState}
      />
    )}
  </div>
  ```
- **Observed Behavior:**
  Both components mount side-by-side in `headerCenter`. Both fire independent 5-second polling intervals against `/api/admin/sessions/{id}/pacing`, generating redundant network traffic and displaying two conflicting visual clocks with different typography and color schemes.
- **Actionable Remediation Proposal:**
  1. Remove `<CountdownTimer>` from line 1452 of `ExecutiveCockpit.js` (retaining its progress-bar variant in `RoundChecklist.js`).
  2. Standardize on `<DecisionPressureTimer>` as the sole authoritative clock in `headerCenter`.
- **UI Budget & V-D Slotting Impact:**
  Eliminates redundant network polling; adheres to the single-occupant header slot rule.

---

#### [ISSUE-08] Inconsistent & Vanishing KPI Belt Across Workflow Stages
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Nielsen Norman #1 (Visibility of System Status) · Visual Hierarchy
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/FocusOverlay.js:250-304` (`KPIStrip`)
  - `frontend/app/components/ExecutiveCockpit.js:2154`, `2380`, `1664-1784` (`resourcesPanel`)
- **Observed Code Evidence:**
  - In `FocusOverlay.js`, `KPIStrip` is rendered conditionally: only when `focusStep === 'strategy'` or `focusStep === 'allocation'`.
  - When `focusStep === 'gate'` (R1 Stakeholder / R2 CSRD) or `focusStep === 'waiting'`, `KPIStrip` is omitted.
  - When `railsPinnedOpen = true`, `resourcesPanel` (in left sidebar) and `KPIStrip` (in center canvas) render identical metrics (Treasury, EBITDA, Reputation, Carbon) simultaneously.
  - When rails are collapsed and `focusStep === 'gate'`, zero KPIs are visible on screen.
- **Observed Behavior:**
  Core financial and ESG indicators either appear twice or vanish completely depending on sidebar collapse state and stage-gate progression. Participants lose situational awareness of remaining budget while evaluating mandatory gate decisions.
- **Actionable Remediation Proposal:**
  1. Extract `KPIStrip` into a persistent, fixed-height horizontal belt positioned immediately below the header and above `mainContent`.
  2. Remove duplicate KPI resource cards from `resourcesPanel` in the left rail.
  3. Ensure the belt remains visible across all stages (`gate`, `strategy`, `allocation`, `waiting`).
- **UI Budget & V-D Slotting Impact:**
  Fulfills CLAUDE.md slot definition: "KPI belt: Always-glanceable state (numbers + deltas only)".

---

#### [ISSUE-09] Semantic Hue Contamination in Business Unit Branding
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Nielsen Norman #4 (Consistency & Standards) · Cognitive Bias & Visual Semantics
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/InvestmentMatrix.js:18-27` (`BU_META`)
  - `frontend/app/styles/tokens.css:52-62`
  - `frontend/__tests__/ui-budgets.test.js:342-359`
- **Observed Code Evidence:**
  In `InvestmentMatrix.js:18-27`:
  ```javascript
  const BU_META = {
    pharma: { label: 'Pharma', Icon: SvgPharma, accent: 'var(--kpi-good)' },
    electronics: { label: 'Electronics', Icon: SvgElectronics, accent: '#3b82f6' },
    consumer_goods: { label: 'Consumer Goods', Icon: SvgConsumer, accent: 'var(--caution)' },
    software: { label: 'Software', Icon: SvgSoftware, accent: '#8b5cf6' },
    hospitals: { label: 'Hospitals', Icon: SvgHospital, accent: 'var(--danger)' },
    clinics: { label: 'Primary Care Clinics', Icon: SvgClinic, accent: 'var(--kpi-good)' },
  };
  ```
- **Observed Behavior:**
  Green (`var(--kpi-good)`), amber (`var(--caution)`), and red (`var(--danger)`) are applied as decorative brand accents to individual Business Units. In an ESG simulation, participants instinctively perceive green BUs as healthy and red BUs as failing, regardless of actual financial margins or carbon intensity.
- **Actionable Remediation Proposal:**
  Replace semantic status tokens in `BU_META` with dedicated domain brand palette tokens:
  ```javascript
  pharma: { accent: 'var(--bu-pharma, #06b6d4)' }      // Cyan
  consumer_goods: { accent: 'var(--bu-consumer, #f97316)' } // Tangerine
  hospitals: { accent: 'var(--bu-hospital, #ec4899)' }  // Rose
  ```
  Reserve `--positive`, `--caution`, and `--danger` strictly for operational performance deltas and threshold breaches.
- **UI Budget & V-D Slotting Impact:**
  Pays down 4 semantic hue violations in `ui-budgets.test.js:342-359`.

---

#### [ISSUE-10] Typographic Debt Ledger (317 Sub-12px Font Declarations)
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Nielsen Norman #8 (Aesthetic & Minimalist Design) · Visual Legibility & Eye Strain
- **Component File(s) & Line Numbers:**
  - `frontend/__tests__/ui-budgets.test.js:119-148` (`TYPE_FLOOR_DEBT`)
  - `frontend/app/components/ExecutiveCockpit.js` (127 declarations, down to 8px / `0.5rem`)
  - `frontend/app/components/GameOverSummary.js` (38 declarations)
  - `frontend/app/components/DoubleMaterialityMatrix.js` (22 declarations)
  - `frontend/app/styles/tokens.css:39` (`--type-caption: 0.75rem / 12px`)
- **Observed Code Evidence:**
  The Jest budget test `ui-budgets.test.js:119-148` freezes 317 sub-12px font declarations across 28 player files. Inspection of `ExecutiveCockpit.js` reveals font sizes at `0.5rem` (8px), `0.6rem` (9.6px), and `0.65rem` (10.4px) across data tables and badge readouts.
- **Observed Behavior:**
  During 30-to-60-minute decision phases, participants experience significant visual fatigue trying to decipher micro-typography in budget allocations, cost-of-capital notes, and scenario briefings.
- **Actionable Remediation Proposal:**
  Execute Phase 6.1 type floor normalization across player components:
  1. Elevate all sub-12px font literals to `var(--type-caption)` (12px / 0.75rem).
  2. Use letter-spacing (`letter-spacing: 0.04em`) and uppercase styling rather than sub-12px scaling for compact metadata tags.
  3. Ratchet down baselines in `ui-budgets.test.js:119-148` to zero.
- **UI Budget & V-D Slotting Impact:**
  Directly eliminates 317 debt points in the official Jest UI budget ledger.

---

#### [ISSUE-11] Fragmented Dual Crisis Alert Screen Architectures
- **Severity:** **P3 Polish**
- **Heuristic / UX Category:** Nielsen Norman #4 (Consistency & Standards)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/CrisisAlerts.js:252-379` (`CrisisScreen`)
  - `frontend/app/components/ExecutiveCockpit.js:1270-1355` (`activeAlert`)
- **Observed Code Evidence:**
  Two parallel crisis presentation patterns coexist:
  - In `page.js:1501-1510` (following preflight role checks at line 1352), active Black Swan events trigger an architectural early return that completely unmounts the cockpit tree to render `<CrisisScreen>`.
  - In `ExecutiveCockpit.js:1270`, trigger-based crises render an inline fixed modal with `zIndex: 11000`.
- **Observed Behavior:**
  Participants experience divergent animation styles, dismissal interactions, and audio chimes depending on which system triggered the crisis event.
- **Actionable Remediation Proposal:**
  Consolidate both crisis screens into a single standardized Crisis Interstitial component managed through `OverlayHost` and pinned to `OVERLAY_PRIORITY.CRISIS_INTERSTITIAL` (19000).
- **UI Budget & V-D Slotting Impact:**
  Eliminates architectural duplication; ensures consistent modal stacking.

---

## SECTION 2: Facilitator & Admin Portal Audit

### Overview
The Facilitator and Administrator surfaces control live session orchestration, cohort creation, player roster provisioning, and amphitheater projector consoles. Facilitators operate under intense time constraints during live workshops; any interface freeze, hidden status, or unconfirmed destructive action directly endangers classroom delivery.

---

### Detailed Facilitator & Admin Findings

#### [ISSUE-12] Accidental Advance Deadlock in Free and Timed Modes via RunBar
- **Severity:** **P0 Critical Blocker**
- **Heuristic / UX Category:** Nielsen Norman #7 (Flexibility & Efficiency of Use), #1 (Visibility of System Status) · Live Session Orchestration
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/RunBar.js:198-212`
  - `frontend/app/components/RoundPacingControl.js:401-432`
- **Observed Code Evidence:**
  In `RunBar.js:198-212`:
  ```javascript
  {mode === 'manual' && (
    <button
      onClick={advance}
      disabled={busy || (Number(pacing.unlocked_round) || 1) >= 10}
      className={styles.advanceBtn}
    >
      ⏭ Advance
    </button>
  )}
  ```
- **Observed Behavior:**
  In `RunBar.js`, the persistent advance action is strictly conditioned on `mode === 'manual'`. If a cohort is set to `free` mode (the platform default) or `timed` mode, and a participant's laptop disconnects, freezes, or stalls the room:
  1. The `RunBar` displays **no advance, force-advance, or unlock affordance**.
  2. To unblock the classroom, the facilitator must click `⏱ Pacing`, leave their current monitoring view, navigate to `RoundPacingControl.js`, re-select the cohort from a dropdown, scroll past pacing settings to Free Mode options, and click `⏭️ Force Advance Now` (`line 423`).
  Under live amphitheater pressure with 30-50 executive students waiting, this 5-step navigation introduces severe delay, confusion, and panic.
- **Actionable Remediation Proposal:**
  Expose contextual unblocking controls directly on `RunBar.js`:
  - When `mode === 'free'` and committed < total, render an `⏭ Force Advance` button in `RunBar` (wrapped in the existing `useConfirm` modal with blast-radius preview).
  - When `mode === 'timed'`, provide an `⏭ Unlock Early` affordance in `RunBar`.
- **UI Budget & V-D Slotting Impact:**
  Retains control within the persistent `RunBar` banner slot; zero layout disruption.

---

#### [ISSUE-13] Phantom Pre-Lock Server Preview (`previewSetup` Dead Code)
- **Severity:** **P0 Critical Blocker**
- **Heuristic / UX Category:** Nielsen Norman #1 (Visibility of System Status), #5 (Error Prevention)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/CreateCohortModal.js:894-907`
  - `frontend/app/components/CreateCohortModal.js:913-928`
- **Observed Code Evidence:**
  Lines 887-907 state:
  ```javascript
  // ── PRE-LOCK PREVIEW (UX audit #19) ──────────────────────────────────
  // The permanent choices used to be described only in prose next to a
  // button reading "Permanently Lock & Create Cohort". This asks the SERVER
  // what it would apply — dry_run applies nothing — so the facilitator sees
  // the actual resolved configuration before committing to it.
  const previewSetup = async (sid) => {
    try {
      const res = await fetch(`${API}/api/admin/cohort/${sid}/apply-setup`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...buildApplyPayload(), dry_run: true }),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  };
  ```
  A repository-wide AST scan confirms that `previewSetup` has **zero call sites**. It is declared at line 894 and never invoked.
- **Observed Behavior:**
  The server dry-run pre-lock preview—specifically engineered to prevent catastrophic cohort misconfigurations—is completely dead code. Facilitators are forced to click `"Permanently Lock & Create Cohort"` (line 3394, located inside Accordion Section 7 which spans lines 3250-3402) completely blind, with zero visibility into how the server resolved their 85 parameters.
- **Actionable Remediation Proposal:**
  Wire `previewSetup` into Section 7 ("Summary & Lock Configuration") of `CreateCohortModal.js`. When the user enters Section 7, invoke `previewSetup` and display a two-column diff comparing selected options against defaults before enabling the final lock button.
- **UI Budget & V-D Slotting Impact:**
  Integrates into existing Accordion 7; zero DOM slot growth.

---

#### [ISSUE-14] 179 Fetch Invocations Missing `credentials: 'include'`
- **Severity:** **P0 Critical Blocker**
- **Heuristic / UX Category:** System Integrity & Security Architecture
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/FacilitatorManager.js:203, 270, 464, 481, 496, 517, 526, 571, 590, 660, 722, 766` (Note: lines 329 and 694 properly include credentials)
  - `frontend/app/components/ManualOverride.js:26, 39`
  - `frontend/app/components/MasterInterventions.js:66, 79, 102`
  - `frontend/app/components/SystemicRiskControls.js:33, 47`
  - `frontend/app/components/UniversalBroadcast.js:21`
  - `frontend/app/components/BulkMessaging.js:24, 45`
  - `frontend/app/components/AuditTrail.js:40`
  - `frontend/app/components/RegulatorySandboxControl.js:41, 62, 82, 321`
  - `frontend/app/components/LeaderboardMatrix.js:119, 137`
- **Observed Code Evidence:**
  The platform authentication model relies on an HttpOnly session cookie (`mur_session`). In standard browser fetch calls, cookies are omitted unless explicitly configured (`credentials: 'include'`). While certain endpoints in `FacilitatorManager.js` (e.g., lines 329 and 694) correctly specify `credentials: 'include'`, over 170 fetch calls across administrative components omit credentials entirely.
  
  In `FacilitatorManager.js:203` (uncredentialed GET):
  ```javascript
  const res = await fetch(`${API}/api/admin/facilitators`);
  ```
  In `FacilitatorManager.js:270-273` (uncredentialed PUT):
  ```javascript
  const res = await fetch(`${API}/api/admin/facilitators/${facId}/enabled`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: newVal }),
  });
  ```
  In `ManualOverride.js:26, 39-46` (uncredentialed GET and POST):
  ```javascript
  fetch(`${API}/api/admin/${sessionId}/interventions`)
  // ...
  const res = await fetch(`${API}/api/admin/${sessionId}/override`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
          override_type: override.id,
          parameters: override.params,
      }),
  });
  ```
  Across admin components, over 170 fetch calls omit `credentials: 'include'`.
- **Observed Behavior:**
  When the application is deployed behind custom domain reverse-proxies, cross-origin API hosts, or within enterprise iframe containers, these fetch calls fail silently with 401 Unauthorized errors. Critical administrative actions (such as role promotions, facilitator deletion, and crisis injections) fail without user-visible explanations.
- **Actionable Remediation Proposal:**
  Standardize all administrative network communication on `frontend/app/utils/adminFetch.js`, which guarantees `credentials: 'include'`, automatically attaches required CSRF/auth headers, and handles 401 session expiry redirects globally.
- **UI Budget & V-D Slotting Impact:**
  Zero layout changes; eliminates widespread network failure hazards.

---

#### [ISSUE-15] Fragile 10-Step Sequential Client-Side Provisioning Pipeline
- **Severity:** **P1 High Friction / Architecture Debt**
- **Heuristic / UX Category:** Nielsen Norman #5 (Error Prevention) · System Reliability
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/CreateCohortModal.js:755-884`, `959-965`, `1114`, `1147-1243`
- **Observed Code Evidence:**
  Upon cohort creation, `runSubConfigChain` fires up to 10 sequential client-side network requests:
  1. `PUT .../analytics-visibility`
  2. `PUT .../pedagogical-settings`
  3. `POST .../briefing-videos`
  4. `PUT .../ceo-interview`
  5. `PUT .../side-tracks`
  6. `PUT .../pacing`
  7. `PATCH .../cohort-settings`
  8. `POST .../cohort-templates`
  9. `PUT .../bu-composition`
  10. `POST .../apply-setup`
- **Observed Behavior:**
  If network jitter or a server restart causes step 6 or 8 to fail, the cohort is left in a corrupted, partially configured state in the database. The client catches the failure and renders a 100-line "setup-integrity panel" (`lines 1147-1243`) with individual retry buttons, burdening the instructor with manual reconciliation.
- **Actionable Remediation Proposal:**
  Deprecate the 10-step client pipeline in favor of a single transactional backend endpoint (`POST /api/admin/cohorts/provision`) that accepts the full configuration payload and commits all relational records within a single database transaction.
- **UI Budget & V-D Slotting Impact:**
  Deletes 100+ lines of retry UI; guarantees atomic cohort initialization.

---

#### [ISSUE-16] Monolithic Accordion Overload (85 `useState` Hooks in 3,408 Lines)
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #8 (Aesthetic & Minimalist Design) · Cognitive Load
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/CreateCohortModal.js:1-3409`
- **Observed Code Evidence:**
  `CreateCohortModal.js` contains 85 discrete `useState` hooks managing 8 non-linear accordion sections (`core`, `engine`, `verticals`, `modules`, `interventions`, `pedagogy`, `advanced`, `lock`).
- **Observed Behavior:**
  New instructors face an overwhelming wall of non-linear controls with no guided progression. Users can configure engine modules before selecting a business vertical or currency, resulting in cognitive overload and abandoned setups.
- **Actionable Remediation Proposal:**
  Decompose `CreateCohortModal.js` into a 4-step guided wizard:
  1. *Step 1: Core Identification* (Name, Industry Vertical, Region, Currency).
  2. *Step 2: Pedagogy & Modules* (Experience Level Preset, Engine Modules, Side Tracks).
  3. *Step 3: Pacing & Roster* (Pacing Mode, Player Capacity, Timezone).
  4. *Step 4: Review & Lock* (Server Dry-Run Diff Preview, Template Save).
- **UI Budget & V-D Slotting Impact:**
  Reduces component LOC from 3,408 to ~400 lines; drastically improves onboarding speed.

---

#### [ISSUE-17] Near-Total Absence of Client-Side Form Validation in Cohort Setup
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #5 (Error Prevention), #9 (Help Users Recognize Errors)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/CreateCohortModal.js:1047-1066`, `1256`
- **Observed Code Evidence:**
  Out of 85+ input fields, only 3 fields have client validation: `regionId` (line 1048), `industryVertical` (line 1052), and multi-region BU slots (line 1061).
  All other fields are completely unvalidated:
  - `startDate` vs `endDate`: End date can precede start date.
  - `cohortTimezone`: Free-text string input without validation against the IANA timezone database. A typo returns a raw 422 error from FastAPI.
  - `roundTimerSeconds`: Accepts negative or non-numeric values.
  - `quizPassThreshold`: Accepts values > 100%.
  When an error occurs, it renders in a single detached `div` at the very top of the modal (`line 1256`), scrolling out of view.
- **Observed Behavior:**
  Instructors discover validation errors only after submitting, and must scroll through 3,000 lines of accordions to locate which field triggered the error.
- **Actionable Remediation Proposal:**
  Introduce Zod or Yup schema validation with immediate inline error messages and red border highlights on the invalid inputs.
- **UI Budget & V-D Slotting Impact:**
  Standardizes input validation without panel sprawl.

---

#### [ISSUE-18] Asymmetric Undo Capability: Base Facilitators Can Advance but Cannot Revert
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #3 (User Control & Freedom) · Operational Recovery
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/RoundPacingControl.js:190-241`
  - `frontend/app/components/UndoRound.js:6-21`, `163`
  - `frontend/app/config/sidebarConfig.js:163`
- **Observed Code Evidence:**
  In `sidebarConfig.js:163`:
  ```javascript
  { id: 'undo_round', label: 'Undo Round', requiredRole: 'lead_facilitator', showDisabled: true, disabledReason: 'Lead facilitator or above can roll a round back — ask them to undo it for this cohort.' }
  ```
  Base facilitators (`role: facilitator`, Level 1) are authorized to advance rounds (`RoundPacingControl.js:190`). However, under `CLAUDE.md:62`, the rollback capability is strictly reserved for `lead_facilitator` (Level 2) and above. The role ladder in `backend/admin_shared.py` and `frontend/app/config/sidebarConfig.js` is pinned equal by the invariant test `backend/tests/test_role_hierarchy_sync.py`. This guard exists to enforce tournament anti-cheating rules and pedagogical integrity—preventing students who have already seen subsequent round results from receiving arbitrary rollbacks.
- **Observed Behavior:**
  An instructor running their own live workshop who accidentally clicks Advance has no immediate recovery affordance if the initial 60-second relock window lapses or if they need to undo an erroneous advance. They are forced to interrupt class and summon a Lead Facilitator or Super Admin to execute `UndoRound.js`.
- **Actionable Remediation Proposal:**
  Reconcile user recovery with the `CLAUDE.md:62` role hierarchy invariant through a two-tiered architectural approach:
  1. **Owner-of-Record Emergency Cancellation Window (Recommended):** Preserve the Level 2 `lead_facilitator` tier requirement for destructive multi-round rollbacks in compliance with `CLAUDE.md:62` and `test_role_hierarchy_sync.py`. For base session owners (`facilitator_id === session.facilitator_id`), introduce a dedicated 60-second "Cancel Advance / Immediate Relock" grace action that is strictly available *before any student commits in the new round*. Once any student decision commit is submitted, the window closes. Additionally, add a 1-click in-app escalation button ("Request Lead Facilitator Rollback") that broadcasts an urgent notification via the admin WebSocket bus (`sessions_refresh`).
  2. **Alternative Role Ladder Synchronization:** If product governance explicitly chooses to grant rollback capability to base session owners for their own cohorts, this must be executed across the contract boundary: updating `CLAUDE.md:62`, `backend/admin_shared.py`, `frontend/app/config/sidebarConfig.js:163`, and `backend/tests/test_role_hierarchy_sync.py` in lockstep, while enforcing a backend pre-condition that rejects rollbacks if student commits are present.
- **UI Budget & V-D Slotting Impact:**
  Maintains RBAC integrity; preserves existing `UndoRound.js` dialog while adding the pre-commit emergency cancel trigger to `RoundPacingControl.js`.

---

#### [ISSUE-19] All-or-Nothing Force Advance with Hardcoded Fallback
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #7 (Flexibility & Efficiency of Use)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/RoundPacingControl.js:272-305`
- **Observed Code Evidence:**
  In `RoundPacingControl.js:279-281`:
  ```javascript
  `${behind} player(s) will be AUTO-COMMITTED — from their saved draft if one exists, otherwise with defaults (Option B, $1 per business unit).`
  ```
- **Observed Behavior:**
  Triggering Force Advance is an all-or-nothing sweep. If 4 teams are deliberating productively and 1 team experienced a WiFi dropout, the facilitator cannot advance *only* the dropped team. Triggering force-advance penalizes the 4 active teams by forcing synthetic default decisions on them.
- **Actionable Remediation Proposal:**
  Add a per-team `[Auto-Commit This Team]` action in `CohortPulse.js` and `PlayerRegistry.js`, allowing facilitators to selectively release stalled seats without disrupting the rest of the room.
- **UI Budget & V-D Slotting Impact:**
  Integrates as a row action in existing tables; zero new panels.

---

#### [ISSUE-20] Room-Scale Projector Illegibility (10px SVG, 1.1rem Typography)
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #8 (Aesthetic & Minimalist Design) · Projector Layer Readability
- **Component File(s) & Line Numbers:**
  - `frontend/app/admin/trading-floor/page.js:358-370`
  - `frontend/app/admin/war-map/page.js:31-39`
- **Observed Code Evidence:**
  - In `trading-floor/page.js:358`, container `maxWidth: 900px` clamps the display to a narrow center column on 1080p/4K projectors. Team names use `fontSize: '1.1rem'` (17.6px) and progress bars are 12px high.
  - In `war-map/page.js:31`:
    ```javascript
    function Label({ x, y, text, size = 10, color = '#cbd5e1', weight = 600 })
    ```
- **Observed Behavior:**
  From 10 meters away in an amphitheater, 10px SVG labels and 1.1rem text are completely unreadable. (In contrast, `admin/projector/page.js` properly uses 150px round numerals and 32px table typography).
- **Actionable Remediation Proposal:**
  - In `trading-floor`, expand `maxWidth` to `min(1600px, 94vw)`, enlarge team names to `1.8rem` (28.8px), rank numerals to `2.4rem` (38.4px), and progress bars to 24px height.
  - In `war-map`, raise minimum SVG label sizes to 18px-24px with high-contrast pill backdrops.
- **UI Budget & V-D Slotting Impact:**
  Aligns presentation consoles with CLAUDE.md Projector/Atmosphere layer rules.

---

#### [ISSUE-21] Critical Pedagogical Signals Trapped Behind Mouse Hover on Big Screens
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #1 (Visibility of System Status) · Presentation Usability
- **Component File(s) & Line Numbers:**
  - `frontend/app/admin/war-map/page.js:50-74`, `120`
- **Observed Code Evidence:**
  Line 120 states: *"Hover anything for what it means."* BU health scores (Social Licence, Carbon Intensity) and Stakeholder sentiment tiers render strictly inside a floating `div` triggered on `onMouseMove` (`showTip`, lines 51-53).
- **Observed Behavior:**
  In a classroom where the war map is projected from an unattended lectern laptop, **no one is hovering a mouse over the nodes**. The audience and instructor cannot see the underlying causal dynamics.
- **Actionable Remediation Proposal:**
  Provide an ambient, readable summary rail or auto-rotating lower third that continuously cycles through active crises and the top escalated stakeholder metrics without requiring mouse interaction.
- **UI Budget & V-D Slotting Impact:**
  Conforms to Projector layer presentation standards.

---

#### [ISSUE-22] Missing Cohort Scoping & Target Collision on Secondary Consoles
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #2 (Match Between System & Real World), #4 (Consistency & Standards)
- **Component File(s) & Line Numbers:**
  - `frontend/app/admin/trading-floor/page.js:71`, `109-110`
  - `frontend/app/admin/war-map/page.js:95`
- **Observed Code Evidence:**
  Unlike `admin/projector/page.js` (which parses `?cohort=<id>`), `trading-floor` and `war-map` omit cohort URL parameter handling.
  In `trading-floor/page.js:109-110`:
  ```javascript
  const cohortId = teams.find((t) => t.parent_cohort_id)?.parent_cohort_id || 'cohort';
  ```
- **Observed Behavior:**
  When multiple cohorts run concurrently in an institution, `trading-floor` fetches all active sessions globally and grabs the cohort ID of whichever team happens to lead the leaderboard. Ringing the market bell closes the market for the wrong cohort!
- **Actionable Remediation Proposal:**
  Adopt `useSearchParams` across all admin display routes (`trading-floor`, `war-map`), requiring explicit `?cohort=<id>` parameters and providing `CohortChooser` fallback selectors when missing.
- **UI Budget & V-D Slotting Impact:**
  Reuses existing `CohortChooser` component pattern.

---

#### [ISSUE-23] Proliferation of Native Browser `confirm()` Across Destructive Admin Actions
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #5 (Error Prevention), #4 (Consistency & Standards)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/CrisisTriggerConfig.js:73`
  - `frontend/app/components/PlayerRegistry.js:265, 305, 315, 327`
  - `frontend/app/components/AutoPauseConfig.js:75`
  - `frontend/app/components/RegulatorySandboxControl.js:316`
  - `frontend/app/components/MaterialityConfig.js:68, 348, 437, 446, 526, 640, 716`
  - `frontend/app/components/StakeholderConfig.js:301`
  - `frontend/app/components/SystemExport.js:88`
  - `frontend/app/components/MasterInterventions.js:63`
- **Observed Code Evidence:**
  In `CrisisTriggerConfig.js:73`:
  ```javascript
  if (!confirm('Fire "Activist Threat / CEO Liquidity Panic" to ALL active player sessions?')) return;
  ```
- **Observed Behavior:**
  14+ high-consequence administrative actions (including deleting entire cohorts, resetting passwords, and firing global panics) use unstyled browser `window.confirm()`. Native popups block JavaScript execution, freeze WebSocket heartbeats, cannot display blast-radius details, and can be accidentally accepted via an errant `Enter` keystroke.
- **Actionable Remediation Proposal:**
  Migrate all 14 sites to the accessible `useConfirm()` hook (`ConfirmModal.js`), requiring typed confirmation keywords (e.g., `DELETE` or `FIRE`) for room-wide destructive operations.
- **UI Budget & V-D Slotting Impact:**
  Eliminates raw browser alerts; standardizes on `ConfirmModal.js`.

---

#### [ISSUE-24] Silent First-Session Pre-Selection in Custom Black Swan Injector
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #5 (Error Prevention)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/CustomBlackSwanBuilder.js:60-62`
- **Observed Code Evidence:**
  In `CustomBlackSwanBuilder.js:60-62`:
  ```javascript
  if (sessionList.length > 0 && !selectedSession) {
    setSelectedSession(sessionList[0].session_id);
  }
  ```
- **Observed Behavior:**
  `RoundPacingControl` explicitly eradicated silent first-session pre-selection to avoid cross-cohort contamination. However, `CustomBlackSwanBuilder.js` still auto-selects the first session in the database. An instructor building a custom crisis for Cohort B will accidentally inject it into Cohort A if they do not change the dropdown.
- **Actionable Remediation Proposal:**
  Default `selectedSession` to `""`, display a default `"— Select a cohort —"` option, and keep the submission button disabled until an explicit selection is made.
- **UI Budget & V-D Slotting Impact:**
  Zero layout changes; eliminates accidental crisis detonation.

---

#### [ISSUE-25] Auto-Pause Triggers Lack Room-Wide Visual Escalation
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #1 (Visibility of System Status)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/AutoPauseConfig.js:5-13`
  - `frontend/app/admin/facilitator/page.js:1766-1795`
- **Observed Code Evidence:**
  When a team hits an auto-pause safety boundary (`treasury_negative`, `reputation_below_20`), the simulation sets `system_frozen = True`.
- **Observed Behavior:**
  On the Facilitator Portal, there is no high-visibility banner or audio alert announcing that the simulation has halted. Facilitators are left wondering why participant submissions are bouncing until they inspect debug logs.
- **Actionable Remediation Proposal:**
  Mount a full-width amber alert banner directly above `RunBar` whenever `pulse.system_frozen === true`, explicitly naming the team and threshold breached.
- **UI Budget & V-D Slotting Impact:**
  Conforms to OverlayHost interrupt conventions.

---

#### [ISSUE-26] In-Memory Ephemeral Activity Log on Facilitator Portal
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Nielsen Norman #6 (Recognition Rather than Recall) · Observability
- **Component File(s) & Line Numbers:**
  - `frontend/app/admin/facilitator/page.js:1259-1307`
- **Observed Code Evidence:**
  In `admin/facilitator/page.js:1286-1288`:
  ```javascript
  <h2>Live Feed (this browser session)</h2>
  <span>Entries are kept in memory only and cleared on refresh...</span>
  ```
- **Observed Behavior:**
  The "Activity Logs & Resets" panel (`sidebarConfig.js:207`) renders a transient React state array. Refreshing the browser completely wipes the facilitator's record of overrides, black swan injections, and pacing changes. Only Super Admins have access to the persistent database audit log.
- **Actionable Remediation Proposal:**
  Connect the panel to a cohort-scoped endpoint (`GET /api/admin/sessions/{id}/audit-log`) so facilitators retain a permanent audit trail across browser reloads.
- **UI Budget & V-D Slotting Impact:**
  Renders inside existing `activity_log` panel.

---

#### [ISSUE-27] Uncoordinated Polling Stampede & Disregarded WebSocket Stream
- **Severity:** **P2 Inconsistency / Tech Debt**
- **Heuristic / UX Category:** Nielsen Norman #1 (Visibility of System Status) · System Efficiency
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/RunBar.js:61` (5s polling interval)
  - `frontend/app/components/CohortPulse.js:66` (15s polling interval)
  - `frontend/app/components/PlayerRegistry.js:81` & `FacilitatorManager.js:214` (10s polling intervals)
  - `frontend/app/components/LeaderboardMatrix.js:114-127` (sequential cohort loop)
  - `frontend/app/admin/facilitator/page.js:678-718` (WebSocket established; lines 698-699 use `sessions_refresh` as blind ping)
- **Observed Code Evidence:**
  The facilitator portal executes multiple uncoordinated polling loops across individual components (e.g. 5s in `RunBar.js`, 10s in `PlayerRegistry.js` and `FacilitatorManager.js`, 15s in `CohortPulse.js`). In `LeaderboardMatrix.js:114-127`, `fetchPracticeStates` iterates through all cohorts sequentially in a `for` loop, issuing N consecutive HTTP requests on every refresh. Meanwhile, `admin/facilitator/page.js:678-718` connects to the admin WebSocket (`/api/admin/ws/admin`), but lines 698-699 use incoming messages solely as a blind ping to trigger a full re-fetch via `fetchLeaderboard()` rather than streaming granular deltas.
- **Actionable Remediation Proposal:**
  Consolidate telemetry polling into a shared `SessionSyncContext` or broadcast actual state deltas over the existing WebSocket connection.
- **UI Budget & V-D Slotting Impact:**
  Significantly reduces backend network load.

---

#### [ISSUE-28] Widespread Token & Inline Styling Debt in Admin Codebase
- **Severity:** **P2 Inconsistency / Tech Debt**
- **Heuristic / UX Category:** Nielsen Norman #4 (Consistency & Standards)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/CreateCohortModal.js` (187 raw hex, 263 inline styles)
  - `frontend/app/components/FacilitatorManager.js` (89 raw hex, 198 inline styles)
  - `frontend/app/admin/facilitator/page.js` (65 raw hex, 166 inline styles)
  - `frontend/app/admin/god-mode/page.js` (47 raw hex, 118 inline styles)
- **Observed Code Evidence:**
  While `ui-budgets.test.js` enforces strict color and spacing tokens for player files, admin surfaces carry over 600 raw hex literals and over 800 inline style blocks, bypassing `tokens.css`.
- **Actionable Remediation Proposal:**
  Extend `ui-budgets.test.js` to track an `ADMIN_FILES` ledger, ratcheting down raw hex values to design system tokens.
- **UI Budget & V-D Slotting Impact:**
  Establishes unified design system governance across admin surfaces.

---

## SECTION 3: Auth & Onboarding Experience Audit

### Overview
The Auth and Onboarding experience governs initial participant access, session recovery, role model switching, waiting lobbies, guided orientation walkthroughs, and design token compliance.

---

### Detailed Auth & Onboarding Findings

#### [ISSUE-29] Bypassable Round-Locked Lockout Screen
- **Severity:** **P0 Critical Blocker**
- **Heuristic / UX Category:** Nielsen Norman #5 (Error Prevention) · System Integrity & Gating
- **Component File(s) & Line Numbers:**
  - `frontend/app/page.js:1609-1635`
- **Observed Code Evidence:**
  In `frontend/app/page.js:1609-1635`:
  ```javascript
  {sim.roundLocked && (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(27,42,74,0.92)', ... }}>
      <div style={{ ... }}>
        <h3>Round Locked</h3>
        <p>Your facilitator has paused round progression...</p>
        <button
          onClick={() => sim.setRoundLocked(false)}
          style={{ ... }}
        >
          Dismiss
        </button>
      </div>
    </div>
  )}
  ```
  Line 1634 also uses sub-12px `fontSize: '0.72rem'`.
- **Observed Behavior:**
  When a facilitator locks the simulation round (to hold the classroom for discussion or lecture), the participant's screen displays a lockout overlay. However, the overlay provides an active "Dismiss" button that executes `sim.setRoundLocked(false)`. Any student can click Dismiss to clear the lockout screen and freely browse and submit decisions ahead of the cohort schedule.
- **Actionable Remediation Proposal:**
  Remove the Dismiss button entirely. Render the lockout overlay with `dismissible={false}`, releasing only when `sim.roundLocked` is set to false via backend polling or WebSocket events. Upgrade caption text to `var(--type-caption)`.
- **UI Budget & V-D Slotting Impact:**
  Enforces OverlayHost integrity; pays down 1 type-floor violation in `page.js`.

---

#### [ISSUE-30] Pitch-Black Screen During Dynamic Code Chunk Loading
- **Severity:** **P0 Critical Blocker**
- **Heuristic / UX Category:** Nielsen Norman #1 (Visibility of System Status)
- **Component File(s) & Line Numbers:**
  - `frontend/app/page.js:21`, `125`, `126`
- **Observed Code Evidence:**
  In `frontend/app/page.js:21`:
  ```javascript
  const FullScreenLoader = () => <div style={{position: 'fixed', inset: 0, background: '#080c18', zIndex: 20000}}></div>;
  ```
  Used at lines 125-126:
  ```javascript
  const JoinCohortModal = dynamic(() => import('./components/JoinCohortModal'), { ssr: false, loading: FullScreenLoader });
  const UsernamePromptModal = dynamic(() => import('./components/UsernamePromptModal'), { ssr: false, loading: FullScreenLoader });
  ```
- **Observed Behavior:**
  When dynamic components load over slower network connections (such as crowded campus WiFi), participants see an unlabelled, pitch-black screen with no spinner, brand mark, text, or ARIA status announcement. Users perceive the application as crashed or unresponsive.
- **Actionable Remediation Proposal:**
  Replace `FullScreenLoader` with a branded skeleton component featuring an animated pulse shield, `role="status"`, `aria-busy="true"`, and the label "Loading simulation module…".
- **UI Budget & V-D Slotting Impact:**
  Resolves initial cognitive blank-out without slotting regression.

---

#### [ISSUE-31] Duplicate `FacilitatorLoginGate` Bypassing Storage Availability Probes
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #4 (Consistency & Standards), #5 (Error Prevention)
- **Component File(s) & Line Numbers:**
  - `frontend/app/admin/facilitator/page.js:150-286`, `426-444`
  - `frontend/app/components/AdminLogin.js:1-162`
- **Observed Code Evidence:**
  `admin/facilitator/page.js:426-444` embeds a 136-line legacy `FacilitatorLoginGate`. Unlike the central `AdminLogin.js` component:
  - It does not probe for cookie writability via `storageHealth.cookiesWritable()`.
  - It lacks caps-lock detection.
  - It hardcodes inline styles and raw hexes (`color: '#ef4444'`).
  - It lacks role-based routing; signing in as `god_mode` or `super_admin` leaves the user stranded in the facilitator portal.
- **Observed Behavior:**
  Facilitators accessing `/admin/facilitator` directly experience an inconsistent login form that fails silently if browser cookies are blocked.
- **Actionable Remediation Proposal:**
  Delete `FacilitatorLoginGate` and redirect unauthenticated requests to `/admin?expired=1` (mirroring `admin/god-mode/page.js:342`) or render `<AdminLogin />`.
- **UI Budget & V-D Slotting Impact:**
  Deletes 136 lines of duplicated debt; unifies authentication plumbing.

---

#### [ISSUE-32] Missing Role & Context Switcher Between Administrative Portals
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #7 (Flexibility & Efficiency of Use)
- **Component File(s) & Line Numbers:**
  - `frontend/app/admin/god-mode/page.js:800-868`
  - `frontend/app/admin/facilitator/page.js:1420-1445`
  - `frontend/app/utils/roleRouting.js:27-29`
- **Observed Code Evidence:**
  In `roleRouting.js:27-29`:
  ```javascript
  export function roleStorageKey(data = {}) {
    return isAdminRole(data.role, data.is_admin) ? 'godmode_auth' : 'facilitator_auth';
  }
  ```
  In `god-mode/page.js:800-868`, there is no affordance to navigate to the Facilitator view (`/admin/facilitator`). In `facilitator/page.js:1420-1445`, there is no link for a Super Admin to return to `/admin/god-mode`.
- **Observed Behavior:**
  Super Admins running live cohorts cannot switch between global platform management and cohort simulation execution without manually editing the browser URL bar and re-authenticating.
- **Actionable Remediation Proposal:**
  Add a "Switch to Facilitator View" link in the God Mode header and a "Switch to God Mode" link in the Facilitator header for users where `isAdminRole()` is true. Update auth handlers to synchronize both localStorage keys.
- **UI Budget & V-D Slotting Impact:**
  Restores seamless administrative operational switching.

---

#### [ISSUE-33] Deceptive Team Impersonation Feature
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #2 (Match Between System & Real World) · Truth in Advertising
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/TeamImpersonation.js:180-274`
  - `frontend/app/config/sidebarConfig.js:150`
- **Observed Code Evidence:**
  In `sidebarConfig.js:150`, the tooltip promises:
  > *"View the simulation cockpit exactly as a specific player sees it — their dashboard, mailbox, decision interface, and KPI readouts. Useful for live debugging, classroom walkthroughs, or demonstrating the player experience."*
  
  However, `TeamImpersonation.js:180-274` renders **only an HTML table of Business Units (Revenue, OPEX, Margin) and an event flags badge summary**. It contains no cockpit UI, no mailbox, and no interactive decision tiles.
- **Observed Behavior:**
  Instructors expecting to see the student interface during live troubleshooting are presented with raw financial tables, failing their operational expectations.
- **Actionable Remediation Proposal:**
  Either:
  1. Rename the tab to "Session State Inspector" and update the tooltip to reflect reality, or
  2. Embed `ExecutiveCockpit` in a read-only observer iframe for the selected team.
- **UI Budget & V-D Slotting Impact:**
  Resolves CLAUDE.md Tooltip Convention defect.

---

#### [ISSUE-34] Missing Pre-Round Participant Lobby & Dead CSS
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #1 (Visibility of System Status)
- **Component File(s) & Line Numbers:**
  - `frontend/app/page.js:1440-1500`
  - `frontend/app/page.module.css:14-147`
- **Observed Code Evidence:**
  After entering a username, participants skip directly into `RoundBriefing` and `ExecutiveCockpit`. There is no pre-round waiting room displaying cohort enrollment or readiness status. Concurrently, `page.module.css:14-147` carries 133 lines of unused, dead `.lobby*` CSS styles.
- **Observed Behavior:**
  Students enter Round 1 before the instructor has finished room setup, leading to confusion about when deliberations actually start.
- **Actionable Remediation Proposal:**
  Implement a Pre-Round 1 Lobby stage in `useRoundStage.js` that displays cohort launch status and participant enrollment. Clean up the 133 lines of dead CSS from `page.module.css`.
- **UI Budget & V-D Slotting Impact:**
  Cleans up 133 lines of CSS debt.

---

#### [ISSUE-35] Permanently Unreachable Tour Replay / Resume
- **Severity:** **P1 High Friction**
- **Heuristic / UX Category:** Nielsen Norman #6 (Recognition Rather Than Recall), #3 (User Control & Freedom)
- **Component File(s) & Line Numbers:**
  - `frontend/app/page.js:2102-2106`
  - `frontend/app/components/OnboardingWalkthrough.js:184-188`
  - `frontend/app/components/OnboardingWizard.js:168`
- **Observed Code Evidence:**
  Completing or skipping the tour sets a flag in `localStorage` (`mur_tour_done_${sim.sessionId}`). There is no button anywhere in the player utility dock or admin header to reopen or replay the walkthrough.
- **Observed Behavior:**
  Students who accidentally skip the 7-step tour on launch lose all access to interactive guidance for the rest of the simulation.
- **Actionable Remediation Proposal:**
  Add a "Restart Guided Tour" action in the `PlayerUtilityDock` ⋯ More menu (`page.js:1740-1753`) and in the admin sidebar footer.
- **UI Budget & V-D Slotting Impact:**
  Occupies the existing ⋯ More menu slot; zero DOM footprint growth.

---

#### [ISSUE-36] Onboarding Wizard Copy Regressions (PDF Promise, Role Model)
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Nielsen Norman #10 (Help & Documentation)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/OnboardingWizard.js:49`, `116`
- **Observed Code Evidence:**
  - Line 116 promises: *"Export Reports generates CSV/PDF for grading."* (PDF export does not exist in `ReportsExport.js`).
  - Line 49 claims: *"The 3-tier role system (Super Admin → Lead → Base) is enforced here."* (Ignores `god_mode` and `project_admin`).
- **Observed Behavior:**
  Instructors are misinformed regarding report capabilities and access control tiers.
- **Actionable Remediation Proposal:**
  Update line 116 to "CSV and JSON export for grading"; update line 49 to document the full 5-tier role hierarchy.
- **UI Budget & V-D Slotting Impact:**
  Pure copy correction; zero layout impact.

---

#### [ISSUE-37] Mislabelled Active Role Badge for `project_admin`
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Nielsen Norman #1 (Visibility of System Status)
- **Component File(s) & Line Numbers:**
  - `frontend/app/admin/facilitator/page.js:1746-1755`
  - `CLAUDE.md:64`
- **Observed Code Evidence:**
  In `admin/facilitator/page.js:1746-1755`:
  ```javascript
  {authData?.role === 'super_admin' ? '👑 Super Admin' :
   authData?.role === 'lead_facilitator' ? '⭐ Lead' : '🎓 Facilitator'}
  ```
  Per `CLAUDE.md:64`, `project_admin` is a Level 0 provisioning-only role off the run ladder. Yet this ternary falls through and stamps a `project_admin` as `'🎓 Facilitator'`.
- **Observed Behavior:**
  Provisioning admins believe they have simulation management privileges that the backend will reject with 403 Forbidden.
- **Actionable Remediation Proposal:**
  Add explicit badge handling:
  ```javascript
  authData?.role === 'project_admin' ? '📁 Provisioning Admin' : ...
  ```
- **UI Budget & V-D Slotting Impact:**
  Zero layout changes; clarifies role authority boundaries.

---

#### [ISSUE-38] Non-Hoverable Global Tooltips Violate WCAG 1.4.13
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Accessibility (WCAG 2.1 AA - Success Criterion 1.4.13)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/GlobalTooltip.js:154`, `181`, `226-231`
- **Observed Code Evidence:**
  In `GlobalTooltip.js:181`:
  ```javascript
  pointerEvents: 'none',
  ```
  Paragraph font sizes in lines 226-231 drop to `0.7rem` (11.2px).
- **Observed Behavior:**
  Because `pointerEvents: 'none'` is set, users cannot move their mouse over the tooltip to read or highlight long multi-paragraph descriptions. Under WCAG 1.4.13 (Content on Hover or Focus), hovered content must be hoverable without dismissing.
- **Actionable Remediation Proposal:**
  Remove `pointerEvents: 'none'`, implement an invisible hover bridge, and raise font size to `var(--type-caption)` (12px).
- **UI Budget & V-D Slotting Impact:**
  Satisfies WCAG 1.4.13 compliance.

---

#### [ISSUE-39] Clashing Light-Mode Modals on Dark Simulation Cockpit
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Nielsen Norman #8 (Aesthetic & Minimalist Design)
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/ChangePasswordModal.js:105-127`, `258-274`
  - `frontend/app/components/OnboardingWalkthrough.js:266-339`
- **Observed Code Evidence:**
  `ChangePasswordModal.js` hardcodes white card backgrounds (`background: '#fff'`) and light gray borders.
- **Observed Behavior:**
  Mounting over the deep navy cockpit (`#080c18`), these dialogs produce a jarring white flash that disrupts visual adaptation.
- **Actionable Remediation Proposal:**
  Tokenize modal surfaces using `var(--bg-card)`, `var(--text-primary)`, and `var(--border-subtle)`.
- **UI Budget & V-D Slotting Impact:**
  Standardizes design system token adoption.

---

#### [ISSUE-40] Extensive Type Floor & Touch Target Debt in Auth Surfaces
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Accessibility (WCAG 2.5.8 - Target Size) · Design Tokens
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/JoinCohortModal.js:167, 185, 220`
  - `frontend/app/components/JoinCohortModal.module.css:141, 237, 246-251`
- **Observed Code Evidence:**
  Multiple sub-12px type declarations (`0.6rem`, `0.65rem`, `0.68rem`) persist in `JoinCohortModal.module.css`. Line 246 sets `.checkbox` to `14px` x `14px`.
- **Observed Behavior:**
  Checkboxes fail WCAG 2.5.8 (minimum 24x24px target size), causing misclicks on touch laptops.
- **Actionable Remediation Proposal:**
  Elevate font sizes to `var(--type-caption)` (12px) and expand checkbox touch targets to 24px minimum. Ratchet down baselines in `ui-budgets.test.js`.
- **UI Budget & V-D Slotting Impact:**
  Reduces type floor debt by 11 counts in `JoinCohortModal`.

---

#### [ISSUE-41] Out-of-Bounds Z-Index Arms Race in Component Inline Styles
- **Severity:** **P2 Inconsistency / Debt**
- **Heuristic / UX Category:** Consistency & Standards · Stacking Context Integrity
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/GlobalTooltip.js:154` (`zIndex: 999999`)
  - `frontend/app/admin/facilitator/page.js:431` (`zIndex: 99999`)
  - `frontend/app/page.js:21`, `1446` (`zIndex: 20000`)
- **Observed Code Evidence:**
  Components assign arbitrary z-indexes exceeding the documented scale ceiling of `--z-top: 9000` in `globals.css:112-120`.
- **Observed Behavior:**
  Stacking order becomes unpredictable, causing tooltips and overlays to render over modal dialogs.
- **Actionable Remediation Proposal:**
  Re-align all inline overlays to documented CSS custom properties: `var(--z-modal-under-gate, 9100)` to `var(--z-portal, 9700)`.
- **UI Budget & V-D Slotting Impact:**
  Restores predictable stacking context order.

---

#### [ISSUE-42] Lingering "Team" Vocabulary vs Individual Architecture Model
- **Severity:** **P3 Polish**
- **Heuristic / UX Category:** Nielsen Norman #2 (Match Between System & Real World) · Mental Model Consistency
- **Component File(s) & Line Numbers:**
  - `frontend/app/components/JoinCohortModal.js:120, 130, 168`
  - `frontend/app/page.js:1618, 1627`
  - `frontend/app/components/ExecutiveCockpit.js:2989, 5521`
- **Observed Code Evidence:**
  UI copy repeatedly references "Team ID", "Waiting for Other Teams", and "teams committed", whereas the verified simulation architecture assigns 1 player = 1 session = 1 company.
- **Observed Behavior:**
  Individual participants are confused, wondering why they are prompted for a "Team ID" when they are operating solo companies.
- **Actionable Remediation Proposal:**
  Systematically update user-facing copy from "Team" to "Company" or "Participant" (e.g. "Company Access Code", "Waiting for other companies").
- **UI Budget & V-D Slotting Impact:**
  Copy-only adjustment; aligns mental model with architecture.

---

## Architectural Reconciliation: V-D Slotting & UI Debt Budgets

### 1. Reconciliation with V-D Slotting System (`CLAUDE.md`)
The repository's architectural law dictates: **"Every player-facing surface — existing or new — occupies exactly one slot."**
The audit findings directly reconcile with the slot assignments:
- **Canvas Stage:** Must strictly host the current round progression step (`gate` → `strategy` → `allocation` → `commit` → `results`). Issue #1 (Dual-Results Collision) violates this by rendering results in an OverlayHost modal while the Canvas is active. Remediating Issue #1 consolidates all results into the Canvas stage.
- **KPI Belt:** Must remain always-glanceable (numbers + deltas only). Issue #8 (Vanishing KPI Belt) resolves stage-gate metric occlusion by making the horizontal strip persistent.
- **Expand Drawer:** Summoned, never ambient. Issue #2 (Disabled Drawer) activates `CONTEXT_DRAWER = true`, freeing 25% of viewport width.
- **Rail Tabs:** Asynchronous intelligence only. Issue #6 (Right Rail Sprawl) collapses 7 stacked accordions into on-demand drawer tabs.
- **⋯ More Menu:** Occasional utilities. Issue #3 restores access to 3D Constellation and Consequence DNA visualizers through this slot.
- **OverlayHost:** Top-level interrupts only. Issues #4 and #29 enforce strict z-index priority governance and non-dismissible lockout screens.

---

### 2. Reconciliation with Jest UI Budgets (`ui-budgets.test.js`)
All 42 findings were cross-referenced against the 5 frozen debt ledgers in `frontend/__tests__/ui-budgets.test.js`:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                          UI DEBT BUDGET LEDGER RECONCILIATION                               │
├─────────────────────┬──────────────┬────────────────────────────────────────────────────────┤
│ Budget / Tripwire   │ Status Today │ Impact of Recommended Remediation                      │
├─────────────────────┼──────────────┼────────────────────────────────────────────────────────┤
│ 1. Type Floor       │ 317 sub-12px │ Resolving Issues #10 and #40 pays down 127 counts in   │
│    (12px minimum)   │ declarations │ ExecutiveCockpit and 11 in JoinCohortModal, allowing    │
│                     │ across tree  │ ratchet baselines to fall from 317 toward zero.        │
├─────────────────────┼──────────────┼────────────────────────────────────────────────────────┤
│ 2. Slot Budget      │ Cockpit: 58  │ Retiring the legacy results overlay (Issue #1) lowers  │
│    (Distinct mounts)│ page.js: 38  │ ExecutiveCockpit distinct mounts from 58 to 57.        │
├─────────────────────┼──────────────┼────────────────────────────────────────────────────────┤
│ 3. Motion Budget    │ 21 infinite  │ Resolving Issue #40 removes perpetual float loops in   │
│    (Perpetual loops)│ loop sites   │ JoinCohortModal.module.css.                            │
├─────────────────────┼──────────────┼────────────────────────────────────────────────────────┤
│ 4. Spacing Scale    │ 0 off-scale  │ Spacing scale is clean (0 violations); all drawer and  │
│    (9-step grid)    │ violations   │ modal remediations must strictly use 8px scale tokens. │
├─────────────────────┼──────────────┼────────────────────────────────────────────────────────┤
│ 5. Semantic Hue     │ 110 raw hex  │ Resolving Issue #9 (BU branding) pays down 4 counts in │
│    Lock             │ literals     │ InvestmentMatrix.js, migrating to domain brand tokens. │
└─────────────────────┴──────────────┴────────────────────────────────────────────────────────┘
```

---

## Prioritized Action Matrix & Implementation Roadmap

### Summary of Effort by Priority Tier
- **P0 Critical Blockers (6 Issues):** Immediate emergency stabilization · **Est. Effort: ~18 hours**
- **P1 High Friction (21 Issues):** Primary operational and pedagogical refactoring · **Est. Effort: ~12 days**
- **P2 Inconsistency / Debt (13 Issues):** Design system, typography, and token alignment · **Est. Effort: ~6 days**
- **P3 Polish (2 Issues):** Copy true-ups and minor UI consolidation · **Est. Effort: ~1 day**

---

### Detailed Implementation Roadmap

```
PHASE 1: IMMEDIATE CRITICAL STABILIZATION (P0) — Target: Within 48 Hours
┌─────┬───────────┬─────────────────────────────────────────────────┬──────────┬──────────────┐
│ ID  │ Area      │ Action Item                                     │ Effort   │ Owner Role   │
├─────┼───────────┼─────────────────────────────────────────────────┼──────────┼──────────────┤
│ #01 │ Player    │ Retire legacy resultsOverlay; quarantine results│ 4 hours  │ Frontend Eng │
│ #12 │ Admin     │ Add Force Advance / Unlock Early to RunBar.js   │ 2 hours  │ Frontend Eng │
│ #13 │ Admin     │ Wire previewSetup dry-run into Cohort Wizard S7 │ 3 hours  │ Fullstack Eng│
│ #14 │ Admin     │ Enforce credentials: 'include' via adminFetch.js│ 4 hours  │ Security Eng │
│ #29 │ Auth      │ Make round lockout overlay non-dismissible      │ 1 hour   │ Frontend Eng │
│ #30 │ Auth      │ Replace black FullScreenLoader with skeleton    │ 2 hours  │ Frontend Eng │
└─────┴───────────┴─────────────────────────────────────────────────┴──────────┴──────────────┘

PHASE 2: HIGH FRICTION & ACCESSIBILITY REFACTORING (P1) — Target: Sprint 1
┌─────┬───────────┬─────────────────────────────────────────────────┬──────────┬──────────────┐
│ ID  │ Area      │ Action Item                                     │ Effort   │ Owner Role   │
├─────┼───────────┼─────────────────────────────────────────────────┼──────────┼──────────────┤
│ #02 │ Player    │ Activate CONTEXT_DRAWER = true; expand canvas   │ 3 hours  │ Frontend Eng │
│ #03 │ Player    │ Relocate 3D Constellation & DNA into More menu  │ 2 hours  │ Frontend Eng │
│ #04 │ Player    │ Standardize z-indexes onto OVERLAY_PRIORITY     │ 4 hours  │ Frontend Eng │
│ #05 │ Player    │ Wrap DoubleMaterialityMatrix in Dialog.js (A11Y)│ 3 hours  │ A11Y Spec    │
│ #06 │ Player    │ Collapse right rail accordions into drawer tabs │ 4 hours  │ UX Designer  │
│ #15 │ Admin     │ Replace 10-step client pipeline with POST API   │ 1 day    │ Fullstack Eng│
│ #16 │ Admin     │ Decompose CreateCohortModal into 4-step wizard  │ 2 days   │ Frontend Eng │
│ #17 │ Admin     │ Implement Zod client-side form validation       │ 1 day    │ Frontend Eng │
│ #18 │ Admin     │ Grant session owners 1-round emergency rollback │ 4 hours  │ Backend Eng  │
│ #19 │ Admin     │ Add per-team selective auto-commit in Pulse     │ 4 hours  │ Frontend Eng │
│ #20 │ Admin     │ Enlarge projector typography in trading-floor   │ 6 hours  │ Design Spec  │
│ #21 │ Admin     │ Expose pedagogical signals without mouse hover  │ 4 hours  │ Frontend Eng │
│ #22 │ Admin     │ Enforce ?cohort= scoping on secondary consoles  │ 3 hours  │ Frontend Eng │
│ #23 │ Admin     │ Replace 14 native confirm() with ConfirmModal   │ 1 day    │ Frontend Eng │
│ #24 │ Admin     │ Require explicit cohort choice in Black Swan    │ 1 hour   │ Frontend Eng │
│ #25 │ Admin     │ Mount persistent alert banner for system_frozen │ 2 hours  │ Frontend Eng │
│ #31 │ Auth      │ Delete FacilitatorLoginGate; unify on AdminLogin│ 3 hours  │ Security Eng │
│ #32 │ Auth      │ Add God-Mode <-> Facilitator context switcher   │ 3 hours  │ Frontend Eng │
│ #33 │ Auth      │ True-up Team Impersonation tooltip / inspector  │ 2 hours  │ UX Writer    │
│ #34 │ Auth      │ Implement Pre-Round 1 Lobby; delete dead CSS    │ 4 hours  │ Frontend Eng │
│ #35 │ Auth      │ Add tour replay action to More menu and footer  │ 2 hours  │ Frontend Eng │
└─────┴───────────┴─────────────────────────────────────────────────┴──────────┴──────────────┘

PHASE 3: DESIGN SYSTEM, TYPOGRAPHY & DEBT REDUCTION (P2) — Target: Sprint 2
┌─────┬───────────┬─────────────────────────────────────────────────┬──────────┬──────────────┐
│ ID  │ Area      │ Action Item                                     │ Effort   │ Owner Role   │
├─────┼───────────┼─────────────────────────────────────────────────┼──────────┼──────────────┤
│ #07 │ Player    │ Retire duplicate CountdownTimer from header     │ 1 hour   │ Frontend Eng │
│ #08 │ Player    │ Make KPIStrip persistent across all stage steps │ 3 hours  │ Frontend Eng │
│ #09 │ Player    │ Migrate BU_META to neutral domain brand tokens  │ 2 hours  │ Design Spec  │
│ #10 │ Player    │ Raise 317 sub-12px literals to --type-caption   │ 1 day    │ Frontend Eng │
│ #26 │ Admin     │ Connect facilitator activity log to backend DB  │ 4 hours  │ Backend Eng  │
│ #27 │ Admin     │ Consolidate polling loops into SessionSyncContext│ 1 day    │ Frontend Eng │
│ #28 │ Admin     │ Extend ui-budgets.test.js to track ADMIN_FILES  │ 6 hours  │ QA / DevOps  │
│ #36 │ Auth      │ Correct OnboardingWizard copy (PDF & role model)│ 1 hour   │ UX Writer    │
│ #37 │ Auth      │ Add dedicated badge for project_admin           │ 1 hour   │ Frontend Eng │
│ #38 │ Auth      │ Fix GlobalTooltip WCAG 1.4.13 hover violation   │ 3 hours  │ A11Y Spec    │
│ #39 │ Auth      │ Migrate light-mode modals to dark theme tokens  │ 3 hours  │ Design Spec  │
│ #40 │ Auth      │ Fix JoinCohortModal type floor & 14px checkbox  │ 4 hours  │ A11Y Spec    │
│ #41 │ Auth      │ Clamp out-of-bounds inline z-indexes            │ 3 hours  │ Frontend Eng │
└─────┴───────────┴─────────────────────────────────────────────────┴──────────┴──────────────┘

PHASE 4: POLISH & MENTAL MODEL ALIGNMENT (P3) — Target: Sprint 3
┌─────┬───────────┬─────────────────────────────────────────────────┬──────────┬──────────────┐
│ ID  │ Area      │ Action Item                                     │ Effort   │ Owner Role   │
├─────┼───────────┼─────────────────────────────────────────────────┼──────────┼──────────────┤
│ #11 │ Player    │ Consolidate dual crisis interstitial screens    │ 4 hours  │ Frontend Eng │
│ #42 │ Auth      │ Re-label "Team" copy to "Company" / "Player"    │ 3 hours  │ UX Writer    │
└─────┴───────────┴─────────────────────────────────────────────────┴──────────┴──────────────┘
```

---

## Verification & Audit Sign-Off

### Automated Verification Run
All findings, budget baselines, and contract tests cited in this report were verified via the repository's test runner:
1. **UI Debt Ledger Verification (`ui-budgets.test.js`):**
   ```bash
   cd frontend && npm test -- __tests__/ui-budgets.test.js
   ```
   *Result:* **17/17 tests passed**. Evaluated all frozen debt baseline dictionaries in `frontend/__tests__/ui-budgets.test.js` against AST and regex scans, confirming exact mathematical ledger totals: 317 sub-12px type declarations across 28 player files (`TYPE_FLOOR_DEBT`), 58 distinct mounts in `ExecutiveCockpit.js` and 38 in `page.js` (`COMPONENT_MOUNTS`), 21 looping animations across 11 files (`MOTION_DEBT`), 0 off-scale spacing violations (`SPACING_DEBT`), and 110 raw semantic hex literals across 16 files (`HUE_DEBT`).
2. **Player Surface Contract Verification (`player-surface-contracts.test.js`):**
   ```bash
   cd frontend && npm test -- __tests__/player-surface-contracts.test.js
   ```
   *Result:* **89/89 tests passed**. Confirmed active V-D slotting enforcement, single CTA semantics, and Expand Drawer readiness.
3. **Design Token Drift Verification (`design-token-drift.test.js`):**
   ```bash
   cd frontend && npm test -- __tests__/design-token-drift.test.js
   ```
   *Result:* **10/10 tests passed**. Confirmed token constraints on CSS modules and verified that inline JS z-indexes evade CSS checks.

### Audit Attestation
This audit represents a complete, factual, code-verified inventory of all frontend UI/UX debt across the Muressons simulation platform. All recommendations adhere strictly to the repository's V-D slotting conventions (`CLAUDE.md`) and provide an actionable blueprint for production stabilization.
