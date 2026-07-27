/**
 * Screen 3 of 7 (ROLE-UX-001 §7): Role and Participant Briefing
 * - Loads role profile via GET /sessions/{id}/roles/me (server-authorized)
 * - Role data is NEVER hardcoded — always fetched from API
 */
import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getMyRole, type ParticipantRoleView } from '../lib/api.ts'
import { useSession } from '../context/SessionContext.tsx'

export default function RoleBriefing() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const { participantToken } = useSession()
  const navigate = useNavigate()
  const [role, setRole] = useState<ParticipantRoleView | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId || !participantToken) return
    getMyRole(sessionId, participantToken)
      .then(setRole)
      .catch(err => setError(err instanceof Error ? err.message : 'Помилка завантаження ролі'))
  }, [sessionId, participantToken])

  if (error) return <p style={{ color: 'red', padding: '2rem' }}>{error}</p>
  if (!role) return <p style={{ padding: '2rem' }}>Завантаження ролі…</p>

  return (
    <main style={{ padding: '2rem', maxWidth: 720, margin: '0 auto' }}>
      <h2>Ваша роль: {role.display_name}</h2>
      <p><strong>Категорія:</strong> {role.category_label}</p>
      <p>{role.description}</p>
      <h3>Типові рішення</h3>
      <ul>{role.typical_decisions.map((d, i) => <li key={i}>{d}</li>)}</ul>
      <h3>Джерела інформації</h3>
      <ul>{role.information_sources.map((s, i) => <li key={i}>{s}</li>)}</ul>
      <h3>Повноваження</h3>
      <p>{role.decision_authority}</p>
      <button onClick={() => navigate(`/sessions/${sessionId}/workspace`)}>
        До симуляції →
      </button>
    </main>
  )
}
