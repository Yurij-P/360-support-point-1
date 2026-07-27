/**
 * Screen 5 of 7 (ROLE-UX-001 §7): Inject Detail
 * - Loads inject from participant view, matches by injectId URL param
 */
import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { TPS360ApiClient } from '../lib/api.ts'
import { useSession } from '../context/SessionContext.tsx'

const client = new TPS360ApiClient()

interface Inject {
  id: string
  title: string
  description: string
  sent_at: string
}

export default function InjectDetail() {
  const { sessionId, injectId } = useParams<{ sessionId: string; injectId: string }>()
  const { participantToken } = useSession()
  const navigate = useNavigate()
  const [inject, setInject] = useState<Inject | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    if (!sessionId || !participantToken || !injectId) return
    client
      .getParticipantView(sessionId, participantToken)
      .then(v => {
        const found = v.injects.find(i => i.id === injectId)
        if (!found) throw new Error('Інджект не знайдено або недоступний')
        setInject(found)
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Помилка'))
  }, [sessionId, participantToken, injectId])

  useEffect(() => { load() }, [load])

  if (error) return <p style={{ color: 'red', padding: '2rem' }}>{error}</p>
  if (!inject) return <p style={{ padding: '2rem' }}>Завантаження…</p>

  return (
    <main style={{ padding: '2rem', maxWidth: 720, margin: '0 auto' }}>
      <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', marginBottom: '1rem', color: '#3b82f6' }}>
        ← Назад
      </button>
      <h2>{inject.title}</h2>
      <p style={{ color: '#64748b', fontSize: '0.85rem' }}>
        {new Date(inject.sent_at).toLocaleString('uk-UA')}
      </p>
      <p style={{ lineHeight: 1.7, marginTop: '1rem' }}>{inject.description}</p>
      <button
        style={{ marginTop: '1.5rem' }}
        onClick={() => navigate(`/sessions/${sessionId}/workspace/injects/${injectId}/decision`)}
      >
        Підготувати рішення →
      </button>
    </main>
  )
}
