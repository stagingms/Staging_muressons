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
  const [leverageAnalysis, setLeverageAnalysis] = useState(null);
  const [contextualCases, setContextualCases] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTimer, setRecordingTimer] = useState(120); // 2 minutes
  const [inputMode, setInputMode] = useState('text'); // 'text' | 'voice'
  const textareaRef = useRef(null);
  const audioRef = useRef(null);
  const audioCacheRef = useRef({});
  const recognitionRef = useRef(null);
  const timerRef = useRef(null);
  const transcriptRef = useRef(''); // Stable ref for the running transcript — avoids stale closures

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
      try { recognitionRef.current.stop(); } catch { /* already stopped */ }
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
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    stopRecording();
    setRecordingTimer(120); // Reset to 2 minutes

    // Seed the transcript ref with whatever text exists now
    transcriptRef.current = currentAnswer || '';

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          transcriptRef.current += (transcriptRef.current ? ' ' : '') + transcript;
        } else {
          interim += transcript;
        }
      }
      setCurrentAnswer(transcriptRef.current + (interim ? ' ' + interim : ''));
    };

    recognition.onerror = (e) => {
      if (e.error === 'not-allowed') {
        alert('Microphone access was denied. Please allow microphone permissions in your browser settings and try again.');
      } else if (e.error !== 'aborted' && e.error !== 'no-speech') {
        console.warn('Speech recognition error:', e.error);
      }
      stopRecording();
    };

    recognition.onend = () => {
      // Recognition ended naturally (e.g. silence timeout) — restart if still recording
      if (recognitionRef.current === recognition) {
        try { recognition.start(); } catch { stopRecording(); }
      }
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch (e) {
      console.error('Failed to start speech recognition:', e);
      alert('Could not start speech recognition. Please check your microphone and try again.');
      stopRecording();
      return;
    }
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
    transcriptRef.current = '';
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
      
      // Fetch pedagogical debrief data asynchronously in the background
      Promise.all([
        fetch(`${API}/api/simulations/${sessionId}/leverage-analysis`).then(r => r.ok ? r.json() : null),
        fetch(`${API}/api/simulations/${sessionId}/contextual-cases`).then(r => r.ok ? r.json() : null)
      ]).then(([levData, caseData]) => {
        if (levData?.leverage_analysis) setLeverageAnalysis(levData.leverage_analysis);
        if (caseData?.contextual_cases) setContextualCases(caseData.contextual_cases);
      }).catch(err => console.error('Failed to fetch debrief data', err));

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
                  onChange={e => { setCurrentAnswer(e.target.value); transcriptRef.current = e.target.value; }}
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
                        <span style={{ fontSize: 'var(--type-caption)', color: '#64748b', marginLeft: 4 }}>remaining</span>
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

            {/* Contextual Cases */}
            {contextualCases?.length > 0 && (
              <div className={styles.feedbackSection} style={{ marginTop: 24 }}>
                <div className={styles.feedbackTitle}>📚 Real-World Contextual Cases</div>
                <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: 12 }}>
                  These case studies reflect the real-world equivalents of your strategic situations.
                </div>
                <div className={styles.insightsGrid}>
                  {contextualCases.map((c, i) => (
                    <div key={i} className={styles.insightCard} style={{ border: '1px solid rgba(99,102,241,0.2)', background: 'rgba(99,102,241,0.02)' }}>
                      <div className={styles.insightTitle} style={{ color: '#4f46e5' }}>{c.headline}</div>
                      <div style={{ fontSize: '0.75rem', color: '#334155', lineHeight: 1.5, marginBottom: 8 }}>{c.brief}</div>
                      <div style={{ fontSize: 'var(--type-caption)', color: '#64748b', fontStyle: 'italic' }}>
                        <strong>Relevance:</strong> {c.relevance}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Leverage Analysis */}
            {leverageAnalysis && leverageAnalysis.dominant_leverage_point && (
              <div className={styles.feedbackSection} style={{ marginTop: 24 }}>
                <div className={styles.feedbackTitle}>⚙️ Meadows Leverage Analysis</div>
                <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: 12 }}>
                  Analysis of your decisions against Donella Meadows' 12 Leverage Points to Intervene in a System.
                </div>
                <div className={styles.insightCard} style={{ borderLeftColor: leverageAnalysis.dominant_leverage_point <= 6 ? '#10b981' : '#f59e0b' }}>
                  <div className={styles.insightTitle}>Dominant Mode: {leverageAnalysis.dominant_name} (LP{leverageAnalysis.dominant_leverage_point})</div>
                  <div style={{ fontSize: '0.8rem', color: '#334155', lineHeight: 1.5, marginBottom: 8 }}>
                    {leverageAnalysis.summary_text}
                  </div>
                  {leverageAnalysis.leverage_point_examples?.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', marginBottom: 4 }}>Key Interventions:</div>
                      <ul style={{ paddingLeft: 16, margin: 0, fontSize: '0.75rem', color: '#475569' }}>
                        {leverageAnalysis.leverage_point_examples.slice(0, 3).map((ex, i) => (
                          <li key={i} style={{ marginBottom: 4 }}>{ex}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className={styles.resultsActions}>
              <button
                className={styles.btnSecondary}
                onClick={() => {
                  // ── Generate self-contained HTML for print-to-PDF ──
                  const scoreRat = results.score_rationale || {};
                  const fs = results.final_scores || {};
                  const ds = results.data_scores || {};
                  const rs = results.response_scores || {};
                  const fb = results.feedback || {};

                  const healthColor = (s) => s >= 8 ? '#10b981' : s >= 6 ? '#3b82f6' : s >= 4 ? '#f59e0b' : '#ef4444';

                  const dimHTML = dimensions.map(d => {
                    const sc = fs[d.id] || 0;
                    const dsc = ds[d.id] || 0;
                    const rsc = rs[d.id] || 0;
                    const rat = scoreRat[d.id] || '';
                    const col = healthColor(sc);
                    const dcol = healthColor(dsc);
                    const rcol = healthColor(rsc);
                    return `
                      <div class="dim-card">
                        <div class="dim-header">
                          <div>
                            <div class="dim-label">${d.label}</div>
                            <div class="dim-desc">${d.description}</div>
                          </div>
                          <div class="dim-score" style="color:${col}">${sc.toFixed(1)}</div>
                        </div>
                        <div class="bar-track"><div class="bar-fill" style="width:${(sc/10)*100}%;background:${col}"></div></div>
                        <div class="blend-formula">
                          ⚖️ Final Score = (Performance ${dsc.toFixed(1)} × 50%) + (Interview ${rsc.toFixed(1)} × 50%) = ${sc.toFixed(1)}
                        </div>
                        <div class="split-bars">
                          <div class="split-bar">
                            <div class="split-header">
                              <span>📊 Performance Score</span>
                              <span style="color:${dcol};font-weight:800">${dsc.toFixed(1)}/10</span>
                            </div>
                            <div class="bar-track"><div class="bar-fill" style="width:${(dsc/10)*100}%;background:${dcol}"></div></div>
                            ${rat ? `<div class="rationale">${rat}</div>` : ''}
                          </div>
                          <div class="split-bar">
                            <div class="split-header">
                              <span>🎤 Interview Score</span>
                              <span style="color:${rcol};font-weight:800">${rsc.toFixed(1)}/10</span>
                            </div>
                            <div class="bar-track"><div class="bar-fill" style="width:${(rsc/10)*100}%;background:${rcol}"></div></div>
                            <div class="rationale">${
                              rsc >= 8 ? 'Your interview responses demonstrated deep, nuanced understanding with specific examples and sophisticated analysis.'
                              : rsc >= 6 ? 'Your responses showed good awareness with reasonable examples, though deeper analysis would have strengthened your score.'
                              : rsc >= 4 ? 'Your responses touched on this dimension but lacked specificity or depth.'
                              : 'This dimension was not well-addressed in your interview responses.'
                            }</div>
                          </div>
                        </div>
                      </div>`;
                  }).join('');

                  const narrativeHTML = (fb.feedback_paragraphs || []).map(p =>
                    `<p class="narrative">${p}</p>`
                  ).join('');

                  const strengthsHTML = (fb.key_strengths || []).map(s =>
                    `<div class="insight strength">${s}</div>`
                  ).join('');

                  const growthHTML = (fb.growth_areas || []).map(g =>
                    `<div class="insight growth">${g}</div>`
                  ).join('');

                  const casesHTML = (contextualCases || []).map(c => `
                    <div class="case-card">
                      <div class="case-headline">${c.headline}</div>
                      <div class="case-brief">${c.brief}</div>
                      <div class="case-relevance"><strong>Relevance:</strong> ${c.relevance}</div>
                    </div>
                  `).join('');

                  const leverageHTML = leverageAnalysis?.dominant_leverage_point ? `
                    <div class="section">
                      <h2>⚙️ Meadows Leverage Analysis</h2>
                      <p class="section-desc">Analysis against Donella Meadows' 12 Leverage Points to Intervene in a System.</p>
                      <div class="leverage-card">
                        <div class="leverage-title">Dominant Mode: ${leverageAnalysis.dominant_name} (LP${leverageAnalysis.dominant_leverage_point})</div>
                        <p class="narrative">${leverageAnalysis.summary_text}</p>
                        ${leverageAnalysis.leverage_point_examples?.length ? `
                          <div class="leverage-examples">
                            <strong>Key Interventions:</strong>
                            <ul>${leverageAnalysis.leverage_point_examples.slice(0,3).map(e => `<li>${e}</li>`).join('')}</ul>
                          </div>
                        ` : ''}
                      </div>
                    </div>
                  ` : '';

                  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CEO Interview — Competency Assessment Report</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@600;700;800&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'DM Sans', 'Inter', system-ui, sans-serif; background: #ffffff; color: #1e293b; line-height: 1.6; }
    .report { max-width: 800px; margin: 0 auto; padding: 40px 32px; }
    .header { text-align: center; padding: 32px 24px; border-radius: 16px; margin-bottom: 28px;
              background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06));
              border: 1px solid rgba(99,102,241,0.2); }
    .header .badge { font-size: var(--type-caption); letter-spacing: 3px; text-transform: uppercase; color: #6366f1; margin-bottom: 8px; }
    .header h1 { font-size: 24px; font-weight: 900; color: #0f172a; margin: 8px 0 4px; }
    .header .subtitle { font-size: 13px; color: #475569; }
    .avg-card { display: flex; align-items: baseline; justify-content: center; gap: 6px;
                padding: 16px; background: rgba(99,102,241,0.06);
                border: 1px solid rgba(99,102,241,0.2); border-radius: 12px; margin-bottom: 24px; }
    .avg-label { font-size: var(--type-caption); font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; }
    .avg-value { font-size: 36px; font-weight: 900; color: #4f46e5; font-family: 'JetBrains Mono', monospace; }
    .avg-scale { font-size: 14px; color: #64748b; font-weight: 600; }
    .methodology { display: flex; gap: 12px; padding: 12px 16px; background: rgba(59,130,246,0.05);
                   border: 1px solid rgba(59,130,246,0.15); border-radius: 10px; margin-bottom: 24px; font-size: 12px; color: #334155; }
    .methodology strong { color: #1e293b; }
    .dim-card { padding: 16px; background: #fafafa;
                border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 12px; }
    .dim-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .dim-label { font-size: 13px; font-weight: 800; color: #0f172a; }
    .dim-desc { font-size: var(--type-caption); color: #64748b; margin-top: 2px; }
    .dim-score { font-size: 18px; font-weight: 900; font-family: 'JetBrains Mono', monospace; }
    .bar-track { height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; margin-bottom: 8px; }
    .bar-fill { height: 100%; border-radius: 3px; }
    .blend-formula { font-size: var(--type-caption); color: #475569; font-family: 'JetBrains Mono', monospace; padding: 6px 10px;
                     background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.12); border-radius: 6px; margin-bottom: 12px; }
    .split-bars { display: flex; flex-direction: column; gap: 10px; }
    .split-bar { display: flex; flex-direction: column; gap: 4px; }
    .split-header { display: flex; justify-content: space-between; font-size: var(--type-caption); font-weight: 700; color: #1e293b; }
    .rationale { font-size: var(--type-caption); color: #334155; line-height: 1.65; padding: 6px 8px; background: #f8fafc;
                 border-left: 3px solid rgba(99,102,241,0.3); border-radius: 0 6px 6px 0; margin-top: 4px; }
    .section { margin-top: 28px; }
    .section h2 { font-size: 15px; font-weight: 800; color: #0f172a; margin-bottom: 12px; padding-bottom: 6px;
                  border-bottom: 1px solid #e2e8f0; }
    .section-desc { font-size: 12px; color: #475569; margin-bottom: 12px; }
    .narrative { font-size: 13px; color: #334155; line-height: 1.7; margin-bottom: 10px; }
    .insights-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
    .insight-card { display: flex; flex-direction: column; gap: 6px; }
    .insight-title { font-size: var(--type-caption); font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.06em; }
    .insight { font-size: 12px; color: #334155; line-height: 1.5; padding: 6px 10px; border-left: 3px solid #94a3b8;
               background: #f8fafc; border-radius: 0 6px 6px 0; }
    .insight.strength { border-left-color: #10b981; }
    .insight.growth { border-left-color: #f59e0b; }
    .case-card { padding: 12px; border: 1px solid rgba(99,102,241,0.2); background: rgba(99,102,241,0.03);
                 border-radius: 8px; margin-bottom: 10px; }
    .case-headline { font-size: 12px; font-weight: 800; color: #4f46e5; margin-bottom: 4px; }
    .case-brief { font-size: 12px; color: #1e293b; line-height: 1.5; margin-bottom: 6px; }
    .case-relevance { font-size: var(--type-caption); color: #475569; font-style: italic; }
    .leverage-card { padding: 14px; border-left: 3px solid #10b981; background: #f0fdf4; border-radius: 0 8px 8px 0; }
    .leverage-title { font-size: 13px; font-weight: 800; color: #0f172a; margin-bottom: 6px; }
    .leverage-examples { margin-top: 10px; font-size: 12px; color: #334155; }
    .leverage-examples ul { padding-left: 18px; margin-top: 4px; }
    .leverage-examples li { margin-bottom: 4px; }
    .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0;
              color: #64748b; font-size: var(--type-caption); }
    @media print {
      body { background: #ffffff !important; color: #1e293b !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      .report { padding: 20px; }
      .dim-card { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <div class="report">
    <div class="header">
      <div class="badge">CEO INTERVIEW — COMPETENCY ASSESSMENT REPORT</div>
      <h1>${persona?.avatar || '👩‍💼'} ${persona?.name || 'CEO'} Assessment</h1>
      <div class="subtitle">by ${persona?.name || 'CEO'} — ${persona?.title || ''}</div>
    </div>

    <div class="avg-card">
      <span class="avg-label">Overall Competency Score</span>
      <span class="avg-value">${avgScore}</span>
      <span class="avg-scale">/10</span>
    </div>

    <div class="methodology">
      <div>⚖️</div>
      <div>Each dimension is scored from two sources: <strong>Performance</strong> (in-game decisions and outcomes across 10 rounds)
      and <strong>Interview</strong> (how you articulated your reasoning in the CEO debrief).
      These are blended <strong>50/50</strong> — reflective insight is valued equally to simulation outcomes.</div>
    </div>

    <div class="section">
      <h2>📊 Competency Dimensions</h2>
      ${dimHTML}
    </div>

    ${narrativeHTML ? `
    <div class="section">
      <h2>💬 Narrative Assessment</h2>
      ${narrativeHTML}
    </div>` : ''}

    <div class="insights-grid">
      ${strengthsHTML ? `<div class="insight-card"><div class="insight-title">🏆 Key Strengths</div>${strengthsHTML}</div>` : ''}
      ${growthHTML ? `<div class="insight-card"><div class="insight-title">📈 Growth Areas</div>${growthHTML}</div>` : ''}
    </div>

    ${casesHTML ? `
    <div class="section">
      <h2>📚 Real-World Contextual Cases</h2>
      <p class="section-desc">These case studies reflect the real-world equivalents of your strategic situations.</p>
      ${casesHTML}
    </div>` : ''}

    ${leverageHTML}

    <div class="footer">
      <p>Muressons Global Command — CEO Interview Competency Assessment</p>
      <p>Report generated ${new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
    </div>
  </div>
  <script>window.onload = function() { window.print(); }</script>
</body>
</html>`;

                  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
                  const url = URL.createObjectURL(blob);
                  const printWindow = window.open(url, '_blank');
                  if (printWindow) {
                    printWindow.onafterprint = () => {
                      URL.revokeObjectURL(url);
                    };
                  } else {
                    // Fallback: direct download as HTML
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'CEO_Interview_Assessment.html';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  }
                }}
              >
                📥 Download PDF
              </button>
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
