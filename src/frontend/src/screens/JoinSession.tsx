/**
 * Screen 1 of 7 (ROLE-UX-001 §7): Join Session
 * D3 decision: join code is one combined string "{session_id}|{join_token}"
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TPS360ApiClient } from '../lib/api.ts'
import { useSession } from '../context/SessionContext.tsx'

const client = new TPS360ApiClient()

export default function JoinSession() {
  const [code, setCode] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setSession } = useSession()

  async function handleJoin(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const parts = code.trim().split('|')
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
      setError('Невірний формат коду. Очікується "session_id|join_token"')
      return
    }
    const [sessionId, joinToken] = parts
    setLoading(true)
    try {
      const result = await client.joinSession(sessionId, joinToken, displayName.trim())
      setSession(sessionId, result.participant_token)
      navigate(`/sessions/${sessionId}/lobby`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка приєднання')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{ padding: '2rem', maxWidth: 480, margin: '0 auto' }}>
      <h1>TPS360</h1>
      <h2>Приєднатися до сесії</h2>
      <form onSubmit={handleJoin}>
        <label style={{ display: 'block' }}>
          {`Ваше ім'я`}
          <input
            type="text"
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
            placeholder="Іван Петренко"
            required
            style={{ display: 'block', marginTop: '0.5rem', width: '100%', fontSize: '1rem' }}
          />
        </label>
        <label style={{ display: 'block', marginTop: '1rem' }}>
          Код сесії
          <input
            type="text"
            value={code}
            onChange={e => setCode(e.target.value)}
            placeholder="session-uuid|join-token"
            required
            style={{ display: 'block', marginTop: '0.5rem', width: '100%', fontFamily: 'monospace', fontSize: '0.9rem' }}
          />
        </label>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ marginTop: '1rem' }}>
          {loading ? 'Підключення…' : 'Приєднатися'}
        </button>
      </form>
      <hr style={{ margin: '2rem 0' }} />
      <p style={{ color: '#666' }}>
        Ви фасилітатор? <a href="/create">Створити нову сесію</a>
      </p>
    </main>
  )
}