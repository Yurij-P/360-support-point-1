/** Role catalog entry as returned by GET /roles/catalog */
export interface RoleCatalogEntry {
  role_id: string
  display_name: string
  category_key: string
  category_label: string
  description: string
  typical_decisions: string[]
  information_sources: string[]
  decision_authority: string
}

/** Response envelope from GET /roles/catalog */
export interface RoleCatalogResponse {
  roles: RoleCatalogEntry[]
  total: number
}

/** Server-authorized participant role view from GET /sessions/{id}/roles/me */
export interface ParticipantRoleView {
  role_id: string
  display_name: string
  category_label: string
  description: string
  typical_decisions: string[]
  information_sources: string[]
  decision_authority: string
  participant_id: string
}
