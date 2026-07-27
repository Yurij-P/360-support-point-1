/**
 * Screen 5 of 7 (ROLE-UX-001 §7): Inject Detail
 * - Shows full inject content for participant review
 * - Links to decision submission
 */
import { useParams, useNavigate } from 'react-router-dom'

export default function InjectDetail() {
  const { sessionId, injectId } = useParams<{ sessionId: string; injectId: string }>()
  const navigate = useNavigate()

  return (
    <main style={{ padding: '2rem', maxWidth: 720, margin: '0 auto' }}>
      <h2>Інджект</h2>
      <p>Сесія: {sessionId} / Інджект: {injectId}</p>
      <p>TODO: завантажити деталі інджекту з API</p>
      <button onClick={() => navigate(`/sessions/${sessionId}/workspace/injects/${injectId}/decision`)}>
        Підготувати рішення →
      </button>
    </main>
  )
}
