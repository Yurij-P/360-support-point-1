/**
 * Screen 6 of 7 (ROLE-UX-001 §7): Decision Preparation and Submission
 * - LEGO Decision Cards interface
 * - Submits decision via POST /sessions/{id}/participants/{pid}/decisions
 */
import { useParams, useNavigate } from 'react-router-dom'

export default function DecisionSubmission() {
  const { sessionId, injectId } = useParams<{ sessionId: string; injectId: string }>()
  const navigate = useNavigate()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    // TODO: POST decision to API
    navigate(`/sessions/${sessionId}/workspace`)
  }

  return (
    <main style={{ padding: '2rem', maxWidth: 720, margin: '0 auto' }}>
      <h2>Рішення по інджекту {injectId}</h2>
      <form onSubmit={handleSubmit}>
        <p>TODO: LEGO Decision Cards (C2 фаза)</p>
        <button type="submit">Надіслати рішення</button>
      </form>
    </main>
  )
}
