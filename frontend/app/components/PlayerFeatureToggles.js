'use client';

/**
 * PlayerFeatureToggles — DEPRECATED / RETIRED.
 *
 * The player-facing round-surface toggles (Decision Consequence Map, Board
 * Room Moment) are no longer a standalone global tab. They are now PER-COHORT
 * settings living in the "Round Surfaces" group of the Player Dashboard panel
 * (AnalyticsControlPanel), persisted via POST /api/admin/player-feature-toggles
 * with a ?session_id, and read cohort-effective from global-settings.
 *
 * This file is kept only because the workspace cannot delete it; it is imported
 * nowhere and renders nothing. Safe to remove.
 */
export default function PlayerFeatureToggles() {
  return null;
}
