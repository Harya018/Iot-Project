/**
 * LiveChart.tsx — Mobile line chart for temperature and humidity.
 * Shows the last 30 readings for performance.
 */

import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';

interface Reading {
  temperature: number;
  humidity: number;
  timestamp: string;
}

interface Props {
  readings: Reading[];
}

const screenWidth = Dimensions.get('window').width - 32; // 16px padding each side

export default function LiveChart({ readings }: Props) {
  const recent = readings.slice(-30);

  if (recent.length < 2) {
    return (
      <View style={styles.placeholder}>
        <Text style={styles.placeholderText}>Collecting data…</Text>
      </View>
    );
  }

  const labels = recent.map((_, i) => (i % 5 === 0 ? `${i}s` : ''));

  const chartConfig = {
    backgroundGradientFrom: '#1a1d27',
    backgroundGradientTo: '#1a1d27',
    decimalPlaces: 1,
    color: (opacity = 1) => `rgba(96, 165, 250, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(156, 163, 175, ${opacity})`,
    style: { borderRadius: 12 },
    propsForDots: { r: '0' },
    propsForBackgroundLines: { stroke: 'rgba(255,255,255,0.04)' },
  };

  const data = {
    labels,
    datasets: [
      {
        data: recent.map((r) => r.temperature),
        color: (opacity = 1) => `rgba(96, 165, 250, ${opacity})`,
        strokeWidth: 2,
      },
      {
        data: recent.map((r) => r.humidity),
        color: (opacity = 1) => `rgba(52, 211, 153, ${opacity})`,
        strokeWidth: 2,
      },
    ],
    legend: ['Temp (°C)', 'Humidity (%)'],
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Live Sensor Chart</Text>
      <LineChart
        data={data}
        width={screenWidth}
        height={180}
        chartConfig={chartConfig}
        bezier
        withDots={false}
        withInnerLines={true}
        withOuterLines={false}
        style={styles.chart}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1a1d27',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  title: {
    color: '#9ca3af',
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
  },
  chart: {
    borderRadius: 12,
    marginLeft: -16,
  },
  placeholder: {
    backgroundColor: '#1a1d27',
    borderRadius: 16,
    padding: 40,
    alignItems: 'center',
    marginBottom: 12,
  },
  placeholderText: {
    color: '#9ca3af',
    fontSize: 13,
  },
});
