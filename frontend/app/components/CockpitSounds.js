/**
 * CockpitSounds — Synthesized UI sound effects for state transitions.
 * Uses the Web Audio API to generate tiny sounds (no external files).
 *
 * #10: Sound Design for Executive Cockpit state transitions.
 */

let audioCtx = null;

function getCtx() {
  if (!audioCtx) {
    try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); }
    catch (e) { return null; }
  }
  return audioCtx;
}

// Soft "zoom in" — entering deep dive
export function playDeepDiveEnter() {
  const ctx = getCtx(); if (!ctx) return;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.connect(gain); gain.connect(ctx.destination);
  osc.type = 'sine';
  osc.frequency.setValueAtTime(400, ctx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(800, ctx.currentTime + 0.15);
  gain.gain.setValueAtTime(0.08, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + 0.2);
}

// Soft "pull back" — exiting to glance
export function playDeepDiveExit() {
  const ctx = getCtx(); if (!ctx) return;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.connect(gain); gain.connect(ctx.destination);
  osc.type = 'sine';
  osc.frequency.setValueAtTime(600, ctx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(300, ctx.currentTime + 0.12);
  gain.gain.setValueAtTime(0.06, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + 0.15);
}

// Satisfying confirmation chime — commit success
export function playCommitSuccess() {
  const ctx = getCtx(); if (!ctx) return;
  [523.25, 659.25, 783.99].forEach((freq, i) => {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.value = freq;
    const t = ctx.currentTime + i * 0.08;
    gain.gain.setValueAtTime(0.07, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.25);
    osc.start(t);
    osc.stop(t + 0.25);
  });
}

// Low tension drone — tipping point warning
export function playTippingWarning() {
  const ctx = getCtx(); if (!ctx) return;
  const osc = ctx.createOscillator();
  const lfo = ctx.createOscillator();
  const lfoGain = ctx.createGain();
  const mainGain = ctx.createGain();
  
  lfo.connect(lfoGain);
  lfoGain.connect(osc.frequency);
  osc.connect(mainGain);
  mainGain.connect(ctx.destination);
  
  osc.type = 'triangle';
  osc.frequency.value = 110;
  lfo.type = 'sine';
  lfo.frequency.value = 4;
  lfoGain.gain.value = 15;
  
  mainGain.gain.setValueAtTime(0.05, ctx.currentTime);
  mainGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
  
  lfo.start(ctx.currentTime);
  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + 0.5);
  lfo.stop(ctx.currentTime + 0.5);
}
