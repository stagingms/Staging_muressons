# Project: Comprehensive UI/UX Audit of Muressons Platform (2026-09)

## Architecture & Scope
A comprehensive, rigorous UI/UX audit of the Muressons simulation platform covering all frontend surfaces:
1. **Player Simulation Surface**: Canvas stage, KPI belt, Expand drawer, Rail tabs, OverlayHost, feedback loops, V-D slotting conventions (`CLAUDE.md`, `player-surface-contracts.test.js`).
2. **Facilitator & Admin Portal**: Session orchestration (`RunBar.js`, `RoundPacingControl.js`), cohort creation wizards (`CreateCohortModal.js`), live projector displays (`admin/projector`, `trading-floor`, `war-map`), and administrative tooling (`FacilitatorManager.js`, God Mode, `ConfirmModal.js`).
3. **Auth & Onboarding Experience**: Initial access, role switching (`ROLE_HIERARCHY`, persona routing), session joins & waiting lobbies, contextual guidance & tours (`OnboardingWalkthrough.js`, `OnboardingWizard.js`), design tokens (`tokens.css`), and UI debt budgets (`ui-budgets.test.js`, `AUDIT_UX_Product_2026-08-02.md`).

## Feature Inventory & Issue Ledger
| # | Area / Domain | Issue Key | Severity | Heuristic Category | Primary Component(s) | Source |
|---|---------------|-----------|----------|-------------------|----------------------|--------|
| 1 | Player Surface | Dual-Results Overlay Collision & Pre-Commit Leak | P0 Critical | Visibility of System Status | `ExecutiveCockpit.js:4982`, `FocusOverlay.js` | Explorer 1 |
| 2 | Player Surface | Disabled Context Drawer & Viewport Starvation | P1 High Friction | Aesthetic & Minimalist Design | `ExecutiveCockpit.js:149`, `rightSidebar` | Explorer 1 |
| 3 | Player Surface | Stranded 3D Constellation & DNA Triggers | P1 High Friction | Recognition Rather Than Recall | `ExecutiveCockpit.js:3014, 3673` | Explorer 1 |
| 4 | Player Surface | Stacking Context Governance Breakdown | P1 High Friction | Consistency & Standards | `overlayPriority.js`, `page.js`, `ExecutiveCockpit.js` | Explorer 1 |
| 5 | Player Surface | CSRD Double Materiality Dialog A11Y Failure | P1 High Friction | User Control & Freedom (WCAG) | `DoubleMaterialityMatrix.js`, `page.js:1928` | Explorer 1 |
| 6 | Player Surface | Right Rail Accordion Sprawl & Cognitive Overload | P1 High Friction | Flexibility & Efficiency | `ExecutiveCockpit.js:4251-4573` | Explorer 1 |
| 7 | Player Surface | Duplicate Cockpit Header Countdown Timers | P2 Inconsistency | Aesthetic & Minimalist Design | `CountdownTimer.js`, `DecisionPressureTimer.js` | Explorer 1 |
| 8 | Player Surface | Inconsistent / Vanishing KPI Belt | P2 Inconsistency | Visibility of System Status | `FocusOverlay.js:250`, `resourcesPanel` | Explorer 1 |
| 9 | Player Surface | Semantic Hue Contamination in BU Branding | P2 Inconsistency | Consistency & Standards | `InvestmentMatrix.js:18-27`, `tokens.css` | Explorer 1 |
| 10 | Player Surface | Typographic Debt (317 Sub-12px Font Declarations)| P2 Debt | Aesthetic & Minimalist Design | `ExecutiveCockpit.js`, `ui-budgets.test.js` | Explorer 1 |
| 11 | Player Surface | Fragmented Dual Crisis Alert Screens | P3 Polish | Consistency & Standards | `CrisisAlerts.js`, `ExecutiveCockpit.js:1270` | Explorer 1 |
| 12 | Facilitator/Admin | RunBar Advance Deadlock in Free/Timed Modes | P0 Critical | Flexibility & Efficiency | `RunBar.js:198-212`, `RoundPacingControl.js` | Explorer 2 |
| 13 | Facilitator/Admin | Phantom Pre-Lock Server Preview (`previewSetup` Dead Code)| P0 Critical | Visibility of System Status | `CreateCohortModal.js:894` | Explorer 2 |
| 14 | Facilitator/Admin | 179 Fetch Invocations Missing `credentials: 'include'` | P0 Critical | System Integrity / Security | `FacilitatorManager.js`, `admin/` components | Explorer 2 |
| 15 | Facilitator/Admin | Fragile 10-Step Sequential Client-Side Creation Pipeline | P1 High Friction | Error Prevention / Reliability | `CreateCohortModal.js:755-884` | Explorer 2 |
| 16 | Facilitator/Admin | Monolithic Accordion Overload (85 `useState` in 3,408 LOC) | P1 High Friction | Cognitive Load / Minimalist Design | `CreateCohortModal.js:1-3409` | Explorer 2 |
| 17 | Facilitator/Admin | Near-Total Absence of Client-Side Form Validation | P1 High Friction | Error Prevention | `CreateCohortModal.js:1047-1066` | Explorer 2 |
| 18 | Facilitator/Admin | Asymmetric Undo Capability (Locked Facilitators) | P1 High Friction | User Control & Freedom | `RoundPacingControl.js`, `UndoRound.js` | Explorer 2 |
| 19 | Facilitator/Admin | All-or-Nothing Force Advance with Hardcoded Fallback | P1 High Friction | Flexibility & Efficiency | `RoundPacingControl.js:272-305` | Explorer 2 |
| 20 | Facilitator/Admin | Room-Scale Projector Illegibility (10px SVG, 1.1rem text)| P1 High Friction | Aesthetic & Minimalist Design | `trading-floor/page.js`, `war-map/page.js` | Explorer 2 |
| 21 | Facilitator/Admin | Critical Pedagogical Signals Trapped Behind Hover | P1 High Friction | Visibility of System Status | `war-map/page.js:50-74` | Explorer 2 |
| 22 | Facilitator/Admin | Missing Cohort Scoping on Secondary Projector Consoles | P1 High Friction | Match Between System & Real World | `trading-floor/page.js:71, 109` | Explorer 2 |
| 23 | Facilitator/Admin | Proliferation of Native Browser `confirm()` (14+ sites)| P1 High Friction | Error Prevention / Consistency | `CrisisTriggerConfig.js`, `PlayerRegistry.js` | Explorer 2 |
| 24 | Facilitator/Admin | Silent First-Session Pre-Selection in Custom Black Swan | P1 High Friction | Error Prevention | `CustomBlackSwanBuilder.js:60-62` | Explorer 2 |
| 25 | Facilitator/Admin | Auto-Pause Triggers Lack Room-Wide Visual Escalation | P1 High Friction | Visibility of System Status | `AutoPauseConfig.js`, `admin/facilitator` | Explorer 2 |
| 26 | Facilitator/Admin | In-Memory Ephemeral Activity Log on Facilitator Portal | P2 Inconsistency | Recognition Rather than Recall | `admin/facilitator/page.js:1259` | Explorer 2 |
| 27 | Facilitator/Admin | Uncoordinated Polling Stampede & Disregarded WebSocket | P2 Tech Debt | Visibility of System Status | `RunBar.js`, `CohortPulse.js`, `Leaderboard` | Explorer 2 |
| 28 | Facilitator/Admin | Widespread Token & Inline Styling Debt in Admin Codebase | P2 Tech Debt | Consistency & Standards | `CreateCohortModal.js`, `FacilitatorManager` | Explorer 2 |
| 29 | Auth & Onboarding | Bypassable Round-Locked Lockout Screen | P0 Critical | Error Prevention / Integrity | `frontend/app/page.js:1609-1635` | Explorer 3 |
| 30 | Auth & Onboarding | Pitch-Black Screen During Dynamic Chunk Load | P0 Critical | Visibility of System Status | `frontend/app/page.js:21, 125` | Explorer 3 |
| 31 | Auth & Onboarding | Duplicate `FacilitatorLoginGate` Bypassing Storage Probes | P1 High Friction | Consistency & Standards | `admin/facilitator/page.js:150-286` | Explorer 3 |
| 32 | Auth & Onboarding | Missing Role & Context Switcher Between Admin Portals | P1 High Friction | Flexibility & Efficiency | `god-mode/page.js`, `facilitator/page.js` | Explorer 3 |
| 33 | Auth & Onboarding | Deceptive Team Impersonation Feature | P1 High Friction | Match Between System & Real World | `TeamImpersonation.js`, `sidebarConfig.js` | Explorer 3 |
| 34 | Auth & Onboarding | Missing Pre-Round Participant Lobby & Dead CSS | P1 High Friction | Visibility of System Status | `page.js:1440`, `page.module.css:14-147` | Explorer 3 |
| 35 | Auth & Onboarding | Permanently Unreachable Tour Replay / Resume | P1 High Friction | Recognition Rather than Recall | `page.js:2102`, `OnboardingWizard.js:168` | Explorer 3 |
| 36 | Auth & Onboarding | Regressed Tour Copy (PDF Export Promise, 3-tier model) | P2 Debt | Help & Documentation | `OnboardingWizard.js:49, 116` | Explorer 3 |
| 37 | Auth & Onboarding | Mislabelled Active Role Badge for `project_admin` | P2 Inconsistency | Visibility of System Status | `admin/facilitator/page.js:1746-1755` | Explorer 3 |
| 38 | Auth & Onboarding | Non-Hoverable Global Tooltips (WCAG 1.4.13 Violation) | P2 Inconsistency | Accessibility (WCAG 1.4.13) | `GlobalTooltip.js:181, 226-231` | Explorer 3 |
| 39 | Auth & Onboarding | Clashing Light-Mode Modals on Dark Simulation Cockpit | P2 Inconsistency | Aesthetic & Minimalist Design | `ChangePasswordModal.js`, `Onboarding` | Explorer 3 |
| 40 | Auth & Onboarding | Type Floor (11 counts) & Touch Target Debt (14px) | P2 Inconsistency | Accessibility (WCAG 2.5.8) | `JoinCohortModal.js`, `.module.css` | Explorer 3 |
| 41 | Auth & Onboarding | Out-of-Bounds Z-Index Arms Race in Component Styles | P2 Debt | Stacking Context Integrity | `GlobalTooltip.js:154`, `page.js:21` | Explorer 3 |
| 42 | Auth & Onboarding | Lingering "Team" Vocabulary vs Individual Model | P3 Polish | Consistency & Mental Model | `JoinCohortModal.js`, `page.js:1618` | Explorer 3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Survey & Scope Mapping | Map all 3 surfaces, slotting conventions, and UI budgets via 3 Explorers | None | DONE |
| M2 | Master Audit Report Compilation | Synthesize all 42 findings into `AUDIT_UI_UX_Comprehensive_2026-09.md` at workspace root via Worker | M1 | IN_PROGRESS |
| M3 | Multi-Role Review & Verification | Deploy 2 Reviewers, 2 Challengers, and 1 Forensic Auditor to verify deliverable against all acceptance criteria | M2 | PLANNED |
| M4 | Final Gate & Sentinel Notification | Verify 100% gate pass and notify Sentinel with completion report | M3 | PLANNED |

## Interface Contracts & Deliverable Acceptance Criteria
Deliverable: `/Users/Dilijithkannan/Documents/AG/Staging_Mayan/AUDIT_UI_UX_Comprehensive_2026-09.md`
Must strictly include:
1. **Executive Summary**: Synthesizing top 3-5 immediate improvement priorities with estimated impact.
2. **Comprehensive Surface Coverage**:
   - Section 1: Player Simulation Surface Audit (Canvas stage, KPI belt, Expand drawer, Rail tabs, OverlayHost)
   - Section 2: Facilitator & Admin Portal Audit (Session orchestration, cohort wizards, live projector displays, admin tooling)
   - Section 3: Auth & Onboarding Experience Audit (Initial access, role switching, session joins, contextual tours, tokens & UI budgets)
3. **Rigorous Issue Specification**: Every issue must have:
   - Explicit Severity: P0 Critical Blocker, P1 High Friction, P2 Inconsistency/Debt, P3 Polish
   - Heuristic/UX Category (Nielsen Norman / Cognitive Load / Error Prevention / WCAG)
   - Concrete Component File(s), line citations, and CSS tokens in `frontend/`
   - Concrete observed behavior / code evidence
   - Actionable remediation proposal
   - UI budget & V-D slotting reconciliation against `frontend/__tests__/ui-budgets.test.js` and `CLAUDE.md`
4. **Prioritized Action Matrix & Implementation Roadmap**: Clear phases (Immediate P0, High Priority P1, Medium Priority P2, Backlog P3).
