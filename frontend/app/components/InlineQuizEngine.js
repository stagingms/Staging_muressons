'use client';

import { useState, useCallback, useEffect } from 'react';
import { playerIdHeader } from '../hooks/useSimulation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * In-game quiz engine with MCQ, scoring, retakes, and bonus points.
 * - Retakes allowed to improve score
 * - After 2nd attempt, correct answers are revealed
 * - Tiered bonus: 60-80%=1500, 80-90%=2000, 90-100%=3000
 * Props: { isOpen, onClose, title, questions, sessionId, notebookId }
 */
export default function InlineQuizEngine({ isOpen, onClose, title, questions = [], sessionId, notebookId, difficulty = 'medium', loading = false, onQuizComplete = null }) {
  const DIFFICULTY_BADGES = { easy: { label: 'Easy', icon: '🟢', color: '#22c55e' }, medium: { label: 'Medium', icon: '🟡', color: '#eab308' }, hard: { label: 'Hard', icon: '🔴', color: '#ef4444' } };
  const diffBadge = DIFFICULTY_BADGES[difficulty] || DIFFICULTY_BADGES.medium;
  const [currentQ, setCurrentQ] = useState(0);
  const [selected, setSelected] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);
  const [answers, setAnswers] = useState([]);
  const [attemptNumber, setAttemptNumber] = useState(1);
  const [showCorrectAnswers, setShowCorrectAnswers] = useState(false);
  const [bonusResult, setBonusResult] = useState(null);

  // Reset state when opened
  useEffect(() => {
    if (isOpen) {
      setCurrentQ(0);
      setSelected(null);
      setShowExplanation(false);
      setScore(0);
      setFinished(false);
      setAnswers([]);
      setBonusResult(null);
    }
  }, [isOpen]);

  const handleSelect = useCallback((optionIndex) => {
    if (showExplanation) return;
    setSelected(optionIndex);
    setShowExplanation(true);
    const isCorrect = optionIndex === questions[currentQ].correct;
    if (isCorrect) setScore(s => s + 1);
    setAnswers(prev => [...prev, { questionIndex: currentQ, selected: optionIndex, correct: isCorrect }]);
  }, [currentQ, showExplanation, questions]);

  // Claim quiz bonus
  const claimQuizBonus = useCallback(async (finalScore) => {
    if (!sessionId || !notebookId) return;
    const pct = Math.round((finalScore / questions.length) * 100);
    try {
      const res = await fetch(`${API_BASE}/api/simulations/${sessionId}/learning-bonus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...playerIdHeader() },
        body: JSON.stringify({ activity_type: 'quiz_complete', notebook_id: notebookId, score_percent: pct }),
      });
      if (res.ok) {
        const data = await res.json();
        setBonusResult(data);
        setAttemptNumber(data.attempt || 1);
        if (data.show_answers) setShowCorrectAnswers(true);
        // Notify the parent so it can refresh the dashboard — the mandatory-quiz
        // gate (globalState.quiz_gate) flips to unblocked once an attempt is
        // recorded, letting the player commit their decisions.
        try { onQuizComplete && onQuizComplete(data); } catch { /* non-critical */ }
      }
    } catch (e) { console.error('Failed to claim quiz bonus', e); }
  }, [sessionId, notebookId, questions.length, onQuizComplete]);

  const nextQuestion = () => {
    if (currentQ + 1 >= questions.length) {
      setFinished(true);
      claimQuizBonus(score + (selected === questions[currentQ]?.correct ? 0 : 0)); // score already updated
    } else {
      setCurrentQ(q => q + 1);
      setSelected(null);
      setShowExplanation(false);
    }
  };

  // Score is updated in handleSelect before nextQuestion runs, but we need final score
  useEffect(() => {
    if (finished && !bonusResult) {
      claimQuizBonus(score);
    }
  }, [finished]);

  const restart = () => {
    setCurrentQ(0);
    setSelected(null);
    setShowExplanation(false);
    setScore(0);
    setFinished(false);
    setAnswers([]);
    setBonusResult(null);
    setAttemptNumber(prev => prev + 1);
  };

  if (!isOpen) return null;

  // Loading state
  if (loading || questions.length === 0) {
    return (
      <div style={{
        position: 'fixed', inset: 0, zIndex: 10000,
        background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: "'DM Sans', sans-serif",
      }} onClick={onClose}>
        <div style={{
          width: 400, borderRadius: 20, background: '#fff',
          boxShadow: '0 25px 60px rgba(0,0,0,0.25)',
          padding: '48px 32px', textAlign: 'center',
        }} onClick={e => e.stopPropagation()}>
          <div style={{ fontSize: '2rem', marginBottom: 12, animation: 'spin 1s linear infinite' }}>🧩</div>
          <div style={{ fontSize: '0.95rem', color: '#4f46e5', fontWeight: 600 }}>Generating Quiz Questions...</div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
            Difficulty: {diffBadge.icon} {diffBadge.label}
          </div>
          <button onClick={onClose} style={{
            marginTop: 20, padding: '8px 20px', borderRadius: 10,
            border: '1px solid #e2e8f0', background: '#fff', color: '#64748b',
            cursor: 'pointer', fontSize: '0.8rem',
          }}>Cancel</button>
        </div>
      </div>
    );
  }

  const percent = Math.round((score / questions.length) * 100);
  const q = questions[currentQ];

  // Tier label for display
  const getTierInfo = (pct) => {
    if (pct >= 90) return { tier: '🏆 Gold', points: 3000, color: '#f59e0b' };
    if (pct >= 80) return { tier: '🥈 Silver', points: 2000, color: '#94a3b8' };
    if (pct >= 60) return { tier: '🥉 Bronze', points: 1500, color: '#cd7f32' };
    return { tier: '📚 Try Again', points: 0, color: '#64748b' };
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 10000,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: "'DM Sans', sans-serif",
    }} onClick={onClose}>
      <div style={{
        width: 580, maxHeight: '90vh', borderRadius: 20,
        background: '#fff', boxShadow: '0 25px 60px rgba(0,0,0,0.25)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={{
          padding: '18px 24px',
          background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: 'var(--type-caption)', color: 'rgba(255,255,255,0.7)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
              🧩 Knowledge Quiz {attemptNumber > 1 ? `· Attempt ${attemptNumber}` : ''}
              <span style={{
                background: diffBadge.color, borderRadius: 8, padding: '2px 8px',
                fontSize: 'var(--type-caption)', fontWeight: 700, color: '#fff',
              }}>{diffBadge.icon} {diffBadge.label}</span>
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginTop: 2 }}>{title}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              background: 'rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 14px',
              fontSize: '0.8rem', fontWeight: 700, color: '#fff',
            }}>
              {score}/{questions.length}
            </div>
            <button onClick={onClose} style={{
              background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: 10,
              width: 32, height: 32, color: '#fff', fontSize: '1rem', cursor: 'pointer',
            }}>✕</button>
          </div>
        </div>

        {/* Progress bar */}
        <div style={{ height: 4, background: '#e2e8f0' }}>
          <div style={{
            height: '100%', borderRadius: 2,
            background: 'linear-gradient(90deg, #4f46e5, #7c3aed)',
            width: `${finished ? 100 : ((currentQ) / questions.length) * 100}%`,
            transition: 'width 0.4s ease',
          }} />
        </div>

        {finished ? (
          /* ═══ Results Screen ═══ */
          <div style={{ padding: '28px 32px', textAlign: 'center', overflowY: 'auto', maxHeight: '70vh' }}>
            {/* Score celebration */}
            <div style={{ fontSize: '3rem', marginBottom: 10 }}>
              {percent >= 90 ? '🎉' : percent >= 80 ? '🏆' : percent >= 60 ? '👍' : '📚'}
            </div>
            <h2 style={{ fontSize: '1.4rem', margin: '0 0 8px', color: '#1e293b' }}>
              {percent >= 90 ? 'Outstanding!' : percent >= 80 ? 'Excellent!' : percent >= 60 ? 'Good effort!' : 'Keep studying!'}
            </h2>
            <p style={{ fontSize: '0.9rem', color: '#64748b', margin: '0 0 12px' }}>
              You scored <strong style={{ color: '#4f46e5' }}>{score}/{questions.length}</strong> ({percent}%)
            </p>

            {/* Bonus points */}
            {bonusResult && (
              <div style={{
                padding: '12px 16px', borderRadius: 12, marginBottom: 16,
                background: bonusResult.points_awarded > 0 ? 'linear-gradient(135deg, #f0fdf4, #ecfdf5)' : '#f8fafc',
                border: `1px solid ${bonusResult.points_awarded > 0 ? '#86efac' : '#e2e8f0'}`,
              }}>
                {bonusResult.points_awarded > 0 ? (
                  <>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#059669' }}>
                      🏆 +{bonusResult.points_awarded} Bonus Points!
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 2 }}>
                      {bonusResult.message}
                    </div>
                  </>
                ) : (
                  <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    {bonusResult.message}
                  </div>
                )}
              </div>
            )}

            {/* Bonus tier table */}
            <div style={{
              background: '#f8fafc', borderRadius: 10, padding: '12px 16px', marginBottom: 16,
              border: '1px solid #e2e8f0', textAlign: 'left',
            }}>
              <div style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: '#94a3b8', marginBottom: 8, textTransform: 'uppercase' }}>
                Bonus Point Tiers
              </div>
              {[
                { label: '90-100%', pts: '3,000', emoji: '🏆', active: percent >= 90 },
                { label: '80-89%', pts: '2,000', emoji: '🥈', active: percent >= 80 && percent < 90 },
                { label: '60-79%', pts: '1,500', emoji: '🥉', active: percent >= 60 && percent < 80 },
                { label: 'Below 60%', pts: '0', emoji: '📚', active: percent < 60 },
              ].map((t, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', padding: '4px 8px',
                  borderRadius: 6, marginBottom: 2, fontSize: '0.78rem',
                  background: t.active ? '#eef2ff' : 'transparent',
                  fontWeight: t.active ? 700 : 400,
                  color: t.active ? '#4f46e5' : '#64748b',
                }}>
                  <span>{t.emoji} {t.label}</span>
                  <span>{t.pts} pts</span>
                </div>
              ))}
            </div>

            {/* Answer summary */}
            <div style={{ textAlign: 'left', marginBottom: 20 }}>
              {answers.map((a, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 12px',
                  borderRadius: 8, marginBottom: 4,
                  background: a.correct ? '#f0fdf4' : '#fef2f2',
                }}>
                  <span style={{ fontSize: '1rem', flexShrink: 0 }}>{a.correct ? '✅' : '❌'}</span>
                  <div style={{ flex: 1 }}>
                    <span style={{ fontSize: '0.8rem', color: '#334155' }}>
                      Q{i + 1}: {questions[a.questionIndex].question}
                    </span>
                    {/* Show correct answer after 2nd attempt */}
                    {showCorrectAnswers && !a.correct && (
                      <div style={{
                        fontSize: '0.75rem', color: '#059669', marginTop: 4,
                        padding: '4px 8px', background: '#ecfdf5', borderRadius: 6,
                      }}>
                        ✓ Correct answer: {questions[a.questionIndex].options[questions[a.questionIndex].correct]}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Show all correct answers after attempt 2 */}
            {showCorrectAnswers && (
              <div style={{
                textAlign: 'left', padding: '14px 16px', borderRadius: 12, marginBottom: 16,
                background: '#fffbeb', border: '1px solid #fde68a',
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#92400e', marginBottom: 8 }}>
                  📖 Answer Key (Revealed after Attempt 2)
                </div>
                {questions.map((q, i) => (
                  <div key={i} style={{ fontSize: '0.78rem', color: '#334155', marginBottom: 6, lineHeight: 1.4 }}>
                    <strong>Q{i + 1}:</strong> {q.question}<br />
                    <span style={{ color: '#059669', fontWeight: 600 }}>→ {q.options[q.correct]}</span>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
              {bonusResult?.status !== 'max_attempts_reached' && bonusResult?.attempts_remaining > 0 ? (
                <button onClick={restart} style={{
                  padding: '10px 24px', borderRadius: 12, border: '1px solid #e2e8f0',
                  background: '#fff', color: '#4f46e5', fontWeight: 600, cursor: 'pointer',
                  fontSize: '0.85rem',
                }}>🔄 Try Again ({bonusResult?.attempts_remaining || 1} left)</button>
              ) : (
                <div style={{
                  padding: '8px 16px', borderRadius: 10, background: '#fef3c7',
                  border: '1px solid #fde68a', fontSize: '0.8rem', color: '#92400e', fontWeight: 600,
                }}>🏁 All attempts used — final score locked</div>
              )}
              <button onClick={onClose} style={{
                padding: '10px 24px', borderRadius: 12, border: 'none',
                background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                color: '#fff', fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem',
              }}>✓ Done</button>
            </div>
          </div>
        ) : (
          /* ═══ Question Screen ═══ */
          <div style={{ padding: '28px 28px 20px' }}>
            <div style={{
              fontSize: 'var(--type-caption)', color: '#94a3b8', fontWeight: 600,
              textTransform: 'uppercase', marginBottom: 10, letterSpacing: 0.5,
            }}>
              Question {currentQ + 1} of {questions.length}
            </div>

            <h3 style={{
              fontSize: '1.05rem', fontWeight: 600, color: '#1e293b',
              lineHeight: 1.5, margin: '0 0 20px',
            }}>
              {q.question}
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
              {q.options.map((opt, i) => {
                const isSelected = selected === i;
                const isCorrect = i === q.correct;
                const showResult = showExplanation;
                
                let bg = '#f8fafc';
                let border = '1px solid #e2e8f0';
                let textColor = '#334155';
                
                if (showResult && isCorrect) {
                  bg = '#f0fdf4'; border = '2px solid #22c55e'; textColor = '#166534';
                } else if (showResult && isSelected && !isCorrect) {
                  bg = '#fef2f2'; border = '2px solid #ef4444'; textColor = '#991b1b';
                } else if (isSelected) {
                  border = '2px solid #4f46e5'; bg = '#eef2ff';
                }

                return (
                  <button key={i} onClick={() => handleSelect(i)} style={{
                    padding: '12px 16px', borderRadius: 12,
                    border, background: bg, color: textColor,
                    textAlign: 'left', cursor: showExplanation ? 'default' : 'pointer',
                    fontSize: '0.85rem', fontWeight: 500,
                    display: 'flex', alignItems: 'center', gap: 10,
                    transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                  }}>
                    <span style={{
                      width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: showResult && isCorrect ? '#22c55e' : showResult && isSelected ? '#ef4444' : '#e2e8f0',
                      color: showResult ? '#fff' : '#64748b',
                      fontSize: 'var(--type-caption)', fontWeight: 700,
                    }}>
                      {showResult && isCorrect ? '✓' : showResult && isSelected ? '✗' : String.fromCharCode(65 + i)}
                    </span>
                    {opt}
                  </button>
                );
              })}
            </div>

            {showExplanation && (
              <div style={{
                padding: '14px 16px', borderRadius: 12, marginBottom: 16,
                background: selected === q.correct ? '#f0fdf4' : '#fffbeb',
                border: `1px solid ${selected === q.correct ? '#bbf7d0' : '#fde68a'}`,
              }}>
                <div style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: selected === q.correct ? '#166534' : '#92400e', marginBottom: 4 }}>
                  {selected === q.correct ? '✅ Correct!' : '💡 Explanation'}
                </div>
                <div style={{ fontSize: '0.82rem', color: '#334155', lineHeight: 1.5 }}>
                  {q.explanation}
                </div>
              </div>
            )}

            {/* Bonus incentive */}
            {!showExplanation && currentQ === 0 && (
              <div style={{ textAlign: 'center', fontSize: 'var(--type-caption)', color: '#94a3b8', marginBottom: 8 }}>
                🏆 Score 60%+ for <strong style={{ color: '#4f46e5' }}>up to 3,000 bonus points</strong>
              </div>
            )}

            {showExplanation && (
              <button onClick={nextQuestion} style={{
                width: '100%', padding: '12px', borderRadius: 12, border: 'none',
                background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                color: '#fff', fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem',
              }}>
                {currentQ + 1 >= questions.length ? '📊 View Results' : 'Next Question →'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
