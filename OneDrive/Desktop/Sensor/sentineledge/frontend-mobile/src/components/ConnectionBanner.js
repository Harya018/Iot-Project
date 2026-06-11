// ─────────────────────────────────────────────
//  SentinelEdge — Connection Banner Component
//  Small animated red banner shown when WebSocket
//  is disconnected.
// ─────────────────────────────────────────────
import React, { useEffect, useRef } from 'react';
import { Animated, Text, StyleSheet, View } from 'react-native';

const ConnectionBanner = ({ connected }) => {
  const fadeAnim = useRef(new Animated.Value(connected ? 0 : 1)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: connected ? 0 : 1,
      duration: 350,
      useNativeDriver: true,
    }).start();
  }, [connected, fadeAnim]);

  // Don't render anything when fully transparent
  if (connected) {
    return (
      <Animated.View style={[styles.banner, { opacity: fadeAnim }]} pointerEvents="none">
        <View style={styles.dot} />
        <Text style={styles.text}>Reconnecting to server...</Text>
      </Animated.View>
    );
  }

  return (
    <Animated.View style={[styles.banner, { opacity: fadeAnim }]}>
      <View style={styles.dot} />
      <Text style={styles.text}>Reconnecting to server...</Text>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#C0392B',
    paddingVertical: 8,
    paddingHorizontal: 16,
    width: '100%',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF8C8C',
    marginRight: 8,
  },
  text: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
});

export default ConnectionBanner;
