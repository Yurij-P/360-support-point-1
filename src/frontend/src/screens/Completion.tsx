/**
 * Screen 7 of 7 (ROLE-UX-001 §7): Completion and Individual Reflection (AAR/Debriefing)
 * - D8 partial: uses AfterActionReviewReport + RoundTelemetrySnapshot from backend
 * - Shows preparedness delta, role summaries, vulnerabilities, AI recommendations
 */
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { TPS360ApiClient } from '../lib/api.ts'

const client = new TPS360ApiClient()

interface AARReport {
  session_id: string
  community_id: string
  total_rounds_played: number
  final_status: string
  initial_preparedness_score: number
  final_preparedness_score: number
  role_performance_summaries: Record<string, string>
  identified_vulnerabilities: string[]
  ai_learning_insights: string[]
  ai_recommendations: string[]
}

interface TelemetryRow {
  round_number: number
  simulated_hours: number
  mitigation_pct: number
  role_capabilities: Record<string, number>
  cognitive_stress_indexes: Record<string, number>
}

function ScoreDelta({ initial, final }: { initial: number; final: number }) {
  const delta = final - initial
  const color = delta >= 0 ? '#22c55e' : '#ef4444'
  const pct = (v: number) => `${(v * 100).toFixed(1)}%`
  return (
    <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', margin: '1rem 0' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Початкова готовність</div>
        <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{pct(initial)}</div>
      </div>
      <div style={{ fontSize: '1.5rem', color }}>{delta >= 0 ? '▲' : '▼'}</div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Фінальна готовність</div>
        <div style={{ fontSize: '2rem', fontWeight: 'bold', color }}>{pct(final)}</div>
      </div>
      <div style={{ color, fontWeight: 'bold', fontSize: '1.1rem' }}>
        {delta >= 0 ? '+' : ''}{pct(delta)}
      </div>
    </div>
  )
}

export default function Completion() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [report, setReport] = useState<AARReport | null>(null)
  const [telemetry, setTelemetry] = useState<TelemetryRow[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    Promise.all([
      client.getAARReport(sessionId),
      client.getSessionTelemetryTyped(sessionId),
    ])
      .then(([r, t]) => {
        setReport(r)
        setTelemetry(t)
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Помилка завантаження AAR'))
  }, [sessionId])

  if (error) return <p style={{ color: 'red', padding: '2rem' }}>{error}</p>
  if (!report) return <p style={{ padding: '2rem' }}>Завантаження звіту…</p>

  const roleEntries = Object.entries(report.role_performance_summaries)

  return (
    <main style={{ padding: '2rem', maxWidth: 800, margin: '0 auto' }}>
      <h2>After-Action Review</h2>
      <p style={{ color: '#64748b' }}>
        Громада: <strong>{report.community_id}</strong> · Раундів: <strong>{report.total_rounds_played}</strong> · Статус: <strong>{report.final_status}</strong>
      </p>

      {/* Preparedness delta */}
      <section style={{ background: '#f8faff', border: '1px solid #dde4f0', borderRadius: 8, padding: '1.25rem', marginBottom: '1.5rem' }}>
        <h3 style={{ margin: '0 0 0.5rem' }}>Індекс готовності</h3>
        <ScoreDelta initial={report.initial_preparedness_score} final={report.final_preparedness_score} />
      </section>

      {/* Telemetry table */}
      {telemetry.length > 0 && (
        <section style={{ marginBottom: '1.5rem' }}>
          <h3>Телеметрія по раундах</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: '#f1f5f9' }}>
                <th style={th}>Раунд</th>
                <th style={th}>Симул. год.</th>
                <th style={th}>Мітигація %</th>
                <th style={th}>Середній стрес</th>
              </tr>
            </thead>
            <tbody>
              {telemetry.map(row => {
                const stressValues = Object.values(row.cognitive_stress_indexes)
                const avgStress = stressValues.length
                  ? stressValues.reduce((a, b) => a + b, 0) / stressValues.length
                  : 0
                return (
                  <tr key={row.round_number}>
                    <td style={td}>{row.round_number}</td>
                    <td style={td}>{row.simulated_hours.toFixed(1)} год</td>
                    <td style={td}>{(row.mitigation_pct * 100).toFixed(0)}%</td>
                    <td style={td}>{(avgStress * 100).toFixed(0)}%</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </section>
      )}

      {/* Role summaries */}
      {roleEntries.length > 0 && (
        <section style={{ marginBottom: '1.5rem' }}>
          <h3>Результати по ролях</h3>
          {roleEntries.map(([role, summary]) => (
            <div key={role} style={{ border: '1px solid #e2e8f0', borderRadius: 6, padding: '0.75rem 1rem', marginBottom: '0.5rem' }}>
              <strong style={{ textTransform: 'capitalize' }}>{role.replace(/_/g, ' ')}</strong>
              <p style={{ margin: '0.25rem 0 0', color: '#555', fontSize: '0.9rem' }}>{summary}</p>
            </div>
          ))}
        </section>
      )}

      {/* Vulnerabilities */}
      {report.identified_vulnerabilities.length > 0 && (
        <section style={{ marginBottom: '1.5rem' }}>
          <h3>⚠️ Виявлені вразливості</h3>
          <ul>
            {report.identified_vulnerabilities.map((v, i) => <li key={i}>{v}</li>)}
          </ul>
        </section>
      )}

      {/* AI insights */}
      {report.ai_learning_insights.length > 0 && (
        <section style={{ marginBottom: '1.5rem' }}>
          <h3>🤖 AI-спостереження</h3>
          <ul>
            {report.ai_learning_insights.map((v, i) => <li key={i}>{v}</li>)}
          </ul>
        </section>
      )}

      {/* AI recommendations */}
      {report.ai_recommendations.length > 0 && (
        <section style={{ marginBottom: '2rem' }}>
          <h3>💡 Рекомендації для наступної сесії</h3>
          <ul>
            {report.ai_recommendations.map((v, i) => <li key={i}>{v}</li>)}
          </ul>
        </section>
      )}

      <a href="/join" style={{ display: 'inline-block', marginTop: '1rem', color: '#3b82f6' }}>
        ← Повернутись на головну
      </a>
    </main>
  )
}

const th: React.CSSProperties = { padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 600, borderBottom: '2px solid #e2e8f0' }
const td: React.CSSProperties = { padding: '0.4rem 0.75rem', borderBottom: '1px solid #f1f5f9' }
