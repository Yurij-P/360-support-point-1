/**
 * Re-exports TPS360ApiClient and adds typed helpers for B3/B4 endpoints.
 * All data access in components must go through this module — never raw fetch.
 */
import type {
  RoleCatalogEntry,
  RoleCatalogResponse,
  ParticipantRoleView,
} from '../types/roles.ts'

import type {
  CrisisDefinition,
  DefineCrisisRequest,
  AddCrisisConditionRequest,
} from '../types/crisis.ts'

export {
  TPS360ApiClient,
  type CommunityCatalogItem,
  type RoleWorkspaceState,
  type FacilitatorConsoleState,
} from '../../api_client.ts'

export type {
  RoleCatalogEntry,
  RoleCatalogResponse,
  ParticipantRoleView,
} from '../types/roles.ts'

export type {
  CrisisDefinition,
  CrisisCondition,
  DefineCrisisRequest,
  AddCrisisConditionRequest,
} from '../types/crisis.ts'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, init)
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}

// ── Role catalog (B3) ──────────────────────────────────────────────────────

export function getRoleCatalog(categoryKey?: string): Promise<RoleCatalogResponse> {
  const params = categoryKey ? `?category_key=${encodeURIComponent(categoryKey)}` : ''
  return apiFetch<RoleCatalogResponse>(`/roles/catalog${params}`)
}

export function getRoleCatalogEntry(roleId: string): Promise<RoleCatalogEntry> {
  return apiFetch<RoleCatalogEntry>(`/roles/catalog/${encodeURIComponent(roleId)}`)
}

export function getMyRole(sessionId: string, participantToken: string): Promise<ParticipantRoleView> {
  return apiFetch<ParticipantRoleView>(`/sessions/${sessionId}/roles/me`, {
    headers: { 'X-Participant-Token': participantToken },
  })
}

// ── Crisis constructor (B4) ────────────────────────────────────────────────

export function getCrisisDefinition(sessionId: string, facilitatorToken: string): Promise<CrisisDefinition | null> {
  return apiFetch<CrisisDefinition | null>(`/sessions/${sessionId}/crisis`, {
    headers: { 'X-Facilitator-Token': facilitatorToken },
  })
}

export function defineCrisis(
  sessionId: string,
  facilitatorToken: string,
  body: DefineCrisisRequest,
): Promise<CrisisDefinition> {
  return apiFetch<CrisisDefinition>(`/sessions/${sessionId}/crisis/define`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Facilitator-Token': facilitatorToken },
    body: JSON.stringify(body),
  })
}

export function addCrisisCondition(
  sessionId: string,
  facilitatorToken: string,
  body: AddCrisisConditionRequest,
): Promise<CrisisDefinition> {
  return apiFetch<CrisisDefinition>(`/sessions/${sessionId}/crisis/add-condition`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Facilitator-Token': facilitatorToken },
    body: JSON.stringify(body),
  })
}
