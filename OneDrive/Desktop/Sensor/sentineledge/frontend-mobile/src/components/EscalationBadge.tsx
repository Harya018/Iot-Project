/**
 * EscalationBadge.tsx — Visual escalation level indicator.
 *
 * Level 1: amber  "Level 1"
 * Level 2: orange "Escalated"
 * Level 3: red pulsing "CRITICAL"
 */

import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';

interface Props {
  level: number;
}

const LEVEL_CONFIG: Record<number, { label: string; bg: string; text: string }> = {
  1: { label: 'Level 1', bg: '#f59e0b20', text: '#f59e0b' },
  2: { label: 'Escalated', bg: '#f9731620', text: '#f97316' },
  3: { label: 'CRITICAL', bg: '#ef444420', text: '#ef4444' },
};

export default function EscalationBadge({ level }: Props) {
  const config = LEVEL_CONFIG[level] || LEVEL_CONFIG[1];
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (level >= 3) {
      const animation = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 0.3, duration: 500, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        ])
      );
      animation.start();
      return () => animation.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [level, pulseAnim]);

  return (
    <Animated.View
      style={[
        styles.badge,
        { backgroundColor: config.bg, borderColor: config.text + '60' },
        level >= 3 && { opacity: pulseAnim },
      ]}
    >
      <Text style={[styles.text, { color: config.text }]}>{config.label}</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 20,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
});
