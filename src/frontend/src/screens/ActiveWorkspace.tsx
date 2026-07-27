/**
 * Screen 4 of 7 (ROLE-UX-001 §7): Active Simulation Workspace
 * - Real-time inject feed via SSE (C2 phase)
 * - For now renders session ID and provides navigation to inject detail
 */
import { useParams, useNavigate } from 'react-router-dom'

export default function ActiveWorkspace() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  return (
    <main style={{ padding: '2rem', maxWidth: 860, margin: '0 auto' }}>
      <h2>Симуляція — Сесія {sessionId}</h2>
      <p>TODO: підключити SSE-стрім інджектів (C2 фаза)</p>
      <button onClick={() => navigate(`/sessions/${sessionId}/completion`)}>
        Завершити сесію
      </button>
    </main>
  )
}
