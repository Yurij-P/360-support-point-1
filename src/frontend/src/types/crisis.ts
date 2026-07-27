/** Crisis condition as used in CrisisDefinition */
export interface CrisisCondition {
  condition_id: string
  description: string
  severity: number
  affected_area: string | null
}

/** Crisis definition attached to a facilitated session */
export interface CrisisDefinition {
  crisis_id: string
  title: string
  category: string
  hazard_type: string
  impact_type: string
  description: string
  conditions: CrisisCondition[]
  defined_at: string
}

/** Request body for POST /sessions/{id}/crisis/define */
export interface DefineCrisisRequest {
  title: string
  category: string
  hazard_type: string
  impact_type: string
  description: string
}

/** Request body for POST /sessions/{id}/crisis/add-condition */
export interface AddCrisisConditionRequest {
  description: string
  severity: number
  affected_area?: string
}
