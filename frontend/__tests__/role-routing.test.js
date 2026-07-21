/**
 * Phase L — role-aware login routing. The single source of truth for
 * "which dashboard does a signed-in identity land on?" A facilitator must
 * NEVER be routed to god mode; only super_admin/admin/god_mode go there.
 */
import { isAdminRole, roleHome, roleStorageKey, roleAuthSubset } from '../app/utils/roleRouting';

describe('roleHome routes each identity to its own dashboard', () => {
  const cases = [
    ['god_mode',         { role: 'god_mode' },         '/admin/god-mode'],
    ['super_admin',      { role: 'super_admin' },       '/admin/god-mode'],
    ['admin (alias)',    { role: 'admin' },             '/admin/god-mode'],
    ['is_admin flag',    { role: 'facilitator', is_admin: true }, '/admin/god-mode'],
    ['lead_facilitator', { role: 'lead_facilitator' },  '/admin/facilitator'],
    ['facilitator',      { role: 'facilitator' },       '/admin/facilitator'],
    ['project_admin',    { role: 'project_admin' },     '/admin/facilitator'],
  ];
  test.each(cases)('%s → %s', (_name, data, expected) => {
    expect(roleHome(data)).toBe(expected);
  });

  test('a plain facilitator is never routed to god mode', () => {
    expect(roleHome({ role: 'facilitator' })).not.toBe('/admin/god-mode');
    expect(roleHome({ role: 'project_admin' })).not.toBe('/admin/god-mode');
  });
});

describe('isAdminRole matches the backend is_admin_role intent', () => {
  test.each(['god_mode', 'super_admin', 'admin'])('%s is admin', (r) => {
    expect(isAdminRole(r)).toBe(true);
  });
  test.each(['facilitator', 'lead_facilitator', 'project_admin'])('%s is not admin', (r) => {
    expect(isAdminRole(r)).toBe(false);
  });
  test('is_admin flag forces admin', () => {
    expect(isAdminRole('facilitator', true)).toBe(true);
  });
});

describe('storage key + subset match the destination page', () => {
  test('admin → godmode_auth, no permission flags leaked', () => {
    expect(roleStorageKey({ role: 'super_admin' })).toBe('godmode_auth');
    const sub = roleAuthSubset({ role: 'super_admin', permissions: { x: 1 }, facilitator_id: 'FAC-1' });
    expect(sub.facilitator_id).toBe('FAC-1');
    expect('permissions' in sub).toBe(false);   // god-mode subset omits it
  });
  test('facilitator → facilitator_auth, carries permissions + capability flags', () => {
    expect(roleStorageKey({ role: 'facilitator' })).toBe('facilitator_auth');
    const sub = roleAuthSubset({ role: 'facilitator', permissions: { can_create_cohorts: false }, shockwave_enabled: true });
    expect(sub.permissions).toEqual({ can_create_cohorts: false });
    expect(sub.shockwave_enabled).toBe(true);
  });
});
