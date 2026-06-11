/**
 * src/components/dashboard/SensorCard.jsx
 * Generic sensor stat card — matches TemperatureCard style exactly.
 *
 * Props:
 *   icon      : lucide-react component
 *   iconColor : string (tailwind or hex)
 *   label     : string — e.g. "Pressure"
 *   value     : string | number | null
 *   unit      : string — e.g. "bar"
 *   subtitle  : string — static info line below value
 *   footer    : string — small bottom line (optional)
 */
import React from 'react'

export default function SensorCard({ icon: Icon, iconColor = '#7C3AED', label, value, unit, subtitle, footer }) {
  return (
    <div className="card p-5 flex flex-col gap-3 transition-all duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {Icon && <Icon size={18} style={{ color: iconColor }} />}
          <span className="text-sm font-semibold text-gray-700">{label}</span>
        </div>
        <span
          className="text-xs font-semibold px-2 py-0.5 rounded-full"
          style={{ background: '#F3F0FF', color: '#7C3AED' }}
        >
          LIVE
        </span>
      </div>

      {/* Big number */}
      <div className="flex items-end gap-2">
        <span className="temp-value" style={{ color: '#1F2937' }}>
          {value !== null && value !== undefined ? value : '—'}
        </span>
        <span className="text-2xl font-semibold text-gray-400 mb-2">{unit}</span>
      </div>

      {/* Subtitle */}
      {subtitle && (
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg"
          style={{ background: '#F8F7FF' }}
        >
          <span className="text-xs font-medium" style={{ color: '#6D28D9' }}>
            {subtitle}
          </span>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-auto pt-1 border-t border-gray-100">
        <span className="text-xs text-gray-400">{footer ?? `Live ${label} reading`}</span>
        <span className="text-xs text-gray-400">Auto-refresh 3s</span>
      </div>
    </div>
  )
}
