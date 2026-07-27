/**
 * Screen 2 of 7 (ROLE-UX-001 §7): Lobby / Readiness
 * - Shows session lifecycle status
 * - Facilitator can start the session once all participants are ready
 */
import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { TPS360ApiClient } from '../lib/api.ts'

const client = new TPS360ApiClient()

export default function Lobby() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [lifecycle, setLifecycle] = useState<string>('Завантаження…')

  useEffect(() => {
    if (!sessionId) return
    client
      .getSession(sessionId)
      .then(s => setLifecycle(s.lifecycle))
      .catch(err => setLifecycle(err instanceof Error ? err.message : 'Помилка'))
  }, [sessionId])

  return (
    <main style={{ padding: '2rem', maxWidth: 640, margin: '0 auto' }}>
      <h2>Лобі — Сесія {sessionId}</h2>
      <p>Статус: <strong>{lifecycle}</strong></p>
      <button onClick={() => navigate(`/sessions/${sessionId}/briefing`)}>
        До брифінгу →
      </button>
    </main>
  )
}
