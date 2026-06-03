/**
 * AlertBanner.tsx — Fixed top banner displayed when there is an active breach.
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

interface BreachEvent {
  parameter: string;
  value: number;
  threshold: number;
  direction: string;
}

interface Props {
  breaches: BreachEvent[];
  onPress: () => void;
}

export default function AlertBanner({ breaches, onPress }: Props) {
  if (breaches.length === 0) return null;

  const primary = breaches[0];
  const unit = primary.parameter === 'temperature' ? '°C' : '%';
  const label = primary.parameter === 'temperature' ? 'Temperature' : 'Humidity';

  return (
    <TouchableOpacity style={styles.banner} onPress={onPress} activeOpacity={0.85}>
      <Text style={styles.icon}>🚨</Text>
      <Text style={styles.text} numberOfLines={1}>
        BREACH: {label} {primary.value}{unit} — Tap to acknowledge
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: '#ef4444',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  icon: {
    fontSize: 16,
  },
  text: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 13,
    flex: 1,
  },
});
