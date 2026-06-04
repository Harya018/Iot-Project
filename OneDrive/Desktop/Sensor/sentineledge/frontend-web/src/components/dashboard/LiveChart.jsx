/**
 * src/components/dashboard/LiveChart.jsx
 * Real-time temperature chart using Chart.js.
 *
 * Key safety rules:
 *  - readings prop is ALWAYS treated as potentially empty/null
 *  - ALL .map() calls guarded to run on safeReadings (never undefined)
 *  - Math.min/max spread protected against empty arrays
 *  - No annotation plugin (removed entirely — threshold lines are datasets)
 */
import { useMemo, useRef } from 'react'
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
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { formatTime } from '../../utils/time.js'
import Card from '../shared/Card.jsx'

// Register ALL required Chart.js modules here (once, at module level)
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
)

export default function LiveChart({ readings, thresholds }) {
  const chartRef = useRef(null)

  // ── Safe defaults ────────────────────────────────────────────────────────────
  const safeReadings = Array.isArray(readings) ? readings : []
  const high = thresholds?.temperature?.high ?? 90
  const low  = thresholds?.temperature?.low  ?? 38

  // Early return BEFORE any .map() that could fail
  if (safeReadings.length === 0) {
    return (
      <Card title="Live Temperature" subtitle="Real-time sensor data">
        <div style={{ height: 260 }} className="flex items-center justify-center text-gray-400 text-sm">
          <div className="text-center">
            <div className="text-2xl mb-2">📡</div>
            <p>Waiting for live data…</p>
            <p className="text-xs text-gray-300 mt-1">Sensor readings appear here in real time</p>
          </div>
        </div>
      </Card>
    )
  }

  // ── Derived data (only runs when safeReadings.length > 0) ───────────────────
  return <LiveChartInner readings={safeReadings} high={high} low={low} chartRef={chartRef} />
}

// Split inner component so hooks / useMemo only run with valid data
function LiveChartInner({ readings, high, low, chartRef }) {
  const temps = readings.map(r => (typeof r?.temperature === 'number' ? r.temperature : null))
  const validTemps = temps.filter(t => t !== null)

  const minY = validTemps.length
    ? Math.floor(Math.min(...validTemps) - 2, low - 3)
    : low - 5
  const maxY = validTemps.length
    ? Math.ceil(Math.max(...validTemps) + 2, high + 3)
    : high + 5

  const labels = readings.map((r, i) =>
    i % 10 === 0 ? (formatTime(r?.timestamp) || '') : ''
  )

  const data = useMemo(() => ({
    labels,
    datasets: [
      {
        label: 'Temperature (°C)',
        data: temps,
        borderColor: '#7C3AED',
        backgroundColor: (ctx) => {
          try {
            const chart = ctx.chart
            const { ctx: c, chartArea } = chart
            if (!chartArea) return 'rgba(124,58,237,0.05)'
            const grad = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
            grad.addColorStop(0, 'rgba(124,58,237,0.18)')
            grad.addColorStop(1, 'rgba(124,58,237,0.01)')
            return grad
          } catch { return 'rgba(124,58,237,0.05)' }
        },
        borderWidth: 2,
        pointRadius: readings.map(r =>
          (r?.breaches?.length ?? 0) > 0 ? 5 : 0
        ),
        pointBackgroundColor: readings.map(r =>
          (r?.breaches?.length ?? 0) > 0 ? '#EF4444' : '#7C3AED'
        ),
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        tension: 0.4,
        fill: true,
        spanGaps: true,
      },
      {
        label: `High: ${high}°C`,
        data: readings.map(() => high),
        borderColor: '#EF4444',
        borderDash: [6, 3],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
      {
        label: `Low: ${low}°C`,
        data: readings.map(() => low),
        borderColor: '#3B82F6',
        borderDash: [6, 3],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
    ],
  }), [readings, high, low, temps, labels]) // eslint-disable-line

  const options = useMemo(() => ({
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: { size: 11, family: 'Inter' },
          color: '#6B7280',
          padding: 16,
          usePointStyle: true,
          pointStyleWidth: 8,
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            if (ctx.datasetIndex === 0) return ` ${ctx.parsed.y?.toFixed(1) ?? '—'}°C`
            return ` ${ctx.dataset.label}`
          },
          title: (items) => {
            const idx = items[0]?.dataIndex
            if (idx !== undefined && readings[idx]) {
              return formatTime(readings[idx]?.timestamp) || ''
            }
            return ''
          },
        },
        backgroundColor: '#1F2937',
        titleFont: { size: 11, family: 'Inter' },
        bodyFont:  { size: 12, family: 'Inter', weight: '600' },
        padding: 10,
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        grid: { color: '#F3F4F6' },
        ticks: {
          font: { size: 10, family: 'Inter' },
          color: '#9CA3AF',
          maxRotation: 0,
        },
      },
      y: {
        min: Math.min(minY, low - 2),
        max: Math.max(maxY, high + 2),
        grid: { color: '#F3F4F6' },
        ticks: {
          font: { size: 10, family: 'Inter' },
          color: '#9CA3AF',
          callback: v => `${v}°C`,
        },
      },
    },
  }), [readings, minY, maxY, high, low]) // eslint-disable-line

  const lastTs = formatTime(readings.at(-1)?.timestamp) || '—'

  return (
    <Card
      title="Live Temperature"
      subtitle="Real-time sensor data"
      headerRight={
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">Updated {lastTs}</span>
          <span className="text-xs font-semibold bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
            {readings.length} readings
          </span>
        </div>
      }
    >
      <div style={{ height: 260 }}>
        <Line ref={chartRef} data={data} options={options} />
      </div>
    </Card>
  )
}
