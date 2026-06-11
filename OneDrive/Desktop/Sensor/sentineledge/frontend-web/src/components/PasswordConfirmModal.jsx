/**
 * src/components/PasswordConfirmModal.jsx
 *
 * Reusable admin password confirmation modal.
 * Shows BEFORE any data-modifying action in the dashboard.
 *
 * Props:
 *   isOpen      : bool   — controls visibility
 *   actionLabel : string — e.g. "Update Thresholds", "Remove Subscriber"
 *   onConfirm   : (password: string) => void — called when Confirm is clicked
 *   onCancel    : () => void — called when Cancel is clicked or modal is closed
 *   error       : string | null — shown in red if the backend returned 401
 */
import { useState, useEffect, useRef } from 'react'
import { ShieldCheck, X } from 'lucide-react'

export default function PasswordConfirmModal({
  isOpen,
  actionLabel = 'perform this action',
  onConfirm,
  onCancel,
  error = null,
}) {
  const [password, setPassword] = useState('')
  const inputRef = useRef(null)

  // Reset and focus on open
  useEffect(() => {
    if (isOpen) {
      setPassword('')
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return
    const handler = (e) => { if (e.key === 'Escape') onCancel() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isOpen, onCancel])

  if (!isOpen) return null

  const handleConfirm = () => {
    if (!password.trim()) return
    onConfirm(password.trim())
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleConfirm()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.55)' }}
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl p-6 flex flex-col gap-4"
        style={{ width: '100%', maxWidth: 380 }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: '#EDE9FE' }}
            >
              <ShieldCheck size={16} style={{ color: '#7C3AED' }} />
            </div>
            <h2 className="text-base font-bold text-gray-900">Confirm Action</h2>
          </div>
          <button
            onClick={onCancel}
            className="p-1 rounded-lg hover:bg-gray-100 text-gray-400"
          >
            <X size={16} />
          </button>
        </div>

        {/* Subtitle */}
        <p className="text-sm text-gray-500">
          Enter admin password to <span className="font-semibold text-gray-700">{actionLabel}</span>
        </p>

        {/* Password input */}
        <input
          ref={inputRef}
          type="password"
          placeholder="Admin password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyDown={handleKeyDown}
          className="form-input"
          autoComplete="current-password"
        />

        {/* Error */}
        {error && (
          <p className="text-xs text-red-600 font-medium">{error}</p>
        )}

        {/* Buttons */}
        <div className="flex gap-2 justify-end mt-1">
          <button
            onClick={onCancel}
            className="btn btn-ghost btn-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!password.trim()}
            className="btn btn-primary btn-sm"
            style={{ background: '#7C3AED' }}
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  )
}
