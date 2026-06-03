/**
 * useAlarmSound.ts — Custom React hook wrapping expo-av alarm sound playback.
 */

import { useCallback } from 'react';
import { playAlarmSound, stopAlarmSound } from '../services/notifications';

export function useAlarmSound() {
  const play = useCallback(async (level: 1 | 2 | 3) => {
    await playAlarmSound(level);
  }, []);

  const stop = useCallback(async () => {
    await stopAlarmSound();
  }, []);

  return { play, stop };
}
