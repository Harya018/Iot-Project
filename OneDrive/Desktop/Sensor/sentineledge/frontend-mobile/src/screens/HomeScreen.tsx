/**
 * HomeScreen.tsx — Main home screen showing live sensor data.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, Animated, SafeAreaView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import MetricCard from '../components/MetricCard';
import LiveChart from '../components/LiveChart';
import AlertBanner from '../components/AlertBanner';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAlarmSound } from '../hooks/useAlarmSound';
import { scheduleLocalNotification } from '../services/notifications';
import { fetchThresholds } from '../services/api';
import type { Thresholds } from '../services/api';

const COLORS = {
  bg: '#0f1117',
  card: '#1a1d27',
  success: '#10b981',
  danger: '#ef4444',
  textPrimary: '#f9fafb',
  textSecondary: '#9ca3af',
};

export default function HomeScreen() {
  const navigation = useNavigation<any>();
  const { reading, breaches, isConnected } = useWebSocket();
  const { play, stop } = useAlarmSound();

  const [readings, setReadings] = useState<{ temperature: number; humidity: number; timestamp: string }[]>([]);
  const [thresholds, setThresholds] = useState<Thresholds | null>(null);
  const flashAnim = useRef(new Animated.Value(0)).current;
  const prevBreachRef = useRef(false);

  useEffect(() => {
    fetchThresholds().then(setThresholds).catch(() => {});
  }, []);

  useEffect(() => {
    if (reading) {
      setReadings((prev) => {
        const next = [...prev, reading];
        return next.length > 60 ? next.slice(-60) : next;
      });
    }
  }, [reading]);

  // Breach effects: alarm + local notification + screen flash
  useEffect(() => {
    const hasBreach = breaches.length > 0;
    if (hasBreach && !prevBreachRef.current) {
      play(1);
      scheduleLocalNotification(
        'SentinelEdge Alert',
        `${breaches[0].parameter} is ${breaches[0].value} — threshold breached!`
      );
      // Flash screen red
      Animated.sequence([
        Animated.timing(flashAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
        Animated.timing(flashAnim, { toValue: 0, duration: 1800, useNativeDriver: true }),
      ]).start();
    } else if (!hasBreach && prevBreachRef.current) {
      stop();
    }
    prevBreachRef.current = hasBreach;
  }, [breaches, play, stop, flashAnim]);

  const getStatus = (param: 'temperature' | 'humidity', val: number | null) => {
    if (!thresholds || val === null || val === undefined) return 'NORMAL' as const;
    if (param === 'temperature') {
      if (val > thresholds.temp_high || val < thresholds.temp_low) return 'CRITICAL' as const;
    } else {
      if (val > thresholds.humidity_high || val < thresholds.humidity_low) return 'CRITICAL' as const;
    }
    return 'NORMAL' as const;
  };

  const tempBreach = breaches.some((b) => b.parameter === 'temperature');
  const humBreach = breaches.some((b) => b.parameter === 'humidity');

  return (
    <SafeAreaView style={styles.safe}>
      {/* Red flash overlay */}
      <Animated.View
        pointerEvents="none"
        style={[
          StyleSheet.absoluteFillObject,
          { backgroundColor: COLORS.danger, opacity: flashAnim, zIndex: 100 },
        ]}
      />

      {/* Alert banner */}
      <AlertBanner
        breaches={breaches}
        onPress={() => navigation.navigate('Acknowledge')}
      />

      {/* Connection status bar */}
      <View style={[styles.statusBar, { backgroundColor: isConnected ? COLORS.success + '20' : COLORS.danger + '20' }]}>
        <View style={[styles.statusDot, { backgroundColor: isConnected ? COLORS.success : COLORS.danger }]} />
        <Text style={[styles.statusText, { color: isConnected ? COLORS.success : COLORS.danger }]}>
          {isConnected ? 'LIVE — Connected to SentinelEdge' : 'DISCONNECTED — Reconnecting…'}
        </Text>
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        <MetricCard
          parameter="temperature"
          value={reading?.temperature ?? null}
          unit="°C"
          status={getStatus('temperature', reading?.temperature ?? null)}
          breach={tempBreach}
          thresholdHigh={thresholds?.temp_high}
          thresholdLow={thresholds?.temp_low}
        />
        <MetricCard
          parameter="humidity"
          value={reading?.humidity ?? null}
          unit="%"
          status={getStatus('humidity', reading?.humidity ?? null)}
          breach={humBreach}
          thresholdHigh={thresholds?.humidity_high}
          thresholdLow={thresholds?.humidity_low}
        />
        <LiveChart readings={readings} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0f1117' },
  statusBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  statusText: { fontSize: 12, fontWeight: '600' },
  scroll: { flex: 1 },
  content: { padding: 16, paddingBottom: 32 },
});
