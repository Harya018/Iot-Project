/**
 * useAudioAlarm.js — Web Audio API alarm hook for SentinelEdge.
 *
 * Generates alarm tones procedurally — no external audio files required.
 * Respects browser autoplay policy by initialising AudioContext only after
 * the first user interaction on the page.
 *
 * Level 1: single 440 Hz beep, 0.5 s
 * Level 2: two beeps, 440 Hz → 880 Hz, 0.3 s each
 * Level 3: continuous repeating 880 Hz alarm until stopAlarm() is called
 */

import { useRef, useCallback, useEffect } from 'react';

export function useAudioAlarm() {
  const audioCtxRef = useRef(null);
  const oscillatorRef = useRef(null); // only used for level-3 continuous alarm
  const hasInteractedRef = useRef(false);
  const level3IntervalRef = useRef(null);

  // Unlock AudioContext after the first user gesture
  useEffect(() => {
    const unlock = () => {
      hasInteractedRef.current = true;
      // Lazily create context on first interaction
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtxRef.current.state === 'suspended') {
        audioCtxRef.current.resume();
      }
    };
    window.addEventListener('click', unlock, { once: true });
    window.addEventListener('keydown', unlock, { once: true });
    return () => {
      window.removeEventListener('click', unlock);
      window.removeEventListener('keydown', unlock);
    };
  }, []);

  const _getCtx = () => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioCtxRef.current;
  };

  /** Play a single beep at the given frequency for durationMs milliseconds. */
  const _beep = useCallback((frequency, durationMs, startTime) => {
    try {
      const ctx = _getCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(frequency, startTime);
      gain.gain.setValueAtTime(0.4, startTime);
      gain.gain.exponentialRampToValueAtTime(0.001, startTime + durationMs / 1000);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(startTime);
      osc.stop(startTime + durationMs / 1000 + 0.05);
    } catch (err) {
      console.warn('[useAudioAlarm] _beep error:', err);
    }
  }, []);

  const stopAlarm = useCallback(() => {
    clearInterval(level3IntervalRef.current);
    level3IntervalRef.current = null;
    try {
      if (oscillatorRef.current) {
        oscillatorRef.current.stop();
        oscillatorRef.current.disconnect();
        oscillatorRef.current = null;
      }
    } catch (_) {
      // Already stopped
    }
  }, []);

  const playAlarm = useCallback((level) => {
    if (!hasInteractedRef.current) return; // Respect autoplay policy

    stopAlarm(); // Always clean up any previous alarm first

    const ctx = _getCtx();
    const now = ctx.currentTime;

    if (level === 1) {
      _beep(440, 500, now);
    } else if (level === 2) {
      _beep(440, 300, now);
      _beep(880, 300, now + 0.4);
    } else if (level === 3) {
      // Play immediately, then repeat every 1.2 s
      const playOneCycle = () => {
        const t = _getCtx().currentTime;
        _beep(880, 300, t);
        _beep(880, 300, t + 0.4);
      };
      playOneCycle();
      level3IntervalRef.current = setInterval(playOneCycle, 1200);
    }
  }, [_beep, stopAlarm]);

  return { playAlarm, stopAlarm };
}
