/**
 * src/components/shared/Toast.jsx
 *
 * Toast notification system.
 * Usage:
 *   const { toasts, addToast } = useToast()
 *   addToast({ type: 'success', message: 'Done!' })
 *   <ToastContainer toasts={toasts} />
 */
import { useState, useCallback } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'

let _id = 0

const ICONS = {
  success: <CheckCircle size={16} className="text-emerald-600 flex-shrink-0" />,
  error:   <XCircle     size={16} className="text-red-600     flex-shrink-0" />,
  warning: <AlertTriangle size={16} className="text-amber-600 flex-shrink-0" />,
  info:    <Info         size={16} className="text-blue-600   flex-shrink-0" />,
}
const BG = {
  success: '#F0FDF4', error: '#FEF2F2', warning: '#FFFBEB', info: '#EFF6FF',
}
const BORDER = {
  success: '#10B981', error: '#EF4444', warning: '#F59E0B', info: '#3B82F6',
}

function ToastItem({ toast, onDismiss }) {
  return (
    <div
      className="toast-enter flex items-start gap-3 rounded-xl px-4 py-3 shadow-lg max-w-sm"
      style={{
        background: BG[toast.type]   || BG.info,
        borderLeft: `4px solid ${BORDER[toast.type] || BORDER.info}`,
        minWidth: 280,
      }}
    >
      {ICONS[toast.type] || ICONS.info}
      <p className="text-sm text-gray-800 flex-1 font-medium">{toast.message}</p>
      <button onClick={() => onDismiss(toast.id)} className="text-gray-400 hover:text-gray-600">
        <X size={14} />
      </button>
    </div>
  )
}

export function ToastContainer({ toasts, onDismiss }) {
  return (
    <div className="fixed top-4 right-4 z-[300] flex flex-col gap-2">
      {toasts.map(t => <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />)}
    </div>
  )
}

export function useToast() {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback(({ type = 'info', message, duration = 4000 }) => {
    const id = ++_id
    setToasts(prev => [...prev, { id, type, message }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration)
  }, [])

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return { toasts, addToast, dismiss }
}
