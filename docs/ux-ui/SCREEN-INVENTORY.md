# TPS360 Screen Inventory

Status: draft UX architecture. Scope: screen specification only.

## Canonical community-first flow

Community Catalog -> Community Selection -> Community Profile / Passport -> Community Geospatial Overview -> Threat Selection / Threat Profile -> Scenario Selection for Community -> Simulation Context Snapshot -> Create Simulation Session -> Join Session -> Lobby -> Readiness Dashboard -> Active Simulation -> Evaluation -> AAR / Debriefing -> Final Report -> Session Archive.

No exact role set, number of rounds, game mechanics, or round transitions are defined here. Those items are marked PRODUCT DECISION REQUIRED where relevant.

## Full inventory

| Stage | Screen | User | Purpose | MVP | Backend/API | Mock data | PRODUCT DECISION REQUIRED | Data passed forward |
|---|---|---|---|---|---|---|---|---|
| Community discovery | Community Catalog | Facilitator / admin | Find and select the community for a run. | MVP | API missing: only `POST /communities` and `GET /communities/{id}` confirmed; no list/search. | Current prototype uses one hard-coded community. | Catalog ownership, filters, sorting, access rules. | `community_id`, community name, metadata. |
| Community context | Community Profile / Passport | Facilitator / admin | Review selected community baseline. | MVP | Partial: `GET /communities/{id}` confirmed; full passport read model not confirmed. | Prototype shows fixed community widgets. | Passport fields, source of truth, freshness rules. | Community profile, settlements/assets/population if available. |
| Community context | Community Geospatial Overview | Facilitator | Understand territory, exposed assets, and operational geography. | MVP | API missing: no confirmed map/geospatial layer endpoint for frontend. | Prototype has static map-like SVG labels. | Map provider, layers, precision, offline behavior, data governance. | Geographic context, exposed assets, selected area/layer state. |
| Threat context | Threat Selection / Threat Profile | Facilitator | Select or assess the threat relevant to the community. | MVP | Partial: `POST /risks` confirmed; list/read/profile API missing. `POST /assessments` exists but not a full threat profile UI. | Prototype has one fixed water incident. | Threat taxonomy, assessment scale, who approves threat selection. | Selected threat/risk input and assessment assumptions. |
| Scenario setup | Scenario Selection for Community | Facilitator | Choose a scenario compatible with community and threat. | MVP | Partial: `POST /scenarios`, `GET /scenarios/{id}` confirmed; list/search/compatibility missing. | Prototype creates one demo scenario. | Scenario taxonomy, versioning, compatibility rules. | `scenario_id`, scenario summary, constraints. |
| Scenario setup | Simulation Context Snapshot | Facilitator | Freeze the community + threat + scenario context before session creation. | MVP | API missing: no confirmed snapshot generation/read/persist endpoint. | Not implemented in frontend. | Snapshot content, immutability, refresh rules, approval owner. | Snapshot ID or embedded context for session creation. |
| Session setup | Create Session | Facilitator | Create a multiplayer simulation session from the selected context. | MVP | `POST /sessions` confirmed; context snapshot link not confirmed. | Not implemented in frontend. | Capacity, role rules, token handling, join code display. | `session_id`, facilitator token, join code/link, capacity/roles. |
| Session entry | Join Session | Participant | Enter session by code/link and name. | MVP | Partial: `POST /sessions/{id}/participants` confirmed; join-by-code lookup not confirmed. | Not implemented in frontend. | Join code format, identity/reconnect rules, participant naming policy. | `participant_id`, name, session reference. |
| Session setup | Lobby | Facilitator / participant | Gather participants and manage roles before launch. | MVP | `GET /sessions/{id}`, `POST /sessions/{id}/participants`, `PUT /sessions/{id}/participants/{participant_id}/role` confirmed. | Not implemented in frontend. | Role taxonomy, self-role vs facilitator assignment, capacity behavior. | Participants, roles, readiness blockers. |
| Session setup | Readiness Dashboard | Facilitator | Confirm launch conditions. | MVP | `GET /sessions/{id}`, `POST /sessions/{id}/start` confirmed. | Not implemented in frontend. | Readiness rules and override policy. | Ready session state, participants, roles. |
| Active runtime | Active Simulation - Facilitator | Facilitator | Run the live simulation. | MVP | `POST /sessions/{id}/injects`, `GET /sessions/{id}`, `GET /sessions/{id}/journal`, `POST /sessions/{id}/complete` confirmed. | Current static dashboard resembles this, but uses legacy simulation API and fixed content. | Event cadence, round model, reveal policy, timer rules. | Injects, decisions, journal, completion state. |
| Active runtime | Active Simulation - Participant | Participant | Receive injects and submit decisions. | MVP | `GET /sessions/{id}` and `POST /sessions/{id}/injects/{inject_id}/decisions` confirmed. | Not implemented in frontend. | Participant visibility, decision editability, reconnect behavior. | Participant decisions and status. |
| Active runtime | Inject Card | Facilitator / participant | Present one inject/event clearly. | MVP | Session inject API confirmed for creation and read through session/journal responses. | Prototype has one static event card. | Severity labels, attachments, close/edit behavior. | Inject ID, content, timestamp, required action. |
| Active runtime | Decision Form | Participant | Capture decision for a specific inject. | MVP | `POST /sessions/{id}/injects/{inject_id}/decisions` confirmed. | Prototype has hard-coded decision cards using legacy `/simulations`. | Free text vs option set, rationale field, edit window. | Decision ID/content linked to participant and role. |
| Active runtime | Session Journal | Facilitator / later participant | Audit events, decisions, and completion. | MVP | `GET /sessions/{id}/journal` confirmed. | Prototype has static timeline. | Journal filters, visibility, export timing. | Timeline for evaluation/AAR/report. |
| Session close | Completion | Facilitator / participant | End active simulation and transition to post-session work. | MVP | `POST /sessions/{id}/complete` confirmed. | Not implemented in frontend. | Completion confirmation, late decisions, transition target. | Completed session, journal, participants, decisions. |
| Post-session | Evaluation | Facilitator / admin / evaluator | Score or assess outcomes. | Next | API missing: `POST /assessments` exists but not confirmed as session evaluation workflow. | Not implemented. | Evaluation rubric, scoring ownership, evidence rules. | Scores, findings, evidence links. |
| Post-session | AAR / Debriefing | Facilitator / participant | Structured after-action review and discussion. | Next | API missing. | Not implemented. | AAR format, participant input rules, facilitation prompts. | Notes, action items, lessons learned. |
| Post-session | Final Report | Facilitator / admin | Generate shareable result. | Next | API missing. | Not implemented. | Report template, approval workflow, export formats. | Report artifact, recommendations, metadata. |
| Archive | Session Archive | Facilitator / admin | Find completed sessions and reports. | Next | API missing: no session list/archive endpoint confirmed. | Not implemented. | Retention, access, search filters, export permissions. | Archived session/report references. |
| Admin | Admin Community Management | Admin | Manage community catalog if TPS360 owns it. | Later | API missing for list/update/delete. | Not implemented. | Whether TPS360 owns community master data. | Community records. |
| Admin | Admin Scenario Management | Admin | Manage scenario library metadata. | Later | Partial: create/get scenario; list/update/archive missing. | Not implemented. | Scenario governance and versioning. | Scenario records. |
| Admin | Admin Users / Organizations | Admin | Manage users and organizations if auth exists. | Later | API missing. | Not implemented. | Auth/RBAC/organization model. | Users, orgs, permissions. |

## Loading, empty, error, success states by screen group

| Group | Required states |
|---|---|
| Catalog/list screens | loading, empty, no results, API error, selection success. |
| Profile/context screens | loading, missing data, stale data warning, API error, ready. |
| Map/geospatial screens | loading layers, unavailable layer, no geodata, API error, selected feature. |
| Threat/scenario screens | loading, empty, incompatible, validation error, selected. |
| Snapshot | generating, incomplete context, generated, stale after context change, API error. |
| Session setup | creating, created, token display/copy, join-code unavailable, API error. |
| Lobby/readiness | loading, empty lobby, full, roles incomplete, ready, start blocked, API error. |
| Active runtime | loading, no active inject, waiting for decisions, submitted, duplicate decision, completed, API error. |
| Post-session | loading, incomplete, saved, submitted, generated, failed. |
| Archive | loading, empty, no results, error, success. |

## Responsive requirements

Desktop:

- Facilitator screens support dense comparison and monitoring.
- Community profile, geospatial overview, and active runtime can use multi-panel layouts.

Tablet:

- Facilitator can run lobby/readiness/active session with fewer visible panels.
- Geospatial overview should support touch-friendly layer controls.

Mobile:

- Participant Join Session, lobby waiting, active inject, decision form, and completion are first-class.
- Facilitator mobile is monitoring/emergency action only unless product owner confirms mobile facilitation.

## Information architecture

### Primary navigation

| Area | Screens |
|---|---|
| Communities | Community Catalog, Community Profile / Passport, Community Geospatial Overview. |
| Threats and Scenarios | Threat Selection / Threat Profile, Scenario Selection for Community, Simulation Context Snapshot. |
| Run Session | Create Session, Join Session, Lobby, Readiness Dashboard, Active Simulation, Completion. |
| Post-Session | Evaluation, AAR / Debriefing, Final Report. |
| Archive | Session Archive. |
| Admin | Community, scenario, user/organization administration only after product decisions. |

### Session transitions

| From | To | Trigger | Current support |
|---|---|---|---|
| context selected | session created/lobby | `POST /sessions` | Partial: snapshot link is not confirmed. |
| lobby | ready | Domain readiness rules | Supported in domain/state; exact UX rule needs approval. |
| ready | active | `POST /sessions/{session_id}/start` | Supported. |
| active | completed | `POST /sessions/{session_id}/complete` | Supported. |
| completed | evaluation | Future evaluation start | API missing. |
| evaluation | AAR / debriefing | Future post-session workflow | API missing. |
| AAR / debriefing | final report | Future report generation | API missing. |
| final report | archived | Future archive action | API missing. |

## Required summary table

| Journey stage | Screen | In documentation | API exists | MVP status | Open decision |
|---|---|---|---|---|---|
| Community discovery | Community Catalog | Yes | Missing list/search | MVP | Catalog ownership, filters, access. |
| Community context | Community Profile / Passport | Yes | Partial | MVP | Passport fields and source of truth. |
| Community context | Community Geospatial Overview | Yes | Missing | MVP | Map provider, layers, data governance. |
| Threat context | Threat Selection / Threat Profile | Yes | Partial | MVP | Threat taxonomy and assessment scale. |
| Scenario setup | Scenario Selection for Community | Yes | Partial | MVP | Compatibility, versioning, selection rules. |
| Scenario setup | Simulation Context Snapshot | Yes | Missing | MVP | Snapshot content and immutability. |
| Session setup | Create Session | Yes | Exists, context link partial | MVP | Capacity, roles, token behavior. |
| Session entry | Join Session | Yes | Partial | MVP | Join-code lookup and reconnect. |
| Session setup | Lobby | Yes | Exists | MVP | Role assignment policy. |
| Session setup | Readiness Dashboard | Yes | Exists | MVP | Readiness override policy. |
| Active runtime | Active Simulation - Facilitator | Yes | Exists | MVP | Event cadence, reveal policy, timers. |
| Active runtime | Active Simulation - Participant | Yes | Exists | MVP | Visibility and decision editability. |
| Active runtime | Inject Card | Yes | Exists | MVP | Severity, attachments, lifecycle. |
| Active runtime | Decision Form | Yes | Exists | MVP | Free text vs options, rationale. |
| Active runtime | Session Journal | Yes | Exists | MVP | Filters, visibility, export. |
| Session close | Completion | Yes | Exists | MVP | Late decisions and transition target. |
| Post-session | Evaluation | Yes | Missing/partial | Next | Rubric and scoring owner. |
| Post-session | AAR / Debriefing | Yes | Missing | Next | AAR format and participant input. |
| Post-session | Final Report | Yes | Missing | Next | Template, approval, export. |
| Archive | Session Archive | Yes | Missing | Next | Retention, search, access. |
