/** src/components/shared/Badge.jsx */
const COLORS = {
  green:  { bg: '#ECFDF5', text: '#065F46', dot: '#10B981' },
  amber:  { bg: '#FFFBEB', text: '#92400E', dot: '#F59E0B' },
  orange: { bg: '#FFF7ED', text: '#9A3412', dot: '#F97316' },
  red:    { bg: '#FEF2F2', text: '#991B1B', dot: '#EF4444' },
  blue:   { bg: '#EFF6FF', text: '#1E40AF', dot: '#3B82F6' },
  gray:   { bg: '#F3F4F6', text: '#374151', dot: '#9CA3AF' },
  purple: { bg: '#F5F3FF', text: '#5B21B6', dot: '#7C3AED' },
}

export default function Badge({ color = 'gray', label, pulse = false, dot = true, small = false }) {
  const c = COLORS[color] || COLORS.gray
  return (
    <span
      style={{ background: c.bg, color: c.text }}
      className={`inline-flex items-center gap-1.5 rounded-full font-medium
        ${small ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'}`}
    >
      {dot && (
        <span
          style={{ background: c.dot }}
          className={`status-dot flex-shrink-0 ${pulse ? 'animate-ping-slow' : ''}`}
        />
      )}
      {label}
    </span>
  )
}
