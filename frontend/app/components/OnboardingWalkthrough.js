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
    title: 'Decision Workspace (Center)',
    body: 'Read the round briefing, complete any required assessments, then choose your strategic response. Each option has different costs and consequences.',
    icon: '🎯',
    position: 'center',
  },
  {
    title: 'Capital Allocation',
    body: 'Allocate 20% of your treasury (CSF Pool) across the 4 business units using the investment sliders. Balance short-term costs against long-term resilience.',
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
    title: 'Commit & Advance',
    body: 'When ready, hit Commit to lock in your decisions. Review the round results, then click Advance to proceed to the next crisis. Good luck, CSO!',
    icon: '✅',
    position: 'right',
  },
];

export default function OnboardingWalkthrough({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [visible, setVisible] = useState(true);

  // Check if user has seen onboarding before
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const seen = localStorage.getItem('muressons_onboarding_done');
      if (seen === 'true') setVisible(false);
    }
  }, []);

  if (!visible) return null;

  const step = STEPS[currentStep];
  const isLast = currentStep === STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      if (typeof window !== 'undefined') {
        localStorage.setItem('muressons_onboarding_done', 'true');
      }
      setVisible(false);
      onComplete?.();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleSkip = () => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('muressons_onboarding_done', 'true');
    }
    setVisible(false);
    onComplete?.();
  };

  // Position styles based on step
  const getPositionStyle = () => {
    switch (step.position) {
      case 'left': return { left: '2%', top: '50%', transform: 'translateY(-50%)' };
      case 'right': return { right: '2%', top: '50%', transform: 'translateY(-50%)' };
      default: return { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' };
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 20000,
      background: 'rgba(15,23,42,0.75)', backdropFilter: 'blur(6px)',
      fontFamily: 'Inter, sans-serif',
    }}>
      {/* Spotlight hint arrows */}
      {step.position === 'left' && (
        <div style={{
          position: 'absolute', left: '25%', top: '15%', bottom: '15%', width: 2,
          background: 'linear-gradient(180deg, transparent, rgba(99,102,241,0.4), transparent)',
          borderRadius: 2,
        }} />
      )}
      {step.position === 'right' && (
        <div style={{
          position: 'absolute', right: '25%', top: '15%', bottom: '15%', width: 2,
          background: 'linear-gradient(180deg, transparent, rgba(99,102,241,0.4), transparent)',
          borderRadius: 2,
        }} />
      )}

      {/* Step Card */}
      <div style={{
        position: 'absolute',
        ...getPositionStyle(),
        background: '#fff', borderRadius: 16, padding: '1.8rem 2rem',
        maxWidth: 420, width: '90%',
        boxShadow: '0 30px 80px rgba(0,0,0,0.3)',
        animation: 'fadeSlideUp 0.3s ease-out',
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
          lineHeight: 1.7, textAlign: 'center',
        }}>{step.body}</p>

        <div style={{ display: 'flex', gap: '0.6rem' }}>
          <button
            onClick={handleSkip}
            style={{
              flex: 1, padding: '9px 0', background: '#f1f5f9', color: '#64748b',
              border: '1px solid #e2e8f0', borderRadius: 8, fontWeight: 600,
              cursor: 'pointer', fontSize: '0.75rem', fontFamily: 'Inter, sans-serif',
            }}
          >Skip Tour</button>
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
  );
}
