/**
 * AcknowledgeScreen.tsx — Prominent one-tap acknowledgement for active alerts.
 * Shows countdown to next escalation level.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, Animated, SafeAreaView,
} from 'react-native';
import { fetchAlerts, acknowledgeAlert } from '../services/api';
import type { Alert } from '../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const COLORS = {
  bg: '#0f1117',
  card: '#1a1d27',
  danger: '#ef4444',
  warning: '#f59e0b',
  success: '#10b981',
  textPrimary: '#f9fafb',
  textSecondary: '#9ca3af',
  primary: '#7c3aed',
};

const ESCALATION_TIMEOUT = 60; // seconds — mirrors backend config

function useCountdown(alert: Alert): number {
  const [remaining, setRemaining] = useState(0);

  useEffect(() => {
    const alertTime = new Date(alert.timestamp).getTime();
    const level = alert.escalation_level;
    const escalatesAt = alertTime + level * ESCALATION_TIMEOUT * 1000;

    const update = () => {
      const now = Date.now();
      const secs = Math.max(0, Math.floor((escalatesAt - now) / 1000));
      setRemaining(secs);
    };

    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, [alert]);

  return remaining;
}

interface AlertItemProps {
  alert: Alert;
  onAck: (id: number, name: string) => Promise<void>;
}

function AlertItem({ alert, onAck }: AlertItemProps) {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const scaleAnim = React.useRef(new Animated.Value(1)).current;
  const remaining = useCountdown(alert);

  // Pre-fill name from AsyncStorage
  useEffect(() => {
    AsyncStorage.getItem('subscriberName').then((n) => {
      if (n) setName(n);
    });
  }, []);

  const handleAck = async () => {
    setLoading(true);
    Animated.sequence([
      Animated.timing(scaleAnim, { toValue: 0.95, duration: 100, useNativeDriver: true }),
      Animated.timing(scaleAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
    ]).start();
    try {
      await onAck(alert.id, name.trim() || 'Mobile User');
      setDone(true);
    } finally {
      setLoading(false);
    }
  };

  const unit = alert.parameter === 'temperature' ? '°C' : '%';
  const label = alert.parameter === 'temperature' ? 'Temperature' : 'Humidity';

  if (done) {
    return (
      <View style={[styles.alertCard, { borderColor: COLORS.success + '60' }]}>
        <Text style={styles.doneText}>✅ Acknowledged — Thank you</Text>
      </View>
    );
  }

  return (
    <View style={[styles.alertCard, { borderColor: COLORS.danger + '80' }]}>
      <Text style={styles.alertTitle}>
        {label} <Text style={{ color: COLORS.danger }}>{alert.value}{unit}</Text>
      </Text>
      <Text style={styles.alertSub}>
        {alert.direction === 'high' ? 'Exceeds' : 'Below'} threshold of {alert.threshold}{unit}
      </Text>

      {alert.escalation_level < 3 && remaining > 0 && (
        <View style={styles.countdown}>
          <Text style={styles.countdownLabel}>
            Escalates to Level {alert.escalation_level + 1} in
          </Text>
          <Text style={styles.countdownValue}>{remaining}s</Text>
        </View>
      )}

      {alert.escalation_level === 3 && (
        <Text style={[styles.countdownLabel, { color: COLORS.danger }]}>
          ⚠️ Maximum escalation reached
        </Text>
      )}

      <TextInput
        placeholder="Your name"
        placeholderTextColor={COLORS.textSecondary}
        value={name}
        onChangeText={setName}
        style={styles.nameInput}
      />

      <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
        <TouchableOpacity style={styles.ackBtn} onPress={handleAck} disabled={loading}>
          <Text style={styles.ackBtnText}>{loading ? 'Acknowledging…' : '✓ Acknowledge Now'}</Text>
        </TouchableOpacity>
      </Animated.View>
    </View>
  );
}

export default function AcknowledgeScreen() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const load = useCallback(async () => {
    try {
      const all = await fetchAlerts();
      setAlerts(all.filter((a) => !a.acknowledged));
    } catch (err) {
      console.warn('[AcknowledgeScreen] load failed:', err);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 10_000);
    return () => clearInterval(timer);
  }, [load]);

  const handleAck = useCallback(async (id: number, name: string) => {
    await acknowledgeAlert(id, name);
    await load();
  }, [load]);

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        {alerts.length === 0 ? (
          <View style={styles.clear}>
            <Text style={styles.clearIcon}>✅</Text>
            <Text style={styles.clearTitle}>All Clear</Text>
            <Text style={styles.clearSub}>No unacknowledged alerts</Text>
          </View>
        ) : (
          <>
            <Text style={styles.sectionTitle}>Active Alerts ({alerts.length})</Text>
            {alerts.map((a) => (
              <AlertItem key={a.id} alert={a} onAck={handleAck} />
            ))}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bg },
  content: { padding: 16, paddingBottom: 48 },
  sectionTitle: {
    color: COLORS.textSecondary,
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
  },
  alertCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1.5,
    gap: 12,
  },
  alertTitle: {
    color: COLORS.textPrimary,
    fontSize: 22,
    fontWeight: '700',
  },
  alertSub: {
    color: COLORS.textSecondary,
    fontSize: 13,
  },
  countdown: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: COLORS.warning + '15',
    borderRadius: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: COLORS.warning + '40',
  },
  countdownLabel: {
    color: COLORS.warning,
    fontSize: 13,
    fontWeight: '600',
    flex: 1,
  },
  countdownValue: {
    color: COLORS.warning,
    fontSize: 20,
    fontWeight: '800',
  },
  nameInput: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: COLORS.textPrimary,
    fontSize: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  ackBtn: {
    backgroundColor: COLORS.success,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  ackBtnText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  doneText: {
    color: COLORS.success,
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center',
    paddingVertical: 20,
  },
  clear: { alignItems: 'center', marginTop: 80, gap: 8 },
  clearIcon: { fontSize: 56 },
  clearTitle: { color: COLORS.textPrimary, fontSize: 22, fontWeight: '700' },
  clearSub: { color: COLORS.textSecondary, fontSize: 14 },
});
