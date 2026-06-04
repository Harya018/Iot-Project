/** src/components/shared/AdminGuard.jsx */
import { Lock } from 'lucide-react'

export default function AdminGuard({ children, isAdmin, onUnlock, message = 'Admin access required to manage this section.' }) {
  if (isAdmin) return children

  return (
    <div className="relative">
      <div className="opacity-30 pointer-events-none select-none">
        {children}
      </div>
      <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm rounded-xl">
        <div className="flex flex-col items-center gap-3 p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
            <Lock size={22} className="text-gray-500" />
          </div>
          <p className="text-sm font-medium text-gray-700 max-w-xs">{message}</p>
          <button
            onClick={onUnlock}
            className="btn btn-primary btn-sm mt-1"
          >
            <Lock size={13} /> Unlock
          </button>
        </div>
      </div>
    </div>
  )
}
