# TPS360 UX/UI Audit

Status: draft design audit. Scope: documentation only; no frontend or backend implementation.

## Product correction from review

The platform flow is community-first, not scenario-first:

Community Catalog -> Community Selection -> Community Profile / Passport -> Community Geospatial Overview -> Threat Selection / Threat Profile -> Scenario Selection for Community -> Simulation Context Snapshot -> Create Simulation Session -> Lobby and Readiness -> Active Simulation -> Evaluation -> AAR / Debriefing -> Final Report -> Archive.

Bereznehuvatska community is only a test/example fixture in the current prototype and must not define the platform architecture.

## Review findings in previous draft

| Gap found | Where it appeared | Correction |
|---|---|---|
| Flow started from scenario library | `USER-FLOWS.md`, `SCREEN-INVENTORY.md`, `UX-UI-ROADMAP.md` | Start with Community Catalog and community context. |
| Community selection was skipped | All UX flow docs | Add Community Catalog and selected community state. |
| Community passport/profile was skipped | All UX flow docs | Add Community Profile / Passport before threat/scenario work. |
| Geospatial overview was skipped | All UX flow docs | Add Community Geospatial Overview and mark real map/API gaps. |
| Threat selection/evaluation was skipped | `SCREEN-INVENTORY.md`, `UX-UI-ROADMAP.md` | Add Threat Selection / Threat Profile before scenario selection. |
| Simulation Context Snapshot was skipped | All UX flow docs | Add snapshot as handoff from community/threat/scenario to session. |
| Prototype community risk | `UX-UI-AUDIT.md` under static data | Explicitly mark Bereznehuvatska as test data only. |
| Possible unconfirmed APIs | Scenario library, dashboard, archive, debrief/report docs | Mark missing APIs and PRODUCT DECISION REQUIRED. |

## Evidence reviewed

- `src/tps360/web/index.html`
- `src/tps360/web/style.css`
- `src/tps360/web/app.js`
- `src/tps360/web/README.md`
- `src/tps360/api/main.py`
- `src/tps360/api/routers/communities.py`
- `src/tps360/api/routers/risks.py`
- `src/tps360/api/routers/assessments.py`
- `src/tps360/api/routers/preparedness_profiles.py`
- `src/tps360/api/routers/scenarios.py`
- `src/tps360/api/routers/sessions.py`
- `src/tps360/api/routers/simulations.py`
- `src/tps360/simulation/domain/session.py`
- `MASTER_PROJECT.md`
- `SKILL.md`

## Current frontend location and stack

The frontend is located in `src/tps360/web` and is served by FastAPI from `src/tps360/api/main.py`.

Observed stack:

- Static HTML: `src/tps360/web/index.html`.
- Handwritten CSS: `src/tps360/web/style.css`.
- Vanilla browser JavaScript: `src/tps360/web/app.js`.
- Static icon asset: `src/tps360/web/icons/water.svg`.
- Google Fonts referenced from HTML: Inter and Outfit.
- No frontend framework, router, build step, component library, or frontend package manager setup was found for the current web surface.

FastAPI routes relevant to the web UI:

- `/` returns `index.html`.
- `/static/*` serves files from `src/tps360/web`.
- `/health` returns a minimal health response.

## Existing pages and routes

| Route | Source | Current behavior |
|---|---|---|
| `/` | `src/tps360/api/main.py` | Serves the single static dashboard. |
| `/static/*` | `src/tps360/api/main.py` | Serves CSS, JS, and icons. |

There are no implemented frontend routes for Community Catalog, Community Profile / Passport, Community Geospatial Overview, Threat Selection, Simulation Context Snapshot, lobby, readiness, participant runtime, admin, evaluation, AAR, report, or archive.

## Existing UI

The current UI is a one-page crisis operations dashboard. It includes static community/scenario widgets, a static map-like panel, one current event panel, three hard-coded decision cards, resource indicators, alerts, and a bottom timeline. These are HTML sections, not reusable frontend components.

## Static and mock data

The page contains hard-coded demo content including Bereznehuvatska community, a water-related incident, map labels, resource cards, alerts, decision options, and timeline entries. This content is mock/test data. It must not be treated as the product baseline, default community, role model, threat catalog, scenario catalog, or gameplay mechanic.

## API currently used by the frontend

| API | Current use | Status |
|---|---|---|
| `POST /communities` | Creates/reuses a fixed demo community. | Prototype only; not a catalog. |
| `POST /scenarios` | Creates a demo scenario and stores returned ID. | Prototype only; not scenario selection. |
| `POST /simulations` | Creates a legacy simulation. | Connected. |
| `POST /simulations/{id}/start` | Starts the legacy simulation. | Connected. |
| `POST /simulations/{id}/decisions` | Sends a selected decision. | Connected. |

The current frontend does not use the newer multiplayer session runtime API from `src/tps360/api/routers/sessions.py`.

## Confirmed API surfaces and UX implications

| Product area | Confirmed API | UX implication |
|---|---|---|
| Health | `GET /health` | Can support service status. |
| Community record | `POST /communities`, `GET /communities/{community_id}` | Single community create/read exists; catalog/list API is not confirmed. |
| Risk/threat input | `POST /risks` | Creation exists; list/read threat profile is not confirmed. |
| Assessments | `POST /assessments` | Creation exists; evaluation UX is not covered by this alone. |
| Preparedness profiles | `GET /preparedness-profiles`, `POST /preparedness-profiles/agree` | Can inform community readiness, but screen contract needs mapping. |
| Scenarios | `POST /scenarios`, `GET /scenarios/{scenario_id}` | Create/read exists; scenario library/search is not confirmed. |
| Sessions | create, get, join, assign role, start, send inject, submit decision, complete, journal | Supports active session runtime, not pre-session catalog/snapshot or post-session reporting. |
| Legacy simulations | create/get/start/deliver inject/decide/complete | Current prototype uses part of this; future UX should not depend on it where `/sessions` is the product runtime. |

## Missing or unconfirmed API for community-first UX

- Community Catalog list/search/filter.
- Community Profile / Passport complete read model.
- Community Geospatial Overview map layers and geodata contract.
- Threat Selection / Threat Profile list/read/ranking contract.
- Scenario Selection for Community list/filter/compatibility contract.
- Simulation Context Snapshot generation/read/persist contract.
- Join Session by join code contract, if session ID is not exposed to participants.
- Session list/resume dashboard.
- Evaluation workflow API.
- AAR / Debriefing API.
- Final Report generation/export API.
- Session Archive list/search/export API.
- Authentication and authorization.
- Real-time sync contract: polling, SSE, or WebSocket.

## Keep / rework / create

| Area | Recommendation | Reason |
|---|---|---|
| FastAPI static serving | Keep temporarily | Useful for prototype delivery. |
| `/health` | Keep | Useful for checks. |
| Existing API error handling in `app.js` | Keep as baseline | Failed responses are surfaced instead of silent success. |
| Current dark dashboard visual style | Rework | Too demo-specific and visually heavy for the full community-first platform. |
| Bereznehuvatska hard-coded content | Rework | It is test data only. |
| Single-page static HTML | Rework | Cannot support community-first and role-specific workflows cleanly. |
| Legacy `/simulations` integration | Rework | Active multiplayer UX should align with `/sessions`. |
| Community Catalog | Create | Required first step of agreed product flow; API missing. |
| Community Profile / Passport | Create | Required before threat/scenario work; partial API only. |
| Community Geospatial Overview | Create | Required by agreed flow; real geodata/API missing. |
| Threat Selection / Threat Profile | Create | Required before scenario selection; API incomplete. |
| Simulation Context Snapshot | Create | Required handoff into session; API missing. |
| Facilitator lobby/runtime console | Create | Session runtime API exists. |
| Participant runtime | Create | Session runtime API exists. |
| Evaluation/AAR/report/archive | Create later | Product flow requires them; backend APIs not confirmed. |

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Starting UX at scenario selection | High | Use community-first IA as the canonical flow. |
| Treating test data as architecture | High | Label all Bereznehuvatska content as fixture/mock only. |
| Designing screens around APIs that do not exist | High | Mark missing APIs and PRODUCT DECISION REQUIRED. |
| Static page cannot scale to role-specific workflows | High | Define IA and split future frontend work into small PRs after approval. |
| No frontend auth model | High | Decide auth before admin/facilitator UX. |
| No real-time transport decision | High | Decide polling/SSE/WebSocket before active runtime UI. |
| Accessibility is not designed into current prototype | Medium | Add WCAG AA, keyboard, focus, and live region requirements. |

## Readiness assessment

Frontend readiness level: prototype. It demonstrates one crisis dashboard with mock community-specific content and partial legacy simulation API wiring. It is not yet a full community-first TPS360 web platform.
