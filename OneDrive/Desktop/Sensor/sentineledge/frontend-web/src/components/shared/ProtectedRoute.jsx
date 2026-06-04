/** src/components/shared/ProtectedRoute.jsx */
import { Navigate } from 'react-router-dom'

export default function ProtectedRoute({ children }) {
  const isAuthed = sessionStorage.getItem('authenticated') === 'true'
  return isAuthed ? children : <Navigate to="/" replace />
}
