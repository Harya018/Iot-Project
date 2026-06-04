/**
 * src/utils/severity.js — Severity colour mapping and labels
 */

const SEVERITY_MAP = {
  NORMAL: {
    bg: '#ECFDF5', text: '#065F46', border: '#10B981', dot: '#10B981',
    tailwind: 'text-emerald-800 bg-emerald-50 border-emerald-500',
  },
  WARNING: {
    bg: '#FFFBEB', text: '#92400E', border: '#F59E0B', dot: '#F59E0B',
    tailwind: 'text-amber-800 bg-amber-50 border-amber-500',
  },
  CRITICAL: {
    bg: '#FFF7ED', text: '#9A3412', border: '#F97316', dot: '#F97316',
    tailwind: 'text-orange-800 bg-orange-50 border-orange-500',
  },
  EMERGENCY: {
    bg: '#FEF2F2', text: '#991B1B', border: '#EF4444', dot: '#EF4444',
    tailwind: 'text-red-800 bg-red-50 border-red-500',
  },
}

export function getSeverityColor(severity) {
  return SEVERITY_MAP[severity?.toUpperCase()] || SEVERITY_MAP.NORMAL
}

export function getDirectionLabel(direction) {
  if (direction === 'high') return 'Above threshold'
  if (direction === 'low')  return 'Below threshold'
  return direction || '—'
}

export function getSeverityLabel(severity) {
  if (!severity) return 'Normal'
  return severity.charAt(0).toUpperCase() + severity.slice(1).toLowerCase()
}

/** Tailwind border class for temperature card */
export function getTempBorderClass(severity) {
  const s = severity?.toUpperCase()
  if (s === 'EMERGENCY') return 'border-2 border-red-500 animate-flash-red'
  if (s === 'CRITICAL')  return 'border-2 border-orange-400'
  if (s === 'WARNING')   return 'border-2 border-amber-400'
  return ''
}

/** Hex color for the temperature number itself */
export function getTempColor(severity) {
  const s = severity?.toUpperCase()
  if (s === 'EMERGENCY') return '#EF4444'
  if (s === 'CRITICAL')  return '#F97316'
  if (s === 'WARNING')   return '#F59E0B'
  return '#10B981'
}
