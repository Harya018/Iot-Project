/**
 * LiveChart.jsx — Dual-axis real-time chart using Chart.js.
 *
 * Props:
 *   readings   : array of { temperature, humidity, timestamp }
 *   thresholds : { temp_high, temp_low, humidity_high, humidity_low }
 */

import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function LiveChart({ readings, thresholds }) {
  const labels = useMemo(
    () =>
      readings.map((r, i) => {
        if (i % 10 !== 0) return '';
        const d = new Date(r.timestamp);
        return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;
      }),
    [readings]
  );

  const temps = useMemo(() => readings.map((r) => r.temperature), [readings]);
  const hums = useMemo(() => readings.map((r) => r.humidity), [readings]);

  const tHigh = thresholds?.temp_high ?? 38;
  const tLow = thresholds?.temp_low ?? 22;
  const hHigh = thresholds?.humidity_high ?? 80;
  const hLow = thresholds?.humidity_low ?? 35;

  const options = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    animation: { duration: 200 },
    scales: {
      x: {
        ticks: { color: '#6b7280', maxRotation: 0, font: { size: 10 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: { display: true, text: 'Temperature (°C)', color: '#60a5fa', font: { size: 11 } },
        ticks: { color: '#60a5fa', font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: { display: true, text: 'Humidity (%)', color: '#34d399', font: { size: 11 } },
        ticks: { color: '#34d399', font: { size: 11 } },
        grid: { drawOnChartArea: false },
      },
    },
    plugins: {
      legend: {
        labels: { color: '#9ca3af', usePointStyle: true, pointStyleWidth: 8 },
      },
      tooltip: {
        backgroundColor: '#1a1d27',
        titleColor: '#f9fafb',
        bodyColor: '#9ca3af',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
      },
      annotation: undefined,
    },
  }), []);

  const data = useMemo(() => ({
    labels,
    datasets: [
      {
        label: 'Temperature (°C)',
        data: temps,
        borderColor: '#60a5fa',
        backgroundColor: 'rgba(96,165,250,0.08)',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        yAxisID: 'y',
        borderWidth: 2,
      },
      {
        label: 'Humidity (%)',
        data: hums,
        borderColor: '#34d399',
        backgroundColor: 'rgba(52,211,153,0.08)',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        yAxisID: 'y1',
        borderWidth: 2,
      },
      // Temperature threshold lines
      {
        label: `Temp High (${tHigh}°C)`,
        data: Array(readings.length).fill(tHigh),
        borderColor: 'rgba(239,68,68,0.6)',
        borderDash: [6, 4],
        borderWidth: 1.5,
        pointRadius: 0,
        yAxisID: 'y',
        fill: false,
        tension: 0,
      },
      {
        label: `Temp Low (${tLow}°C)`,
        data: Array(readings.length).fill(tLow),
        borderColor: 'rgba(245,158,11,0.6)',
        borderDash: [6, 4],
        borderWidth: 1.5,
        pointRadius: 0,
        yAxisID: 'y',
        fill: false,
        tension: 0,
      },
      // Humidity threshold lines
      {
        label: `Hum High (${hHigh}%)`,
        data: Array(readings.length).fill(hHigh),
        borderColor: 'rgba(239,68,68,0.4)',
        borderDash: [3, 5],
        borderWidth: 1.5,
        pointRadius: 0,
        yAxisID: 'y1',
        fill: false,
        tension: 0,
      },
      {
        label: `Hum Low (${hLow}%)`,
        data: Array(readings.length).fill(hLow),
        borderColor: 'rgba(245,158,11,0.4)',
        borderDash: [3, 5],
        borderWidth: 1.5,
        pointRadius: 0,
        yAxisID: 'y1',
        fill: false,
        tension: 0,
      },
    ],
  }), [labels, temps, hums, tHigh, tLow, hHigh, hLow, readings.length]);

  return (
    <div className="bg-card rounded-2xl p-6 ring-1 ring-white/5">
      <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-widest mb-4">
        Live Sensor Chart
      </h3>
      <div style={{ height: 280 }}>
        {readings.length > 0 ? (
          <Line data={data} options={options} />
        ) : (
          <div className="flex items-center justify-center h-full text-text-secondary text-sm">
            Waiting for data…
          </div>
        )}
      </div>
    </div>
  );
}
