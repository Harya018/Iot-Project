/**
 * src/pages/LoginPage.jsx
 * Full-screen passcode login. Passcode: 1234 (hardcoded for now).
 * On success → stores 'authenticated' in sessionStorage → navigates to /dashboard.
 */
import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Thermometer } from 'lucide-react'

const PASSCODE = '1234'

export default function LoginPage() {
  const [pin,     setPin]     = useState('')
  const [error,   setError]   = useState('')
  const [shaking, setShaking] = useState(false)
  const inputRef  = useRef(null)
  const navigate  = useNavigate()

  // If already authenticated, skip login
  useEffect(() => {
    if (sessionStorage.getItem('authenticated') === 'true') {
      navigate('/dashboard', { replace: true })
    }
    inputRef.current?.focus()
  }, [navigate])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (pin === PASSCODE) {
      sessionStorage.setItem('authenticated', 'true')
      navigate('/dashboard', { replace: true })
    } else {
      setShaking(true)
      setError('Incorrect passcode. Please try again.')
      setPin('')
      setTimeout(() => setShaking(false), 500)
      inputRef.current?.focus()
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ background: 'linear-gradient(135deg, #1E1B4B 0%, #2D2680 50%, #1E1B4B 100%)' }}
    >
      {/* Background pattern */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="absolute rounded-full opacity-5"
            style={{
              width: `${120 + i * 80}px`,
              height: `${120 + i * 80}px`,
              border: '1px solid #fff',
              top: `${10 + i * 12}%`,
              left: `${5 + i * 15}%`,
            }}
          />
        ))}
      </div>

      <div
        className={`relative bg-white rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-6
          transition-all duration-150 ${shaking ? 'animate-shake' : ''}`}
        style={{ width: '100%', maxWidth: 380 }}
      >
        {/* Logo */}
        <div className="flex flex-col items-center gap-3">
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg"
            style={{ background: 'linear-gradient(135deg, #7C3AED, #5B21B6)' }}
          >
            <Thermometer size={30} className="text-white" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">SentinelEdge</h1>
            <p className="text-sm font-medium text-gray-500 mt-0.5">Admin Dashboard</p>
          </div>
        </div>

        {/* Divider */}
        <div className="w-full border-t border-gray-100" />

        {/* Form */}
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 text-center">
              Enter Passcode
            </label>
            <input
              ref={inputRef}
              type="password"
              inputMode="numeric"
              maxLength={6}
              placeholder="••••"
              value={pin}
              onChange={e => {
                setPin(e.target.value.replace(/\D/g, ''))
                setError('')
              }}
              className="form-input text-center text-2xl tracking-[0.5em] font-bold"
              style={{ letterSpacing: '0.5em' }}
              autoComplete="off"
            />
          </div>

          {error && (
            <p className="text-xs text-red-600 text-center font-medium">{error}</p>
          )}

          <button
            type="submit"
            disabled={pin.length < 4}
            className="btn btn-primary w-full justify-center py-3 text-base font-semibold"
            style={{ background: '#7C3AED' }}
          >
            Enter Dashboard
          </button>
        </form>

        <p className="text-xs text-gray-400 text-center">
          SentinelEdge v1.0.0 · IoT Temperature Monitoring
        </p>
      </div>

      {/* Shake keyframe */}
      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          20% { transform: translateX(-8px); }
          40% { transform: translateX(8px); }
          60% { transform: translateX(-6px); }
          80% { transform: translateX(6px); }
        }
        .animate-shake { animation: shake 0.45s ease-in-out; }
      `}</style>
    </div>
  )
}
