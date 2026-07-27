/**
 * Screen 2 of 7 (ROLE-UX-001 §7): Lobby / Readiness
 * - Shows live lobby status from GET /sessions/{id}/lobby-status
 * - Participant sees count and readiness; facilitator sees can_start
 */
import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { TPS360ApiClient } from '../lib/api.ts'

const client = new TPS360ApiClient()

interface LobbyStatus {
  capacity: number
  connected_count: number
  assigned_count: number
  can_start: boolean
  readiness_message: string
  participants: Array<{ participant_id: string; display_name: string; role_id: string | null }>
}

export default function Lobby() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [lobby, setLobby] = useState<LobbyStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    client
      .getLobbyStatus(sessionId)
      .then(setLobby)
      .catch(err => setError(err instanceof Error ? err.message : 'Помилка лобі'))

    const interval = setInterval(() => {
      if (!sessionId) return
      client.getLobbyStatus(sessionId).then(setLobby).catch(() => {})
    }, 5000)
    return () => clearInterval(interval)
  }, [sessionId])

  if (error) return <p style={{ color: 'red', padding: '2rem' }}>{error}</p>
  if (!lobby) return <p style={{ padding: '2rem' }}>Завантаження лобі…</p>

  return (
    <main style={{ padding: '2rem', maxWidth: 640, margin: '0 auto' }}>
      <h2>Лобі — Сесія {sessionId}</h2>
      <p>
        <strong>{lobby.connected_count}</strong> / {lobby.capacity} учасників
        {lobby.assigned_count > 0 && ` · ${lobby.assigned_count} з роллю`}
      </p>
      <p style={{ color: lobby.can_start ? 'green' : '#888' }}>{lobby.readiness_message}</p>

      {lobby.participants.length > 0 && (
        <ul>
          {lobby.participants.map(p => (
            <li key={p.participant_id}>
              {p.display_name} {p.role_id ? `✅` : '⏳'}
            </li>
          ))}
        </ul>
      )}

      <button
        onClick={() => navigate(`/sessions/${sessionId}/briefing`)}
        style={{ marginTop: '1rem' }}
      >
        До брифінгу →
      </button>
    </main>
  )
}
