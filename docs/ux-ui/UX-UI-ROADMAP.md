# TPS360 UX/UI Roadmap

Status: draft plan. Scope: UX/UI sequencing only; no implementation.


## Wireframes v1.1 status

- Community-first wireframes v1.1: APPROVED.
- High-fidelity UI: NOT STARTED.
- Frontend implementation: NOT STARTED.

## Guiding constraint

Do not start by building a new frontend. First validate the community-first flow, agree missing product decisions, and map API gaps.

Canonical flow:

Community Catalog -> Community Profile / Passport -> Community Geospatial Overview -> Threat Selection / Threat Profile -> Scenario Selection for Community -> Simulation Context Snapshot -> Create Session -> Join Session -> Lobby -> Readiness -> Active Simulation -> Evaluation -> AAR / Debriefing -> Final Report -> Session Archive.

## Wireframe order

### Phase 1: Community-first MVP setup

1. Community Catalog.
2. Community Profile / Passport.
3. Community Geospatial Overview.
4. Threat Selection / Threat Profile.
5. Scenario Selection for Community.
6. Simulation Context Snapshot.
7. Create Session.
8. Join Session.
9. Lobby facilitator view.
10. Lobby participant view.
11. Readiness Dashboard.

### Phase 2: Active runtime MVP

1. Active Simulation - Facilitator.
2. Active Simulation - Participant.
3. Inject Card.
4. Decision Form.
5. Session Journal.
6. Completion.

### Phase 3: Post-session flow

1. Evaluation.
2. AAR / Debriefing.
3. Final Report.
4. Session Archive.

### Phase 4: Minimal administration

1. Community administration only if TPS360 owns community master data.
2. Scenario management only after scenario governance is approved.
3. Facilitator/user access only after auth is approved.
4. Organization settings only if deployment model requires it.

## First approval screens

| Screen | Reason |
|---|---|
| Community Catalog | Confirms that product starts from communities, not scenarios. |
| Community Profile / Passport | Defines the core context users must trust before simulation. |
| Community Geospatial Overview | Defines map/layer expectations and missing API needs. |
| Threat Selection / Threat Profile | Defines how threat context narrows scenario choice. |
| Simulation Context Snapshot | Defines handoff from community/threat/scenario into session. |
| Active Simulation - Facilitator | Highest-risk live control surface. |
| Active Simulation - Participant | Determines mobile participant usability. |
| Session Journal | Establishes auditability for evaluation/AAR/report. |

## Interactive prototype order

1. Select community from catalog.
2. Review passport and geospatial overview.
3. Select threat and scenario.
4. Review Simulation Context Snapshot.
5. Create session.
6. Participant joins.
7. Facilitator runs lobby/readiness.
8. Facilitator sends one inject.
9. Participant submits decision.
10. Journal records inject and decision.
11. Facilitator completes session.
12. Evaluation/AAR/report are represented as placeholders until APIs and product rules are approved.

Prototype data can be static initially, but it must be generic and clearly separated from Bereznehuvatska test fixtures.

## Future frontend PR breakdown after design approval

| PR | Scope | Depends on |
|---|---|---|
| PR 1 | Frontend shell and routing | Architecture decision. |
| PR 2 | Design tokens and shared components | Design system approval. |
| PR 3 | Community Catalog | Community list/search API. |
| PR 4 | Community Profile / Passport | Passport read model. |
| PR 5 | Community Geospatial Overview | Map/geodata API and provider decision. |
| PR 6 | Threat Selection / Threat Profile | Threat list/read/ranking API. |
| PR 7 | Scenario Selection for Community | Scenario list/search/compatibility API. |
| PR 8 | Simulation Context Snapshot | Snapshot API and immutability decision. |
| PR 9 | Create Session, Join Session, Lobby | Session API plus join-code decision. |
| PR 10 | Readiness and role assignment | Role taxonomy and readiness policy. |
| PR 11 | Active facilitator runtime | Session injects, decisions, journal, complete. |
| PR 12 | Active participant runtime | Participant UX and reconnect decision. |
| PR 13 | Completion and post-session placeholders | Transition decisions. |
| PR 14 | Evaluation/AAR/report/archive | Backend and product model required. |

## Missing API list

- Community Catalog list/search/filter.
- Community Profile / Passport complete read model.
- Community Geospatial Overview layers/geodata.
- Threat Selection / Threat Profile list/read/ranking.
- Scenario Selection for Community list/search/compatibility.
- Simulation Context Snapshot generation/read/persist.
- Join Session by code/link lookup if participants do not know session ID.
- Session dashboard/list/resume.
- Evaluation workflow.
- AAR / Debriefing workflow.
- Final Report generation/export.
- Session Archive list/search/export.
- Auth/RBAC/admin management.
- Real-time session update transport.

## PRODUCT DECISION REQUIRED

- Community catalog ownership and source of truth.
- Community passport fields and data freshness rules.
- Geospatial provider, layers, precision, and data governance.
- Threat taxonomy and assessment scale.
- Scenario compatibility and versioning rules.
- Simulation Context Snapshot content and immutability.
- Join code format and participant reconnect model.
- Role taxonomy and role assignment policy.
- Readiness rules and facilitator override policy.
- Inject lifecycle and event cadence.
- Participant decision format: free text, options, rationale, edit window.
- Visibility of participant decisions.
- Evaluation rubric and ownership.
- AAR / Debriefing format and participant input model.
- Report template, approval, export formats.
- Archive retention, access, and search rules.

## Risks to resolve before high-fidelity UI

- Starting with scenario selection instead of community context.
- Treating one test community as platform architecture.
- Designing map-heavy screens before geodata/API decisions.
- Building post-session screens before evaluation/AAR/report models exist.
- Building around legacy `/simulations` endpoints while active multiplayer uses `/sessions`.
- Leaving participant mobile experience as a secondary adaptation.

## Recommended next action

Create low-fidelity wireframes for:

1. Community Catalog.
2. Community Profile / Passport.
3. Community Geospatial Overview.
4. Threat Selection / Threat Profile.
5. Simulation Context Snapshot.
6. Active Simulation - Facilitator.
7. Active Simulation - Participant.
8. Session Journal.
