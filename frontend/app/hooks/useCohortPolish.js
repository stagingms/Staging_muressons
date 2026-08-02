'use client';

/**
 * useCohortPolish(sessionId) — LOW-tier polish: cohort accessibility defaults
 * + white-label branding, fetched once from session-info and APPLIED at the
 * document level so every panel inherits them without per-component wiring.
 *
 * Accessibility (cohort defaults; players can still adjust locally where a
 * local control exists — these set the baseline):
 *   high_contrast      → `mur-high-contrast` class on <html> (CSS hooks below)
 *   font_scale         → `--mur-font-scale` CSS var + root font-size multiplier
 *   reduced_motion     → `mur-reduced-motion` class (collapse animations)
 *   colorblind_safe    → `mur-colorblind-safe` class (chart palette hook)
 *   screen_reader_mode → `mur-screen-reader` class (denser labels hook)
 *
 * Branding:
 *   primary_color → `--mur-brand-primary` CSS var
 *   institution / logo_url → returned for the header to render.
 *
 * Fail-open: no config or any fetch error ⇒ nothing is applied and branding
 * is empty — byte-for-byte the previous experience.
 */

import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const ACC_CLASSES = {
  high_contrast: 'mur-high-contrast',
  reduced_motion: 'mur-reduced-motion',
  colorblind_safe: 'mur-colorblind-safe',
  screen_reader_mode: 'mur-screen-reader',
};

function applyPolish(acc, branding) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  Object.entries(ACC_CLASSES).forEach(([key, cls]) => {
    root.classList.toggle(cls, !!(acc && acc[key]));
  });
  const scale = Number(acc?.font_scale) || 1.0;
  if (scale !== 1.0) {
    root.style.setProperty('--mur-font-scale', String(scale));
    root.style.fontSize = `${Math.round(scale * 100)}%`;
  } else {
    root.style.removeProperty('--mur-font-scale');
    root.style.removeProperty('font-size');
  }
  if (branding?.primary_color) {
    root.style.setProperty('--mur-brand-primary', branding.primary_color);
  } else {
    root.style.removeProperty('--mur-brand-primary');
  }
}

export function useCohortPolish(sessionId) {
  const [branding, setBranding] = useState({ institution: null, logo_url: null, primary_color: null });
  const [accessibility, setAccessibility] = useState({});

  useEffect(() => {
    if (!sessionId) return;
    let alive = true;
    fetch(`${API}/api/simulations/${sessionId}/session-info`)
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        if (!alive || !d) return;
        const acc = d.accessibility_defaults || {};
        const brand = d.branding || {};
        setAccessibility(acc);
        setBranding({
          institution: brand.institution || null,
          logo_url: brand.logo_url || null,
          primary_color: brand.primary_color || null,
        });
        applyPolish(acc, brand);
      })
      .catch(() => {}); // fail-open: keep the default experience
    return () => { alive = false; };
  }, [sessionId]);

  return { branding, accessibility };
}

export default useCohortPolish;
