/** src/components/shared/Card.jsx */
export default function Card({ title, subtitle, headerRight, children, className = '', noPadding = false }) {
  return (
    <div className={`card ${className}`}>
      {(title || headerRight) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div>
            <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {headerRight && <div className="flex items-center gap-2">{headerRight}</div>}
        </div>
      )}
      <div className={noPadding ? '' : 'p-5'}>{children}</div>
    </div>
  )
}
