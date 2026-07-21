/**
 * SoundManager — Audio feedback utility for simulation events.
 * Improvement #3.4: Sound & audio feedback
 *
 * Uses Web Audio API oscillator tones (no external files needed).
 */

class SoundManager {
  constructor() {
    this.enabled = typeof window !== 'undefined' &&
      localStorage.getItem('muressons_sound') !== 'false';
    this.ctx = null;
  }

  _ensureContext() {
    if (!this.ctx && typeof window !== 'undefined') {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return this.ctx;
  }

  _playTone(freq, duration = 0.15, type = 'sine', volume = 0.12) {
    if (!this.enabled) return;
    try {
      const ctx = this._ensureContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(volume, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + duration);
    } catch { /* silent fail */ }
  }

  commit() { this._playTone(523, 0.1); setTimeout(() => this._playTone(659, 0.1), 100); setTimeout(() => this._playTone(784, 0.15), 200); }
  advance() { this._playTone(440, 0.08); setTimeout(() => this._playTone(554, 0.08), 80); setTimeout(() => this._playTone(659, 0.12), 160); }
  alert() { this._playTone(350, 0.2, 'square', 0.08); setTimeout(() => this._playTone(300, 0.3, 'square', 0.06), 200); }
  click() { this._playTone(800, 0.05, 'sine', 0.06); }
  success() { this._playTone(523, 0.08); setTimeout(() => this._playTone(784, 0.15), 120); }
  error() { this._playTone(200, 0.2, 'sawtooth', 0.06); }
  // EX-5: Deep ominous thrum for tipping point activation
  tippingWarning() {
    this._playTone(80, 0.6, 'sawtooth', 0.10);
    setTimeout(() => this._playTone(60, 0.8, 'sawtooth', 0.08), 300);
    setTimeout(() => this._playTone(110, 0.4, 'square', 0.06), 700);
  }

  toggle() {
    this.enabled = !this.enabled;
    if (typeof window !== 'undefined') {
      localStorage.setItem('muressons_sound', this.enabled ? 'true' : 'false');
    }
    if (this.enabled) this.click();
    return this.enabled;
  }
}

const soundManager = typeof window !== 'undefined' ? new SoundManager() : { commit(){}, advance(){}, alert(){}, click(){}, success(){}, error(){}, tippingWarning(){}, toggle(){ return false; }, enabled: false };
export default soundManager;
