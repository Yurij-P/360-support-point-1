/**
 * TPS360 Web Workspace API Client
 * Provides type-safe access to TPS360 REST endpoints and SSE real-time event streams.
 */

export interface CommunityCatalogItem {
  id: string;
  name: string;
  oblast: string;
  population: number;
  settlements_count: number;
  data_completeness_pct: number;
}

export interface RoleWorkspaceState {
  session_id: string;
  role_id: string;
  role_title: string;
  resources: Record<string, Record<string, number>>;
  cognitive_stress_level_pct: number;
  capability_score: number;
}

export interface FacilitatorConsoleState {
  session_id: string;
  current_round: number;
  simulated_hours: number;
  participants_count: number;
  session_status: string;
}

export class TPS360ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = "http://localhost:8000/api/v1") {
    this.baseUrl = baseUrl;
  }

  async fetchCommunitiesCatalog(): Promise<CommunityCatalogItem[]> {
    const res = await fetch(`${this.baseUrl}/communities/catalog`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async fetchCommunityPassport(communityId: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/communities/${communityId}/passport`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async fetchRoleWorkspace(sessionId: string, roleId: string): Promise<RoleWorkspaceState> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/role-workspace?role_id=${roleId}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async submitLegoDecisionCard(sessionId: string, decisionPayload: Record<string, unknown>): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/lego-decisions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(decisionPayload),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async fetchFacilitatorConsole(sessionId: string): Promise<FacilitatorConsoleState> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/facilitator-console`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async fetchFutureProjections(sessionId: string): Promise<Record<string, unknown>[]> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/future-projections`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async injectPsychologicalFriction(sessionId: string, frictionPayload: Record<string, unknown>): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/injects/psychological-friction`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(frictionPayload),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async fetchAARReport(sessionId: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/aar-report`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async fetchSessionTelemetry(sessionId: string): Promise<Record<string, unknown>[]> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/telemetry`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async createSession(params: {
    communityId: string
    facilitatorName: string
    playerCapacity: number
  }): Promise<{
    id: string
    facilitator_token: string
    join_token: string
    status: string
  }> {
    const res = await fetch(`${this.baseUrl}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        community_id: params.communityId,
        facilitator_name: params.facilitatorName,
        player_capacity: params.playerCapacity,
        role_profiles: [],
      }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async joinSession(
    sessionId: string,
    joinToken: string,
    displayName: string,
  ): Promise<{
    participant_id: string
    participant_token: string
    display_name: string
    lifecycle: string
    session_status: string
  }> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/participants/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ join_token: joinToken, display_name: displayName }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async getLobbyStatus(sessionId: string): Promise<{
    session_id: string
    capacity: number
    connected_count: number
    assigned_count: number
    can_start: boolean
    readiness_message: string
    participants: Array<{ participant_id: string; display_name: string; role_id: string | null }>
  }> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/lobby-status`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async getSession(sessionId: string): Promise<{ id: string; status: string; [key: string]: unknown }> {
    const res = await fetch(`${this.baseUrl}/sessions/${sessionId}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  subscribeToSessionEvents(sessionId: string, onMessage: (event: MessageEvent) => void): EventSource {
    const eventSource = new EventSource(`${this.baseUrl}/events/session/${sessionId}/stream`);
    eventSource.onmessage = onMessage;
    return eventSource;
  }
}
