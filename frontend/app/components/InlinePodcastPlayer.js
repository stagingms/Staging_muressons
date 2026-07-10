'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * In-game podcast player with dual AI hosts and text-to-speech.
 * Awards 1000 bonus points when fully listened.
 * Props: { isOpen, onClose, title, transcript, sessionId, notebookId }
 */
export default function InlinePodcastPlayer({ isOpen, onClose, title, transcript = [], sessionId, notebookId }) {
  const [currentLine, setCurrentLine] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [hasEnded, setHasEnded] = useState(false);
  const [bonusBanner, setBonusBanner] = useState(null);
  const utteranceRef = useRef(null);
  const scrollRef = useRef(null);
  const bonusClaimedRef = useRef(false);

  const SPEAKERS = {
    'Dr. Priya Sharma': { color: '#8b5cf6', avatar: '👩‍🔬', shortName: 'Priya' },
    'Prof. James Walker': { color: '#3b82f6', avatar: '👨‍🏫', shortName: 'James' },
  };

  const getSpeakerInfo = (name) => SPEAKERS[name] || { color: '#6b7280', avatar: '🎙️', shortName: name };

  // Claim podcast bonus
  const claimBonus = useCallback(async () => {
    if (bonusClaimedRef.current || !sessionId || !notebookId) return;
    bonusClaimedRef.current = true;
    try {
      const res = await fetch(`${API_BASE}/api/simulations/${sessionId}/learning-bonus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activity_type: 'podcast_complete', notebook_id: notebookId }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.points_awarded > 0) {
          setBonusBanner({ points: data.points_awarded, message: data.message });
        }
      }
    } catch (e) { console.error('Failed to claim podcast bonus', e); }
  }, [sessionId, notebookId]);

  // Speak a single line via Web Speech API
  const speakLine = useCallback((index) => {
    if (index >= transcript.length) {
      setIsPlaying(false);
      setHasEnded(true);
      claimBonus();
      return;
    }
    
    window.speechSynthesis.cancel();
    const line = transcript[index];
    const utter = new SpeechSynthesisUtterance(line.text);
    utter.rate = speed;
    
    const voices = window.speechSynthesis.getVoices();
    const speaker = getSpeakerInfo(line.speaker);
    if (speaker.shortName === 'Priya' && voices.length > 1) {
      utter.voice = voices.find(v => v.name.includes('Female') || v.name.includes('Samantha') || v.name.includes('Zira')) || voices[1];
    } else if (voices.length > 0) {
      utter.voice = voices.find(v => v.name.includes('Male') || v.name.includes('David') || v.name.includes('Daniel')) || voices[0];
    }
    
    utter.onend = () => {
      const next = index + 1;
      setCurrentLine(next);
      if (next < transcript.length) {
        speakLine(next);
      } else {
        setIsPlaying(false);
        setHasEnded(true);
        claimBonus();
      }
    };
    
    utteranceRef.current = utter;
    setCurrentLine(index);
    window.speechSynthesis.speak(utter);
  }, [transcript, speed, claimBonus]);

  const togglePlay = () => {
    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      setHasEnded(false);
      speakLine(currentLine >= transcript.length ? 0 : currentLine);
    }
  };

  const skipForward = () => {
    const next = Math.min(currentLine + 1, transcript.length - 1);
    window.speechSynthesis.cancel();
    setCurrentLine(next);
    if (isPlaying) speakLine(next);
  };

  const skipBack = () => {
    const prev = Math.max(currentLine - 1, 0);
    window.speechSynthesis.cancel();
    setCurrentLine(prev);
    if (isPlaying) speakLine(prev);
  };

  const restart = () => {
    window.speechSynthesis.cancel();
    setCurrentLine(0);
    setHasEnded(false);
    setIsPlaying(true);
    speakLine(0);
  };

  useEffect(() => {
    if (!isOpen) {
      window.speechSynthesis?.cancel();
      setIsPlaying(false);
    }
    if (isOpen) {
      bonusClaimedRef.current = false;
      setBonusBanner(null);
    }
  }, [isOpen]);

  useEffect(() => {
    if (scrollRef.current) {
      const activeEl = scrollRef.current.querySelector(`[data-line-index="${currentLine}"]`);
      if (activeEl) activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [currentLine]);

  useEffect(() => { window.speechSynthesis?.getVoices(); }, []);

  if (!isOpen) return null;

  const progress = transcript.length > 0 ? ((currentLine) / transcript.length) * 100 : 0;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 10000,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: "'DM Sans', sans-serif",
    }} onClick={onClose}>
      <div style={{
        width: 640, maxHeight: '90vh', borderRadius: 20,
        background: 'linear-gradient(160deg, #1e1b4b, #0f172a)',
        boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={{
          padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.1)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: '0.7rem', color: '#a78bfa', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
              🎧 AI Podcast
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', marginTop: 4 }}>{title}</div>
          </div>
          <button onClick={onClose} style={{
            background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 10,
            width: 36, height: 36, color: '#fff', fontSize: '1.1rem', cursor: 'pointer',
          }}>✕</button>
        </div>

        {/* Bonus banner */}
        {bonusBanner && (
          <div style={{
            padding: '10px 24px', background: 'linear-gradient(90deg, #059669, #10b981)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            animation: 'fadeInUp 0.4s ease',
          }}>
            <span style={{ fontSize: '1.2rem' }}>🏆</span>
            <span style={{ color: '#fff', fontWeight: 700, fontSize: '0.85rem' }}>
              +{bonusBanner.points} Bonus Points!
            </span>
            <span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.75rem' }}>
              Podcast complete
            </span>
          </div>
        )}

        {/* Speakers */}
        <div style={{
          display: 'flex', justifyContent: 'center', gap: 40, padding: '20px 24px',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
        }}>
          {Object.entries(SPEAKERS).map(([name, info]) => {
            const isActive = isPlaying && transcript[currentLine]?.speaker === name;
            return (
              <div key={name} style={{ textAlign: 'center' }}>
                <div style={{
                  width: 64, height: 64, borderRadius: '50%', margin: '0 auto',
                  background: isActive ? info.color : 'rgba(255,255,255,0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '1.8rem', transition: 'background 0.3s, color 0.3s, border-color 0.3s, box-shadow 0.3s, opacity 0.3s, transform 0.3s',
                  boxShadow: isActive ? `0 0 20px ${info.color}80` : 'none',
                  animation: isActive ? 'pulse 1.5s ease-in-out infinite' : 'none',
                }}>
                  {info.avatar}
                </div>
                <div style={{ color: isActive ? '#fff' : '#94a3b8', fontSize: '0.75rem', marginTop: 8, fontWeight: isActive ? 700 : 400 }}>
                  {info.shortName}
                </div>
              </div>
            );
          })}
        </div>

        {/* Transcript */}
        <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '16px 24px', maxHeight: 340 }}>
          {transcript.map((line, i) => {
            const info = getSpeakerInfo(line.speaker);
            const isActive = i === currentLine;
            const isPast = i < currentLine;
            return (
              <div key={i} data-line-index={i}
                onClick={() => { window.speechSynthesis.cancel(); setCurrentLine(i); if (isPlaying) speakLine(i); }}
                style={{
                  display: 'flex', gap: 10, padding: '10px 12px', borderRadius: 10,
                  marginBottom: 6, cursor: 'pointer',
                  background: isActive ? `${info.color}20` : 'transparent',
                  borderLeft: isActive ? `3px solid ${info.color}` : '3px solid transparent',
                  opacity: isPast ? 0.5 : 1, transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                }}>
                <span style={{ fontSize: '1.2rem', flexShrink: 0 }}>{info.avatar}</span>
                <div>
                  <div style={{ fontSize: '0.65rem', color: info.color, fontWeight: 600, marginBottom: 2 }}>{info.shortName}</div>
                  <div style={{ fontSize: '0.82rem', color: '#e2e8f0', lineHeight: 1.5 }}>{line.text}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress Bar */}
        <div style={{ padding: '0 24px' }}>
          <div style={{ height: 3, background: 'rgba(255,255,255,0.1)', borderRadius: 2 }}>
            <div style={{ height: '100%', background: 'linear-gradient(90deg, #8b5cf6, #3b82f6)', borderRadius: 2, width: `${progress}%`, transition: 'width 0.3s' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#64748b', marginTop: 4 }}>
            <span>{currentLine} / {transcript.length} segments</span>
            <span>{Math.round(progress)}%</span>
          </div>
        </div>

        {/* Reward info */}
        {!bonusBanner && !hasEnded && (
          <div style={{ textAlign: 'center', padding: '4px 24px', fontSize: '0.68rem', color: '#64748b' }}>
            🏆 Listen to the full podcast to earn <strong style={{ color: '#10b981' }}>+1,000 bonus points</strong>
          </div>
        )}

        {/* Controls */}
        <div style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
          <button onClick={skipBack} style={{
            width: 40, height: 40, borderRadius: '50%', border: '1px solid rgba(255,255,255,0.2)',
            background: 'transparent', color: '#fff', fontSize: '1rem', cursor: 'pointer',
          }}>⏮</button>
          <button onClick={hasEnded ? restart : togglePlay} style={{
            width: 56, height: 56, borderRadius: '50%', border: 'none',
            background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
            color: '#fff', fontSize: '1.3rem', cursor: 'pointer',
            boxShadow: '0 4px 20px rgba(139,92,246,0.4)',
          }}>
            {hasEnded ? '🔄' : isPlaying ? '⏸' : '▶'}
          </button>
          <button onClick={skipForward} style={{
            width: 40, height: 40, borderRadius: '50%', border: '1px solid rgba(255,255,255,0.2)',
            background: 'transparent', color: '#fff', fontSize: '1rem', cursor: 'pointer',
          }}>⏭</button>
          <div style={{ marginLeft: 20 }}>
            <button onClick={() => setSpeed(s => s === 2 ? 1 : s + 0.5)} style={{
              padding: '4px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.2)',
              background: 'rgba(255,255,255,0.05)', color: '#a78bfa', fontSize: '0.75rem',
              fontWeight: 600, cursor: 'pointer',
            }}>{speed}x</button>
          </div>
        </div>
      </div>
    </div>
  );
}
