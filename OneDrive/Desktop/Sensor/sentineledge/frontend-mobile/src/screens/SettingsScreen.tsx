/**
 * SettingsScreen.tsx — Server connection and subscriber settings.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  ScrollView, SafeAreaView, KeyboardAvoidingView, Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { healthCheck } from '../services/api';
import { wsService } from '../services/websocket';
import { requestNotificationPermissions } from '../services/notifications';

const COLORS = {
  bg: '#0f1117',
  card: '#1a1d27',
  success: '#10b981',
  danger: '#ef4444',
  primary: '#7c3aed',
  textPrimary: '#f9fafb',
  textSecondary: '#9ca3af',
  warning: '#f59e0b',
};

export default function SettingsScreen() {
  const [serverIp, setServerIp] = useState('192.168.1.100');
  const [serverPort, setServerPort] = useState('8000');
  const [subscriberName, setSubscriberName] = useState('');
  const [saved, setSaved] = useState(false);
  const [connectionResult, setConnectionResult] = useState<null | boolean>(null);
  const [testing, setTesting] = useState(false);
  const [notifStatus, setNotifStatus] = useState<'idle' | 'granted' | 'denied'>('idle');

  useEffect(() => {
    const load = async () => {
      const ip = await AsyncStorage.getItem('serverIp');
      const port = await AsyncStorage.getItem('serverPort');
      const name = await AsyncStorage.getItem('subscriberName');
      if (ip) setServerIp(ip);
      if (port) setServerPort(port);
      if (name) setSubscriberName(name);
    };
    load();
  }, []);

  const handleSave = useCallback(async () => {
    await AsyncStorage.setItem('serverIp', serverIp.trim());
    await AsyncStorage.setItem('serverPort', serverPort.trim());
    await AsyncStorage.setItem('subscriberName', subscriberName.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
    // Reconnect WebSocket with new settings
    wsService.reconnect();
  }, [serverIp, serverPort, subscriberName]);

  const handleTestConnection = useCallback(async () => {
    setTesting(true);
    setConnectionResult(null);
    const ok = await healthCheck();
    setConnectionResult(ok);
    setTesting(false);
  }, []);

  const handleRegisterNotifications = useCallback(async () => {
    const granted = await requestNotificationPermissions();
    setNotifStatus(granted ? 'granted' : 'denied');
  }, []);

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <Text style={styles.title}>⚙️ Settings</Text>
            <Text style={styles.subtitle}>Configure your SentinelEdge connection</Text>
          </View>

          {/* Server Connection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Server Connection</Text>

            <Text style={styles.label}>Server IP Address</Text>
            <TextInput
              value={serverIp}
              onChangeText={setServerIp}
              style={styles.input}
              placeholder="192.168.1.100"
              placeholderTextColor={COLORS.textSecondary}
              keyboardType="numeric"
              autoCapitalize="none"
            />

            <Text style={styles.label}>Port</Text>
            <TextInput
              value={serverPort}
              onChangeText={setServerPort}
              style={styles.input}
              placeholder="8000"
              placeholderTextColor={COLORS.textSecondary}
              keyboardType="numeric"
            />

            <Text style={styles.label}>Your Name (for acknowledgements)</Text>
            <TextInput
              value={subscriberName}
              onChangeText={setSubscriberName}
              style={styles.input}
              placeholder="Alice"
              placeholderTextColor={COLORS.textSecondary}
              autoCapitalize="words"
            />

            <TouchableOpacity style={styles.primaryBtn} onPress={handleSave}>
              <Text style={styles.primaryBtnText}>
                {saved ? '✓ Saved!' : 'Save Settings'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Test Connection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Connection Test</Text>
            <TouchableOpacity
              style={[styles.secondaryBtn, testing && styles.btnDisabled]}
              onPress={handleTestConnection}
              disabled={testing}
            >
              <Text style={styles.secondaryBtnText}>
                {testing ? 'Testing…' : 'Test Connection'}
              </Text>
            </TouchableOpacity>
            {connectionResult !== null && (
              <View style={[
                styles.resultBanner,
                { backgroundColor: connectionResult ? COLORS.success + '20' : COLORS.danger + '20' },
              ]}>
                <Text style={[
                  styles.resultText,
                  { color: connectionResult ? COLORS.success : COLORS.danger },
                ]}>
                  {connectionResult
                    ? '✓ Connected successfully'
                    : '✗ Connection failed — check IP and port'}
                </Text>
              </View>
            )}
          </View>

          {/* Notifications */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Notifications</Text>
            <Text style={styles.infoText}>
              SentinelEdge sends local notifications when your device receives breach data
              over WebSocket. No internet or cloud service required.
            </Text>
            <TouchableOpacity style={styles.secondaryBtn} onPress={handleRegisterNotifications}>
              <Text style={styles.secondaryBtnText}>Enable Notifications</Text>
            </TouchableOpacity>
            {notifStatus !== 'idle' && (
              <View style={[
                styles.resultBanner,
                { backgroundColor: notifStatus === 'granted' ? COLORS.success + '20' : COLORS.danger + '20' },
              ]}>
                <Text style={[
                  styles.resultText,
                  { color: notifStatus === 'granted' ? COLORS.success : COLORS.danger },
                ]}>
                  {notifStatus === 'granted'
                    ? '✓ Notifications enabled'
                    : '✗ Permission denied — enable in device settings'}
                </Text>
              </View>
            )}
          </View>

          <Text style={styles.footer}>SentinelEdge v1.0.0 — All local, zero cloud</Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bg },
  content: { padding: 20, paddingBottom: 48 },
  header: { marginBottom: 24 },
  title: { color: COLORS.textPrimary, fontSize: 24, fontWeight: '800', marginBottom: 4 },
  subtitle: { color: COLORS.textSecondary, fontSize: 14 },
  section: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
    gap: 10,
  },
  sectionTitle: {
    color: COLORS.textSecondary,
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 4,
  },
  label: { color: COLORS.textSecondary, fontSize: 12, fontWeight: '600' },
  input: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: COLORS.textPrimary,
    fontSize: 15,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  primaryBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 4,
  },
  primaryBtnText: { color: '#fff', fontSize: 15, fontWeight: '700' },
  secondaryBtn: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  secondaryBtnText: { color: COLORS.textPrimary, fontSize: 15, fontWeight: '600' },
  btnDisabled: { opacity: 0.5 },
  resultBanner: { borderRadius: 10, padding: 12 },
  resultText: { fontSize: 13, fontWeight: '600' },
  infoText: { color: COLORS.textSecondary, fontSize: 13, lineHeight: 20 },
  footer: { color: COLORS.textSecondary, fontSize: 11, textAlign: 'center', marginTop: 12 },
});
