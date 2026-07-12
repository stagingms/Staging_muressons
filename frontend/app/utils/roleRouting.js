/**
 * roleRouting — single source of truth for "which dashboard does a signed-in
 * identity land on?" (Phase L: role-aware login).
 *
 * The server is the authority on the ROLE (returned by /facilitators/login and
 * enforced by the JWT cookie + require_* guards). This module only decides
 * WHERE to route a already-authenticated identity — a UX convenience, never the
 * security boundary. Mirrors CLAUDE.md's is_admin_role (level ≥ super_admin):
 * god_mode and super_admin/admin own the God Mode console; everyone else
 * (lead_facilitator, facilitator, project_admin) lands on the facilitator
 * portal, which itself renders the correct role-filtered view.
 */

// Client-side echo of backend is_admin_role: god_mode (4) and super_admin/admin
// (3) are "admin". We can only see the role string + is_admin flag here; that's
// enough for routing (the server still enforces the real gate).
export function isAdminRole(role, isAdmin = false) {
  return role === 'super_admin' || role === 'admin' || role === 'god_mode' || isAdmin === true;
}

/** Where a freshly-authenticated identity should be sent. */
export function roleHome(data = {}) {
  return isAdminRole(data.role, data.is_admin) ? '/admin/god-mode' : '/admin/facilitator';
}

/** localStorage key the destination dashboard reads its cached auth from. */
export function roleStorageKey(data = {}) {
  return isAdminRole(data.role, data.is_admin) ? 'godmode_auth' : 'facilitator_auth';
}

/**
 * The display-safe subset each dashboard persists (C-2: booleans/ids only, no
 * PII — XSS can read localStorage). Kept identical to what each page already
 * writes so the destination mounts straight into its dashboard.
 */
export function roleAuthSubset(data = {}) {
  const {
    facilitator_id, role, allowed_tabs, is_admin, username, name,
    shockwave_enabled, trading_floor_enabled, situation_room_enabled,
    must_change_password, permissions,
  } = data;
  if (isAdminRole(role, is_admin)) {
    return { facilitator_id, role, allowed_tabs, is_admin, username, name };
  }
  return {
    facilitator_id, role, allowed_tabs, is_admin, username, name,
    shockwave_enabled, trading_floor_enabled, situation_room_enabled,
    must_change_password, permissions,
  };
}
