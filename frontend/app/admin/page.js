'use client';

/**
 * /admin — the single admin entry point (Phase L: role-aware login).
 *
 * REPLACES the old two-card "System Access Portal" that advertised
 * "God Mode — Super Admin" to every unauthenticated visitor and made people
 * self-select a portal before logging in. You cannot hide a role from a
 * facilitator on a page that shows every role's door pre-auth.
 *
 * New flow: one neutral sign-in → the SERVER returns the role → we route the
 * identity to the one dashboard it owns. god_mode / project_admin are never
 * named here. This is UX routing only; the JWT cookie + require_* guards remain
 * the real security boundary (a facilitator who forges client state is still
 * rejected server-side).
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import AdminLogin from '../components/AdminLogin';
import { roleHome, roleStorageKey, roleAuthSubset } from '../utils/roleRouting';

export default function AdminGateway() {
  const router = useRouter();
  // When a dashboard bounces an expired/unauth session back here it appends
  // ?expired=1 so we can explain why they're seeing the login again.
  const [expired, setExpired] = useState(false);
  useEffect(() => {
    try { setExpired(new URLSearchParams(window.location.search).get('expired') === '1'); }
    catch { /* ignore */ }
  }, []);

  const handleSuccess = (data) => {
    // Persist the display-safe subset under the key the destination dashboard
    // reads on mount, so it lands straight in — no second login.
    try {
      localStorage.setItem(roleStorageKey(data), JSON.stringify(roleAuthSubset(data)));
    } catch { /* ignore storage failure — the JWT cookie still authenticates */ }
    router.push(roleHome(data));
  };

  return (
    <AdminLogin
      onSuccess={handleSuccess}
      subtitle={expired ? 'Your session expired — please sign in again to continue.' : undefined}
    />
  );
}
