/**
 * MetricCard.tsx — Mobile sensor metric display card.
 */

import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';

const COLORS = {
  bg: '#0f1117',
  card: '#1a1d27',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  primary: '#7c3aed',
  textPrimary: '#f9fafb',
  textSecondary: '#9ca3af',
};

type Status = 'NORMAL' | 'WARNING' | 'CRITICAL';

interface Props {
  parameter: 'temperature' | 'humidity';
  value: number | null;
  unit: string;
  status: Status;
  breach: boolean;
  thresholdHigh?: number;
  thresholdLow?: number;
}

const STATUS_COLORS: Record<Status, string> = {
  NORMAL: COLORS.success,
  WARNING: COLORS.warning,
  CRITICAL: COLORS.danger,
};

export default function MetricCard({
  parameter, value, unit, status, breach, thresholdHigh, thresholdLow,
}: Props) {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (breach) {
      const animation = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 0.5, duration: 700, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 700, useNativeDriver: true }),
        ])
      );
      animation.start();
      return () => animation.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [breach, pulseAnim]);

  const label = parameter === 'temperature' ? '🌡️ Temperature' : '💧 Humidity';
  const statusColor = STATUS_COLORS[status];

  return (
    <Animated.View
      style={[
        styles.card,
        breach && { borderColor: COLORS.danger, borderWidth: 1.5 },
        breach && { opacity: pulseAnim },
      ]}
    >
      <View style={styles.header}>
        <Text style={styles.label}>{label}</Text>
        <View style={[styles.badge, { backgroundColor: statusColor + '20', borderColor: statusColor + '60' }]}>
          <Text style={[styles.badgeText, { color: statusColor }]}>{status}</Text>
        </View>
      </View>

      <Text style={[styles.value, { color: statusColor }]}>
        {value !== null && value !== undefined ? `${value}` : '--'}
        <Text style={styles.unit}>{unit}</Text>
      </Text>

      {(thresholdHigh !== undefined || thresholdLow !== undefined) && (
        <View style={styles.thresholds}>
          {thresholdHigh !== undefined && (
            <Text style={styles.thresholdText}>
              <Text style={{ color: COLORS.danger }}>● </Text>
              High: {thresholdHigh}{unit}
            </Text>
          )}
          {thresholdLow !== undefined && (
            <Text style={styles.thresholdText}>
              <Text style={{ color: COLORS.warning }}>● </Text>
              Low: {thresholdLow}{unit}
            </Text>
          )}
        </View>
      )}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  label: {
    color: COLORS.textSecondary,
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 20,
    borderWidth: 1,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  value: {
    fontSize: 56,
    fontWeight: '800',
    letterSpacing: -1,
    marginBottom: 12,
  },
  unit: {
    fontSize: 22,
    fontWeight: '500',
    color: COLORS.textSecondary,
  },
  thresholds: {
    flexDirection: 'row',
    gap: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.05)',
    paddingTop: 10,
  },
  thresholdText: {
    color: COLORS.textSecondary,
    fontSize: 11,
  },
});
