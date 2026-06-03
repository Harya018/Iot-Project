/**
 * AlertScreen.tsx — Full list of alerts with escalation badges and acknowledge.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity, TextInput,
  RefreshControl, SafeAreaView, Alert as RNAlert,
} from 'react-native';
import EscalationBadge from '../components/EscalationBadge';
import { fetchAlerts, acknowledgeAlert } from '../services/api';
import type { Alert } from '../services/api';

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

function formatTime(ts: string): string {
  return new Date(ts).toLocaleString();
}

interface AlertCardProps {
  alert: Alert;
  onAck: (id: number, name: string) => Promise<void>;
}

function AlertCard({ alert, onAck }: AlertCardProps) {
  const [showInput, setShowInput] = useState(false);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);

  const unit = alert.parameter === 'temperature' ? '°C' : '%';
  const label = alert.parameter === 'temperature' ? 'Temperature' : 'Humidity';

  const handleAck = async () => {
    setLoading(true);
    try {
      await onAck(alert.id, name.trim() || 'Mobile User');
    } finally {
      setLoading(false);
      setShowInput(false);
    }
  };

  return (
    <View style={[styles.card, alert.acknowledged && styles.cardAcked]}>
      <View style={styles.cardHeader}>
        <EscalationBadge level={alert.escalation_level} />
        <Text style={styles.timestamp}>{formatTime(alert.timestamp)}</Text>
      </View>

      <Text style={styles.alertText}>
        {label} <Text style={{ color: alert.direction === 'high' ? COLORS.danger : COLORS.warning }}>
          {alert.value}{unit}
        </Text>
        {' '}— {alert.direction === 'high' ? 'exceeds' : 'below'} threshold {alert.threshold}{unit}
      </Text>

      {alert.acknowledged ? (
        <Text style={styles.ackedText}>
          ✓ Acknowledged by {alert.acknowledged_by}
        </Text>
      ) : (
        <View style={styles.ackRow}>
          {!showInput ? (
            <TouchableOpacity style={styles.ackBtn} onPress={() => setShowInput(true)}>
              <Text style={styles.ackBtnText}>Acknowledge</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.ackInputRow}>
              <TextInput
                placeholder="Your name"
                placeholderTextColor={COLORS.textSecondary}
                value={name}
                onChangeText={setName}
                style={styles.nameInput}
                onSubmitEditing={handleAck}
              />
              <TouchableOpacity
                style={[styles.ackBtn, { backgroundColor: COLORS.success + '30' }]}
                onPress={handleAck}
                disabled={loading}
              >
                <Text style={[styles.ackBtnText, { color: COLORS.success }]}>
                  {loading ? '…' : 'OK'}
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

export default function AlertScreen() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchAlerts();
      setAlerts(data);
    } catch (err) {
      console.warn('Failed to load alerts:', err);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 15_000);
    return () => clearInterval(interval);
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const handleAck = useCallback(async (id: number, name: string) => {
    await acknowledgeAlert(id, name);
    await load();
  }, [load]);

  return (
    <SafeAreaView style={styles.safe}>
      <FlatList
        data={alerts}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => <AlertCard alert={item} onAck={handleAck} />}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />
        }
        ListEmptyComponent={
          <Text style={styles.empty}>No alerts recorded yet.</Text>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bg },
  list: { padding: 16, paddingBottom: 32 },
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 14,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.2)',
  },
  cardAcked: { opacity: 0.6, borderColor: 'rgba(255,255,255,0.05)' },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  timestamp: { color: COLORS.textSecondary, fontSize: 11 },
  alertText: { color: COLORS.textPrimary, fontSize: 14, marginBottom: 10 },
  ackedText: { color: COLORS.success, fontSize: 12, fontWeight: '600' },
  ackRow: { alignItems: 'flex-start' },
  ackInputRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  ackBtn: {
    backgroundColor: '#7c3aed30',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#7c3aed60',
  },
  ackBtnText: { color: '#7c3aed', fontWeight: '700', fontSize: 13 },
  nameInput: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    color: COLORS.textPrimary,
    fontSize: 13,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    minWidth: 120,
  },
  empty: {
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 60,
    fontSize: 14,
  },
});
