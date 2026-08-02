'use client';
import { useState, useEffect, useCallback } from 'react';

/**
 * OnboardingWalkthrough — Step-by-step guided tour for first-time players.
 * Improvement #1.4: Onboarding walkthrough overlay
 * MC-01: Advanced Climate Engine bonus tour steps
 *
 * Positioning: Card anchors dynamically relative to the spotlight element
 * to prevent overlap at any screen size.
 */

const BASE_STEPS = [
  {
    title: 'Welcome to the Executive Cockpit',
    body: 'You are the Chief Sustainability Officer of Muressons Global — a diversified conglomerate with 4 business units. OBJECTIVE: finish Year 5 (Round 10) with the strongest Terminal Valuation and Regenerative Multiple (M_R) \u2014 the score that prices your profits AND your impact together. Every decision moves it.',
    icon: '🏢',
    target: null, // no spotlight — centered card
  },
  {
    title: 'KPI Dashboard',
    body: 'The left panel shows real-time financial performance (EBITDA), environmental impact (CO₂), strategic resilience (VRIO Radar), and stakeholder trust. These update after every round.',
    icon: '📊',
    target: 'tour-kpi-target',
  },
  {
    title: 'Briefing & Decision Workspace',
    body: 'Each round starts with a crisis briefing. Complete any required gate assessments (like the Stakeholder Map), then choose your strategic response from the available options.',
    icon: '📋',
    target: 'tour-briefing-target',
  },
  {
    title: 'Capital Allocation',
    body: 'Allocate your treasury (CSF Pool) across the business units using the investment sliders. Balance short-term costs against long-term resilience.',
    icon: '💰',
    target: 'tour-capital-target',
  },
  {
    title: 'Intelligence Hub',
    body: 'The right panel contains your Executive Mailbox for crisis briefings, the Market Reality Feed for external events, and learning resources.',
    icon: '📬',
    target: 'tour-intelligence-target',
  },
  {
    title: 'Player Tools',
    body: 'Quick-access tools: Leaderboard, Achievements, AI Board Advisor, and Glossary. You can also toggle the soundtrack here.',
    icon: '🧭',
    target: 'tour-player-guides-target',
  },
  {
    title: 'Commit & Advance',
    body: 'When ready, hit Commit to lock in your decisions. Review the round results, then advance to the next crisis. Good luck, CSO!',
    icon: '✅',
    target: null, // fallback to commit button via querySelector
    fallbackSelector: 'button[class*="commitBtn"], [class*="rightCommit"]',
  },
];

const CLIMATE_EXTRA_STEPS = [
  {
    title: '🌍 Advanced Climate Engine',
    body: 'Every round, an Internal Carbon Fee is charged on each Business Unit based on its Carbon Intensity (CI). Higher CI = higher fee.',
    icon: '💨',
    target: null,
    isClimate: true,
  },
  {
    title: '🌱 The Green Fund',
    body: 'Carbon fees flow into a shared Green Fund that automatically subsidises green CapEx investments — reducing your out-of-pocket cost.',
    icon: '🌱',
    target: null,
    isClimate: true,
  },
  {
    title: '🌡️ Tipping Points',
    body: 'Watch the group average Carbon Intensity (CI). If it exceeds 70, a Climate Tipping Point is triggered — imposing hostile regulation, inflation, and reduced valuations.',
    icon: '🌡️',
    target: null,
    isClimate: true,
  },
];

export default function OnboardingWalkthrough({ onComplete, roundNumber, decisionParadigm }) {
  const STEPS = decisionParadigm === 'advanced_climate'
    ? [...BASE_STEPS, ...CLIMATE_EXTRA_STEPS]
    : BASE_STEPS;

  const [currentStep, setCurrentStep] = useState(0);
  const [visible, setVisible] = useState(true);
  const [tourActive, setTourActive] = useState(false);
  const [spot, setSpot] = useState({ x: 0, y: 0, w: 0, h: 0 });
  // Track which side of the screen the spotlight is on for card placement
  const [cardSide, setCardSide] = useState('center');

  // Start tour automatically on round 1
  useEffect(() => {
    if (roundNumber === 1 && visible && !tourActive) {
      setTourActive(true);
      setCurrentStep(0);
    } else if (roundNumber !== 1) {
      setVisible(false);
    }
  }, [roundNumber]);

  // Spotlight measurement — uses actual DOM elements, with intelligent fallbacks
  const measureTarget = useCallback(() => {
    if (!tourActive) return;
    const step = STEPS[currentStep];
    if (!step) return;

    let el = null;

    // Try the explicit target ID first
    if (step.target) {
      el = document.getElementById(step.target);
    }
    // Try fallback selector
    if (!el && step.fallbackSelector) {
      el = document.querySelector(step.fallbackSelector);
    }

    if (el) {
      const rect = el.getBoundingClientRect();
      const pad = 10;
      const newSpot = {
        x: rect.left - pad,
        y: rect.top - pad,
        w: rect.width + pad * 2,
        h: rect.height + pad * 2,
      };
      setSpot(newSpot);

      // Determine card placement based on spotlight position
      const vw = window.innerWidth;
      const spotCenterX = newSpot.x + newSpot.w / 2;
      if (spotCenterX < vw * 0.35) {
        setCardSide('right'); // spotlight is left → card goes right
      } else if (spotCenterX > vw * 0.65) {
        setCardSide('left'); // spotlight is right → card goes left
      } else {
        // Spotlight is center — put card above or below depending on vertical position
        const spotCenterY = newSpot.y + newSpot.h / 2;
        setCardSide(spotCenterY < window.innerHeight * 0.5 ? 'below' : 'above');
      }
    } else {
      // No element found — center everything
      setSpot({ x: 0, y: 0, w: 0, h: 0 });
      setCardSide('center');
    }
  }, [currentStep, tourActive]);

  useEffect(() => {
    if (!tourActive) return;

    // Measure immediately, then after layout stabilizes
    measureTarget();
    const raf = requestAnimationFrame(() => {
      measureTarget();
      setTimeout(measureTarget, 200);
    });

    window.addEventListener('resize', measureTarget);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', measureTarget);
    };
  }, [currentStep, tourActive, measureTarget]);

  if (!visible) return null;

  const step = STEPS[currentStep] || STEPS[0];
  const isLast = currentStep === STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      setTourActive(false);
      setVisible(false);
      onComplete?.();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleSkip = () => {
    setTourActive(false);
    setVisible(false);
    onComplete?.();
  };

  // Dynamic card positioning based on spotlight location
  const getCardStyle = () => {
    const base = {
      position: 'absolute',
      zIndex: 3,
      pointerEvents: 'all',
      transition: 'background 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), color 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), border-color 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1)',
    };

    switch (cardSide) {
      case 'right':
        return { ...base, left: `${Math.min(spot.x + spot.w + 24, window.innerWidth - 460)}px`, top: '50%', transform: 'translateY(-50%)' };
      case 'left':
        return { ...base, left: `${Math.max(spot.x - 460, 16)}px`, top: '50%', transform: 'translateY(-50%)' };
      case 'below':
        return { ...base, left: '50%', top: `${Math.min(spot.y + spot.h + 24, window.innerHeight - 300)}px`, transform: 'translateX(-50%)' };
      case 'above':
        return { ...base, left: '50%', top: `${Math.max(spot.y - 300, 16)}px`, transform: 'translateX(-50%)' };
      default: // center
        return { ...base, left: '50%', top: '50%', transform: 'translate(-50%, -50%)' };
    }
  };

  return (
    <>
      {/* ── Active Tour Overlay ── */}
      {tourActive && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, fontFamily: 'Inter, sans-serif', pointerEvents: 'none' }}>

          {/* Invisible click blocker — prevents interaction with cockpit while tour runs */}
          <div style={{ position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'all' }} />

          {/* Spotlight Cutout Overlay.

              VEIL OPACITY (2026-08-01): both branches used to sit at 0.75,
              which reads as "the briefing and workspace are blacked out". Two
              different jobs need two different weights:

                * SPOTLIGHT branch — a real element is highlighted, so the veil
                  must push everything else back while the ring draws the eye.
                  0.55 still does that, and the cockpit stays legible behind it
                  (context is the point of an orientation tour).

                * NO-TARGET branch — reached whenever a step's element is not
                  mounted yet, which is NORMAL, not an error: the Capital
                  Allocation panel (tour-capital-target) only exists inside the
                  deep-dive stage, so during Foundation the tour describes it
                  while it is legitimately absent. With nothing to highlight,
                  the veil's only job is to seat the card — at 0.75 it just
                  hid the whole cockpit for no benefit. 0.38 keeps the card
                  dominant while the screen behind it stays readable. */}
          {spot.w > 0 && spot.h > 0 ? (
            <div style={{
              position: 'absolute',
              left: spot.x,
              top: spot.y,
              width: spot.w,
              height: spot.h,
              borderRadius: '10px',
              border: '2px dashed #a5b4fc',
              background: 'transparent',
              zIndex: 3,
              transition: 'all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1)',
              pointerEvents: 'none',
              /* The 9999px box-shadow creates the dark overlay outside the box, while the box itself remains transparent */
              boxShadow: '0 0 0 9999px rgba(15, 23, 42, 0.55), 0 0 20px rgba(165, 180, 252, 0.15)',
            }} />
          ) : (
            <div style={{
              position: 'absolute', inset: 0,
              background: 'rgba(15, 23, 42, 0.38)',
              zIndex: 2, pointerEvents: 'none'
            }} />
          )}

          {/* Step Card */}
          <div style={{
            ...getCardStyle(),
            background: '#fff', borderRadius: 16, padding: '1.8rem 2rem',
            maxWidth: 420, width: '90%',
            boxShadow: '0 30px 80px rgba(0,0,0,0.5)',
            minHeight: 200, display: 'flex', flexDirection: 'column'
          }}>
            {/* Progress dots */}
            <div style={{
              display: 'flex', gap: 6, marginBottom: '1rem', justifyContent: 'center',
            }}>
              {STEPS.map((_, i) => (
                <div key={i} style={{
                  width: i === currentStep ? 20 : 6, height: 6, borderRadius: 3,
                  background: i === currentStep ? '#6366f1' : i < currentStep ? '#a5b4fc' : '#e2e8f0',
                  transition: 'background 0.3s, color 0.3s, border-color 0.3s, box-shadow 0.3s, opacity 0.3s, transform 0.3s',
                }} />
              ))}
            </div>

            {/* Climate step badge */}
            {step.isClimate && (
              <div style={{
                textAlign: 'center', marginBottom: '0.5rem',
              }}>
                <span style={{
                  display: 'inline-block',
                  fontSize: '0.68rem', fontWeight: 800,
                  letterSpacing: '0.12em', textTransform: 'uppercase',
                  padding: '3px 10px', borderRadius: 20,
                  background: 'rgba(16,185,129,0.12)',
                  border: '1px solid rgba(16,185,129,0.3)',
                  color: '#10b981',
                }}>
                  🌍 Advanced Climate Edition
                </span>
              </div>
            )}

            <div style={{ fontSize: '2rem', textAlign: 'center', marginBottom: '0.6rem' }}>{step.icon}</div>
            <h2 style={{
              margin: '0 0 0.5rem', fontSize: '1.1rem', fontWeight: 800,
              color: '#0f172a', textAlign: 'center',
            }}>{step.title}</h2>
            <p style={{
              margin: '0 0 1.2rem', fontSize: '0.82rem', color: '#64748b',
              lineHeight: 1.7, textAlign: 'center', flex: 1,
            }}>{step.body}</p>

            <div style={{ display: 'flex', gap: '0.6rem', marginTop: 'auto' }}>
              <button
                onClick={handleSkip}
                style={{
                  flex: 1, padding: '9px 0', background: '#f1f5f9', color: '#64748b',
                  border: '1px solid #e2e8f0', borderRadius: 8, fontWeight: 600,
                  cursor: 'pointer', fontSize: '0.75rem', fontFamily: 'Inter, sans-serif',
                }}
              >End Tour</button>
              <button
                onClick={handleNext}
                style={{
                  flex: 2, padding: '9px 0',
                  background: step.isClimate
                    ? 'linear-gradient(135deg, #059669, #10b981)'
                    : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700,
                  cursor: 'pointer', fontSize: '0.75rem', fontFamily: 'Inter, sans-serif',
                  boxShadow: step.isClimate
                    ? '0 4px 14px rgba(16,185,129,0.3)'
                    : '0 4px 14px rgba(99,102,241,0.3)',
                }}
              >{isLast ? '🚀 Start Playing' : `Next (${currentStep + 1}/${STEPS.length})`}</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
