/**
 * Screen 1 of 7 (ROLE-UX-001 §7): Join Session
 * - Participant enters session ID + join token → receives participant_token
 * - D3 (join code format) is an open decision; currently uses two fields
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TPS360ApiClient } from '../lib/api.ts'
import { useSession } from '../context/SessionContext.tsx'

const client = new TPS360ApiClient()

export default function JoinSession() {
  const [sessionId, setSessionId] = useState('')
  const [joinToken, setJoinToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setSession } = useSession()

  async function handleJoin(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const result = await client.joinSession(sessionId.trim(), joinToken.trim())
      setSession(sessionId.trim(), result.participant_token)
      navigate(`/sessions/${sessionId.trim()}/lobby`)
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
        <label>
          ID сесії
          <input
            type="text"
            value={sessionId}
            onChange={e => setSessionId(e.target.value)}
            placeholder="session-uuid"
            required
            style={{ display: 'block', marginTop: '0.5rem', width: '100%' }}
          />
        </label>
        <label style={{ marginTop: '1rem', display: 'block' }}>
          Токен учасника
          <input
            type="text"
            value={joinToken}
            onChange={e => setJoinToken(e.target.value)}
            placeholder="join-token"
            required
            style={{ display: 'block', marginTop: '0.5rem', width: '100%' }}
          />
        </label>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ marginTop: '1rem' }}>
          {loading ? 'Підключення…' : 'Приєднатися'}
        </button>
      </form>
    </main>
  )
}
