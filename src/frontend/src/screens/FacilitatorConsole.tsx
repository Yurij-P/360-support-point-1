/**
 * Facilitator Master Console (C2)
 * - Session lifecycle control: start, advance round, complete
 * - Send manual injects
 * - AI 5-variant future projections
 */
import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { TPS360ApiClient } from '../lib/api.ts'
import { useSession } from '../context/SessionContext.tsx'

const client = new TPS360ApiClient()

interface Projection {
  variant_id: string
  variant_name: string
  hazard_level: string
  projected_impact_summary: string
  suggested_inject_title: string
  suggested_inject_description: string
}

interface ConsoleState {
  status: string
  current_round: number
  simulated_hours_passed: number
  connected_participants_count: number
  assigned_roles_count: number
  future_projections_5_variants: Projection[]
}

const HAZARD_COLOR: Record<string, string> = {
  LOW: '#22c55e',
  MODERATE: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
  CATASTROPHIC: '#7c3aed',
}

export default function FacilitatorConsole() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const { facilitatorToken } = useSession()
  const [console_, setConsole] = useState<ConsoleState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [injectTitle, setInjectTitle] = useState('')
  const [injectDesc, setInjectDesc] = useState('')
  const [injectSent, setInjectSent] = useState<string | null>(null)

  const load = useCallback(() => {
    if (!sessionId || !facilitatorToken) return
    client
      .getFacilitatorConsole(sessionId, facilitatorToken)
      .then(setConsole)
      .catch(err => setError(err instanceof Error ? err.message : 'Помилка консолі'))
  }, [sessionId, facilitatorToken])

  useEffect(() => {
    load()
    const t = setInterval(load, 8000)
    return () => clearInterval(t)
  }, [load])

  async function act(fn: () => Promise<unknown>, label: string) {
    setBusy(true)
    setError(null)
    try {
      await fn()
      load()
    } catch (err) {
      setError(`${label}: ${err instanceof Error ? err.message : 'Помилка'}`)
    } finally {
      setBusy(false)
    }
  }

  async function handleSendInject(e: React.FormEvent) {
    e.preventDefault()
    if (!sessionId || !facilitatorToken) return
    await act(async () => {
      const inj = await client.sendInject(sessionId, facilitatorToken, {
        title: injectTitle.trim(),
        description: injectDesc.trim(),
      })
      setInjectSent(inj.title)
      setInjectTitle('')
      setInjectDesc('')
    }, 'Інджект')
  }

  if (!facilitatorToken) {
    return <p style={{ padding: '2rem', color: 'red' }}>Доступ лише для фасилітатора</p>
  }

  return (
    <main style={{ padding: '2rem', maxWidth: 900, margin: '0 auto' }}>
      <h2>Консоль Фасилітатора — {sessionId}</h2>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {/* Status panel */}
      {console_ && (
        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
          <Stat label="Статус" value={console_.status} />
          <Stat label="Раунд" value={`${console_.current_round}`} />
          <Stat label="Симул. годин" value={`${console_.simulated_hours_passed.toFixed(1)}`} />
          <Stat label="Учасники" value={`${console_.connected_participants_count}`} />
          <Stat label="З роллю" value={`${console_.assigned_roles_count}`} />
        </div>
      )}

      {/* Lifecycle controls */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        {console_?.status === 'PENDING' && (
          <button
            disabled={busy}
            onClick={() => act(() => client.startSession(sessionId!, facilitatorToken), 'Старт')}
            style={{ background: '#22c55e', color: '#fff', border: 'none', padding: '0.5rem 1.25rem', borderRadius: 6, cursor: 'pointer' }}
          >
            ▶ Розпочати сесію
          </button>
        )}
        {console_?.status === 'ACTIVE' && (
          <>
            <button
              disabled={busy}
              onClick={() => act(() => client.advanceRound(sessionId!, facilitatorToken), 'Раунд')}
              style={{ background: '#3b82f6', color: '#fff', border: 'none', padding: '0.5rem 1.25rem', borderRadius: 6, cursor: 'pointer' }}
            >
              ⏩ Наступний раунд
            </button>
            <button
              disabled={busy}
              onClick={() => act(() => client.completeSession(sessionId!, facilitatorToken), 'Завершення')}
              style={{ background: '#6b7280', color: '#fff', border: 'none', padding: '0.5rem 1.25rem', borderRadius: 6, cursor: 'pointer' }}
            >
              ■ Завершити сесію
            </button>
          </>
        )}
      </div>

      {/* Send inject */}
      {console_?.status === 'ACTIVE' && (
        <section style={{ marginBottom: '2rem', background: '#f8faff', border: '1px solid #dde4f0', borderRadius: 8, padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.75rem' }}>Надіслати інджект</h3>
          {injectSent && <p style={{ color: '#22c55e' }}>✓ «{injectSent}» надіслано</p>}
          <form onSubmit={handleSendInject}>
            <input
              type="text"
              placeholder="Заголовок"
              value={injectTitle}
              onChange={e => setInjectTitle(e.target.value)}
              required
              style={{ display: 'block', width: '100%', marginBottom: '0.5rem' }}
            />
            <textarea
              placeholder="Опис події / задачі для учасників"
              value={injectDesc}
              onChange={e => setInjectDesc(e.target.value)}
              required
              rows={3}
              style={{ display: 'block', width: '100%', marginBottom: '0.5rem' }}
            />
            <button type="submit" disabled={busy}>Надіслати</button>
          </form>
        </section>
      )}

      {/* AI projections */}
      {console_ && console_.future_projections_5_variants.length > 0 && (
        <section>
          <h3>AI: 5 варіантів розвитку подій</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {console_.future_projections_5_variants.map(p => (
              <div
                key={p.variant_id}
                style={{ border: `1px solid ${HAZARD_COLOR[p.hazard_level] ?? '#ccc'}`, borderRadius: 8, padding: '0.75rem 1rem' }}
              >
                <strong>{p.variant_name}</strong>
                <span style={{ marginLeft: '0.5rem', color: HAZARD_COLOR[p.hazard_level] ?? '#666', fontSize: '0.85rem' }}>
                  [{p.hazard_level}]
                </span>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem', color: '#444' }}>{p.projected_impact_summary}</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: '#666' }}>
                  💡 {p.suggested_inject_title}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: '#f1f5f9', borderRadius: 8, padding: '0.5rem 1rem', minWidth: 100, textAlign: 'center' }}>
      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{label}</div>
      <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{value}</div>
    </div>
  )
}
