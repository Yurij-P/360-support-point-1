/**
 * Screen 4 of 7 (ROLE-UX-001 §7): Active Simulation Workspace
 * - Loads participant view + all visible injects
 * - SSE subscription refreshes view on server events
 */
import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { TPS360ApiClient } from '../lib/api.ts'
import { useSession } from '../context/SessionContext.tsx'

const client = new TPS360ApiClient()

interface InjectSummary {
  id: string
  title: string
  description: string
  sent_at: string
}

export default function ActiveWorkspace() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const { participantToken } = useSession()
  const navigate = useNavigate()
  const [injects, setInjects] = useState<InjectSummary[]>([])
  const [sessionStatus, setSessionStatus] = useState<string>('Завантаження…')
  const [error, setError] = useState<string | null>(null)

  const loadView = useCallback(() => {
    if (!sessionId || !participantToken) return
    client
      .getParticipantView(sessionId, participantToken)
      .then(v => {
        setInjects(v.injects)
        setSessionStatus(v.session_status)
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Помилка'))
  }, [sessionId, participantToken])

  useEffect(() => {
    loadView()
    if (!sessionId) return
    const es = client.subscribeToSessionEvents(sessionId, () => loadView())
    return () => es.close()
  }, [sessionId, loadView])

  if (error) return <p style={{ color: 'red', padding: '2rem' }}>{error}</p>

  return (
    <main style={{ padding: '2rem', maxWidth: 860, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Симуляція</h2>
        <span style={{ background: '#f1f5f9', borderRadius: 6, padding: '0.25rem 0.75rem', fontSize: '0.9rem' }}>
          {sessionStatus}
        </span>
      </div>

      <h3>Ваші інджекти ({injects.length})</h3>
      {injects.length === 0 ? (
        <p style={{ color: '#888' }}>Очікуйте інджектів від фасилітатора…</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {injects.map(inj => (
            <li
              key={inj.id}
              style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '0.5rem', cursor: 'pointer' }}
              onClick={() => navigate(`/sessions/${sessionId}/workspace/injects/${inj.id}`)}
            >
              <strong>{inj.title}</strong>
              <span style={{ marginLeft: '0.75rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                {new Date(inj.sent_at).toLocaleTimeString('uk-UA')}
              </span>
              <p style={{ margin: '0.25rem 0 0', color: '#555', fontSize: '0.9rem' }}>{inj.description.slice(0, 120)}…</p>
            </li>
          ))}
        </ul>
      )}

      <button
        style={{ marginTop: '2rem' }}
        onClick={() => navigate(`/sessions/${sessionId}/completion`)}
      >
        Завершити участь
      </button>
    </main>
  )
}
