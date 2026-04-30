'use client';

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import styles from './CEOInterview.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * CEOInterview — Post-Game Competency Assessment
 *
 * Renders the CEO interview experience after R10 results:
 * 1. CEO introduction (avatar + voice)
 * 2. Sequential Q&A (5 questions, text or voice input)
 * 3. Assessment submission → spider diagram + narrative feedback
 *
 * Props:
 *  - sessionId: string
 *  - onClose: () => void — dismiss interview
 *  - onComplete: (results) => void — assessment done
 */

const PHASE = {
  LOADING: 'loading',
  INTRO: 'intro',
  QUESTIONS: 'questions',
  SUBMITTING: 'submitting',
  RESULTS: 'results',
  ERROR: 'error',
};

/**
 * DimensionCard — Expandable score breakdown for a single competency dimension.
 * Shows final blended score, split Performance/Interview bars, and the rationale.
 */
function DimensionCard({ dimension, score, dataScore, responseScore, rationale, barColor, dataBarColor, respBarColor }) {
  const [expanded, setExpanded] = useState(false);
  const d = dimension;

  // Generate interview score rationale (rule-based, mirroring data rationale approach)
  const getInterviewRationale = (dimId, respScore) => {
    if (respScore >= 8) return 'Your interview responses demonstrated deep, nuanced understanding with specific examples and sophisticated analysis of trade-offs.';
    if (respScore >= 6) return 'Your responses showed good awareness of this dimension with reasonable examples, though deeper analysis would have strengthened your score.';
    if (respScore >= 4) return 'Your responses touched on this dimension but lacked specificity or depth. More concrete examples from your simulation experience would have improved this score.';
    return 'This dimension was not well-addressed in your interview responses. Future interviews should explicitly connect your decisions to this competency area.';
  };

  // Blend explanation
  const blendExplainer = `Final Score = (Performance ${dataScore.toFixed(1)} × 50%) + (Interview ${responseScore.toFixed(1)} × 50%) = ${score.toFixed(1)}`;

  return (
    <div className={styles.dimCard}>
      {/* Clickable Header */}
      <button
        className={styles.dimCardHeader}
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <div className={styles.dimCardLeft}>
          <span className={styles.dimRowLabel}>{d.label}</span>
          <span className={styles.dimCardDesc}>{d.description}</span>
        </div>
        <div className={styles.dimCardRight}>
          <span className={styles.dimRowScore} style={{ color: barColor }}>
            {score.toFixed(1)}
          </span>
          <span className={styles.dimExpandIcon} data-expanded={expanded}>
            ▾
          </span>
        </div>
      </button>

      {/* Main bar */}
      <div className={styles.dimBarTrack}>
        <div
          className={styles.dimBarFill}
          style={{ width: `${(score / 10) * 100}%`, background: barColor }}
        />
      </div>

      {/* Compact sub-scores (always visible) */}
      <div className={styles.dimRowSub}>
        <span style={{ color: dataBarColor }}>📊 Performance: {dataScore.toFixed(1)}</span>
        <span style={{ color: respBarColor }}>🎤 Interview: {responseScore.toFixed(1)}</span>
      </div>

      {/* Expanded Detail Panel */}
      {expanded && (
        <div className={styles.dimExpanded}>
          {/* Blend Formula */}
          <div className={styles.blendFormula}>
            <span className={styles.blendLabel}>⚖️ Score Composition</span>
            <span className={styles.blendValue}>{blendExplainer}</span>
          </div>

          {/* Split bars with labels */}
          <div className={styles.splitBars}>
            <div className={styles.splitBar}>
              <div className={styles.splitBarHeader}>
                <span className={styles.splitBarLabel}>📊 Performance Score</span>
                <span className={styles.splitBarScore} style={{ color: dataBarColor }}>{dataScore.toFixed(1)}/10</span>
              </div>
              <div className={styles.splitBarTrack}>
                <div
                  className={styles.splitBarFill}
                  style={{ width: `${(dataScore / 10) * 100}%`, background: dataBarColor }}
                />
              </div>
              {rationale && (
                <div className={styles.rationaleText}>{rationale}</div>
              )}
            </div>

            <div className={styles.splitBar}>
              <div className={styles.splitBarHeader}>
                <span className={styles.splitBarLabel}>🎤 Interview Score</span>
                <span className={styles.splitBarScore} style={{ color: respBarColor }}>{responseScore.toFixed(1)}/10</span>
              </div>
              <div className={styles.splitBarTrack}>
                <div
                  className={styles.splitBarFill}
                  style={{ width: `${(responseScore / 10) * 100}%`, background: respBarColor }}
                />
              </div>
              <div className={styles.rationaleText}>
                {getInterviewRationale(d.id, responseScore)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CEOInterview({ sessionId, onClose, onComplete }) {
  const [phase, setPhase] = useState(PHASE.LOADING);
  const [questions, setQuestions] = useState([]);
  const [persona, setPersona] = useState(null);
  const [dimensions, setDimensions] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [responses, setResponses] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTimer, setRecordingTimer] = useState(120); // 2 minutes
  const [inputMode, setInputMode] = useState('text'); // 'text' | 'voice'
  const textareaRef = useRef(null);
  const audioRef = useRef(null);
  const audioCacheRef = useRef({});
  const recognitionRef = useRef(null);
  const timerRef = useRef(null);

  // ── Fetch questions on mount ──
  useEffect(() => {
    if (!sessionId) return;
    (async () => {
      try {
        const res = await fetch(`${API}/api/simulations/${sessionId}/ceo-interview/questions`);
        if (!res.ok) {
          if (res.status === 403) {
            setError('CEO Interview is not enabled for this cohort.');
          } else {
            setError('Failed to load interview questions.');
          }
          setPhase(PHASE.ERROR);
          return;
        }
        const data = await res.json();
        setQuestions(data.questions || []);
        setPersona(data.persona || {});
        setDimensions(data.dimensions || []);
        setResponses(new Array((data.questions || []).length).fill(''));
        setPhase(PHASE.INTRO);
      } catch (e) {
        setError('Network error loading interview.');
        setPhase(PHASE.ERROR);
      }
    })();
  }, [sessionId]);

  // ── Auto-focus textarea on question change ──
  useEffect(() => {
    if (phase === PHASE.QUESTIONS && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [phase, currentQ]);

  // ── TTS Audio Helper ──
  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsPlaying(false);
  }, []);

  const speakText = useCallback(async (text, cacheKey) => {
    if (!text || !sessionId) return;
    stopAudio();

    // Check cache first
    if (audioCacheRef.current[cacheKey]) {
      const audio = new Audio(`data:audio/mpeg;base64,${audioCacheRef.current[cacheKey]}`);
      audioRef.current = audio;
      setIsPlaying(true);
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => setIsPlaying(false);
      audio.play().catch(() => setIsPlaying(false));
      return;
    }

    try {
      const res = await fetch(`${API}/api/simulations/${sessionId}/ceo-interview/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.audio_b64) {
          audioCacheRef.current[cacheKey] = data.audio_b64;
          const audio = new Audio(`data:audio/mpeg;base64,${data.audio_b64}`);
          audioRef.current = audio;
          setIsPlaying(true);
          audio.onended = () => setIsPlaying(false);
          audio.onerror = () => setIsPlaying(false);
          audio.play().catch(() => setIsPlaying(false));
        }
      }
    } catch {
      // TTS unavailable — silent fallback, text is still displayed
    }
  }, [sessionId, stopAudio]);

  // ── Auto-speak intro on phase transition ──
  useEffect(() => {
    if (phase === PHASE.INTRO && persona?.intro_text) {
      speakText(persona.intro_text, 'intro');
    }
    return () => stopAudio();
  }, [phase, persona?.intro_text]);

  // ── Auto-speak each question ──
  useEffect(() => {
    if (phase === PHASE.QUESTIONS && questions[currentQ]) {
      const q = questions[currentQ];
      const fullText = q.ceo_intro
        ? `${q.ceo_intro} ${q.text}`
        : q.text;
      speakText(fullText, `q${currentQ}`);
    }
    return () => stopAudio();
  }, [phase, currentQ, questions]);

  // ── Auto-speak outro on results ──
  useEffect(() => {
    if (phase === PHASE.RESULTS && persona?.outro_text) {
      speakText(persona.outro_text, 'outro');
    }
    return () => stopAudio();
  }, [phase, persona?.outro_text]);

  // ── Cleanup on unmount ──
  useEffect(() => {
    return () => { stopAudio(); stopRecording(); };
  }, [stopAudio]);

  // ── Speech Recognition (Voice Input) ──
  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsRecording(false);
  }, []);

  const startRecording = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    stopRecording();
    setRecordingTimer(120); // Reset to 2 minutes

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    let finalTranscript = currentAnswer || '';

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += (finalTranscript ? ' ' : '') + transcript;
        } else {
          interim += transcript;
        }
      }
      setCurrentAnswer(finalTranscript + (interim ? ' ' + interim : ''));
    };

    recognition.onerror = (e) => {
      if (e.error !== 'aborted') {
        console.warn('Speech recognition error:', e.error);
      }
      stopRecording();
    };

    recognition.onend = () => {
      // Recognition ended naturally — might need restart for continuous mode
      if (recognitionRef.current) {
        try { recognition.start(); } catch { stopRecording(); }
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);

    // Start 2-minute countdown
    timerRef.current = setInterval(() => {
      setRecordingTimer(prev => {
        if (prev <= 1) {
          stopRecording();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [currentAnswer, stopRecording]);

  // Reset recording when question changes
  useEffect(() => {
    stopRecording();
    setRecordingTimer(120);
  }, [currentQ, stopRecording]);

  // ── Submit responses ──
  const handleSubmit = useCallback(async () => {
    setPhase(PHASE.SUBMITTING);
    try {
      const res = await fetch(`${API}/api/simulations/${sessionId}/ceo-interview/assess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses }),
      });
      if (!res.ok) throw new Error('Assessment failed');
      const data = await res.json();
      setResults(data);
      setPhase(PHASE.RESULTS);
      onComplete?.(data);
    } catch (e) {
      setError('Failed to submit assessment. Please try again.');
      setPhase(PHASE.ERROR);
    }
  }, [sessionId, responses, onComplete]);

  const handleNextQuestion = useCallback(() => {
    const updated = [...responses];
    updated[currentQ] = currentAnswer;
    setResponses(updated);
    setCurrentAnswer('');

    if (currentQ < questions.length - 1) {
      setCurrentQ(currentQ + 1);
    } else {
      // All questions answered — submit
      const final = [...updated];
      setResponses(final);
      setTimeout(() => handleSubmit(), 100);
    }
  }, [currentQ, currentAnswer, responses, questions, handleSubmit]);

  // ── Radar Chart (SVG) ──
  const RadarChart = useMemo(() => {
    if (!results?.final_scores || !dimensions.length) return null;

    const size = 280;
    const cx = size / 2;
    const cy = size / 2;
    const maxR = 110;
    const n = dimensions.length;
    const angleStep = (2 * Math.PI) / n;

    const getPoint = (i, value) => {
      const angle = -Math.PI / 2 + i * angleStep;
      const r = (value / 10) * maxR;
      return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
    };

    // Grid rings
    const rings = [2, 4, 6, 8, 10];
    const gridLines = rings.map(ring => {
      const points = dimensions.map((_, i) => getPoint(i, ring));
      return points.map(p => `${p.x},${p.y}`).join(' ');
    });

    // Data polygon
    const dataPoints = dimensions.map((d, i) =>
      getPoint(i, results.final_scores[d.id] || 0)
    );
    const dataPolygon = dataPoints.map(p => `${p.x},${p.y}`).join(' ');

    // Labels
    const labels = dimensions.map((d, i) => {
      const angle = -Math.PI / 2 + i * angleStep;
      const lr = maxR + 28;
      return {
        x: cx + lr * Math.cos(angle),
        y: cy + lr * Math.sin(angle),
        label: d.label.split(' '),
        score: (results.final_scores[d.id] || 0).toFixed(1),
      };
    });

    return (
      <svg viewBox={`0 0 ${size} ${size}`} className={styles.radar}>
        {/* Grid */}
        {gridLines.map((pts, i) => (
          <polygon
            key={i}
            points={pts}
            fill="none"
            stroke="rgba(148,163,184,0.15)"
            strokeWidth="0.5"
          />
        ))}
        {/* Axes */}
        {dimensions.map((_, i) => {
          const p = getPoint(i, 10);
          return (
            <line
              key={i}
              x1={cx} y1={cy} x2={p.x} y2={p.y}
              stroke="rgba(148,163,184,0.1)"
              strokeWidth="0.5"
            />
          );
        })}
        {/* Data polygon */}
        <polygon
          points={dataPolygon}
          fill="rgba(99,102,241,0.2)"
          stroke="#818cf8"
          strokeWidth="2"
          className={styles.radarPoly}
        />
        {/* Data points */}
        {dataPoints.map((p, i) => (
          <circle
            key={i}
            cx={p.x} cy={p.y} r="4"
            fill="#818cf8"
            stroke="#0f172a"
            strokeWidth="2"
          />
        ))}
        {/* Labels */}
        {labels.map((l, i) => (
          <text
            key={i}
            x={l.x} y={l.y}
            textAnchor="middle"
            dominantBaseline="central"
            className={styles.radarLabel}
          >
            {l.label.map((word, wi) => (
              <tspan key={wi} x={l.x} dy={wi === 0 ? 0 : 11}>{word}</tspan>
            ))}
            <tspan x={l.x} dy={12} className={styles.radarScore}>{l.score}</tspan>
          </text>
        ))}
      </svg>
    );
  }, [results, dimensions]);

  // ═══════════════════════════════════════════════════════════
  //  RENDER
  // ═══════════════════════════════════════════════════════════

  // ── LOADING ──
  if (phase === PHASE.LOADING) {
    return (
      <div className={styles.overlay}>
        <div className={styles.container}>
          <div className={styles.loadingPulse}>
            <span className={styles.ceoAvatar}>👩‍💼</span>
            <div className={styles.loadingText}>Preparing your interview…</div>
          </div>
        </div>
      </div>
    );
  }

  // ── ERROR ──
  if (phase === PHASE.ERROR) {
    return (
      <div className={styles.overlay}>
        <div className={styles.container}>
          <div className={styles.errorState}>
            <span style={{ fontSize: '2rem' }}>⚠️</span>
            <div>{error}</div>
            <button className={styles.btnSecondary} onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    );
  }

  // ── INTRO ──
  if (phase === PHASE.INTRO) {
    return (
      <div className={styles.overlay}>
        <div className={styles.container}>
          <div className={styles.introSection}>
            <div className={styles.ceoCard}>
              <span className={styles.ceoAvatarLarge}>{persona?.avatar || '👩‍💼'}</span>
              <div className={styles.ceoInfo}>
                <div className={styles.ceoName}>{persona?.name || 'CEO'}</div>
                <div className={styles.ceoTitle}>{persona?.title || ''}</div>
              </div>
            </div>
            <div className={styles.introText}>
              {persona?.intro_text || 'Let\'s discuss your strategic journey.'}
            </div>
            {isPlaying && (
              <div className={styles.audioIndicator}>
                <span className={styles.soundWave}>🔊</span>
                <span>Speaking…</span>
              </div>
            )}
            <div className={styles.introDimensions}>
              <div className={styles.dimTitle}>You'll be assessed on {dimensions.length} dimensions:</div>
              <div className={styles.dimGrid}>
                {dimensions.map(d => (
                  <div key={d.id} className={styles.dimChip}>
                    <span className={styles.dimLabel}>{d.label}</span>
                    <span className={styles.dimDesc}>{d.description}</span>
                  </div>
                ))}
              </div>
            </div>
            <button
              className={styles.btnPrimary}
              onClick={() => setPhase(PHASE.QUESTIONS)}
            >
              🎤 Begin Interview ({questions.length} Questions)
            </button>
            <button
              className={styles.btnGhost}
              onClick={onClose}
            >
              Skip Interview
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── QUESTIONS ──
  if (phase === PHASE.QUESTIONS) {
    const q = questions[currentQ];
    const isLastQ = currentQ === questions.length - 1;
    const canProceed = currentAnswer.trim().length >= 20;

    return (
      <div className={styles.overlay}>
        <div className={styles.container}>
          <div className={styles.questionSection}>
            {/* Progress */}
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${((currentQ + 1) / questions.length) * 100}%` }}
              />
            </div>
            <div className={styles.progressLabel}>
              Question {currentQ + 1} of {questions.length}
            </div>

            {/* CEO prompt */}
            <div className={styles.ceoBubble}>
              <span className={styles.ceoAvatarSmall}>{persona?.avatar || '👩‍💼'}</span>
              <div className={styles.bubbleContent}>
                {q?.ceo_intro && (
                  <div className={styles.ceoIntro}>{q.ceo_intro}</div>
                )}
                <div className={styles.questionText}>{q?.text || ''}</div>
                <div className={styles.questionDimensions}>
                  {(q?.dimensions || []).map(d => (
                    <span key={d} className={styles.dimTag}>{d.replace(/_/g, ' ')}</span>
                  ))}
                </div>
              </div>
              {isPlaying && (
                <div className={styles.audioIndicator} style={{ marginTop: '0.3rem' }}>
                  <span className={styles.soundWave}>🔊</span>
                  <span>Speaking…</span>
                </div>
              )}
            </div>

            {/* Response input */}
            <div className={styles.responseArea}>
              {/* Input mode toggle */}
              <div className={styles.inputModeToggle}>
                <button
                  className={`${styles.modeBtn} ${inputMode === 'text' ? styles.modeBtnActive : ''}`}
                  onClick={() => { setInputMode('text'); stopRecording(); }}
                >
                  ⌨️ Type
                </button>
                <button
                  className={`${styles.modeBtn} ${inputMode === 'voice' ? styles.modeBtnActive : ''}`}
                  onClick={() => setInputMode('voice')}
                  disabled={typeof window !== 'undefined' && !('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)}
                  title={typeof window !== 'undefined' && !('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) ? 'Voice input not supported in this browser' : 'Switch to voice input'}
                >
                  🎙️ Speak
                </button>
              </div>

              {inputMode === 'text' ? (
                <textarea
                  ref={textareaRef}
                  className={styles.responseInput}
                  value={currentAnswer}
                  onChange={e => setCurrentAnswer(e.target.value)}
                  placeholder="Type your response here… (minimum 20 characters)"
                  rows={5}
                />
              ) : (
                <div className={styles.voiceInputArea}>
                  <div className={styles.voiceTranscript}>
                    {currentAnswer || (
                      <span style={{ color: '#475569', fontStyle: 'italic' }}>
                        {isRecording ? 'Listening… speak your response' : 'Press the microphone to start recording'}
                      </span>
                    )}
                  </div>
                  <div className={styles.voiceControls}>
                    <button
                      className={`${styles.micBtn} ${isRecording ? styles.micBtnActive : ''}`}
                      onClick={() => {
                        if (isRecording) {
                          stopRecording();
                        } else {
                          startRecording();
                        }
                      }}
                    >
                      {isRecording ? '⏹️ Stop' : '🎙️ Record'}
                    </button>
                    {isRecording && (
                      <div className={styles.timerDisplay}>
                        <span className={styles.recordDot}>●</span>
                        {Math.floor(recordingTimer / 60)}:{String(recordingTimer % 60).padStart(2, '0')}
                        <span style={{ fontSize: '0.55rem', color: '#64748b', marginLeft: 4 }}>remaining</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className={styles.responseFooter}>
                <span className={styles.charCount}>
                  {currentAnswer.length} chars
                  {inputMode === 'voice' && isRecording && (
                    <span style={{ color: '#ef4444', marginLeft: 6 }}>
                      🔴 Recording
                    </span>
                  )}
                  {!canProceed && currentAnswer.length > 0 && (
                    <span style={{ color: '#f59e0b', marginLeft: 6 }}>
                      ({20 - currentAnswer.trim().length} more needed)
                    </span>
                  )}
                </span>
                <button
                  className={styles.btnPrimary}
                  disabled={!canProceed}
                  onClick={() => { stopRecording(); handleNextQuestion(); }}
                >
                  {isLastQ ? '✅ Submit All Responses' : `Next Question →`}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── SUBMITTING ──
  if (phase === PHASE.SUBMITTING) {
    return (
      <div className={styles.overlay}>
        <div className={styles.container}>
          <div className={styles.loadingPulse}>
            <span className={styles.ceoAvatar}>{persona?.avatar || '👩‍💼'}</span>
            <div className={styles.loadingText}>
              {persona?.name || 'CEO'} is reviewing your responses…
            </div>
            <div className={styles.loadingSubtext}>Generating competency assessment</div>
          </div>
        </div>
      </div>
    );
  }

  // ── RESULTS ──
  if (phase === PHASE.RESULTS && results) {
    const feedback = results.feedback || {};
    const scoreRationale = results.score_rationale || {};
    const avgScore = dimensions.length > 0
      ? (Object.values(results.final_scores || {}).reduce((a, b) => a + b, 0) / dimensions.length).toFixed(1)
      : '—';

    return (
      <div className={styles.overlay}>
        <div className={styles.container}>
          <div className={styles.resultsSection}>
            {/* Header */}
            <div className={styles.resultsHeader}>
              <span className={styles.ceoAvatarSmall}>{persona?.avatar || '👩‍💼'}</span>
              <div>
                <div className={styles.resultsTitle}>Competency Assessment</div>
                <div className={styles.resultsSubtitle}>
                  by {persona?.name || 'CEO'} — {persona?.title || ''}
                </div>
              </div>
            </div>

            {/* Outro */}
            <div className={styles.outroText}>
              {persona?.outro_text || ''}
            </div>

            {/* Average Score */}
            <div className={styles.avgScoreCard}>
              <div className={styles.avgLabel}>Overall Competency Score</div>
              <div className={styles.avgValue}>{avgScore}</div>
              <div className={styles.avgScale}>/10</div>
            </div>

            {/* Radar Chart */}
            <div className={styles.radarContainer}>
              {RadarChart}
            </div>

            {/* Scoring Methodology Explainer */}
            <div className={styles.methodologyPill}>
              <div className={styles.methodologyIcon}>⚖️</div>
              <div className={styles.methodologyContent}>
                <div className={styles.methodologyTitle}>Scoring Methodology</div>
                <div className={styles.methodologyText}>
                  Each dimension is scored from two sources: <strong>Performance</strong> (your
                  in-game decisions and outcomes across 10 rounds) and <strong>Interview</strong> (how
                  you articulated your reasoning in the CEO debrief). These are blended <strong>50/50</strong> to
                  produce your final score — meaning reflective insight is valued equally to
                  simulation outcomes.
                </div>
              </div>
            </div>

            {/* Dimension Breakdown */}
            <div className={styles.dimBreakdown}>
              {dimensions.map(d => {
                const score = results.final_scores?.[d.id] || 0;
                const dataScore = results.data_scores?.[d.id] || 0;
                const responseScore = results.response_scores?.[d.id] || 0;
                const rationale = scoreRationale[d.id] || '';
                const barColor = score >= 8 ? '#10b981' : score >= 6 ? '#3b82f6' : score >= 4 ? '#f59e0b' : '#ef4444';
                const dataBarColor = dataScore >= 7 ? '#10b981' : dataScore >= 4 ? '#3b82f6' : '#ef4444';
                const respBarColor = responseScore >= 7 ? '#10b981' : responseScore >= 4 ? '#3b82f6' : '#ef4444';
                return (
                  <DimensionCard
                    key={d.id}
                    dimension={d}
                    score={score}
                    dataScore={dataScore}
                    responseScore={responseScore}
                    rationale={rationale}
                    barColor={barColor}
                    dataBarColor={dataBarColor}
                    respBarColor={respBarColor}
                  />
                );
              })}
            </div>

            {/* Narrative Feedback */}
            {feedback.feedback_paragraphs?.length > 0 && (
              <div className={styles.feedbackSection}>
                <div className={styles.feedbackTitle}>💬 Narrative Assessment</div>
                {feedback.feedback_paragraphs.map((p, i) => (
                  <p key={i} className={styles.feedbackParagraph}>{p}</p>
                ))}
              </div>
            )}

            {/* Strengths + Growth Areas */}
            <div className={styles.insightsGrid}>
              {feedback.key_strengths?.length > 0 && (
                <div className={styles.insightCard}>
                  <div className={styles.insightTitle}>🏆 Key Strengths</div>
                  {feedback.key_strengths.map((s, i) => (
                    <div key={i} className={styles.insightItem} style={{ borderLeftColor: '#10b981' }}>
                      {s}
                    </div>
                  ))}
                </div>
              )}
              {feedback.growth_areas?.length > 0 && (
                <div className={styles.insightCard}>
                  <div className={styles.insightTitle}>📈 Growth Areas</div>
                  {feedback.growth_areas.map((g, i) => (
                    <div key={i} className={styles.insightItem} style={{ borderLeftColor: '#f59e0b' }}>
                      {g}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className={styles.resultsActions}>
              <button className={styles.btnPrimary} onClick={onClose}>
                📊 Return to Results
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
