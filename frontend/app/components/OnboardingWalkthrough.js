'use client';
import { useState, useEffect } from 'react';

/**
 * OnboardingWalkthrough — Step-by-step guided tour for first-time players.
 * Improvement #1.4: Onboarding walkthrough overlay
 */

const STEPS = [
  {
    title: 'Welcome to the Executive Cockpit',
    body: 'You are the Chief Sustainability Officer of Muressons Global — a diversified conglomerate with 4 business units. Your decisions over 10 rounds will shape the company\'s future.',
    icon: '🏢',
    position: 'center',
  },
  {
    title: 'KPI Dashboard (Left Panel)',
    body: 'Monitor real-time financial performance (EBITDA), environmental impact (CO₂), strategic resilience (VRIO Radar), and stakeholder trust. These update after every round.',
    icon: '📊',
    position: 'left',
  },
  {
    title: 'Stage 1: Briefing & Gates',
    body: 'Start each round by carefully reading the crisis briefing. You must complete any required gateway assessments (like the Stakeholder Map) before you can unlock your strategic options.',
    icon: '📋',
    position: 'center',
  },
  {
    title: 'Stage 2: Decision Workspace',
    body: 'Once gates are passed, choose your strategic response. Each option has different costs and consequences.',
    icon: '🎯',
    position: 'center',
  },
  {
    title: 'Capital Allocation',
    body: 'Allocate your treasury (CSF Pool) across the 4 business units using the investment sliders. Balance short-term costs against long-term resilience.',
    icon: '💰',
    position: 'center',
  },
  {
    title: 'Intelligence Hub (Right Panel)',
    body: 'Check your Executive Mailbox for crisis briefings, read the Market Reality Feed for external events, and access learning resources via the Resources panel.',
    icon: '📬',
    position: 'right',
  },
  {
    title: 'Player Guides & Actions',
    body: 'Use these quick-access tools to view the Leaderboard, check Achievements, consult the AI Board Advisor, or open the Glossary. You can also toggle the soundtrack here.',
    icon: '🧭',
    position: 'center',
  },
  {
    title: 'Commit & Advance',
    body: 'When ready, hit Commit to lock in your decisions. Review the round results, then click Advance to proceed to the next crisis. Good luck, CSO!',
    icon: '✅',
    position: 'right',
  },
];

export default function OnboardingWalkthrough({ onComplete, roundNumber }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [visible, setVisible] = useState(true);
  const [promptOpen, setPromptOpen] = useState(false);
  const [tourActive, setTourActive] = useState(false);
  // Must be declared here (before any early return) to satisfy Rules of Hooks
  const [spot, setSpot] = useState({ x: '0', y: '0', w: '0', h: '0' });

  // Ask for tour every time round 1 starts
  useEffect(() => {
    if (roundNumber === 1 && visible) {
      setPromptOpen(true);
    } else {
      setVisible(false);
      setPromptOpen(false);
    }
  }, [roundNumber]);

  // Must be above early return — spotlight positioning effect (Rules of Hooks)
  useEffect(() => {
    if (!tourActive) return;

    const updateSpot = () => {
      const HPx = window.innerHeight - 52;
      let newSpot = { x: '0', y: '0', w: '0', h: '0' };
      
      switch(currentStep) {
        case 0: break;
        case 1: newSpot = { x: '0', y: '52px', w: '24%', h: `${HPx}px` }; break;
        case 2: 
          const bTarget = document.getElementById('tour-briefing-target');
          if (bTarget) {
            const rect = bTarget.getBoundingClientRect();
            newSpot = { x: `${rect.left - 8}px`, y: `${rect.top - 8}px`, w: `${rect.width + 16}px`, h: `${rect.height + 16}px` };
          }
          break;
        case 3: 
          const sTarget = document.getElementById('tour-strategic-target');
          if (sTarget) {
            const rect = sTarget.getBoundingClientRect();
            newSpot = { x: `${rect.left - 8}px`, y: `${rect.top - 8}px`, w: `${rect.width + 16}px`, h: `${rect.height + 16}px` };
          }
          break;
        case 4: 
          const cTarget = document.getElementById('tour-capital-target');
          if (cTarget) {
            const rect = cTarget.getBoundingClientRect();
            newSpot = { x: `${rect.left - 8}px`, y: `${rect.top - 8}px`, w: `${rect.width + 16}px`, h: `${rect.height + 16}px` };
          }
          break;
        case 5: newSpot = { x: '76%', y: '52px', w: '24%', h: `${HPx * 0.88}px` }; break;
        case 6:
          const guides = document.getElementById('tour-player-guides-target');
          if (guides) {
            const rect = guides.getBoundingClientRect();
            newSpot = { x: `${rect.left - 12}px`, y: `${rect.top - 12}px`, w: `${rect.width + 24}px`, h: `${rect.height + 24}px` };
          }
          break;
        case 7:
          const btn = document.querySelector('button[class*="commitBtn"]');
          if (btn) {
            const rect = btn.getBoundingClientRect();
            newSpot = { 
              x: `${rect.left - 12}px`, 
              y: `${rect.top - 12}px`, 
              w: `${rect.width + 24}px`, 
              h: `${rect.height + 24}px` 
            };
          } else {
            newSpot = { x: '76%', y: `calc(100vh - 12vh)`, w: '24%', h: `12vh` };
          }
          break;
      }
      setSpot(newSpot);
    };

    updateSpot();
    setTimeout(updateSpot, 50);
    window.addEventListener('resize', updateSpot);
    return () => window.removeEventListener('resize', updateSpot);
  }, [currentStep, tourActive]);

  if (!visible) return null;

  const handleStartTour = () => {
    setPromptOpen(false);
    setTourActive(true);
    setCurrentStep(0);
  };

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
    setPromptOpen(false);
    setTourActive(false);
    setVisible(false);
    onComplete?.();
  };

  // Position styles based on step
  const getCardStyle = () => {
    switch (step.position) {
      case 'left': return { left: '26%', top: '50%', transform: 'translateY(-50%)' }; // Shifted right so it doesn't overlap left panel
      case 'right': return { right: '26%', top: '50%', transform: 'translateY(-50%)' }; // Shifted left to not overlap right panel
      default: 
        if (currentStep === 2) return { left: '50%', bottom: '15%', transform: 'translateX(-50%)' }; // Briefing at top, card at bottom
        if (currentStep === 3) return { left: '50%', top: '15%', transform: 'translateX(-50%)' }; // Strategic Options at bottom, card at top
        if (currentStep === 4) return { left: '50%', bottom: '15%', transform: 'translateX(-50%)' }; // Investment Matrix in middle, card at bottom
        if (currentStep === 6) return { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }; // Player guides card in middle
        if (currentStep === 7) return { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }; // Back to center
        return { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' };
    }
  };



  return (
    <>
      {/* ── Prompt Dialog ── */}
      {promptOpen && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 20000,
          background: 'rgba(15,23,42,0.85)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'Inter, sans-serif',
        }}>
          <div style={{
            background: '#fff', borderRadius: 16, padding: '2rem', maxWidth: 400, width: '90%',
            textAlign: 'center', boxShadow: '0 30px 60px rgba(0,0,0,0.4)',
            animation: 'fadeSlideUp 0.3s ease-out'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>👋</div>
            <h2 style={{ margin: '0 0 0.5rem', color: '#0f172a', fontWeight: 800 }}>Welcome to Module 1</h2>
            <p style={{ color: '#64748b', fontSize: '0.88rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>
              You have just entered the Executive Cockpit. Would you like a quick interactive tour to familiarize yourself with the controls?
            </p>
            <div style={{ display: 'flex', gap: '0.8rem' }}>
              <button
                onClick={handleSkip}
                style={{
                  flex: 1, padding: '10px 0', border: '1px solid #cbd5e1', background: '#f8fafc',
                  color: '#475569', borderRadius: 8, fontWeight: 700, cursor: 'pointer'
                }}
              >Skip Tour</button>
              <button
                onClick={handleStartTour}
                style={{
                  flex: 1, padding: '10px 0', border: 'none', background: '#6366f1',
                  color: '#fff', borderRadius: 8, fontWeight: 700, cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(99,102,241,0.3)'
                }}
              >Yes, Start Tour</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Active Tour Overlay ── */}
      {tourActive && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, fontFamily: 'Inter, sans-serif' }}>
          
          {/* SVG Spotlight Mask background */}
          <svg style={{ position: 'absolute', inset: 0, width: '100vw', height: '100vh', pointerEvents: 'none' }}>
            <defs>
              <mask id="spotlight-mask">
                <rect x="0" y="0" width="100%" height="100%" fill="white" />
                <rect x={spot.x} y={spot.y} width={spot.w} height={spot.h} fill="black" rx="8" />
              </mask>
            </defs>
            <rect 
              x="0" y="0" width="100%" height="100%" 
              fill="rgba(15,23,42,0.85)" 
              mask="url(#spotlight-mask)" 
              style={{ backdropFilter: 'blur(6px)' }}
            />
            {/* Outline box around the cutout */}
            {spot.w !== '0' && (
              <rect x={spot.x} y={spot.y} width={spot.w} height={spot.h} fill="none" stroke="#6366f1" strokeWidth="3" strokeDasharray="6 4" rx="8" />
            )}
          </svg>

          {/* Invisible click blocker over the cutout to prevent interaction during tour */}
          <div style={{ position: 'absolute', inset: 0, zIndex: 1 }} />

          {/* Step Card */}
          <div style={{
            position: 'absolute',
            ...getCardStyle(),
            zIndex: 2,
            background: '#fff', borderRadius: 16, padding: '1.8rem 2rem',
            maxWidth: 420, width: '90%',
            boxShadow: '0 30px 80px rgba(0,0,0,0.5)',
            transition: 'all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1)',
            minHeight: 220, display: 'flex', flexDirection: 'column'
          }}>
            {/* Progress dots */}
            <div style={{
              display: 'flex', gap: 6, marginBottom: '1rem', justifyContent: 'center',
            }}>
              {STEPS.map((_, i) => (
                <div key={i} style={{
                  width: i === currentStep ? 20 : 6, height: 6, borderRadius: 3,
                  background: i === currentStep ? '#6366f1' : i < currentStep ? '#a5b4fc' : '#e2e8f0',
                  transition: 'all 0.3s',
                }} />
              ))}
            </div>

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
                  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700,
                  cursor: 'pointer', fontSize: '0.75rem', fontFamily: 'Inter, sans-serif',
                  boxShadow: '0 4px 14px rgba(99,102,241,0.3)',
                }}
              >{isLast ? '🚀 Start Playing' : `Next (${currentStep + 1}/${STEPS.length})`}</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
