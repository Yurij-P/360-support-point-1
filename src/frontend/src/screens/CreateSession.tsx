/**
 * Facilitator screen: browse Community Catalog, create a session, get the join code.
 * D3: join code shared with participants = "{session_id}|{join_token}"
 */
import { useEffect, useState } from 'react'
import { TPS360ApiClient, type CommunityCatalogItem } from '../lib/api.ts'
import { useSession } from '../context/SessionContext.tsx'

const client = new TPS360ApiClient()

interface CreatedSession {
  id: string
  facilitator_token: string
  join_token: string
  joinCode: string
}

export default function CreateSession() {
  const [communities, setCommunities] = useState<CommunityCatalogItem[]>([])
  const [communityId, setCommunityId] = useState('')
  const [facilitatorName, setFacilitatorName] = useState('')
  const [playerCapacity, setPlayerCapacity] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [created, setCreated] = useState<CreatedSession | null>(null)
  const [copied, setCopied] = useState(false)
  const { setFacilitator } = useSession()

  useEffect(() => {
    client.fetchCommunitiesCatalog()
      .then(setCommunities)
      .catch(err => setError(err instanceof Error ? err.message : 'Помилка каталогу'))
  }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const session = await client.createSession({
        communityId,
        facilitatorName: facilitatorName.trim(),
        playerCapacity,
      })
      const joinCode = `${session.id}|${session.join_token}`
      setFacilitator(session.id, session.facilitator_token)
      setCreated({ ...session, joinCode })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка створення сесії')
    } finally {
      setLoading(false)
    }
  }

  function copyCode() {
    if (!created) return
    navigator.clipboard.writeText(created.joinCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (created) {
    return (
      <main style={{ padding: '2rem', maxWidth: 560, margin: '0 auto' }}>
        <h2>✅ Сесію створено</h2>
        <p>Передайте учасникам цей код:</p>
        <div style={{
          background: '#f0f4ff',
          border: '1px solid #c0d0ff',
          borderRadius: 8,
          padding: '1rem 1.5rem',
          fontFamily: 'monospace',
          fontSize: '1rem',
          wordBreak: 'break-all',
          marginBottom: '0.75rem',
        }}>
          {created.joinCode}
        </div>
        <button onClick={copyCode} style={{ marginBottom: '1.5rem' }}>
          {copied ? '✓ Скопійовано' : 'Скопіювати код'}
        </button>
        <br />
        <a href={`/sessions/${created.id}/lobby`}>
          Відкрити лобі →
        </a>
      </main>
    )
  }

  return (
    <main style={{ padding: '2rem', maxWidth: 560, margin: '0 auto' }}>
      <h1>TPS360</h1>
      <h2>Створити сесію (Фасилітатор)</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleCreate}>
        <label style={{ display: 'block' }}>
          Ваше ім'я
          <input
            type="text"
            value={facilitatorName}
            onChange={e => setFacilitatorName(e.target.value)}
            placeholder="Марія Коваль"
            required
            style={{ display: 'block', marginTop: '0.5rem', width: '100%' }}
          />
        </label>

        <label style={{ display: 'block', marginTop: '1rem' }}>
          Громада
          <select
            value={communityId}
            onChange={e => setCommunityId(e.target.value)}
            required
            style={{ display: 'block', marginTop: '0.5rem', width: '100%' }}
          >
            <option value="">— оберіть громаду —</option>
            {communities.map(c => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.oblast}) — {c.population.toLocaleString()} мешк.
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: 'block', marginTop: '1rem' }}>
          Кількість учасників
          <input
            type="number"
            min={1}
            max={50}
            value={playerCapacity}
            onChange={e => setPlayerCapacity(Number(e.target.value))}
            required
            style={{ display: 'block', marginTop: '0.5rem', width: 100 }}
          />
        </label>

        <button type="submit" disabled={loading || communities.length === 0} style={{ marginTop: '1.5rem' }}>
          {loading ? 'Створення…' : 'Створити сесію'}
        </button>
      </form>
      <hr style={{ margin: '2rem 0' }} />
      <p style={{ color: '#666' }}>
        <a href="/join">← Приєднатися як учасник</a>
      </p>
    </main>
  )
}
