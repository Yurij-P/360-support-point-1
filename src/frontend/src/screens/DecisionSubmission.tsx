/**
 * Screen 6 of 7 (ROLE-UX-001 §7): Decision Preparation and Submission
 * - Free-text decision (LEGO cards UI planned for C3)
 * - POST /sessions/{id}/injects/{inject_id}/decisions
 */
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { TPS360ApiClient } from '../lib/api.ts'
import { useSession } from '../context/SessionContext.tsx'

const client = new TPS360ApiClient()

export default function DecisionSubmission() {
  const { sessionId, injectId } = useParams<{ sessionId: string; injectId: string }>()
  const { participantToken } = useSession()
  const navigate = useNavigate()
  const [decisionText, setDecisionText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!sessionId || !injectId || !participantToken) return
    setError(null)
    setLoading(true)
    try {
      await client.submitDecision(sessionId, injectId, participantToken, {
        text: decisionText.trim(),
        action: 'manual',
      })
      navigate(`/sessions/${sessionId}/workspace`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка відправки')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{ padding: '2rem', maxWidth: 720, margin: '0 auto' }}>
      <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', marginBottom: '1rem', color: '#3b82f6' }}>
        ← Назад
      </button>
      <h2>Рішення</h2>
      <p style={{ color: '#64748b', fontSize: '0.85rem' }}>Інджект: {injectId}</p>
      <form onSubmit={handleSubmit}>
        <label style={{ display: 'block' }}>
          Ваше рішення
          <textarea
            value={decisionText}
            onChange={e => setDecisionText(e.target.value)}
            placeholder="Опишіть ваше рішення, дії, ресурси що задіяні…"
            required
            rows={6}
            style={{ display: 'block', width: '100%', marginTop: '0.5rem', fontSize: '1rem' }}
          />
        </label>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ marginTop: '1rem' }}>
          {loading ? 'Відправка…' : 'Надіслати рішення'}
        </button>
      </form>
    </main>
  )
}
