# TPS360 Participant Workspace Wireframes

## Status

APPROVED UX LOGIC prototype with a minimal participant API integration. This remains a low-fidelity UX artifact, not production frontend code.

## Seven-screen lifecycle

1. Join Session.
2. Lobby / Readiness.
3. Role and Participant Briefing.
4. Active Simulation Workspace.
5. Inject Detail.
6. Decision Preparation and Submission.
7. Completion and Individual Reflection.

The facilitator assigns the role between Lobby and Briefing. Participants cannot self-select, change, automatically receive, or randomly receive a role.

## API integration

The runtime calls the participant API at `http://127.0.0.1:8000` by default. Override it before loading the page with `window.TPS360_API_BASE_URL` when a different local API address is required.

- Join: `POST /sessions/{session_id}/participants/join` with `join_token` and `display_name`.
- Reconnect and polling: `GET /sessions/{session_id}/participant` with `X-Participant-Token`.
- No facilitator token is used by this workspace.
- The participant token is stored only in localStorage and is never rendered, logged, or put in the URL.
- Inject and decision API calls are intentionally out of scope for this step.

Participant identity and participant token are retained locally as MOCK DATA for reconnect. Server-side persistence is API REQUIRED and remains in-memory in the current backend process.

## Role model

The runtime consumes a universal scenario/session role profile contract with: `role_id`, `role_version`, `title`, `category_id`, `category_title`, `briefing`, `responsibilities`, `permissions`, `available_data`, `resources`, `allowed_actions`, `restrictions`, `interactions`, `visibility_rules`, and `tasks`.

The three original profiles and the emergency medical representative are demo fixtures. The fourth profile validates that the same shell works for an arbitrary category; it is not a production role definition.

The 7-category / 23-position catalog is a UX coverage reference only. It is not the roster of this session.

## Data markers

- `MOCK DATA` identifies illustrative local values or local persistence.
- `API REQUIRED` identifies backend work that is not implemented in the workspace.
- `ROLE MODEL NOT APPROVED` identifies demo role content.
- `PRODUCT DECISION REQUIRED` identifies unresolved product behavior.

## Local launch

Start the API from the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn tps360.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, start the participant preview on its own port:

```powershell
python -m http.server 3001 --bind 127.0.0.1 --directory docs/ux-ui/prototypes/participant-workspace-v1.1
```

Open `http://localhost:3001/TPS360%20Participant%20Wireframes.html`.

The API permits only `http://localhost:3001` and `http://127.0.0.1:3001` as participant origins. No dependencies, CDN, `eval`, `new Function`, or unsafe HTML insertion are used.

## Local checks

```powershell
node --check participant-api.js
node --test participant-api.test.js
```