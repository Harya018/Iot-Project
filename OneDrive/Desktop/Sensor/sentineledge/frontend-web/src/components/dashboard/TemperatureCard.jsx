/**
 * src/components/dashboard/TemperatureCard.jsx
 * Hero stat card — current temperature + severity status.
 * All props are fully optional/null-safe.
 */
import { Thermometer, AlertTriangle } from 'lucide-react'
import { utcToIST } from '../../utils/time.js'
import { getSeverityColor, getSeverityLabel, getTempColor, getTempBorderClass } from '../../utils/severity.js'
import Badge from '../shared/Badge.jsx'

function severity2badge(s) {
  const m = { NORMAL:'green', WARNING:'amber', CRITICAL:'orange', EMERGENCY:'red' }
  return m[String(s ?? '').toUpperCase()] || 'green'
}

export default function TemperatureCard({ reading, thresholds }) {
  // All properties safely extracted with defaults
  const temp      = reading?.temperature ?? null
  const ts        = reading?.timestamp   ?? null
  const breaches  = Array.isArray(reading?.breaches) ? reading.breaches : []
  const hasBreach = breaches.length > 0
  const topBreach = breaches[0] ?? null
  const sev       = topBreach?.severity || (hasBreach ? 'WARNING' : 'NORMAL')
  const sevUp     = String(sev).toUpperCase()
  const tempColor = hasBreach ? getTempColor(sev) : '#1F2937'

  const high = thresholds?.temperature?.high ?? 90
  const low  = thresholds?.temperature?.low  ?? 38

  const borderClass = hasBreach ? getTempBorderClass(sev) : ''
  const isEmergency = sevUp === 'EMERGENCY'

  // Display value
  const displayTemp = typeof temp === 'number' ? temp.toFixed(1) : '—'

  return (
    <div
      className={`card p-5 flex flex-col gap-3 ${borderClass} transition-all duration-500
        ${isEmergency ? 'animate-flash-red' : ''}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Thermometer size={18} className="text-purple-500" />
          <span className="text-sm font-semibold text-gray-700">Temperature</span>
        </div>
        <Badge
          color={severity2badge(sev)}
          label={hasBreach ? getSeverityLabel(sev) : 'NORMAL'}
          pulse={isEmergency}
        />
      </div>

      {/* Big number */}
      <div className="flex items-end gap-2">
        <span
          className="temp-value animate-pulse-num"
          style={{ color: tempColor }}
        >
          {displayTemp}
        </span>
        <span className="text-2xl font-semibold text-gray-400 mb-2">°C</span>
      </div>

      {/* Breach banner */}
      {hasBreach && topBreach && (
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg"
          style={{ background: getSeverityColor(sev)?.bg ?? '#FEF2F2' }}
        >
          <AlertTriangle size={14} style={{ color: getSeverityColor(sev)?.dot ?? '#EF4444', flexShrink: 0 }} />
          <span className="text-xs font-semibold" style={{ color: getSeverityColor(sev)?.text ?? '#991B1B' }}>
            BREACH ACTIVE — {getSeverityLabel(sev)} ·{' '}
            {topBreach.direction === 'high' ? 'Above' : 'Below'} threshold
          </span>
        </div>
      )}

      {/* Loading state when no data yet */}
      {!reading && (
        <div className="text-xs text-gray-400 text-center py-1">Connecting to sensor…</div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-auto pt-1 border-t border-gray-100">
        <span className="text-xs text-gray-400">Normal: {low}°C – {high}°C</span>
        <span className="text-xs text-gray-400">{ts ? utcToIST(ts) : 'No data yet'}</span>
      </div>
    </div>
  )
}
