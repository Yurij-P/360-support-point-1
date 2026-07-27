/**
 * Screen 7 of 7 (ROLE-UX-001 §7): Completion and Individual Reflection
 * - Shows session summary and personal AAR reflection prompt
 */
import { useParams } from 'react-router-dom'

export default function Completion() {
  const { sessionId } = useParams<{ sessionId: string }>()

  return (
    <main style={{ padding: '2rem', maxWidth: 720, margin: '0 auto' }}>
      <h2>Сесію завершено</h2>
      <p>Сесія: {sessionId}</p>
      <p>TODO: завантажити індивідуальне резюме та AAR-форму (C3 фаза)</p>
    </main>
  )
}
